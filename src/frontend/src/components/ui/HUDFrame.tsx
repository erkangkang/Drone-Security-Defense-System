import { clsx } from 'clsx';

interface HUDFrameProps {
  children: React.ReactNode;
  className?: string;
  color?: 'cyan' | 'green' | 'red' | 'amber';
}

const colorMap = {
  cyan: 'border-[rgba(0,230,168,0.3)]',
  green: 'border-[rgba(34,197,94,0.3)]',
  red: 'border-[rgba(244,63,94,0.3)]',
  amber: 'border-[rgba(251,191,36,0.3)]',
};

const cornerColorMap = {
  cyan: 'rgba(0, 230, 168, 0.6)',
  green: 'rgba(34, 197, 94, 0.6)',
  red: 'rgba(244, 63, 94, 0.6)',
  amber: 'rgba(251, 191, 36, 0.6)',
};

export function HUDFrame({ children, className, color = 'cyan' }: HUDFrameProps) {
  const c = cornerColorMap[color];

  return (
    <div
      className={clsx('relative border rounded-lg', colorMap[color], className)}
      style={{
        boxShadow: `inset 0 0 20px ${c.replace('0.6', '0.05')}`,
      }}
    >
      {/* Top-left corner */}
      <div
        className="absolute top-0 left-0 w-3 h-3 pointer-events-none"
        style={{ borderTop: `2px solid ${c}`, borderLeft: `2px solid ${c}` }}
      />
      {/* Top-right corner */}
      <div
        className="absolute top-0 right-0 w-3 h-3 pointer-events-none"
        style={{ borderTop: `2px solid ${c}`, borderRight: `2px solid ${c}` }}
      />
      {/* Bottom-left corner */}
      <div
        className="absolute bottom-0 left-0 w-3 h-3 pointer-events-none"
        style={{ borderBottom: `2px solid ${c}`, borderLeft: `2px solid ${c}` }}
      />
      {/* Bottom-right corner */}
      <div
        className="absolute bottom-0 right-0 w-3 h-3 pointer-events-none"
        style={{ borderBottom: `2px solid ${c}`, borderRight: `2px solid ${c}` }}
      />

      {/* Top glow line */}
      <div
        className="absolute top-0 left-3 right-3 h-px pointer-events-none"
        style={{
          background: `linear-gradient(90deg, transparent, ${c.replace('0.6', '0.3')}, transparent)`,
        }}
      />

      {children}
    </div>
  );
}
