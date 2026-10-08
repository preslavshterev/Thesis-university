import pandas as pd


def build_inventory_table(inventory, products, stores, categories):
    table = (
        inventory[["product_id", "store_id", "quantity_available"]]
        .merge(products[["product_id", "product_name", "category_id", "cost"]], on="product_id")
        .merge(stores[["store_id", "store_name"]], on="store_id")
        .merge(categories[["category_id", "category_name"]], on="category_id")
    )
    table["stock_value"] = table["quantity_available"] * table["cost"]
    return table


def stock_by_store(table):
    return (
        table.groupby("store_name")
        .agg(units=("quantity_available", "sum"), stock_value=("stock_value", "sum"))
        .sort_values("units", ascending=False)
        .reset_index()
    )


def stock_value_by_category(table):
    return (
        table.groupby("category_name")["stock_value"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )


def low_stock_items(table, threshold):
    low = table[table["quantity_available"] <= threshold]
    columns = ["product_name", "store_name", "category_name", "quantity_available"]
    return low[columns].sort_values("quantity_available")