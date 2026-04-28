import apiClient from './client';
import type { Statistics, TrafficDataPoint } from '@/types';

export const statisticsApi = {
  /**
   * 获取统计数据
   */
  getStatistics: async (hours = 24) => {
    const response = await apiClient.get<Statistics>('/statistics/', { params: { hours } });
    return response.data;
  },

  /**
   * 获取流量趋势
   */
  getTrafficTrends: async (hours = 24) => {
    const response = await apiClient.get<{
      time_series: TrafficDataPoint[];
      total_events: number;
      peak_hour: TrafficDataPoint | null;
    }>('/statistics/traffic', { params: { hours } });
    return response.data;
  },

  /**
   * 获取威胁统计
   */
  getThreatStatistics: async () => {
    const response = await apiClient.get('/statistics/threats');
    return response.data;
  },

  /**
   * 获取仪表盘数据
   */
  getDashboardData: async () => {
    const response = await apiClient.get('/statistics/dashboard');
    return response.data;
  },

  /**
   * 获取时间线数据
   */
  getTimelineData: async (hours = 24, eventType?: string) => {
    const response = await apiClient.get('/statistics/timeline', {
      params: { hours, event_type: eventType },
    });
    return response.data;
  },
};
