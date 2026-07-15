import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useCallback, useRef, useState } from 'react';
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

// WebSocket hook for real-time incident updates
export function useIncidentWebSocket(onIncidentUpdate?: (data: any) => void) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const qc = useQueryClient();

  const connect = useCallback(() => {
    try {
      const wsUrl = `ws://localhost:8000/ws/incidents`;
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastMessage(data);
          
          // Invalidate queries based on message type
          if (data.type === 'incident_update' || data.type === 'incident_created') {
            qc.invalidateQueries({ queryKey: ['incidents'] });
            if (onIncidentUpdate) onIncidentUpdate(data);
          }
        } catch (e) {
          console.error('Error parsing WebSocket message:', e);
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        // Reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(connect, 5000);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        ws.close();
      };
      
      wsRef.current = ws;
    } catch (error) {
      console.error('WebSocket connection error:', error);
    }
  }, [qc, onIncidentUpdate]);

  useEffect(() => {
    connect();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  return { isConnected, lastMessage, sendMessage };
}

// SLA Metrics hooks
export function useSlaMetrics(dmaId?: string) {
  return useQuery({
    queryKey: ['sla-metrics', dmaId],
    queryFn: () => dmaId ? api.incidents.slaMetrics(dmaId) : api.incidents.slaMetrics(),
    refetchInterval: 300000, // 5 minutes
  });
}

export function useCheckSlaBreaches() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.incidents.checkSlaBreaches(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['incidents'] });
      qc.invalidateQueries({ queryKey: ['sla-metrics'] });
    },
  });
}
