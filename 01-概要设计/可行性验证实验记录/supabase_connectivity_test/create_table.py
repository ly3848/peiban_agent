#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建 Supabase 测试表的辅助脚本
使用 PostgreSQL 连接直接创建表
"""

import psycopg2
import sys

# PostgreSQL 连接字符串
DATABASE_URL = "postgresql://postgres:w123456789.@db.euzzmtqrmdlbaanjizlt.supabase.co:5432/postgres"

# 创建表的 SQL
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS test_ping (
  id BIGSERIAL PRIMARY KEY,
  test_data TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 插入一条测试数据
INSERT INTO test_ping (test_data) 
VALUES ('Initial test data')
ON CONFLICT DO NOTHING;

-- 启用 RLS
ALTER TABLE test_ping ENABLE ROW LEVEL SECURITY;

-- 删除现有策略（如果存在）
DROP POLICY IF EXISTS "Allow all read" ON test_ping;
DROP POLICY IF EXISTS "Allow all insert" ON test_ping;
DROP POLICY IF EXISTS "Allow all update" ON test_ping;
DROP POLICY IF EXISTS "Allow all delete" ON test_ping;

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
"""

def main():
    try:
        print("正在连接到 Supabase 数据库...")
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("正在创建测试表 test_ping...")
        cursor.execute(CREATE_TABLE_SQL)
        
        print("✓ 测试表创建成功！")
        
        # 验证表是否存在
        cursor.execute("SELECT COUNT(*) FROM test_ping;")
        count = cursor.fetchone()[0]
        print(f"✓ 表中现有数据: {count} 条")
        
        cursor.close()
        conn.close()
        
        print("\n现在可以运行测试脚本了：")
        print("python test_connectivity.py --url https://euzzmtqrmdlbaanjizlt.supabase.co --key <your-key> --table test_ping")
        
    except ImportError:
        print("错误: 需要安装 psycopg2")
        print("请运行: pip install psycopg2-binary")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

