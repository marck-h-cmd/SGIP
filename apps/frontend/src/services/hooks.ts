import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './api';

export function useDmas() {
  return useQuery({ queryKey: ['dmas'], queryFn: api.dmas.list });
}

export function useDma(id: string) {
  return useQuery({ queryKey: ['dma', id], queryFn: () => api.dmas.get(id), enabled: !!id });
}

export function useDmaSensors(id: string) {
  return useQuery({ queryKey: ['dma-sensors', id], queryFn: () => api.dmas.getSensors(id), enabled: !!id });
}

export function useDmaMetrics(id: string) {
  return useQuery({ queryKey: ['dma-metrics', id], queryFn: () => api.dmas.getMetrics(id), enabled: !!id });
}

export function useLatestTelemetry() {
  return useQuery({ queryKey: ['telemetry-latest'], queryFn: api.telemetry.latest, refetchInterval: 60000 });
}

export function useTelemetryHistory(dmaId: string, hours = 24) {
  return useQuery({
    queryKey: ['telemetry-history', dmaId, hours],
    queryFn: () => api.telemetry.history(dmaId, hours),
    enabled: !!dmaId,
  });
}

export function useMocheTrends() {
  return useQuery({ queryKey: ['moche-trends'], queryFn: api.telemetry.mocheTrends, refetchInterval: 60000 });
}

export function useRecentAnomalies() {
  return useQuery({ queryKey: ['anomalies-recent'], queryFn: api.anomalies.mocheRecent, refetchInterval: 60000 });
}

export function useAnomalyStats() {
  return useQuery({ queryKey: ['anomaly-stats'], queryFn: api.anomalies.mocheStats });
}

export function useIncidents(dmaId?: string) {
  return useQuery({
    queryKey: ['incidents', dmaId],
    queryFn: () => api.incidents.list(dmaId),
  });
}

export function useUpdateIncidentStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => api.incidents.updateStatus(id, status),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['incidents'] }); },
  });
}

export function useExecutiveKpis() {
  return useQuery({ queryKey: ['kpis-executive'], queryFn: api.kpis.executive, refetchInterval: 60000 });
}

export function useAlerts() {
  return useQuery({ queryKey: ['alerts'], queryFn: api.alerts.list, refetchInterval: 60000 });
}

export function useAcknowledgeAlert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.alerts.acknowledge(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['alerts'] }); },
  });
}

export function useWaterLoss() {
  return useQuery({ queryKey: ['water-loss'], queryFn: api.kpis.waterLoss });
}

export function useDailyReport(date?: string) {
  return useQuery({ queryKey: ['report-daily', date], queryFn: () => api.reports.mocheDaily(date) });
}

export function useWeeklyReport() {
  return useQuery({ queryKey: ['report-weekly'], queryFn: api.reports.mocheWeekly });
}

export function useCustomReport(startDate: string, endDate: string) {
  return useQuery({
    queryKey: ['report-custom', startDate, endDate],
    queryFn: () => api.reports.mocheCustom(startDate, endDate),
    enabled: !!startDate && !!endDate,
  });
}
