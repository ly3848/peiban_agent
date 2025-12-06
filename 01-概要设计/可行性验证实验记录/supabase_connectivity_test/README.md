# Supabase 国内连通性验证测试

本目录包含实验四的测试脚本和相关文档，用于验证 Supabase 在国内网络环境下的连通性和性能。

## 文件说明

- `test_connectivity.py`: 测试脚本，用于测试 Supabase API 读写速度和 Storage 下载速度
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

### 2. 准备 Supabase 项目

在运行测试之前，需要：

1. **创建 Supabase 项目**
   - 访问 [Supabase](https://supabase.com) 创建项目
   - Region 选择 Singapore 或 Tokyo（推荐）

2. **创建测试表**
   - 在 Supabase SQL Editor 中执行：
   ```sql
   CREATE TABLE test_ping (
     id BIGSERIAL PRIMARY KEY,
     test_data TEXT,
     created_at TIMESTAMP DEFAULT NOW()
   );
   ```

3. **配置 Storage（可选）**
   - 创建一个 Storage Bucket（设置为 public）
   - 上传一张测试图片（建议 500KB 左右）

### 3. 获取配置信息

需要以下信息：

- **Supabase URL**: 项目设置 → API → Project URL
  - 格式: `https://xxx.supabase.co`
- **API Key**: 项目设置 → API → anon public key
  - 或使用 service_role key（需要更高权限）

### 4. 运行测试

#### 基本测试（仅数据库）

```bash
python test_connectivity.py \
  --url https://your-project.supabase.co \
  --key your-api-key \
  --table test_ping \
  --num-tests 10 \
  --output results.json
```

#### 完整测试（包含 Storage）

```bash
python test_connectivity.py \
  --url https://your-project.supabase.co \
  --key your-api-key \
  --table test_ping \
  --bucket your-bucket-name \
  --file path/to/test-image.jpg \
  --num-tests 10 \
  --output results.json
```

#### 使用环境变量

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-api-key"

python test_connectivity.py --table test_ping --num-tests 10
```

## 参数说明

| 参数 | 说明 | 必需 | 默认值 |
|------|------|------|--------|
| `--url` | Supabase 项目 URL | 是 | - |
| `--key` | Supabase API Key | 是 | - |
| `--table` | 测试表名 | 否 | `test_ping` |
| `--bucket` | Storage bucket 名称 | 否 | - |
| `--file` | Storage 文件路径 | 否 | - |
| `--num-tests` | 每个测试的次数 | 否 | `10` |
| `--output` | 结果输出文件 | 否 | 不保存 |

## 测试内容

### 1. 域名解析测试

测试 Supabase 域名的 DNS 解析是否正常。

### 2. 数据库读取测试

通过 PostgREST API 执行 `SELECT * FROM test_ping` 查询，测试读取速度。

**预期结果**: 平均延迟 < 800ms

### 3. 数据库写入测试

通过 PostgREST API 执行 `INSERT` 操作，测试写入速度。

**预期结果**: 平均延迟 < 800ms

### 4. Storage 下载测试

下载 Storage 中的测试图片，测试下载速度。

**预期结果**: 100KB 图片 < 1秒

## 输出说明

### 控制台输出

测试过程中会实时显示：
- 每次测试的延迟时间
- 测试统计结果
- 评估结论

### JSON 结果文件

如果使用 `--output` 参数，会生成包含详细数据的 JSON 文件：

```json
{
  "test_time": "2024-01-01T12:00:00",
  "supabase_url": "https://xxx.supabase.co",
  "dns": {
    "success": true,
    "resolved_ips": ["xxx.xxx.xxx.xxx"]
  },
  "database_read": {
    "success": true,
    "success_rate": 100.0,
    "latency": {
      "avg_ms": 500,
      "min_ms": 300,
      "max_ms": 800,
      "all_values": [500, 300, ...]
    }
  },
  "database_write": { ... },
  "storage_download": { ... }
}
```

## 评估标准

根据测试计划的要求：

### 数据库 API

- **✓ 优秀**: 平均延迟 < 800ms
- **⚠ 可接受**: 平均延迟 < 1500ms
- **✗ 需要优化**: 平均延迟 > 1500ms

### Storage 下载

- **✓ 优秀**: 100KB 图片 < 1秒
- **⚠ 可接受**: 100KB 图片 < 2秒
- **✗ 需要优化**: 100KB 图片 > 2秒

### 成功率

- **预期**: 请求成功率 > 99%

## 记录测试结果

测试完成后，请将结果填写到 `实验结果记录.md` 文件中。

## 常见问题

### Q: 如何获取 Supabase URL 和 API Key？

A: 
1. 登录 Supabase 控制台
2. 进入项目设置 → API
3. Project URL 就是 `--url` 参数的值
4. anon public key 就是 `--key` 参数的值

### Q: 测试表不存在怎么办？

A: 在 Supabase SQL Editor 中执行：
```sql
CREATE TABLE test_ping (
  id BIGSERIAL PRIMARY KEY,
  test_data TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Q: Storage 测试失败怎么办？

A: 检查以下几点：
- Bucket 是否设置为 public
- 文件路径是否正确
- API Key 是否有 Storage 访问权限

### Q: 如何创建测试图片？

A: 可以使用任意图片，建议大小在 500KB 左右。可以通过以下方式创建：
- 使用图片编辑软件调整图片大小
- 或使用在线工具压缩图片

## 注意事项

1. **API Key 权限**: 使用 anon key 时，确保表有适当的 RLS (Row Level Security) 策略
2. **测试间隔**: 脚本在每次测试之间会等待 0.5 秒，避免请求过快
3. **网络环境**: 确保在国内网络环境下进行测试
4. **Storage 权限**: 如果 Storage bucket 不是 public，需要配置适当的访问策略

## 技术支持

如有问题，请参考：
- [Supabase 文档](https://supabase.com/docs)
- 项目架构设计文档

