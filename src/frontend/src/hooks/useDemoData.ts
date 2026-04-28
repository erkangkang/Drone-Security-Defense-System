import { useDemoStore } from '@/store/demoStore';
import type { DronePosition, MapThreatMarker } from '@/store/demoStore';

export function useDemoDrones(): DronePosition[] {
  const { enabled, drones } = useDemoStore();
  return enabled ? drones : [];
}

export function useDemoThreats(): MapThreatMarker[] {
  const { enabled, threats } = useDemoStore();
  return enabled ? threats : [];
}

export function useDemoAlerts() {
  const { enabled, alerts } = useDemoStore();
  return enabled ? alerts : [];
}

export function useDemoTrafficData(hours: number) {
  const { enabled, trafficData } = useDemoStore();
  if (!enabled) return null;

  const now = new Date();
  const cutoff = new Date(now.getTime() - hours * 3600000);
  const filtered = trafficData.filter((d) => new Date(d.timestamp) >= cutoff);
  return {
    time_series: filtered,
    total_events: filtered.reduce((sum, d) => sum + d.count, 0),
  };
}

export function useDemoSystemStatus() {
  const { enabled, systemStatus } = useDemoStore();
  return enabled ? systemStatus : null;
}

export function useDemoDetectors() {
  const { enabled, detectors } = useDemoStore();
  return enabled ? detectors : [];
}

export function useDemoMode() {
  const { enabled, toggle } = useDemoStore();
  return { enabled, toggle };
}
