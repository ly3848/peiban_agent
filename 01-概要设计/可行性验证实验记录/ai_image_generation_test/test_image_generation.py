#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 绘图 (Stable Diffusion) 风格一致性测试脚本

功能：
1. 使用硅基流动 API 生成图片
2. 测试风格一致性
3. 记录生成时间和质量
4. 保存生成的图片

使用方法：
    python test_image_generation.py --api-key YOUR_API_KEY --num-images 10
"""

import argparse
import base64
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests


class ImageGenerationTester:
    """AI 图片生成测试器"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.siliconflow.cn/v1"):
        """
        初始化测试器
        
        Args:
            api_key: 硅基流动 API Key
            base_url: API 基础 URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        model: str = "stable-diffusion-xl-base-1.0",
        width: int = 512,
        height: int = 512,
        num_inference_steps: int = 20,
        timeout: int = 60
    ) -> Dict:
        """
        生成单张图片
        
        Args:
            prompt: 正向提示词
            negative_prompt: 反向提示词
            model: 模型名称
            width: 图片宽度
            height: 图片高度
            num_inference_steps: 推理步数
            timeout: 超时时间（秒）
            
        Returns:
            包含生成结果的字典
        """
        # 硅基流动使用 images/generations 端点
        endpoint = f"{self.base_url}/images/generations"
        
        result = {
            "success": False,
            "image_url": None,
            "image_base64": None,
            "generation_time_ms": None,
            "error": None,
            "response_data": None
        }
        
        payload = {
            "model": model,
            "prompt": prompt,
            "width": width,
            "height": height,
            "num_inference_steps": num_inference_steps,
        }
        
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        
        try:
            t0 = time.time()
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=timeout
            )
            t1 = time.time()
            
            generation_time_ms = (t1 - t0) * 1000
            result["generation_time_ms"] = generation_time_ms
            
            if response.status_code == 200:
                data = response.json()
                result["response_data"] = data
                
                # 硅基流动返回格式: {"images": [{"url": "..."}]}
                if "images" in data and len(data["images"]) > 0:
                    image_data = data["images"][0]
                    if "url" in image_data:
                        result["image_url"] = image_data["url"]
                    elif "b64_json" in image_data:
                        result["image_base64"] = image_data["b64_json"]
                
                # 也尝试 data 字段（兼容其他格式）
                if "data" in data and len(data["data"]) > 0:
                    image_data = data["data"][0]
                    if "url" in image_data:
                        result["image_url"] = image_data["url"]
                    elif "b64_json" in image_data:
                        result["image_base64"] = image_data["b64_json"]
                
                if result["image_url"] or result["image_base64"]:
                    result["success"] = True
                else:
                    result["error"] = "响应中未找到图片数据"
            else:
                result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
        except requests.exceptions.Timeout:
            result["error"] = f"请求超时（>{timeout}秒）"
        except Exception as e:
            result["error"] = f"请求异常: {str(e)}"
        
        return result
    
    def save_image(self, image_data: str, output_path: str, is_base64: bool = True):
        """
        保存图片到文件
        
        Args:
            image_data: 图片数据（base64 或 URL）
            output_path: 输出路径
            is_base64: 是否为 base64 格式
        """
        try:
            if is_base64:
                # 解码 base64
                if image_data.startswith("data:image"):
                    # 移除 data URL 前缀
                    image_data = image_data.split(",")[1]
                image_bytes = base64.b64decode(image_data)
            else:
                # 从 URL 下载
                response = requests.get(image_data, timeout=30)
                image_bytes = response.content
            
            # 保存文件
            with open(output_path, 'wb') as f:
                f.write(image_bytes)
            
            return True
        except Exception as e:
            print(f"  保存图片失败: {str(e)}")
            return False
    
    def run_batch_test(
        self,
        prompt: str,
        negative_prompt: str = "",
        num_images: int = 10,
        output_dir: str = "generated_images",
        model: str = "stable-diffusion-xl-base-1.0"
    ) -> Dict:
        """
        批量生成图片并测试
        
        Args:
            prompt: 正向提示词
            negative_prompt: 反向提示词
            num_images: 生成图片数量
            output_dir: 输出目录
            model: 模型名称
            
        Returns:
            测试结果统计
        """
        print(f"\n{'='*60}")
        print("AI 图片生成风格一致性测试")
        print(f"{'='*60}")
        print(f"模型: {model}")
        print(f"正向提示词: {prompt}")
        print(f"反向提示词: {negative_prompt}")
        print(f"生成数量: {num_images}")
        print(f"{'='*60}\n")
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        results = []
        successful_generations = []
        
        for i in range(1, num_images + 1):
            print(f"[{i}/{num_images}] 正在生成图片...", end=" ", flush=True)
            
            result = self.generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                model=model
            )
            
            if result["success"]:
                # 保存图片
                image_filename = f"image_{i:02d}_{int(time.time())}.png"
                image_path = output_path / image_filename
                
                saved = False
                if result["image_base64"]:
                    saved = self.save_image(
                        result["image_base64"],
                        str(image_path),
                        is_base64=True
                    )
                elif result["image_url"]:
                    saved = self.save_image(
                        result["image_url"],
                        str(image_path),
                        is_base64=False
                    )
                
                if saved:
                    generation_time = result["generation_time_ms"]
                    successful_generations.append(result)
                    results.append({
                        "index": i,
                        "success": True,
                        "generation_time_ms": generation_time,
                        "image_path": str(image_path),
                        "image_filename": image_filename
                    })
                    print(f"✓ {generation_time:.0f}ms - 已保存: {image_filename}")
                else:
                    results.append({
                        "index": i,
                        "success": False,
                        "error": "图片保存失败"
                    })
                    print(f"✗ 生成成功但保存失败")
            else:
                results.append({
                    "index": i,
                    "success": False,
                    "error": result["error"]
                })
                print(f"✗ 失败: {result['error']}")
            
            # 避免请求过快
            if i < num_images:
                time.sleep(1)
        
        # 统计结果
        if not successful_generations:
            return {
                "success": False,
                "error": "所有图片生成均失败",
                "total_images": num_images,
                "successful_images": 0,
                "results": results
            }
        
        generation_times = [r["generation_time_ms"] for r in successful_generations]
        
        stats = {
            "success": True,
            "total_images": num_images,
            "successful_images": len(successful_generations),
            "success_rate": len(successful_generations) / num_images * 100,
            "generation_time": {
                "avg_ms": sum(generation_times) / len(generation_times),
                "min_ms": min(generation_times),
                "max_ms": max(generation_times),
                "all_values": generation_times
            },
            "output_dir": str(output_path),
            "results": results
        }
        
        return stats
    
    def print_summary(self, stats: Dict):
        """打印测试总结"""
        print(f"\n{'='*60}")
        print("测试总结")
        print(f"{'='*60}")
        
        if not stats.get("success"):
            print(f"✗ 测试失败: {stats.get('error', 'Unknown error')}")
            return
        
        print(f"总生成数量: {stats['total_images']}")
        print(f"成功数量: {stats['successful_images']}")
        print(f"成功率: {stats['success_rate']:.1f}%")
        
        print(f"\n生成时间统计:")
        gen_time = stats['generation_time']
        print(f"  平均: {gen_time['avg_ms']:.0f} ms ({gen_time['avg_ms']/1000:.1f} 秒)")
        print(f"  最小: {gen_time['min_ms']:.0f} ms ({gen_time['min_ms']/1000:.1f} 秒)")
        print(f"  最大: {gen_time['max_ms']:.0f} ms ({gen_time['max_ms']/1000:.1f} 秒)")
        
        # 评估速度
        avg_seconds = gen_time['avg_ms'] / 1000
        if avg_seconds < 15:
            print(f"\n速度评估: ✓ 优秀 (< 15秒)")
        elif avg_seconds < 30:
            print(f"\n速度评估: ⚠ 可接受 (< 30秒)")
        else:
            print(f"\n速度评估: ✗ 需要优化 (> 30秒)")
        
        print(f"\n图片保存目录: {stats['output_dir']}")
        print(f"{'='*60}\n")
        
        print("⚠️  注意: 请手动检查生成的图片质量，评估风格一致性")
        print("   预期: 至少 8/10 张图片五官端正、风格契合")


def main():
    parser = argparse.ArgumentParser(
        description="AI 图片生成风格一致性测试工具"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        required=True,
        help="硅基流动 API Key (或设置环境变量 SILICONFLOW_API_KEY)"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="https://api.siliconflow.cn/v1",
        help="API 基础 URL (默认: https://api.siliconflow.cn/v1)"
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default="1girl, cute, pink hair, student uniform, anime style",
        help="正向提示词 (默认: 1girl, cute, pink hair, student uniform, anime style)"
    )
    parser.add_argument(
        "--negative-prompt",
        type=str,
        default="nsfw, ugly, deformed, blurry, bad anatomy, bad proportions",
        help="反向提示词"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="black-forest-labs/FLUX.1-schnell",
        help="模型名称 (默认: black-forest-labs/FLUX.1-schnell)"
    )
    parser.add_argument(
        "--num-images",
        type=int,
        default=10,
        help="生成图片数量 (默认: 10)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="generated_images",
        help="输出目录 (默认: generated_images)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="结果输出文件路径 (JSON格式)"
    )
    
    args = parser.parse_args()
    
    # 从环境变量获取配置（如果命令行未提供）
    api_key = args.api_key or os.getenv("SILICONFLOW_API_KEY")
    
    if not api_key:
        print("错误: 请提供 API Key (--api-key 或环境变量 SILICONFLOW_API_KEY)")
        sys.exit(1)
    
    # 创建测试器
    tester = ImageGenerationTester(
        api_key=api_key,
        base_url=args.base_url
    )
    
    # 运行批量测试
    stats = tester.run_batch_test(
        prompt=args.prompt,
        negative_prompt=args.negative_prompt,
        num_images=args.num_images,
        output_dir=args.output_dir,
        model=args.model
    )
    
    # 打印总结
    tester.print_summary(stats)
    
    # 保存结果到文件
    if args.output:
        output_data = {
            "test_time": datetime.now().isoformat(),
            "config": {
                "base_url": args.base_url,
                "model": args.model,
                "prompt": args.prompt,
                "negative_prompt": args.negative_prompt,
                "num_images": args.num_images,
                "output_dir": args.output_dir
            },
            "statistics": stats
        }
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"结果已保存到: {args.output}")
    
    # 返回退出码
    if not stats.get("success") or stats["success_rate"] < 80:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

