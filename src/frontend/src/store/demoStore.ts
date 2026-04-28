import { create } from 'zustand';

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

export interface MapThreatMarker {
  threat_id: string;
  latitude: number;
  longitude: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  threat_type: string;
  timestamp: string;
  description: string;
}

interface DemoStore {
  enabled: boolean;
  toggle: () => void;
  drones: DronePosition[];
  threats: MapThreatMarker[];
  alerts: Array<{
    alert_id: string;
    threat_type: string;
    severity: string;
    status: string;
    source: string;
    timestamp: string;
  }>;
  trafficData: Array<{
    timestamp: string;
    count: number;
    by_severity: Record<string, number>;
  }>;
  systemStatus: {
    running: boolean;
    platform: string;
    detectors: string[];
    stats: { uptime: number; events_processed: number; threats_detected: number; start_time: number };
    web_stats: { total_alerts: number; total_threats: number; active_alerts: number; alerts_by_severity: Record<string, number>; threats_by_type: Record<string, number> };
  } | null;
  detectors: Array<{
    name: string;
    running: boolean;
    enabled: boolean;
    type: string;
    stats: Record<string, unknown>;
  }>;
}

const THREAT_TYPES = [
  'mavlink_hijacking', 'mavlink_command_injection', 'mavlink_mitm',
  'gps_spoofing', 'gps_position_jump',
  'sensor_spoofing', 'sensor_anomaly',
  'dos_attack', 'syn_flood', 'udp_flood',
  'firmware_tampering',
];

const DETECTOR_TYPES = ['mavlink', 'gps', 'sensor', 'dos', 'firmware'];
const SEVERITIES: Array<'low' | 'medium' | 'high' | 'critical'> = ['low', 'medium', 'high', 'critical'];
const SEVERITY_WEIGHTS = [0.7, 0.9, 0.98, 1.0];

function randomSeverity(): 'low' | 'medium' | 'high' | 'critical' {
  const r = Math.random();
  for (let i = 0; i < SEVERITY_WEIGHTS.length; i++) {
    if (r < SEVERITY_WEIGHTS[i]) return SEVERITIES[i];
  }
  return 'low';
}

function randomThreatType(): string {
  return THREAT_TYPES[Math.floor(Math.random() * THREAT_TYPES.length)];
}

let idCounter = 0;
function nextId(prefix: string): string {
  return `${prefix}-${++idCounter}`;
}

const BEIJING_CENTER = { lat: 39.9042, lng: 116.4074 };

function generateDrone(): DronePosition {
  return {
    drone_id: 'drone-001',
    latitude: BEIJING_CENTER.lat + (Math.random() - 0.5) * 0.02,
    longitude: BEIJING_CENTER.lng + (Math.random() - 0.5) * 0.02,
    altitude: 50 + Math.random() * 200,
    heading: Math.random() * 360,
    speed: 2 + Math.random() * 15,
    timestamp: new Date().toISOString(),
    status: Math.random() > 0.9 ? 'warning' : 'normal',
  };
}

function generateThreat(): MapThreatMarker {
  return {
    threat_id: nextId('threat'),
    latitude: BEIJING_CENTER.lat + (Math.random() - 0.5) * 0.05,
    longitude: BEIJING_CENTER.lng + (Math.random() - 0.5) * 0.05,
    severity: randomSeverity(),
    threat_type: randomThreatType(),
    timestamp: new Date().toISOString(),
    description: `检测到${randomThreatType()}威胁`,
  };
}

function generateTrafficData(hours: number) {
  const now = new Date();
  const points = [];
  for (let i = hours * 4; i >= 0; i--) {
    const ts = new Date(now.getTime() - i * 15 * 60 * 1000);
    const base = Math.floor(Math.random() * 5) + 1;
    // Simulate daytime peak
    const hourFactor = ts.getHours() >= 8 && ts.getHours() <= 20 ? 2 : 0.5;
    points.push({
      timestamp: ts.toISOString(),
      count: Math.floor(base * hourFactor),
      by_severity: {
        low: Math.floor(base * hourFactor * 0.7),
        medium: Math.floor(base * hourFactor * 0.2),
        high: Math.floor(base * hourFactor * 0.08),
        critical: Math.floor(base * hourFactor * 0.02),
      },
    });
  }
  return points;
}

function generateDetectors() {
  return DETECTOR_TYPES.map((type) => ({
    name: `${type}_detector`,
    running: true,
    enabled: true,
    type,
    stats: {
      events_processed: Math.floor(Math.random() * 5000) + 1000,
      threats_detected: Math.floor(Math.random() * 50),
      last_activity: new Date().toISOString(),
    },
  }));
}

// Timer reference for cleanup
let simulationTimer: ReturnType<typeof setInterval> | null = null;

export const useDemoStore = create<DemoStore>((set, get) => ({
  enabled: false,
  drones: [generateDrone()],
  threats: Array.from({ length: 5 }, generateThreat),
  alerts: Array.from({ length: 8 }, () => ({
    alert_id: nextId('alert'),
    threat_type: randomThreatType(),
    severity: randomSeverity(),
    status: Math.random() > 0.3 ? 'new' : 'acknowledged',
    source: `detector_${DETECTOR_TYPES[Math.floor(Math.random() * DETECTOR_TYPES.length)]}`,
    timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString(),
  })),
  trafficData: generateTrafficData(24),
  systemStatus: {
    running: true,
    platform: 'windows',
    detectors: DETECTOR_TYPES.map((t) => `${t}_detector`),
    stats: {
      uptime: Math.floor(Math.random() * 86400) + 3600,
      events_processed: Math.floor(Math.random() * 50000),
      threats_detected: Math.floor(Math.random() * 200),
      start_time: Date.now() / 1000 - Math.floor(Math.random() * 86400),
    },
    web_stats: {
      total_alerts: Math.floor(Math.random() * 100) + 10,
      total_threats: Math.floor(Math.random() * 200) + 20,
      active_alerts: Math.floor(Math.random() * 15),
      alerts_by_severity: { low: 30, medium: 15, high: 8, critical: 2 },
      threats_by_type: Object.fromEntries(
        THREAT_TYPES.slice(0, 6).map((t) => [t, Math.floor(Math.random() * 30) + 1])
      ),
    },
  },
  detectors: generateDetectors(),

  toggle: () => {
    const newState = !get().enabled;
    if (newState) {
      // Start simulation
      simulationTimer = setInterval(() => {
        const { drones, threats, alerts } = get();
        // Drift drone position
        const updatedDrone = {
          ...drones[0],
          latitude: drones[0].latitude + (Math.random() - 0.5) * 0.001,
          longitude: drones[0].longitude + (Math.random() - 0.5) * 0.001,
          altitude: drones[0].altitude + (Math.random() - 0.5) * 5,
          heading: (drones[0].heading + (Math.random() - 0.5) * 10) % 360,
          speed: Math.max(0, drones[0].speed + (Math.random() - 0.5) * 2),
          timestamp: new Date().toISOString(),
        };

        // Occasionally add a new threat
        const newThreat = Math.random() > 0.7 ? [generateThreat()] : [];
        const updatedThreats = [...newThreat, ...threats].slice(0, 50);

        // Occasionally add a new alert
        const newAlert = Math.random() > 0.6
          ? [{
              alert_id: nextId('alert'),
              threat_type: randomThreatType(),
              severity: randomSeverity(),
              status: 'new',
              source: `detector_${DETECTOR_TYPES[Math.floor(Math.random() * DETECTOR_TYPES.length)]}`,
              timestamp: new Date().toISOString(),
            }]
          : [];
        const updatedAlerts = [...newAlert, ...alerts].slice(0, 100);

        // Update system stats
        const status = get().systemStatus;
        const updatedStatus = status ? {
          ...status,
          stats: {
            ...status.stats,
            uptime: status.stats.uptime + 5,
            events_processed: status.stats.events_processed + Math.floor(Math.random() * 10),
          },
          web_stats: {
            ...status.web_stats,
            active_alerts: updatedAlerts.filter((a) => a.status !== 'resolved').length,
          },
        } : null;

        set({
          drones: [updatedDrone],
          threats: updatedThreats,
          alerts: updatedAlerts,
          systemStatus: updatedStatus,
        });
      }, 5000);
    } else {
      // Stop simulation
      if (simulationTimer) {
        clearInterval(simulationTimer);
        simulationTimer = null;
      }
    }
    set({ enabled: newState });
  },
}));
