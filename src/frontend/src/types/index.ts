// 系统状态类型
export interface SystemStatus {
  running: boolean;
  platform: string;
  detectors: string[];
  handlers: string[];
  analyzers: string[];
  stats: {
    start_time: number;
    events_processed: number;
    threats_detected: number;
    uptime: number;
  };
  web_stats?: WebStats;
}

export interface WebStats {
  total_alerts: number;
  total_threats: number;
  active_alerts: number;
  alerts_by_severity: Record<string, number>;
  threats_by_type: Record<string, number>;
}

// 告警类型
export interface Alert {
  alert_id: string;
  threat_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'new' | 'acknowledged' | 'resolved' | 'false_positive';
  source: string;
  timestamp: string;
  acknowledged_by?: string;
  acknowledged_at?: string;
  resolved_at?: string;
  notes?: string;
  evidence?: Record<string, unknown>;
  confidence?: number;
}

// 威胁事件类型
export interface Threat {
  event_id: string;
  threat_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  detector: string;
  source: string;
  evidence: Record<string, unknown>;
  confidence: number;
  timestamp: string;
  resolved: boolean;
}

// 检测器状态类型
export interface DetectorStatus {
  name: string;
  running: boolean;
  enabled: boolean;
  type: string;
  stats: Record<string, unknown>;
}

// 统计数据类型
export interface Statistics {
  total_alerts: number;
  total_threats: number;
  active_alerts: number;
  alerts_by_severity: Record<string, number>;
  threats_by_type: Record<string, number>;
  traffic_trends: TrafficDataPoint[];
  detector_stats: Record<string, unknown>;
}

export interface TrafficDataPoint {
  timestamp: string;
  count: number;
  by_severity?: Record<string, number>;
}

// WebSocket消息类型
export interface WSMessage {
  type: string;
  data?: unknown;
  timestamp?: string;
}

// API响应类型
export interface ApiResponse<T = unknown> {
  success: boolean;
  message?: string;
  data?: T;
}

export interface ErrorResponse {
  error: string;
  message: string;
  detail?: string;
}

// 无人机位置类型
export interface DronePosition {
  drone_id: string;
  latitude: number;
  longitude: number;
  altitude: number;
  heading: number;
  speed: number;
  timestamp: string;
  status: 'normal' | 'warning' | 'threat';
}

// 严重程度颜色映射
export const severityColors: Record<string, string> = {
  low: '#00E6A8',
  medium: '#fbbf24',
  high: '#f59e0b',
  critical: '#f43f5e',
};

// 严重程度标签映射
export const severityLabels: Record<string, string> = {
  low: '低',
  medium: '中',
  high: '高',
  critical: '严重',
};

// 状态标签映射
export const statusLabels: Record<string, string> = {
  new: '新建',
  acknowledged: '已确认',
  resolved: '已解决',
  false_positive: '误报',
};
