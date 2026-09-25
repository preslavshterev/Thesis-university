-- Customers from Sofia
SELECT first_name, last_name
FROM customers
WHERE city = 'Sofia';

-- Cancelled orders
SELECT order_id
FROM orders
WHERE status = 'cancelled';

-- Products priced above 100
SELECT product_name, category_id
FROM products
WHERE price > 100.00;

-- Top 5 most expensive products
SELECT product_name, price
FROM products
ORDER BY price DESC
LIMIT 5;

-- JOIN: order items with product names
SELECT o.order_item_id, o.order_id, o.product_id, p.product_name, o.quantity
FROM order_items o
JOIN products p ON p.product_id = o.product_id;

-- JOIN: orders + order_items + products chained together
SELECT o.order_id, o.order_date, p.product_name, oi.quantity
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id;

-- LEFT JOIN: all products, with or without a promotion
SELECT p.product_id, p.product_name, pm.discount_percent
FROM products p
LEFT JOIN promotions pm ON p.product_id = pm.product_id;

-- LEFT JOIN: orders with no assigned employee
SELECT o.order_id, e.first_name, e.last_name
FROM orders o
LEFT JOIN employees e ON o.employee_id = e.employee_id
WHERE e.employee_id IS NULL;

-- GROUP BY + SUM: total revenue per product
SELECT product_id, SUM(quantity * unit_price) AS total_revenue
FROM order_items
GROUP BY product_id;

-- GROUP BY + JOIN: total revenue per category (uses unit_price, the price
-- at time of sale — not products.price, which is the current price)
SELECT c.category_name, SUM(oi.quantity * oi.unit_price) AS total_revenue_from_category
FROM categories c
JOIN products p ON c.category_id = p.category_id
JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY c.category_name
ORDER BY total_revenue_from_category DESC;


-- =====================================================================
-- DAY 6: Subqueries, CTEs, window functions, views
-- =====================================================================

-- Subquery: products priced above the average product price
SELECT product_name, price
FROM products
WHERE price > (SELECT AVG(price) FROM products);

-- CTE: top 3 categories by revenue
WITH category_revenue AS (
    SELECT c.category_name, SUM(oi.quantity * oi.unit_price) AS total_revenue_from_category
    FROM categories c
    JOIN products p ON c.category_id = p.category_id
    JOIN order_items oi ON p.product_id = oi.product_id
    GROUP BY category_name
)
SELECT * FROM category_revenue
ORDER BY total_revenue_from_category DESC
LIMIT 3;

-- Window function: rank products by price within each category
-- (CTE + WHERE rank = 1 -> the single most expensive product per category)
WITH rank_in_category AS (
    SELECT
        p.product_name,
        c.category_name,
        p.price,
        RANK() OVER (PARTITION BY c.category_id ORDER BY p.price DESC) AS rank_in_category
    FROM products p
    JOIN categories c ON p.category_id = c.category_id
)
SELECT * FROM rank_in_category
WHERE rank_in_category = 1;

-- VIEW: customer lifetime value (total paid + number of orders per customer)
-- Run once to create; DROP VIEW customer_lifetime_value; if you need to redefine it.
CREATE VIEW customer_lifetime_value AS
SELECT c.customer_id, SUM(pm.amount) AS paid_by_customer, COUNT(pm.order_id) AS number_of_orders
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
JOIN payments pm ON pm.order_id = o.order_id
GROUP BY customer_id;

SELECT * FROM customer_lifetime_value
ORDER BY paid_by_customer DESC
LIMIT 10;
