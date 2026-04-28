import { useQuery } from '@tanstack/react-query';
import { Card } from '@/components/ui/Card';
import { systemApi } from '@/api/system';
import { useSystemStatus } from '@/hooks/useSystemStatus';
import { clsx } from 'clsx';

export function Settings() {
  const { systemStatus, isLoading: statusLoading, reloadConfig, isReloading } = useSystemStatus();

  const { data: info, isLoading: infoLoading, refetch: refetchInfo } = useQuery({
    queryKey: ['system', 'info'],
    queryFn: () => systemApi.getInfo(),
    refetchInterval: 60000,
  });

  const platform = info?.platform || systemStatus?.platform || 'unknown';
  const version = info?.version || 'unknown';

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[#e2e8f0] font-orbitron neon-text">系统配置</h1>
        <div className="flex items-center gap-2">
          <button className="btn-secondary px-3 py-2" onClick={() => refetchInfo()}>
            刷新信息
          </button>
          <button className={clsx('btn-primary px-3 py-2', isReloading && 'opacity-70')} onClick={() => reloadConfig()} disabled={isReloading}>
            {isReloading ? '重载中…' : '重载配置'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card variant="hud">
          <h3 className="text-xs font-semibold text-[#e2e8f0] mb-3 font-orbitron tracking-wider uppercase">系统信息</h3>
          <div className="space-y-2 text-sm">
            <Row label="服务" value="drone-security-defense" />
            <Row label="版本" value={version} />
            <Row label="平台" value={platform} />
            <Row label="状态" value={statusLoading ? 'LOADING' : systemStatus ? 'RUNNING' : 'UNKNOWN'} tone={systemStatus ? 'ok' : 'warn'} />
            <Row label="接口" value="/api" tone="muted" />
          </div>
          {(infoLoading || statusLoading) && <div className="mt-3 text-xs text-[#94a3b8] font-mono">正在获取信息…</div>}
        </Card>

        <Card variant="glass">
          <h3 className="text-xs font-semibold text-[#e2e8f0] mb-3 font-orbitron tracking-wider uppercase">组件清单</h3>
          <div className="space-y-3">
            <ListBlock title="Detectors" items={info?.detectors} />
            <ListBlock title="Handlers" items={info?.handlers} />
            <ListBlock title="Analyzers" items={info?.analyzers} />
          </div>
        </Card>

        <Card variant="hud">
          <h3 className="text-xs font-semibold text-[#e2e8f0] mb-3 font-orbitron tracking-wider uppercase">运维操作</h3>
          <div className="space-y-3 text-sm">
            <ActionLine
              title="配置热重载"
              desc="从服务端重新加载 YAML 配置（不重启进程）"
              buttonText={isReloading ? '执行中…' : '执行'}
              onClick={() => reloadConfig()}
              disabled={isReloading}
            />
            <ActionLine title="建议" desc="修改配置文件后，优先使用热重载；若变更未生效，再重启服务。" />
          </div>
        </Card>
      </div>
    </div>
  );
}

function Row({ label, value, tone = 'muted' }: { label: string; value: string; tone?: 'ok' | 'warn' | 'muted' }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-[#94a3b8] font-mono text-xs">{label}</span>
      <span
        className={clsx(
          'font-mono text-xs px-2 py-1 rounded border',
          tone === 'ok' && 'text-accent-green border-success-500/30 bg-success-500/10',
          tone === 'warn' && 'text-warning-300 border-warning-500/30 bg-warning-500/10',
          tone === 'muted' && 'text-[#e2e8f0] border-soc-border bg-soc-bg-secondary/70'
        )}
      >
        {value}
      </span>
    </div>
  );
}

function ListBlock({ title, items }: { title: string; items?: string[] }) {
  const list = Array.isArray(items) ? items : [];
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-[#94a3b8] font-mono">{title}</span>
        <span className="text-xs text-accent-cyan/80 font-mono">{list.length}</span>
      </div>
      <div className="rounded border border-soc-border bg-soc-bg-secondary/60 p-2 max-h-40 overflow-auto">
        {list.length === 0 ? (
          <div className="text-xs text-[#64748b] font-mono">暂无数据</div>
        ) : (
          <div className="space-y-1">
            {list.map((s) => (
              <div key={s} className="text-xs text-[#e2e8f0] font-mono truncate">
                {s}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ActionLine({
  title,
  desc,
  buttonText,
  onClick,
  disabled,
}: {
  title: string;
  desc: string;
  buttonText?: string;
  onClick?: () => void;
  disabled?: boolean;
}) {
  return (
    <div className="rounded border border-soc-border bg-soc-bg-secondary/50 p-3">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-sm text-[#e2e8f0] font-orbitron tracking-wide">{title}</div>
          <div className="text-xs text-[#94a3b8] mt-1">{desc}</div>
        </div>
        {buttonText && onClick && (
          <button className={clsx('btn-primary px-3 py-2 text-xs', disabled && 'opacity-70')} onClick={onClick} disabled={disabled}>
            {buttonText}
          </button>
        )}
      </div>
    </div>
  );
}
