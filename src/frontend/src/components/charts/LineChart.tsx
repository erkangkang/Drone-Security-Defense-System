import { useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';
import { CHART_THEME, getDefaultGrid, getDefaultTitle, getDefaultTooltip, getDefaultXAxis, getDefaultYAxis } from './chartTheme';

interface LineChartProps {
  data: Array<{ timestamp: string; value: number; [key: string]: unknown }>;
  title?: string;
  height?: number;
  valueKey?: string;
  color?: string;
}

export function LineChart({
  data,
  title = '',
  height = 300,
  valueKey = 'value',
  color = CHART_THEME.accentCyan,
}: LineChartProps) {
  const chartRef = useRef<ReactECharts>(null);

  const option: EChartsOption = {
    backgroundColor: CHART_THEME.backgroundColor,
    title: title ? getDefaultTitle(title) : undefined,
    grid: getDefaultGrid(title),
    tooltip: {
      ...getDefaultTooltip(),
    },
    xAxis: {
      ...getDefaultXAxis(
        data.map((d) => {
          const date = new Date(d.timestamp);
          return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
        })
      ),
    },
    yAxis: getDefaultYAxis(),
    series: [
      {
        data: data.map((d) => d[valueKey as keyof typeof d] as number),
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: {
          color,
          width: 2,
          shadowBlur: 10,
          shadowColor: `${color}60`,
          shadowOffsetY: 4,
        },
        itemStyle: {
          color,
          shadowBlur: 6,
          shadowColor: `${color}80`,
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: `${color}30` },
              { offset: 1, color: `${color}05` },
            ],
          },
        },
      },
    ],
  };

  return <ReactECharts ref={chartRef} option={option} style={{ height: `${height}px` }} />;
}
