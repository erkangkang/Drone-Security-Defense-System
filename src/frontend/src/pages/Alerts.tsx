import { useState } from 'react';
import { useAlerts, useAlertActions } from '@/hooks/useAlerts';
import { Card } from '@/components/ui/Card';
import { formatRelativeTime } from '@/utils/format';
import { severityColors, statusLabels } from '@/types';
import { clsx } from 'clsx';

export function Alerts() {
  const [filter, setFilter] = useState<{ status?: string; severity?: string }>({});
  const { alerts, isLoading } = useAlerts({ ...filter, limit: 100 });
  const { acknowledgeAlert, resolveAlert, markFalsePositive } = useAlertActions();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[#e2e8f0] font-orbitron neon-text">告警管理</h1>

      {/* Filters */}
      <Card variant="glass">
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <label className="text-xs text-[#94a3b8] font-orbitron tracking-wider">状态:</label>
            <select
              className="input w-auto font-mono"
              value={filter.status || ''}
              onChange={(e) => setFilter({ ...filter, status: e.target.value || undefined })}
            >
              <option value="">全部</option>
              <option value="new">新建</option>
              <option value="acknowledged">已确认</option>
              <option value="resolved">已解决</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-xs text-[#94a3b8] font-orbitron tracking-wider">严重程度:</label>
            <select
              className="input w-auto font-mono"
              value={filter.severity || ''}
              onChange={(e) => setFilter({ ...filter, severity: e.target.value || undefined })}
            >
              <option value="">全部</option>
              <option value="low">低</option>
              <option value="medium">中</option>
              <option value="high">高</option>
              <option value="critical">严重</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Alert List */}
      <Card>
        {isLoading ? (
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-20 bg-soc-bg-tertiary rounded" />
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {alerts.length === 0 ? (
              <div className="text-center py-8 text-[#64748b] font-mono">暂无告警</div>
            ) : (
              alerts.map((alert) => (
                <AlertListItem
                  key={alert.alert_id}
                  alert={alert}
                  onAcknowledge={() => acknowledgeAlert({ alertId: alert.alert_id })}
                  onResolve={() => resolveAlert({ alertId: alert.alert_id })}
                  onMarkFalsePositive={() => markFalsePositive({ alertId: alert.alert_id })}
                />
              ))
            )}
          </div>
        )}
      </Card>
    </div>
  );
}

interface AlertListItemProps {
  alert: {
    alert_id: string;
    threat_type: string;
    severity: string;
    status: string;
    source: string;
    timestamp: string;
    notes?: string;
    acknowledged_by?: string;
  };
  onAcknowledge: () => void;
  onResolve: () => void;
  onMarkFalsePositive: () => void;
}

function AlertListItem({ alert, onAcknowledge, onResolve, onMarkFalsePositive }: AlertListItemProps) {
  const severityColor = severityColors[alert.severity] || '#64748b';

  return (
    <div
      className="p-4 border border-soc-border rounded-lg hover:bg-soc-bg-tertiary/70 transition-colors relative overflow-hidden"
      style={{ borderLeftWidth: '3px', borderLeftColor: severityColor }}
    >
      {/* Top accent line */}
      <div
        className="absolute top-0 left-0 right-0 h-px"
        style={{ background: `linear-gradient(90deg, transparent, ${severityColor}40, transparent)` }}
      />

      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <span
            className="h-3 w-3 rounded-full animate-pulse-glow"
            style={{ backgroundColor: severityColor, boxShadow: `0 0 6px ${severityColor}` }}
          />
          <div>
            <h3 className="font-medium text-[#e2e8f0] font-mono">{alert.threat_type}</h3>
            <p className="text-sm text-[#94a3b8] font-mono">
              来源: {alert.source} &middot; {formatRelativeTime(alert.timestamp)}
            </p>
          </div>
        </div>
        <span
          className={clsx(
            'px-2 py-1 text-xs font-medium rounded-full font-mono',
            alert.status === 'new'
              ? 'bg-accent-cyan/20 text-accent-cyan'
              : alert.status === 'acknowledged'
              ? 'bg-warning-500/20 text-warning-400'
              : 'bg-soc-bg-tertiary text-[#94a3b8]'
          )}
        >
          {statusLabels[alert.status] || alert.status}
        </span>
      </div>

      <div className="flex items-center justify-between">
        <div className="text-sm">
          {alert.acknowledged_by && (
            <span className="text-[#94a3b8] font-mono">
              确认人: {alert.acknowledged_by}
              {alert.notes && ` (${alert.notes})`}
            </span>
          )}
        </div>
        <div className="flex gap-2">
          {alert.status === 'new' && (
            <button onClick={onAcknowledge} className="btn btn-secondary text-sm py-1 px-3 font-mono">
              确认
            </button>
          )}
          {alert.status !== 'resolved' && (
            <button onClick={onResolve} className="btn btn-primary text-sm py-1 px-3 font-mono">
              解决
            </button>
          )}
          <button onClick={onMarkFalsePositive} className="text-sm text-[#64748b] hover:text-[#94a3b8] font-mono">
            误报
          </button>
        </div>
      </div>
    </div>
  );
}
