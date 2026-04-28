import { MetricCard, ThreatLevelGauge, ThreatTimeline, DroneStatusPanel, DetectorGrid, AlertFeedEnhanced, RadarRing } from '@/components/dashboard';
import { Card } from '@/components/ui/Card';
import { useTrafficTrends } from '@/hooks/useStatistics';
import { useSystemStatus } from '@/hooks/useSystemStatus';
import { useDetectors } from '@/hooks/useDetectors';
import { useActiveAlerts } from '@/hooks/useAlerts';
import { useSystemWebSocket } from '@/hooks/useWebSocket';
import { useDemoMode, useDemoDrones, useDemoAlerts, useDemoTrafficData, useDemoSystemStatus, useDemoDetectors } from '@/hooks/useDemoData';
import { useWSStore } from '@/store/websocketStore';
import { formatDuration } from '@/utils/format';

export function Dashboard() {
  const { connected } = useSystemWebSocket();
  const { enabled: demoEnabled } = useDemoMode();
  const wsConnected = useWSStore((s) => s.connected);

  // Real data hooks
  const { trafficData } = useTrafficTrends(24);
  const { systemStatus } = useSystemStatus();
  const { detectors: realDetectors } = useDetectors();
  const { alerts: realAlerts } = useActiveAlerts(20);

  // Demo data hooks
  const demoDrone = useDemoDrones();
  const demoTraffic = useDemoTrafficData(24);
  const demoAlerts = useDemoAlerts();
  const demoStatus = useDemoSystemStatus();
  const demoDetectors = useDemoDetectors();

  // Choose data source
  const useDemo = demoEnabled || !wsConnected;

  const traffic = useDemo ? demoTraffic : trafficData;
  const status = useDemo ? demoStatus : systemStatus;
  const detectors = useDemo ? demoDetectors : realDetectors;
  const alerts = useDemo ? demoAlerts : realAlerts;
  const drone = useDemo && demoDrone.length > 0 ? demoDrone[0] : null;

  const timelineData = traffic?.time_series || [];
  const uptime = status?.stats?.uptime || 0;
  const threatsDetected = status?.stats?.threats_detected || status?.web_stats?.total_threats || 0;
  const activeAlerts = status?.web_stats?.active_alerts || alerts.length || 0;
  const runningDetectors = Array.isArray(detectors) ? detectors.filter((d: any) => d.running).length : 0;

  // Calculate threat level (0-100)
  const threatLevel = Math.min(100, Math.max(0,
    activeAlerts * 5 + (status?.web_stats?.threats_by_type
      ? Object.keys(status.web_stats.threats_by_type).length * 8
      : threatsDetected * 2)
  ));

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[#e2e8f0] flex items-center gap-3 font-orbitron neon-text">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-accent-cyan" style={{ filter: 'drop-shadow(0 0 4px rgba(0,230,168,0.35))' }}>
            <path d="M12 2L4 6v4l8 4 8-4V6l-8-4z" stroke="currentColor" strokeWidth="1.5" fill="none"/>
            <path d="M4 10v4l8 4 8-4v-4" stroke="currentColor" strokeWidth="1.5" fill="none"/>
            <circle cx="12" cy="12" r="2" fill="currentColor"/>
          </svg>
          态势感知仪表盘
        </h1>
        <div className="flex items-center gap-2">
          <span
            className={`h-2 w-2 rounded-full ${
              connected || useDemo
                ? 'bg-accent-green animate-pulse-glow shadow-[0_0_6px_#10b981]'
                : 'bg-danger-400'
            }`}
          />
          <span className="text-sm text-[#94a3b8] font-mono">
            {useDemo ? 'DEMO 模式' : connected ? '实时连接' : '离线'}
          </span>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="威胁总数"
          value={threatsDetected}
          color="cyan"
          icon={<ShieldIcon />}
        />
        <MetricCard
          title="活跃告警"
          value={activeAlerts}
          color={activeAlerts > 5 ? 'red' : activeAlerts > 0 ? 'amber' : 'green'}
          icon={<BellIcon />}
        />
        <MetricCard
          title="在线检测器"
          value={`${runningDetectors}/${Array.isArray(detectors) ? detectors.length : 0}`}
          color="green"
          icon={<RadarIcon />}
        />
        <MetricCard
          title="运行时间"
          value={formatDuration(uptime)}
          color="default"
          icon={<ClockIcon />}
        />
      </div>

      {/* Accent divider */}
      <div className="h-px bg-gradient-to-r from-transparent via-accent-cyan/25 to-transparent" />

      {/* Main Content Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Threat Timeline */}
        <Card>
          <h3 className="text-xs font-semibold text-[#e2e8f0] mb-2 font-orbitron tracking-wider uppercase">威胁时间线</h3>
          <ThreatTimeline data={timelineData} height={250} />
        </Card>

        {/* Drone Status + Radar + Gauge */}
        <div className="space-y-4">
          <DroneStatusPanel drone={drone} />

          {/* Threat Level Gauge with RadarRing */}
          <Card>
            <h3 className="text-xs font-semibold text-[#e2e8f0] mb-1 font-orbitron tracking-wider uppercase">威胁等级</h3>
            <div className="flex items-center justify-center gap-4">
              <div className="hidden sm:block opacity-60">
                <RadarRing size={120} threatCount={Math.min(activeAlerts, 8)} />
              </div>
              <div className="flex-1">
                <ThreatLevelGauge level={threatLevel} height={160} />
              </div>
            </div>
          </Card>
        </div>

        {/* Alert Feed */}
        <AlertFeedEnhanced alerts={alerts} />
      </div>

      {/* Detector Grid */}
      <Card>
        {Array.isArray(detectors) && detectors.length > 0 && (
          <DetectorGrid detectors={detectors} />
        )}
      </Card>
    </div>
  );
}

// Mini SVG icons
function ShieldIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 16 16" fill="none" className="text-accent-cyan">
      <path d="M8 1L2 4v4c0 3.5 2.5 6.5 6 7.5 3.5-1 6-4 6-7.5V4L8 1z" stroke="currentColor" strokeWidth="1.5"/>
    </svg>
  );
}

function BellIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 16 16" fill="none" className="text-accent-cyan">
      <path d="M12 7V6a4 4 0 0 0-8 0v1l-1 3h10l-1-3z" stroke="currentColor" strokeWidth="1.5"/>
    </svg>
  );
}

function RadarIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 16 16" fill="none" className="text-accent-cyan">
      <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5"/>
      <circle cx="8" cy="8" r="3" stroke="currentColor" strokeWidth="1"/>
      <circle cx="8" cy="8" r="1" fill="currentColor"/>
    </svg>
  );
}

function ClockIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 16 16" fill="none" className="text-accent-cyan">
      <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5"/>
      <path d="M8 4v4l3 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}
