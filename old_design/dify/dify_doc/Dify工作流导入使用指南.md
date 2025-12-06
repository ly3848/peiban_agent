# Dify AI伴侣Agent工作流导入使用指南

## 概述

本指南包含5个核心Dify工作流DSL文件，用于构建AI伴侣Agent系统。这些工作流基于《AI伴侣Agent完整架构设计 V2.0》中的核心模块实现。

### 📦 包含的工作流

| # | 工作流名称 | 文件名 | 描述 | 延迟目标 |
|---|-----------|--------|------|---------|
| 1 | 智能路由器 | 01-conversation-router.yml | 根据用户输入判断路由(fast/smart/vip) | <200ms |
| 2 | 快速通道 | 02-fast-chat-flow.yml | 小模型处理简单问候、闲聊 | <300ms |
| 3 | 智能通道 | 03-smart-chat-flow.yml | 支持情绪分析、记忆检索、工具调用 | <1.5s |
| 4 | 情感对话Agent | 04-emotional-chat-agent.yml | 人格驱动+情绪自适应的纯对话生成 | - |
| 5 | 评审员 | 05-response-critic-flow.yml | 质量检查,防止答非所问、幻觉 | <100ms |

---

## 快速开始

### 前置要求

- Dify 0.6.0+ 版本
- 已配置的大模型API密钥：
  - OpenAI GPT-4o-mini / GPT-3.5-turbo
  - DeepSeek Chat (可选,用于智能路由)
  - Tongyi Qwen-turbo (快速通道)

### 导入步骤

#### 1️⃣ 打开Dify管理后台

访问你的Dify部署地址 (默认 `http://localhost/`)

#### 2️⃣ 创建应用 - 导入DSL

1. 点击 **"创建应用"**
2. 选择 **"导入DSL"**
3. 选择对应的 `.yml` 文件

#### 3️⃣ 依次导入5个工作流

建议按以下顺序导入：

```
1. 01-conversation-router.yml (必须首先导入)
   ↓
2. 02-fast-chat-flow.yml (依赖router的结果)
   ↓
3. 03-smart-chat-flow.yml (依赖router的结果,需要配置知识库)
   ↓
4. 04-emotional-chat-agent.yml (可独立运行)
   ↓
5. 05-response-critic-flow.yml (可独立运行)
```

#### 4️⃣ 配置模型和API

导入后需要配置的项目：

**Router工作流**:
```
- 模型: DeepSeek Chat 或 GPT-4o-mini
- Provider: deepseek 或 openai
```

**Fast_Path工作流**:
```
- E_Sensor1模型: qwen-turbo (阿里通义)
- Simple_Chat模型: qwen-turbo
- Critic模型: qwen-turbo (或 gpt-3.5-turbo)
```

**Smart_Path工作流**:
```
- E_Sensor2模型: gpt-4o-mini
- Orchestrator模型: gpt-4o-mini
- E_Chat模型: gpt-4o-mini
- Critic模型: gpt-3.5-turbo
- 知识库: 需要创建并配置 (用于记忆检索)
```

**Emotional_Chat_Agent**:
```
- 模型: gpt-4o-mini (可选择 gpt-4 获得更好效果)
```

**Critic_Flow**:
```
- 模型: gpt-3.5-turbo (轻量级质检)
```

---

## 工作流详细说明

### 1. 智能路由器 (01-conversation-router.yml)

**职责**: 分析用户意图并决定使用哪条处理通道

**输入变量**:
```json
{
  "user_input": "用户的文本输入",
  "user_id": "用户唯一标识",
  "is_vip": "true|false",
  "conversation_history": "历史对话JSON(可选)"
}
```

**输出结果**:
```json
{
  "route": "fast|smart|vip",
  "intent": "用户意图描述",
  "confidence": 0.0-1.0,
  "reasoning": "判断理由"
}
```

**路由规则**:
- `fast`: 简单问候、闲聊 (<20字，无复杂任务)
- `smart`: 复杂对话、记忆查询、情绪倾诉、工具调用
- `vip`: 心理咨询、亲密模式 (需要is_vip=true)

**调试建议**:
- 测试各类用户输入，验证路由准确率>85%
- 如置信度<0.6，自动降级到fast路由
- 使用Code节点做JSON解析和fallback处理

---

### 2. 快速通道 (02-fast-chat-flow.yml)

**职责**: 快速处理简单问候和闲聊

**流程**:
```
Start
  → E_Sensor1(快速情绪识别)
  → Simple_Chat(小模型对话)
  → Critic(轻量级质检)
  → [if pass] Answer
  → [if fail] Retry(最多1次)
```

**特点**:
- 使用qwen-turbo小模型 (成本低，速度快)
- 延迟目标<300ms
- 不涉及记忆检索，无需知识库
- 包含Critic重试机制

**测试用例**:
```
✅ "早安" → 温暖问候
✅ "在吗" → 确认在线
✅ "很开心" → 分享喜悦
❌ "我好累,应该怎么办" → 应该路由到smart (太复杂)
```

---

### 3. 智能通道 (03-smart-chat-flow.yml)

**职责**: 处理复杂对话、情绪倾诉、记忆查询、工具调用

**流程**:
```
Start
  → E_Sensor2(深度情绪分析) 【并行】
  → Memory_Retrieval(记忆库检索) 【并行】
  → Orchestrator(任务规划)
  → E_Chat(情感对话Agent)
  → Critic(质量检查)
  → [if pass] Answer
  → [if fail] Retry(最多1次)
```

**核心能力**:
1. **多维情绪分析**: primary + secondary emotions + intensity
2. **情绪自适应策略**: empathy_first / validation / solution_oriented / celebrate / casual
3. **记忆检索**: 通过知识库RAG检索用户相关记忆
4. **任务规划**: 根据情绪决定是否调用工具
5. **Critic质检**: 检查相关性、一致性、安全性、自然度

**关键配置 - 知识库设置**:

需要在Dify创建知识库并配置:

1. **创建知识库**:
   - 名称: `user_memories` (或自定义)
   - 向量模型: OpenAI text-embedding-3-small
   - 重排序模型: bge-reranker-large

2. **上传记忆示例** (Markdown格式):
   ```markdown
   # 用户姓名
   - 用户名: 小张
   - 昵称: Zoe

   # 家庭成员
   - 姐姐: 小明 (医生,心脏病史)
   - 爸爸: 小李 (退休工程师)

   # 工作信息
   - 职位: 产品经理
   - 公司: 某科技公司
   - 最近忙碌，压力大

   # 兴趣爱好
   - 喜欢看书,特别是心理学
   - 喜欢瑜伽
   - 喜欢巧克力蛋糕
   ```

3. **配置检索参数**:
   - Top K: 5
   - 启用重排序: 是
   - 相似度阈值: 0.3
   - 向量权重: 0.7, 关键词权重: 0.3

**测试用例**:
```
✅ "我好累,应该怎么办" → 情绪倾诉 + 建议
✅ "我姐姐叫什么" → 记忆查询 + 召回"小明"
✅ "下周五给姐姐买蛋糕" → 工具调用 + 设置提醒
✅ "我升职了!" → 庆祝 + 深入了解
```

**调试建议**:
- 先测试路由准确性 (Router流程)
- 再测试情绪识别 (E_Sensor2)
- 然后测试记忆检索 (确保知识库配置正确)
- 最后测试完整流程

---

### 4. 情感对话Agent (04-emotional-chat-agent.yml)

**职责**: 纯对话生成，不做质检、不需要路由

**输入变量**:
```json
{
  "user_input": "用户输入",
  "user_name": "用户名",
  "companion_name": "伴侣名(如:Luna)",
  "personality_description": "完整的人格描述",
  "days_together": 30,
  "emotion_primary_name": "焦虑",
  "emotion_intensity": 0.8,
  "secondary_emotions": "[{name: 疲惫, intensity: 0.6}]",
  "response_strategy": "empathy_first|validation|...",
  "memory_cards": "用户记忆(JSON)",
  "personality_tone": "温柔、亲切",
  "particles": "呢、哦、嗯",
  "forbidden_expressions": "不关我事、随便"
}
```

**输出结果**:
```
2-4句话的对话回复
```

**使用场景**:
- 作为Fast_Path/Smart_Path的后端调用
- 独立测试对话质量
- 评测情绪自适应能力

**关键提示**:
1. **人格配置很重要**: 详细的personality_description决定伴侣风格
2. **情绪适配是核心**: response_strategy必须被遵守
3. **记忆引用自然**: 如果有相关记忆，应自然地引用

---

### 5. 评审员 (05-response-critic-flow.yml)

**职责**: 独立质量检查工作流

**输入变量**:
```json
{
  "user_input": "用户输入",
  "context": "对话上下文",
  "draft_response": "待评估的AI回复",
  "memory_cards": "用户记忆"
}
```

**输出结果**:
```json
{
  "pass": true/false,
  "reason": "驳回原因(如果fail)",
  "suggestion": "改进建议",
  "scores": {
    "relevance": 9,
    "consistency": 9,
    "safety": 10,
    "naturalness": 8
  },
  "average_score": 9.0,
  "need_retry": false
}
```

**4项质检标准**:

| 标准 | 含义 | 常见问题 |
|------|------|---------|
| 相关性 | 是否回应用户核心concern | 答非所问 |
| 一致性 | 是否与记忆/人设一致 | 幻觉(凭空捏造) |
| 安全性 | 是否有违规内容 | 暴力、歧视 |
| 自然度 | 是否像人类而非机器 | 过度正式、模板感 |

**使用场景**:
- 作为Smart_Path流程中的质检节点
- 评测Agent输出质量
- 训练改进prompt

**评分逻辑**:
- ✅ Pass: 平均分≥7.5分
- ❌ Fail: 平均分<7.5分或单项<6分

---

## 集成方案

### 方案A: 三通道并联

```
FastAPI Gateway
  ├─ Router Flow
  ├─ [if fast] → Fast_Chat_Flow
  ├─ [if smart] → Smart_Chat_Flow
  └─ [if vip] → VIP_Agent_Flow (待实现)
```

### 方案B: 完整链路

```
FastAPI Gateway (输入安全检查)
  ↓
Router Flow (意图识别)
  ↓
[条件分支]
  ├─ Fast_Chat_Flow (小模型)
  │    ├─ E_Sensor1 → Simple_Chat → Critic
  │
  ├─ Smart_Chat_Flow (大模型+工具)
  │    ├─ E_Sensor2 → Orchestrator → E_Chat → Critic
  │
  └─ VIP_Agents (专用Agent)
  ↓
FastAPI Gateway (输出安全检查 + 异步入队)
  ↓
用户
```

### 方案C: 仅FastAPI + Critic独立

不使用Dify内的Critic，而是调用独立的Critic_Flow进行质检。

---

## 配置最佳实践

### 1. 模型成本优化

```yaml
FastPath:
  - 情绪识别: qwen-turbo (¥0.0008/1k tokens)
  - 对话生成: qwen-turbo
  - 质检: qwen-turbo
  → 成本: 最低

SmartPath:
  - 情绪分析: gpt-4o-mini (¥0.15/1m input)
  - 编排规划: gpt-4o-mini
  - 对话生成: gpt-4o-mini
  - 质检: gpt-3.5-turbo (¥0.05/1m input)
  → 成本: 中等

Router:
  - 路由决策: deepseek-chat (¥0.14/1m input) 或 gpt-4o-mini
  → 成本: 低
```

### 2. 温度参数设置

```
Router: temperature=0.3 (确定性强)
E_Sensor1: temperature=0.2 (快速识别)
E_Sensor2: temperature=0.5 (平衡)
E_Chat: temperature=0.8 (创意对话)
Critic: temperature=0.1 (严格评判)
```

### 3. 超时配置

```
Fast_Chat_Flow: 2s (p95<300ms)
Smart_Chat_Flow: 4s (p95<1.5s)
Critic: 1s (p95<100ms)
Router: 1s (p95<200ms)
```

### 4. Fallback策略

```
Router失败 → 默认fast路由
Critic失败 → 直接返回回复(不重试)
E_Chat失败 → 返回保底模板
记忆检索失败 → 继续流程,不中断
```

---

## 测试清单

### ✅ 导入测试

```
□ 所有5个工作流都导入成功
□ 没有缺失的模型或插件
□ 所有LLM节点都有模型配置
□ 知识库已创建(Smart_Chat_Flow需要)
```

### ✅ 单体测试

```
1. Router Flow
   □ 简单问候 → fast (置信度>0.9)
   □ 情绪倾诉 → smart (置信度>0.85)
   □ 记忆查询 → smart
   □ VIP心理咨询 → vip

2. Fast_Chat_Flow
   □ "早安" → 回复<300ms
   □ 无幻觉、无违规

3. Smart_Chat_Flow
   □ "我好累" → 共情回复
   □ 记忆检索准确
   □ "我升职了" → 庆祝语气

4. E_Chat Agent
   □ empathy_first策略 ✓
   □ validation策略 ✓
   □ solution_oriented策略 ✓
   □ celebrate策略 ✓

5. Critic Flow
   □ 答非所问识别 ✓
   □ 幻觉识别 ✓
   □ 自然度评分准确 ✓
```

### ✅ 集成测试

```
□ Router → Fast_Path 完整链路
□ Router → Smart_Path 完整链路
□ Smart_Path + Critic 重试机制
□ 记忆检索 + 情绪自适应组合
□ 性能指标达标:
  - Fast: p95<300ms
  - Smart: p95<1.5s
  - Router: p95<200ms
  - Critic: p95<100ms
```

---

## 常见问题

### Q: 导入后无法运行，提示"模型不存在"

**A**: 需要在Dify设置中配置模型API密钥
- 进入 Settings → Model Providers
- 配置 OpenAI、DeepSeek、Tongyi等厂商密钥
- 重启Dify服务

### Q: 知识库检索返回为空

**A**:
1. 检查知识库是否创建 (Settings → Knowledge Bases)
2. 检查是否上传了记忆文档
3. 检查向量化是否完成 (可能需要等待)
4. 调整相似度阈值(从0.5降低到0.3)

### Q: Critic总是驳回回复

**A**:
1. 检查draft_response是否为空
2. 检查memory_cards格式是否正确
3. 降低temperature=0.1 (太低可能导致回复固化)
4. 检查Critic Prompt是否被正确注入

### Q: 性能不达标

**A**:
1. Fast_Path用错了模型 (应该用qwen-turbo)
2. Smart_Path并行度不够 (E_Sensor2和Memory_Retrieval应并行)
3. 知识库检索慢 (调整top_k从10减到5)
4. 检查网络延迟和LLM响应时间

### Q: E_Chat生成的文字过长

**A**:
- System Prompt中加入: "回复长度: 2-4句话,不超过100字"
- 设置max_tokens=100左右
- Critic检查"自然度"会标记过长

---

## 升级和维护

### 定期评测

每周运行黄金测试集（50-100条）:
- 路由准确率
- 情绪识别准确率
- 记忆召回精度
- Critic通过率
- 平均响应时间

### Prompt优化

根据评测结果持续优化:
- Router路由规则
- E_Sensor2情绪识别
- E_Chat人设和语气
- Critic质检标准

### 模型替换

- 快速通道: qwen-turbo → qwen-long (成本+0.0002/1k)
- 智能通道: gpt-4o-mini → gpt-4 (成本×10,质量+20%)
- 路由器: deepseek → gpt-4o-mini (置信度+5%)

---

## 参考资源

- 📖 [架构设计文档](AI伴侣Agent架构设计-V2.md)
- 📖 [Dify实现指南](Dify实现指南-核心模块.md)
- 🔗 [Dify官方文档](https://docs.dify.ai)
- 🔗 [OpenAI API参考](https://platform.openai.com/docs)
- 🔗 [DeepSeek API参考](https://www.deepseek.com/api)

---

## 支持

如有问题，请参考:
1. Dify官方文档
2. 查看工作流执行日志 (Dify控制面板)
3. 检查模型API配额 (防止超额)
4. 搜索相关错误提示

---

**最后更新**: 2025-11-11
**维护者**: Claude Code
**版本**: 1.0
