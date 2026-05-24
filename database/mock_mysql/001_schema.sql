CREATE DATABASE IF NOT EXISTS x_agent_mock_biz
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE x_agent_mock_biz;

DROP TABLE IF EXISTS risk_case_actions;
DROP TABLE IF EXISTS risk_cases;
DROP TABLE IF EXISTS risk_rule_hits;
DROP TABLE IF EXISTS risk_rules;
DROP TABLE IF EXISTS risk_merchant_profiles;
DROP TABLE IF EXISTS risk_user_profiles;
DROP TABLE IF EXISTS fact_user_events;
DROP TABLE IF EXISTS fact_refunds;
DROP TABLE IF EXISTS fact_payments;
DROP TABLE IF EXISTS fact_order_items;
DROP TABLE IF EXISTS fact_orders;
DROP TABLE IF EXISTS dim_products;
DROP TABLE IF EXISTS dim_categories;
DROP TABLE IF EXISTS dim_merchants;
DROP TABLE IF EXISTS dim_users;
DROP TABLE IF EXISTS dim_regions;

CREATE TABLE dim_regions (
  id BIGINT PRIMARY KEY,
  region_code VARCHAR(32) NOT NULL UNIQUE COMMENT '区域编码',
  region_name VARCHAR(64) NOT NULL COMMENT '区域名称',
  province VARCHAR(64) NOT NULL COMMENT '省份',
  city VARCHAR(64) NOT NULL COMMENT '城市',
  tier TINYINT NOT NULL COMMENT '城市等级, 1 表示一线城市',
  created_at DATETIME NOT NULL COMMENT '创建时间'
) COMMENT='区域维表, 用于按省份、城市和城市等级进行统计分析';

CREATE TABLE dim_users (
  id BIGINT PRIMARY KEY,
  user_no VARCHAR(64) NOT NULL UNIQUE COMMENT '用户业务编号',
  region_id BIGINT NOT NULL COMMENT '注册区域 ID',
  gender VARCHAR(16) NOT NULL COMMENT '性别',
  age INT NOT NULL COMMENT '年龄',
  registered_at DATETIME NOT NULL COMMENT '注册时间',
  status VARCHAR(32) NOT NULL COMMENT '用户状态: active, frozen, closed',
  created_at DATETIME NOT NULL COMMENT '创建时间',
  CONSTRAINT fk_dim_users_region FOREIGN KEY (region_id) REFERENCES dim_regions(id),
  INDEX idx_dim_users_region (region_id),
  INDEX idx_dim_users_registered_at (registered_at)
) COMMENT='用户维表, 记录用户基础属性和注册区域';

CREATE TABLE dim_merchants (
  id BIGINT PRIMARY KEY,
  merchant_no VARCHAR(64) NOT NULL UNIQUE COMMENT '商户业务编号',
  merchant_name VARCHAR(128) NOT NULL COMMENT '商户名称',
  region_id BIGINT NOT NULL COMMENT '经营区域 ID',
  category VARCHAR(64) NOT NULL COMMENT '商户经营类型',
  onboarded_at DATETIME NOT NULL COMMENT '入驻时间',
  status VARCHAR(32) NOT NULL COMMENT '商户状态: active, suspended, closed',
  created_at DATETIME NOT NULL COMMENT '创建时间',
  CONSTRAINT fk_dim_merchants_region FOREIGN KEY (region_id) REFERENCES dim_regions(id),
  INDEX idx_dim_merchants_region (region_id),
  INDEX idx_dim_merchants_status (status)
) COMMENT='商户维表, 记录平台商户基础属性';

CREATE TABLE dim_categories (
  id BIGINT PRIMARY KEY,
  category_code VARCHAR(32) NOT NULL UNIQUE COMMENT '类目编码',
  category_name VARCHAR(64) NOT NULL COMMENT '类目名称',
  parent_id BIGINT NULL COMMENT '父类目 ID',
  level TINYINT NOT NULL COMMENT '类目层级',
  created_at DATETIME NOT NULL COMMENT '创建时间',
  CONSTRAINT fk_dim_categories_parent FOREIGN KEY (parent_id) REFERENCES dim_categories(id)
) COMMENT='商品类目维表, 支持按商品类目聚合分析';

CREATE TABLE dim_products (
  id BIGINT PRIMARY KEY,
  product_no VARCHAR(64) NOT NULL UNIQUE COMMENT '商品业务编号',
  merchant_id BIGINT NOT NULL COMMENT '所属商户 ID',
  category_id BIGINT NOT NULL COMMENT '所属类目 ID',
  product_name VARCHAR(128) NOT NULL COMMENT '商品名称',
  list_price DECIMAL(12,2) NOT NULL COMMENT '挂牌价',
  status VARCHAR(32) NOT NULL COMMENT '商品状态: active, offline',
  created_at DATETIME NOT NULL COMMENT '创建时间',
  CONSTRAINT fk_dim_products_merchant FOREIGN KEY (merchant_id) REFERENCES dim_merchants(id),
  CONSTRAINT fk_dim_products_category FOREIGN KEY (category_id) REFERENCES dim_categories(id),
  INDEX idx_dim_products_merchant (merchant_id),
  INDEX idx_dim_products_category (category_id)
) COMMENT='商品维表, 记录商品所属商户、类目和价格信息';

CREATE TABLE fact_orders (
  id BIGINT PRIMARY KEY,
  order_no VARCHAR(64) NOT NULL UNIQUE COMMENT '订单业务编号',
  user_id BIGINT NOT NULL COMMENT '下单用户 ID',
  merchant_id BIGINT NOT NULL COMMENT '订单商户 ID',
  region_id BIGINT NOT NULL COMMENT '下单区域 ID',
  order_status VARCHAR(32) NOT NULL COMMENT '订单状态: created, paid, cancelled, refunded',
  total_amount DECIMAL(12,2) NOT NULL COMMENT '订单应付金额',
  discount_amount DECIMAL(12,2) NOT NULL COMMENT '优惠金额',
  payable_amount DECIMAL(12,2) NOT NULL COMMENT '实际应付金额',
  created_at DATETIME NOT NULL COMMENT '下单时间',
  paid_at DATETIME NULL COMMENT '支付时间',
  cancelled_at DATETIME NULL COMMENT '取消时间',
  CONSTRAINT fk_fact_orders_user FOREIGN KEY (user_id) REFERENCES dim_users(id),
  CONSTRAINT fk_fact_orders_merchant FOREIGN KEY (merchant_id) REFERENCES dim_merchants(id),
  CONSTRAINT fk_fact_orders_region FOREIGN KEY (region_id) REFERENCES dim_regions(id),
  INDEX idx_fact_orders_created_at (created_at),
  INDEX idx_fact_orders_user (user_id),
  INDEX idx_fact_orders_merchant (merchant_id),
  INDEX idx_fact_orders_status (order_status)
) COMMENT='订单事实表, 记录订单主数据, 常用于订单数、GMV、客单价等统计';

CREATE TABLE fact_order_items (
  id BIGINT PRIMARY KEY,
  order_id BIGINT NOT NULL COMMENT '订单 ID',
  product_id BIGINT NOT NULL COMMENT '商品 ID',
  quantity INT NOT NULL COMMENT '购买数量',
  item_amount DECIMAL(12,2) NOT NULL COMMENT '明细应付金额',
  discount_amount DECIMAL(12,2) NOT NULL COMMENT '明细优惠金额',
  created_at DATETIME NOT NULL COMMENT '创建时间',
  CONSTRAINT fk_fact_order_items_order FOREIGN KEY (order_id) REFERENCES fact_orders(id),
  CONSTRAINT fk_fact_order_items_product FOREIGN KEY (product_id) REFERENCES dim_products(id),
  INDEX idx_fact_order_items_order (order_id),
  INDEX idx_fact_order_items_product (product_id)
) COMMENT='订单明细事实表, 用于商品、类目和明细金额分析';

CREATE TABLE fact_payments (
  id BIGINT PRIMARY KEY,
  payment_no VARCHAR(64) NOT NULL UNIQUE COMMENT '支付流水号',
  order_id BIGINT NOT NULL COMMENT '订单 ID',
  user_id BIGINT NOT NULL COMMENT '支付用户 ID',
  channel VARCHAR(32) NOT NULL COMMENT '支付渠道: alipay, wechat, bank_card, balance',
  payment_status VARCHAR(32) NOT NULL COMMENT '支付状态: paid, failed, processing',
  amount DECIMAL(12,2) NOT NULL COMMENT '支付金额',
  paid_at DATETIME NOT NULL COMMENT '支付发起或完成时间',
  failure_reason VARCHAR(128) NULL COMMENT '支付失败原因',
  CONSTRAINT fk_fact_payments_order FOREIGN KEY (order_id) REFERENCES fact_orders(id),
  CONSTRAINT fk_fact_payments_user FOREIGN KEY (user_id) REFERENCES dim_users(id),
  INDEX idx_fact_payments_order (order_id),
  INDEX idx_fact_payments_user (user_id),
  INDEX idx_fact_payments_paid_at (paid_at),
  INDEX idx_fact_payments_status (payment_status)
) COMMENT='支付事实表, 记录支付流水, 用于支付金额、支付成功率等统计';

CREATE TABLE fact_refunds (
  id BIGINT PRIMARY KEY,
  refund_no VARCHAR(64) NOT NULL UNIQUE COMMENT '退款流水号',
  order_id BIGINT NOT NULL COMMENT '订单 ID',
  payment_id BIGINT NOT NULL COMMENT '支付流水 ID',
  refund_status VARCHAR(32) NOT NULL COMMENT '退款状态: success, failed, processing',
  refund_reason VARCHAR(128) NOT NULL COMMENT '退款原因',
  refund_amount DECIMAL(12,2) NOT NULL COMMENT '退款金额',
  requested_at DATETIME NOT NULL COMMENT '退款申请时间',
  completed_at DATETIME NULL COMMENT '退款完成时间',
  CONSTRAINT fk_fact_refunds_order FOREIGN KEY (order_id) REFERENCES fact_orders(id),
  CONSTRAINT fk_fact_refunds_payment FOREIGN KEY (payment_id) REFERENCES fact_payments(id),
  INDEX idx_fact_refunds_order (order_id),
  INDEX idx_fact_refunds_requested_at (requested_at),
  INDEX idx_fact_refunds_status (refund_status)
) COMMENT='退款事实表, 用于退款金额、退款率和异常退款分析';

CREATE TABLE fact_user_events (
  id BIGINT PRIMARY KEY,
  user_id BIGINT NOT NULL COMMENT '用户 ID',
  event_type VARCHAR(64) NOT NULL COMMENT '行为类型: login, view_product, add_cart, submit_order',
  product_id BIGINT NULL COMMENT '关联商品 ID',
  merchant_id BIGINT NULL COMMENT '关联商户 ID',
  device_type VARCHAR(32) NOT NULL COMMENT '设备类型: ios, android, web',
  ip_region_id BIGINT NOT NULL COMMENT 'IP 解析区域 ID',
  occurred_at DATETIME NOT NULL COMMENT '行为发生时间',
  CONSTRAINT fk_fact_user_events_user FOREIGN KEY (user_id) REFERENCES dim_users(id),
  CONSTRAINT fk_fact_user_events_product FOREIGN KEY (product_id) REFERENCES dim_products(id),
  CONSTRAINT fk_fact_user_events_merchant FOREIGN KEY (merchant_id) REFERENCES dim_merchants(id),
  CONSTRAINT fk_fact_user_events_region FOREIGN KEY (ip_region_id) REFERENCES dim_regions(id),
  INDEX idx_fact_user_events_user (user_id),
  INDEX idx_fact_user_events_type (event_type),
  INDEX idx_fact_user_events_occurred_at (occurred_at)
) COMMENT='用户行为事实表, 用于漏斗、活跃和异常行为分析';

CREATE TABLE risk_user_profiles (
  user_id BIGINT PRIMARY KEY,
  risk_level VARCHAR(32) NOT NULL COMMENT '用户风险等级: low, medium, high',
  risk_score DECIMAL(6,2) NOT NULL COMMENT '用户风险分',
  is_blacklisted TINYINT(1) NOT NULL COMMENT '是否黑名单用户',
  last_evaluated_at DATETIME NOT NULL COMMENT '最近评估时间',
  CONSTRAINT fk_risk_user_profiles_user FOREIGN KEY (user_id) REFERENCES dim_users(id),
  INDEX idx_risk_user_profiles_level (risk_level),
  INDEX idx_risk_user_profiles_score (risk_score)
) COMMENT='用户风控画像表, 用于用户风险分层和黑名单分析';

CREATE TABLE risk_merchant_profiles (
  merchant_id BIGINT PRIMARY KEY,
  risk_level VARCHAR(32) NOT NULL COMMENT '商户风险等级: low, medium, high',
  risk_score DECIMAL(6,2) NOT NULL COMMENT '商户风险分',
  abnormal_refund_rate DECIMAL(8,4) NOT NULL COMMENT '异常退款率',
  last_evaluated_at DATETIME NOT NULL COMMENT '最近评估时间',
  CONSTRAINT fk_risk_merchant_profiles_merchant FOREIGN KEY (merchant_id) REFERENCES dim_merchants(id),
  INDEX idx_risk_merchant_profiles_level (risk_level)
) COMMENT='商户风控画像表, 用于商户风险分层和异常退款分析';

CREATE TABLE risk_rules (
  id BIGINT PRIMARY KEY,
  rule_code VARCHAR(64) NOT NULL UNIQUE COMMENT '规则编码',
  rule_name VARCHAR(128) NOT NULL COMMENT '规则名称',
  rule_type VARCHAR(64) NOT NULL COMMENT '规则类型: user, merchant, payment, refund',
  severity VARCHAR(32) NOT NULL COMMENT '严重级别: low, medium, high',
  enabled TINYINT(1) NOT NULL COMMENT '是否启用',
  created_at DATETIME NOT NULL COMMENT '创建时间'
) COMMENT='风控规则表, 记录规则元数据和严重级别';

CREATE TABLE risk_rule_hits (
  id BIGINT PRIMARY KEY,
  rule_id BIGINT NOT NULL COMMENT '命中规则 ID',
  user_id BIGINT NULL COMMENT '命中用户 ID',
  merchant_id BIGINT NULL COMMENT '命中商户 ID',
  order_id BIGINT NULL COMMENT '关联订单 ID',
  payment_id BIGINT NULL COMMENT '关联支付 ID',
  hit_score DECIMAL(6,2) NOT NULL COMMENT '命中分数',
  hit_detail VARCHAR(255) NOT NULL COMMENT '命中详情',
  hit_at DATETIME NOT NULL COMMENT '命中时间',
  CONSTRAINT fk_risk_rule_hits_rule FOREIGN KEY (rule_id) REFERENCES risk_rules(id),
  CONSTRAINT fk_risk_rule_hits_user FOREIGN KEY (user_id) REFERENCES dim_users(id),
  CONSTRAINT fk_risk_rule_hits_merchant FOREIGN KEY (merchant_id) REFERENCES dim_merchants(id),
  CONSTRAINT fk_risk_rule_hits_order FOREIGN KEY (order_id) REFERENCES fact_orders(id),
  CONSTRAINT fk_risk_rule_hits_payment FOREIGN KEY (payment_id) REFERENCES fact_payments(id),
  INDEX idx_risk_rule_hits_rule (rule_id),
  INDEX idx_risk_rule_hits_user (user_id),
  INDEX idx_risk_rule_hits_order (order_id),
  INDEX idx_risk_rule_hits_hit_at (hit_at)
) COMMENT='风控规则命中事实表, 用于风险事件和规则效果分析';

CREATE TABLE risk_cases (
  id BIGINT PRIMARY KEY,
  case_no VARCHAR(64) NOT NULL UNIQUE COMMENT '风控案件编号',
  user_id BIGINT NULL COMMENT '案件用户 ID',
  merchant_id BIGINT NULL COMMENT '案件商户 ID',
  order_id BIGINT NULL COMMENT '关联订单 ID',
  case_type VARCHAR(64) NOT NULL COMMENT '案件类型: fraud, refund_abuse, merchant_abuse',
  case_status VARCHAR(32) NOT NULL COMMENT '案件状态: open, reviewing, closed',
  priority VARCHAR(32) NOT NULL COMMENT '优先级: low, medium, high',
  opened_at DATETIME NOT NULL COMMENT '开案时间',
  closed_at DATETIME NULL COMMENT '结案时间',
  CONSTRAINT fk_risk_cases_user FOREIGN KEY (user_id) REFERENCES dim_users(id),
  CONSTRAINT fk_risk_cases_merchant FOREIGN KEY (merchant_id) REFERENCES dim_merchants(id),
  CONSTRAINT fk_risk_cases_order FOREIGN KEY (order_id) REFERENCES fact_orders(id),
  INDEX idx_risk_cases_status (case_status),
  INDEX idx_risk_cases_opened_at (opened_at)
) COMMENT='风控案件表, 用于风险处置和案件效率分析';

CREATE TABLE risk_case_actions (
  id BIGINT PRIMARY KEY,
  case_id BIGINT NOT NULL COMMENT '风控案件 ID',
  action_type VARCHAR(64) NOT NULL COMMENT '处置动作: freeze_user, review_order, warn_merchant, close_case',
  operator VARCHAR(64) NOT NULL COMMENT '操作人',
  action_result VARCHAR(64) NOT NULL COMMENT '处置结果',
  action_note VARCHAR(255) NOT NULL COMMENT '处置说明',
  created_at DATETIME NOT NULL COMMENT '处置时间',
  CONSTRAINT fk_risk_case_actions_case FOREIGN KEY (case_id) REFERENCES risk_cases(id),
  INDEX idx_risk_case_actions_case (case_id),
  INDEX idx_risk_case_actions_created_at (created_at)
) COMMENT='风控案件处置动作表, 用于追踪案件处理过程';
