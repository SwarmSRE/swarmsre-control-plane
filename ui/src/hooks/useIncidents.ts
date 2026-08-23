import { useState, useEffect, useCallback } from 'react';
import { useWebSocket } from './useWebSocket';

export interface Incident {
  id: string;
  title: string;
  description: string;
  status: 'OPEN' | 'INVESTIGATING' | 'QUARANTINED' | 'PROPOSED' | 'RESOLVED' | 'REJECTED' | 'FAILED';
  source: string;
  created_at: string;
  updated_at: string;
  raw_event?: Record<string, unknown>;
  quarantine_result?: Record<string, unknown>;
  rca_summary?: string;
  proposed_patch?: string;
  confidence_score?: number;
  evidence_chain?: Record<string, unknown>[];
  log_hunter_output?: Record<string, unknown>;
  telemetry_output?: Record<string, unknown>;
  agent_trace?: Array<{
    agent: string;
    timestamp: string;
    summary: string;
    details: string;
  }>;
}

export function useIncidents() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isConnected, lastEvent } = useWebSocket('/ws/incidents');

  const fetchIncidents = useCallback(async () => {
    try {
      const res = await fetch('/api/incidents');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setIncidents(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchIncidents();
  }, [fetchIncidents]);

  // Update incidents when WebSocket events arrive
  useEffect(() => {
    if (lastEvent) {
      fetchIncidents();
    }
  }, [lastEvent, fetchIncidents]);

  const getStatusCounts = useCallback(() => {
    return {
      open: incidents.filter(i => i.status === 'OPEN').length,
      investigating: incidents.filter(i => i.status === 'INVESTIGATING').length,
      proposed: incidents.filter(i => i.status === 'PROPOSED').length,
      resolved: incidents.filter(i => i.status === 'RESOLVED').length,
      rejected: incidents.filter(i => i.status === 'REJECTED').length,
      failed: incidents.filter(i => i.status === 'FAILED').length,
      total: incidents.length,
    };
  }, [incidents]);

  return {
    incidents,
    loading,
    error,
    isConnected,
    fetchIncidents,
    getStatusCounts,
  };
}
