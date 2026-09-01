# Online Supermarket: Market Basket Analysis & Customer Segmentation

An end-to-end data mining project on a 1M-row online supermarket transaction dataset, combining temporal shopping-pattern analysis, a **from-scratch Apriori implementation**, association rule mining, sequential purchase-order analysis, cross-section merchandising suggestions, and customer segmentation with K-Means.

## Overview

Working from raw transaction-level data (`Customer_ID`, `Transaction_ID`, `Product`, `Section`, `Day_of_Week`, `Hour`, `Order`, `Last_Purchase`), this project answers five analytical questions about shopping behavior and turns them into concrete, actionable retail recommendations.

## Analysis

**Q1 — Temporal Shopping Patterns**
- Purchases are split into weekend vs. weekday and into three daily time periods (00–07, 08–15, 16–23)
- ~50% of all purchases happen on the two weekend days
- A section-vs-time-period heatmap shows category-specific timing (e.g. eggs & dairy peak in the 08–15 window)
- Customer counts and average basket size are compared across weekend/weekday and time period

**Q2a — Association Rule Mining (Apriori)**
- A **custom Apriori algorithm** is implemented from scratch (level-wise candidate generation + support pruning) and run on the full transaction set
- Fresh fruits (55.6%) and fresh vegetables (44.4%) are the most frequent items, appearing in over half of all baskets
- `mlxtend`'s Apriori + `association_rules` is then used to mine rules at ≥2% support and ≥70% confidence, ranked by confidence/lift
- Example: customers who buy {fresh vegetables, yogurt, fresh fruits} buy fresh vegetables 90.2% of the time — a strong basis for co-location/promotion

**Q2b — Sequential (Ordered) Purchase Rules**
- Uses each transaction's item `Order` to mine directional "A is bought before B" rules (excluding self-pairs), filtered at ≥70% confidence
- Example: customers who buy fresh herbs go on to buy fresh vegetables with very high likelihood — useful for in-store product placement sequencing

**Q3 — Best-Sellers vs. Low-Sellers Bundling**
- Identifies the top-20 and bottom-20 selling products
- At the extreme tails, no association rules connect best- and low-sellers (confidence threshold is too strict for rare items)
- Widening the low-seller band to the 45th–65th percentile surfaces **granola** as a low-seller that co-occurs strongly with fresh fruit — a candidate for a discount bundle to boost visibility

**Q4 — Section Merge / Cross-Merchandising Suggestions**
- Aggregates association rules by product `Section` to score which department pairs co-occur most often in purchase baskets
- Top suggestion: co-locating fruits & vegetables with dairy

**Q5 — Customer Segmentation (K-Means)**
- Customer-level features: transaction count, product count, and recency statistics (`Last_Purchase` mean/max/min)
- Cluster count selected via the Elbow method and Silhouette score (`MiniBatchKMeans`, scanned over k=2–8)
- Three resulting segments:
  - **Low-Value** — few transactions, long time since last purchase
  - **Regular** — moderate purchase volume, recently active
  - **Loyal** — highest transaction count, highest volume, most engaged

## Tech Stack

- Python, pandas, NumPy
- mlxtend (Apriori, association rules, transaction encoding)
- scikit-learn (K-Means / MiniBatchKMeans, StandardScaler, silhouette score)
- matplotlib

## Project Structure

```
.
├── notebook.ipynb    # Full analysis: Q1 (temporal patterns) → Q2 (association rules) →
│                      #   Q3 (bundling) → Q4 (section merges) → Q5 (customer segmentation)
└── Online_SuperMarket.csv   # Dataset (not included — see Dataset section)
```

## How to Run

1. Install dependencies:
   ```bash
   pip install pandas numpy matplotlib scikit-learn mlxtend
   ```
2. Download `dataset.zip` and unzip it, then update `INPUT_FILE` to point to your local copy of the dataset.
3. Run the notebook top to bottom.

## Dataset

Online supermarket transaction log (~1M rows) — update this section with the dataset's source/link if it's publicly available, or note that it's private/coursework data.

## Contact
Feel free to reach out if you have questions or feedback! You can find me on Telegram: @AmirDevil

## License
This project is licensed under the MIT License. By contributing, you agree that your contributions will be released under the same license.

