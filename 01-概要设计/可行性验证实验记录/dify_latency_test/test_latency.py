#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify API + LLM 延迟与流式响应测试脚本

功能：
1. 测试 Dify API 流式响应的首字延迟 (TTFB)
2. 测试完整生成时间
3. 验证 SSE 连接的稳定性
4. 支持多次测试并统计平均值

使用方法：
    python test_latency.py --api-key YOUR_API_KEY --app-id YOUR_APP_ID --network wifi
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


class DifyLatencyTester:
    """Dify API 延迟测试器"""
    
    def __init__(self, api_key: str, app_id: Optional[str] = None, base_url: str = "https://api.dify.ai/v1"):
        """
        初始化测试器
        
        Args:
            api_key: Dify API Key
            app_id: Dify Application ID (可选，应用级 API Key 可能不需要)
            base_url: Dify API 基础URL，默认为官方地址
        """
        self.api_key = api_key
        self.app_id = app_id
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def test_streaming_chat(
        self, 
        query: str, 
        user_id: str = "test_user",
        timeout: int = 60
    ) -> Dict:
        """
        测试流式聊天请求
        
        Args:
            query: 用户输入的查询文本
            user_id: 用户ID
            timeout: 请求超时时间（秒）
            
        Returns:
            包含测试结果的字典：
            {
                "success": bool,
                "ttfb_ms": float,  # 首字延迟（毫秒）
                "total_time_ms": float,  # 总耗时（毫秒）
                "first_char": str,  # 第一个字符
                "full_response": str,  # 完整响应
                "char_count": int,  # 字符数
                "error": str,  # 错误信息（如果有）
                "response_chunks": List[str]  # 所有响应块
            }
        """
        # 确保 URL 拼接正确
        base = self.base_url.rstrip('/')
        url = f"{base}/chat-messages"
        
        payload = {
            "inputs": {},
            "query": query,
            "response_mode": "streaming",
            "conversation_id": "",
            "user": user_id
        }
        
        result = {
            "success": False,
            "ttfb_ms": None,
            "total_time_ms": None,
            "first_char": None,
            "full_response": "",
            "char_count": 0,
            "error": None,
            "response_chunks": []
        }
        
        try:
            t0 = time.time()  # 发送时间
            
            # 发起流式请求
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                stream=True,
                timeout=timeout
            )
            
            if response.status_code != 200:
                result["error"] = f"HTTP {response.status_code}: {response.text}"
                return result
            
            t1 = None  # 收到第一个字符的时间
            first_char_received = False
            full_response = ""
            
            # 解析 SSE 流
            for line in response.iter_lines():
                if not line:
                    continue
                    
                # SSE 格式：data: {...}
                if line.startswith(b"data: "):
                    data_str = line[6:].decode('utf-8')
                    
                    # 跳过结束标记
                    if data_str.strip() == "[DONE]":
                        break
                    
                    try:
                        data = json.loads(data_str)
                        
                        # 记录第一个字符的时间
                        if not first_char_received:
                            t1 = time.time()
                            first_char_received = True
                            
                            # 提取第一个字符
                            if "answer" in data:
                                result["first_char"] = data["answer"][0] if data["answer"] else ""
                            elif "text" in data:
                                result["first_char"] = data["text"][0] if data["text"] else ""
                        
                        # 提取响应内容
                        chunk_text = ""
                        if "answer" in data:
                            chunk_text = data["answer"]
                        elif "text" in data:
                            chunk_text = data["text"]
                        elif "content" in data:
                            chunk_text = data["content"]
                        
                        if chunk_text:
                            result["response_chunks"].append(chunk_text)
                            full_response += chunk_text
                            
                    except json.JSONDecodeError as e:
                        print(f"Warning: Failed to parse JSON: {data_str[:100]}...", file=sys.stderr)
                        continue
            
            t2 = time.time()  # 连接结束时间
            
            if t1 is None:
                result["error"] = "未收到任何响应数据"
                return result
            
            # 计算延迟
            result["ttfb_ms"] = (t1 - t0) * 1000
            result["total_time_ms"] = (t2 - t0) * 1000
            result["full_response"] = full_response
            result["char_count"] = len(full_response)
            result["success"] = True
            
        except requests.exceptions.Timeout:
            result["error"] = f"请求超时（>{timeout}秒）"
        except requests.exceptions.RequestException as e:
            result["error"] = f"请求异常: {str(e)}"
        except Exception as e:
            result["error"] = f"未知错误: {str(e)}"
        
        return result
    
    def run_batch_tests(
        self, 
        query: str,
        num_tests: int = 10,
        network_type: str = "unknown"
    ) -> Dict:
        """
        批量运行测试
        
        Args:
            query: 测试查询文本
            num_tests: 测试次数
            network_type: 网络类型（wifi/4g/5g等）
            
        Returns:
            统计结果字典
        """
        print(f"\n{'='*60}")
        print(f"开始批量测试 - 网络类型: {network_type}")
        print(f"测试次数: {num_tests}")
        print(f"查询文本: {query[:50]}...")
        print(f"{'='*60}\n")
        
        results = []
        successful_tests = []
        
        for i in range(1, num_tests + 1):
            print(f"[{i}/{num_tests}] 正在测试...", end=" ", flush=True)
            
            result = self.test_streaming_chat(query)
            results.append(result)
            
            if result["success"]:
                successful_tests.append(result)
                print(f"✓ TTFB: {result['ttfb_ms']:.0f}ms, "
                      f"总耗时: {result['total_time_ms']:.0f}ms, "
                      f"字符数: {result['char_count']}")
            else:
                print(f"✗ 失败: {result['error']}")
            
            # 避免请求过快
            if i < num_tests:
                time.sleep(1)
        
        # 统计结果
        if not successful_tests:
            return {
                "network_type": network_type,
                "total_tests": num_tests,
                "successful_tests": 0,
                "success_rate": 0.0,
                "error": "所有测试均失败"
            }
        
        ttfb_list = [r["ttfb_ms"] for r in successful_tests]
        total_time_list = [r["total_time_ms"] for r in successful_tests]
        char_count_list = [r["char_count"] for r in successful_tests]
        
        stats = {
            "network_type": network_type,
            "total_tests": num_tests,
            "successful_tests": len(successful_tests),
            "success_rate": len(successful_tests) / num_tests * 100,
            "ttfb": {
                "avg_ms": sum(ttfb_list) / len(ttfb_list),
                "min_ms": min(ttfb_list),
                "max_ms": max(ttfb_list),
                "all_values": ttfb_list
            },
            "total_time": {
                "avg_ms": sum(total_time_list) / len(total_time_list),
                "min_ms": min(total_time_list),
                "max_ms": max(total_time_list),
                "all_values": total_time_list
            },
            "char_count": {
                "avg": sum(char_count_list) / len(char_count_list),
                "min": min(char_count_list),
                "max": max(char_count_list)
            },
            "streaming_stable": all(
                len(r["response_chunks"]) > 0 for r in successful_tests
            )
        }
        
        return stats
    
    def print_statistics(self, stats: Dict):
        """打印统计结果"""
        print(f"\n{'='*60}")
        print("测试统计结果")
        print(f"{'='*60}")
        print(f"网络类型: {stats['network_type']}")
        print(f"总测试次数: {stats['total_tests']}")
        print(f"成功次数: {stats['successful_tests']}")
        print(f"成功率: {stats['success_rate']:.1f}%")
        
        if stats.get('error'):
            print(f"\n错误信息: {stats['error']}")
            print(f"{'='*60}\n")
            return
        
        if stats['successful_tests'] == 0:
            print("\n⚠ 所有测试均失败，无法计算统计数据")
            print(f"{'='*60}\n")
            return
        
        print(f"\n首字延迟 (TTFB):")
        print(f"  平均: {stats['ttfb']['avg_ms']:.0f} ms")
        print(f"  最小: {stats['ttfb']['min_ms']:.0f} ms")
        print(f"  最大: {stats['ttfb']['max_ms']:.0f} ms")
        print(f"\n总耗时:")
        print(f"  平均: {stats['total_time']['avg_ms']:.0f} ms")
        print(f"  最小: {stats['total_time']['min_ms']:.0f} ms")
        print(f"  最大: {stats['total_time']['max_ms']:.0f} ms")
        print(f"\n响应字符数:")
        print(f"  平均: {stats['char_count']['avg']:.0f}")
        print(f"  最小: {stats['char_count']['min']}")
        print(f"  最大: {stats['char_count']['max']}")
        print(f"\n流式解析稳定性: {'✓ 正常' if stats['streaming_stable'] else '✗ 异常'}")
        print(f"{'='*60}\n")
        
        # 评估结果
        avg_ttfb = stats['ttfb']['avg_ms']
        if avg_ttfb < 1500:
            print("✓ 首字延迟评估: 优秀 (< 1.5秒)")
        elif avg_ttfb < 3000:
            print("⚠ 首字延迟评估: 可接受 (< 3秒)")
        else:
            print("✗ 首字延迟评估: 需要优化 (> 3秒)")


def main():
    parser = argparse.ArgumentParser(
        description="Dify API + LLM 延迟与流式响应测试工具"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        required=True,
        help="Dify API Key (或设置环境变量 DIFY_API_KEY)"
    )
    parser.add_argument(
        "--app-id",
        type=str,
        required=False,
        help="Dify Application ID (可选，应用级 API Key 可能不需要，或设置环境变量 DIFY_APP_ID)"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="https://api.dify.ai/v1",
        help="Dify API 基础URL (默认: https://api.dify.ai/v1)"
    )
    parser.add_argument(
        "--query",
        type=str,
        default="你好，我想和你聊聊天。今天天气不错，你觉得我们应该聊些什么有趣的话题呢？",
        help="测试查询文本（默认: 50字左右的测试文本）"
    )
    parser.add_argument(
        "--network",
        type=str,
        default="unknown",
        choices=["wifi", "4g", "5g", "unknown"],
        help="网络类型 (wifi/4g/5g/unknown)"
    )
    parser.add_argument(
        "--num-tests",
        type=int,
        default=10,
        help="测试次数 (默认: 10)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="结果输出文件路径 (JSON格式)"
    )
    
    args = parser.parse_args()
    
    # 从环境变量获取配置（如果命令行未提供）
    api_key = args.api_key or os.getenv("DIFY_API_KEY")
    app_id = args.app_id or os.getenv("DIFY_APP_ID")
    
    if not api_key:
        print("错误: 请提供 Dify API Key (--api-key 或环境变量 DIFY_API_KEY)")
        sys.exit(1)
    
    # app_id 是可选的，应用级 API Key 可能不需要
    if not app_id:
        print("提示: 未提供 Application ID，将使用应用级 API Key 进行测试")
    
    # 创建测试器
    tester = DifyLatencyTester(
        api_key=api_key,
        app_id=app_id,
        base_url=args.base_url
    )
    
    # 运行批量测试
    stats = tester.run_batch_tests(
        query=args.query,
        num_tests=args.num_tests,
        network_type=args.network
    )
    
    # 打印统计结果
    tester.print_statistics(stats)
    
    # 保存结果到文件
    if args.output:
        output_data = {
            "test_time": datetime.now().isoformat(),
            "config": {
                "base_url": args.base_url,
                "app_id": app_id or "N/A (应用级 API Key)",
                "network_type": args.network,
                "query": args.query,
                "num_tests": args.num_tests
            },
            "statistics": stats
        }
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到: {args.output}")
    
    # 返回退出码
    if stats["success_rate"] < 50:
        sys.exit(1)
    elif stats["ttfb"]["avg_ms"] > 3000:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

