# Sales Analytics System

A sales analytics system built on a MySQL database of a retail business: data preparation (ETL), business analysis, customer segmentation, revenue forecasting and an interactive Streamlit dashboard with login and downloadable reports.

The data is synthetic (generated with Python and Faker). It demonstrates the methods and the system, it does not describe a real company. Because the generated daily revenue has no trend or seasonality, the forecasting models can only predict a roughly average level.

## Features

| Dashboard page | What it shows |
-----------------------------------
| Dashboard - Revenue, profit, order count and average order value |
| Sales - Monthly revenue, revenue by category and by store |
| Customers - RFM segments and K-Means clusters |
| Products - Top and bottom products, seasonality, promotion effect |
| Inventory - Stock by store, stock value, low-stock items (adjustable threshold) |
| Forecast - ARIMA forecast with 95% interval, backtest, model comparison |
| Reports - Excel and CSV downloads that follow the sidebar filters |

Sidebar filters (period, stores, categories) apply to Dashboard, Sales, Products and Reports. Access is protected by a username and password.

## Technology

Python, MySQL, SQL, SQLAlchemy, Pandas, NumPy, scikit-learn (K-Means), statsmodels (ARIMA, exponential smoothing), Faker, Streamlit, Plotly, openpyxl.

## Project structure


app.py                  Dashboard entry point (login, filters, navigation)
auth.py                 Login and password hashing
filters.py              Sidebar filters
data_access.py          Cached loading of the prepared data files
formatting.py           Currency formatting
views/                  One file per dashboard page

schema.sql              Database schema
generate_data.py        Synthetic data generator (clears and refills the database)
queries.sql             Analytical SQL queries
data_quality.py         Data quality checks
feature_engineering.py  Derived columns (dates, line totals, price tiers)
etl_pipeline.py         Extract, transform, load into output/fact_sales.parquet

sales.py                KPIs and revenue breakdowns
customers.py            RFM scoring and K-Means segmentation
products.py             Product rankings, seasonality, promotion effect
inventory.py            Stock tables
forecasting.py          Time series, ARIMA, evaluation
reports.py              Excel and CSV report building

export_tables.py        Copies lookup tables from MySQL to output/
make_password_hash.py   Creates the dashboard login settings
run_all.py              Runs the whole pipeline and the tests
test_system.py          End-to-end consistency tests
test_data_quality.py    Tests for the data quality checks


Early exploration scripts (pandas_basics.py, numpy_analysis.py and similar) are kept for reference.

## Setup

1. Install Python 3.11 or newer and MySQL.
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


python run_all.py


Start the dashboard:


streamlit run app.py


The dashboard reads the files in `output/`, not the database. After the database data changes, run `python run_all.py` again.

Run only the tests:


python test_system.py


## Known limitations

- The data is synthetic and random, so charts show no real business trend and the forecast is nearly flat.
- The first month in the monthly revenue chart is incomplete because the data starts at the end of that month.
- Customer segments (RFM, K-Means) are calculated on the whole history and are not affected by the filters.
- Inventory is a snapshot without dates, so it has no period filter.
- Login supports one user and has no lockout or HTTPS. It is suitable for a demonstration, not for public hosting.
- Values such as the number of clusters (`OPTIMAL_K`) and the ARIMA differencing order were chosen for the current data and must be reviewed if the data changes.