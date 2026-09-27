import pandas as pd

FACT_SALES_PATH = "output/fact_sales.parquet"


# =====================================================================
# 1. Raw RFM metrics
# =====================================================================

def calculate_rfm(completed):
    """Compute raw Recency (days), Frequency (order count) and Monetary
    (total revenue) per customer."""
    completed = completed.copy()
    completed["order_date"] = pd.to_datetime(completed["order_date"])

    snapshot_date = completed["order_date"].max() + pd.Timedelta(days=1)

    rfm = completed.groupby("customer_id").agg(
        recency_days=("order_date", lambda dates: (snapshot_date - dates.max()).days),
        frequency=("order_id", "nunique"),
        monetary=("line_total", "sum"),
    ).reset_index()

    return rfm


# =====================================================================
# 2. Scoring via quintiles (1-5)
# =====================================================================

def score_rfm(rfm):
    """Score each RFM metric into quintiles 1-5. Recency is reversed
    (fewer days = higher score); Frequency and Monetary are direct
    (higher value = higher score). rank(method="first") breaks ties so
    qcut always has unique bin edges."""
    rfm = rfm.copy()

    rfm["R_score"] = pd.qcut(
        rfm["recency_days"].rank(method="first"), q=5, labels=[5, 4, 3, 2, 1]
    ).astype(int)
    rfm["F_score"] = pd.qcut(
        rfm["frequency"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    rfm["M_score"] = pd.qcut(
        rfm["monetary"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]
    ).astype(int)

    return rfm


# =====================================================================
# 3. Segment assignment
# =====================================================================

def assign_segment(row):
    r, f, m = row["R_score"], row["F_score"], row["M_score"]

    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    elif f >= 4 and m >= 3:
        return "Loyal Customers"
    elif r >= 4 and f <= 2:
        return "New Customers"
    elif r <= 2 and f >= 3:
        return "At Risk"
    elif r <= 2 and f <= 2:
        return "Lost"
    else:
        return "Need Attention"


def add_segments(rfm):
    rfm = rfm.copy()
    rfm["segment"] = rfm.apply(assign_segment, axis=1)
    return rfm


# =====================================================================
# 4. Full pipeline
# =====================================================================

def build_rfm_table(fact_sales):
    completed = fact_sales[fact_sales["status"] == "completed"]
    rfm = calculate_rfm(completed)
    rfm = score_rfm(rfm)
    rfm = add_segments(rfm)
    return rfm


if __name__ == "__main__":
    fact_sales = pd.read_parquet(FACT_SALES_PATH)

    rfm = build_rfm_table(fact_sales)

    print("=== RFM TABLE (first 10 customers) ===")
    print(rfm.head(10))

    print("\n=== CUSTOMER COUNT PER SEGMENT ===")
    print(rfm["segment"].value_counts())

    print("\n=== AVERAGE MONETARY VALUE PER SEGMENT ===")
    print(rfm.groupby("segment")["monetary"].mean().sort_values(ascending=False))

    rfm.to_csv("output/rfm_table.csv", index=False)
    print("\nSaved RFM table to output/rfm_table.csv")