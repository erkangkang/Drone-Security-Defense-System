import { clsx } from 'clsx';

interface HexPanelProps {
  children: React.ReactNode;
  className?: string;
  active?: boolean;
  color?: 'cyan' | 'green' | 'red' | 'amber';
}

const glowColorMap = {
  cyan: 'rgba(0, 230, 168, 0.36)',
  green: 'rgba(34, 197, 94, 0.36)',
  red: 'rgba(244, 63, 94, 0.38)',
  amber: 'rgba(251, 191, 36, 0.4)',
};

export function HexPanel({ children, className, active = false, color = 'cyan' }: HexPanelProps) {
  return (
    <div
      className={clsx(
        'hex-panel p-4 bg-soc-bg-secondary transition-all duration-300',
        active && 'ring-1',
        className
      )}
      style={{
        boxShadow: active ? `0 0 15px ${glowColorMap[color]}` : undefined,
      }}
    >
      {children}
    </div>
  );
}
