export const CHART_THEME = {
  textColor: '#e2e8f0',
  subTextColor: '#94a3b8',
  axisLineColor: '#1B2A2F',
  axisLabelColor: '#64748b',
  splitLineColor: 'rgba(27, 42, 47, 0.55)',
  backgroundColor: 'transparent',
  titleColor: '#e2e8f0',
  accentCyan: '#00E6A8',
  severityColors: {
    low: '#00E6A8',
    medium: '#fbbf24',
    high: '#f59e0b',
    critical: '#f43f5e',
  },
  chartColors: ['#00E6A8', '#22c55e', '#fbbf24', '#fb7185', '#a3e635', '#38bdf8'],
  cardBg: '#0C1113',
  borderColor: '#1B2A2F',
  glowColors: {
    cyan: 'rgba(0, 230, 168, 0.36)',
    green: 'rgba(34, 197, 94, 0.36)',
    amber: 'rgba(251, 191, 36, 0.4)',
    red: 'rgba(244, 63, 94, 0.38)',
  },
} as const;

export function getDefaultGrid(title?: string) {
  return {
    left: '3%',
    right: '4%',
    bottom: '3%',
    top: title ? '14%' : '6%',
    containLabel: true,
  };
}

export function getDefaultTitle(title: string) {
  return {
    text: title,
    textStyle: {
      color: CHART_THEME.titleColor,
      fontSize: 13,
      fontWeight: 600 as const,
      fontFamily: 'Orbitron',
      letterSpacing: 1,
    },
  };
}

export function getDefaultTooltip() {
  return {
    trigger: 'axis' as const,
    backgroundColor: 'rgba(12, 17, 19, 0.96)',
    borderColor: CHART_THEME.borderColor,
    textStyle: {
      color: CHART_THEME.textColor,
      fontFamily: 'Share Tech Mono',
    },
  };
}

export function getDefaultXAxis(categories: string[]) {
  return {
    type: 'category' as const,
    data: categories,
    axisLine: { lineStyle: { color: CHART_THEME.axisLineColor } },
    axisLabel: { color: CHART_THEME.axisLabelColor, fontSize: 11, fontFamily: 'Share Tech Mono' },
  };
}

export function getDefaultYAxis() {
  return {
    type: 'value' as const,
    axisLine: { lineStyle: { color: CHART_THEME.axisLineColor } },
    axisLabel: { color: CHART_THEME.axisLabelColor, fontSize: 11, fontFamily: 'Share Tech Mono' },
    splitLine: { lineStyle: { color: CHART_THEME.splitLineColor } },
  };
}
