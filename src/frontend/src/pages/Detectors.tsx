import { useDetectors, useDetectorActions } from '@/hooks/useDetectors';
import { Card } from '@/components/ui/Card';
import { clsx } from 'clsx';

export function Detectors() {
  const { detectors, isLoading } = useDetectors();
  const { startDetector, stopDetector, isStarting, isStopping } = useDetectorActions();

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[#e2e8f0] font-orbitron neon-text">检测器管理</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {isLoading ? (
          [...Array(6)].map((_, i) => (
            <Card key={i}>
              <div className="animate-pulse">
                <div className="h-4 bg-soc-bg-tertiary rounded w-1/3 mb-4" />
                <div className="space-y-2">
                  <div className="h-3 bg-soc-bg-tertiary rounded" />
                  <div className="h-3 bg-soc-bg-tertiary rounded" />
                </div>
              </div>
            </Card>
          ))
        ) : (
          detectors.map((detector) => (
            <DetectorCard
              key={detector.name}
              detector={detector}
              onStart={() => startDetector(detector.name)}
              onStop={() => stopDetector(detector.name)}
              isStarting={isStarting}
              isStopping={isStopping}
            />
          ))
        )}
      </div>
    </div>
  );
}

interface DetectorCardProps {
  detector: {
    name: string;
    running: boolean;
    enabled: boolean;
    type: string;
    stats: Record<string, unknown>;
  };
  onStart: () => void;
  onStop: () => void;
  isStarting: boolean;
  isStopping: boolean;
}

function DetectorCard({ detector, onStart, onStop, isStarting, isStopping }: DetectorCardProps) {
  const stats = detector.stats || {};

  return (
    <Card glow={detector.running ? 'cyan' : 'none'} variant="hud">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-[#e2e8f0] capitalize font-mono">{detector.name}</h3>
        <span
          className={clsx(
            'px-2 py-1 text-xs font-medium rounded-full font-mono',
            detector.running
              ? 'bg-success-500/20 text-success-400'
              : 'bg-soc-bg-tertiary text-[#94a3b8]'
          )}
        >
          {detector.running ? '运行中' : '已停止'}
        </span>
      </div>

      <div className="space-y-3 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-[#94a3b8] font-orbitron tracking-wider text-xs">类型</span>
          <span className="font-medium text-[#e2e8f0] capitalize font-mono">{detector.type}</span>
        </div>

        {stats.events_processed !== undefined && (
          <div className="flex justify-between text-sm">
            <span className="text-[#94a3b8] font-orbitron tracking-wider text-xs">处理事件</span>
            <span className="font-medium text-accent-cyan font-mono">{String(stats.events_processed)}</span>
          </div>
        )}

        {stats.threats_detected !== undefined && (
          <div className="flex justify-between text-sm">
            <span className="text-[#94a3b8] font-orbitron tracking-wider text-xs">检测威胁</span>
            <span className="font-medium text-danger-400 font-mono">{String(stats.threats_detected)}</span>
          </div>
        )}

        {stats.last_activity !== undefined && (
          <div className="flex justify-between text-sm">
            <span className="text-[#94a3b8] font-orbitron tracking-wider text-xs">最后活动</span>
            <span className="font-medium text-[#e2e8f0] font-mono">
              {new Date(String(stats.last_activity)).toLocaleTimeString()}
            </span>
          </div>
        )}
      </div>

      <div className="flex gap-2">
        {detector.running ? (
          <button
            onClick={onStop}
            disabled={isStopping}
            className={clsx(
              'btn flex-1 font-mono',
              isStopping ? 'bg-soc-bg-tertiary text-[#94a3b8]' : 'btn-danger'
            )}
          >
            {isStopping ? '停止中...' : '停止'}
          </button>
        ) : (
          <button
            onClick={onStart}
            disabled={isStarting}
            className={clsx(
              'btn flex-1 font-mono',
              isStarting ? 'bg-soc-bg-tertiary text-[#94a3b8]' : 'btn-success'
            )}
          >
            {isStarting ? '启动中...' : '启动'}
          </button>
        )}
      </div>
    </Card>
  );
}
