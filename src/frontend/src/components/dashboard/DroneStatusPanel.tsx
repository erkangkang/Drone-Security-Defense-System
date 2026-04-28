import { HUDFrame } from '@/components/ui/HUDFrame';

interface DroneStatusPanelProps {
  drone: {
    latitude: number;
    longitude: number;
    altitude: number;
    speed: number;
    heading: number;
    status: 'normal' | 'warning' | 'threat';
  } | null;
}

const statusMap = {
  normal: { label: '正常', color: 'text-success-400', bg: 'bg-success-500/20' },
  warning: { label: '警告', color: 'text-warning-400', bg: 'bg-warning-500/20' },
  threat: { label: '威胁', color: 'text-danger-400', bg: 'bg-danger-500/20' },
};

const hudColorMap = {
  normal: 'cyan' as const,
  warning: 'amber' as const,
  threat: 'red' as const,
};

export function DroneStatusPanel({ drone }: DroneStatusPanelProps) {
  if (!drone) {
    return (
      <HUDFrame color="cyan">
        <div className="p-6">
          <h3 className="text-xs font-semibold text-[#e2e8f0] mb-3 font-orbitron tracking-wider uppercase">无人机状态</h3>
          <div className="text-center py-6 text-[#64748b] text-sm font-mono">无数据</div>
        </div>
      </HUDFrame>
    );
  }

  const status = statusMap[drone.status || 'normal'];

  return (
    <HUDFrame color={hudColorMap[drone.status || 'normal']}>
      <div className="p-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-semibold text-[#e2e8f0] font-orbitron tracking-wider uppercase">无人机状态</h3>
          <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${status.bg} ${status.color} font-mono`}>
            {status.label}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <StatusItem label="纬度" value={drone.latitude.toFixed(6)} />
          <StatusItem label="经度" value={drone.longitude.toFixed(6)} />
          <StatusItem label="高度" value={`${drone.altitude.toFixed(1)} m`} />
          <StatusItem label="速度" value={`${drone.speed.toFixed(1)} m/s`} />
          <StatusItem label="航向" value={`${drone.heading.toFixed(0)}°`} />
          <StatusItem label="状态" value={status.label} highlight={drone.status !== 'normal'} colorHint={drone.status} />
        </div>
      </div>
    </HUDFrame>
  );
}

function StatusItem({ label, value, highlight, colorHint }: { label: string; value: string; highlight?: boolean; colorHint?: string }) {
  const barColor = colorHint === 'threat' ? '#f43f5e' : colorHint === 'warning' ? '#fbbf24' : '#00E6A8';
  const valueTone = colorHint === 'threat' ? 'text-danger-400' : colorHint === 'warning' ? 'text-warning-400' : 'text-accent-cyan';
  return (
    <div className="bg-soc-bg-primary rounded px-3 py-2 relative overflow-hidden border border-soc-border/70">
      <div
        className="absolute left-0 top-0 bottom-0 w-0.5"
        style={{ backgroundColor: highlight ? barColor : 'rgba(0,230,168,0.14)' }}
      />
      <div className="text-[10px] text-[#64748b] font-orbitron tracking-wider uppercase">{label}</div>
      <div className={`text-sm font-medium font-mono ${highlight ? valueTone : 'text-[#e2e8f0]'}`}>
        {value}
      </div>
    </div>
  );
}
