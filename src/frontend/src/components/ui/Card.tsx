import { clsx } from 'clsx';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  glow?: 'cyan' | 'green' | 'red' | 'amber' | 'none';
  variant?: 'default' | 'glass' | 'hud';
}

const glowMap = {
  cyan: 'border-accent-cyan/30 shadow-glow-cyan',
  green: 'border-success-500/30 shadow-glow-green',
  red: 'border-danger-500/30 shadow-glow-red',
  amber: 'border-warning-500/30 shadow-glow-amber',
  none: '',
};

const variantMap = {
  default: 'rounded-lg border border-soc-border bg-soc-bg-secondary',
  glass: 'glass rounded-lg',
  hud: 'hud-frame rounded-lg bg-soc-bg-secondary',
};

export function Card({ children, className, glow = 'none', variant = 'default' }: CardProps) {
  return (
    <div
      className={clsx(
        'p-4 lg:p-5',
        variantMap[variant],
        glow !== 'none' && glowMap[glow],
        className
      )}
    >
      {children}
    </div>
  );
}
