import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import { CHART_THEME } from '@/components/charts/chartTheme';

interface ThreatTimelineProps {
  data: Array<{
    timestamp: string;
    count: number;
    by_severity?: Record<string, number>;
  }>;
  height?: number;
}

export function ThreatTimeline({ data, height = 250 }: ThreatTimelineProps) {
  const categories = data.map((d) => {
    const date = new Date(d.timestamp);
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
  });

  const option: EChartsOption = {
    backgroundColor: CHART_THEME.backgroundColor,
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(12, 17, 19, 0.96)',
      borderColor: CHART_THEME.borderColor,
      textStyle: { color: CHART_THEME.textColor },
    },
    legend: {
      data: ['低', '中', '高', '严重'],
      bottom: 0,
      textStyle: { color: CHART_THEME.axisLabelColor, fontSize: 11, fontFamily: 'Share Tech Mono' },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '8%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLine: { lineStyle: { color: CHART_THEME.axisLineColor } },
      axisLabel: { color: CHART_THEME.axisLabelColor, fontSize: 10, fontFamily: 'Share Tech Mono' },
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: CHART_THEME.axisLineColor } },
      axisLabel: { color: CHART_THEME.axisLabelColor, fontSize: 10, fontFamily: 'Share Tech Mono' },
      splitLine: { lineStyle: { color: CHART_THEME.splitLineColor } },
    },
    series: [
      {
        name: '严重',
        type: 'line',
        stack: 'total',
        areaStyle: { color: 'rgba(244, 63, 94, 0.28)' },
        lineStyle: { color: '#f43f5e', width: 1.5, shadowBlur: 8, shadowColor: 'rgba(244,63,94,0.38)' },
        itemStyle: { color: '#f43f5e' },
        data: data.map((d) => d.by_severity?.critical || 0),
        smooth: true,
        symbol: 'none',
      },
      {
        name: '高',
        type: 'line',
        stack: 'total',
        areaStyle: { color: 'rgba(245, 158, 11, 0.25)' },
        lineStyle: { color: '#f59e0b', width: 1.5, shadowBlur: 8, shadowColor: 'rgba(245,158,11,0.35)' },
        itemStyle: { color: '#f59e0b' },
        data: data.map((d) => d.by_severity?.high || 0),
        smooth: true,
        symbol: 'none',
      },
      {
        name: '中',
        type: 'line',
        stack: 'total',
        areaStyle: { color: 'rgba(251, 191, 36, 0.3)' },
        lineStyle: { color: '#fbbf24', width: 1.5, shadowBlur: 8, shadowColor: 'rgba(251,191,36,0.4)' },
        itemStyle: { color: '#fbbf24' },
        data: data.map((d) => d.by_severity?.medium || 0),
        smooth: true,
        symbol: 'none',
      },
      {
        name: '低',
        type: 'line',
        stack: 'total',
        areaStyle: { color: 'rgba(0, 230, 168, 0.18)' },
        lineStyle: { color: '#00E6A8', width: 1.5, shadowBlur: 8, shadowColor: 'rgba(0,230,168,0.32)' },
        itemStyle: { color: '#00E6A8' },
        data: data.map((d) => d.by_severity?.low || 0),
        smooth: true,
        symbol: 'none',
      },
    ],
  };

  return <ReactECharts option={option} style={{ height: `${height}px` }} />;
}
