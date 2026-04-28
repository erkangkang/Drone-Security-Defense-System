import apiClient from './client';
import type { SystemStatus } from '@/types';

export const systemApi = {
  /**
   * 获取系统状态
   */
  getStatus: async () => {
    const response = await apiClient.get<SystemStatus>('/system/status');
    return response.data;
  },

  /**
   * 健康检查
   */
  healthCheck: async () => {
    const response = await apiClient.get('/system/health');
    return response.data;
  },

  /**
   * 重新加载配置
   */
  reloadConfig: async () => {
    const response = await apiClient.post('/system/config/reload', {});
    return response.data;
  },

  /**
   * 获取系统信息
   */
  getInfo: async () => {
    const response = await apiClient.get('/system/info');
    return response.data;
  },
};
