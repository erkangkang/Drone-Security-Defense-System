import { useQuery } from '@tanstack/react-query';
import { threatsApi } from '@/api/threats';
import type { Threat } from '@/types';

export function useThreats(params?: { limit?: number; threat_type?: string; severity?: string }) {
  const {
    data: threats = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['threats', params],
    queryFn: () => threatsApi.getThreats(params),
    refetchInterval: 10000, // 每10秒刷新
  });

  return {
    threats: threats as Threat[],
    isLoading,
    error,
    refetch,
  };
}

export function useThreatTimeline(limit = 100) {
  const {
    data: timeline = { events: [], total: 0 },
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['threats', 'timeline', limit],
    queryFn: () => threatsApi.getTimeline(limit),
    refetchInterval: 15000, // 每15秒刷新
  });

  return {
    events: timeline.events as Threat[],
    total: timeline.total,
    isLoading,
    error,
    refetch,
  };
}

export function useThreatDistribution() {
  const {
    data: distribution = {
      by_type: {},
      by_severity: {},
      by_detector: {},
      total: 0,
    },
    isLoading,
    error,
  } = useQuery({
    queryKey: ['threats', 'distribution'],
    queryFn: () => threatsApi.getDistribution(),
    refetchInterval: 30000, // 每30秒刷新
  });

  return {
    distribution,
    isLoading,
    error,
  };
}
