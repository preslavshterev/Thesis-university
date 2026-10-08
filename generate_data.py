"""
Generate realistic test data for the diploma_project database.
Safe to re-run: clears existing data first (in FK-safe order), then repopulates.
"""

import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from faker import Faker
from sqlalchemy import create_engine, text

# =====================================================================
# 0. SETTINGS — loaded from .env
# =====================================================================
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "diploma_project")

N_CUSTOMERS = 200
N_PRODUCTS = 100
N_ORDERS = 800
MONTHS_BACK = 24          # generate orders across the last 24 months
RETURN_RATE = 0.03        # 3% of order_items get a return

fake = Faker()
random.seed(42)           # reproducible results on re-run

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")

# =====================================================================
# 1. Fixed reference data
# =====================================================================
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
    """Returns a plausible Bulgarian mobile number, e.g. +359 88 123 4567."""
    prefix = random.choice(["87", "88", "89", "98", "99"])
    part1 = random.randint(100, 999)
    part2 = random.randint(1000, 9999)
    return f"+359 {prefix} {part1} {part2}"

def random_bulgarian_name():
    """Returns (first_name, last_name) as a matching-gender pair."""
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
ORDER_STATUSES_WEIGHTED = ["completed"] * 85 + ["cancelled"] * 10 + ["pending"] * 5

POSITIONS = ["Sales Associate", "Cashier", "Shift Manager"]

RETURN_REASONS = [
    "Defective product", "Wrong size", "Did not meet expectations",
    "Customer changed mind", "Late delivery"
]

# =====================================================================
# 2. Clear existing data (children first, respecting foreign keys)
# =====================================================================
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

    # --- categories, stores, employees, products ---
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

    employee_ids = []
    for store_id in store_ids:
        for _ in range(random.randint(3, 5)):
            result = conn.execute(text("""
                INSERT INTO employees (first_name, last_name, store_id, position, hire_date)
                VALUES (:fn, :ln, :sid, :pos, :hd)
            """), {
                "fn": (emp_name := random_bulgarian_name())[0], "ln": emp_name[1], "sid": store_id,
                "pos": random.choice(POSITIONS),
                "hd": fake.date_between(start_date="-3y", end_date="-1M"),
            })
            employee_ids.append(result.lastrowid)

    product_ids = []
    product_prices = {}
    for _ in range(N_PRODUCTS):
        category_name = random.choice(CATEGORY_NAMES)
        base_name = random.choice(PRODUCT_TEMPLATES[category_name])
        product_name = f"{base_name} {fake.word().capitalize()}"
        cost = round(random.uniform(5, 150), 2)
        price = round(cost * random.uniform(1.3, 2.2), 2)  # 30%-120% margin
        result = conn.execute(text("""
            INSERT INTO products (product_name, category_id, price, cost)
            VALUES (:pn, :cid, :price, :cost)
        """), {"pn": product_name, "cid": category_ids[category_name],
                "price": price, "cost": cost})
        pid = result.lastrowid
        product_ids.append(pid)
        product_prices[pid] = price

    # --- customers ---
    print(f"Generating {N_CUSTOMERS} customers...")
    customer_ids = []
    for i in range(1, N_CUSTOMERS + 1):
        result = conn.execute(text("""
            INSERT INTO customers (first_name, last_name, email, phone, city, registration_date)
            VALUES (:fn, :ln, :email, :phone, :city, :rd)
        """), {
            "fn": (cust_name := random_bulgarian_name())[0], "ln": cust_name[1],
            "email": f"{cust_name[0].lower()}.{cust_name[1].lower()}{i}@example.com",
            "phone": random_bulgarian_phone(),
            "city": random.choice(BULGARIAN_CITIES),
            "rd": fake.date_between(start_date="-3y", end_date="today"),
        })
        customer_ids.append(result.lastrowid)

    # --- orders + order_items + payments ---
    print(f"Generating {N_ORDERS} orders and their line items...")
    order_item_ids_all = []
    for _ in range(N_ORDERS):
        order_date = fake.date_time_between(
            start_date=f"-{MONTHS_BACK}M", end_date="now")
        status = random.choice(ORDER_STATUSES_WEIGHTED)
        customer_id = random.choice(customer_ids)
        store_id = random.choice(store_ids)
        employee_id = random.choice(employee_ids) if random.random() > 0.05 else None

        result = conn.execute(text("""
            INSERT INTO orders (customer_id, store_id, employee_id, order_date, status)
            VALUES (:cid, :sid, :eid, :od, :st)
        """), {"cid": customer_id, "sid": store_id, "eid": employee_id,
                "od": order_date, "st": status})
        order_id = result.lastrowid

        chosen_products = random.sample(product_ids, k=random.randint(1, 5))
        order_total = 0.0
        for pid in chosen_products:
            quantity = random.randint(1, 3)
            unit_price = product_prices[pid]
            item_result = conn.execute(text("""
                INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                VALUES (:oid, :pid, :q, :up)
            """), {"oid": order_id, "pid": pid, "q": quantity, "up": unit_price})
            order_item_ids_all.append(item_result.lastrowid)
            order_total += quantity * unit_price

        print("Generating payments...") if order_id == 1 else None
        if status != "pending":
            payment_date = order_date + timedelta(hours=random.randint(0, 48))
            conn.execute(text("""
                INSERT INTO payments (order_id, payment_date, amount, payment_method)
                VALUES (:oid, :pd, :amt, :pm)
            """), {"oid": order_id, "pd": payment_date,
                    "amt": round(order_total, 2),
                    "pm": random.choice(PAYMENT_METHODS)})

    # --- inventory ---
    print("Generating inventory by store...")
    for pid in product_ids:
        for sid in store_ids:
            conn.execute(text("""
                INSERT INTO inventory (product_id, store_id, quantity_available, last_updated)
                VALUES (:pid, :sid, :qty, :lu)
            """), {"pid": pid, "sid": sid,
                    "qty": random.randint(0, 200),
                    "lu": datetime.now()})

    # --- promotions ---
    print("Generating promotions...")
    promo_products = random.sample(product_ids, k=int(N_PRODUCTS * 0.2))
    for pid in promo_products:
        start = fake.date_between(start_date="-6M", end_date="today")
        end = start + timedelta(days=random.randint(7, 30))
        conn.execute(text("""
            INSERT INTO promotions (product_id, discount_percent, start_date, end_date)
            VALUES (:pid, :disc, :sd, :ed)
        """), {"pid": pid, "disc": round(random.uniform(5, 40), 2),
                "sd": start, "ed": end})

    # --- returns ---
    print("Generating product returns...")
    n_returns = int(len(order_item_ids_all) * RETURN_RATE)
    returned_items = random.sample(order_item_ids_all, k=n_returns)
    for item_id in returned_items:
        row = conn.execute(text(
            "SELECT quantity, unit_price FROM order_items WHERE order_item_id = :id"),
            {"id": item_id}).fetchone()
        refund = round(row[0] * row[1], 2)
        conn.execute(text("""
            INSERT INTO returns (order_item_id, return_date, reason, refund_amount)
            VALUES (:oid, :rd, :reason, :amt)
        """), {"oid": item_id, "rd": fake.date_between(start_date="-6M", end_date="today"),
                "reason": random.choice(RETURN_REASONS), "amt": refund})

print("\nDone! The database has been populated successfully.")