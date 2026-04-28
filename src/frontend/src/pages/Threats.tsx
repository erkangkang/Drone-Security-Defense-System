import { useState } from 'react';
import { useThreats } from '@/hooks/useThreats';
import { Card } from '@/components/ui/Card';
import { PieChart, BarChart } from '@/components/charts';
import { formatDateTime } from '@/utils/format';
import { severityColors, severityLabels } from '@/types';

export function Threats() {
  const [filter, setFilter] = useState<{ severity?: string }>({});
  const { threats, isLoading } = useThreats({ ...filter, limit: 100 });

  const threatCounts = threats.reduce(
    (acc, threat) => {
      acc[threat.threat_type] = (acc[threat.threat_type] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  const severityCounts = threats.reduce(
    (acc, threat) => {
      acc[threat.severity] = (acc[threat.severity] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[#e2e8f0] font-orbitron neon-text">威胁分析</h1>

      {/* Filters */}
      <Card variant="glass">
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <label className="text-xs text-[#94a3b8] font-orbitron tracking-wider">严重程度:</label>
            <select
              className="input w-auto font-mono"
              value={filter.severity || ''}
              onChange={(e) => setFilter({ severity: e.target.value || undefined })}
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

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <PieChart
            data={threatCounts}
            title="威胁类型分布"
            height={280}
          />
        </Card>
        <Card>
          <BarChart
            data={severityCounts}
            title="严重程度分布"
            height={280}
            colors={['#00E6A8', '#fbbf24', '#f59e0b', '#f43f5e']}
            labels={severityLabels}
          />
        </Card>
      </div>

      {/* Threat List */}
      <Card>
        <h2 className="text-lg font-semibold text-[#e2e8f0] mb-4 font-orbitron tracking-wider">
          威胁事件 ({threats.length})
        </h2>
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
            {threats.length === 0 ? (
              <div className="text-center py-8 text-[#64748b] font-mono">暂无威胁事件</div>
            ) : (
              threats.map((threat) => (
                <ThreatListItem key={threat.event_id} threat={threat} />
              ))
            )}
          </div>
        )}
      </Card>
    </div>
  );
}

interface ThreatListItemProps {
  threat: {
    event_id: string;
    threat_type: string;
    severity: string;
    detector: string;
    source: string;
    confidence: number;
    timestamp: string;
    evidence?: Record<string, unknown>;
  };
}

function ThreatListItem({ threat }: ThreatListItemProps) {
  const severityColor = severityColors[threat.severity] || '#64748b';

  return (
    <div
      className="p-4 border border-soc-border rounded-lg hover:bg-soc-bg-tertiary/70 transition-colors relative overflow-hidden"
      style={{ borderLeftWidth: '3px', borderLeftColor: severityColor }}
    >
      <div
        className="absolute top-0 left-0 right-0 h-px"
        style={{ background: `linear-gradient(90deg, transparent, ${severityColor}40, transparent)` }}
      />

      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <span
            className="h-3 w-3 rounded-full"
            style={{ backgroundColor: severityColor, boxShadow: `0 0 6px ${severityColor}` }}
          />
          <div>
            <h3 className="font-medium text-[#e2e8f0] font-mono">{threat.threat_type}</h3>
            <p className="text-sm text-[#94a3b8] font-mono">
              检测器: {threat.detector} &middot; 来源: {threat.source}
            </p>
          </div>
        </div>
        <div className="text-right">
          <span
            className="text-sm font-medium font-mono"
            style={{ color: severityColor }}
          >
            {severityLabels[threat.severity] || threat.severity}
          </span>
          <p className="text-xs text-[#64748b] font-mono">{formatDateTime(threat.timestamp)}</p>
        </div>
      </div>

      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-4">
          <span className="text-[#94a3b8] font-mono">
            置信度: <span className="text-accent-cyan neon-text">{(threat.confidence * 100).toFixed(0)}%</span>
          </span>
        </div>
        <button className="text-accent-cyan hover:text-accent-cyan/80 font-medium font-mono text-sm">
          查看详情
        </button>
      </div>

      {threat.evidence && Object.keys(threat.evidence).length > 0 && (
        <details className="mt-3">
          <summary className="text-sm text-[#64748b] cursor-pointer hover:text-[#94a3b8] font-mono">
            证据
          </summary>
          <pre className="mt-2 text-xs bg-soc-bg-primary p-3 rounded border border-soc-border overflow-auto max-h-32 font-mono">
            {JSON.stringify(threat.evidence, null, 2)}
          </pre>
        </details>
      )}
    </div>
  );
}
