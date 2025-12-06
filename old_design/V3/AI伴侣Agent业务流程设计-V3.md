# AI伴侣Agent V3 业务流程设计

## 文档信息
- **版本**: V3.0
- **创建日期**: 2025/11/19
- **基于架构**: [AI伴侣Agent架构设计-V3.md](./V3/AI伴侣Agent架构设计-V3.md)
- **模块数量**: 7个核心业务模块

---

## 目录

1. [角色创建模块业务流](#角色创建模块业务流)
2. [角色问答模块业务流](#角色问答模块业务流)
3. [2.5D形象互动模块业务流](#2.5d形象互动模块业务流)
4. [照片建模VIP服务业务流](#照片建模vip服务业务流)
5. [新用户引导模块业务流](#新用户引导模块业务流)
6. [记忆管理模块业务流](#记忆管理模块业务流)
7. [VIP功能升级模块业务流](#vip功能升级模块业务流)

---

## 角色创建模块业务流

```mermaid
flowchart TD
    %% 泳道定义
    subgraph 用户层 ["👤 用户层"]
        A1[用户进入角色创建界面]
        A2[选择创建方式]
        A3[输入角色信息]
        A4[上传照片/视频]
        A5[选择风格偏好]
        A6[查看预览效果]
        A7[确认创建]
        A8[完成创建]
    end

    subgraph 客户端层 ["📱 客户端层"]
        B1[显示角色创建界面]
        B2[展示创建选项]
        B3[表单验证]
        B4[文件上传处理]
        B5[调用创建API]
        B6[加载进度显示]
        B7[展示创建结果]
    end

    subgraph API网关层 ["🚪 API网关层"]
        C1[鉴权验证]
        C2[输入安全检查]
        C3[请求路由分发]
        C4[VIP权限检查]
        C5[返回响应]
    end

    subgraph 智能路由层 ["🧭 智能路由层"]
        D1[意图识别]
        D2[检测创建模式]
        D3[分发到对应Agent]
    end

    subgraph 业务服务层 ["⚙️ 业务服务层"]
        E1[基础模板Agent]
        E2[160性格引擎]
        E3[照片建模Agent]
        E4[角色配置服务]
        E5[数据库存储]
    end

    subgraph 存储层 ["💾 存储层"]
        F1[用户数据库]
        F2[角色数据库]
        F3[模型存储MinIO]
        F4[配置缓存Redis]
    end

    %% 流程连接
    A1 --> B1
    B1 --> A2
    A2 --> B2
    B2 --> A3
    A3 --> B3

    %% 基础模板创建路径
    B3 -->|选择基础模板| B5
    B5 --> C1
    C1 --> C2
    C2 --> C3
    C3 --> D1
    D1 -->|基础模板创建| D2
    D2 --> D3
    D3 --> E1
    E1 --> E2
    E2 --> E4
    E4 --> E5
    E5 --> F1
    E5 --> F2
    E5 --> F4
    F4 --> C5
    C5 --> B6
    B6 --> A6
    A6 --> A7
    A7 --> B7
    B7 --> A8

    %% VIP照片建模路径
    A3 -->|选择照片建模| A4
    A4 --> B4
    B4 -->|照片/视频文件| B5
    B5 --> C1
    C1 -->|VIP功能检查| C4
    C4 -->|VIP权限验证| D1
    D1 -->|照片建模请求| D2
    D2 --> D3
    D3 --> E3
    E3 -->|AI建模处理| F3
    F3 --> E4
    E4 --> E5
    E5 --> F1
    E5 --> F2
    E5 --> F3
    F3 --> C5
    C5 --> B6
    B6 -->|显示建模进度| A5
    A5 --> A6

    %% 样式定义
    classDef user fill:#e0f2fe,stroke:#0284c7,stroke-width:2px
    classDef client fill:#fef3c7,stroke:#f59e0b,stroke-width:2px
    classDef gateway fill:#ddd6fe,stroke:#7c3aed,stroke-width:2px
    classDef router fill:#d1fae5,stroke:#10b981,stroke-width:2px
    classDef service fill:#fecaca,stroke:#dc2626,stroke-width:2px
    classDef storage fill:#fed7aa,stroke:#ea580c,stroke-width:2px

    class A1,A2,A3,A4,A5,A6,A7,A8 user
    class B1,B2,B3,B4,B5,B6,B7 client
    class C1,C2,C3,C4,C5 gateway
    class D1,D2,D3 router
    class E1,E2,E3,E4,E5 service
    class F1,F2,F3,F4 storage
```

### 角色创建模块流程说明

#### 1. 基础模板创建流程
1. **用户选择**: 用户选择基础模板创建方式
2. **信息输入**: 填写角色名称、性格描述等基本信息
3. **性格匹配**: 160种性格引擎进行MBTI×语言风格匹配
4. **配置保存**: 保存角色配置到数据库和缓存
5. **创建完成**: 返回创建成功结果

#### 2. VIP照片建模流程
1. **VIP权限检查**: 验证用户是否有照片建模权限
2. **文件上传**: 用户上传3-5张照片或1-2个视频
3. **AI建模处理**: 调用AI建模服务进行3D模型生成
4. **质量评估**: 评估建模质量和相似度
5. **存储优化**: 优化模型并存储到MinIO
6. **结果返回**: 返回建模结果和预览链接

#### 3. 关键检查点
- **权限验证**: VIP功能权限检查
- **文件验证**: 照片质量和数量验证
- **内容安全**: 上传内容安全检查
- **性能优化**: 大文件处理和进度反馈

---

## 角色问答模块业务流

```mermaid
flowchart TD
    %% 泳道定义
    subgraph 用户层 ["👤 用户层"]
        A1[用户输入对话消息]
        A2[等待回复]
        A3[查看回复内容]
        A4[查看2.5D形象]
        A5[继续对话或结束]
    end

    subgraph 客户端层 ["📱 客户端层"]
        B1[消息输入界面]
        B2[消息预处理]
        B3[发送请求]
        B4[显示加载状态]
        B5[渲染回复内容]
        B6[播放形象动画]
        B7[界面更新]
    end

    subgraph API网关层 ["🚪 API网关层"]
        C1[身份鉴权]
        C2[输入安全预检]
        C3[危机信号检测]
        C4[请求限流]
        C5[响应返回]
    end

    subgraph 智能路由层 ["🧭 智能路由层"]
        D1[意图识别]
        D2[复杂度评估]
        D3[VIP模式检测]
        D4[路由决策]
    end

    subgraph 同步处理层 ["⚡ 同步处理层"]
        E1[快速通道]
        E2[智能通道]
        E3[VIP专属Agent]
        E4[情感传感器]
        E5[编排器Orchestrator]
        E6[情感对话Agent]
        E7[评审员Critic]
        E8[安全检查]
    end

    subgraph 记忆引擎 ["🧠 记忆引擎"]
        F1[短期记忆Redis]
        F2[长期记忆pgvector]
        F3[关系图谱Neo4j]
        F4[记忆检索RAG]
    end

    subgraph 异步处理层 ["🌙 异步处理层"]
        G1[消息队列]
        G2[记忆分析师]
        G3[反思Agent]
        G4[目标追踪器]
        G5[2.5D形象生成器]
    end

    %% 危机处理特殊路径 (最高优先级)
    C3 -->|检测到危机信号| H1[危机干预模板库]
    H1 -->|直接返回资源| C5
    C5 --> B5
    B5 --> A3

    %% 正常对话流程
    A1 --> B1
    B1 --> B2
    B2 --> B3
    B3 --> C1
    C1 --> C2
    C2 --> C3
    C3 -->|无危机信号| C4
    C4 --> D1

    %% 路由决策
    D1 --> D2
    D2 --> D3
    D3 --> D4

    %% 简单对话快速通道
    D4 -->|简单问候| E1
    E1 --> E4
    E4 -->|基础情绪识别| E6
    E6 --> E7
    E7 --> E8
    E8 --> C5

    %% 复杂对话智能通道
    D4 -->|复杂任务| E2
    E2 --> E4
    E4 -->|深度情绪分析| E5
    E5 -->|调用工具| F4
    F4 -->|检索记忆| F1
    F1 -->|查询长期记忆| F2
    F2 -->|关系图谱| F3
    F3 -->|记忆上下文| E5
    E5 -->|综合上下文| E6
    E6 -->|情绪自适应回复| E7
    E7 -->|内容质量检查| E8
    E8 -->|安全合规检查| C5

    %% VIP专属服务路径
    D4 -->|VIP功能| E3
    E3 -->|情感教练/亲密模式| E7
    E7 --> C5

    %% 响应返回和异步处理
    C5 --> B4
    B4 --> B5
    B5 --> A3
    A3 --> A4

    %% 2.5D形象触发
    A3 -->|触发形象生成| G5
    G5 -->|形象动画| B6
    B6 --> A4

    %% 异步记忆处理
    E6 -->|写入对话记录| G1
    G1 --> G2
    G1 --> G3
    G2 -->|记忆分析| F2
    G3 -->|质量评估| F4
    G4 -->|目标追踪| F3

    %% 用户继续对话
    A4 --> A5
    A5 -->|继续对话| A1
    A5 -->|结束对话| B7

    %% 样式定义
    classDef user fill:#e0f2fe,stroke:#0284c7,stroke-width:2px
    classDef client fill:#fef3c7,stroke:#f59e0b,stroke-width:2px
    classDef gateway fill:#ddd6fe,stroke:#7c3aed,stroke-width:2px
    classDef router fill:#d1fae5,stroke:#10b981,stroke-width:2px
    classDef sync fill:#fecaca,stroke:#dc2626,stroke-width:2px
    classDef memory fill:#fed7aa,stroke:#ea580c,stroke-width:2px
    classDef async fill:#fbcfe8,stroke:#ec4899,stroke-width:2px
    classDef crisis fill:#fca5a5,stroke:#b91c1c,stroke-width:3px

    class A1,A2,A3,A4,A5 user
    class B1,B2,B3,B4,B5,B6,B7 client
    class C1,C2,C3,C4,C5 gateway
    class D1,D2,D3,D4 router
    class E1,E2,E3,E4,E5,E6,E7,E8 sync
    class F1,F2,F3,F4 memory
    class G1,G2,G3,G4,G5 async
    class H1 crisis
```

### 角色问答模块流程说明

#### 1. 危机处理优先流程
- **最高优先级**: 检测到危机信号（自杀、自残等）直接返回干预资源
- **无需AI处理**: 直接调用危机干预模板库，跳过所有Agent
- **快速响应**: 500ms内返回帮助信息

#### 2. 智能路由决策
- **简单问候**: 基础情绪识别 + 小模型快速回复
- **复杂任务**: 深度情绪分析 + 记忆检索 + 编排器
- **VIP功能**: 情感教练、亲密模式等专属服务
- **复杂度评估**: 根据输入长度和意图选择处理路径

#### 3. 记忆系统协同
- **短期记忆**: 当前对话上下文（Redis）
- **长期记忆**: 用户偏好和历史事实（pgvector）
- **关系图谱**: 人物关系和事件时间线（Neo4j）
- **记忆检索**: RAG算法检索相关记忆

#### 4. 异步处理优化
- **实时响应**: 同步处理确保<1.5s响应时间
- **后台分析**: 异步进行记忆分析、质量评估
- **形象生成**: 独立线程处理2.5D形象动画

---

## 2.5D形象互动模块业务流

```mermaid
flowchart TD
    %% 泳道定义
    subgraph 用户层 ["👤 用户层"]
        A1[用户触发形象请求]
        A2[输入形象指令]
        A3[等待形象渲染]
        A4[查看形象动画]
        A5[与形象互动]
        A6[分享或保存]
    end

    subgraph 客户端层 ["📱 客户端层"]
        B1[形象展示界面]
        B2[指令输入框]
        B3[请求发送]
        B4[加载动画]
        B5[渲染形象]
        B6[播放动画]
        B7[互动响应]
    end

    subgraph API网关层 ["🚪 API网关层"]
        C1[VIP权限验证]
        C2[请求鉴权]
        C3[输入验证]
        C4[响应返回]
    end

    subgraph 智能路由层 ["🧭 智能路由层"]
        D1[形象请求识别]
        D2[意图解析]
        D3[VIP等级检查]
        D4[路由到形象Agent]
    end

    subgraph 形象Agent ["🎭 形象Agent"]
        E1[情绪解析]
        E2[意图识别]
        E3[表情映射]
        E4[动作选择]
        E5[动画序列生成]
    end

    subgraph 形象引擎 ["🎨 形象引擎"]
        F1[情绪-表情映射器]
        F2[动作模板库]
        F3[动画生成器]
        F4[渲染引擎]
        F5[同步服务]
    end

    subgraph 存储系统 ["💾 存储系统"]
        G1[模型存储MinIO]
        G2[动画缓存Redis]
        G3[材质贴图库]
        G4[CDN分发]
    end

    subgraph 优化服务 ["⚡ 优化服务"]
        H1[移动端适配]
        H2[性能优化]
        H3[预计算服务]
        H4[质量控制]
    end

    %% 主要流程
    A1 --> B1
    B1 --> A2
    A2 --> B2
    B2 --> B3
    B3 --> C1
    C1 --> C2
    C2 --> C3
    C3 --> D1

    %% 意图识别和路由
    D1 --> D2
    D2 --> D3
    D3 --> D4
    D4 --> E1

    %% 形象处理流程
    E1 -->|情绪分析| E2
    E2 -->|意图解析| E3
    E3 -->|表情映射| E4
    E4 -->|动作选择| E5
    E5 -->|动画序列| F1

    %% 引擎处理流程
    F1 -->|情绪映射| F2
    F2 -->|模板选择| F3
    F3 -->|动画生成| F4
    F4 -->|渲染处理| F5

    %% 存储和缓存
    F4 -->|获取模型| G1
    F4 -->|检查缓存| G2
    F4 -->|材质贴图| G3
    G1 -->|模型数据| F4
    G2 -->|缓存结果| F4
    G3 -->|贴图数据| F4

    %% 优化处理
    F4 -->|渲染优化| H1
    H1 -->|移动适配| H2
    H2 -->|性能优化| H3
    H3 -->|预计算| H4
    H4 -->|质量控制| F5

    %% 同步和响应
    F5 -->|同步服务| C4
    C4 --> B4
    B4 -->|显示加载| A3
    A3 --> B5
    B5 -->|渲染形象| B6
    B6 -->|播放动画| A4
    A4 --> A5
    A5 --> B7
    B7 --> A6

    %% 缓存优化路径
    F3 -->|热门动画| G2
    G2 -->|快速返回| C4
    C4 --> B5

    %% CDN分发路径
    F4 -->|渲染结果| G4
    G4 -->|全球分发| B6

    %% 样式定义
    classDef user fill:#e0f2fe,stroke:#0284c7,stroke-width:2px
    classDef client fill:#fef3c7,stroke:#f59e0b,stroke-width:2px
    classDef gateway fill:#ddd6fe,stroke:#7c3aed,stroke-width:2px
    classDef router fill:#d1fae5,stroke:#10b981,stroke-width:2px
    classDef agent fill:#fecaca,stroke:#dc2626,stroke-width:2px
    classDef engine fill:#fed7aa,stroke:#ea580c,stroke-width:2px
    classDef storage fill:#f0abfc,stroke:#a21caf,stroke-width:2px
    classDef optimize fill:#d1fae5,stroke:#10b981,stroke-width:2px

    class A1,A2,A3,A4,A5,A6 user
    class B1,B2,B3,B4,B5,B6,B7 client
    class C1,C2,C3,C4 gateway
    class D1,D2,D3,D4 router
    class E1,E2,E3,E4,E5 agent
    class F1,F2,F3,F4,F5 engine
    class G1,G2,G3,G4 storage
    class H1,H2,H3,H4 optimize
```

### 2.5D形象互动模块流程说明

#### 1. 形象请求处理
- **VIP权限验证**: 检查用户是否有2.5D形象权限
- **意图识别**: 解析用户的具体请求（表情、动作、表演）
- **情绪映射**: 将对话情绪转换为形象表情

#### 2. 表情动作映射
- **情绪分析**: 分析对话中的情绪色彩和强度
- **表情选择**: 根据情绪选择对应的面部表情
- **动作匹配**: 选择与情绪和意图匹配的动作
- **动画序列**: 生成流畅的动画过渡序列

#### 3. 渲染优化
- **移动端适配**: 针对移动设备进行性能优化
- **GPU加速**: 利用硬件加速提升渲染性能
- **缓存策略**: 热门动画预计算和缓存
- **质量控制**: 确保动画质量和流畅度

#### 4. 存储分发
- **模型存储**: MinIO存储3D模型和材质
- **动画缓存**: Redis缓存热门动画内容
- **CDN分发**: 全球CDN加速动画加载
- **实时同步**: 确保动画与对话内容同步

---

## 照片建模VIP服务业务流

```mermaid
flowchart TD
    %% 泳道定义
    subgraph 用户层 ["👤 VIP用户层"]
        A1[用户选择照片建模]
        A2[准备照片/视频]
        A3[上传文件]
        A4[等待建模]
        A5[查看预览]
        A6[选择风格]
        A7[确认建模]
        A8[获取最终模型]
    end

    subgraph 客户端层 ["📱 客户端层"]
        B1[建模界面]
        B2[文件选择器]
        B3[上传进度]
        B4[质量检测]
        B5[建模进度]
        B6[预览展示]
        B7[风格选择器]
        B8[结果展示]
    end

    subgraph API网关层 ["🚪 API网关层"]
        C1[VIP高级权限验证]
        C2[文件安全检查]
        C3[请求鉴权]
        C4[使用次数检查]
        C5[响应返回]
    end

    subgraph 照片建模Agent ["📸 照片建模Agent"]
        D1[输入验证]
        D2[质量检查]
        D3[人脸特征提取]
        D4[AI模型生成]
        D5[风格化处理]
        D6[模型优化]
        D7[质量评估]
        D8[预览生成]
    end

    subgraph AI建模服务 ["🧠 AI建模服务"]
        E1[人脸识别服务]
        E2[特征点提取]
        E3[3D模型生成]
        E4[风格化引擎]
        E5[材质贴图处理]
    end

    subgraph 模型存储 ["💾 模型存储系统"]
        F1[原始文件存储]
        F2[特征数据存储]
        F3[3D模型存储MinIO]
        F4[预览图存储]
        F5[CDN分发]
    end

    subgraph 质量控制 ["🔍 质量控制系统"]
        G1[图片质量评估]
        G2[人脸相似度评估]
        G3[模型质量检查]
        G4[渲染性能测试]
        G5[用户反馈收集]
    end

    %% 主要流程
    A1 --> B1
    B1 --> A2
    A2 --> B2
    B2 --> A3
    A3 --> B3
    B3 --> C1

    %% 权限和安全检查
    C1 -->|VIP高级验证| C4
    C4 -->|使用次数| C2
    C2 -->|文件安全| C3
    C3 --> D1

    %% 输入验证和质量检查
    D1 -->|数量格式验证| D2
    D2 -->|质量检查| B4
    B4 -->|质量提示| A2
    D2 -->|通过验证| D3

    %% 人脸特征提取
    D3 -->|调用AI服务| E1
    E1 -->|人脸检测| E2
    E2 -->|特征点| D4
    D4 -->|存储特征| F2

    %% AI模型生成
    D4 -->|特征数据| E3
    E3 -->|3D模型| D5
    D5 -->|风格处理| E4
    E4 -->|材质处理| E5

    %% 模型存储和质量控制
    D5 -->|原始模型| F3
    E5 -->|风格化模型| F3
    D6 -->|优化后模型| F3
    F3 -->|模型数据| G3
    G3 -->|质量检查| D7

    %% 质量评估流程
    D2 -->|质量数据| G1
    D3 -->|特征数据| G2
    D6 -->|优化模型| G4
    G1 -->|质量分数| D7
    G2 -->|相似度| D7
    G4 -->|性能数据| D7
    D7 -->|综合评估| D8

    %% 预览生成和用户确认
    D8 -->|生成预览| F4
    F4 -->|预览图| C5
    C5 --> B5
    B5 -->|建模进度| A4
    A4 --> B6
    B6 -->|360度预览| A5
    A5 --> A6
    A6 --> B7
    B7 -->|风格选项| A7
    A7 -->|确认建模| D8
    D8 -->|最终模型| F1
    F1 -->|存储模型| F5
    F5 -->|CDN分发| B8
    B8 -->|最终结果| A8

    %% 用户反馈循环
    A8 --> G5
    G5 -->|反馈数据| D6
    D6 -->|模型优化| D8

    %% 缓存和CDN优化
    F4 -->|预览缓存| C5
    F5 -->|模型缓存| F5
    F5 -->|快速加载| B8

    %% 样式定义
    classDef user fill:#e0f2fe,stroke:#0284c7,stroke-width:2px
    classDef client fill:#fef3c7,stroke:#f59e0b,stroke-width:2px
    classDef gateway fill:#ddd6fe,stroke:#7c3aed,stroke-width:2px
    classDef agent fill:#fecaca,stroke:#dc2626,stroke-width:2px
    classDef ai fill:#fed7aa,stroke:#ea580c,stroke-width:2px
    classDef storage fill:#f0abfc,stroke:#a21caf,stroke-width:2px
    classDef quality fill:#d1fae5,stroke:#10b981,stroke-width:2px

    class A1,A2,A3,A4,A5,A6,A7,A8 user
    class B1,B2,B3,B4,B5,B6,B7,B8 client
    class C1,C2,C3,C4,C5 gateway
    class D1,D2,D3,D4,D5,D6,D7,D8 agent
    class E1,E2,E3,E4,E5 ai
    class F1,F2,F3,F4,F5 storage
    class G1,G2,G3,G4,G5 quality
```

### 照片建模VIP服务业务流说明

#### 1. VIP权限和使用管理
- **VIP高级权限验证**: 确保用户有照片建模权限
- **使用次数检查**: 检查月度使用次数限制
- **文件安全检查**: 确保上传内容合规安全

#### 2. 输入处理和质量控制
- **文件数量验证**: 3-5张照片或1-2个视频
- **图片质量评估**: 清晰度、角度、光线分析
- **实时反馈**: 向用户提供具体的质量改进建议

#### 3. AI建模处理流程
- **人脸特征提取**: 多角度特征点提取和融合
- **3D模型生成**: 基于特征的AI模型生成
- **风格化处理**: 卡通化、美颜等风格处理
- **材质贴图**: 皮肤、头发、服装材质处理

#### 4. 质量评估系统
- **人脸相似度**: 与原始照片的相似度评估（>80%）
- **模型质量**: 面数、拓扑结构质量检查
- **渲染性能**: 移动端渲染性能测试
- **综合评分**: 多维度质量综合评分

#### 5. 用户体验优化
- **实时进度**: 建模各阶段的进度反馈
- **360度预览**: 多角度模型预览
- **风格选择**: 多种风格化选项
- **快速加载**: CDN加速和缓存优化

---

## 新用户引导模块业务流

```mermaid
flowchart TD
    %% 泳道定义
    subgraph 新用户层 ["🆕 新用户层"]
        A1[首次打开应用]
        A2[进入引导流程]
        A3[与萌教官互动]
        A4[学习功能介绍]
        A5[创建首个角色]
        A6[完成首次对话]
        A7[完成引导]
        A8[开始使用应用]
    end

    subgraph 客户端层 ["📱 客户端层"]
        B1[启动界面]
        B2[引导界面]
        B3[NPC对话界面]
        B4[功能演示界面]
        B5[角色创建引导]
        B6[对话引导]
        B7[完成界面]
        B8[主界面]
    end

    subgraph API网关层 ["🚪 API网关层"]
        C1[新用户识别]
        C2[引导状态检查]
        C3[请求路由]
        C4[状态更新]
        C5[引导记录]
    end

    subgraph 智能路由层 ["🧭 智能路由层"]
        D1[新用户检测]
        D2[引导触发]
        D3[步骤路由]
        D4[进度管理]
    end

    subgraph 引导系统 ["🎓 新用户引导系统"]
        E1[萌教官NPC]
        E2[引导流程管理器]
        E3[进度追踪器]
        E4[欢迎向导]
        E5[功能介绍器]
    end

    subgraph 业务服务层 ["⚙️ 业务服务层"]
        F1[角色创建服务]
        F2[对话服务]
        F3[用户管理服务]
        F4[配置服务]
    end

    subgraph 存储层 ["💾 存储层"]
        G1[引导状态数据库]
        G2[用户数据库]
        G3[进度缓存Redis]
        G4[配置缓存]
    end

    %% 主要流程
    A1 --> B1
    B1 --> C1
    C1 -->|检测新用户| D1
    D1 -->|触发引导| D2
    D2 --> C2
    C2 -->|未完成引导| A2
    A2 --> B2

    %% 引导启动
    B2 --> E4
    E4 -->|欢迎向导| E1
    E1 -->|萌教官欢迎| B3
    B3 --> A3
    A3 --> C3
    C3 --> D3
    D3 --> E2

    %% 引导步骤管理
    E2 -->|当前步骤| E3
    E3 -->|进度检查| G3
    G3 -->|进度数据| E2
    E2 -->|步骤控制| E5

    %% 功能介绍步骤
    E5 -->|角色创建介绍| B4
    B4 -->|功能演示| A4
    A4 -->|功能学习| C4
    C4 -->|状态更新| G1

    %% 角色创建引导
    E5 -->|角色创建引导| B5
    B5 -->|引导创建| A5
    A5 -->|创建首个角色| F1
    F1 -->|角色数据| G2
    F1 -->|创建成功| E3
    E3 -->|进度更新| C4

    %% 首次对话引导
    E3 -->|进入对话引导| B6
    B6 -->|对话引导| A6
    A6 -->|首次对话| F2
    F2 -->|对话记录| G2
    F2 -->|对话成功| E3
    E3 -->|完成引导检查| D4

    %% 引导完成
    D4 -->|所有步骤完成| A7
    A7 --> B7
    B7 -->|完成界面| E4
    E4 -->|引导总结| C5
    C5 -->|记录完成| G1
    G1 -->|更新用户状态| G2
    G2 -->|用户已激活| B8
    B8 --> A8

    %% 可跳过步骤处理
    A4 -->|跳过介绍| E2
    E2 -->|进入下一步| E5
    A5 -->|跳过创建| E2
    E2 -->|检查必需步骤| E3
    E3 -->|必需完成| B6

    %% 引导中断和恢复
    A3 -->|中途退出| C5
    C5 -->|保存进度| G1
    G1 -->|下次启动| D1
    D1 -->|恢复引导| D2

    %% 个性化引导
    E1 -->|用户反馈分析| E4
    E4 -->|个性化调整| E5
    E5 -->|定制引导内容| B3

    %% 样式定义
    classDef user fill:#e0f2fe,stroke:#0284c7,stroke-width:2px
    classDef client fill:#fef3c7,stroke:#f59e0b,stroke-width:2px
    classDef gateway fill:#ddd6fe,stroke:#7c3aed,stroke-width:2px
    classDef router fill:#d1fae5,stroke:#10b981,stroke-width:2px
    classDef onboard fill:#fecaca,stroke:#dc2626,stroke-width:2px
    classDef service fill:#fed7aa,stroke:#ea580c,stroke-width:2px
    classDef storage fill:#f0abfc,stroke:#a21caf,stroke-width:2px

    class A1,A2,A3,A4,A5,A6,A7,A8 user
    class B1,B2,B3,B4,B5,B6,B7,B8 client
    class C1,C2,C3,C4,C5 gateway
    class D1,D2,D3,D4 router
    class E1,E2,E3,E4,E5 onboard
    class F1,F2,F3,F4 service
    class G1,G2,G3,G4 storage
```

### 新用户引导模块业务流说明

#### 1. 新用户检测和引导触发
- **自动识别**: 首次启动应用自动检测新用户
- **引导状态管理**: 跟踪用户引导进度和中断状态
- **恢复机制**: 支持引导中断后从断点恢复

#### 2. 萌教官NPC交互
- **人格化引导**: ESFJ温柔体贴型人格配置
- **分步教学**: 7个引导步骤的渐进式教学
- **互动式学习**: 用户可以随时提问和重复说明

#### 3. 引导步骤管理
- **必需步骤**: 角色创建、首次对话等必须完成的步骤
- **可选步骤**: 功能介绍、VIP功能等可跳过的步骤
- **智能跳转**: 根据用户兴趣和反馈调整引导路径

#### 4. 功能演示和体验
- **角色创建演示**: 展示基础模板和VIP照片建模
- **2.5D形象展示**: 演示虚拟形象的表情和动作
- **首次对话引导**: 指导用户进行第一次AI对话

#### 5. 进度跟踪和个性化
- **实时进度**: Redis缓存引导进度状态
- **个性化调整**: 根据用户反馈调整引导内容
- **完成奖励**: 引导完成后的庆祝和鼓励

---

## 记忆管理模块业务流

```mermaid
flowchart TD
    %% 泳道定义
    subgraph 用户层 ["👤 用户层"]
        A1[用户与AI对话]
        A2[提及信息/事实]
        A3[询问记忆内容]
        A4[纠错记忆]
        A5[查看记忆管理]
        A6[导出记忆数据]
    end

    subgraph 客户端层 ["📱 客户端层"]
        B1[对话界面]
        B2[记忆纠错界面]
        B3[记忆管理界面]
        B4[数据导出界面]
        B5[同步状态显示]
    end

    subgraph API网关层 ["🚪 API网关层"]
        C1[对话请求处理]
        C2[记忆操作请求]
        C3[权限验证]
        C4[请求路由]
    end

    subgraph 同步记忆处理 ["⚡ 同步记忆处理"]
        D1[短期记忆Redis]
        D2[快速检索]
        D3[上下文管理]
        D4[记忆写入]
    end

    subgraph 异步记忆处理 ["🌙 异步记忆处理"]
        E1[消息队列]
        E2[记忆分析师]
        E3[反思Agent]
        E4[纠错处理器]
        E5[目标追踪器]
    end

    subgraph 长期记忆系统 ["📚 长期记忆系统"]
        F1[pgvector数据库]
        F2[RAG检索引擎]
        F3[向量化存储]
        F4[语义搜索]
    end

    subgraph 关系图谱系统 ["🕸️ 关系图谱系统"]
        G1[Neo4j数据库]
        G2[实体关系抽取]
        G3[时间线构建]
        G4[图谱查询]
    end

    subgraph 形象记忆系统 ["🎭 形象记忆系统"]
        H1[MinIO存储]
        H2[2.5D模型数据]
        H3[表情动画库]
        H4[形象关联]
    end

    %% 对话记忆流程
    A1 --> B1
    B1 --> C1
    C1 --> C3
    C3 --> D1
    D1 -->|当前上下文| D2
    D2 -->|相关记忆检索| D3
    D3 -->|上下文+记忆| C1
    C1 -->|增强回复| B1
    B1 --> A2

    %% 记忆写入流程
    A2 -->|对话内容| C1
    C1 -->|提取记忆| D4
    D4 -->|写入短期| D1
    D4 -->|异步处理| E1
    E1 --> E2
    E1 --> E3
    E2 -->|对话分析| F1
    E3 -->|质量检查| F1

    %% 长期记忆处理
    E2 -->|关键信息| F3
    F3 -->|向量化| F1
    F1 -->|存储事实| F2
    F2 -->|RAG检索| F4
    F4 -->|语义搜索| D2

    %% 关系图谱构建
    E2 -->|实体关系| G2
    G2 -->|关系抽取| G1
    G1 -->|图谱存储| G3
    G3 -->|时间线| G4
    G4 -->|关系查询| D2

    %% 形象记忆关联
    E2 -->|形象信息| H4
    H4 -->|形象关联| H1
    H1 -->|模型存储| H2
    H2 -->|动画数据| H3
    H3 -->|形象检索| D2

    %% 记忆查询和纠错
    A3 -->|询问记忆| B1
    B1 --> C2
    C2 -->|记忆查询| C4
    C4 -->|检索请求| D2
    D2 -->|多源检索| F4
    D2 -->|图谱查询| G4
    D2 -->|形象查询| H3
    F4 -->|语义结果| C2
    G4 -->|关系结果| C2
    H3 -->|形象结果| C2
    C2 -->|综合结果| B1
    B1 --> A3

    %% 记忆纠错流程
    A4 --> B2
    B2 -->|纠错请求| C2
    C2 -->|纠错操作| E4
    E4 -->|污染检测| F1
    E4 -->|数据修正| G1
    E4 -->|记忆重建| D1
    E4 -->|验证结果| B2
    B2 --> A4

    %% 记忆管理界面
    A5 --> B3
    B3 -->|管理请求| C2
    C2 -->|数据查询| F1
    C2 -->|图谱查询| G1
    C2 -->|形象查询| H1
    F1 -->|记忆统计| B3
    G1 -->|关系图谱| B3
    H1 -->|形象数据| B3
    B3 --> A5

    %% 数据导出
    A6 --> B4
    B4 -->|导出请求| C2
    C2 -->|数据聚合| F1
    F1 -->|格式化输出| B4
    B4 -->|下载文件| A6

    %% 同步状态显示
    D1 -->|记忆同步状态| B5
    F1 -->|长期记忆状态| B5
    G1 -->|图谱状态| B5
    B5 --> A1

    %% 样式定义
    classDef user fill:#e0f2fe,stroke:#0284c7,stroke-width:2px
    classDef client fill:#fef3c7,stroke:#f59e0b,stroke-width:2px
    classDef gateway fill:#ddd6fe,stroke:#7c3aed,stroke-width:2px
    classDef sync fill:#d1fae5,stroke:#10b981,stroke-width:2px
    classDef async fill:#fbcfe8,stroke:#ec4899,stroke-width:2px
    classDef longterm fill:#fed7aa,stroke:#ea580c,stroke-width:2px
    classDef graphdb fill:#fecaca,stroke:#dc2626,stroke-width:2px
    classDef avatar fill:#f0abfc,stroke:#a21caf,stroke-width:2px

    class A1,A2,A3,A4,A5,A6 user
    class B1,B2,B3,B4,B5 client
    class C1,C2,C3,C4 gateway
    class D1,D2,D3,D4 sync
    class E1,E2,E3,E4,E5 async
    class F1,F2,F3,F4 longterm
    class G1,G2,G3,G4 graphdb
    class H1,H2,H3,H4 avatar
```

### 记忆管理模块业务流说明

#### 1. 四层记忆架构
- **短期记忆**: 当前对话上下文（Redis，24小时）
- **长期记忆**: 事实、偏好、历史记录（pgvector）
- **关系图谱**: 人物关系、事件时间线（Neo4j）
- **形象记忆**: 2.5D模型、表情动画（MinIO）

#### 2. 实时记忆处理
- **同步检索**: 对话时实时检索相关记忆
- **上下文管理**: 维护当前对话的上下文
- **快速响应**: 缓存热点记忆数据
- **记忆写入**: 实时写入新的对话内容

#### 3. 异步记忆分析
- **对话总结**: 提取关键信息和事实
- **知识图谱构建**: 自动构建人物关系图谱
- **质量评估**: 检查记忆的一致性和准确性
- **目标追踪**: 追踪用户的长期目标和偏好

#### 4. 记忆检索系统
- **RAG检索**: 基于向量相似度的语义检索
- **图谱查询**: 基于关系网络的复杂查询
- **多源融合**: 整合多个记忆源的信息
- **个性化排序**: 基于用户偏好的结果排序

#### 5. 记忆纠错机制
- **污染检测**: 检测和识别错误或污染的记忆
- **数据修正**: 修正或删除不准确的信息
- **记忆重建**: 重新组织和优化记忆结构
- **用户验证**: 纠错结果需要用户确认

---

## VIP功能升级模块业务流

```mermaid
flowchart TD
    %% 泳道定义
    subgraph 用户层 ["👤 用户层"]
        A1[用户使用应用]
        A2[触发VIP功能]
        A3[收到升级提示]
        A4[查看升级选项]
        A5[选择升级套餐]
        A6[完成支付]
        A7[享受VIP功能]
        A8[管理订阅]
    end

    subgraph 客户端层 ["📱 客户端层"]
        B1[功能限制提示]
        B2[升级推荐界面]
        B3[套餐选择界面]
        B4[支付界面]
        B5[升级成功界面]
        B6[订阅管理界面]
    end

    subgraph API网关层 ["🚪 API网关层"]
        C1[权限检查中间件]
        C2[升级触发检测]
        C3[支付API集成]
        C4[VIP状态同步]
        C5[权限更新通知]
    end

    subgraph 智能升级系统 ["🧠 智能升级系统"]
        D1[行为追踪器]
        D2[升级触发分析]
        D3[个性化推荐器]
        D4[转化漏斗分析]
        D5[A/B测试管理]
    end

    subgraph VIP权限系统 ["👑 VIP权限系统"]
        E1[权限定义引擎]
        E2[使用次数管理]
        E3[功能解锁控制]
        E4[等级验证服务]
        E5[权限缓存Redis]
    end

    subgraph 支付系统 ["💳 支付系统"]
        F1[支付网关集成]
        F2[订阅管理]
        F3[退款处理]
        F4[发票管理]
        F5[优惠码系统]
    end

    subgraph 运营系统 ["📊 运营系统"]
        G1[用户行为分析]
        G2[收入统计]
        G3[转化率分析]
        G4[客服工单系统]
        G5[营销活动管理]
    end

    %% 功能限制和升级触发
    A1 -->|尝试VIP功能| A2
    A2 --> B1
    B1 -->|权限检查| C1
    C1 -->|权限不足| C2
    C2 -->|触发分析| D1
    D1 -->|行为数据| D2
    D2 -->|升级判断| C2
    C2 -->|显示升级提示| A3
    A3 --> B2

    %% 个性化推荐
    B2 --> D3
    D3 -->|个性化推荐| B3
    B3 --> A4
    A4 --> A5
    A5 --> B4

    %% 支付处理
    B4 --> C3
    C3 -->|支付请求| F1
    F1 -->|支付处理| F2
    F2 -->|订阅创建| F3
    F3 -->|支付成功| C3
    C3 -->|同步VIP状态| C4
    C4 -->|权限更新| C5
    C5 -->|通知客户端| B5
    B5 --> A7
    A7 -->|享受VIP功能| A1

    %% 权限系统
    C5 --> E4
    E4 -->|权限验证| E1
    E1 -->|权限定义| E3
    E3 -->|功能解锁| E2
    E2 -->|使用次数| E5
    E5 -->|权限缓存| C1
    C1 -->|权限检查通过| A1

    %% 订阅管理
    A8 --> B6
    B6 -->|管理请求| C4
    C4 -->|订阅查询| F2
    F2 -->|订阅信息| B6
    B6 -->|变更请求| F3
    F3 -->|处理变更| C4
    C4 -->|状态同步| E4

    %% 运营分析
    D1 -->|行为数据| G1
    D2 -->|转化数据| G3
    F1 -->|收入数据| G2
    G1 -->|用户洞察| D3
    G2 -->|收入分析| D4
    G3 -->|转化优化| D5

    %% A/B测试
    D5 -->|测试配置| B2
    D5 -->|测试配置| B3
    D5 -->|测试配置| B4
    B2 -->|测试数据| G3
    B3 -->|测试数据| G3
    B4 -->|测试数据| G3
    G3 -->|测试结果| D4

    %% 客服支持
    A8 -->|客服需求| G4
    G4 -->|工单处理| F3
    F3 -->|问题解决| G4
    G4 -->|用户通知| B6

    %% 营销活动
    G5 -->|优惠活动| F5
    F5 -->|优惠码| B3
    B3 -->|使用优惠| F1
    F1 -->|优惠验证| F5

    %% 样式定义
    classDef user fill:#e0f2fe,stroke:#0284c7,stroke-width:2px
    classDef client fill:#fef3c7,stroke:#f59e0b,stroke-width:2px
    classDef gateway fill:#ddd6fe,stroke:#7c3aed,stroke-width:2px
    classDef smart fill:#d1fae5,stroke:#10b981,stroke-width:2px
    classDef vip fill:#fecaca,stroke:#dc2626,stroke-width:2px
    classDef payment fill:#fed7aa,stroke:#ea580c,stroke-width:2px
    classDef ops fill:#f0abfc,stroke:#a21caf,stroke-width:2px

    class A1,A2,A3,A4,A5,A6,A7,A8 user
    class B1,B2,B3,B4,B5,B6 client
    class C1,C2,C3,C4,C5 gateway
    class D1,D2,D3,D4,D5 smart
    class E1,E2,E3,E4,E5 vip
    class F1,F2,F3,F4,F5 payment
    class G1,G2,G3,G4,G5 ops
```

### VIP功能升级模块业务流说明

#### 1. 智能升级触发系统
- **行为追踪**: 监控用户使用VIP功能的行为模式
- **触发分析**: 识别最佳升级推荐时机
- **个性化推荐**: 基于用户行为的个性化套餐推荐
- **转化优化**: 通过A/B测试优化转化率

#### 2. VIP权限管理
- **四层等级体系**: 免费版、VIP基础、VIP高级、VIP至尊
- **权限定义引擎**: 灵活的权限配置和功能解锁
- **使用次数管理**: 精确控制各功能的使用次数
- **实时权限缓存**: Redis缓存确保权限检查性能

#### 3. 支付订阅系统
- **多支付方式**: 集成主流支付网关
- **订阅管理**: 支持月付、年付、升级、降级
- **自动续费**: 智能续费提醒和处理
- **退款处理**: 自动化退款审批流程

#### 4. 运营数据分析
- **转化漏斗分析**: 从功能限制到支付成功的全链路分析
- **用户行为洞察**: 深度分析用户使用模式
- **收入统计**: 实时收入数据和趋势分析
- **ROI评估**: 营销活动和功能开发的投资回报率

#### 5. 客服和支持体系
- **智能客服**: 基于常见问题的自动回复
- **工单系统**: VIP用户的优先支持通道
- **问题追踪**: 完整的问题处理流程记录
- **用户反馈**: 收集和分类用户反馈建议

---

## 业务流设计总结

### 核心设计原则

1. **用户体验优先**
   - 实时响应：同步处理确保<1.5s响应时间
   - 渐进引导：新用户7步引导，降低学习成本
   - 智能推荐：基于行为的个性化VIP推荐

2. **技术架构清晰**
   - 分层设计：用户层→客户端→网关→路由→服务→存储
   - 权限控制：VIP权限中间件统一管理功能访问
   - 异步优化：后台处理提升用户体验

3. **商业化精细化**
   - 四层VIP体系：免费→基础($9.9)→高级($19.9)→至尊($39.9)
   - 差异化功能：2.5D形象、照片建模、160性格等核心卖点
   - 智能升级：基于用户行为的精准升级推荐

4. **数据驱动运营**
   - 全链路追踪：从用户行为到转化的完整数据采集
   - A/B测试：持续优化界面文案和推荐策略
   - ROI分析：量化每个功能的商业价值

### 关键性能指标

- **响应时间**: 对话<1.5s，形象生成<800ms，照片建模<5s
- **转化率目标**: 免费→VIP基础12%，基础→高级5%，高级→至尊2%
- **用户留存**: 新用户引导完成率>80%，7日留存>60%
- **系统可用性**: 99.9%可用性，数据持久性99.999%

### 下一步实施建议

1. **Phase 1 (Week 1-6)**: 核心功能开发
   - 角色创建和问答模块
   - 基础2.5D形象系统
   - 新用户引导流程

2. **Phase 2 (Week 7-12)**: VIP功能完善
   - 照片建模系统
   - 160种性格引擎
   - 商业化支付系统

3. **Phase 3 (Week 13-18)**: 优化和扩展
   - 性能优化和稳定性提升
   - 高级VIP功能开发
   - 数据分析和运营工具

---

*文档版本: V3.0 | 最后更新: 2025/11/19 | 基于架构设计文档 V3.0*