import { clsx } from 'clsx';

interface MetricCardProps {
  title: string;
  value: number | string;
  icon?: React.ReactNode;
  color?: 'cyan' | 'green' | 'red' | 'amber' | 'default';
  suffix?: string;
}

const colorMap = {
  cyan: { text: 'text-accent-cyan', border: 'border-accent-cyan/30', glow: 'shadow-glow-cyan', bg: 'bg-accent-cyan/10', topLine: 'rgba(0,230,168,0.5)' },
  green: { text: 'text-accent-green', border: 'border-success-500/30', glow: 'shadow-glow-green', bg: 'bg-success-500/10', topLine: 'rgba(34,197,94,0.5)' },
  red: { text: 'text-danger-400', border: 'border-danger-500/30', glow: 'shadow-glow-red', bg: 'bg-danger-500/10', topLine: 'rgba(244,63,94,0.5)' },
  amber: { text: 'text-warning-400', border: 'border-warning-500/30', glow: 'shadow-glow-amber', bg: 'bg-warning-500/10', topLine: 'rgba(251,191,36,0.5)' },
  default: { text: 'text-[#e2e8f0]', border: 'border-soc-border', glow: '', bg: 'bg-soc-bg-secondary/80', topLine: 'rgba(0,230,168,0.2)' },
};

export function MetricCard({ title, value, icon, color = 'default', suffix }: MetricCardProps) {
  const c = colorMap[color];

  return (
    <div
      className={clsx(
        'rounded-lg border bg-soc-bg-secondary p-4 transition-all relative overflow-hidden',
        c.border,
        c.glow
      )}
    >
      {/* Top accent line */}
      <div
        className="absolute top-0 left-0 right-0 h-px"
        style={{ background: `linear-gradient(90deg, transparent, ${c.topLine}, transparent)` }}
      />

      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-[#94a3b8] font-orbitron tracking-wider uppercase">{title}</span>
        {icon && <span className={c.text}>{icon}</span>}
      </div>
      <div className="flex items-baseline gap-1">
        <span className={clsx('text-3xl font-bold font-mono', c.text)} style={{ textShadow: `0 0 10px ${c.topLine.replace('0.5', '0.3')}` }}>
          {value}
        </span>
        {suffix && <span className="text-sm text-[#64748b] font-mono">{suffix}</span>}
      </div>
    </div>
  );
}
