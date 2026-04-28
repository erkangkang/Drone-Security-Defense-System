import { useEffect, useRef } from 'react';
import { DroneMap } from '@/components/map';
import { HUDFrame } from '@/components/ui/HUDFrame';
import { Card } from '@/components/ui/Card';
import { useDemoDrones, useDemoThreats } from '@/hooks/useDemoData';
import { useWSStore } from '@/store/websocketStore';
import { useDemoStore } from '@/store/demoStore';
import { severityColors, severityLabels } from '@/types';
import { formatRelativeTime } from '@/utils/format';

export function MapPage() {
  const wsConnected = useWSStore((s) => s.connected);
  const demoEnabled = useDemoStore((s) => s.enabled);
  const useDemo = demoEnabled || !wsConnected;

  const drone = useDemoDrones();
  const threats = useDemoThreats();

  const currentDrone = drone.length > 0 ? drone[0] : null;
  const trailRef = useRef<Array<[number, number]>>([]);

  // Build trail from drone positions
  useEffect(() => {
    if (currentDrone) {
      trailRef.current = [
        ...trailRef.current.slice(-50),
        [currentDrone.latitude, currentDrone.longitude],
      ];
    }
  }, [currentDrone?.latitude, currentDrone?.longitude]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[#e2e8f0] font-orbitron neon-text">态势地图</h1>
        <div className="flex items-center gap-2">
          <span
            className={`h-2 w-2 rounded-full ${
              useDemo
                ? 'bg-accent-cyan animate-pulse-glow'
                : 'bg-accent-green animate-pulse-glow shadow-[0_0_6px_#10b981]'
            }`}
          />
          <span className="text-sm text-[#94a3b8] font-mono">
            {useDemo ? 'DEMO 数据' : '实时数据'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4" style={{ minHeight: 'calc(100vh - 200px)' }}>
        {/* Map - Takes 3 columns, wrapped in HUDFrame */}
        <div className="lg:col-span-3 overflow-hidden" style={{ minHeight: '500px' }}>
          <HUDFrame color="cyan" className="h-full">
            <DroneMap
              drone={currentDrone}
              threats={useDemo ? threats : []}
              trail={trailRef.current}
              className="w-full h-full rounded-lg"
            />
          </HUDFrame>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Drone Status */}
          <Card variant="glass">
            <h3 className="text-xs font-semibold text-[#e2e8f0] mb-3 font-orbitron tracking-wider uppercase">无人机状态</h3>
            {currentDrone ? (
              <div className="space-y-2">
                <InfoRow label="纬度" value={currentDrone.latitude.toFixed(6)} />
                <InfoRow label="经度" value={currentDrone.longitude.toFixed(6)} />
                <InfoRow label="高度" value={`${currentDrone.altitude.toFixed(1)} m`} />
                <InfoRow label="速度" value={`${currentDrone.speed.toFixed(1)} m/s`} />
                <InfoRow label="航向" value={`${currentDrone.heading.toFixed(0)}°`} />
                <div className="h-px bg-soc-border my-2" />
                <div className="flex items-center justify-between">
                  <span className="text-xs text-[#94a3b8] font-orbitron tracking-wider uppercase">状态</span>
                  <span className={`text-xs font-medium font-mono ${
                    currentDrone.status === 'normal' ? 'text-success-400' :
                    currentDrone.status === 'warning' ? 'text-warning-400' : 'text-danger-400'
                  }`}>
                    {currentDrone.status === 'normal' ? '正常' : currentDrone.status === 'warning' ? '警告' : '威胁'}
                  </span>
                </div>
              </div>
            ) : (
              <div className="text-center py-4 text-[#64748b] text-sm font-mono">无位置数据</div>
            )}
          </Card>

          {/* Threat List */}
          <Card variant="glass">
            <h3 className="text-xs font-semibold text-[#e2e8f0] mb-3 font-orbitron tracking-wider uppercase">
              威胁标记 ({threats.length})
            </h3>
            <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1 mask-fade-edges">
              {threats.length === 0 ? (
                <div className="text-center py-4 text-[#64748b] text-sm font-mono">暂无威胁</div>
              ) : (
                threats.slice(0, 20).map((threat) => (
                  <div
                    key={threat.threat_id}
                    className="p-2 rounded border border-soc-border bg-soc-bg-primary/80"
                    style={{ borderLeftWidth: '3px', borderLeftColor: severityColors[threat.severity] }}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-[#e2e8f0] font-mono">{threat.threat_type}</span>
                      <span className="text-[10px] font-mono" style={{ color: severityColors[threat.severity] }}>
                        {severityLabels[threat.severity]}
                      </span>
                    </div>
                    <div className="text-[10px] text-[#64748b] font-mono">
                      {formatRelativeTime(threat.timestamp)}
                    </div>
                  </div>
                ))
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-[#94a3b8] font-orbitron tracking-wider">{label}</span>
      <span className="text-xs font-medium text-[#e2e8f0] font-mono">{value}</span>
    </div>
  );
}
