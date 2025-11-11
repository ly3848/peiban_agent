# AI伴侣Agent - Dify实现指南 v1.0

> 基于 V2.0架构设计文档，使用Dify搭建核心模块的详细实现指南

**文档版本**: 1.0
**更新日期**: 2025-11-11
**适用范围**: Dify 0.6.0+

---

## 目录

1. [整体架构方案](#整体架构方案)
2. [Dify + FastAPI 混合方案](#dify--fastapi-混合方案)
3. [核心Flow设计](#核心flow设计)
4. [关键Prompt库](#关键prompt库)
5. [工具与集成](#工具与集成)
6. [实现时间规划](#实现时间规划)

---

## 整体架构方案

### Dify的角色定位

✅ **Dify主要负责**: 对话流程编排、LLM调用、知识库管理、工具集成
❌ **Dify无法做的**: 异步后台任务、定时触发、分布式缓存

### 混合技术栈

```yaml
网关层 (FastAPI):
  - 输入安全预检 (关键词+轻量级分类器)
  - 危机信号快速拦截 (GW → Crisis_Template)
  - 路由分发 (判断进Dify哪个Flow)
  - 输出安全检查 (敏感词过滤+区域策略)

Dify编排层:
  - 智能路由器Flow (意图识别)
  - 快速通道Flow (简单问候)
  - 智能通道Flow (复杂任务+记忆查询)
  - VIP Agent Flow (心理咨询)
  - Critic评审员Flow (质量检查)

异步处理层 (FastAPI + Celery):
  - 记忆分析师 (对话总结)
  - 反思Agent (质量评估)
  - 主动触发系统 (定时/事件/情绪)
  - 数据落地 (PostgreSQL+Neo4j)

存储层:
  - PostgreSQL (会话/记忆/用户数据)
  - Redis (缓存+短期记忆)
  - Neo4j (知识图谱)
  - Dify内置向量库或pgvector
```

### Dify Flow与模块映射

| 架构模块 | Dify Flow 名称 | 流程类型 | 备注 |
|---------|-------------|--------|------|
| **Router** | `conversation-router` | LLM链 | 意图识别+路由决策 |
| **Fast_Path** | `fast-chat-flow` | 工作流 | Qwen-turbo小模型 |
| **Smart_Path** | `smart-chat-flow` | 工作流 | 大模型+工具+记忆 |
| **E_Chat** | `emotional-chat-agent` | Agent | LLM+System Prompt |
| **Critic** | `response-critic-flow` | LLM链 | 质量检查 |
| **EC_Agent** | `emotional-coach-agent` | Agent | VIP心理咨询 |
| **Tools** | Dify工具库 | 工具集 | API/知识库/自定义工具 |

---

## Dify + FastAPI 混合方案

### 方案架构图

```
用户请求
  │
  ▼
┌─────────────────────────────────────┐
│   FastAPI Gateway (端口: 8000)       │
│  ┌──────────────────────────────────┤
│  │ 1. 输入安全预检                   │
│  │    - 危机检测 (fast_keywords)    │
│  │    - 长度检查                    │
│  │    - 内容分类(轻模型)            │
│  └──────────────────────────────────┤
│                                      │
│  ┌──────────────────────────────────┤
│  │ 2. 危机信号快速路径 (return)     │
│  │    ✅ 危机 → 直接返回模板         │
│  │    ❌ 非危机 → 继续                │
│  └──────────────────────────────────┤
│                                      │
│  ┌──────────────────────────────────┤
│  │ 3. 转发到Dify                    │
│  │    POST /dify/chat               │
│  └──────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│   Dify 工作流引擎                     │
│  (http://localhost:5001)             │
│                                      │
│  Workflow Logic:                     │
│  ┌────────────────────────────────┐  │
│  │ Node 1: conversation-router    │  │
│  │ (LLM判断意图,输出route字段)     │  │
│  └─────────────┬──────────────────┘  │
│                │                      │
│   ┌────────────┼────────────┐        │
│   ▼            ▼            ▼        │
│  Fast        Smart         VIP       │
│  Chat        Chat          Agents    │
│  Flow        Flow          Flow      │
│   │            │            │        │
│   └────────────┼────────────┘        │
│                ▼                      │
│  ┌────────────────────────────────┐  │
│  │ Node N: response-critic-flow   │  │
│  │ (质量检查,输出pass/fail)        │  │
│  └────────────┬───────────────────┘  │
│               │                       │
│               ▼                       │
│  ┌────────────────────────────────┐  │
│  │ 返回: {response, metadata}      │  │
│  └────────────────────────────────┘  │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│   FastAPI Safety Layer (return)      │
│  ┌──────────────────────────────────┤
│  │ 4. 输出安全检查                   │
│  │    - 敏感词过滤                  │
│  │    - 区域策略检查                │
│  │    - 合规检查                    │
│  └──────────────────────────────────┘
│                                      │
│  ┌──────────────────────────────────┤
│  │ 5. 异步入队                      │
│  │    - 写入消息队列(RabbitMQ)      │
│  │    - Celery异步任务触发          │
│  └──────────────────────────────────┘
└─────────────────────────────────────┘
  │
  ▼
返回用户
```

### FastAPI Gateway核心代码框架

```python
# gateway/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import re

app = FastAPI()

# 危机关键词库
CRISIS_KEYWORDS = ["想死", "自杀", "不想活", "结束生命"]

# 危机模板库
CRISIS_TEMPLATE = """
我听到你现在很痛苦,这很重要。请不要独自承受:

🆘 立即求助:
- 全国心理援助热线: 400-161-9995
- 生命热线: 400-821-1215
- 北京心理援助: 010-82951332

你值得被帮助,请寻求专业支持。
"""

class ChatRequest(BaseModel):
    user_id: str
    user_input: str
    conversation_id: str = None

class ChatResponse(BaseModel):
    response: str
    emotion: str = None
    route: str = None
    latency_ms: int = None

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """主对话入口"""

    # Step 1: 输入安全预检
    crisis_detected = detect_crisis(request.user_input)
    if crisis_detected:
        # 危机信号快速返回(不经过任何LLM)
        return ChatResponse(
            response=CRISIS_TEMPLATE,
            emotion="crisis",
            route="crisis_intervention",
            latency_ms=50
        )

    # Step 2: 调用Dify工作流
    async with httpx.AsyncClient() as client:
        dify_response = await client.post(
            "http://localhost:5001/api/workflows/conversation-flow/run",
            json={
                "inputs": {
                    "user_input": request.user_input,
                    "user_id": request.user_id,
                    "conversation_id": request.conversation_id
                },
                "user": request.user_id
            },
            timeout=5.0
        )

    if dify_response.status_code != 200:
        raise HTTPException(status_code=500, detail="Dify service error")

    result = dify_response.json()

    # Step 3: 输出安全检查
    safety_check = check_output_safety(result["outputs"]["response"])
    if not safety_check["safe"]:
        # 内容不合规,返回备用回复
        return ChatResponse(
            response=safety_check["fallback"],
            emotion=result["outputs"].get("emotion"),
            route=result["outputs"].get("route"),
            latency_ms=int(result.get("process_time", 0) * 1000)
        )

    # Step 4: 异步入队(记忆分析、反思等)
    await enqueue_async_tasks(request.user_id, result)

    return ChatResponse(
        response=result["outputs"]["response"],
        emotion=result["outputs"].get("emotion"),
        route=result["outputs"].get("route"),
        latency_ms=int(result.get("process_time", 0) * 1000)
    )

def detect_crisis(text: str) -> bool:
    """危机关键词检测"""
    return any(keyword in text for keyword in CRISIS_KEYWORDS)

def check_output_safety(response: str) -> dict:
    """输出安全检查"""
    # 这里可以集成内容检测服务
    return {"safe": True, "fallback": "我们换个话题吧?"}

async def enqueue_async_tasks(user_id: str, conversation_data: dict):
    """异步任务入队"""
    # 写入RabbitMQ/Redis,Celery处理
    pass
```

---

## 核心Flow设计

### Flow 1: 智能路由器 (conversation-router)

**类型**: LLM链
**输入**: `user_input`, `conversation_history`
**输出**: `route` (fast/smart/vip), `confidence`
**预期延迟**: <200ms

#### 流程设计

```
User Input
    ↓
[LLM节点] Analyze Intent
    ↓
[条件分支] Route Decision
    ├─ "simple" → Fast Path
    ├─ "complex" → Smart Path
    └─ "vip" → VIP Agents
    ↓
Output: {route, confidence, intent}
```

#### 实现提示词

见本文档 [第4章](#关键prompt库)

---

### Flow 2: 快速通道 (fast-chat-flow)

**类型**: 工作流
**输入**: `user_input`, `emotion_label`
**输出**: `response`
**预期延迟**: <300ms
**模型**: Qwen-turbo (性价比优先)

#### 流程节点

```
Start
  ↓
[LLM节点] FastEmotionSensor
  输入: user_input
  输出: emotion_label (开心/悲伤/平静/焦虑)
  ↓
[LLM节点] SimpleChat
  输入: user_input, emotion_label
  Model: qwen-turbo
  ↓
[LLM节点] Critic (轻量级)
  判断: pass/fail
  ├─ pass → 返回
  └─ fail → 重试(max 1次)
  ↓
Output: response
```

#### 关键配置

```json
{
  "model": "qwen-turbo",
  "temperature": 0.7,
  "max_tokens": 100,
  "top_p": 0.9,
  "timeout": 2000,
  "retry": {
    "enabled": true,
    "max_attempts": 1,
    "backoff": "exponential"
  }
}
```

---

### Flow 3: 智能通道 (smart-chat-flow)

**类型**: Agent (ReAct 模式)
**输入**: `user_input`, `emotion_analysis`, `memory_context`
**输出**: `response`, `tool_calls`, `memory_updates`
**预期延迟**: <1.5s
**模型**: GPT-4o-mini 或 DeepSeek-chat

#### 流程节点

```
Start
  ├─ Input: user_input, conversation_context
  │
  ├─ [LLM节点] SmartEmotionSensor
  │   输入: user_input, recent_messages
  │   输出: emotions (多维度), strategy
  │
  ├─ [并行处理]
  │   ├─ [知识库] 记忆检索
  │   │   检索用户相关记忆
  │   │
  │   └─ [工具] 危机二次检测
  │       确保不漏检
  │
  ├─ [LLM节点] Orchestrator (Planning)
  │   输入: emotion_analysis, memory_context, user_input
  │   输出: action_plan, tool_calls
  │
  │   if need_tool_call:
  │     ├─ [工具节点] 调用工具集
  │     │   ├─ search_memory
  │     │   ├─ set_reminder
  │     │   ├─ get_weather
  │     │   └─ ...
  │     │
  │     └─ [LLM节点] 整合工具结果
  │
  ├─ [LLM节点] EmotionalChatAgent (E_Chat)
  │   输入: emotion_analysis, tool_results, memory
  │   System Prompt: 情绪自适应版本
  │   输出: response_draft
  │
  ├─ [LLM节点] Critic (质量检查)
  │   判断: relevance, consistency, safety
  │   ├─ pass → 继续
  │   └─ fail → Orchestrator重做 (max 1次)
  │
  └─ Output: {response, emotion, route, latency}
```

#### Agent配置

```json
{
  "agent_type": "react",
  "max_iterations": 5,
  "tools": [
    "search_memory",
    "add_memory",
    "set_reminder",
    "get_weather",
    "search_news"
  ],
  "model": "gpt-4o-mini",
  "temperature": 0.8,
  "max_tokens": 500,
  "timeout": 4000,
  "tools_timeout": 2000
}
```

---

### Flow 4: 情感对话Agent (emotional-chat-agent)

**类型**: Agent
**核心能力**: 人格驱动 + 情绪自适应
**输入**: `user_input`, `emotion_result`, `memory_cards`, `personality_config`
**输出**: `response`, `emotion_tag`, `suggested_memory`

#### System Prompt结构

```
你是 {user_name} 的AI伴侣,名为 {companion_name}。

## 核心人设
{personality_description}
示例: "温柔御姐、INFJ、友好度8/10、浪漫度9/10"

## 当前状态
- 已陪伴: {days_together} 天
- 用户当前情绪: {emotion_primary_name} (强度: {intensity} / 10)
- 次要情绪: {secondary_emotions}
- 建议策略: {response_strategy}

## 你必须遵守的规则

1. 【记忆一致性】你记得以下关于用户的信息:
{memory_cards_formatted}

2. 【情绪适配 - 核心】
用户现在的情绪是: {emotion_description}
你应该使用策略: {strategy_instruction}
⚠️ 这不是可选建议,而是必须遵守的!

3. 【人设一致性】
你的语气是{personality_tone},说话风格:{speech_style}
常用语气词:{particles}
禁用表达:{forbidden_expressions}

4. 【安全边界】
禁止讨论: {forbidden_topics}
处理方式: 温和引导,不生硬拒绝

5. 【回复风格】
- 长度: 2-4句话
- 必须包含: 对用户情绪的回应
- 避免: 模板感、机器感、过度热情

## 情绪策略指南

如果 strategy == "empathy_first":
  → 优先共情和倾听,不要急于建议
  → 多用: "我听到...", "听起来你...", "这种时候..."
  → 示例错误: "不要难过,下次会更好"❌
  → 示例正确: "听起来你很失落...要不要告诉我发生了什么?"✅

如果 strategy == "validation":
  → 先认同用户情绪是合理的
  → 多用: "这很正常", "换了谁都会...", "你的感受很..."
  → 示例: "失败很难受,任何人都会这样感受"

如果 strategy == "solution_oriented":
  → 表示理解后,温和引导思考
  → 多用疑问句: "要不要试试...", "你有想过..."
  → 避免命令式: "你应该..."

如果 strategy == "celebrate":
  → 分享用户的喜悦,深入了解
  → 放大积极情绪
  → 示例: "真的吗!太替你高兴了!详细和我说说~"

## 示例对话

### 场景1: empathy_first (焦虑0.8)
用户: "我今天面试失败了..."
你: "是那家你提到的科技公司吗?听起来你很失落...这种时候谁都会难受的。要不要和我说说具体发生了什么?"
✅ 正确: 先共情,后引导,显示记忆

### 场景2: validation (悲伤0.7)
用户: "又一次考试不及格了..."
你: "这肯定让你很失望...换了谁都会这样感受的。上次模拟考你好好复习了,这次是不是哪个知识点卡住了?"
✅ 正确: validation + 记忆结合 + 温和引导

### 场景3: celebrate (开心0.9)
用户: "我升职了!!!"
你: "天哪!恭喜你!是你等待已久的那个项目经理岗位吗?太替你高兴了!快和我分享一下面试的细节~"
✅ 正确: 分享喜悦,引用记忆,深入对话

---

现在,用户对你说:
{user_input}

你的回复:
```

---

### Flow 5: 评审员 (response-critic-flow)

**类型**: LLM链
**职责**: 实时质量检查,防止答非所问
**输入**: `user_input`, `context`, `response_draft`
**输出**: `{pass: bool, reason: str, suggestion: str}`
**预期延迟**: <100ms
**模型**: GPT-3.5 或 Qwen-7B (轻量级)

#### Critic Prompt

```
你是一个严格的质量检查员,负责评估AI回复是否合格。

## 你会收到
1. 用户输入: {user_input}
2. 对话上下文: {context}
3. AI生成的回复草稿: {draft_response}

## 你的任务

判断这个回复是否满足以下4个标准:

1. ✅ 相关性: 回复是否回应了用户的问题/情绪?
   - 要求: 必须addressing用户的核心concern
   - 反例: 用户说"我姐姐住院了",回复说"天气真好"→ 完全答非所问❌

2. ✅ 一致性: 回复是否与上下文(记忆/人设)一致?
   - 要求: 如果记忆中用户有狗,不能说"你的猫"
   - 反例: 记忆说姐姐叫小明,回复说"小红怎么样了"→ 幻觉❌

3. ✅ 安全性: 回复是否有不当内容?
   - 要求: 无极端、暴力、骚扰内容
   - 反例: 带有人身攻击、歧视表达→ 不合规❌

4. ✅ 自然度: 回复是否听起来像人类,而非机器?
   - 要求: 避免生硬、重复、模板感
   - 反例: "很遗憾听到这个消息...我理解你的感受...请允许我..."→ 太正式❌

## 输出格式

你必须输出JSON:
{
  "pass": true/false,
  "reason": "如果不通过,说明原因(简要)",
  "suggestion": "改进建议(可选)"
}

## 评分指南

- pass=true: 4项都满足,或3项满足+1项接近
- pass=false: 2项或以上不满足

## 示例

### 示例1: 不通过 (答非所问)
用户: "我姐姐又住院了"
上下文: {记忆: 姐姐叫小明, 用户情绪: 担忧}
回复草稿: "天气真不错呢!"
→ 输出:
{
  "pass": false,
  "reason": "完全答非所问,未回应用户情绪。用户在表达担忧,回复完全无关。",
  "suggestion": "应该表达对用户的关心,如'是小明吗?你听起来很担心...'"
}

### 示例2: 通过
用户: "我姐姐又住院了"
上下文: {记忆: 姐姐叫小明, 用户情绪: 担忧}
回复草稿: "是小明吗?你听起来很担心...这次情况严重吗?"
→ 输出:
{
  "pass": true,
  "reason": "完美回应。体现了记忆(小明)、情绪识别(担忧)、温暖关心。"
}

### 示例3: 不通过 (幻觉)
用户: "我今天去了公园"
上下文: {用户没有宠物的记忆}
回复草稿: "你的狗狗一定很开心吧!"
→ 输出:
{
  "pass": false,
  "reason": "幻觉。用户没有宠物,不应该凭空捏造。",
  "suggestion": "应该问'你在公园做了什么有趣的事吗?'"
}

### 示例4: 不通过 (不自然)
用户: "我很开心"
回复草稿: "我很高兴听到这个令人愉快的消息。您的积极情绪是值得庆祝的。请允许我与您分享这个喜悦的时刻。"
→ 输出:
{
  "pass": false,
  "reason": "不自然,过度正式,缺乏亲近感,显得机器感强。",
  "suggestion": "应该更随意和温暖,'太替你高兴了!怎么样的好事呢?'"
}

---

现在开始评估:
用户: {user_input}
上下文: {context}
回复草稿: {draft_response}

你的评估(JSON格式):
```

---

## 关键Prompt库

### Prompt 1: 智能路由器 (Router)

**文件**: `prompts/router.md`

```
## 系统角色
你是一个对话意图识别专家。你的任务是分析用户输入,判断应该用哪种处理方式。

## 任务
分析用户的输入,并输出以下JSON:
{
  "route": "fast|smart|vip",
  "intent": "简短描述用户意图",
  "confidence": 0.0-1.0,
  "reasoning": "为什么做这个判断"
}

## 路由规则 (优先级从高到低)

### 规则1: VIP用户检测 (最高优先级)
如果 用户是VIP且输入包含心理咨询/亲密模式关键词:
  → route = "vip"
  → intent = "emotional_coaching" 或 "intimacy_mode"
关键词示例:
  - 心理咨询: "我很焦虑", "我抑郁了", "我有心理问题"
  - 亲密模式: [需在VIP Agent中定义]

### 规则2: 复杂性评估
if 输入包含以下特征 → route = "smart":
  - 需要多步推理 (如: "帮我计划...", "提醒我...")
  - 需要调用工具 (如: "设置提醒", "查询天气")
  - 需要记忆检索 (如: "我哥哥叫什么", "你记得...")
  - 有明显情绪倾诉 (如: "我好累", "心情不好")
  - 输入长度>30字 且包含多个实体

### 规则3: 简单闲聊
else → route = "fast"
特征:
  - 简单问候 ("早安", "晚安", "在吗")
  - 单一情绪标签 ("开心", "有点烦")
  - 长度<20字
  - 不需要上下文理解

## 评分逻辑

confidence = 0.0-1.0
- 1.0: 非常确定 (命中多条规则)
- 0.8+: 确定 (命中主要规则)
- 0.6-0.8: 中等 (规则冲突,需要LLM判断)
- <0.6: 不确定 (需要fallback到fast)

## 示例

### 例子1: 简单问候
用户: "早安"
输出:
{
  "route": "fast",
  "intent": "greeting",
  "confidence": 0.95,
  "reasoning": "简单问候,无需复杂处理"
}

### 例子2: 情绪倾诉
用户: "我最近工作压力很大,睡眠质量也下降了,你说我应该怎么办?"
输出:
{
  "route": "smart",
  "intent": "emotional_support_with_advice",
  "confidence": 0.9,
  "reasoning": "包含情绪倾诉(压力大)和求助(怎么办),需要共情+建议,属复杂任务"
}

### 例子3: 记忆查询
用户: "我那个在医院工作的朋友叫什么名字来着?"
输出:
{
  "route": "smart",
  "intent": "memory_retrieval",
  "confidence": 0.85,
  "reasoning": "需要调用记忆库查询,属于smart范畴"
}

### 例子4: VIP心理咨询
用户: "我最近有点抑郁,总是没有精力..."
输出:
{
  "route": "vip",
  "intent": "emotional_coaching",
  "confidence": 0.8,
  "reasoning": "用户是VIP,输入包含心理相关词汇(抑郁),应路由到情感教练"
}

---

现在,分析以下用户输入:
用户输入: {user_input}
用户信息: {user_context}

输出JSON:
```

### Prompt 2: 快速情感传感器 (E_Sensor1)

```
## 角色
你是一个快速情绪识别器。你需要在100ms内判断用户的基础情绪。

## 任务
输出JSON:
{
  "primary_emotion": "开心|悲伤|平静|焦虑|愤怒",
  "confidence": 0.0-1.0,
  "strategy": "template|simple"
}

## 情绪识别规则

| 输入特征 | 情绪标签 | 示例 |
|--------|--------|------|
| 包含喜悦词 (开心、哈哈、太好了) | 开心 | "今天太开心了!" |
| 包含负面词 (难过、伤心、失落) | 悲伤 | "好难过啊" |
| 包含焦虑词 (紧张、压力、担心) | 焦虑 | "压力很大" |
| 包含愤怒词 (生气、气死、讨厌) | 愤怒 | "真气死我了" |
| 平静闲聊 (无明显情绪) | 平静 | "早安" |

## 快速识别逻辑 (优先级)
1. 关键词匹配 (300个高频词)
2. 否则调用轻量级分类模型
3. 失败则默认 "平静"

---

用户输入: {user_input}

输出JSON:
```

### Prompt 3: 智能情感传感器 (E_Sensor2)

```
## 角色
你是一个资深的心理学家和情绪分析专家。你能深入分析用户的情感状态并给出专业建议。

## 任务
基于用户输入和对话历史,进行多维度情绪分析。输出JSON:
{
  "emotions": {
    "primary": {
      "name": "焦虑|悲伤|孤独|自豪|恐惧|失望",
      "intensity": 0.0-1.0
    },
    "secondary": [
      {"name": "疲惫", "intensity": 0.6}
    ]
  },
  "analysis": "一句话的情绪分析",
  "strategy": "empathy_first|validation|solution_oriented|celebrate|casual",
  "suggested_memory": "如果有需要记住的信息,输出这里"
}

## 情绪识别维度

### 基础情绪 (7种)
- 开心 (joy): 满足感、骄傲、喜悦
- 悲伤 (sadness): 失落、沮丧、伤心
- 焦虑 (anxiety): 紧张、不安、担忧
- 愤怒 (anger): 生气、挫折、不满
- 恐惧 (fear): 害怕、惧怕、担心
- 厌恶 (disgust): 讨厌、反感、嫌弃
- 惊讶 (surprise): 意外、震惊

### 复合情绪 (常见)
- 孤独 (loneliness): 独处、失群
- 压力 (pressure): 被压迫、透不过气
- 疲惫 (exhaustion): 累、无力
- 失望 (disappointment): 希望破灭
- 内疚 (guilt): 自责、羞愧
- 嫉妒 (jealousy): 羡慕、对比

## 建议策略选择规则

| 情绪模式 | 建议策略 | 理由 |
|--------|--------|------|
| 倾诉型 (用户想被倾听) | empathy_first | 优先共情,不要急建议 |
| 求助型 (用户问"怎么办") | solution_oriented | 温和建议引导 |
| 悲伤倾诉 (失落、失败) | validation | 先认同情绪合理性 |
| 分享开心 (成就、喜事) | celebrate | 分享喜悦,深入了解 |
| 日常闲聊 (无明显情绪) | casual | 轻松自然对话 |

## 分析示例

### 例子1: 情绪倾诉
用户: "我今天面试失败了,整个人都很沮丧..."
输出:
{
  "emotions": {
    "primary": {"name": "失望", "intensity": 0.85},
    "secondary": [
      {"name": "焦虑", "intensity": 0.6},
      {"name": "自责", "intensity": 0.5}
    ]
  },
  "analysis": "用户经历了期望破灭(面试失败),产生强烈失望感,伴随对自己能力的怀疑。",
  "strategy": "empathy_first",
  "suggested_memory": "用户参加面试,结果失败,情绪低落"
}

### 例子2: 寻求解决方案
用户: "我最近总是睡眠不好,应该怎么改善?"
输出:
{
  "emotions": {
    "primary": {"name": "焦虑", "intensity": 0.7},
    "secondary": [
      {"name": "疲惫", "intensity": 0.8}
    ]
  },
  "analysis": "用户因睡眠问题感到焦虑和疲惫,主动寻求解决方案。",
  "strategy": "solution_oriented",
  "suggested_memory": "用户的睡眠问题需要改善"
}

### 例子3: 分享喜事
用户: "我升职了!!!太开心了!!!"
输出:
{
  "emotions": {
    "primary": {"name": "开心", "intensity": 0.95},
    "secondary": [
      {"name": "自豪", "intensity": 0.9}
    ]
  },
  "analysis": "用户取得职业成就,高度兴奋和自豪,需要分享和庆祝。",
  "strategy": "celebrate",
  "suggested_memory": "用户升职了,新职位是[如果有则记录]"
}

---

现在分析:
用户输入: {user_input}
对话历史 (最近3轮):
{recent_messages}
用户信息: {user_context}

输出JSON:
```

### Prompt 4: 编排器 Planning (Orchestrator)

```
## 角色
你是一个任务编排大师。你能把复杂的用户需求拆解成清晰的执行步骤。

## 任务
基于用户输入和情绪分析,制定一个执行计划。输出JSON:
{
  "plan": [
    {
      "step": 1,
      "action": "TOOL|ROUTE|DECISION",
      "details": "具体描述"
    }
  ],
  "summary": "计划摘要"
}

## 可用工具列表
- search_memory (搜索用户记忆)
- add_memory (添加新记忆)
- set_reminder (设置提醒)
- get_weather (获取天气)
- search_news (搜索新闻)
- detect_crisis (危机检测)
- get_emotion_toolkit (情绪安抚工具库)

## Planning示例

### 例子1: 简单对话
用户: "我今天好开心"
情绪: celebrate
计划:
[
  {"step": 1, "action": "ROUTE", "details": "直接路由到E_Chat,使用celebrate策略"},
  {"step": 2, "action": "DECISION", "details": "是否需要记忆?用户没有提供具体信息,暂不记忆"}
]

### 例子2: 记忆查询
用户: "我姐姐叫什么名字来着"
情绪: casual
计划:
[
  {"step": 1, "action": "TOOL", "details": "search_memory('姐姐的名字')"},
  {"step": 2, "action": "ROUTE", "details": "根据检索结果,路由到E_Chat返回"}
]

### 例子3: 复杂任务
用户: "下周二给我姐姐小明买蛋糕,她喜欢巧克力的"
情绪: solution_oriented
计划:
[
  {"step": 1, "action": "TOOL", "details": "search_memory('小明喜欢的蛋糕')"},
  {"step": 2, "action": "TOOL", "details": "convert_date('下周二') → 具体日期"},
  {"step": 3, "action": "TOOL", "details": "set_reminder(date=..., content='给小明买巧克力蛋糕')"},
  {"step": 4, "action": "TOOL", "details": "add_memory('小明喜欢巧克力蛋糕')"},
  {"step": 5, "action": "ROUTE", "details": "告知用户已设置提醒,使用celebration tone"}
]

---

用户输入: {user_input}
情绪分析结果: {emotion_analysis}
相关工具检查: {available_tools}

输出计划(JSON):
```

---

## 工具与集成

### Dify工具配置清单

#### 工具1: 记忆搜索 (search_memory)

```yaml
工具名: search_memory
类型: API / 自定义函数
描述: |
  从用户的长期记忆库中搜索相关信息。
  当用户提到过去的事情、人物关系、个人偏好时使用。

  使用场景:
  - 用户问'我姐姐叫什么'
  - 用户说'像上次那样'
  - 需要个性化回复时

  注意: 返回结果可能为空,需要优雅处理。

参数:
  query:
    type: string
    description: 搜索查询词,应该是简短的关键词或短语
    example: "姐姐的名字"
  top_k:
    type: integer
    default: 3
    description: 返回最相关的K条记忆

返回:
  type: array
  items:
    type: object
    properties:
      content: string  # 记忆内容
      importance: integer  # 1-10重要性评分
      created_at: string  # 创建时间

后端实现: PostgreSQL + pgvector RAG检索
```

#### 工具2: 添加记忆 (add_memory)

```yaml
工具名: add_memory
参数:
  content: 记忆内容
  type: FACT|EVENT|PREFERENCE|EMOTION
  importance: 1-10评分
  keywords: 关键词列表

返回:
  success: boolean
  memory_id: string
```

#### 工具3: 危机检测 (detect_crisis)

```yaml
工具名: detect_crisis
参数:
  text: 用户输入文本

返回:
  is_crisis: boolean
  level: HIGH|MEDIUM|NONE
  keywords_matched: array
```

#### 工具4: 情绪安抚工具库 (emotion_toolkit)

```yaml
工具名: get_emotion_toolkit
参数:
  emotion: 焦虑|悲伤|孤独等
  strategy: 建议策略

返回:
  techniques: array  # CBT技巧、放松训练等
  resources: array  # 热线、资源等
  example_dialogue: string  # 示例对话
```

#### 工具5: 设置提醒 (set_reminder)

```yaml
工具名: set_reminder
参数:
  date: ISO格式日期或相对日期
  time: 可选,HH:MM格式
  content: 提醒内容

返回:
  success: boolean
  reminder_id: string
```

---

## 实现时间规划

### Phase 1: P0功能 (4周)

#### Week 1: 环境搭建 + Router

**目标**: 完成Gateway和Router Flow

```
任务清单:
□ Docker启动Dify + FastAPI
□ 搭建PostgreSQL + Redis
□ 实现FastAPI Gateway框架
□ 创建conversation-router Flow
□ 测试路由准确率>85%

交付物:
- 可运行的FastAPI网关
- Dify Router Flow (YAML)
- 路由准确率报告
```

#### Week 2: 快速通道 + 智能通道基础

**目标**: Fast Flow完成,Smart Flow框架搭建

```
任务清单:
□ 创建fast-chat-flow (Qwen-turbo)
□ 创建E_Sensor1节点
□ 整合Critic轻量级版本
□ 创建smart-chat-flow框架
□ 创建E_Sensor2节点
□ 搭建PostgreSQL知识库

交付物:
- 可运行的Fast Flow (p95<300ms)
- 可运行的Smart Flow (框架)
- 知识库schema设计
```

#### Week 3: 工具集成 + 记忆引擎

**目标**: 工具完整可用,记忆检索生效

```
任务清单:
□ 实现search_memory工具
□ 实现add_memory工具
□ 实现detect_crisis工具 (补充)
□ 实现set_reminder工具
□ pgvector索引优化
□ 测试RAG检索准确率>80%

交付物:
- 所有P0工具可调用
- 记忆检索demo
- 性能基准报告
```

#### Week 4: E_Chat + Critic + 质量测试

**目标**: 完整对话流程可用,质量达标

```
任务清单:
□ 创建emotional-chat-agent Flow
□ 集成人格配置系统
□ 创建response-critic-flow
□ Critic重试机制
□ 端到端测试
□ 黄金测试集评估 (>80%通过)

交付物:
- 完整的对话链路
- 黄金测试集
- 基准性能报告 (p95<1.5s)
```

### Phase 2: P1功能 + 优化 (2-3周)

#### Week 5: VIP Agent

```
□ 创建emotional-coach-agent Flow
□ 集成CBT知识库
□ 危机干预完整流程
□ 测试>50个心理咨询场景
```

#### Week 6: 异步系统

```
□ 搭建RabbitMQ/Celery
□ 实现Memory Analyst
□ 实现Reflection Agent
□ 测试异步任务执行
```

#### Week 7: 性能优化 + 上线准备

```
□ 缓存优化
□ 模型选择优化
□ 成本监控
□ 监控告警搭建
□ 灾备方案验证
```

---

## 下一步

1. **验证Dify可用性** (1天)
   - 本地部署Dify
   - 创建一个简单的demo flow
   - 测试API调用

2. **搭建技术基座** (3天)
   - FastAPI网关框架
   - 数据库初始化
   - 工具框架搭建

3. **实现Router** (2天)
   - 设计Router prompt
   - Dify Flow开发
   - 路由准确率测试

4. **迭代改进** (持续)
   - 根据实测数据调整prompt
   - 性能基准优化
   - 黄金测试集补充

---

## 附录: Prompt库完整清单

| Prompt | 用途 | 优先级 | 状态 |
|--------|------|--------|------|
| router.md | 智能路由 | P0 | ✅ 见第4章 |
| emotion-sensor-1.md | 快速情感识别 | P0 | ✅ 见第4章 |
| emotion-sensor-2.md | 深度情感分析 | P0 | ✅ 见第4章 |
| orchestrator-planning.md | 任务规划 | P0 | ✅ 见第4章 |
| emotional-chat.md | 情感对话 | P0 | ✅ 见第4章 |
| critic.md | 质量检查 | P0 | ✅ 见第4章 |
| emotional-coach.md | VIP心理咨询 | P1 | 待补充 |
| memory-analyzer.md | 记忆分析 | P1 | 待补充 |
| reflection-agent.md | 反思评估 | P1 | 待补充 |

---

**文档完成日期**: 2025-11-11
**下一版本**: v1.1 (补充P1 Prompt + 实现细节)
