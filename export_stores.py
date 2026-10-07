import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "diploma_project")

OUTPUT_PATH = "output/stores.csv"

if __name__ == "__main__":
    engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")
    stores = pd.read_sql("SELECT * FROM stores", engine)

    os.makedirs("output", exist_ok=True)
    stores.to_csv(OUTPUT_PATH, index=False)
    print(f"Saved {len(stores)} stores to {OUTPUT_PATH}")