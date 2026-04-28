# 无人机网络安全防御系统 - 项目介绍
# Drone Security Defense System - Project Introduction

## 项目概述

### 项目背景

随着无人机技术的快速发展，无人机面临的网络安全威胁日益严峻。攻击者可以通过通信劫持、GPS欺骗、传感器数据篡改等方式非法控制无人机，造成严重的安全隐患。本项目旨在构建一个全面的无人机网络安全防御系统。

### 项目定位

无人机网络安全防御系统是一个**跨平台、模块化、可扩展**的无人机安全防护解决方案，可作为独立守护进程运行，提供实时的网络安全监控和防护能力。

### 核心价值主张

- **全面防护**: 覆盖通信、导航、传感器、固件等多个攻击面
- **实时响应**: 毫秒级威胁检测与告警
- **可视化管理**: Web界面提供直观的态势感知
- **灵活部署**: 支持Linux、Android、嵌入式Linux等多种平台
- **低资源消耗**: 优化的资源配置，适配边缘计算场景

---

## 系统架构

### 整体架构图

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           SecurityDaemon (守护进程核心)                     │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐ │
│  │Detector  │──▶│Analyzer  │──▶│ Handler  │──▶│WebBridge │──▶│WebServer │ │
│  │(检测器)  │   │(分析器)  │   │(处理器)  │   │(桥接层)  │   │(API服务)│ │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘ │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                            ┌───────────────┐
                            │  EventBus     │
                            │  (事件总线)    │
                            └───────────────┘
                                    │
        ┌───────────┬───────────┬───┴────┬────────┬────────┬────────┐
        ▼           ▼           ▼        ▼        ▼        ▼        ▼
   ┌────────┐ ┌────────┐ ┌────────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
   │MAVLink │ │  GPS   │ │Sensor  │ │ DoS  │ │Firm- │ │Alert │ │Log   │
   │Interface││Interface││Interface││Det.  │ │ware  │ │Hand. │ │Hand. │
   └────────┘ └────────┘ └────────┘ └──────┘ └──────┘ └──────┘ └──────┘
```

### 数据流架构

```
外部数据源 → 数据接口层 → 检测器 → 分析器 → 事件总线 → 处理器 → 响应动作
                                            │
                                            ▼
                                      Web实时推送
```

---

## 技术栈

### 后端技术栈

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **运行时** | Python | 3.8+ | 核心开发语言 |
| **Web框架** | FastAPI | 0.104+ | RESTful API服务 |
| **实时通信** | Websockets | 12.0+ | WebSocket服务 |
| **异步框架** | Uvicorn | 0.24+ | ASGI服务器 |
| **无人机协议** | PyMAVLink | 2.4.0+ | MAVLink协议解析 |
| **数据处理** | NumPy / Pandas | 1.24+/2.0+ | 数据分析处理 |
| **机器学习** | Scikit-learn | 1.3.0+ | 异常检测模型 |
| **网络安全** | Scapy | 2.5.0+ | 网络包分析 |
| **加密** | PyCryptodome | 3.19+ | 加密解密功能 |
| **日志** | Colorlog | 6.8+ | 彩色日志输出 |
| **系统监控** | psutil | 5.9+ | 系统资源监控 |

### 前端技术栈

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **框架** | React | 18.2+ | UI框架 |
| **语言** | TypeScript | 5.2+ | 类型安全开发 |
| **构建工具** | Vite | 5.0+ | 快速构建 |
| **路由** | React Router | 6.20+ | 前端路由 |
| **状态管理** | Zustand | 4.4+ | 轻量级状态管理 |
| **数据获取** | TanStack Query | 5.12+ | 服务端状态管理 |
| **图表库** | ECharts | 5.4+ | 数据可视化 |
| **地图** | Leaflet | 1.9+ | 地图展示 |
| **样式** | TailwindCSS | 3.3+ | 原子化CSS |
| **HTTP客户端** | Axios | 1.6+ | API请求 |

---

## 核心功能模块

### 1. 检测器模块 (Detectors)

检测器是系统的第一道防线，负责实时监控各种数据源并识别潜在威胁。

#### MAVLink检测器 (`mavlink_detector.py`)

**检测能力**:
- 消息序列号异常检测（防重放攻击）
- 系统/组件ID变更检测（防劫持攻击）
- 异常命令模式识别（防命令注入）
- 消息频率异常检测（防中间人攻击）

**关键配置**:
```yaml
detectors:
  mavlink:
    enabled: true
    interval: 0.1  # 检测间隔(秒)
    settings:
      max_message_gap: 10
      allowed_system_ids: [1, 255]
      allowed_component_ids: [1, 50, 190, 191, 192]
```

#### GPS检测器 (`gps_detector.py`)

**检测能力**:
- 位置跳变检测（检测GPS欺骗）
- 速度约束验证（检测异常运动）
- 信号质量检查（检测信号干扰）
- 多源位置交叉验证

**关键配置**:
```yaml
detectors:
  gps:
    enabled: true
    interval: 0.5
    settings:
      max_jump_distance: 1000  # 米
      max_acceleration: 10.0   # m/s²
      min_satellites: 6
```

#### 传感器检测器 (`sensor_detector.py`)

**检测能力**:
- 数据范围验证（检测异常值）
- 传感器间一致性检查（检测数据篡改）
- 噪声模式分析（检测欺骗信号）

#### DoS检测器 (`dos_detector.py`)

**检测能力**:
- 连接频率监控
- 请求速率限制
- 资源使用异常检测

### 2. 分析器模块 (Analyzers)

分析器对检测器输出进行深度分析，提高检测准确性。

#### 统计分析器 (`statistical_analyzer.py`)

使用Z-score和IQR方法进行异常值检测，识别统计显著偏差。

#### 关联分析器 (`correlation_analyzer.py`)

分析多源数据的时间关联性，识别复合攻击模式。

#### 机器学习分析器 (`ml_analyzer.py`)

基于历史数据训练的异常检测模型（可选模块）。

### 3. 处理器模块 (Handlers)

处理器负责对检测到的威胁进行响应。

- **AlertHandler**: 告警生成和管理
- **LogHandler**: 安全事件日志记录
- **BlockHandler**: 自动阻断（谨慎使用）
- **CloudHandler**: 云端威胁情报同步

### 4. Web界面模块

提供可视化的监控和管理界面。

#### 功能特性

- **态势感知仪表盘**: 实时系统状态、威胁概览
- **告警管理**: 查看、确认、解决告警
- **威胁分析**: 时间线、类型分布、严重程度统计
- **检测器控制**: 实时启停控制
- **统计分析**: 多维度数据统计和图表展示

---

## 项目结构

```
drone_security_defense/
├── src/
│   ├── core/                      # 核心模块
│   │   ├── daemon.py              # 守护进程主类
│   │   ├── event_bus.py           # 事件总线
│   │   ├── config_manager.py      # 配置管理器
│   │   ├── platform_detector.py   # 平台检测器
│   │   └── web_bridge.py          # Web服务器桥接
│   │
│   ├── web/                       # Web服务器模块
│   │   ├── server.py              # FastAPI服务器
│   │   ├── app.py                 # FastAPI应用配置
│   │   ├── routers/               # API路由
│   │   │   ├── system.py          # 系统状态API
│   │   │   ├── alerts.py          # 告警管理API
│   │   │   ├── threats.py         # 威胁事件API
│   │   │   ├── detectors.py       # 检测器控制API
│   │   │   └── statistics.py      # 统计数据API
│   │   ├── websocket/             # WebSocket模块
│   │   │   ├── manager.py         # 连接管理器
│   │   │   └── broadcaster.py     # 实时广播器
│   │   ├── services/              # 业务服务
│   │   │   ├── data_service.py    # 数据服务
│   │   │   └── alert_service.py   # 告警服务
│   │   └── models/                # 数据模型
│   │
│   ├── frontend/                  # 前端项目
│   │   ├── src/
│   │   │   ├── api/               # API客户端
│   │   │   ├── components/        # React组件
│   │   │   ├── hooks/             # React Hooks
│   │   │   ├── pages/             # 页面组件
│   │   │   └── types/             # TypeScript类型
│   │   ├── package.json
│   │   └── vite.config.ts
│   │
│   ├── detectors/                 # 检测器
│   │   ├── base_detector.py       # 检测器基类
│   │   ├── mavlink_detector.py    # MAVLink检测器
│   │   ├── gps_detector.py        # GPS检测器
│   │   ├── sensor_detector.py     # 传感器检测器
│   │   ├── dos_detector.py        # DoS检测器
│   │   └── firmware_detector.py   # 固件检测器
│   │
│   ├── analyzers/                 # 分析器
│   │   ├── base_analyzer.py       # 分析器基类
│   │   ├── statistical_analyzer.py
│   │   ├── correlation_analyzer.py
│   │   └── ml_analyzer.py
│   │
│   ├── handlers/                  # 处理器
│   │   ├── base_handler.py
│   │   ├── alert_handler.py
│   │   ├── log_handler.py
│   │   ├── block_handler.py
│   │   └── cloud_handler.py
│   │
│   ├── interfaces/                # 数据接口
│   │   ├── mavlink_interface.py
│   │   ├── gps_interface.py
│   │   ├── sensor_interface.py
│   │   └── network_interface.py
│   │
│   ├── models/                    # 数据模型
│   │   ├── threat_event.py        # 威胁事件模型
│   │   ├── alert.py               # 告警模型
│   │   └── telemetry.py           # 遥测数据模型
│   │
│   ├── utils/                     # 工具模块
│   │   ├── logger.py              # 日志工具
│   │   ├── crypto.py              # 加密工具
│   │   ├── time_utils.py          # 时间工具
│   │   └── packet_parser.py       # 数据包解析
│   │
│   └── main.py                    # 程序入口
│
├── config/                        # 配置文件
│   ├── default_config.yaml        # 默认配置
│   └── rules/                     # 检测规则
│       ├── mavlink_rules.yaml
│       ├── gps_rules.yaml
│       ├── sensor_rules.yaml
│       └── dos_rules.yaml
│
├── scripts/                       # 脚本
│   ├── install.sh                 # 安装脚本
│   ├── start_daemon.sh            # 启动脚本
│   └── stop_daemon.sh             # 停止脚本
│
├── tests/                         # 测试
│   ├── test_detectors/
│   ├── test_analyzers/
│   └── test_handlers/
│
├── docs/                          # 文档
│   ├── API.md                     # API文档
│   └── DEPLOYMENT.md              # 部署指南
│
├── requirements.txt               # Python依赖
├── setup.py                       # 安装配置
├── README.md                      # 项目说明
└── CHANGELOG.md                   # 更新日志
```

---

## 安全威胁检测能力

### 1. MAVLink通信攻击防护

| 攻击类型 | 检测方法 | 严重程度 |
|---------|---------|---------|
| 重放攻击 | 消息序列号验证 | 高 |
| 中间人攻击 | 消息频率异常检测 | 中 |
| 命令注入 | 异常命令识别 | 严重 |
| 会话劫持 | 系统/组件ID变更检测 | 严重 |

### 2. GPS欺骗检测

| 检测项 | 方法 | 阈值示例 |
|-------|------|---------|
| 位置跳变 | 距离变化率 | >1000米/秒 |
| 加速度异常 | 运动学约束 | >10 m/s² |
| 信号质量 | 卫星数量 | <6颗 |
| 速度一致性 | 多源对比 | 差异>5 m/s |

### 3. 传感器数据篡改检测

| 传感器 | 检测方法 |
|--------|---------|
| IMU | 数据范围验证 + 噪声分析 |
| 气压计 | 高度交叉验证 |
| 磁力计 | 方向一致性检查 |
| 温度传感器 | 物理合理性验证 |

### 4. DoS攻击防护

- 连接频率限制: 每秒最大连接数
- 请求速率限制: 每秒最大请求数
- 资源使用监控: CPU/内存阈值告警

---

## 开发指南

### 环境搭建

#### 后端环境

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 创建日志目录
mkdir -p logs

# 运行系统
python src/main.py --config config/default_config.yaml
```

#### 前端环境

```bash
# 进入前端目录
cd src/frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build
```

### 开发模式运行

```bash
# 终端1: 启动后端
python src/main.py --config config/default_config.yaml

# 终端2: 启动前端开发服务器
cd src/frontend && npm run dev
```

### 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_detectors/ -v

# 生成覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

## 快速开始

### 5分钟快速体验

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动系统（带Web界面）
python src/main.py --config config/default_config.yaml

# 3. 访问Web界面
# 浏览器打开: http://localhost:8080

# 4. 查看实时日志
tail -f logs/daemon.log
```

### 访问Web API

```bash
# 获取系统状态
curl http://localhost:8080/api/system/status

# 获取活跃告警
curl http://localhost:8080/api/alerts/active

# 获取威胁统计
curl http://localhost:8080/api/threats/distribution
```

---

## 项目亮点

1. **事件驱动架构**: 高效的异步事件处理机制
2. **模块化设计**: 各模块独立，易于扩展和维护
3. **跨平台支持**: 适配Linux、Android、嵌入式系统
4. **实时可视化**: WebSocket实时推送，ECharts数据可视化
5. **全面的检测能力**: 覆盖多种无人机安全威胁
6. **灵活的配置**: YAML配置文件，支持热重载
7. **完善的API**: RESTful API + WebSocket双接口

