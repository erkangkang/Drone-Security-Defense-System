import apiClient from './client';
import type { DetectorStatus } from '@/types';

export const detectorsApi = {
  /**
   * 获取所有检测器状态
   */
  getDetectors: async () => {
    const response = await apiClient.get<DetectorStatus[]>('/detectors/');
    return response.data;
  },

  /**
   * 获取指定检测器状态
   */
  getDetector: async (name: string) => {
    const response = await apiClient.get<DetectorStatus>(`/detectors/${name}`);
    return response.data;
  },

  /**
   * 启动检测器
   */
  startDetector: async (name: string) => {
    const response = await apiClient.post(`/detectors/${name}/start`, {});
    return response.data;
  },

  /**
   * 停止检测器
   */
  stopDetector: async (name: string) => {
    const response = await apiClient.post(`/detectors/${name}/stop`, {});
    return response.data;
  },

  /**
   * 控制检测器
   */
  controlDetector: async (name: string, action: 'start' | 'stop') => {
    const response = await apiClient.post(`/detectors/${name}/control`, { action });
    return response.data;
  },

  /**
   * 获取检测器摘要
   */
  getSummary: async () => {
    const response = await apiClient.get('/detectors/statistics/summary');
    return response.data;
  },
};
