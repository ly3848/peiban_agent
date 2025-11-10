# AI伴侣 MVP 架构设计文档

**项目**: AI伴侣Agent
**阶段**: MVP (Minimum Viable Product)
**版本**: 1.0
**日期**: 2025-11-10
**开发者**: 1人
**目标周期**: 4周(28天)

---

## 目录

1. [架构概览](#架构概览)
2. [系统拓扑图](#系统拓扑图)
3. [核心模块设计](#核心模块设计)
4. [数据模型](#数据模型)
5. [API接口定义](#api接口定义)
6. [部署架构](#部署架构)
7. [成本分析](#成本分析)
8. [性能指标](#性能指标)
9. [风险与降级方案](#风险与降级方案)

---

## 架构概览

### 核心设计理念

**极简但完整**: 只做PRD P0功能,去掉所有P1/P2的复杂设计

| 维度 | 方案 | 说明 |
|-----|------|------|
| **LLM核心** | Dify + DeepSeek-V3 | 内置人格/记忆/安全,无需自研 |
| **通信方式** | 文本+语音+视频 | PRD要求的3种交互方式 |
| **记忆存储** | Dify知识库+PostgreSQL | 向量RAG+历史记录,无需Neo4j |
| **语音处理** | Azure Speech SDK | ASR+TTS,无需本地部署 |
| **视频生成** | SadTalker自部署 | 成本$120/月,可控可扩展 |
| **路由复杂度** | 直接转Dify | 无需智能路由器,单一流程 |
| **质检机制** | Dify内置 | 无需独立Critic服务 |

### 架构分层

```
┌─────────────────────────────────────────────────┐
│           客户端层 (Web UI / Mobile)             │
├─────────────────────────────────────────────────┤
│          API网关层 (Flask/FastAPI)               │
│     ├─ 鉴权 (JWT)                               │
│     ├─ 限流 (60条/分钟)                        │
│     └─ 危机检测 (10个关键词)                    │
├─────────────────────────────────────────────────┤
│         核心处理层 (Dify为主)                    │
│     ├─ Dify Chatflow (LLM+人格+记忆)           │
│     ├─ 语音模块 (Azure Speech SDK)              │
│     ├─ 视频模块 (SadTalker)                     │
│     └─ 安全过滤 (Moderation)                    │
├─────────────────────────────────────────────────┤
│        数据存储层 (PostgreSQL/Redis)             │
│     ├─ PostgreSQL: 用户/对话/记忆               │
│     └─ Redis: 会话缓存                          │
└─────────────────────────────────────────────────┘
```

---

## 系统拓扑图

```
                        [用户]
                          │
                          ▼
        ┌──────────────────────────────────┐
        │      API 网关 (Flask/FastAPI)     │
        │  ├─ JWT认证                       │
        │  ├─ 限流器                        │
        │  └─ 危机关键词检测 ◄──┐           │
        └──────────────────────┬───────────┘
                               │
        ┌──────────────────────▼───────────┐
        │       核心处理层                   │
        │ ┌──────────────────────────────┐ │
        │ │   Dify Chatflow              │ │
        │ │ ├─ System Prompt (人格)      │ │
        │ │ ├─ LLM: DeepSeek-V3          │ │
        │ │ ├─ 知识库: RAG检索           │ │
        │ │ └─ Moderation: 内容审核      │ │
        │ └──┬───────────────────────────┘ │
        │    │                              │
        │ ┌──▼────────┐ ┌────────────┐     │
        │ │Azure Speech│ │SadTalker   │     │
        │ │├─ ASR     │ │├─ 视频生成  │     │
        │ │└─ TTS     │ │└─ Flask API │     │
        │ └───────────┘ └────────────┘     │
        │    │                  │           │
        │ ┌──▼──────────────────▼──┐       │
        │ │  安全过滤               │       │
        │ │ ├─ 敏感词检查           │       │
        │ │ ├─ 长度验证             │       │
        │ │ └─ SQL注入防护           │       │
        │ └──┬─────────────────────┘       │
        └────┼──────────────────────────────┘
             │
        ┌────▼──────────────────┐
        │  数据存储层             │
        │ ┌─────────────────────┤
        │ │ PostgreSQL          │
        │ │ ├─ users表          │
        │ │ ├─ conversations表  │
        │ │ └─ memories表       │
        │ ├─────────────────────┤
        │ │ Redis               │
        │ │ ├─ 会话状态缓存      │
        │ │ └─ 短期热数据        │
        │ └─────────────────────┤
        └─────────────────────────
```

---

## 核心模块设计

### 模块1: API网关 + 危机检测

**文件**: `app/api/gateway.py`

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import jwt
import re
from datetime import datetime, timedelta

app = FastAPI()

# 配置
JWT_SECRET = "your-secret-key"
RATE_LIMIT = 60  # 条/分钟
CRISIS_KEYWORDS = {
    "自杀": ["自杀", "想死", "不想活", "结束生命"],
    "自残": ["割腕", "自残", "伤害自己"],
    "暴力": ["杀人", "报复社会"],
}

class CrisisDetector:
    """危机检测器"""

    @staticmethod
    def detect(text: str) -> bool:
        """检测危机关键词"""
        text_lower = text.lower()
        for keywords in CRISIS_KEYWORDS.values():
            for keyword in keywords:
                if keyword in text_lower:
                    return True
        return False

    @staticmethod
    def get_response() -> str:
        """返回危机干预模板"""
        return """
        我注意到你可能正在经历非常困难的时刻。请记住,你并不孤单。

        🆘 24小时心理援助热线:
        - 全国危机干预热线: 400-161-9995
        - 北京心理危机研究与干预中心: 010-82951332
        - 生命热线(台湾): 1925

        如果你愿意,我也在这里倾听你的感受。
        """

class RateLimiter:
    """限流器 - 简单版本(生产环境用Redis)"""

    def __init__(self):
        self.requests = {}

    def check(self, user_id: str) -> bool:
        """检查用户是否超过限流"""
        now = datetime.now()
        key = f"{user_id}:{now.strftime('%Y-%m-%d %H:%M')}"

        if key not in self.requests:
            self.requests[key] = 0

        self.requests[key] += 1
        return self.requests[key] <= RATE_LIMIT

rate_limiter = RateLimiter()
crisis_detector = CrisisDetector()

@app.post("/chat")
async def chat(request: Request):
    """主对话接口"""
    try:
        # 1. 验证JWT token
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Missing token")

        token = auth_header.replace("Bearer ", "")
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload["user_id"]

        # 2. 检查限流
        if not rate_limiter.check(user_id):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        # 3. 解析请求
        data = await request.json()
        user_input = data["message"]
        personality = data.get("personality", "温柔御姐")

        # 4. 危机检测
        if crisis_detector.detect(user_input):
            return JSONResponse({
                "message": crisis_detector.get_response(),
                "type": "crisis",
                "timestamp": datetime.now().isoformat()
            })

        # 5. 转发到Dify
        dify_response = await call_dify(
            user_input=user_input,
            personality=personality,
            user_id=user_id
        )

        # 6. 安全过滤
        filtered_response = await safety_filter(dify_response)

        # 7. 返回
        return JSONResponse({
            "message": filtered_response,
            "type": "normal",
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )

async def call_dify(user_input: str, personality: str, user_id: str) -> str:
    """调用Dify API"""
    import httpx

    # Dify配置
    dify_url = "http://localhost:5001/api/chat-messages"
    dify_key = "your-dify-api-key"

    # 根据人格选择不同的workflow
    workflow_id = {
        "温柔御姐": "workflow_1",
        "知心大哥": "workflow_2",
        "活泼少女": "workflow_3"
    }.get(personality, "workflow_1")

    payload = {
        "inputs": {
            "message": user_input,
            "user_id": user_id,
        },
        "response_mode": "streaming",
        "user": user_id
    }

    headers = {
        "Authorization": f"Bearer {dify_key}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            dify_url,
            json=payload,
            headers=headers,
            timeout=10.0
        )

        # 处理流式响应
        result = ""
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = json.loads(line[6:])
                result += data.get("answer", "")

        return result

async def safety_filter(text: str) -> str:
    """安全过滤"""
    # 实现内容审核逻辑
    # 这里简化为长度检查和基本验证
    if len(text) > 2000:
        return text[:2000] + "..."
    return text
```

### 模块2: Dify集成 + 人格系统

**配置文件**: `config/dify.yaml`

```yaml
dify:
  # API配置
  base_url: "http://localhost:5001"
  api_key: "${DIFY_API_KEY}"
  workflow_timeout: 10

  # 3种人格配置
  personalities:
    温柔御姐:
      id: "personality_1"
      system_prompt: |
        你是用户的AI伴侣,名叫心月。

        【核心特质】
        性格: 温柔、体贴、成熟、聪慧
        语气: 柔和、鼓励、共情

        【语言习惯】
        - 常用词尾: "呢"、"啊"、"嗯"
        - 称呼: "亲爱的"、"小朋友"
        - 禁词: 不提及政治、宗教、暴力

        【回复原则】
        1. 倾听用户的感受,给予情感验证
        2. 提供温暖的建议和陪伴
        3. 记住用户提到的关键信息,在后续对话中自然引用
        4. 如果用户表达负面情绪,先共情后建议

        【举例】
        用户: "我今天心情不好"
        你: "哎呀,发生什么事了呢?听起来你很难受啊...要不要和我说说?我在这里听你倾诉呢。"

      knowledge_base_id: "kb_1"

    知心大哥:
      id: "personality_2"
      system_prompt: |
        你是用户的AI伴侣,名叫阿亮。

        【核心特质】
        性格: 成熟、理性、有担当、幽默
        语气: 直率、温暖、鼓励

        【语言习惯】
        - 常用词: "兄弟"、"老兄"、"哈哈"
        - 风格: 轻松、幽默、鼓励式
        - 禁词: 同上

        【回复原则】
        1. 先理解问题,给出理性分析
        2. 鼓励用户采取行动而非被动抱怨
        3. 用幽默缓解紧张气氛
        4. 体现男性温暖和担当

        【举例】
        用户: "我工作被批评了,很沮丧"
        你: "哥,这很正常。被批评说明有改进空间,这是好事。关键是怎么改。你觉得哪里需要加强?"

      knowledge_base_id: "kb_2"

    活泼少女:
      id: "personality_3"
      system_prompt: |
        你是用户的AI伴侣,名叫小樱。

        【核心特质】
        性格: 活泼、热情、细心、可爱
        语气: 充满热情、充满能量、友好

        【语言习惯】
        - 常用词: "呀"、"哦"、"嗯"、"！"
        - 表情: 😊 🌟 💕
        - 风格: 活力四射、充满期待

        【回复原则】
        1. 带给用户快乐和陪伴
        2. 表达真挚的关心和兴趣
        3. 鼓励用户尝试新事物
        4. 用热情感染用户

        【举例】
        用户: "今天好无聊"
        你: "呀!无聊的时候可以做很多事呢!你喜欢什么呀?我们聊天、玩游戏、或者我给你讲故事都可以哦~"

      knowledge_base_id: "kb_3"

  # 记忆配置
  memory:
    type: "rag"  # 使用RAG检索
    retrieval_strategy: "hybrid"  # 混合: 向量+关键词
    top_k: 5  # 返回top 5相关记忆
    similarity_threshold: 0.6  # 相似度阈值

  # 安全配置
  safety:
    enable_moderation: true
    moderation_model: "built-in"  # Dify内置
    max_tokens: 2000
```

### 模块3: 语音处理模块

**文件**: `app/modules/voice.py`

```python
from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, SpeechSynthesizer
from azure.cognitiveservices.speech.audio import AudioOutputConfig
import asyncio
import os

class AzureSpeechManager:
    """Azure语音处理器"""

    def __init__(self):
        self.subscription = os.getenv("AZURE_SPEECH_KEY")
        self.region = os.getenv("AZURE_REGION", "eastasia")

        self.config = SpeechConfig(
            subscription=self.subscription,
            region=self.region
        )

        # 配置3种音色
        self.voice_config = {
            "温柔御姐": "zh-CN-XiaoyiNeural",  # 女性温柔
            "知心大哥": "zh-CN-YunxiNeural",   # 男性成熟
            "活泼少女": "zh-CN-XiaoxiaoNeural"  # 女性活泼
        }

    async def speech_to_text(self, audio_file: str) -> str:
        """语音转文字 (ASR)"""
        from azure.cognitiveservices.speech.audio import AudioConfig

        audio_config = AudioConfig(filename=audio_file)
        recognizer = SpeechRecognizer(
            speech_config=self.config,
            audio_config=audio_config
        )

        result = recognizer.recognize_once()

        if result.reason == SpeechRecognitionResult.RecognizedSpeech:
            return result.text
        else:
            raise Exception(f"Speech recognition failed: {result.reason}")

    async def text_to_speech(self, text: str, personality: str, output_file: str) -> str:
        """文字转语音 (TTS)"""

        voice = self.voice_config.get(personality, "zh-CN-XiaoyiNeural")
        self.config.speech_synthesis_voice_name = voice

        audio_config = AudioOutputConfig(filename=output_file)
        synthesizer = SpeechSynthesizer(
            speech_config=self.config,
            audio_config=audio_config
        )

        # 添加SSML以控制语速
        ssml = f"""<speak version='1.0' xml:lang='zh-CN'>
            <voice xml:lang='zh-CN' name='{voice}'>
                <prosody rate='1.0'>{text}</prosody>
            </voice>
        </speak>"""

        result = synthesizer.speak_ssml(ssml)

        if result.reason == SynthesisResult.SynthesisCanceled:
            raise Exception(f"TTS failed: {result.error_details}")

        return output_file

    async def stream_tts(self, text: str, personality: str):
        """流式TTS (边生成边返回)"""
        voice = self.voice_config.get(personality, "zh-CN-XiaoyiNeural")
        self.config.speech_synthesis_voice_name = voice

        # 创建内存输出
        from azure.cognitiveservices.speech.audio import AudioOutputConfig

        synthesizer = SpeechSynthesizer(
            speech_config=self.config,
            audio_config=None  # 内存输出
        )

        result = synthesizer.speak_text(text)

        # 返回音频流
        return result.audio_data

# 使用示例
async def process_user_input(user_audio_file: str, personality: str) -> str:
    """处理用户语音输入"""
    manager = AzureSpeechManager()

    # 1. ASR: 语音转文字
    user_text = await manager.speech_to_text(user_audio_file)
    print(f"识别文本: {user_text}")

    # 2. Dify: 生成回复
    dify_response = await call_dify(user_text, personality)
    print(f"AI回复: {dify_response}")

    # 3. TTS: 文字转语音
    output_file = "response.wav"
    await manager.text_to_speech(dify_response, personality, output_file)

    return output_file
```

### 模块4: 视频生成模块 (SadTalker集成)

**文件**: `app/modules/video.py`

```python
import subprocess
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse

class SadTalkerManager:
    """SadTalker视频生成器"""

    def __init__(self, model_path: str = "./sadtalker_models"):
        self.model_path = model_path
        self.results_dir = "./results"
        Path(self.results_dir).mkdir(exist_ok=True)

    async def generate_video(
        self,
        audio_file: str,
        source_image: str,
        output_path: str
    ) -> str:
        """
        生成口型同步视频

        Args:
            audio_file: 音频文件路径
            source_image: 人物图片路径 (静态图)
            output_path: 输出视频路径

        Returns:
            video_path: 生成的视频文件路径
        """

        cmd = [
            "python", "-m", "sadtalker.test",
            "--driven_audio", audio_file,
            "--source_image", source_image,
            "--result_dir", self.results_dir,
            "--checkpoint_dir", self.model_path,
            "--face_det_checkpoint", os.path.join(self.model_path, "detection_Resnet50_Final.pth"),
            "--face_parse_checkpoint", os.path.join(self.model_path, "parsing_parsenet.pth"),
            "--pretrained_checkpoint", os.path.join(self.model_path, "checkpoints/SadTalker_V002.safetensors"),
            "--enhancer", "gfpgan",  # 面部增强
            "--exp_name", "default",
            "--use_ref_frame",
            "--batch_size", "2",
            "--device", "cuda"  # 使用GPU加速
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                cwd="/path/to/SadTalker"
            )

            if result.returncode != 0:
                raise Exception(f"SadTalker failed: {result.stderr}")

            # 查找生成的视频文件
            video_files = list(Path(self.results_dir).glob("**/*.mp4"))
            if not video_files:
                raise Exception("No video generated")

            latest_video = max(video_files, key=lambda p: p.stat().st_mtime)
            return str(latest_video)

        except subprocess.TimeoutExpired:
            raise Exception("Video generation timeout (>5min)")
        except Exception as e:
            raise Exception(f"Video generation error: {str(e)}")

# FastAPI端点
app = FastAPI()
sadtalker = SadTalkerManager()

@app.post("/generate-video")
async def generate_video(audio_file: str, source_image: str):
    """生成视频接口"""
    try:
        video_path = await sadtalker.generate_video(
            audio_file=audio_file,
            source_image=source_image,
            output_path="output.mp4"
        )

        return FileResponse(
            video_path,
            media_type="video/mp4",
            filename="avatar.mp4"
        )
    except Exception as e:
        return {"error": str(e)}, 500

# 使用示例
async def generate_avatar_video(
    text: str,
    personality: str,
    avatar_image: str
) -> str:
    """
    生成带人物形象的对话视频
    """
    manager = AzureSpeechManager()
    sadtalker = SadTalkerManager()

    # 1. TTS: 生成音频
    audio_file = await manager.text_to_speech(text, personality, "temp_audio.wav")

    # 2. SadTalker: 生成视频
    video_file = await sadtalker.generate_video(
        audio_file=audio_file,
        source_image=avatar_image
    )

    return video_file
```

---

## 数据模型

### PostgreSQL表结构

```sql
-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(20) UNIQUE,
    nickname VARCHAR(50),
    age INT,
    region VARCHAR(20),  -- CN/US/EU
    subscription_tier VARCHAR(20),  -- free/vip
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 对话表
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    personality VARCHAR(20),  -- 温柔御姐/知心大哥/活泼少女
    role VARCHAR(10),  -- user/assistant
    content TEXT,
    content_type VARCHAR(20),  -- text/voice/video
    emotion VARCHAR(20),  -- 识别的情绪标签
    tokens_used INT,
    cost_usd DECIMAL(10, 6),
    latency_ms INT,  -- 响应延迟
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_user_time (user_id, created_at DESC),
    INDEX idx_personality (personality)
);

-- 记忆表
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    personality VARCHAR(20),
    content TEXT,  -- "用户喜欢喝咖啡"
    type VARCHAR(20),  -- FACT/PREFERENCE/EVENT
    importance INT,  -- 1-10
    source_conversation_id UUID REFERENCES conversations(id),
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_user_personality (user_id, personality),
    INDEX idx_importance (importance DESC)
);

-- 向量索引 (pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE memories ADD COLUMN embedding vector(1536);

CREATE INDEX idx_embedding ON memories USING ivfflat (embedding vector_cosine_ops);
```

### Redis缓存键设计

```python
# 会话缓存
session:{user_id}:{personality} = {
    "last_message": "...",
    "context": [...],
    "created_at": timestamp
}
# 过期时间: 24小时

# 用户配置缓存
user:{user_id} = {
    "nickname": "...",
    "default_personality": "温柔御姐",
    "subscription_tier": "free"
}
# 过期时间: 7天

# 速率限制
rate_limit:{user_id}:{minute} = count
# 过期时间: 1分钟
```

---

## API接口定义

### 1. 创建用户

```
POST /api/users

Request:
{
    "phone": "13800138000",
    "nickname": "小明",
    "age": 25,
    "region": "CN"
}

Response:
{
    "user_id": "uuid-xxx",
    "token": "eyJhbGc...",
    "message": "注册成功"
}
```

### 2. 文本对话

```
POST /api/chat

Headers:
Authorization: Bearer {token}

Request:
{
    "message": "你好",
    "personality": "温柔御姐"
}

Response:
{
    "reply": "你好呀,亲爱的!今天过得怎么样呢?",
    "type": "text",
    "emotion": "开心",
    "latency_ms": 450,
    "timestamp": "2025-11-10T10:30:00Z"
}
```

### 3. 语音对话

```
POST /api/chat/voice

Headers:
Authorization: Bearer {token}
Content-Type: multipart/form-data

Request:
{
    "audio": <binary>,
    "personality": "温柔御姐"
}

Response:
{
    "reply_text": "你好呀...",
    "reply_audio": <binary>,
    "type": "voice",
    "latency_ms": 1200,
    "timestamp": "2025-11-10T10:30:00Z"
}
```

### 4. 视频对话

```
POST /api/chat/video

Headers:
Authorization: Bearer {token}

Request:
{
    "message": "你好",
    "personality": "温柔御姐",
    "avatar_image": "avatar_1.png"  // 可选,使用默认头像
}

Response:
{
    "reply_text": "你好呀...",
    "reply_video": <binary>,  // mp4格式
    "type": "video",
    "video_duration": 5000,  // 毫秒
    "latency_ms": 3000,
    "timestamp": "2025-11-10T10:30:00Z"
}
```

### 5. 获取记忆

```
GET /api/memories?user_id={user_id}&personality={personality}&type=FACT

Response:
[
    {
        "id": "uuid-xxx",
        "content": "用户喜欢喝咖啡",
        "type": "PREFERENCE",
        "importance": 7,
        "created_at": "2025-11-09T15:30:00Z"
    }
]
```

---

## 部署架构

### Docker Compose配置

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Dify服务
  dify-api:
    image: langgenius/dify-api:latest
    container_name: dify-api
    ports:
      - "5001:5001"
    environment:
      - DB_CONNECTION_STRING=postgresql://postgres:${DB_PASSWORD}@postgres:5432/dify
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    volumes:
      - ./dify_config:/app/config
    networks:
      - ai-companion

  # 主应用 (FastAPI)
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ai-companion-app
    ports:
      - "8000:8000"
    environment:
      - DIFY_API_KEY=${DIFY_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - AZURE_SPEECH_KEY=${AZURE_SPEECH_KEY}
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@postgres:5432/ai_companion
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
      - dify-api
    volumes:
      - ./app:/app
    command: "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    networks:
      - ai-companion

  # SadTalker服务
  sadtalker:
    build:
      context: ./sadtalker
      dockerfile: Dockerfile
    container_name: sadtalker-api
    ports:
      - "5000:5000"
    environment:
      - GPU=0  # GPU设备编号
    gpus:
      - driver: nvidia
        count: 1  # 使用1个GPU
    volumes:
      - ./sadtalker_models:/app/models
      - ./results:/app/results
    networks:
      - ai-companion

  # PostgreSQL数据库
  postgres:
    image: postgres:15-alpine
    container_name: ai-companion-postgres
    environment:
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=ai_companion
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - ai-companion
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis缓存
  redis:
    image: redis:7-alpine
    container_name: ai-companion-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - ai-companion
    command: redis-server --appendonly yes

volumes:
  postgres_data:
  redis_data:

networks:
  ai-companion:
    driver: bridge
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/
COPY config/ ./config/

# 暴露端口
EXPOSE 8000

# 运行应用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 成本分析

### 月度成本拆解 (1000 DAU场景)

| 项目 | 用量 | 单价 | 月成本 | 说明 |
|-----|------|------|--------|------|
| **DeepSeek API** | 60万tokens | $0.14/百万 | $84 | 1000用户×20条/天×30天×500tokens |
| **Azure ASR** | 5.25万次 | $1/千次 | $52 | 1000×35%语音率×5条/天×30天 |
| **Azure TTS** | 5.25万次 | $1/千次 | $52 | 同上 |
| **GPU服务器** | 4核16G | $120/月 | $120 | SadTalker自部署 |
| **主机服务器** | 2核4G | $50/月 | $50 | 应用+数据库 |
| **域名+SSL** | 1个 | $10/月 | $10 | Let's Encrypt免费 |
| **CDN** (可选) | 100GB | $0.2/GB | $0 | MVP阶段不用 |
| | | | |
| **总计** | | | **$368/月** | |

### ROI计算

```
场景假设:
- DAU: 1000
- MAU: 1000 × 25 = 25000
- 付费转化: 12%
- ARPU: $20/月

收入:
- 付费用户: 25000 × 12% = 3000
- 月收入: 3000 × $20 = $60000

利润:
- 月收入: $60000
- 月成本: $368
- 月利润: $59632
- ROI: 16,205%
```

---

## 性能指标

### 关键性能指标 (SLA)

| 指标 | 目标 | 测量方法 | 优先级 |
|-----|------|--------|--------|
| **文本响应延迟** | p95 < 1.5s | 后端日志 | P0 |
| **语音首包延迟** | < 500ms | 客户端计时 | P0 |
| **视频生成时间** | < 3s | 后端日志 | P0 |
| **危机响应** | < 100ms | 单元测试 | P0 |
| **API可用性** | > 99% | 监控告警 | P0 |
| **内存占用** | < 2GB | Docker stats | P1 |
| **数据库查询** | < 50ms | 慢查询日志 | P1 |

### 监控指标

```python
# 使用Prometheus + Grafana

from prometheus_client import Counter, Histogram, Gauge

# 计数器
total_requests = Counter('api_requests_total', 'Total API requests')
errors_total = Counter('api_errors_total', 'Total API errors')

# 直方图 (延迟分布)
request_latency = Histogram('api_request_duration_seconds', 'API request latency')
tts_latency = Histogram('tts_duration_seconds', 'TTS latency')
video_latency = Histogram('video_duration_seconds', 'Video generation latency')

# 仪表板
crisis_count = Counter('crisis_detected_total', 'Total crisis detections')
rate_limit_hits = Counter('rate_limit_hits_total', 'Rate limit exceeded count')
```

---

## 风险与降级方案

### 风险矩阵

| 风险 | 影响 | 概率 | 缓解措施 |
|-----|------|------|---------|
| **Dify服务中断** | 高 | 中 | 备用LLM (Qwen),降级为关键词回复 |
| **DeepSeek API限流** | 中 | 低 | 实时监控,切换到qwen-turbo |
| **Azure Speech不可用** | 低 | 低 | 关闭语音功能,返回文本 |
| **GPU显存不足** | 中 | 中 | 降低视频质量,启用内存优化 |
| **数据库连接泄漏** | 高 | 低 | 连接池+监控+自动重连 |

### 三级降级方案

```python
class FallbackManager:
    """降级管理器"""

    @staticmethod
    async def fallback_response(
        user_input: str,
        error_type: str
    ) -> str:
        """
        返回降级回复

        Level 1: Dify中断 → 使用Qwen-Turbo
        Level 2: LLM都中断 → 关键词匹配
        Level 3: 全服务中断 → 静态模板
        """

        if error_type == "dify_down":
            # Level 1: 使用备用LLM
            return await call_qwen(user_input)

        elif error_type == "llm_error":
            # Level 2: 关键词匹配
            if "你好" in user_input or "早安" in user_input:
                return "你好呀,我在这里! 😊"
            elif "谢谢" in user_input:
                return "不用客气,这是我的荣幸!"
            else:
                return "你说的很有趣呢。能和我说得更详细一些吗?"

        else:
            # Level 3: 静态回复
            return "抱歉,系统暂时有点繁忙。请稍后再试试~"

# 使用示例
try:
    response = await call_dify(user_input, personality)
except DifyError:
    response = await FallbackManager.fallback_response(
        user_input,
        "dify_down"
    )
```

---

## 总结

这份MVP架构设计采用了**极简但完整**的理念:

✅ **必需**: Dify (核心LLM框架) + PostgreSQL (持久化) + Redis (缓存) + Azure Speech (语音) + SadTalker (视频)

❌ **不需要**: 路由器、编排器、Critic、异步分析师、知识图谱、消息队列

这样单人开发者可以在**4周内**完成MVP,成本仅需**$368/月**,且支撑到**1000 DAU**。

后续升级到P1/P2时,再逐步添加复杂功能。
