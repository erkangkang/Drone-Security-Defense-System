import { useThreatDistribution } from '@/hooks/useThreats';
import { Card } from '@/components/ui/Card';
import { severityColors, severityLabels } from '@/types';

export function ThreatOverview() {
  const { distribution, isLoading } = useThreatDistribution();

  if (isLoading || !distribution) {
    return (
      <Card>
        <div className="animate-pulse">
          <div className="h-4 bg-soc-bg-tertiary rounded w-1/4 mb-4" />
          <div className="space-y-2">
            <div className="h-3 bg-soc-bg-tertiary rounded" />
            <div className="h-3 bg-soc-bg-tertiary rounded" />
          </div>
        </div>
      </Card>
    );
  }

  const threatsByType = distribution.by_type || {};
  const threatsBySeverity = distribution.by_severity || {};

  return (
    <Card>
      <h2 className="text-lg font-semibold text-[#e2e8f0] mb-4">威胁概览</h2>

      <div className="space-y-4">
        {/* 按类型分布 */}
        <div>
          <h3 className="text-sm font-medium text-[#94a3b8] mb-2">威胁类型</h3>
          <div className="space-y-2">
            {Object.entries(threatsByType).map(([type, count]) => (
              <div key={type} className="flex items-center justify-between">
                <span className="text-sm text-[#94a3b8]">{type}</span>
                <span className="text-sm font-medium text-[#e2e8f0]">{count as number}</span>
              </div>
            ))}
            {Object.keys(threatsByType).length === 0 && (
              <div className="text-sm text-[#64748b] text-center py-2">暂无威胁数据</div>
            )}
          </div>
        </div>

        <div className="h-px bg-soc-border" />

        {/* 按严重程度分布 */}
        <div>
          <h3 className="text-sm font-medium text-[#94a3b8] mb-2">严重程度</h3>
          <div className="space-y-2">
            {Object.entries(threatsBySeverity)
              .sort(([, a], [, b]) => (b as number) - (a as number))
              .map(([severity, count]) => (
                <div key={severity} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span
                      className="h-3 w-3 rounded-full"
                      style={{ backgroundColor: severityColors[severity] }}
                    />
                    <span className="text-sm text-[#94a3b8]">
                      {severityLabels[severity] || severity}
                    </span>
                  </div>
                  <span className="text-sm font-medium text-[#e2e8f0]">{count as number}</span>
                </div>
              ))}
            {Object.keys(threatsBySeverity).length === 0 && (
              <div className="text-sm text-[#64748b] text-center py-2">暂无威胁数据</div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
