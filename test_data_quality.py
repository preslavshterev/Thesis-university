import pandas as pd

from data_quality import check_duplicates, check_invalid_records


def test_data_quality_catches_issues():
    customers = pd.DataFrame({
        "customer_id": [1, 2, 3],
        "email": ["a@test.com", "a@test.com", "b@test.com"],  # intentional duplicate
    })

    products = pd.DataFrame({
        "product_id": [1, 2],
        "price": [-10.0, 50.0],   # intentional negative price
        "cost": [5.0, 20.0],
    })

    orders = pd.DataFrame({
        "order_id": [1],
        "order_date": [pd.Timestamp.now() + pd.Timedelta(days=30)],  # intentional future date
        "status": ["completed"],
    })

    order_items = pd.DataFrame({
        "order_item_id": [1],
        "quantity": [-2],          # intentional invalid quantity
        "unit_price": [10.0],
    })

    dup_customers = check_duplicates(customers, "customers", subset=["email"])
    assert len(dup_customers) == 2, "Failed to catch duplicate emails"

    issues = check_invalid_records(customers, products, orders, order_items)
    assert len(issues["negative_prices"]) == 1, "Failed to catch negative price"
    assert len(issues["future_orders"]) == 1, "Failed to catch future order"
    assert len(issues["invalid_quantity"]) == 1, "Failed to catch invalid quantity"

    print("All data quality checks correctly caught the injected issues.")


if __name__ == "__main__":
    test_data_quality_catches_issues()