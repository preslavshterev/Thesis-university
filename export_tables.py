import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "diploma_project")

OUTPUT_DIR = "output"
TABLES = ["stores", "promotions", "inventory", "products"]

if __name__ == "__main__":
    engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for table in TABLES:
        df = pd.read_sql(f"SELECT * FROM {table}", engine)
        df.to_csv(f"{OUTPUT_DIR}/{table}.csv", index=False)
        print(f"Saved {len(df)} rows to {OUTPUT_DIR}/{table}.csv")