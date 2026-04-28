import { Card } from '@/components/ui/Card';
import { formatRelativeTime } from '@/utils/format';
import { severityColors, severityLabels } from '@/types';
import { clsx } from 'clsx';

interface AlertFeedEnhancedProps {
  alerts: Array<{
    alert_id: string;
    threat_type: string;
    severity: string;
    status: string;
    source: string;
    timestamp: string;
  }>;
}

export function AlertFeedEnhanced({ alerts }: AlertFeedEnhancedProps) {
  return (
    <Card>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-semibold text-[#e2e8f0] font-orbitron tracking-wider uppercase">实时告警</h3>
        <span className="text-xs text-accent-cyan font-mono">{alerts.length} 条</span>
      </div>

      <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1 mask-fade-edges">
        {alerts.length === 0 ? (
          <div className="text-center py-6 text-[#64748b] text-sm font-mono">暂无告警</div>
        ) : (
          alerts.map((alert) => {
            const severityColor = severityColors[alert.severity] || '#64748b';
            const isCritical = alert.severity === 'critical';
            return (
              <div
                key={alert.alert_id}
                className={clsx(
                  'p-2.5 rounded border border-soc-border bg-soc-bg-primary/80 hover:bg-soc-bg-tertiary/70 transition-colors',
                  isCritical && 'animate-pulse-glow'
                )}
                style={{ borderLeftWidth: '3px', borderLeftColor: severityColor }}
              >
                <div className="flex items-start justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span
                      className="h-1.5 w-1.5 rounded-full"
                      style={{ backgroundColor: severityColor, boxShadow: `0 0 6px ${severityColor}` }}
                    />
                    <span className="text-xs font-medium text-[#e2e8f0] truncate max-w-[140px] font-mono">
                      {alert.threat_type}
                    </span>
                  </div>
                  <span className="text-[10px] text-[#64748b] whitespace-nowrap font-mono">
                    {formatRelativeTime(alert.timestamp)}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-[10px]">
                  <span className="text-[#64748b] font-mono">{alert.source}</span>
                  <span style={{ color: severityColor }} className="font-mono">
                    {severityLabels[alert.severity] || alert.severity}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </Card>
  );
}
