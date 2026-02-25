-- SQL Setup Script for Promotion Data
-- Run this in your database or use: python manage.py dbshell < setup_promotions.sql

-- ============================================
-- 1. UPDATE SITE SETTINGS
-- ============================================
UPDATE website_sitesettings 
SET 
  shipping_cost = 10.00,
  tax = 10.00
WHERE id = 1;

-- ============================================
-- 2. CREATE FREE SHIPPING PROMOTION
-- ============================================
INSERT INTO product_promotion 
(`promotion_type`, `title`, `description`, `start_date`, `end_date`, `is_active`, `created_at`, `updated_at`)
VALUES 
(
  'free_shipping',
  'Free Shipping on Orders Over $50',
  'Get free shipping when you spend $50 or more. Valid for all smartphones and gadgets.',
  NOW(),
  DATE_ADD(NOW(), INTERVAL 30 DAY),
  1,
  NOW(),
  NOW()
);

-- Get the ID (should be the last inserted)
SET @free_shipping_id = LAST_INSERT_ID();

-- ============================================
-- 3. CREATE FREE GIFT PROMOTION
-- ============================================
INSERT INTO product_promotion 
(`promotion_type`, `title`, `description`, `start_date`, `end_date`, `is_active`, `created_at`, `updated_at`)
VALUES 
(
  'free_gift',
  'Free Gift with Premium Phones',
  'Buy any premium smartphone and get a free premium case worth $30.',
  NOW(),
  DATE_ADD(NOW(), INTERVAL 15 DAY),
  1,
  NOW(),
  NOW()
);

SET @free_gift_id = LAST_INSERT_ID();

-- ============================================
-- 4. CREATE UPCOMING PROMOTION
-- ============================================
INSERT INTO product_promotion 
(`promotion_type`, `title`, `description`, `start_date`, `end_date`, `is_active`, `created_at`, `updated_at`)
VALUES 
(
  'free_shipping',
  'Coming Soon - Free Shipping Festival',
  'Big free shipping festival coming next month. Stay tuned!',
  DATE_ADD(NOW(), INTERVAL 7 DAY),
  DATE_ADD(NOW(), INTERVAL 37 DAY),
  1,
  NOW(),
  NOW()
);

-- ============================================
-- 5. CREATE EXPIRED PROMOTION
-- ============================================
INSERT INTO product_promotion 
(`promotion_type`, `title`, `description`, `start_date`, `end_date`, `is_active`, `created_at`, `updated_at`)
VALUES 
(
  'free_gift',
  'Expired - Spring Sale Gift',
  'This promotion has expired.',
  DATE_SUB(NOW(), INTERVAL 30 DAY),
  DATE_SUB(NOW(), INTERVAL 1 DAY),
  1,
  NOW(),
  NOW()
);

-- ============================================
-- 6. LINK PRODUCTS TO FREE SHIPPING PROMOTION
-- ============================================
-- Link first 3 active products
INSERT INTO product_promotion_products (promotion_id, product_id)
SELECT @free_shipping_id, id
FROM product_product
WHERE is_active = 1
LIMIT 3;

-- ============================================
-- 7. LINK PRODUCTS TO FREE GIFT PROMOTION
-- ============================================
-- Link products 4-5
INSERT INTO product_promotion_products (promotion_id, product_id)
SELECT @free_gift_id, id
FROM product_product
WHERE is_active = 1
LIMIT 2 OFFSET 2;

-- ============================================
-- VERIFY DATA
-- ============================================
-- Check promotions created
SELECT 'Total Promotions' as `Description`, COUNT(*) as `Count`
FROM product_promotion
UNION ALL
SELECT 'Free Shipping', COUNT(*)
FROM product_promotion
WHERE promotion_type = 'free_shipping'
UNION ALL
SELECT 'Free Gift', COUNT(*)
FROM product_promotion
WHERE promotion_type = 'free_gift'
UNION ALL
SELECT 'Active Promotions', COUNT(*)
FROM product_promotion
WHERE is_active = 1 AND start_date <= NOW() AND end_date >= NOW()
UNION ALL
SELECT 'Upcoming Promotions', COUNT(*)
FROM product_promotion
WHERE is_active = 1 AND start_date > NOW()
UNION ALL
SELECT 'Expired Promotions', COUNT(*)
FROM product_promotion
WHERE end_date < NOW();

-- Check linked products
SELECT 
  p.title as 'Promotion',
  p.promotion_type as 'Type',
  COUNT(pp.product_id) as 'Products Linked'
FROM product_promotion p
LEFT JOIN product_promotion_products pp ON p.id = pp.promotion_id
GROUP BY p.id, p.title, p.promotion_type;

-- ============================================
-- ALTERNATIVE: Remove All Promotions (Clean Slate)
-- ============================================
-- DELETE FROM product_promotion_products;
-- DELETE FROM product_promotion;
