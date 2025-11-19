-- Seed demo data for Grocery Recommendations

-- Users
INSERT INTO users (email, name)
SELECT 'demo@user.com', 'Demo User'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'demo@user.com');

INSERT INTO users (email, name)
SELECT 'alice@example.com', 'Alice'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'alice@example.com');

INSERT INTO users (email, name)
SELECT 'bob@example.com', 'Bob'
WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'bob@example.com');

-- Categories
INSERT INTO categories (name, slug)
SELECT 'Fruits', 'fruits'
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Fruits');

INSERT INTO categories (name, slug)
SELECT 'Vegetables', 'vegetables'
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Vegetables');

INSERT INTO categories (name, slug)
SELECT 'Dairy', 'dairy'
WHERE NOT EXISTS (SELECT 1 FROM categories WHERE name = 'Dairy');

-- Shops (longitude, latitude) Karachi examples
INSERT INTO shops (name, address, location)
SELECT 'City Mart', 'Downtown Branch', ST_SetSRID(ST_MakePoint(67.0011,24.8607),4326)::geography
WHERE NOT EXISTS (SELECT 1 FROM shops WHERE name = 'City Mart');

INSERT INTO shops (name, address, location)
SELECT 'Fresh Hub', 'East Market', ST_SetSRID(ST_MakePoint(67.0065,24.8620),4326)::geography
WHERE NOT EXISTS (SELECT 1 FROM shops WHERE name = 'Fresh Hub');

INSERT INTO shops (name, address, location)
SELECT 'Green Basket', 'West End', ST_SetSRID(ST_MakePoint(67.0005,24.8589),4326)::geography
WHERE NOT EXISTS (SELECT 1 FROM shops WHERE name = 'Green Basket');

INSERT INTO shops (name, address, location)
SELECT 'Daily Needs', 'Central Avenue', ST_SetSRID(ST_MakePoint(67.0040,24.8615),4326)::geography
WHERE NOT EXISTS (SELECT 1 FROM shops WHERE name = 'Daily Needs');

INSERT INTO shops (name, address, location)
SELECT 'MegaMart', 'North Square', ST_SetSRID(ST_MakePoint(67.0100,24.8650),4326)::geography
WHERE NOT EXISTS (SELECT 1 FROM shops WHERE name = 'MegaMart');

-- Products with analytics fields
INSERT INTO products (name, category_id, shop_id, daily_views, weekly_sales, last_purchased_at)
SELECT 'Bananas',
       (SELECT id FROM categories WHERE slug='fruits'),
       (SELECT id FROM shops WHERE name='City Mart'),
       15, 7, now() - interval '1 day'
WHERE NOT EXISTS (
  SELECT 1 FROM products
  WHERE name='Bananas' AND shop_id=(SELECT id FROM shops WHERE name='City Mart')
);

INSERT INTO products (name, category_id, shop_id, daily_views, weekly_sales, last_purchased_at)
SELECT 'Apples',
       (SELECT id FROM categories WHERE slug='fruits'),
       (SELECT id FROM shops WHERE name='Fresh Hub'),
       8, 3, now() - interval '3 days'
WHERE NOT EXISTS (
  SELECT 1 FROM products
  WHERE name='Apples' AND shop_id=(SELECT id FROM shops WHERE name='Fresh Hub')
);

INSERT INTO products (name, category_id, shop_id, daily_views, weekly_sales, last_purchased_at)
SELECT 'Carrots',
       (SELECT id FROM categories WHERE slug='vegetables'),
       (SELECT id FROM shops WHERE name='Green Basket'),
       20, 11, now() - interval '12 hours'
WHERE NOT EXISTS (
  SELECT 1 FROM products
  WHERE name='Carrots' AND shop_id=(SELECT id FROM shops WHERE name='Green Basket')
);

INSERT INTO products (name, category_id, shop_id, daily_views, weekly_sales, last_purchased_at)
SELECT 'Milk 1L',
       (SELECT id FROM categories WHERE slug='dairy'),
       (SELECT id FROM shops WHERE name='City Mart'),
       30, 14, now() - interval '2 hours'
WHERE NOT EXISTS (
  SELECT 1 FROM products
  WHERE name='Milk 1L' AND shop_id=(SELECT id FROM shops WHERE name='City Mart')
);

INSERT INTO products (name, category_id, shop_id, daily_views, weekly_sales, last_purchased_at)
SELECT 'Yogurt Pack',
       (SELECT id FROM categories WHERE slug='dairy'),
       (SELECT id FROM shops WHERE name='Fresh Hub'),
       5, 2, now() - interval '5 days'
WHERE NOT EXISTS (
  SELECT 1 FROM products
  WHERE name='Yogurt Pack' AND shop_id=(SELECT id FROM shops WHERE name='Fresh Hub')
);

INSERT INTO products (name, category_id, shop_id, daily_views, weekly_sales, last_purchased_at)
SELECT 'Oranges',
       (SELECT id FROM categories WHERE slug='fruits'),
       (SELECT id FROM shops WHERE name='Daily Needs'),
       18, 9, now() - interval '2 days'
WHERE NOT EXISTS (
  SELECT 1 FROM products
  WHERE name='Oranges' AND shop_id=(SELECT id FROM shops WHERE name='Daily Needs')
);

INSERT INTO products (name, category_id, shop_id, daily_views, weekly_sales, last_purchased_at)
SELECT 'Spinach Bunch',
       (SELECT id FROM categories WHERE slug='vegetables'),
       (SELECT id FROM shops WHERE name='Daily Needs'),
       10, 4, now() - interval '1 day'
WHERE NOT EXISTS (
  SELECT 1 FROM products
  WHERE name='Spinach Bunch' AND shop_id=(SELECT id FROM shops WHERE name='Daily Needs')
);

INSERT INTO products (name, category_id, shop_id, daily_views, weekly_sales, last_purchased_at)
SELECT 'Cheddar Cheese',
       (SELECT id FROM categories WHERE slug='dairy'),
       (SELECT id FROM shops WHERE name='MegaMart'),
       25, 12, now() - interval '3 hours'
WHERE NOT EXISTS (
  SELECT 1 FROM products
  WHERE name='Cheddar Cheese' AND shop_id=(SELECT id FROM shops WHERE name='MegaMart')
);

INSERT INTO products (name, category_id, shop_id, daily_views, weekly_sales, last_purchased_at)
SELECT 'Tomatoes',
       (SELECT id FROM categories WHERE slug='vegetables'),
       (SELECT id FROM shops WHERE name='MegaMart'),
       22, 10, now() - interval '8 hours'
WHERE NOT EXISTS (
  SELECT 1 FROM products
  WHERE name='Tomatoes' AND shop_id=(SELECT id FROM shops WHERE name='MegaMart')
);

INSERT INTO product_view_events (user_id, product_id, created_at)
SELECT u.id, p.id, now() - (random() * interval '2 days')
FROM users u, products p
WHERE u.email = 'demo@user.com' AND p.name = 'Bananas'
  AND NOT EXISTS (
    SELECT 1 FROM product_view_events pve
    WHERE pve.user_id = u.id AND pve.product_id = p.id
  );

INSERT INTO product_view_events (user_id, product_id, created_at)
SELECT u.id, p.id, now() - (random() * interval '2 days')
FROM users u, products p
WHERE u.email = 'demo@user.com' AND p.name = 'Milk 1L'
  AND NOT EXISTS (
    SELECT 1 FROM product_view_events pve
    WHERE pve.user_id = u.id AND pve.product_id = p.id
  );

INSERT INTO product_view_events (user_id, product_id, created_at)
SELECT u.id, p.id, now() - (random() * interval '2 days')
FROM users u, products p
WHERE u.email = 'demo@user.com' AND p.name = 'Carrots'
  AND NOT EXISTS (
    SELECT 1 FROM product_view_events pve
    WHERE pve.user_id = u.id AND pve.product_id = p.id
  );

INSERT INTO purchase_events (user_id, product_id, quantity, price_at_purchase, created_at)
SELECT u.id, p.id, 1, 120.00, now() - interval '6 hours'
FROM users u, products p
WHERE u.email = 'demo@user.com' AND p.name = 'Milk 1L'
  AND NOT EXISTS (
    SELECT 1 FROM purchase_events pe
    WHERE pe.user_id = u.id AND pe.product_id = p.id
  );

INSERT INTO purchase_events (user_id, product_id, quantity, price_at_purchase, created_at)
SELECT u.id, p.id, 2, 200.00, now() - interval '1 day'
FROM users u, products p
WHERE u.email = 'demo@user.com' AND p.name = 'Carrots'
  AND NOT EXISTS (
    SELECT 1 FROM purchase_events pe
    WHERE pe.user_id = u.id AND pe.product_id = p.id
  );


INSERT INTO product_view_events (user_id, product_id, created_at)
SELECT u.id, p.id, now() - (random() * interval '3 days')
FROM users u, products p
WHERE u.email = 'alice@example.com' AND p.name IN ('Bananas','Oranges','Milk 1L')
  AND NOT EXISTS (
    SELECT 1 FROM product_view_events pve
    WHERE pve.user_id = u.id AND pve.product_id = p.id
  );

INSERT INTO product_view_events (user_id, product_id, created_at)
SELECT u.id, p.id, now() - (random() * interval '3 days')
FROM users u, products p
WHERE u.email = 'bob@example.com' AND p.name IN ('Carrots','Tomatoes','Spinach Bunch')
  AND NOT EXISTS (
    SELECT 1 FROM product_view_events pve
    WHERE pve.user_id = u.id AND pve.product_id = p.id
  );

INSERT INTO purchase_events (user_id, product_id, quantity, price_at_purchase, created_at)
SELECT u.id, p.id, 1, 150.00, now() - interval '10 hours'
FROM users u, products p
WHERE u.email = 'alice@example.com' AND p.name = 'Oranges'
  AND NOT EXISTS (
    SELECT 1 FROM purchase_events pe
    WHERE pe.user_id = u.id AND pe.product_id = p.id
  );

INSERT INTO purchase_events (user_id, product_id, quantity, price_at_purchase, created_at)
SELECT u.id, p.id, 2, 220.00, now() - interval '16 hours'
FROM users u, products p
WHERE u.email = 'bob@example.com' AND p.name = 'Tomatoes'
  AND NOT EXISTS (
    SELECT 1 FROM purchase_events pe
    WHERE pe.user_id = u.id AND pe.product_id = p.id
  );