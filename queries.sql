SELECT first_name, last_name
FROM customers
WHERE city = 'Sofia';


SELECT order_id
FROM orders
WHERE status = 'cancelled';


SELECT product_name, category_id
FROM products
WHERE price > 100.00;


SELECT product_name, price
FROM products
ORDER BY price DESC
LIMIT 5;


SELECT o.order_item_id, o.order_id, o.product_id, p.product_name, o.quantity
FROM order_items o
JOIN products p ON p.product_id = o.product_id;


SELECT o.order_id, o.order_date, p.product_name, oi.quantity
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id;


SELECT p.product_id, p.product_name, pm.discount_percent
FROM products p
LEFT JOIN promotions pm ON p.product_id = pm.product_id;


SELECT o.order_id, e.first_name, e.last_name
FROM orders o
LEFT JOIN employees e ON o.employee_id = e.employee_id
WHERE e.employee_id IS NULL;


SELECT product_id, SUM(quantity * unit_price) AS total_revenue
FROM order_items
GROUP BY product_id;


SELECT c.category_name, SUM(oi.quantity * oi.unit_price) AS total_revenue_from_category
FROM categories c
JOIN products p ON c.category_id = p.category_id
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status = 'completed'
GROUP BY c.category_name
ORDER BY total_revenue_from_category DESC;


SELECT product_name, price
FROM products
WHERE price > (SELECT AVG(price) FROM products);


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


CREATE OR REPLACE VIEW customer_lifetime_value AS
SELECT o.customer_id,
       SUM(oi.quantity * oi.unit_price) AS completed_revenue,
       COUNT(DISTINCT o.order_id) AS completed_orders
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
WHERE o.status = 'completed'
GROUP BY o.customer_id;

SELECT * FROM customer_lifetime_value
ORDER BY completed_revenue DESC
LIMIT 10;
