import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "diploma_project")

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")

# зареждане на цяла таблица в DataFrame
orders_df = pd.read_sql("SELECT * FROM orders", engine)

print(orders_df.head())
print("\nRow and column count:", orders_df.shape)
print("\nColumn data types:")
print(orders_df.dtypes)
print("\nSummary statistics:")
print(orders_df.describe())


customers_df = pd.read_sql("SELECT * FROM customers", engine)
products_df = pd.read_sql("SELECT * FROM products", engine)
order_items_df = pd.read_sql("SELECT * FROM order_items", engine)

print(customers_df.head())
print(products_df.head())
print(order_items_df.head())