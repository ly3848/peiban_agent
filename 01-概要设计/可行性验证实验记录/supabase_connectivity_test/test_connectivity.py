#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase 国内连通性验证测试脚本

功能：
1. 测试 PostgREST API 读写速度
2. 测试 Storage 图片加载速度
3. 测试域名解析连通性
4. 统计成功率和延迟

使用方法：
    python test_connectivity.py --url YOUR_SUPABASE_URL --key YOUR_API_KEY
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests


class SupabaseConnectivityTester:
    """Supabase 连通性测试器"""
    
    def __init__(self, supabase_url: str, api_key: str):
        """
        初始化测试器
        
        Args:
            supabase_url: Supabase 项目 URL (例如: https://xxx.supabase.co)
            api_key: Supabase API Key (anon key 或 service role key)
        """
        self.supabase_url = supabase_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
    def test_dns_resolution(self, domain: str = None) -> Dict:
        """
        测试域名解析连通性
        
        Args:
            domain: 要测试的域名，默认使用 Supabase URL 的域名
            
        Returns:
            包含测试结果的字典
        """
        if domain is None:
            from urllib.parse import urlparse
            domain = urlparse(self.supabase_url).netloc
        
        result = {
            "success": False,
            "domain": domain,
            "resolved_ips": [],
            "error": None
        }
        
        try:
            import socket
            ips = socket.gethostbyname_ex(domain)
            result["resolved_ips"] = ips[2]
            result["success"] = True
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def test_database_read(self, table_name: str = "test_ping", num_tests: int = 10) -> Dict:
        """
        测试数据库读取速度
        
        Args:
            table_name: 测试表名
            num_tests: 测试次数
            
        Returns:
            统计结果字典
        """
        url = f"{self.supabase_url}/rest/v1/{table_name}"
        
        latencies = []
        successful = 0
        
        print(f"\n测试数据库读取 ({table_name})...")
        
        for i in range(num_tests):
            try:
                t0 = time.time()
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=10
                )
                t1 = time.time()
                
                latency_ms = (t1 - t0) * 1000
                
                if response.status_code == 200:
                    latencies.append(latency_ms)
                    successful += 1
                    print(f"  [{i+1}/{num_tests}] ✓ {latency_ms:.0f}ms")
                else:
                    print(f"  [{i+1}/{num_tests}] ✗ HTTP {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                print(f"  [{i+1}/{num_tests}] ✗ 错误: {str(e)}")
            
            # 避免请求过快
            if i < num_tests - 1:
                time.sleep(0.5)
        
        if not latencies:
            return {
                "success": False,
                "error": "所有测试均失败",
                "successful_tests": 0,
                "total_tests": num_tests
            }
        
        return {
            "success": True,
            "successful_tests": successful,
            "total_tests": num_tests,
            "success_rate": successful / num_tests * 100,
            "latency": {
                "avg_ms": sum(latencies) / len(latencies),
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "all_values": latencies
            }
        }
    
    def test_database_write(self, table_name: str = "test_ping", num_tests: int = 10) -> Dict:
        """
        测试数据库写入速度
        
        Args:
            table_name: 测试表名
            num_tests: 测试次数
            
        Returns:
            统计结果字典
        """
        url = f"{self.supabase_url}/rest/v1/{table_name}"
        
        latencies = []
        successful = 0
        
        print(f"\n测试数据库写入 ({table_name})...")
        
        for i in range(num_tests):
            try:
                payload = {
                    "id": int(time.time() * 1000) + i,  # 唯一ID
                    "test_data": f"test_{i}",
                    "created_at": datetime.now().isoformat()
                }
                
                t0 = time.time()
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=10
                )
                t1 = time.time()
                
                latency_ms = (t1 - t0) * 1000
                
                if response.status_code in [200, 201]:
                    latencies.append(latency_ms)
                    successful += 1
                    print(f"  [{i+1}/{num_tests}] ✓ {latency_ms:.0f}ms")
                else:
                    print(f"  [{i+1}/{num_tests}] ✗ HTTP {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                print(f"  [{i+1}/{num_tests}] ✗ 错误: {str(e)}")
            
            # 避免请求过快
            if i < num_tests - 1:
                time.sleep(0.5)
        
        if not latencies:
            return {
                "success": False,
                "error": "所有测试均失败",
                "successful_tests": 0,
                "total_tests": num_tests
            }
        
        return {
            "success": True,
            "successful_tests": successful,
            "total_tests": num_tests,
            "success_rate": successful / num_tests * 100,
            "latency": {
                "avg_ms": sum(latencies) / len(latencies),
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "all_values": latencies
            }
        }
    
    def test_storage_download(self, bucket_name: str, file_path: str, num_tests: int = 10) -> Dict:
        """
        测试 Storage 文件下载速度
        
        Args:
            bucket_name: Storage bucket 名称
            file_path: 文件路径
            num_tests: 测试次数
            
        Returns:
            统计结果字典
        """
        # 获取公开 URL
        url = f"{self.supabase_url}/storage/v1/object/public/{bucket_name}/{file_path}"
        
        latencies = []
        file_sizes = []
        successful = 0
        
        print(f"\n测试 Storage 下载 ({bucket_name}/{file_path})...")
        
        for i in range(num_tests):
            try:
                t0 = time.time()
                response = requests.get(url, timeout=30, stream=True)
                t1 = time.time()
                
                latency_ms = (t1 - t0) * 1000
                
                if response.status_code == 200:
                    # 读取完整内容以获取文件大小
                    content = response.content
                    file_size = len(content)
                    file_sizes.append(file_size)
                    
                    latencies.append(latency_ms)
                    successful += 1
                    
                    size_kb = file_size / 1024
                    print(f"  [{i+1}/{num_tests}] ✓ {latency_ms:.0f}ms ({size_kb:.1f}KB)")
                else:
                    print(f"  [{i+1}/{num_tests}] ✗ HTTP {response.status_code}: {response.text[:100]}")
                    
            except Exception as e:
                print(f"  [{i+1}/{num_tests}] ✗ 错误: {str(e)}")
            
            # 避免请求过快
            if i < num_tests - 1:
                time.sleep(0.5)
        
        if not latencies:
            return {
                "success": False,
                "error": "所有测试均失败",
                "successful_tests": 0,
                "total_tests": num_tests
            }
        
        return {
            "success": True,
            "successful_tests": successful,
            "total_tests": num_tests,
            "success_rate": successful / num_tests * 100,
            "latency": {
                "avg_ms": sum(latencies) / len(latencies),
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "all_values": latencies
            },
            "file_size": {
                "avg_bytes": sum(file_sizes) / len(file_sizes) if file_sizes else 0,
                "min_bytes": min(file_sizes) if file_sizes else 0,
                "max_bytes": max(file_sizes) if file_sizes else 0
            }
        }
    
    def run_all_tests(
        self,
        table_name: str = "test_ping",
        bucket_name: Optional[str] = None,
        file_path: Optional[str] = None,
        num_tests: int = 10
    ) -> Dict:
        """
        运行所有测试
        
        Args:
            table_name: 测试表名
            bucket_name: Storage bucket 名称（可选）
            file_path: Storage 文件路径（可选）
            num_tests: 每个测试的次数
            
        Returns:
            所有测试结果的汇总
        """
        print(f"\n{'='*60}")
        print("Supabase 连通性测试")
        print(f"{'='*60}")
        print(f"Supabase URL: {self.supabase_url}")
        print(f"测试次数: {num_tests}")
        print(f"{'='*60}\n")
        
        results = {
            "test_time": datetime.now().isoformat(),
            "supabase_url": self.supabase_url,
            "dns": {},
            "database_read": {},
            "database_write": {},
            "storage_download": {}
        }
        
        # 1. DNS 解析测试
        print("1. 测试域名解析...")
        dns_result = self.test_dns_resolution()
        results["dns"] = dns_result
        if dns_result["success"]:
            print(f"  ✓ 域名解析成功: {', '.join(dns_result['resolved_ips'])}")
        else:
            print(f"  ✗ 域名解析失败: {dns_result['error']}")
        
        # 2. 数据库读取测试
        print("\n2. 测试数据库读取...")
        read_result = self.test_database_read(table_name, num_tests)
        results["database_read"] = read_result
        
        # 3. 数据库写入测试
        print("\n3. 测试数据库写入...")
        write_result = self.test_database_write(table_name, num_tests)
        results["database_write"] = write_result
        
        # 4. Storage 下载测试（如果提供了 bucket 和文件路径）
        if bucket_name and file_path:
            print("\n4. 测试 Storage 下载...")
            storage_result = self.test_storage_download(bucket_name, file_path, num_tests)
            results["storage_download"] = storage_result
        else:
            print("\n4. 跳过 Storage 下载测试（未提供 bucket 和文件路径）")
            results["storage_download"] = {"skipped": True}
        
        return results
    
    def print_summary(self, results: Dict):
        """打印测试总结"""
        print(f"\n{'='*60}")
        print("测试总结")
        print(f"{'='*60}")
        
        # DNS
        if results["dns"].get("success"):
            print(f"\n域名解析: ✓ 成功")
            print(f"  解析IP: {', '.join(results['dns']['resolved_ips'])}")
        else:
            print(f"\n域名解析: ✗ 失败")
            print(f"  错误: {results['dns'].get('error', 'Unknown')}")
        
        # 数据库读取
        if results["database_read"].get("success"):
            read = results["database_read"]
            print(f"\n数据库读取:")
            print(f"  成功率: {read['success_rate']:.1f}% ({read['successful_tests']}/{read['total_tests']})")
            print(f"  平均延迟: {read['latency']['avg_ms']:.0f}ms")
            print(f"  最小延迟: {read['latency']['min_ms']:.0f}ms")
            print(f"  最大延迟: {read['latency']['max_ms']:.0f}ms")
            
            # 评估
            avg = read['latency']['avg_ms']
            if avg < 800:
                print(f"  评估: ✓ 优秀 (< 800ms)")
            elif avg < 1500:
                print(f"  评估: ⚠ 可接受 (< 1500ms)")
            else:
                print(f"  评估: ✗ 需要优化 (> 1500ms)")
        else:
            print(f"\n数据库读取: ✗ 失败")
            print(f"  错误: {results['database_read'].get('error', 'Unknown')}")
        
        # 数据库写入
        if results["database_write"].get("success"):
            write = results["database_write"]
            print(f"\n数据库写入:")
            print(f"  成功率: {write['success_rate']:.1f}% ({write['successful_tests']}/{write['total_tests']})")
            print(f"  平均延迟: {write['latency']['avg_ms']:.0f}ms")
            print(f"  最小延迟: {write['latency']['min_ms']:.0f}ms")
            print(f"  最大延迟: {write['latency']['max_ms']:.0f}ms")
            
            # 评估
            avg = write['latency']['avg_ms']
            if avg < 800:
                print(f"  评估: ✓ 优秀 (< 800ms)")
            elif avg < 1500:
                print(f"  评估: ⚠ 可接受 (< 1500ms)")
            else:
                print(f"  评估: ✗ 需要优化 (> 1500ms)")
        else:
            print(f"\n数据库写入: ✗ 失败")
            print(f"  错误: {results['database_write'].get('error', 'Unknown')}")
        
        # Storage 下载
        if results["storage_download"].get("skipped"):
            print(f"\nStorage 下载: ⏭ 已跳过")
        elif results["storage_download"].get("success"):
            storage = results["storage_download"]
            print(f"\nStorage 下载:")
            print(f"  成功率: {storage['success_rate']:.1f}% ({storage['successful_tests']}/{storage['total_tests']})")
            print(f"  平均延迟: {storage['latency']['avg_ms']:.0f}ms")
            print(f"  最小延迟: {storage['latency']['min_ms']:.0f}ms")
            print(f"  最大延迟: {storage['latency']['max_ms']:.0f}ms")
            if "file_size" in storage:
                size_kb = storage['file_size']['avg_bytes'] / 1024
                print(f"  文件大小: {size_kb:.1f}KB")
            
            # 评估（100KB 图片 < 1s）
            avg = storage['latency']['avg_ms']
            if avg < 1000:
                print(f"  评估: ✓ 优秀 (< 1秒)")
            elif avg < 2000:
                print(f"  评估: ⚠ 可接受 (< 2秒)")
            else:
                print(f"  评估: ✗ 需要优化 (> 2秒)")
        else:
            print(f"\nStorage 下载: ✗ 失败")
            print(f"  错误: {results['storage_download'].get('error', 'Unknown')}")
        
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Supabase 国内连通性验证测试工具"
    )
    parser.add_argument(
        "--url",
        type=str,
        required=True,
        help="Supabase 项目 URL (例如: https://xxx.supabase.co，或设置环境变量 SUPABASE_URL)"
    )
    parser.add_argument(
        "--key",
        type=str,
        required=True,
        help="Supabase API Key (anon key 或 service role key，或设置环境变量 SUPABASE_KEY)"
    )
    parser.add_argument(
        "--table",
        type=str,
        default="test_ping",
        help="测试表名 (默认: test_ping)"
    )
    parser.add_argument(
        "--bucket",
        type=str,
        help="Storage bucket 名称 (可选)"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Storage 文件路径 (可选，需要与 --bucket 一起使用)"
    )
    parser.add_argument(
        "--num-tests",
        type=int,
        default=10,
        help="每个测试的次数 (默认: 10)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="结果输出文件路径 (JSON格式)"
    )
    
    args = parser.parse_args()
    
    # 从环境变量获取配置（如果命令行未提供）
    supabase_url = args.url or os.getenv("SUPABASE_URL")
    api_key = args.key or os.getenv("SUPABASE_KEY")
    
    if not supabase_url:
        print("错误: 请提供 Supabase URL (--url 或环境变量 SUPABASE_URL)")
        sys.exit(1)
    
    if not api_key:
        print("错误: 请提供 Supabase API Key (--key 或环境变量 SUPABASE_KEY)")
        sys.exit(1)
    
    # 创建测试器
    tester = SupabaseConnectivityTester(
        supabase_url=supabase_url,
        api_key=api_key
    )
    
    # 运行所有测试
    results = tester.run_all_tests(
        table_name=args.table,
        bucket_name=args.bucket,
        file_path=args.file,
        num_tests=args.num_tests
    )
    
    # 打印总结
    tester.print_summary(results)
    
    # 保存结果到文件
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到: {args.output}")
    
    # 返回退出码
    success = (
        results["database_read"].get("success", False) and
        results["database_write"].get("success", False)
    )
    
    if not success:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

