import { clsx } from 'clsx';

interface DetectorGridProps {
  detectors: Array<{
    name: string;
    running: boolean;
    type: string;
    stats: Record<string, unknown>;
  }>;
}

export function DetectorGrid({ detectors }: DetectorGridProps) {
  return (
    <div className="space-y-2">
      <h3 className="text-xs font-semibold text-[#e2e8f0] mb-3 font-orbitron tracking-wider uppercase">检测器状态</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {detectors.map((det) => (
          <DetectorTile key={det.name} detector={det} />
        ))}
      </div>
    </div>
  );
}

function DetectorTile({ detector }: { detector: DetectorGridProps['detectors'][0] }) {
  const threats = (detector.stats?.threats_detected as number) || 0;

  return (
    <div
      className={clsx(
        'flex items-center justify-between p-3 rounded-lg border transition-all relative overflow-hidden',
        detector.running
          ? 'border-accent-cyan/20 bg-accent-cyan/5'
          : 'border-soc-border bg-soc-bg-primary'
      )}
    >
      {/* Running indicator top line */}
      {detector.running && (
        <div
          className="absolute top-0 left-0 right-0 h-px"
          style={{ background: 'linear-gradient(90deg, transparent, rgba(0,230,168,0.35), transparent)' }}
        />
      )}

      <div className="flex items-center gap-3">
        <span
          className={clsx(
            'h-2 w-2 rounded-full',
            detector.running
              ? 'bg-success-400 animate-pulse-glow shadow-[0_0_6px_#22c55e]'
              : 'bg-[#64748b]'
          )}
        />
        <span className="text-sm text-[#e2e8f0] capitalize font-mono">{detector.type}</span>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-xs text-[#64748b] font-mono">
          威胁: <span className={threats > 0 ? 'text-danger-400 font-medium neon-text-red' : 'text-[#94a3b8]'}>{threats}</span>
        </span>
        <span
          className={clsx(
            'text-xs font-mono',
            detector.running ? 'text-success-400' : 'text-[#64748b]'
          )}
        >
          {detector.running ? '运行' : '停止'}
        </span>
      </div>
    </div>
  );
}
