# Dify API + LLM 延迟与流式响应测试

本目录包含实验二的测试脚本和相关文档，用于验证 Dify API 在国内网络环境下的延迟和流式响应性能。

## 文件说明

- `test_latency.py`: 测试脚本，用于测量 Dify API 的首字延迟 (TTFB) 和完整生成时间
- `requirements.txt`: Python 依赖包列表
- `实验结果记录.md`: 测试结果记录模板
- `README.md`: 本说明文档

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 准备 Dify 应用

1. 登录 [Dify 平台](https://dify.ai)
2. 创建一个新的"聊天助手"应用
3. 选择模型（建议：DeepSeek-V2 或 GPT-4o-mini）
4. 获取应用的 **API Key** 和 **Application ID**

### 3. 运行测试

#### 基本用法

```bash
python test_latency.py \
  --api-key YOUR_API_KEY \
  --app-id YOUR_APP_ID \
  --network wifi \
  --num-tests 10
```

#### 使用环境变量（推荐）

```bash
export DIFY_API_KEY="your_api_key"
export DIFY_APP_ID="your_app_id"

python test_latency.py --network wifi --num-tests 10
```

#### 保存结果到文件

```bash
python test_latency.py \
  --api-key YOUR_API_KEY \
  --app-id YOUR_APP_ID \
  --network wifi \
  --num-tests 10 \
  --output wifi_results.json
```

### 4. 测试不同网络环境

#### WiFi 环境测试

```bash
python test_latency.py \
  --api-key YOUR_API_KEY \
  --app-id YOUR_APP_ID \
  --network wifi \
  --num-tests 10 \
  --output wifi_results.json
```

#### 4G/5G 热点测试

1. 连接手机热点
2. 运行测试：

```bash
python test_latency.py \
  --api-key YOUR_API_KEY \
  --app-id YOUR_APP_ID \
  --network 4g \
  --num-tests 10 \
  --output 4g_results.json
```

## 参数说明

| 参数 | 说明 | 必需 | 默认值 |
|------|------|------|--------|
| `--api-key` | Dify API Key | 是 | - |
| `--app-id` | Dify Application ID | 是 | - |
| `--base-url` | Dify API 基础URL | 否 | `https://api.dify.ai/v1` |
| `--query` | 测试查询文本 | 否 | 默认50字测试文本 |
| `--network` | 网络类型 | 否 | `unknown` |
| `--num-tests` | 测试次数 | 否 | `10` |
| `--output` | 结果输出文件 | 否 | 不保存 |

## 输出说明

### 控制台输出

测试过程中会实时显示：
- 每次测试的 TTFB（首字延迟）
- 总耗时
- 响应字符数
- 测试统计结果

### JSON 结果文件

如果使用 `--output` 参数，会生成包含详细数据的 JSON 文件：

```json
{
  "test_time": "2024-01-01T12:00:00",
  "config": {
    "base_url": "https://api.dify.ai/v1",
    "app_id": "app-xxx",
    "network_type": "wifi",
    "query": "测试文本...",
    "num_tests": 10
  },
  "statistics": {
    "network_type": "wifi",
    "total_tests": 10,
    "successful_tests": 10,
    "success_rate": 100.0,
    "ttfb": {
      "avg_ms": 1200,
      "min_ms": 800,
      "max_ms": 2000,
      "all_values": [1200, 800, ...]
    },
    "total_time": {
      "avg_ms": 5000,
      "min_ms": 3000,
      "max_ms": 8000,
      "all_values": [5000, 3000, ...]
    },
    "char_count": {
      "avg": 150,
      "min": 100,
      "max": 200
    },
    "streaming_stable": true
  }
}
```

## 评估标准

根据测试计划的要求：

- **✓ 优秀**: 平均 TTFB < 1.5 秒
- **⚠ 可接受**: 平均 TTFB < 3 秒
- **✗ 需要优化**: 平均 TTFB > 3 秒

## 记录测试结果

测试完成后，请将结果填写到 `实验结果记录.md` 文件中，包括：

1. Dify 应用配置信息
2. WiFi 环境测试结果
3. 4G/5G 环境测试结果
4. 对比分析和结论

## 常见问题

### Q: 如何获取 Dify API Key 和 Application ID？

A: 
1. 登录 Dify 平台
2. 进入你的应用
3. 在"API 访问"或"设置"页面可以找到 API Key
4. Application ID 在应用的 URL 或设置页面中

### Q: 测试失败怎么办？

A: 检查以下几点：
- API Key 和 Application ID 是否正确
- 网络连接是否正常
- Dify 应用是否已正确配置并发布
- 查看错误信息，可能是 API 限制或模型问题

### Q: 如何测试自定义查询文本？

A: 使用 `--query` 参数：

```bash
python test_latency.py \
  --api-key YOUR_API_KEY \
  --app-id YOUR_APP_ID \
  --query "你的自定义查询文本" \
  --network wifi
```

### Q: 如何测试自建的 Dify 实例？

A: 使用 `--base-url` 参数指定你的 Dify 实例地址：

```bash
python test_latency.py \
  --api-key YOUR_API_KEY \
  --app-id YOUR_APP_ID \
  --base-url https://your-dify-instance.com/v1 \
  --network wifi
```

## 注意事项

1. **测试间隔**: 脚本在每次测试之间会等待 1 秒，避免请求过快
2. **超时设置**: 默认超时时间为 60 秒，如果响应较慢可以修改代码中的 `timeout` 参数
3. **网络切换**: 测试不同网络环境时，确保已切换到对应网络（WiFi 或手机热点）
4. **API 限制**: 注意 Dify API 的调用频率限制，避免超出配额

## 技术支持

如有问题，请参考：
- [Dify API 文档](https://docs.dify.ai/guides/application-development/api-reference)
- 项目架构设计文档

