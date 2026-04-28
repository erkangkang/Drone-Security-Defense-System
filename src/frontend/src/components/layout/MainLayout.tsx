import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import { useWSStore } from '@/store/websocketStore';
import { useDemoMode } from '@/hooks/useDemoData';

const navigation = [
  { name: '态势感知', href: '/dashboard', icon: DashboardIcon },
  { name: '态势大屏', href: '/screen', icon: ScreenIcon },
  { name: '态势地图', href: '/map', icon: MapIcon },
  { name: '告警管理', href: '/alerts', icon: BellIcon },
  { name: '威胁分析', href: '/threats', icon: ShieldIcon },
  { name: '检测器', href: '/detectors', icon: RadarIcon },
  { name: '统计分析', href: '/statistics', icon: ChartIcon },
  { name: '系统配置', href: '/settings', icon: SettingsIcon },
];

interface MainLayoutProps {
  children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const location = useLocation();
  const isScreen = location.pathname.startsWith('/screen');

  return (
    <div className="min-h-screen bg-soc-bg-primary grid-bg">
      {/* Header */}
      <header
        className={clsx(
          'border-b border-soc-border sticky top-0 z-50 backdrop-blur-sm',
          isScreen ? 'bg-soc-bg-secondary/90' : 'bg-soc-bg-secondary/85'
        )}
        style={{ boxShadow: '0 1px 0 rgba(0,230,168,0.12), 0 0 22px rgba(0,230,168,0.03)' }}
      >
        <div className={clsx('px-4 sm:px-6 lg:px-8', isScreen && 'px-3 sm:px-4 lg:px-6')}>
          <div className={clsx('flex items-center justify-between', isScreen ? 'h-12' : 'h-14')}>
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-2">
                <DroneLogo />
                <h1 className="text-lg font-bold text-accent-cyan tracking-wide font-orbitron neon-text">
                  无人机安全防御系统
                </h1>
              </div>
              <nav className="hidden md:flex gap-1">
                {navigation.map((item) => {
                  const isActive = location.pathname === item.href;
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={clsx(
                        'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all',
                        isActive
                          ? 'text-accent-cyan bg-accent-cyan/10 shadow-glow-cyan'
                          : 'text-[#94a3b8] hover:text-[#e2e8f0] hover:bg-soc-bg-tertiary'
                      )}
                    >
                      <item.icon active={isActive} />
                      {item.name}
                    </Link>
                  );
                })}
              </nav>
            </div>
            <div className="flex items-center gap-4">
              <DemoToggle />
              <ConnectionStatus />
              <SystemTime />
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className={clsx(isScreen ? 'px-3 sm:px-4 lg:px-6 py-3' : 'px-4 sm:px-6 lg:px-8 py-6')}>
        {children}
      </main>
    </div>
  );
}

function ConnectionStatus() {
  const connected = useWSStore((s) => s.connected);
  const connectionStatus = useWSStore((s) => s.connectionStatus);

  return (
    <div className="flex items-center gap-2">
      <span
        className={clsx(
          'h-2 w-2 rounded-full',
          connected
            ? 'bg-accent-green animate-pulse-glow shadow-[0_0_6px_#10b981]'
            : connectionStatus === 'connecting'
            ? 'bg-warning-400 animate-pulse'
            : 'bg-danger-400'
        )}
      />
      <span className="text-sm text-[#94a3b8] font-mono">
        {connected ? '已连接' : connectionStatus === 'connecting' ? '连接中...' : '未连接'}
      </span>
    </div>
  );
}

function DemoToggle() {
  const { enabled, toggle } = useDemoMode();

  return (
    <button
      onClick={toggle}
      className={clsx(
        'flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-medium transition-all border font-mono',
        enabled
          ? 'bg-accent-cyan/20 text-accent-cyan border-accent-cyan/30 shadow-glow-cyan'
          : 'bg-soc-bg-tertiary text-[#64748b] border-soc-border hover:text-[#94a3b8]'
      )}
    >
      <span className={clsx('h-1.5 w-1.5 rounded-full', enabled ? 'bg-accent-cyan animate-pulse-glow' : 'bg-[#64748b]')} />
      DEMO
    </button>
  );
}

function SystemTime() {
  const [time, setTime] = React.useState(new Date());

  React.useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="text-sm text-accent-cyan/70 font-mono neon-text" style={{ letterSpacing: '0.05em' }}>
      {time.toLocaleTimeString('zh-CN')}
    </div>
  );
}

// SVG Icon Components
function DroneLogo() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-accent-cyan" style={{ filter: 'drop-shadow(0 0 4px rgba(0,230,168,0.35))' }}>
      <path d="M12 2L4 6v4l8 4 8-4V6l-8-4z" stroke="currentColor" strokeWidth="1.5" fill="none"/>
      <path d="M4 10v4l8 4 8-4v-4" stroke="currentColor" strokeWidth="1.5" fill="none"/>
      <circle cx="12" cy="12" r="2" fill="currentColor"/>
      <path d="M5 6L2 4M19 6l3-2M5 18l-3 2M19 18l3 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}

function ScreenIcon({ active }: { active: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="2" y="3" width="12" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.5" fill={active ? 'currentColor' : 'none'} opacity={active ? 0.22 : 1}/>
      <path d="M6 13h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}

function DashboardIcon({ active }: { active: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="1" y="1" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.5" fill={active ? 'currentColor' : 'none'} opacity={active ? 0.3 : 1}/>
      <rect x="9" y="1" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.5" fill={active ? 'currentColor' : 'none'} opacity={active ? 0.3 : 1}/>
      <rect x="1" y="9" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.5" fill={active ? 'currentColor' : 'none'} opacity={active ? 0.3 : 1}/>
      <rect x="9" y="9" width="6" height="6" rx="1" stroke="currentColor" strokeWidth="1.5" fill={active ? 'currentColor' : 'none'} opacity={active ? 0.3 : 1}/>
    </svg>
  );
}

function MapIcon({ active }: { active: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M8 14s5-4.5 5-8A5 5 0 0 0 3 6c0 3.5 5 8 5 8z" stroke="currentColor" strokeWidth="1.5" fill={active ? 'currentColor' : 'none'} opacity={active ? 0.3 : 1}/>
      <circle cx="8" cy="6" r="2" stroke="currentColor" strokeWidth="1.5" fill={active ? 'currentColor' : 'none'}/>
    </svg>
  );
}

function BellIcon({ active }: { active: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M8 14a2 2 0 0 0 2-2H6a2 2 0 0 0 2 2z" fill="currentColor"/>
      <path d="M12 7V6a4 4 0 0 0-8 0v1l-1 3h10l-1-3z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" fill={active ? 'currentColor' : 'none'} opacity={active ? 0.3 : 1}/>
    </svg>
  );
}

function ShieldIcon({ active }: { active: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path d="M8 1L2 4v4c0 3.5 2.5 6.5 6 7.5 3.5-1 6-4 6-7.5V4L8 1z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" fill={active ? 'currentColor' : 'none'} opacity={active ? 0.3 : 1}/>
      <path d="M6 8l1.5 1.5L10 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function RadarIcon({ active }: { active: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5" opacity={active ? 0.9 : 1}/>
      <circle cx="8" cy="8" r="3" stroke="currentColor" strokeWidth="1.5" opacity={active ? 0.75 : 1}/>
      <circle cx="8" cy="8" r="1" fill={active ? 'currentColor' : 'none'} opacity={active ? 0.35 : 1}/>
      <line x1="8" y1="2" x2="8" y2="8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  );
}

function ChartIcon({ active }: { active: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <rect x="1" y="9" width="3" height="5" rx="0.5" stroke="currentColor" strokeWidth="1.5" fill={active ? 'currentColor' : 'none'} opacity={active ? 0.3 : 1}/>
      <rect x="6.5" y="5" width="3" height="9" rx="0.5" stroke="currentColor" strokeWidth="1.5" fill={active ? 'currentColor' : 'none'} opacity={active ? 0.3 : 1}/>
      <rect x="12" y="2" width="3" height="12" rx="0.5" stroke="currentColor" strokeWidth="1.5" fill={active ? 'currentColor' : 'none'} opacity={active ? 0.3 : 1}/>
    </svg>
  );
}

function SettingsIcon({ active }: { active: boolean }) {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
      <path
        d="M8 1.8l.9 1.6a1 1 0 0 0 .8.5l1.8.2-.9 1.6a1 1 0 0 0 0 1l.9 1.6-1.8.2a1 1 0 0 0-.8.5L8 13.9l-.9-1.6a1 1 0 0 0-.8-.5l-1.8-.2.9-1.6a1 1 0 0 0 0-1l-.9-1.6 1.8-.2a1 1 0 0 0 .8-.5L8 1.8z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
        fill={active ? 'currentColor' : 'none'}
        opacity={active ? 0.22 : 1}
      />
      <circle cx="8" cy="8" r="1.7" stroke="currentColor" strokeWidth="1.5" />
    </svg>
  );
}
