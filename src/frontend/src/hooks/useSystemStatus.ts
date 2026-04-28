import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { systemApi } from '@/api/system';
import type { SystemStatus } from '@/types';

export function useSystemStatus() {
  const queryClient = useQueryClient();

  const {
    data: systemStatus,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['system', 'status'],
    queryFn: () => systemApi.getStatus(),
    refetchInterval: 5000, // 每5秒刷新
  });

  const reloadConfigMutation = useMutation({
    mutationFn: () => systemApi.reloadConfig(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['system', 'status'] });
    },
  });

  return {
    systemStatus: systemStatus as SystemStatus | undefined,
    isLoading,
    error,
    refetch,
    reloadConfig: reloadConfigMutation.mutate,
    isReloading: reloadConfigMutation.isPending,
  };
}
