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

export function Screen() {
  const { connected } = useSystemWebSocket();
  const { enabled: demoEnabled } = useDemoMode();
  const wsConnected = useWSStore((s) => s.connected);

  const { trafficData } = useTrafficTrends(24);
  const { systemStatus } = useSystemStatus();
  const { detectors: realDetectors } = useDetectors();
  const { alerts: realAlerts } = useActiveAlerts(20);

  const demoDrone = useDemoDrones();
  const demoTraffic = useDemoTrafficData(24);
  const demoAlerts = useDemoAlerts();
  const demoStatus = useDemoSystemStatus();
  const demoDetectors = useDemoDetectors();

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

  const threatLevel = Math.min(
    100,
    Math.max(
      0,
      activeAlerts * 5 +
        (status?.web_stats?.threats_by_type ? Object.keys(status.web_stats.threats_by_type).length * 8 : threatsDetected * 2)
    )
  );

  return (
    <div className="h-[calc(100vh-3.5rem)] min-h-[720px]">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold text-[#e2e8f0] font-orbitron neon-text tracking-wide">无人机安全态势大屏</h1>
          <div className="h-px w-16 bg-gradient-to-r from-transparent via-accent-cyan/45 to-transparent" />
          <span className="text-xs text-[#94a3b8] font-mono">{useDemo ? 'DEMO' : connected ? 'REALTIME' : 'OFFLINE'}</span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`h-2 w-2 rounded-full ${connected || useDemo ? 'bg-accent-green animate-pulse-glow shadow-[0_0_6px_#22c55e]' : 'bg-danger-400'}`}
          />
          <span className="text-xs text-[#94a3b8] font-mono">{useDemo ? '数据演示' : connected ? '实时连接' : '离线'}</span>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-3 h-[calc(100%-2.25rem)]">
        <div className="col-span-3 flex flex-col gap-3 min-w-0">
          <div className="grid grid-cols-1 gap-3">
            <MetricCard title="威胁总数" value={threatsDetected} color="cyan" icon={<ShieldIcon />} />
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
            <MetricCard title="运行时间" value={formatDuration(uptime)} color="default" icon={<ClockIcon />} />
          </div>

          <Card className="flex-1 min-h-0" variant="hud">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-semibold text-[#e2e8f0] font-orbitron tracking-wider uppercase">威胁等级</h3>
              <span className="text-xs text-accent-cyan/80 font-mono">{Math.round(threatLevel)}%</span>
            </div>
            <div className="flex items-center justify-center gap-3">
              <div className="opacity-70">
                <RadarRing size={120} threatCount={Math.min(activeAlerts, 8)} />
              </div>
              <div className="flex-1">
                <ThreatLevelGauge level={threatLevel} height={170} />
              </div>
            </div>
          </Card>
        </div>

        <div className="col-span-6 flex flex-col gap-3 min-w-0">
          <Card className="flex-1 min-h-0" variant="hud">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-semibold text-[#e2e8f0] font-orbitron tracking-wider uppercase">威胁时间线</h3>
              <span className="text-xs text-[#94a3b8] font-mono">24H</span>
            </div>
            <ThreatTimeline data={timelineData} height={260} />
          </Card>

          <Card className="flex-1 min-h-0" variant="glass">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-semibold text-[#e2e8f0] font-orbitron tracking-wider uppercase">检测器概览</h3>
              <span className="text-xs text-[#94a3b8] font-mono">RUNNING {runningDetectors}</span>
            </div>
            {Array.isArray(detectors) && detectors.length > 0 && <DetectorGrid detectors={detectors} />}
          </Card>
        </div>

        <div className="col-span-3 flex flex-col gap-3 min-w-0">
          <div className="min-h-0">
            <DroneStatusPanel drone={drone} />
          </div>

          <div className="flex-1 min-h-0">
            <AlertFeedEnhanced alerts={alerts} />
          </div>
        </div>
      </div>
    </div>
  );
}

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
