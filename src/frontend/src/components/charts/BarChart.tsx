import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import { CHART_THEME, getDefaultGrid, getDefaultTitle, getDefaultTooltip, getDefaultXAxis, getDefaultYAxis } from './chartTheme';

interface BarChartProps {
  data: Record<string, number>;
  title?: string;
  height?: number;
  color?: string;
  labels?: Record<string, string>;
  colors?: string[];
}

export function BarChart({
  data,
  title = '',
  height = 300,
  color = CHART_THEME.accentCyan,
  labels,
  colors,
}: BarChartProps) {
  const categories = Object.keys(data);
  const values = Object.values(data);
  const useMultiColor = !!colors && colors.length > 0;

  const seriesData = useMultiColor
    ? values.map((v, i) => {
        const c = `${colors![i % colors!.length]}`;
        return {
          value: v,
          itemStyle: {
            color: {
              type: 'linear' as const,
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: c },
                { offset: 1, color: `${c}aa` },
              ],
            },
            borderRadius: [4, 4, 0, 0] as [number, number, number, number],
            shadowBlur: 8,
            shadowColor: `${c}40`,
          },
        };
      })
    : values.map((v) => ({
        value: v,
        itemStyle: {
          color: {
            type: 'linear' as const,
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color },
              { offset: 1, color: `${color}aa` },
            ],
          },
          borderRadius: [4, 4, 0, 0] as [number, number, number, number],
          shadowBlur: 8,
          shadowColor: `${color}40`,
        },
      }));

  const option: EChartsOption = {
    backgroundColor: CHART_THEME.backgroundColor,
    title: title ? getDefaultTitle(title) : undefined,
    grid: getDefaultGrid(title),
    tooltip: {
      ...getDefaultTooltip(),
      axisPointer: { type: 'shadow' },
    },
    xAxis: {
      ...getDefaultXAxis(categories.map((c) => labels?.[c] || c)),
      axisLabel: {
        color: CHART_THEME.axisLabelColor,
        fontSize: 11,
        interval: 0,
        rotate: categories.length > 6 ? 45 : 0,
        fontFamily: 'Share Tech Mono',
      },
    },
    yAxis: getDefaultYAxis(),
    series: [
      {
        data: seriesData,
        type: 'bar',
        barWidth: '60%',
      },
    ],
  };

  return <ReactECharts option={option} style={{ height: `${height}px` }} />;
}
