import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

FACT_SALES_PATH = "output/fact_sales.parquet"
OUTPUT_DIR = "output"

# Set this after inspecting the elbow plot (output/elbow_method.png).
OPTIMAL_K = 4


# =====================================================================
# 1. RFM metrics
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
# 2. RFM scoring via quintiles (1-5)
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
# 3. RFM segment assignment
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


def build_rfm_table(fact_sales):
    completed = fact_sales[fact_sales["status"] == "completed"]
    rfm = calculate_rfm(completed)
    rfm = score_rfm(rfm)
    rfm = add_segments(rfm)
    return rfm


# =====================================================================
# 4. K-Means: standardization
# =====================================================================

def scale_features(rfm):
    """Standardize recency/frequency/monetary so K-Means treats them
    with equal weight regardless of their original scale."""
    features = rfm[["recency_days", "frequency", "monetary"]]
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)
    return scaled


# =====================================================================
# 5. K-Means: elbow method
# =====================================================================

def run_elbow_method(scaled_features, k_range=range(1, 11)):
    """Fit K-Means for each k in k_range and return the list of inertia
    values, to help visually pick the "elbow" point."""
    inertias = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(scaled_features)
        inertias.append(km.inertia_)
    return list(k_range), inertias


def plot_elbow(k_values, inertias, output_path):
    plt.figure(figsize=(8, 5))
    plt.plot(k_values, inertias, marker="o")
    plt.xlabel("Number of clusters (k)")
    plt.ylabel("Inertia")
    plt.title("Elbow method")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


# =====================================================================
# 6. K-Means: final clustering
# =====================================================================

def fit_kmeans(scaled_features, k):
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(scaled_features)
    return labels


def describe_clusters(rfm):
    return rfm.groupby("cluster")[["recency_days", "frequency", "monetary"]].mean()


if __name__ == "__main__":
    fact_sales = pd.read_parquet(FACT_SALES_PATH)

    print("=== BUILDING RFM TABLE ===")
    rfm = build_rfm_table(fact_sales)
    print(rfm.head(10))

    print("\n=== CUSTOMER COUNT PER SEGMENT ===")
    print(rfm["segment"].value_counts())

    rfm.to_csv(f"{OUTPUT_DIR}/rfm_table.csv", index=False)
    print(f"\nSaved RFM table to {OUTPUT_DIR}/rfm_table.csv")

    scaled_features = scale_features(rfm)

    print("\n=== ELBOW METHOD ===")
    k_values, inertias = run_elbow_method(scaled_features)
    for k, inertia in zip(k_values, inertias):
        print(f"k={k}: inertia={inertia:.2f}")
    plot_elbow(k_values, inertias, f"{OUTPUT_DIR}/elbow_method.png")
    print(f"Elbow plot saved to {OUTPUT_DIR}/elbow_method.png -- inspect it to confirm OPTIMAL_K.")

    print(f"\n=== FINAL CLUSTERING (k={OPTIMAL_K}) ===")
    rfm["cluster"] = fit_kmeans(scaled_features, OPTIMAL_K)

    print("\n=== CLUSTER PROFILES (mean recency/frequency/monetary) ===")
    print(describe_clusters(rfm))

    print("\n=== COMPARISON: K-Means cluster vs RFM segment ===")
    print(pd.crosstab(rfm["cluster"], rfm["segment"]))

    rfm.to_csv(f"{OUTPUT_DIR}/rfm_table_with_clusters.csv", index=False)
    print(f"\nSaved {OUTPUT_DIR}/rfm_table_with_clusters.csv")