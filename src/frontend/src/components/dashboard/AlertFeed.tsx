import { useActiveAlerts, useAlertActions } from '@/hooks/useAlerts';
import { Card } from '@/components/ui/Card';
import { formatRelativeTime } from '@/utils/format';
import { severityColors, severityLabels, statusLabels } from '@/types';
import { clsx } from 'clsx';

interface AlertFeedProps {
  limit?: number;
}

export function AlertFeed({ limit = 10 }: AlertFeedProps) {
  const { alerts, isLoading } = useActiveAlerts(limit);
  const { acknowledgeAlert, resolveAlert } = useAlertActions();

  if (isLoading) {
    return (
      <Card>
        <div className="animate-pulse">
          <div className="h-4 bg-soc-bg-tertiary rounded w-1/4 mb-4" />
          <div className="space-y-2">
            <div className="h-16 bg-soc-bg-tertiary rounded" />
            <div className="h-16 bg-soc-bg-tertiary rounded" />
          </div>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-[#e2e8f0]">最近告警</h2>
        <span className="text-sm text-[#94a3b8]">{alerts.length} 条告警</span>
      </div>

      <div className="space-y-3 max-h-[400px] overflow-y-auto">
        {alerts.length === 0 ? (
          <div className="text-center py-8 text-[#64748b]">暂无告警</div>
        ) : (
          alerts.map((alert) => (
            <AlertItem
              key={alert.alert_id}
              alert={alert}
              onAcknowledge={() => acknowledgeAlert({ alertId: alert.alert_id })}
              onResolve={() => resolveAlert({ alertId: alert.alert_id })}
            />
          ))
        )}
      </div>
    </Card>
  );
}

interface AlertItemProps {
  alert: {
    alert_id: string;
    threat_type: string;
    severity: string;
    status: string;
    source: string;
    timestamp: string;
  };
  onAcknowledge: () => void;
  onResolve: () => void;
}

function AlertItem({ alert, onAcknowledge, onResolve }: AlertItemProps) {
  const severityColor = severityColors[alert.severity] || '#64748b';

  return (
    <div className="p-3 border border-soc-border rounded-lg hover:bg-soc-bg-tertiary/70 transition-colors"
      style={{ borderLeftWidth: '3px', borderLeftColor: severityColor }}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <span
            className="h-2 w-2 rounded-full animate-pulse-glow"
            style={{ backgroundColor: severityColor }}
          />
          <span className="text-sm font-medium text-[#e2e8f0]">{alert.threat_type}</span>
          <span
            className={clsx(
              'px-2 py-0.5 text-xs font-medium rounded-full',
              alert.status === 'new'
                ? 'bg-accent-cyan/20 text-accent-cyan'
                : 'bg-soc-bg-tertiary text-[#94a3b8]'
            )}
          >
            {statusLabels[alert.status] || alert.status}
          </span>
        </div>
        <span className="text-xs text-[#64748b]">{formatRelativeTime(alert.timestamp)}</span>
      </div>

      <div className="flex items-center justify-between">
        <div className="text-sm text-[#94a3b8]">
          <span>来源: {alert.source}</span>
          <span className="mx-2">·</span>
          <span style={{ color: severityColor }}>
            {severityLabels[alert.severity] || alert.severity}
          </span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onAcknowledge}
            className="text-xs text-accent-cyan hover:text-accent-cyan/80 font-medium"
          >
            确认
          </button>
          <button
            onClick={onResolve}
            className="text-xs text-[#94a3b8] hover:text-[#e2e8f0] font-medium"
          >
            解决
          </button>
        </div>
      </div>
    </div>
  );
}
