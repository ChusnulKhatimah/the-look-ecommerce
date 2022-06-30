/* Create order_items table */ 
CREATE TABLE public.order_items
(
	id int
	,order_id int
	,user_id int
	,product_id int
	,inventory_item_id int
	,status varchar
	,created_at timestamp
	,shipped_at timestamp
	,delivered_at timestamp
	,returned_at timestamp
	,sale_price float
);

/* Look within order_items table */
SELECT * 
FROM order_items; /* order_items contained 180.508 rows */

/* Sorting order_items based on order_id ASC */
SELECT *
FROM order_items
ORDER BY order_id ASC; /* From this query, we can see that:
1. one user, could have more than one order_id. 
2. one order_id, user can buy different products at a time.
3. every order_id have their own status. 
4. but, one order_id could be created by user at different times.
5. the workflow of shipment is: created - shipped - delivered - returned.
6. column with timestamp (created - shipped - delivered - returned), aligned with status. */

/* How many order in order_items? */
SELECT COUNT(DISTINCT order_id) AS n_order
FROM order_items; /* 124.512 orders */

/* How many user in order_items? */
SELECT COUNT(DISTINCT user_id) AS n_user
FROM order_items; /* 79.986 user */

/* How many product in order_items? */
SELECT COUNT(DISTINCT product_id) AS n_product
FROM order_items; /* 29.050 products */

/* How many status in order_items? */
SELECT COUNT(DISTINCT status) AS n_status
FROM order_items; /* 5 status processing - cancelled - shiped - completed - returned*/

/* Shorten sale_price column name into product_price */
SELECT sale_price 
AS product_price
FROM order_items;

/* Lowest product price */
SELECT MIN(sale_price) AS total
FROM order_items; /* 0.019 $ */

/* Highest product price */
SELECT MAX(sale_price) AS total
FROM order_items; /* 999 $ */

/* So, the product price vary from $ 0.019 - $ 999 */

/* Add sales column into order_items */
ALTER TABLE order_items
ADD sales float;

/* Total sales for each status */
SELECT
    status,
    SUM(sale_price) AS total_sales_status
FROM order_items
GROUP BY status;

/* 10 products with highest sales */
SELECT
    product_id,
    SUM(sale_price) AS total_sales_product
FROM order_items
GROUP BY product_id
ORDER BY SUM(sale_price) DESC
LIMIT 10;

/* 10 products with lowest sales */
SELECT
    product_id,
    SUM(sale_price) AS total_sales_product
FROM order_items
GROUP BY product_id
ORDER BY SUM(sale_price) ASC
LIMIT 10;

/* Products that have total sales more than $1.000 */
SELECT
    product_id,
    SUM(sale_price) as total_sales_product
FROM order_items
GROUP BY product_id
HAVING SUM(sale_price) > 500;

/* Categorizing product_id as Profitable, Medium, and Non-Profitable products */
SELECT 
    product_id, 
    SUM(sale_price),
CASE
    WHEN SUM(sale_price) > 500 THEN 'Profitable'
    WHEN SUM(sale_price) < 10 THEN 'Not Profitable'
    ELSE 'Medium'
END AS ProductCategory
FROM order_items
GROUP BY product_id;

----------------------------------------------------------------

/* Create orders table */
CREATE TABLE public.orders
(
	order_id int
	,user_id int
	,status varchar
    ,gender varchar
	,created_at timestamp
    ,returned_at timestamp
	,shipped_at timestamp
	,delivered_at timestamp
	,num_of_item float
);

/* Look within orders table */
SELECT * 
FROM orders; /* orders contained 124.512 rows */

/* How many unique order in orders? */
SELECT COUNT(DISTINCT order_id) AS n_order
FROM orders; /*Every rows, contain 1 order_id, there's no doubled order_id */

/* How many user in orders? */
SELECT COUNT(DISTINCT user_id) AS n_user
FROM orders;

/* How many status in orders? */
SELECT COUNT(DISTINCT status) AS n_status
FROM orders;

/* How many orders in each status? */
SELECT 
    status,
    COUNT(order_id) AS n_order_status
FROM orders
GROUP BY status;

/* How many gender in orders? */
SELECT COUNT(DISTINCT gender)
FROM orders;

/* Total items created by users? */
SELECT SUM(num_of_item)
FROM orders;

/* How many items sold based on gender? */
SELECT 
    gender,
    SUM(num_of_item) AS n_items_sold
FROM orders
GROUP BY gender;

/* LEFT join for order_items and orders table */
SELECT * FROM order_items;
SELECT * FROM orders;

SELECT 
    c.order_id
    ,c.user_id
    ,c.product_id
    ,c.status
    ,c.created_at
    ,c.shipped_at
    ,c.delivered_at
    ,c.returned_at
    ,c.sale_price
    ,p.gender
    ,p.num_of_item
FROM order_items AS c
LEFT JOIN orders AS p
ON c.order_id = p.order_id;

/* CREATE NEW TABLE sales */
CREATE TABLE public.sales
(
	order_id int
	,user_id int
	,product_id int
	,status varchar
	,created_at varchar
	,shipped_at varchar
	,delivered_at varchar
	,returned_at varchar
	,sale_price float
    ,gender varchar
    ,num_of_item int
);

/* ADD NEW COLUMN 'total_price' */
ALTER TABLE sales
ADD total_price varchar;

ALTER TABLE sales
DROP COLUMN total_price;

/* SELECT ALL from sales */
SELECT * FROM sales;

/* SET 'total_price' values from multiplying num_of_item and sale_price */
SELECT *,
    num_of_item * sale_price AS total_price
FROM sales;