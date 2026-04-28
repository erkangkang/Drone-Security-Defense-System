import { useState } from 'react';
import { useStatistics, useTrafficTrends } from '@/hooks/useStatistics';
import { Card } from '@/components/ui/Card';
import { LineChart, PieChart, BarChart } from '@/components/charts';
import { severityLabels } from '@/types';

export function Statistics() {
  const [hours, setHours] = useState(24);
  const { statistics } = useStatistics(hours);
  const { trafficData } = useTrafficTrends(hours);

  const lineChartData = trafficData?.time_series || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[#e2e8f0] font-orbitron neon-text">统计分析</h1>
        <div className="flex items-center gap-2">
          <label className="text-xs text-[#94a3b8] font-orbitron tracking-wider">时间范围:</label>
          <select
            className="input w-auto font-mono"
            value={hours}
            onChange={(e) => setHours(Number(e.target.value))}
          >
            <option value={1}>1小时</option>
            <option value={6}>6小时</option>
            <option value={24}>24小时</option>
            <option value={48}>48小时</option>
            <option value={168}>7天</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card glow="cyan" variant="glass">
          <div className="text-center">
            <div className="text-3xl font-bold text-accent-cyan font-mono neon-text">
              {statistics?.total_alerts || 0}
            </div>
            <div className="text-xs text-[#94a3b8] font-orbitron tracking-wider mt-1">总告警数</div>
          </div>
        </Card>
        <Card glow="red" variant="glass">
          <div className="text-center">
            <div className="text-3xl font-bold text-danger-400 font-mono neon-text-red">
              {statistics?.active_alerts || 0}
            </div>
            <div className="text-xs text-[#94a3b8] font-orbitron tracking-wider mt-1">活跃告警</div>
          </div>
        </Card>
        <Card variant="glass">
          <div className="text-center">
            <div className="text-3xl font-bold text-[#e2e8f0] font-mono">
              {statistics?.total_threats || 0}
            </div>
            <div className="text-xs text-[#94a3b8] font-orbitron tracking-wider mt-1">总威胁数</div>
          </div>
        </Card>
        <Card variant="glass">
          <div className="text-center">
            <div className="text-3xl font-bold text-[#e2e8f0] font-mono">
              {trafficData?.total_events || 0}
            </div>
            <div className="text-xs text-[#94a3b8] font-orbitron tracking-wider mt-1">事件总数</div>
          </div>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <LineChart
            data={lineChartData.map((d) => ({
              timestamp: d.timestamp,
              value: d.count,
            }))}
            title="流量趋势"
            height={300}
          />
        </Card>

        <Card>
          <PieChart
            data={statistics?.threats_by_type || {}}
            title="威胁类型分布"
            height={300}
          />
        </Card>

        <Card>
          <BarChart
            data={statistics?.alerts_by_severity || {}}
            title="告警严重程度分布"
            height={300}
            colors={['#00E6A8', '#fbbf24', '#f59e0b', '#f43f5e']}
            labels={severityLabels}
          />
        </Card>

        <Card>
          <BarChart
            data={Object.entries(statistics?.detector_stats || {})
              .filter(([_, stats]) => typeof stats === 'object' && stats !== null && 'threats_detected' in stats)
              .reduce((acc, [name, stats]) => {
                acc[name] = (stats as { threats_detected: number }).threats_detected;
                return acc;
              }, {} as Record<string, number>)}
            title="检测器威胁检测分布"
            height={300}
          />
        </Card>
      </div>
    </div>
  );
}
