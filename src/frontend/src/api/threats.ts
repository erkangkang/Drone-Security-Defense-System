import apiClient from './client';
import type { Threat } from '@/types';

export const threatsApi = {
  /**
   * 获取威胁列表
   */
  getThreats: async (params?: { limit?: number; threat_type?: string; severity?: string }) => {
    const response = await apiClient.get<Threat[]>('/threats/', { params });
    return response.data;
  },

  /**
   * 获取威胁时间线
   */
  getTimeline: async (limit = 100) => {
    const response = await apiClient.get<{ events: Threat[]; total: number }>('/threats/timeline', {
      params: { limit },
    });
    return response.data;
  },

  /**
   * 获取威胁类型
   */
  getTypes: async () => {
    const response = await apiClient.get<{ types: string[]; distribution: Record<string, number> }>('/threats/types');
    return response.data;
  },

  /**
   * 获取威胁分布
   */
  getDistribution: async () => {
    const response = await apiClient.get('/threats/distribution');
    return response.data;
  },

  /**
   * 获取威胁详情
   */
  getThreat: async (eventId: string) => {
    const response = await apiClient.get<Threat>(`/threats/${eventId}`);
    return response.data;
  },
};
