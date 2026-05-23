USE x_agent_mock_biz;

INSERT INTO dim_regions (id, region_code, region_name, province, city, tier, created_at) VALUES
(1, 'CN-SH', '上海', '上海市', '上海市', 1, '2026-01-01 00:00:00'),
(2, 'CN-BJ', '北京', '北京市', '北京市', 1, '2026-01-01 00:00:00'),
(3, 'CN-GD-SZ', '深圳', '广东省', '深圳市', 1, '2026-01-01 00:00:00'),
(4, 'CN-ZJ-HZ', '杭州', '浙江省', '杭州市', 2, '2026-01-01 00:00:00'),
(5, 'CN-SC-CD', '成都', '四川省', '成都市', 2, '2026-01-01 00:00:00'),
(6, 'CN-HB-WH', '武汉', '湖北省', '武汉市', 2, '2026-01-01 00:00:00'),
(7, 'CN-JS-NJ', '南京', '江苏省', '南京市', 2, '2026-01-01 00:00:00'),
(8, 'CN-FJ-XM', '厦门', '福建省', '厦门市', 3, '2026-01-01 00:00:00');

INSERT INTO dim_users (id, user_no, region_id, gender, age, registered_at, status, created_at)
SELECT
  n,
  CONCAT('U', LPAD(n, 5, '0')),
  1 + MOD(n, 8),
  CASE MOD(n, 3) WHEN 0 THEN 'unknown' WHEN 1 THEN 'female' ELSE 'male' END,
  18 + MOD(n * 7, 45),
  TIMESTAMP('2025-10-01 08:00:00') + INTERVAL n DAY,
  CASE WHEN MOD(n, 23) = 0 THEN 'frozen' WHEN MOD(n, 41) = 0 THEN 'closed' ELSE 'active' END,
  TIMESTAMP('2025-10-01 08:00:00') + INTERVAL n DAY
FROM (
  SELECT ones.n + tens.n * 10 + 1 AS n
  FROM
    (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
     UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) ones
  CROSS JOIN
    (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
     UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) tens
) seq
WHERE n <= 80;

INSERT INTO dim_merchants (id, merchant_no, merchant_name, region_id, category, onboarded_at, status, created_at) VALUES
(1, 'M0001', '海风数码旗舰店', 1, 'digital', '2025-01-10 10:00:00', 'active', '2025-01-10 10:00:00'),
(2, 'M0002', '北辰家居馆', 2, 'home', '2025-01-15 10:00:00', 'active', '2025-01-15 10:00:00'),
(3, 'M0003', '鹏城潮流服饰', 3, 'fashion', '2025-02-01 10:00:00', 'active', '2025-02-01 10:00:00'),
(4, 'M0004', '西湖美妆优选', 4, 'beauty', '2025-02-08 10:00:00', 'active', '2025-02-08 10:00:00'),
(5, 'M0005', '蓉城食品仓', 5, 'food', '2025-02-20 10:00:00', 'active', '2025-02-20 10:00:00'),
(6, 'M0006', '江城运动户外', 6, 'sports', '2025-03-01 10:00:00', 'active', '2025-03-01 10:00:00'),
(7, 'M0007', '金陵母婴生活', 7, 'baby', '2025-03-08 10:00:00', 'active', '2025-03-08 10:00:00'),
(8, 'M0008', '鹭岛图书音像', 8, 'book', '2025-03-15 10:00:00', 'active', '2025-03-15 10:00:00'),
(9, 'M0009', '华东折扣商城', 1, 'mixed', '2025-04-01 10:00:00', 'suspended', '2025-04-01 10:00:00'),
(10, 'M0010', '未来智能硬件', 3, 'digital', '2025-04-15 10:00:00', 'active', '2025-04-15 10:00:00'),
(11, 'M0011', '山城精品百货', 5, 'mixed', '2025-05-01 10:00:00', 'active', '2025-05-01 10:00:00'),
(12, 'M0012', '云上虚拟商品', 4, 'virtual', '2025-05-18 10:00:00', 'active', '2025-05-18 10:00:00');

INSERT INTO dim_categories (id, category_code, category_name, parent_id, level, created_at) VALUES
(1, 'DIGITAL', '数码', NULL, 1, '2025-01-01 00:00:00'),
(2, 'HOME', '家居', NULL, 1, '2025-01-01 00:00:00'),
(3, 'FASHION', '服饰', NULL, 1, '2025-01-01 00:00:00'),
(4, 'BEAUTY', '美妆', NULL, 1, '2025-01-01 00:00:00'),
(5, 'FOOD', '食品', NULL, 1, '2025-01-01 00:00:00'),
(6, 'SPORTS', '运动', NULL, 1, '2025-01-01 00:00:00'),
(7, 'BABY', '母婴', NULL, 1, '2025-01-01 00:00:00'),
(8, 'BOOK', '图书', NULL, 1, '2025-01-01 00:00:00'),
(9, 'PHONE', '手机', 1, 2, '2025-01-01 00:00:00'),
(10, 'LAPTOP', '电脑', 1, 2, '2025-01-01 00:00:00'),
(11, 'SHOES', '鞋靴', 3, 2, '2025-01-01 00:00:00'),
(12, 'SKINCARE', '护肤', 4, 2, '2025-01-01 00:00:00');

INSERT INTO dim_products (id, product_no, merchant_id, category_id, product_name, list_price, status, created_at)
SELECT
  n,
  CONCAT('P', LPAD(n, 5, '0')),
  1 + MOD(n, 12),
  1 + MOD(n, 12),
  CONCAT('测试商品-', LPAD(n, 3, '0')),
  19.90 + MOD(n * 37, 5000),
  CASE WHEN MOD(n, 17) = 0 THEN 'offline' ELSE 'active' END,
  TIMESTAMP('2025-06-01 09:00:00') + INTERVAL n HOUR
FROM (
  SELECT ones.n + tens.n * 10 + 1 AS n
  FROM
    (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
     UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) ones
  CROSS JOIN
    (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4) tens
) seq
WHERE n <= 48;

INSERT INTO fact_orders (
  id, order_no, user_id, merchant_id, region_id, order_status, total_amount,
  discount_amount, payable_amount, created_at, paid_at, cancelled_at
)
SELECT
  n,
  CONCAT('O', LPAD(n, 8, '0')),
  1 + MOD(n * 7, 80),
  1 + MOD(n * 5, 12),
  1 + MOD(n * 3, 8),
  CASE
    WHEN MOD(n, 19) = 0 THEN 'cancelled'
    WHEN MOD(n, 13) = 0 THEN 'refunded'
    WHEN MOD(n, 7) = 0 THEN 'created'
    ELSE 'paid'
  END,
  ROUND(60 + MOD(n * 43, 3000) + MOD(n, 5) * 0.37, 2),
  ROUND(MOD(n * 11, 120), 2),
  ROUND(60 + MOD(n * 43, 3000) + MOD(n, 5) * 0.37 - MOD(n * 11, 120), 2),
  TIMESTAMP('2026-05-01 00:00:00') + INTERVAL MOD(n * 5, 21) DAY + INTERVAL MOD(n * 17, 24) HOUR,
  CASE WHEN MOD(n, 19) = 0 OR MOD(n, 7) = 0 THEN NULL
       ELSE TIMESTAMP('2026-05-01 00:00:00') + INTERVAL MOD(n * 5, 21) DAY + INTERVAL MOD(n * 17 + 1, 24) HOUR
  END,
  CASE WHEN MOD(n, 19) = 0
       THEN TIMESTAMP('2026-05-01 00:00:00') + INTERVAL MOD(n * 5, 21) DAY + INTERVAL MOD(n * 17 + 2, 24) HOUR
       ELSE NULL
  END
FROM (
  SELECT ones.n + tens.n * 10 + hundreds.n * 100 + 1 AS n
  FROM
    (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
     UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) ones
  CROSS JOIN
    (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
     UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) tens
  CROSS JOIN
    (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2) hundreds
) seq
WHERE n <= 240;

INSERT INTO fact_order_items (id, order_id, product_id, quantity, item_amount, discount_amount, created_at)
SELECT
  o.id * 10 + item_seq.item_no,
  o.id,
  1 + MOD(o.id * 3 + item_seq.item_no, 48),
  1 + MOD(o.id + item_seq.item_no, 3),
  ROUND(o.payable_amount / (2 + MOD(o.id, 2)) + item_seq.item_no * 3.50, 2),
  ROUND(MOD(o.id + item_seq.item_no, 20), 2),
  o.created_at
FROM fact_orders o
JOIN (
  SELECT 1 AS item_no UNION ALL SELECT 2 UNION ALL SELECT 3
) item_seq ON item_seq.item_no <= 1 + MOD(o.id, 3);

INSERT INTO fact_payments (id, payment_no, order_id, user_id, channel, payment_status, amount, paid_at, failure_reason)
SELECT
  o.id,
  CONCAT('PAY', LPAD(o.id, 8, '0')),
  o.id,
  o.user_id,
  CASE MOD(o.id, 4) WHEN 0 THEN 'alipay' WHEN 1 THEN 'wechat' WHEN 2 THEN 'bank_card' ELSE 'balance' END,
  CASE WHEN o.order_status IN ('paid', 'refunded') THEN 'paid' WHEN MOD(o.id, 7) = 0 THEN 'failed' ELSE 'processing' END,
  o.payable_amount,
  COALESCE(o.paid_at, o.created_at + INTERVAL 15 MINUTE),
  CASE WHEN MOD(o.id, 7) = 0 THEN 'insufficient_balance' ELSE NULL END
FROM fact_orders o
WHERE o.order_status <> 'cancelled';

INSERT INTO fact_refunds (
  id, refund_no, order_id, payment_id, refund_status, refund_reason, refund_amount, requested_at, completed_at
)
SELECT
  o.id,
  CONCAT('REF', LPAD(o.id, 8, '0')),
  o.id,
  p.id,
  CASE WHEN MOD(o.id, 5) = 0 THEN 'processing' ELSE 'success' END,
  CASE MOD(o.id, 4)
    WHEN 0 THEN 'quality_issue'
    WHEN 1 THEN 'user_regret'
    WHEN 2 THEN 'merchant_delay'
    ELSE 'risk_review'
  END,
  ROUND(o.payable_amount * (CASE WHEN MOD(o.id, 3) = 0 THEN 1.00 ELSE 0.35 END), 2),
  o.created_at + INTERVAL 2 DAY,
  CASE WHEN MOD(o.id, 5) = 0 THEN NULL ELSE o.created_at + INTERVAL 3 DAY END
FROM fact_orders o
JOIN fact_payments p ON p.order_id = o.id
WHERE o.order_status = 'refunded' OR MOD(o.id, 17) = 0;

INSERT INTO fact_user_events (id, user_id, event_type, product_id, merchant_id, device_type, ip_region_id, occurred_at)
SELECT
  n,
  1 + MOD(n * 11, 80),
  CASE MOD(n, 4) WHEN 0 THEN 'login' WHEN 1 THEN 'view_product' WHEN 2 THEN 'add_cart' ELSE 'submit_order' END,
  CASE WHEN MOD(n, 4) = 0 THEN NULL ELSE 1 + MOD(n * 7, 48) END,
  CASE WHEN MOD(n, 4) = 0 THEN NULL ELSE 1 + MOD(n * 5, 12) END,
  CASE MOD(n, 3) WHEN 0 THEN 'ios' WHEN 1 THEN 'android' ELSE 'web' END,
  1 + MOD(n * 13, 8),
  TIMESTAMP('2026-05-01 00:00:00') + INTERVAL MOD(n * 3, 21) DAY + INTERVAL MOD(n * 5, 24) HOUR
FROM (
  SELECT ones.n + tens.n * 10 + hundreds.n * 100 + 1 AS n
  FROM
    (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
     UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) ones
  CROSS JOIN
    (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
     UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) tens
  CROSS JOIN
    (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3) hundreds
) seq
WHERE n <= 360;

INSERT INTO risk_user_profiles (user_id, risk_level, risk_score, is_blacklisted, last_evaluated_at)
SELECT
  id,
  CASE WHEN MOD(id, 11) = 0 THEN 'high' WHEN MOD(id, 5) = 0 THEN 'medium' ELSE 'low' END,
  ROUND(15 + MOD(id * 9, 85) + MOD(id, 3) * 0.33, 2),
  CASE WHEN MOD(id, 37) = 0 THEN 1 ELSE 0 END,
  '2026-05-22 08:00:00'
FROM dim_users;

INSERT INTO risk_merchant_profiles (merchant_id, risk_level, risk_score, abnormal_refund_rate, last_evaluated_at)
SELECT
  id,
  CASE WHEN id IN (9, 12) THEN 'high' WHEN id IN (4, 7, 11) THEN 'medium' ELSE 'low' END,
  ROUND(20 + MOD(id * 13, 80), 2),
  ROUND(0.02 + MOD(id * 7, 30) / 100, 4),
  '2026-05-22 08:00:00'
FROM dim_merchants;

INSERT INTO risk_rules (id, rule_code, rule_name, rule_type, severity, enabled, created_at) VALUES
(1, 'R_USER_HIGH_FREQ', '用户短时高频下单', 'user', 'medium', 1, '2025-01-01 00:00:00'),
(2, 'R_PAY_FAIL_SPIKE', '支付失败率突增', 'payment', 'medium', 1, '2025-01-01 00:00:00'),
(3, 'R_REFUND_ABUSE', '异常退款倾向', 'refund', 'high', 1, '2025-01-01 00:00:00'),
(4, 'R_MERCHANT_ABNORMAL', '商户异常交易', 'merchant', 'high', 1, '2025-01-01 00:00:00'),
(5, 'R_BLACKLIST_USER', '黑名单用户交易', 'user', 'high', 1, '2025-01-01 00:00:00'),
(6, 'R_REMOTE_LOGIN', '异地登录后下单', 'user', 'low', 1, '2025-01-01 00:00:00');

INSERT INTO risk_rule_hits (
  id, rule_id, user_id, merchant_id, order_id, payment_id, hit_score, hit_detail, hit_at
)
SELECT
  n,
  1 + MOD(n, 6),
  o.user_id,
  o.merchant_id,
  o.id,
  p.id,
  ROUND(35 + MOD(n * 11, 65), 2),
  CONCAT('mock risk hit for order ', o.order_no),
  o.created_at + INTERVAL 20 MINUTE
FROM (
  SELECT ones.n + tens.n * 10 + 1 AS n
  FROM
    (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
     UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) ones
  CROSS JOIN
    (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
     UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) tens
) seq
JOIN fact_orders o ON o.id = 1 + MOD(n * 9, 240)
LEFT JOIN fact_payments p ON p.order_id = o.id
WHERE n <= 90;

INSERT INTO risk_cases (
  id, case_no, user_id, merchant_id, order_id, case_type, case_status, priority, opened_at, closed_at
)
SELECT
  n,
  CONCAT('CASE', LPAD(n, 6, '0')),
  o.user_id,
  o.merchant_id,
  o.id,
  CASE MOD(n, 3) WHEN 0 THEN 'fraud' WHEN 1 THEN 'refund_abuse' ELSE 'merchant_abuse' END,
  CASE MOD(n, 4) WHEN 0 THEN 'closed' WHEN 1 THEN 'open' WHEN 2 THEN 'reviewing' ELSE 'closed' END,
  CASE MOD(n, 3) WHEN 0 THEN 'high' WHEN 1 THEN 'medium' ELSE 'low' END,
  o.created_at + INTERVAL 1 HOUR,
  CASE WHEN MOD(n, 4) IN (0, 3) THEN o.created_at + INTERVAL 2 DAY ELSE NULL END
FROM (
  SELECT ones.n + tens.n * 10 + 1 AS n
  FROM
    (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
     UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9) ones
  CROSS JOIN
    (SELECT 0 n UNION ALL SELECT 1 UNION ALL SELECT 2) tens
) seq
JOIN fact_orders o ON o.id = 1 + MOD(n * 13, 240)
WHERE n <= 24;

INSERT INTO risk_case_actions (id, case_id, action_type, operator, action_result, action_note, created_at)
SELECT
  c.id * 10 + action_seq.action_no,
  c.id,
  CASE action_seq.action_no WHEN 1 THEN 'review_order' WHEN 2 THEN 'warn_merchant' ELSE 'close_case' END,
  CASE MOD(c.id, 3) WHEN 0 THEN 'alice' WHEN 1 THEN 'bob' ELSE 'carol' END,
  CASE WHEN c.case_status = 'closed' AND action_seq.action_no = 3 THEN 'closed' ELSE 'recorded' END,
  CONCAT('mock action ', action_seq.action_no, ' for ', c.case_no),
  c.opened_at + INTERVAL action_seq.action_no HOUR
FROM risk_cases c
JOIN (
  SELECT 1 AS action_no UNION ALL SELECT 2 UNION ALL SELECT 3
) action_seq ON action_seq.action_no <= CASE WHEN c.case_status = 'closed' THEN 3 ELSE 2 END;
