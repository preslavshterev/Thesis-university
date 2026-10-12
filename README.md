# Sales Analytics System

A sales analytics system built on a MySQL database of a retail business: data preparation (ETL), business analysis, customer segmentation, revenue forecasting and an interactive Streamlit dashboard with login and downloadable reports.

The data is synthetic. It is generated with Python from a simple demand model (growth trend, weekly and yearly seasonality, Black Friday), so the sales series has a pattern for the forecasting models to learn. It demonstrates the methods and the system, it does not describe a real company.

## Features

| Dashboard page - What it shows |

| Dashboard - Revenue, profit, order count and average order value 
| Sales - Monthly revenue, revenue by category and by store 
| Customers - RFM segments and K-Means clusters (cluster 0 has the highest average spend) 
| Products - Top and bottom products, seasonality, promotion effect 
| Inventory - Stock by store, stock value, low-stock items (adjustable threshold) 
| Forecast - Seasonal ARIMA forecast with 95% interval, backtest, model comparison over 8 rolling windows 
| Reports - Excel and CSV downloads that follow the sidebar filters 

Sidebar filters (period, stores, categories) apply to Dashboard, Sales, Products and Reports. Access is protected by a username and password. The dashboard uses a dark theme.

## Technology

Python, MySQL, SQL, SQLAlchemy, Pandas, NumPy, scikit-learn (K-Means), statsmodels (ARIMA, SARIMA, exponential smoothing), Faker, Streamlit, Plotly, openpyxl.

## Data

The generator creates two full years of sales (2024-10-01 to 2026-09-30) for 4 stores: about 25,000 orders, 1,000 customers and 100 products in 8 categories. A fixed random seed and a fixed end date make every run produce the same data.

Expected daily orders follow: base level x growth trend x month factor x weekday factor x event boost, with Poisson noise on top. The rules are in `demand_model.py`.

## Project structure

```
app.py                  - Dashboard entry point (login, filters, navigation)
auth.py                 - Login and password hashing
filters.py              - Sidebar filters
data_access.py          - Cached loading of the prepared data files
formatting.py           - Currency formatting
ui.py                   - Shared chart styles, colors and card helpers
style.css               - Dark theme styles (cards, hover effects)
.streamlit/config.toml  - Streamlit theme and settings
views/                  - One file per dashboard page

schema.sql              - Database schema
demand_model.py         - Demand rules: trend, seasonality, order times
generate_data.py        - Synthetic data generator (clears and refills the database)
queries.sql             - Analytical SQL queries
data_quality.py         - Data quality checks
feature_engineering.py  - Derived columns (dates, line totals, price tiers)
etl_pipeline.py         - Extract, transform, load into output/fact_sales.parquet

sales.py                - KPIs and revenue breakdowns
customers.py            - RFM scoring and K-Means segmentation
products.py             - Product rankings, seasonality, promotion effect
inventory.py            - Stock tables
forecasting.py          - Time series, ARIMA/SARIMA, rolling backtest, evaluation
reports.py              - Excel and CSV report building

export_tables.py        - Copies lookup tables from MySQL to output/
make_password_hash.py   - Creates the dashboard login settings
run_all.py              - Runs the whole pipeline and the tests
test_system.py          - End-to-end consistency tests
test_data_quality.py     -Tests for the data quality checks
```

Early exploration scripts (pandas_basics.py, numpy_analysis.py and similar) are kept for reference.

## Setup

1. Install Python 3.10 or newer and MySQL.
2. Create and activate a virtual environment, then install the packages:
   
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt

   
3. Create the database: run `schema.sql` in MySQL (for example in MySQL Workbench).
4. Create a `.env` file in the project root:
   
   DB_USER=your_mysql_user
   DB_PASSWORD=your_mysql_password
   DB_HOST=localhost
   DB_NAME=diploma_project

   
5. Create the dashboard login and add the two printed lines to `.env`:
   
   python make_password_hash.py
   
6. Fill the database with synthetic data:
   
   python generate_data.py
   

## Run

Build all prepared files and run the tests:


'python run_all.py'


To clear the database, generate new data and rebuild everything in one step:


'python run_all.py --regenerate-data'


Start the dashboard:


'streamlit run app.py'


The dashboard reads the files in `output/`, not the database. After the database data changes, run `python run_all.py` again. The first visit to the Forecast page takes about a minute while the models are fitted; the result is cached afterwards.

Run only the tests:


'python test_system.py'


The tests check that totals agree across all layers (database, prepared files, KPIs, breakdowns, reports), that the filters and the password hashing work, and that the prepared files match MySQL when the database is reachable.

## Known limitations

- The data is synthetic. The trend and seasonality are built into the generator, so the results show that the methods work, not how a real business behaves.
- Daily revenue still contains a lot of random noise, so even the best forecasting model has a sizeable error. Weekly seasonality is captured by SARIMA, individual days remain hard to predict.
- In the synthetic data, a customer's total spend follows the number of orders almost linearly, so K-Means clusters differ mostly by activity level and recency.
- Customer segments (RFM, K-Means) are calculated on the whole history and are not affected by the filters.
- Inventory is a snapshot without dates, so it has no period filter.
- Login supports one user and has no lockout or HTTPS. It is suitable for a demonstration, not for public hosting.
- Values such as the number of clusters (`OPTIMAL_K`), the ARIMA differencing order and the seasonal period were chosen for the current data and must be reviewed if the data changes.
- The dashboard styles rely on Streamlit element names, so they may need small adjustments after a major Streamlit upgrade.