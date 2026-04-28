# API 参考文档

# API Reference

本文档详细描述无人机安全防御系统的API接口。

## 基础信息

- **Base URL**: `http://localhost:8080/api`
- **Content-Type**: `application/json`
- **WebSocket URL**: `ws://localhost:8080/ws`

## 认证

当前版本未启用认证。如需启用，请在配置文件中设置：

```yaml
web:
  auth:
    enabled: true
```

## RESTful API

### 系统状态 API

#### 获取系统状态

```http
GET /api/system/status
```

**响应示例**:

```json
{
  "running": true,
  "platform": "linux",
  "detectors": ["mavlink", "gps", "sensor", "dos"],
  "handlers": ["alert", "log", "block"],
  "analyzers": ["statistical", "correlation"],
  "stats": {
    "start_time": 1642252800,
    "events_processed": 15234,
    "threats_detected": 47,
    "uptime": 3600
  },
  "web_stats": {
    "total_alerts": 47,
    "total_threats": 47,
    "active_alerts": 3,
    "alerts_by_severity": {
      "low": 20,
      "medium": 15,
      "high": 10,
      "critical": 2
    }
  }
}
```

#### 健康检查

```http
GET /api/system/health
```

**响应示例**:

```json
{
  "status": "healthy",
  "service": "drone-security-defense",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 重新加载配置

```http
POST /api/system/config/reload
```

**请求体**:

```json
{
  "force": false
}
```

**响应示例**:

```json
{
  "success": true,
  "message": "配置重新加载成功"
}
```

### 告警 API

#### 获取告警列表

```http
GET /api/alerts?limit=100&status=new&severity=high
```

**查询参数**:

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| limit | integer | 否 | 返回数量限制 (1-1000)，默认100 |
| status | string | 否 | 过滤状态 (new/acknowledged/resolved/false_positive) |
| severity | string | 否 | 过滤严重程度 (low/medium/high/critical) |

**响应示例**:

```json
[
  {
    "alert_id": "550e8400-e29b-41d4-a716-446655440000",
    "threat_type": "gps_spoofing",
    "severity": "high",
    "status": "new",
    "source": "gps0",
    "timestamp": "2024-01-15T10:30:00Z",
    "acknowledged_by": null,
    "acknowledged_at": null,
    "resolved_at": null,
    "notes": null,
    "evidence": {
      "position_jump": 1200,
      "expected_lat": 39.9042,
      "actual_lat": 39.9242
    },
    "confidence": 0.95
  }
]
```

#### 获取活跃告警

```http
GET /api/alerts/active?limit=50
```

**查询参数**:

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| limit | integer | 否 | 返回数量限制 (1-500)，默认50 |

#### 确认告警

```http
POST /api/alerts/{alert_id}/acknowledge
```

**路径参数**:

| 参数 | 类型 | 描述 |
|------|------|------|
| alert_id | string | 告警ID |

**请求体**:

```json
{
  "user": "admin",
  "notes": "正在处理中"
}
```

**响应示例**:

```json
{
  "success": true,
  "message": "告警已确认: 550e8400-e29b-41d4-a716-446655440000",
  "alert_id": "550e8400-e29b-41d4-a716-446655440000",
  "acknowledged_by": "admin",
  "timestamp": "2024-01-15T10:35:00Z"
}
```

#### 解决告警

```http
POST /api/alerts/{alert_id}/resolve
```

**请求体**:

```json
{
  "user": "admin"
}
```

#### 标记误报

```http
POST /api/alerts/{alert_id}/false_positive
```

**请求体**:

```json
{
  "user": "admin"
}
```

#### 获取告警统计

```http
GET /api/alerts/statistics/summary
```

**响应示例**:

```json
{
  "total": 47,
  "by_status": {
    "new": 3,
    "acknowledged": 5,
    "resolved": 38,
    "false_positive": 1
  },
  "by_severity": {
    "low": 20,
    "medium": 15,
    "high": 10,
    "critical": 2
  },
  "by_type": {
    "gps_spoofing": 15,
    "mavlink_hijacking": 10,
    "sensor_spoofing": 12,
    "dos_attack": 10
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 威胁事件 API

#### 获取威胁列表

```http
GET /api/threats?limit=100&threat_type=gps_spoofing&severity=high
```

**查询参数**:

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| limit | integer | 否 | 返回数量限制 (1-1000)，默认100 |
| threat_type | string | 否 | 过滤威胁类型 |
| severity | string | 否 | 过滤严重程度 |

**响应示例**:

```json
[
  {
    "event_id": "650e8400-e29b-41d4-a716-446655440000",
    "threat_type": "gps_spoofing",
    "severity": "high",
    "detector": "gps",
    "source": "gps0",
    "evidence": {
      "position_jump": 1200,
      "velocity_anomaly": true
    },
    "confidence": 0.95,
    "timestamp": "2024-01-15T10:30:00Z",
    "resolved": false
  }
]
```

#### 获取威胁时间线

```http
GET /api/threats/timeline?limit=100
```

**响应示例**:

```json
{
  "events": [
    {
      "event_id": "650e8400-e29b-41d4-a716-446655440000",
      "threat_type": "gps_spoofing",
      "severity": "high",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 47
}
```

#### 获取威胁类型

```http
GET /api/threats/types
```

**响应示例**:

```json
{
  "types": [
    "mavlink_hijacking",
    "mavlink_mitm",
    "gps_spoofing",
    "sensor_spoofing",
    "dos_attack"
  ],
  "distribution": {
    "gps_spoofing": 15,
    "mavlink_hijacking": 10
  }
}
```

#### 获取威胁分布

```http
GET /api/threats/distribution
```

**响应示例**:

```json
{
  "by_type": {
    "gps_spoofing": 15,
    "mavlink_hijacking": 10,
    "sensor_spoofing": 12,
    "dos_attack": 10
  },
  "by_severity": {
    "low": 10,
    "medium": 15,
    "high": 15,
    "critical": 7
  },
  "by_detector": {
    "gps": 15,
    "mavlink": 20,
    "sensor": 12
  },
  "total": 47
}
```

### 检测器 API

#### 获取所有检测器

```http
GET /api/detectors
```

**响应示例**:

```json
[
  {
    "name": "gps",
    "running": true,
    "enabled": true,
    "type": "gps",
    "stats": {
      "running": true,
      "events_processed": 5234,
      "threats_detected": 15,
      "last_activity": "2024-01-15T10:29:55Z"
    }
  }
]
```

#### 获取指定检测器

```http
GET /api/detectors/{name}
```

**响应示例**:

```json
{
  "name": "gps",
  "running": true,
  "enabled": true,
  "type": "gps",
  "stats": {
    "running": true,
    "events_processed": 5234,
    "threats_detected": 15,
    "last_activity": "2024-01-15T10:29:55Z"
  }
}
```

#### 启动检测器

```http
POST /api/detectors/{name}/start
```

**响应示例**:

```json
{
  "success": true,
  "message": "检测器已启动: gps"
}
```

#### 停止检测器

```http
POST /api/detectors/{name}/stop
```

#### 控制检测器

```http
POST /api/detectors/{name}/control
```

**请求体**:

```json
{
  "action": "start"
}
```

### 统计数据 API

#### 获取统计数据

```http
GET /api/statistics?hours=24
```

**查询参数**:

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| hours | integer | 否 | 统计时间范围（小时），1-168，默认24 |

**响应示例**:

```json
{
  "total_alerts": 47,
  "total_threats": 47,
  "active_alerts": 3,
  "alerts_by_severity": {
    "low": 20,
    "medium": 15,
    "high": 10,
    "critical": 2
  },
  "threats_by_type": {
    "gps_spoofing": 15,
    "mavlink_hijacking": 10
  },
  "traffic_trends": [
    {
      "timestamp": "2024-01-15 00:00",
      "count": 5,
      "by_severity": {
        "low": 2,
        "medium": 2,
        "high": 1
      }
    }
  ],
  "detector_stats": {
    "gps": {
      "threats_detected": 15
    }
  }
}
```

#### 获取流量趋势

```http
GET /api/statistics/traffic?hours=24
```

**响应示例**:

```json
{
  "time_series": [
    {
      "timestamp": "2024-01-15 00:00",
      "count": 5,
      "by_severity": {
        "low": 2,
        "medium": 2,
        "high": 1
      }
    }
  ],
  "total_events": 47,
  "peak_hour": {
    "timestamp": "2024-01-15 10:00",
    "count": 12
  }
}
```

#### 获取威胁统计

```http
GET /api/statistics/threats
```

#### 获取仪表盘数据

```http
GET /api/statistics/dashboard
```

#### 获取时间线数据

```http
GET /api/statistics/timeline?hours=24&event_type=threat
```

**查询参数**:

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| hours | integer | 否 | 统计时间范围（小时） |
| event_type | string | 否 | 事件类型 (threat/alert/all) |

## WebSocket API

### 连接

```javascript
const ws = new WebSocket('ws://localhost:8080/ws');
```

### 订阅频道

**客户端 → 服务器**:

```json
{
  "action": "subscribe",
  "channels": ["threats", "alerts", "system", "detectors"]
}
```

**可用频道**:

- `threats` - 威胁检测事件
- `alerts` - 告警创建事件
- `system` - 系统状态更新
- `detectors` - 检测器状态更新

### 取消订阅

```json
{
  "action": "unsubscribe",
  "channels": ["alerts"]
}
```

### Ping/Pong

**客户端**:

```json
{
  "action": "ping"
}
```

**服务器响应**:

```json
{
  "type": "pong",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 获取连接状态

```json
{
  "action": "get_status"
}
```

**服务器响应**:

```json
{
  "type": "status",
  "subscriptions": ["threats", "alerts"],
  "active_connections": 3
}
```

### 服务器推送消息

#### 威胁检测事件

```json
{
  "type": "threat.detected",
  "data": {
    "event_id": "650e8400-e29b-41d4-a716-446655440000",
    "threat_type": "gps_spoofing",
    "severity": "high",
    "detector": "gps",
    "source": "gps0",
    "evidence": {
      "position_jump": 1200
    },
    "confidence": 0.95,
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### 告警创建事件

```json
{
  "type": "alert.created",
  "data": {
    "alert_id": "550e8400-e29b-41d4-a716-446655440000",
    "threat_type": "gps_spoofing",
    "severity": "high",
    "status": "new",
    "source": "gps0",
    "timestamp": "2024-01-15T10:30:05Z"
  },
  "timestamp": "2024-01-15T10:30:05Z"
}
```

#### 系统状态更新

```json
{
  "type": "system.update",
  "data": {
    "running": true,
    "uptime": 3600,
    "threats_detected": 47
  },
  "timestamp": "2024-01-15T10:30:10Z"
}
```

#### 检测器状态更新

```json
{
  "type": "detector.update",
  "detector": "gps",
  "data": {
    "running": true,
    "threats_detected": 15
  }
}
```

## 错误响应

所有API在发生错误时返回以下格式：

```json
{
  "error": "error_type",
  "message": "错误描述",
  "detail": "详细错误信息（可选）"
}
```

### HTTP状态码

| 状态码 | 描述 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

## 速率限制

当前版本未启用速率限制。如需启用，可在配置中添加：

```yaml
web:
  rate_limit:
    enabled: true
    requests_per_minute: 60
```
