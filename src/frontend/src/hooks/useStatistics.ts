import { useQuery } from '@tanstack/react-query';
import { statisticsApi } from '@/api/statistics';
import type { Statistics } from '@/types';

export function useStatistics(hours = 24) {
  const {
    data: statistics,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['statistics', hours],
    queryFn: () => statisticsApi.getStatistics(hours),
    refetchInterval: 30000, // 每30秒刷新
  });

  return {
    statistics: statistics as Statistics | undefined,
    isLoading,
    error,
    refetch,
  };
}

export function useTrafficTrends(hours = 24) {
  const {
    data: trafficData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['statistics', 'traffic', hours],
    queryFn: () => statisticsApi.getTrafficTrends(hours),
    refetchInterval: 60000, // 每分钟刷新
  });

  return {
    trafficData,
    isLoading,
    error,
  };
}

export function useDashboardData() {
  const {
    data: dashboardData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => statisticsApi.getDashboardData(),
    refetchInterval: 10000, // 每10秒刷新
  });

  return {
    dashboardData,
    isLoading,
    error,
    refetch,
  };
}
