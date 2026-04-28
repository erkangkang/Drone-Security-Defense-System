import { useSystemStatus } from '@/hooks/useSystemStatus';
import { Card } from '@/components/ui/Card';
import { formatDuration } from '@/utils/format';

export function SystemStatusCard() {
  const { systemStatus, isLoading } = useSystemStatus();

  if (isLoading || !systemStatus) {
    return (
      <Card>
        <div className="animate-pulse">
          <div className="h-4 bg-soc-bg-tertiary rounded w-1/4 mb-4" />
          <div className="space-y-2">
            <div className="h-3 bg-soc-bg-tertiary rounded" />
            <div className="h-3 bg-soc-bg-tertiary rounded" />
            <div className="h-3 bg-soc-bg-tertiary rounded" />
          </div>
        </div>
      </Card>
    );
  }

  const uptime = systemStatus.stats?.uptime || 0;
  const threatsDetected = systemStatus.stats?.threats_detected || 0;
  const activeAlerts = systemStatus.web_stats?.active_alerts || 0;

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-[#e2e8f0]">系统状态</h2>
        <span
          className={`px-2 py-1 text-xs font-medium rounded-full ${
            systemStatus.running
              ? 'bg-success-500/20 text-success-400'
              : 'bg-soc-bg-tertiary text-[#94a3b8]'
          }`}
        >
          {systemStatus.running ? '运行中' : '已停止'}
        </span>
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-[#94a3b8]">运行时间</span>
          <span className="text-sm font-medium text-[#e2e8f0]">{formatDuration(uptime)}</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm text-[#94a3b8]">平台</span>
          <span className="text-sm font-medium text-[#e2e8f0]">{systemStatus.platform}</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-sm text-[#94a3b8]">检测器数量</span>
          <span className="text-sm font-medium text-[#e2e8f0]">{systemStatus.detectors?.length || 0}</span>
        </div>

        <div className="h-px bg-soc-border" />

        <div className="grid grid-cols-2 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-accent-cyan">{threatsDetected}</div>
            <div className="text-xs text-[#94a3b8]">检测威胁</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-danger-400">{activeAlerts}</div>
            <div className="text-xs text-[#94a3b8]">活跃告警</div>
          </div>
        </div>
      </div>
    </Card>
  );
}
