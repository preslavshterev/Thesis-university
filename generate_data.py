"""Generate synthetic data for the diploma_project database."""

import os
import random
from datetime import date, datetime, timedelta

import numpy as np
from dotenv import load_dotenv
from faker import Faker
from sqlalchemy import create_engine, text

from demand_model import category_factor, draw_order_counts, random_order_time

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "diploma_project")

N_CUSTOMERS = 1000
N_PRODUCTS = 100
N_DAYS = 730
DATA_END = date(2026, 9, 30)
DATA_START = DATA_END - timedelta(days=N_DAYS - 1)
RETURN_RATE = 0.03
CHURN_SHARE = 0.30
PENDING_WINDOW_DAYS = 3

STORE_SHARES = [0.35, 0.25, 0.22, 0.18]
ORDER_STATUSES = ["completed", "cancelled", "pending"]
OLD_STATUS_WEIGHTS = [0.92, 0.08, 0.00]
RECENT_STATUS_WEIGHTS = [0.70, 0.05, 0.25]
ITEMS_PER_ORDER_P = [0.20, 0.35, 0.28, 0.12, 0.05]
QUANTITY_P = [0.70, 0.25, 0.05]

SEED = 42
random.seed(SEED)
Faker.seed(SEED)
rng = np.random.default_rng(SEED)
fake = Faker()

BULK_CHUNK = 5000


def bulk_insert(conn, sql, rows):
    for start in range(0, len(rows), BULK_CHUNK):
        conn.execute(text(sql), rows[start:start + BULK_CHUNK])

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")

CATEGORY_NAMES = [
    "Shoes", "Clothing", "Accessories", "Electronics",
    "Home Goods", "Sports Equipment", "Cosmetics", "Toys"
]

STORES = [
    ("Downtown Store", "Sofia"),
    ("Mladost Store", "Sofia"),
    ("Plovdiv Store", "Plovdiv"),
    ("Varna Store", "Varna"),
]

BULGARIAN_CITIES = [
    "Sofia", "Plovdiv", "Varna", "Burgas", "Ruse",
    "Stara Zagora", "Pleven", "Sliven", "Dobrich", "Shumen",
]

BULGARIAN_MALE_FIRST_NAMES = [
    "Ivan", "Georgi", "Dimitar", "Nikolay", "Petar", "Stoyan", "Hristo",
    "Aleksandar", "Todor", "Vasil", "Stefan", "Angel", "Yordan", "Boris",
    "Emil", "Kiril", "Martin", "Plamen", "Rumen", "Zhivko",
]

BULGARIAN_FEMALE_FIRST_NAMES = [
    "Maria", "Elena", "Petya", "Ivanka", "Yana", "Kristina", "Desislava",
    "Vasilka", "Rositsa", "Nadezhda", "Silvia", "Teodora", "Milena",
    "Antoaneta", "Galina", "Radostina", "Snezhana", "Tsvetelina", "Valeria",
    "Zornitsa",
]

BULGARIAN_LAST_NAMES = [
    "Ivanov", "Ivanova", "Georgiev", "Georgieva", "Dimitrov", "Dimitrova",
    "Petrov", "Petrova", "Stoyanov", "Stoyanova", "Hristov", "Hristova",
    "Angelov", "Angelova", "Todorov", "Todorova", "Vasilev", "Vasileva",
    "Stefanov", "Stefanova", "Yordanov", "Yordanova", "Borisov", "Borisova",
    "Kirilov", "Kirilova", "Marinov", "Marinova", "Nikolov", "Nikolova",
]

def random_bulgarian_phone():
    prefix = random.choice(["87", "88", "89", "98", "99"])
    part1 = random.randint(100, 999)
    part2 = random.randint(1000, 9999)
    return f"+359 {prefix} {part1} {part2}"

def random_bulgarian_name():
    if random.random() < 0.5:
        first = random.choice(BULGARIAN_MALE_FIRST_NAMES)
        last = random.choice([n for n in BULGARIAN_LAST_NAMES if not n.endswith("a")])
    else:
        first = random.choice(BULGARIAN_FEMALE_FIRST_NAMES)
        last = random.choice([n for n in BULGARIAN_LAST_NAMES if n.endswith("a")])
    return first, last

PRODUCT_TEMPLATES = {
    "Shoes": ["Sneakers", "Running Shoes", "Boots", "Sandals", "Dress Shoes"],
    "Clothing": ["T-Shirt", "Pants", "Jacket", "Dress", "Sweater"],
    "Accessories": ["Bag", "Belt", "Sunglasses", "Hat", "Wallet"],
    "Electronics": ["Headphones", "Smart Watch", "Powerbank", "USB-C Cable", "Keyboard"],
    "Home Goods": ["Frying Pan", "Cup Set", "Kitchen Knife", "Blanket", "Candle Holder"],
    "Sports Equipment": ["Yoga Mat", "Dumbbells", "Ball", "Jump Rope", "Water Bottle"],
    "Cosmetics": ["Face Cream", "Perfume", "Shampoo", "Shower Gel", "Lip Balm"],
    "Toys": ["Teddy Bear", "Building Blocks", "Puzzle", "Toy Car", "Board Game"],
}

PAYMENT_METHODS = ["card", "cash", "bank_transfer"]

POSITIONS = ["Sales Associate", "Cashier", "Shift Manager"]

RETURN_REASONS = [
    "Defective product", "Wrong size", "Did not meet expectations",
    "Customer changed mind", "Late delivery"
]

TABLES_IN_DELETE_ORDER = [
    "returns", "promotions", "inventory", "payments", "order_items",
    "orders", "products", "employees", "stores", "categories", "customers",
]

with engine.begin() as conn:
    print("Clearing existing data...")

    conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    for table in TABLES_IN_DELETE_ORDER:
        conn.execute(text(f"TRUNCATE TABLE {table}"))
    conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))

    print("Creating categories, stores, employees, and products...")

    category_ids = {}
    for name in CATEGORY_NAMES:
        result = conn.execute(text(
            "INSERT INTO categories (category_name) VALUES (:name)"), {"name": name})
        category_ids[name] = result.lastrowid

    store_ids = []
    for store_name, city in STORES:
        result = conn.execute(text(
            "INSERT INTO stores (store_name, city) VALUES (:s, :c)"),
            {"s": store_name, "c": city})
        store_ids.append(result.lastrowid)

    employees_by_store = {store_id: [] for store_id in store_ids}
    for store_id in store_ids:
        for _ in range(random.randint(3, 5)):
            first, last = random_bulgarian_name()
            hire_date = DATA_END - timedelta(days=int(rng.integers(60, 1095)))

            result = conn.execute(text("""
                INSERT INTO employees (first_name, last_name, store_id, position, hire_date)
                VALUES (:fn, :ln, :sid, :pos, :hd)
            """), {"fn": first, "ln": last, "sid": store_id,
                    "pos": random.choice(POSITIONS), "hd": hire_date})

            employees_by_store[store_id].append(result.lastrowid)

    product_ids = []
    product_prices = {}
    product_categories = []
    for _ in range(N_PRODUCTS):
        category_name = random.choice(CATEGORY_NAMES)
        base_name = random.choice(PRODUCT_TEMPLATES[category_name])
        product_name = f"{base_name} {fake.word().capitalize()}"

        cost = round(random.uniform(5, 150), 2)
        price = round(cost * random.uniform(1.3, 2.2), 2)

        result = conn.execute(text("""
            INSERT INTO products (product_name, category_id, price, cost)
            VALUES (:pn, :cid, :price, :cost)
        """), {"pn": product_name, "cid": category_ids[category_name],
                "price": price, "cost": cost})

        pid = result.lastrowid
        product_ids.append(pid)
        product_prices[pid] = price
        product_categories.append(category_name)

    print(f"Generating {N_CUSTOMERS} customers...")

    customer_rows = []
    registration = []
    active_until = []
    for i in range(1, N_CUSTOMERS + 1):
        first, last = random_bulgarian_name()

        reg_date = DATA_START - timedelta(days=365) + timedelta(
            days=int(rng.integers(0, (DATA_END - DATA_START).days + 335)))

        if rng.random() < CHURN_SHARE:
            last_active = reg_date + timedelta(days=int(rng.integers(60, 450)))
        else:
            last_active = DATA_END

        registration.append(reg_date)
        active_until.append(last_active)

        customer_rows.append({
            "cid": i, "fn": first, "ln": last,
            "email": f"{first.lower()}.{last.lower()}{i}@example.com",
            "phone": random_bulgarian_phone(),
            "city": random.choice(BULGARIAN_CITIES),
            "rd": reg_date,
        })

    bulk_insert(conn, """
        INSERT INTO customers (customer_id, first_name, last_name, email, phone, city, registration_date)
        VALUES (:cid, :fn, :ln, :email, :phone, :city, :rd)
    """, customer_rows)

    registration = np.array(registration, dtype="datetime64[D]")
    active_until = np.array(active_until, dtype="datetime64[D]")

    customer_activity = np.clip(rng.lognormal(mean=0.0, sigma=0.8, size=N_CUSTOMERS), 0.1, 4.0)

    product_popularity = rng.lognormal(mean=0.0, sigma=0.7, size=N_PRODUCTS)
    product_weights_by_month = {}
    for month in range(1, 13):
        weights = product_popularity * np.array(
            [category_factor(c, month) for c in product_categories])
        product_weights_by_month[month] = weights / weights.sum()

    days = [DATA_START + timedelta(days=i) for i in range(N_DAYS)]
    order_counts = draw_order_counts(rng, days)

    print(f"Generating {int(order_counts.sum())} orders over {N_DAYS} days...")

    order_rows, item_rows, payment_rows = [], [], []
    item_order_date = {}

    order_id = 0
    item_id = 0

    for day, n_orders in zip(days, order_counts):
        if n_orders == 0:
            continue

        eligible = np.flatnonzero(
            (registration <= np.datetime64(day)) & (active_until >= np.datetime64(day)))

        weights = customer_activity[eligible]
        buyers = rng.choice(eligible, size=n_orders, p=weights / weights.sum())
        is_recent = (DATA_END - day).days < PENDING_WINDOW_DAYS

        for buyer in buyers:
            order_id += 1

            order_date = random_order_time(rng, day)
            store_id = int(rng.choice(store_ids, p=STORE_SHARES))
            employee_id = (int(rng.choice(employees_by_store[store_id]))
                           if rng.random() > 0.05 else None)

            status_weights = RECENT_STATUS_WEIGHTS if is_recent else OLD_STATUS_WEIGHTS
            status = str(rng.choice(ORDER_STATUSES, p=status_weights))

            order_rows.append({"oid": order_id, "cid": int(buyer) + 1, "sid": store_id,
                               "eid": employee_id, "od": order_date, "st": status})

            n_items = int(rng.choice([1, 2, 3, 4, 5], p=ITEMS_PER_ORDER_P))
            chosen = rng.choice(N_PRODUCTS, size=n_items, replace=False,
                                p=product_weights_by_month[day.month])
            order_total = 0.0

            for product_index in chosen:
                item_id += 1

                pid = product_ids[int(product_index)]
                quantity = int(rng.choice([1, 2, 3], p=QUANTITY_P))
                unit_price = product_prices[pid]

                item_rows.append({"iid": item_id, "oid": order_id, "pid": pid,
                                  "q": quantity, "up": unit_price})
                item_order_date[item_id] = order_date

                order_total += quantity * unit_price

            if status != "pending":
                payment_rows.append({
                    "oid": order_id,
                    "pd": order_date + timedelta(hours=int(rng.integers(0, 49))),
                    "amt": round(order_total, 2),
                    "pm": random.choice(PAYMENT_METHODS)})

    bulk_insert(conn, """
        INSERT INTO orders (order_id, customer_id, store_id, employee_id, order_date, status)
        VALUES (:oid, :cid, :sid, :eid, :od, :st)
    """, order_rows)

    bulk_insert(conn, """
        INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price)
        VALUES (:iid, :oid, :pid, :q, :up)
    """, item_rows)

    print("Generating payments...")

    bulk_insert(conn, """
        INSERT INTO payments (order_id, payment_date, amount, payment_method)
        VALUES (:oid, :pd, :amt, :pm)
    """, payment_rows)

    print("Generating inventory by store...")

    inventory_rows = [
        {"pid": pid, "sid": sid, "qty": random.randint(0, 200), "lu": datetime.now()}
        for pid in product_ids for sid in store_ids]

    bulk_insert(conn, """
        INSERT INTO inventory (product_id, store_id, quantity_available, last_updated)
        VALUES (:pid, :sid, :qty, :lu)
    """, inventory_rows)

    print("Generating promotions...")

    promo_rows = []
    for pid in random.sample(product_ids, k=int(N_PRODUCTS * 0.2)):
        start = DATA_END - timedelta(days=int(rng.integers(0, 180)))

        end = start + timedelta(days=random.randint(7, 30))
        promo_rows.append({"pid": pid, "disc": round(random.uniform(5, 40), 2),
                           "sd": start, "ed": end})

    bulk_insert(conn, """
        INSERT INTO promotions (product_id, discount_percent, start_date, end_date)
        VALUES (:pid, :disc, :sd, :ed)
    """, promo_rows)

    print("Generating product returns...")

    items_by_id = {row["iid"]: row for row in item_rows}
    n_returns = int(len(item_rows) * RETURN_RATE)
    return_rows = []

    for item_id in rng.choice(list(items_by_id), size=n_returns, replace=False):
        item = items_by_id[int(item_id)]

        return_date = min(
            item_order_date[item["iid"]].date() + timedelta(days=int(rng.integers(1, 31))),
            DATA_END)

        return_rows.append({"oid": item["iid"], "rd": return_date,
                            "reason": random.choice(RETURN_REASONS),
                            "amt": round(item["q"] * item["up"], 2)})

    bulk_insert(conn, """
        INSERT INTO returns (order_item_id, return_date, reason, refund_amount)
        VALUES (:oid, :rd, :reason, :amt)
    """, return_rows)

print("\nDone! The database has been populated successfully.")