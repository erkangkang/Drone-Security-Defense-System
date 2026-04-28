interface RadarRingProps {
  size?: number;
  threatCount?: number;
}

export function RadarRing({ size = 200, threatCount = 0 }: RadarRingProps) {
  const center = size / 2;
  const radius = size / 2 - 4;

  // Generate threat dots at random positions within the ring
  const dots = Array.from({ length: Math.min(threatCount, 8) }, (_, i) => {
    const angle = (i * 137.5 * Math.PI) / 180; // golden angle distribution
    const r = radius * 0.4 * (0.3 + Math.random() * 0.6);
    return {
      cx: center + r * Math.cos(angle),
      cy: center + r * Math.sin(angle),
      key: i,
    };
  });

  return (
    <div
      className="relative"
      style={{ width: size, height: size }}
    >
      {/* Outer ring */}
      <svg width={size} height={size} className="absolute inset-0">
        {/* Concentric circles */}
        <circle cx={center} cy={center} r={radius} fill="none" stroke="rgba(0,230,168,0.12)" strokeWidth="1" />
        <circle cx={center} cy={center} r={radius * 0.66} fill="none" stroke="rgba(0,230,168,0.08)" strokeWidth="1" />
        <circle cx={center} cy={center} r={radius * 0.33} fill="none" stroke="rgba(0,230,168,0.08)" strokeWidth="1" />

        {/* Cross lines */}
        <line x1={center} y1={2} x2={center} y2={size - 2} stroke="rgba(0,230,168,0.06)" strokeWidth="1" />
        <line x1={2} y1={center} x2={size - 2} y2={center} stroke="rgba(0,230,168,0.06)" strokeWidth="1" />

        {/* Diagonal lines */}
        <line x1={center - radius * 0.7} y1={center - radius * 0.7} x2={center + radius * 0.7} y2={center + radius * 0.7} stroke="rgba(0,230,168,0.04)" strokeWidth="1" />
        <line x1={center + radius * 0.7} y1={center - radius * 0.7} x2={center - radius * 0.7} y2={center + radius * 0.7} stroke="rgba(0,230,168,0.04)" strokeWidth="1" />

        {/* Threat dots */}
        {dots.map((dot) => (
          <g key={dot.key}>
            <circle cx={dot.cx} cy={dot.cy} r="4" fill="rgba(244,63,94,0.82)" />
            <circle cx={dot.cx} cy={dot.cy} r="8" fill="none" stroke="rgba(244,63,94,0.32)" strokeWidth="1" className="animate-pulse-glow" />
          </g>
        ))}

        {/* Center dot */}
        <circle cx={center} cy={center} r="3" fill="rgba(0,230,168,0.82)" />
      </svg>

      {/* Scanning line - rotates via CSS animation */}
      <div
        className="absolute inset-0 animate-radar-sweep"
        style={{ width: size, height: size }}
      >
        <svg width={size} height={size}>
          <defs>
            <linearGradient id="sweepGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="rgba(0,230,168,0.4)" />
              <stop offset="100%" stopColor="rgba(0,230,168,0)" />
            </linearGradient>
          </defs>
          {/* Sweep line */}
          <line
            x1={center}
            y1={center}
            x2={center}
            y2={4}
            stroke="url(#sweepGrad)"
            strokeWidth="2"
          />
          {/* Sweep cone */}
          <path
            d={`M ${center} ${center} L ${center - radius * 0.15} ${4} A ${radius} ${radius} 0 0 1 ${center + radius * 0.15} ${4} Z`}
            fill="rgba(0,230,168,0.04)"
          />
        </svg>
      </div>
    </div>
  );
}
