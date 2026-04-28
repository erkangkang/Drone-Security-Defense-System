import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import { CHART_THEME } from '@/components/charts/chartTheme';

interface ThreatLevelGaugeProps {
  level: number; // 0-100
  height?: number;
}

export function ThreatLevelGauge({ level, height = 200 }: ThreatLevelGaugeProps) {
  const label =
    level < 25 ? '安全' : level < 50 ? '低风险' : level < 75 ? '中等风险' : '高危';
  const color =
    level < 25
      ? '#22c55e'
      : level < 50
      ? '#00E6A8'
      : level < 75
      ? '#fbbf24'
      : '#f43f5e';

  const option: EChartsOption = {
    backgroundColor: 'transparent',
    series: [
      {
        type: 'gauge',
        startAngle: 200,
        endAngle: -20,
        center: ['50%', '60%'],
        radius: '90%',
        min: 0,
        max: 100,
        splitNumber: 4,
        axisLine: {
          lineStyle: {
            width: 18,
            color: [
              [0.25, '#22c55e'],
              [0.5, '#00E6A8'],
              [0.75, '#fbbf24'],
              [1, '#f43f5e'],
            ],
            shadowBlur: 20,
            shadowColor: color,
            shadowOffsetY: 0,
          },
        },
        pointer: {
          itemStyle: {
            color: color,
            shadowBlur: 10,
            shadowColor: color,
          },
          width: 4,
          length: '60%',
        },
        axisTick: {
          show: false,
        },
        splitLine: {
          show: false,
        },
        axisLabel: {
          show: false,
        },
        detail: {
          valueAnimation: true,
          formatter: `{value}`,
          color: color,
          fontSize: 32,
          fontWeight: 'bold',
          fontFamily: 'Orbitron',
          offsetCenter: [0, '20%'],
          textShadowBlur: 15,
          textShadowColor: `${color}60`,
        },
        title: {
          offsetCenter: [0, '50%'],
          color: CHART_THEME.subTextColor,
          fontSize: 14,
          fontFamily: 'Share Tech Mono',
        },
        data: [{ value: level, name: label }],
      },
    ],
  };

  return <ReactECharts option={option} style={{ height: `${height}px` }} />;
}
