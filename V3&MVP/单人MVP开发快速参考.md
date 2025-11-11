# AI伴侣 MVP 单人开发快速参考指南

**项目**: AI伴侣Agent
**目标**: 4周内交付可演示的MVP
**开发者**: 1人
**成本**: 约$280/月(优化后,使用SadTalker自部署)

---

## 📋 核心功能清单(PRD P0,必须完成)

- [x] **基础对话**: 文本输入 + Dify LLM + 3种人格Prompt
- [x] **语音交互**: Azure Speech SDK (ASR + TTS, 3种音色)
- [x] **Video Avatar**: SadTalker自部署 (口型同步视频)
- [x] **人格切换**: 温柔御姐/知心大哥/活泼少女
- [x] **简单记忆**: Dify知识库 + PostgreSQL对话历史
- [x] **危机干预**: 10个关键词 → 固定模板+热线
- [x] **基础安全**: Dify内置审核 + 输入验证

---

## 🎯 4周开发路线图(28天)

### Week 1: 环境搭建 (Day 1-7)

#### Day 1-2: Dify + 数据库部署
```bash
# Dify本地部署 (Docker)
git clone https://github.com/langgenius/dify.git
cd dify/docker
docker-compose up -d

# PostgreSQL + Redis
docker run -d -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15
docker run -d -p 6379:6379 redis:7
```
- 验证Dify Web界面 (http://localhost)
- 创建3个Persona (温柔御姐/知心大哥/活泼少女)
- 导入DeepSeek-V3 LLM配置

#### Day 3: DeepSeek API申请 + 第一个Chatflow
1. 访问 https://platform.deepseek.com
2. 申请API Key (首次充值$5即可)
3. 在Dify中配置DeepSeek-V3作为LLM
4. 创建简单Chatflow: 输入 → LLM → 输出
5. 测试: "你好" → "你好!我是你的AI伴侣..."

#### Day 4-5: Azure Speech SDK集成
```bash
# Azure Speech Python SDK
pip install azure-cognitiveservices-speech

# 测试代码
from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer, SpeechSynthesizer

config = SpeechConfig(
    subscription="YOUR_KEY",  # 从Azure Portal获取
    region="eastasia"
)

# ASR测试
recognizer = SpeechRecognizer(speech_config=config)
result = recognizer.recognize_once()
print(result.text)

# TTS测试
synthesizer = SpeechSynthesizer(speech_config=config)
audio_config = AudioOutputConfig(filename="output.wav")
synthesizer.speak_text_async("你好").get()
```
- 申请Azure认知服务Free Tier (前5小时免费)
- 配置3种音色 (女性温柔/男性沉稳/女性活泼)
- 集成到Flask API

#### Day 6-7: SadTalker视频部署
```bash
# 环境: Ubuntu 20.04 + CUDA 11.8
git clone https://github.com/OpenTalker/SadTalker.git
cd SadTalker

# 安装依赖
conda create -n sadtalker python=3.8
conda activate sadtalker
pip install -r requirements.txt

# 下载模型 (约2GB,可能需要VPN)
bash scripts/download_models.sh

# 启动Flask API
python -c "
from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route('/generate_video', methods=['POST'])
def generate_video():
    data = request.json
    audio_path = data['audio']
    image_path = data['image']

    cmd = f'python -m sadtalker.test --driven_audio {audio_path} --source_image {image_path} --result_dir ./results'
    subprocess.run(cmd, shell=True)

    return jsonify({'video': './results/video.mp4'})

app.run(port=5000)
"
```

### Week 2: 核心功能 (Day 8-14)

#### Day 8-9: 3种人格Prompt配置

在Dify中为每个人格创建独立的System Prompt:

**人格1: 温柔御姐**
```
你是用户的AI伴侣,名叫心月。

性格特点: 温柔、体贴、成熟、聪慧
语气: "呢"、"啊"、"嗯"为结尾
称呼: 亲爱的、小朋友
禁忌: 不提及政治、宗教、暴力

你的目标是倾听用户的感受,给予温暖的回应和建议。

示例对话:
用户: "我今天心情不好"
你: "哎呀,发生什么事了呢?听起来你很难受啊...要不要和我说说?我在这里听你倾诉呢。"

用户: "没什么,就是工作压力大"
你: "这种时候谁都会感到疲惫的。你已经很努力了。要不要试试深呼吸?或者和我聊天放松一下呢?"
```

**人格2: 知心大哥**
```
你是用户的AI伴侣,名叫阿亮。

性格特点: 成熟、理性、有担当、幽默
语气: 直率、温暖、鼓励式
称呼: 兄弟、老兄
禁忌: 同上

你的目标是给出理性建议,鼓励用户采取行动。

示例对话:
用户: "我工作被批评了,很沮丧"
你: "哥,这很正常。被批评说明有改进空间,这是好事。关键是怎么改。你觉得哪里需要加强?"
```

**人格3: 活泼少女**
```
你是用户的AI伴侣,名叫小樱。

性格特点: 活泼、热情、细心、可爱
语气: 多用感叹号、表情符号、"呀"、"哦"、"嗯"
称呼: 小姐姐/小哥哥、亲
禁忌: 同上

你的目标是带给用户快乐和陪伴。

示例对话:
用户: "今天好无聊"
你: "呀!无聊的时候可以做很多事呢!你喜欢什么呀?我们聊天、玩游戏、或者我给你讲故事都可以哦~"
```

#### Day 8补充: API网关完整实现

**文件: app/api/gateway.py**

完整实现JWT认证、限流、危机检测三大功能:

```python
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import jwt
import redis
import httpx
import json
from datetime import datetime, timedelta

app = FastAPI()
security = HTTPBearer()
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# 配置
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
RATE_LIMIT = 60  # 60条/分钟

CRISIS_KEYWORDS = {
    "自杀": ["自杀", "想死", "不想活", "结束生命"],
    "自残": ["割腕", "自残", "伤害自己"],
    "暴力": ["杀人", "报复社会"],
}

class AuthManager:
    """JWT认证管理"""

    @staticmethod
    def create_token(user_id: str) -> str:
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(days=7)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> str:
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload["user_id"]
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

class CrisisDetector:
    """危机检测器"""

    @staticmethod
    def detect(text: str) -> bool:
        text_lower = text.lower()
        for keywords in CRISIS_KEYWORDS.values():
            for keyword in keywords:
                if keyword in text_lower:
                    return True
        return False

    @staticmethod
    def get_response() -> str:
        return """
我注意到你可能正在经历非常困难的时刻。请记住,你并不孤单。

🆘 24小时心理援助热线:
- 全国危机干预热线: 400-161-9995
- 北京心理危机研究与干预中心: 010-82951332
- 生命热线(台湾): 1925

如果你愿意,我也在这里倾听你的感受。
"""

class RateLimiter:
    """Redis限流器"""

    @staticmethod
    def check(user_id: str) -> bool:
        now = datetime.now()
        key = f"rate_limit:{user_id}:{now.strftime('%Y-%m-%d %H:%M')}"

        count = redis_client.incr(key)
        if count == 1:
            redis_client.expire(key, 60)  # 1分钟过期

        return count <= RATE_LIMIT

# 依赖注入
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    return AuthManager.verify_token(token)

crisis_detector = CrisisDetector()

@app.post("/api/users")
async def create_user(request: Request):
    """用户注册"""
    data = await request.json()
    user_id = f"user_{datetime.now().timestamp()}"

    # TODO: 存储到PostgreSQL

    token = AuthManager.create_token(user_id)
    return {
        "user_id": user_id,
        "token": token,
        "message": "注册成功"
    }

@app.post("/chat")
async def chat(
    request: Request,
    user_id: str = Depends(get_current_user)
):
    """主对话接口"""
    # 限流检查
    if not RateLimiter.check(user_id):
        raise HTTPException(status_code=429, detail="请求过于频繁,请稍后再试")

    data = await request.json()
    user_input = data["message"]
    personality = data.get("personality", "温柔御姐")

    # 危机检测
    if crisis_detector.detect(user_input):
        return JSONResponse({
            "message": crisis_detector.get_response(),
            "type": "crisis",
            "timestamp": datetime.now().isoformat()
        })

    # 调用Dify
    dify_response = await call_dify(user_input, personality, user_id)

    # 安全过滤
    filtered_response = await safety_filter(dify_response)

    return JSONResponse({
        "message": filtered_response,
        "type": "normal",
        "timestamp": datetime.now().isoformat()
    })

async def call_dify(user_input: str, personality: str, user_id: str) -> str:
    """调用Dify API"""
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
    if len(text) > 2000:
        return text[:2000] + "..."
    return text
```

测试验证:
```bash
# 1. 获取token
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{"phone":"13800138000","nickname":"测试用户"}'

# 2. 使用token对话
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer {your_token}" \
  -H "Content-Type: application/json" \
  -d '{"message":"你好","personality":"温柔御姐"}'
```

#### Day 9: Redis缓存策略

**文件: app/cache/manager.py**

```python
import redis
import json
from typing import Optional, List
from datetime import datetime

class CacheManager:
    """统一缓存管理"""

    def __init__(self):
        self.redis = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )

    # 会话缓存 (24小时)
    def set_session(self, user_id: str, personality: str, context: List[dict]):
        key = f"session:{user_id}:{personality}"
        value = json.dumps({
            "context": context,
            "created_at": datetime.now().isoformat()
        })
        self.redis.setex(key, 86400, value)  # 24小时

    def get_session(self, user_id: str, personality: str) -> Optional[List[dict]]:
        key = f"session:{user_id}:{personality}"
        data = self.redis.get(key)
        if data:
            return json.loads(data)["context"]
        return None

    # 用户配置缓存 (7天)
    def set_user(self, user_id: str, config: dict):
        key = f"user:{user_id}"
        self.redis.setex(key, 604800, json.dumps(config))  # 7天

    def get_user(self, user_id: str) -> Optional[dict]:
        key = f"user:{user_id}"
        data = self.redis.get(key)
        return json.loads(data) if data else None

    # 记忆缓存 (热门记忆,1小时)
    def cache_memory(self, user_id: str, personality: str, memories: List[dict]):
        key = f"memory:{user_id}:{personality}"
        self.redis.setex(key, 3600, json.dumps(memories))

    def get_cached_memory(self, user_id: str, personality: str) -> Optional[List[dict]]:
        key = f"memory:{user_id}:{personality}"
        data = self.redis.get(key)
        return json.loads(data) if data else None
```

使用示例:
```python
cache = CacheManager()

# 存储对话上下文
cache.set_session(
    user_id="user-123",
    personality="温柔御姐",
    context=[
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好呀~"}
    ]
)

# 获取历史上下文
history = cache.get_session("user-123", "温柔御姐")

# 缓存用户配置
cache.set_user("user-123", {
    "nickname": "小明",
    "default_personality": "温柔御姐",
    "subscription_tier": "free"
})
```

#### Day 10-11: 记忆系统配置

1. **Dify知识库设置**:
   - 创建3个Dataset (一个per人格)
   - 导入预制记忆:
     - 用户基本信息: 姓名、年龄、职业
     - 重要关系: 家人、朋友、同事
     - 偏好: 音乐、电影、食物
     - 创伤事件: (用户主动告诉时记录)

2. **PostgreSQL表设计**:
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    name VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users,
    role VARCHAR(10),  -- "user" or "assistant"
    content TEXT,
    personality VARCHAR(20),  -- "温柔御姐" | "知心大哥" | "活泼少女"
    emotion VARCHAR(20),  -- 情绪标签
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE memories (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users,
    content TEXT,  -- "用户喜欢咖啡"
    importance INT,  -- 1-10
    created_at TIMESTAMP DEFAULT NOW()
);

-- 向量索引 (pgvector)
CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE memories ADD COLUMN embedding vector(1536);
CREATE INDEX idx_embedding ON memories USING ivfflat (embedding vector_cosine_ops);
```

3. **记忆提取逻辑** (在Dify中配置):
   - 新对话 → LLM提取关键信息 → 存入PostgreSQL memories表

#### Day 12: 危机关键词配置

在API网关中配置:
```python
CRISIS_KEYWORDS = {
    "suicide": ["自杀", "想死", "不想活", "结束生命"],
    "self_harm": ["割腕", "自残", "伤害自己"],
    "violence": ["杀人", "报复社会"],
}

CRISIS_RESPONSE = """
我注意到你可能正在经历非常困难的时刻。请记住,你并不孤单。

🆘 24小时心理援助热线:
- 全国危机干预热线: 400-161-9995
- 北京心理危机研究与干预中心: 010-82951332
- 生命热线(台湾): 1925(安心专线)

如果你愿意,我也在这里倾听你的感受。
"""
```

#### Day 13-14: 多人格切换逻辑

前端实现:
```javascript
// 人格选择
onPersonalityChange(personality) {
  // 切换Dify的System Prompt
  // 切换对应的记忆库
  // 保存选择到localStorage
  this.currentPersonality = personality;
}
```

### Week 3: 集成测试 (Day 15-21)

#### Day 15-17: 端到端测试

1. **文本对话测试**:
   - 输入: "你好"
   - 预期: 根据当前人格返回问候
   - 验证: 40ms内返回

2. **语音对话测试**:
   - 输入: 录音 "我今天很开心"
   - 流程: ASR → Dify → TTS
   - 验证: 首包<500ms,总耗时<2s

3. **视频测试**:
   - 输入: 文本
   - 流程: Dify → TTS → SadTalker
   - 验证: 视频<3s生成

4. **多人格切换测试**:
   - 同一句话用3种人格回复,检查一致性

#### Day 18-19: Prompt调优

基于实际测试调优:
- 情绪准确度: 测试"我好累" → 应返回共情而非建议
- 记忆引用: "你记得我叫什么吗?" → 应准确提取
- 人格一致: 每个回复都体现该人格特质

#### Day 20-21: 简单Web UI开发

用Vue3 + Element Plus构建:
```vue
<template>
  <div class="chat-container">
    <!-- 人格选择 -->
    <el-select v-model="personality" @change="switchPersonality">
      <el-option label="温柔御姐" value="温柔御姐"></el-option>
      <el-option label="知心大哥" value="知心大哥"></el-option>
      <el-option label="活泼少女" value="活泼少女"></el-option>
    </el-select>

    <!-- 对话窗口 -->
    <div class="messages">
      <div v-for="msg in messages" :key="msg.id" class="message" :class="msg.role">
        {{ msg.content }}
      </div>
    </div>

    <!-- 视频窗口 (可选) -->
    <video v-if="videoUrl" :src="videoUrl" controls></video>

    <!-- 输入区 -->
    <div class="input-area">
      <textarea v-model="inputText" placeholder="输入消息..."></textarea>
      <button @click="sendMessage">发送</button>
      <button @click="startVoice" :disabled="isListening">🎤 语音</button>
    </div>
  </div>
</template>
```

### Week 4: 部署上线 (Day 22-28)

#### Day 22-23: Docker生产部署

**docker-compose.prod.yml**:
```yaml
version: '3.8'

services:
  # Nginx反向代理
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    networks:
      - ai-companion
    restart: unless-stopped

  # 主应用 (FastAPI)
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ai-companion-app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@postgres:5432/ai_companion
      - REDIS_URL=redis://redis:6379
      - DIFY_API_KEY=${DIFY_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - AZURE_SPEECH_KEY=${AZURE_SPEECH_KEY}
      - AZURE_REGION=eastasia
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - postgres
      - redis
      - dify-api
    volumes:
      - ./app:/app
    command: "uvicorn app.main:app --host 0.0.0.0 --port 8000"
    networks:
      - ai-companion
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  # Dify服务
  dify-api:
    image: langgenius/dify-api:latest
    container_name: dify-api
    ports:
      - "5001:5001"
    environment:
      - DB_CONNECTION_STRING=postgresql://postgres:${DB_PASSWORD}@postgres:5432/dify
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${DIFY_SECRET_KEY}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./dify_config:/app/config
    networks:
      - ai-companion
    restart: unless-stopped

  # SadTalker服务
  sadtalker:
    build:
      context: ./sadtalker
      dockerfile: Dockerfile
    container_name: sadtalker-api
    ports:
      - "5000:5000"
    environment:
      - GPU=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    volumes:
      - ./sadtalker_models:/app/models
      - ./results:/app/results
    networks:
      - ai-companion
    restart: unless-stopped

  # PostgreSQL + pgvector
  postgres:
    image: ankane/pgvector:latest
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
    restart: unless-stopped
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
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    restart: unless-stopped

  # Prometheus监控
  prometheus:
    image: prom/prometheus:latest
    container_name: ai-companion-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    networks:
      - ai-companion
    restart: unless-stopped

  # Grafana可视化
  grafana:
    image: grafana/grafana:latest
    container_name: ai-companion-grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - ai-companion
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  ai-companion:
    driver: bridge
```

**Dockerfile**:
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

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 运行应用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**环境变量配置 (.env)**:
```
# 数据库
DB_PASSWORD=your_secure_password_here

# API密钥
DIFY_API_KEY=app-xxx
DIFY_SECRET_KEY=your-dify-secret
DEEPSEEK_API_KEY=sk-xxx
AZURE_SPEECH_KEY=xxx
AZURE_REGION=eastasia

# JWT
JWT_SECRET=your-super-secret-key-change-this

# Redis
REDIS_PASSWORD=your_redis_password

# Grafana
GRAFANA_PASSWORD=admin_password
```

部署命令:
```bash
# 1. 准备环境
cp .env.example .env
vim .env  # 填写真实密钥

# 2. 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 3. 检查健康状态
docker-compose ps
docker-compose logs -f app

# 4. 数据库迁移
docker-compose exec app alembic upgrade head

# 5. 验证服务
curl http://localhost:8000/health
```

#### Day 24: 监控告警配置