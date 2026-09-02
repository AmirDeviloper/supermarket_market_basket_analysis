import os
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


class BaghiyyatollahClinicScraper:
    def __init__(self, temp_dir='temp', results_dir='results'):
        self.full_url = 'https://nobat.bmsu.ac.ir/new_ora/NobatFuture'
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/141.0.0.0 Safari/537.36',
        }
        self.links = []
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.verify = False
        self.cookies_for_playwright = []

        self._playwright = None
        self._browser = None
        self._context = None

        self.temp_dir = temp_dir
        self.results_dir = results_dir
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.results_dir, exist_ok=True)


    def fetch_page(self, full_url=None):
        if full_url is None:
            full_url = self.full_url
        print(f"Fetching Link'")
        response = self.session.get(full_url, timeout=10)
        if response.status_code == 200:
            self.cookies_for_playwright = [
                {
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': cookie.domain,
                    'path': cookie.path,
                }
                for cookie in self.session.cookies
            ]
            return BeautifulSoup(response.text, 'html.parser')
        else:
            raise Exception(f"Failed to fetch: {response.status_code}")

    def extract_clinic_group_links(self, soup):
        buttons = soup.find_all('a', class_='btn-warning')
        links = []
        for i, btn in enumerate(buttons):
            onclick = btn.get('onclick')
            if onclick:
                clinic_group_id, clinic_group_title = self.parse_onclick(onclick)
                full_link = f'https://nobat.bmsu.ac.ir/New_ORA/NobatFuture/DisplayClinicsListForClinicGroupID?ID={clinic_group_id}&Title={clinic_group_title}'
                links.append(full_link)
                print(f"Group [{i + 1} / {len(buttons)}]")
        return links

    def parse_onclick(self, onclick):
        pattern = r"['()]"
        on_click_cleaned = re.sub(pattern, '', onclick.replace('NextPage', ''))
        return on_click_cleaned.split(',')

    def extract_doctors_links_for_clinic_group_pages(self, soup):
        buttons = soup.find_all('a', class_='btn-warning')
        links = []
        for i, btn in enumerate(buttons):
            onclick = btn.get('onclick')
            if onclick:
                clinic_id, clinic_title = self.parse_onclick(onclick)
                full_link = f'https://nobat.bmsu.ac.ir/New_ORA/NobatFuture/DisplayDoctorsListForClinicID?ID={clinic_id}&Title={clinic_title}'
                links.append(full_link)
                print(f"Doctor [{i + 1} / {len(buttons)}]")
        return links

    def extract_reserve_doctor_links_pages(self, soup):
        buttons = soup.find_all('a', class_='w-100')
        links = []
        for i, btn in enumerate(buttons):
            onclick = btn.get('onclick')
            if onclick:
                doctor_id, shift, doctor_name = self.parse_onclick(onclick)
                full_link = f'https://nobat.bmsu.ac.ir/New_ORA/NobatFuture/SelectReserveAppointmentPlan?Code={doctor_id}&DrFullname={shift}&ShiftName={doctor_name}'
                links.append(full_link)
                print(f"Reserve [{i + 1} / {len(buttons)}]")
        return links

    def _ensure_browser(self):
        if not self._playwright:
            self._playwright = sync_playwright().start()
        if not self._browser:
            self._browser = self._playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
        if not self._context:
            self._context = self._browser.new_context(
                user_agent=self.headers['user-agent'],
                viewport={'width': 1280, 'height': 720}
            )
            if self.cookies_for_playwright:
                self._context.add_cookies(self.cookies_for_playwright)

    def close_browser(self):
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()

    def click_button_with_playwright(self, url):
        self._ensure_browser()
        page = self._context.new_page()
        try:
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_load_state('networkidle')

            buttons = page.query_selector_all('.btn-warning')
            if not buttons:
                print(f"button not found at [{url}]")
                return page.content()

            first_button = buttons[0]
            try:
                with page.expect_navigation(wait_until='networkidle', timeout=30000):
                    first_button.click()
            except:
                first_button.click()

            page.wait_for_load_state('networkidle')
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            return page.content()

        except Exception as e:
            print(f"error while reading final page: {e}")
            try:
                return page.content()
            except:
                return f"<html><body>Error: {str(e)}</body></html>"
        finally:
            page.close()


    @staticmethod
    def sanitize_filename(name):

        if not name:
            return 'نامشخص'
        name = str(name).strip()

        name = re.sub(r'[\\/:*?"<>|]', '_', name)
        name = re.sub(r'\s+', ' ', name).strip()

        return name if name else 'نامشخص'

    def _save_doctor_csv_to_temp(self, doctor_records, file_name):
        safe_file_name = self.sanitize_filename(file_name)
        df = pd.DataFrame(doctor_records)
        temp_path = os.path.join(self.temp_dir, f'{safe_file_name}.csv')
        df.to_csv(temp_path, index=False, encoding='utf-8-sig')
        print(f"stored at temp: {temp_path}")
        return temp_path

    def build_results_by_specialty(self, all_doctors):
        if not all_doctors:
            print("files not exists.")
            return

        df_all = pd.DataFrame(all_doctors)

        if 'تخصص' not in df_all.columns:
            print("not found skills.")
            return

        df_all['تخصص'] = df_all['تخصص'].fillna('نامشخص')

        for specialty, group_df in df_all.groupby('تخصص'):
            safe_specialty = self.sanitize_filename(specialty)
            output_path = os.path.join(self.results_dir, f'{safe_specialty}.xlsx')
            group_df.to_excel(output_path, index=False, engine='openpyxl')
            print(f"final file write at: {output_path} ({len(group_df)} recorded)")


    def process_reservation_links_with_playwright(self, reservation_links):
        all_doctors = []
        clinic_doctors = []
        for i, link in enumerate(reservation_links, 1):
            print(f"Processing Link [{i} / {len(reservation_links)}]")
            try:
                html_content = self.click_button_with_playwright(link)
                soup = BeautifulSoup(html_content, 'html.parser')
                result = soup.select_one('body > div.container > div.row.col-lg-12.Asli.m-0')
                if not result:
                    continue
                cards = result.find_all('div', recursive=False)

                if cards:
                    file_name = None
                    for card in cards:

                        name_label = card.find('label', string=lambda x: x and 'نام پزشک' in x)
                        name_value = name_label.find_next('h6').get_text(strip=True) if name_label else None

                        specialty_label = card.find('label', string=lambda x: x and 'تخصص' in x)
                        specialty_value = specialty_label.find_next('h6').get_text(strip=True) if specialty_label else None

                        day_label = card.find('label', string=lambda x: x and 'روز' in x)
                        day_value = day_label.find_next('h6').get_text(strip=True) if day_label else None

                        date_label = card.find('label', string=lambda x: x and 'تاریخ' in x)
                        date_value = date_label.find_next('h6').get_text(strip=True) if date_label else None

                        shift_label = card.find('label', string=lambda x: x and 'شیفت' in x)
                        shift_value = shift_label.find_next('h6').get_text(strip=True) if shift_label else None

                        time_label = card.find('label', string=lambda x: x and 'ساعت' in x)
                        time_value = time_label.find_next('h6').get_text(strip=True) if time_label else None

                        reserve_link_tag = card.find('a', class_='btn btn-success')
                        reserve_link = reserve_link_tag['href'] if reserve_link_tag else None

                        doctor = {
                            'نام پزشک': name_value,
                            'تخصص': specialty_value,
                            'روز': day_value,
                            'تاریخ': date_value,
                            'شیفت': shift_value,
                            'ساعت': time_value,
                            'لینک رزرو': reserve_link
                        }

                        file_name = f'{name_value}_{specialty_value}_{shift_value}'

                        all_doctors.append(doctor)
                        clinic_doctors.append(doctor)

                    if clinic_doctors and file_name:
                        self._save_doctor_csv_to_temp(clinic_doctors, file_name)
                    clinic_doctors = []

            except Exception as e:
                print(f"error while reading final page: {e}")
                continue

        if all_doctors:
            df = pd.DataFrame(all_doctors)
            df.to_csv(os.path.join(self.temp_dir, 'doctors.csv'), index=False, encoding='utf-8-sig')

        return all_doctors

    def scrape_all_links(self):
        all_reserve_links = []
        all_doctors_overall = []
        try:
            soup = self.fetch_page()
            group_links = self.extract_clinic_group_links(soup)

            for i, group_link in enumerate(group_links, 1):
                print(f"Clinic [{i} / {len(group_links)}]")
                clinic_soup = self.fetch_page(group_link)
                clinic_doctors_links = self.extract_doctors_links_for_clinic_group_pages(clinic_soup)

                for clinic_doctor_link in clinic_doctors_links:
                    doctor_soup = self.fetch_page(clinic_doctor_link)
                    doctor_reserve_links = self.extract_reserve_doctor_links_pages(doctor_soup)
                    all_reserve_links.extend(doctor_reserve_links)

                doctors_from_clinic = self.process_reservation_links_with_playwright(doctor_reserve_links)
                if doctors_from_clinic:
                    all_doctors_overall.extend(doctors_from_clinic)

            self.build_results_by_specialty(all_doctors_overall)

            return all_reserve_links

        except Exception as e:
            print(f"Error: {e}")
            return all_reserve_links


def main():
    scraper = BaghiyyatollahClinicScraper(temp_dir='temp', results_dir='results')
    try:
        reserve_links = scraper.scrape_all_links()
        if reserve_links:
            print(f"\ncompleted!")
        else:
            print("no links found.")
    except Exception as e:
        print(f"error: {e}")
    finally:
        scraper.close_browser()


if __name__ == "__main__":
    main()