import apiClient from './client';
import type { Alert } from '@/types';

export const alertsApi = {
  /**
   * 获取告警列表
   */
  getAlerts: async (params?: { limit?: number; status?: string; severity?: string }) => {
    const response = await apiClient.get<Alert[]>('/alerts/', { params });
    return response.data;
  },

  /**
   * 获取活跃告警
   */
  getActiveAlerts: async (limit = 50) => {
    const response = await apiClient.get<Alert[]>('/alerts/active', { params: { limit } });
    return response.data;
  },

  /**
   * 获取告警详情
   */
  getAlert: async (alertId: string) => {
    const response = await apiClient.get<Alert>(`/alerts/${alertId}`);
    return response.data;
  },

  /**
   * 确认告警
   */
  acknowledgeAlert: async (alertId: string, user = 'web', notes = '') => {
    const response = await apiClient.post(`/alerts/${alertId}/acknowledge`, { user, notes });
    return response.data;
  },

  /**
   * 解决告警
   */
  resolveAlert: async (alertId: string, user = 'web') => {
    const response = await apiClient.post(`/alerts/${alertId}/resolve`, { user });
    return response.data;
  },

  /**
   * 标记为误报
   */
  markFalsePositive: async (alertId: string, user = 'web') => {
    const response = await apiClient.post(`/alerts/${alertId}/false_positive`, { user });
    return response.data;
  },

  /**
   * 获取告警统计
   */
  getStatistics: async () => {
    const response = await apiClient.get('/alerts/statistics/summary');
    return response.data;
  },
};
