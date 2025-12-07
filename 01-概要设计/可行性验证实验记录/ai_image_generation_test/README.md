# AI 绘图 (Stable Diffusion) 风格一致性测试

本目录包含实验五的测试脚本和相关文档，用于验证 AI 图片生成 API 的风格一致性和生成速度。

## 文件说明

- `test_image_generation.py`: 测试脚本，用于生成图片并测试风格一致性
- `requirements.txt`: Python 依赖包列表
- `实验结果记录.md`: 测试结果记录模板
- `README.md`: 本说明文档

## 快速开始

### 1. 安装依赖

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 运行测试

#### 基本用法

```bash
python test_image_generation.py \
  --api-key sk-kxdeuhjyqhfohjzkbrelqhvsogxhvrrvzlrjxlliveclbqtu \
  --num-images 10 \
  --output test_results.json
```

#### 自定义提示词

```bash
python test_image_generation.py \
  --api-key YOUR_API_KEY \
  --prompt "1girl, cute, pink hair, student uniform, anime style" \
  --negative-prompt "nsfw, ugly, deformed, blurry" \
  --num-images 10
```

#### 使用环境变量

```bash
export SILICONFLOW_API_KEY="your-api-key"
python test_image_generation.py --num-images 10
```

## 参数说明

| 参数 | 说明 | 必需 | 默认值 |
|------|------|------|--------|
| `--api-key` | 硅基流动 API Key | 是 | - |
| `--base-url` | API 基础 URL | 否 | `https://api.siliconflow.cn/v1` |
| `--prompt` | 正向提示词 | 否 | `1girl, cute, pink hair, student uniform, anime style` |
| `--negative-prompt` | 反向提示词 | 否 | `nsfw, ugly, deformed, blurry, bad anatomy, bad proportions` |
| `--model` | 模型名称 | 否 | `stable-diffusion-xl-base-1.0` |
| `--num-images` | 生成图片数量 | 否 | `10` |
| `--output-dir` | 输出目录 | 否 | `generated_images` |
| `--output` | 结果输出文件 | 否 | 不保存 |

## 测试内容

### 1. 图片生成测试

使用固定的提示词生成多张图片，测试：
- 生成速度（预期 < 15秒）
- 生成成功率
- 风格一致性（需要人工检查）

### 2. 预期结果

根据测试计划的要求：

- **可用率**: 生成 10 张图，至少 8 张五官端正、风格契合
- **速度**: < 15秒

## 输出说明

### 控制台输出

测试过程中会实时显示：
- 每次生成的进度
- 生成时间
- 图片保存状态

### 生成的图片

所有生成的图片保存在 `generated_images/` 目录下，文件名格式：
- `image_01_timestamp.png`
- `image_02_timestamp.png`
- ...

### JSON 结果文件

如果使用 `--output` 参数，会生成包含详细数据的 JSON 文件：

```json
{
  "test_time": "2024-01-01T12:00:00",
  "config": {
    "model": "stable-diffusion-xl-base-1.0",
    "prompt": "...",
    "num_images": 10
  },
  "statistics": {
    "successful_images": 10,
    "success_rate": 100.0,
    "generation_time": {
      "avg_ms": 12000,
      "min_ms": 8000,
      "max_ms": 15000
    }
  }
}
```

## 评估标准

### 速度评估

- **✓ 优秀**: 平均生成时间 < 15秒
- **⚠ 可接受**: 平均生成时间 < 30秒
- **✗ 需要优化**: 平均生成时间 > 30秒

### 质量评估（需要人工检查）

- **✓ 优秀**: 至少 8/10 张图片五官端正、风格契合
- **⚠ 可接受**: 6-7/10 张图片符合要求
- **✗ 需要优化**: < 6/10 张图片符合要求

## 记录测试结果

测试完成后，请：

1. 检查生成的图片质量
2. 统计符合要求的图片数量
3. 将结果填写到 `实验结果记录.md` 文件中

## 常见问题

### Q: 如何获取硅基流动 API Key？

A: 
1. 访问 [硅基流动](https://siliconflow.cn)
2. 注册/登录账号
3. 在控制台获取 API Key

### Q: 生成的图片在哪里？

A: 图片保存在 `generated_images/` 目录下（或通过 `--output-dir` 指定的目录）

### Q: 如何评估图片质量？

A: 需要人工检查每张图片：
- 五官是否端正
- 风格是否统一（二次元风格）
- 是否有明显缺陷（崩坏、变形等）

### Q: API 调用失败怎么办？

A: 检查以下几点：
- API Key 是否正确
- 网络连接是否正常
- API 端点是否正确
- 查看错误信息，可能是模型名称不正确或 API 格式变化

## 注意事项

1. **API 费用**: 注意图片生成可能产生费用
2. **生成时间**: 图片生成可能需要较长时间，请耐心等待
3. **质量检查**: 风格一致性需要人工检查，脚本只统计生成速度和成功率
4. **模型选择**: 不同模型的效果可能不同，可以尝试不同的模型

## 技术支持

如有问题，请参考：
- [硅基流动文档](https://siliconflow.cn/docs)
- 项目架构设计文档

