import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import { CHART_THEME, getDefaultTitle } from './chartTheme';

interface PieChartProps {
  data: Record<string, number>;
  title?: string;
  height?: number;
  colors?: string[];
  labels?: Record<string, string>;
}

export function PieChart({
  data,
  title = '',
  height = 300,
  colors = [...CHART_THEME.chartColors],
  labels,
}: PieChartProps) {
  const seriesData = Object.entries(data).map(([name, value]) => ({
    name: labels?.[name] || name,
    value,
  }));

  const option: EChartsOption = {
    backgroundColor: CHART_THEME.backgroundColor,
    title: title ? { ...getDefaultTitle(title), left: 'center' } : undefined,
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
      backgroundColor: 'rgba(17, 24, 39, 0.95)',
      borderColor: CHART_THEME.borderColor,
      textStyle: { color: CHART_THEME.textColor },
    },
    legend: {
      orient: 'horizontal',
      bottom: 0,
      textStyle: {
        color: CHART_THEME.axisLabelColor,
        fontSize: 11,
      },
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 6,
          borderColor: CHART_THEME.cardBg,
          borderWidth: 2,
        },
        label: {
          show: false,
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 12,
            fontWeight: 'bold',
            color: CHART_THEME.textColor,
          },
        },
        labelLine: {
          show: false,
        },
        data: seriesData,
      },
    ],
    color: colors,
  };

  return <ReactECharts option={option} style={{ height: `${height}px` }} />;
}
