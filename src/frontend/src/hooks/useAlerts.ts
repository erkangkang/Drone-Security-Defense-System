import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { alertsApi } from '@/api/alerts';
import type { Alert } from '@/types';

export function useAlerts(params?: { limit?: number; status?: string; severity?: string }) {
  const {
    data: alerts = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['alerts', params],
    queryFn: () => alertsApi.getAlerts(params),
    refetchInterval: 10000, // 每10秒刷新
  });

  return {
    alerts: alerts as Alert[],
    isLoading,
    error,
    refetch,
  };
}

export function useActiveAlerts(limit = 50) {
  const {
    data: alerts = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['alerts', 'active', limit],
    queryFn: () => alertsApi.getActiveAlerts(limit),
    refetchInterval: 5000, // 每5秒刷新
  });

  return {
    alerts: alerts as Alert[],
    isLoading,
    error,
    refetch,
  };
}

export function useAlert(alertId: string) {
  const {
    data: alert,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['alerts', alertId],
    queryFn: () => alertsApi.getAlert(alertId),
    enabled: !!alertId,
  });

  return {
    alert,
    isLoading,
    error,
  };
}

export function useAlertActions() {
  const queryClient = useQueryClient();

  const acknowledgeMutation = useMutation({
    mutationFn: ({ alertId, user, notes }: { alertId: string; user?: string; notes?: string }) =>
      alertsApi.acknowledgeAlert(alertId, user, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });

  const resolveMutation = useMutation({
    mutationFn: ({ alertId, user }: { alertId: string; user?: string }) =>
      alertsApi.resolveAlert(alertId, user),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });

  const markFalsePositiveMutation = useMutation({
    mutationFn: ({ alertId, user }: { alertId: string; user?: string }) =>
      alertsApi.markFalsePositive(alertId, user),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });

  return {
    acknowledgeAlert: acknowledgeMutation.mutate,
    resolveAlert: resolveMutation.mutate,
    markFalsePositive: markFalsePositiveMutation.mutate,
    isAcknowledging: acknowledgeMutation.isPending,
    isResolving: resolveMutation.isPending,
    isMarkingFalsePositive: markFalsePositiveMutation.isPending,
  };
}
