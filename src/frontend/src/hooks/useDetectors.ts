import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { detectorsApi } from '@/api/detectors';
import type { DetectorStatus } from '@/types';

export function useDetectors() {
  const {
    data: detectors = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['detectors'],
    queryFn: () => detectorsApi.getDetectors(),
    refetchInterval: 10000, // 每10秒刷新
  });

  return {
    detectors: detectors as DetectorStatus[],
    isLoading,
    error,
    refetch,
  };
}

export function useDetector(name: string) {
  const {
    data: detector,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['detectors', name],
    queryFn: () => detectorsApi.getDetector(name),
    enabled: !!name,
    refetchInterval: 5000, // 每5秒刷新
  });

  return {
    detector,
    isLoading,
    error,
    refetch,
  };
}

export function useDetectorActions() {
  const queryClient = useQueryClient();

  const startMutation = useMutation({
    mutationFn: (name: string) => detectorsApi.startDetector(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['detectors'] });
    },
  });

  const stopMutation = useMutation({
    mutationFn: (name: string) => detectorsApi.stopDetector(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['detectors'] });
    },
  });

  return {
    startDetector: startMutation.mutate,
    stopDetector: stopMutation.mutate,
    isStarting: startMutation.isPending,
    isStopping: stopMutation.isPending,
  };
}
