import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

RFM_TABLE_PATH = "output/rfm_table.csv"
OUTPUT_DIR = "output"


OPTIMAL_K = 4


# =====================================================================
# 1. Standardization
# =====================================================================

def scale_features(rfm):
    """Standardize recency/frequency/monetary so K-Means treats them
    with equal weight regardless of their original scale."""
    features = rfm[["recency_days", "frequency", "monetary"]]
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)
    return scaled


# =====================================================================
# 2. Elbow method
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
# 3. Final clustering
# =====================================================================

def fit_kmeans(scaled_features, k):
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(scaled_features)
    return labels


# =====================================================================
# 4. Cluster description
# =====================================================================

def describe_clusters(rfm):
    return rfm.groupby("cluster")[["recency_days", "frequency", "monetary"]].mean()


if __name__ == "__main__":
    rfm = pd.read_csv(RFM_TABLE_PATH)

    scaled_features = scale_features(rfm)

    print("=== ELBOW METHOD ===")
    k_values, inertias = run_elbow_method(scaled_features)
    for k, inertia in zip(k_values, inertias):
        print(f"k={k}: inertia={inertia:.2f}")
    plot_elbow(k_values, inertias, f"{OUTPUT_DIR}/elbow_method.png")
    print(f"Elbow plot saved to {OUTPUT_DIR}/elbow_method.png -- inspect it to confirm OPTIMAL_K.")

    print(f"\n=== FINAL CLUSTERING (k={OPTIMAL_K}) ===")
    rfm["cluster"] = fit_kmeans(scaled_features, OPTIMAL_K)

    print("\n=== CLUSTER SIZES ===")
    print(rfm["cluster"].value_counts().sort_index())

    print("\n=== CLUSTER PROFILES (mean recency/frequency/monetary) ===")
    print(describe_clusters(rfm))

    print("\n=== COMPARISON: K-Means cluster vs RFM segment ===")
    print(pd.crosstab(rfm["cluster"], rfm["segment"]))

    rfm.to_csv(f"{OUTPUT_DIR}/rfm_table_with_clusters.csv", index=False)
    print(f"\nSaved {OUTPUT_DIR}/rfm_table_with_clusters.csv")