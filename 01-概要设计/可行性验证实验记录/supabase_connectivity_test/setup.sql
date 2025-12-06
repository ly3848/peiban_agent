-- Supabase 连通性测试 - 数据库表创建脚本
-- 在 Supabase SQL Editor 中执行此脚本

-- 创建测试表
CREATE TABLE IF NOT EXISTS test_ping (
  id BIGSERIAL PRIMARY KEY,
  test_data TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 插入一条测试数据
INSERT INTO test_ping (test_data) 
VALUES ('Initial test data');

-- 如果需要允许匿名访问（使用 anon key），需要配置 RLS 策略
-- 注意：这会让表对所有用户可读可写，仅用于测试

-- 启用 RLS
ALTER TABLE test_ping ENABLE ROW LEVEL SECURITY;

-- 允许所有人读取
CREATE POLICY "Allow all read" ON test_ping
  FOR SELECT
  USING (true);

-- 允许所有人插入
CREATE POLICY "Allow all insert" ON test_ping
  FOR INSERT
  WITH CHECK (true);

-- 允许所有人更新
CREATE POLICY "Allow all update" ON test_ping
  FOR UPDATE
  USING (true);

-- 允许所有人删除
CREATE POLICY "Allow all delete" ON test_ping
  FOR DELETE
  USING (true);

