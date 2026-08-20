import React from 'react';
import type { Incident } from '../hooks/useIncidents';

interface IncidentTimelineProps {
  incidents: Incident[];
  onSelect: (incident: Incident) => void;
  selectedId?: string;
}

const statusIcons: Record<string, string> = {
  OPEN: '🔴',
  INVESTIGATING: '🔍',
  PROPOSED: '🧠',
  RESOLVED: '✅',
  REJECTED: '❌',
};

function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = Math.floor((now - then) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export const IncidentTimeline: React.FC<IncidentTimelineProps> = ({
  incidents,
  onSelect,
  selectedId,
}) => {
  const sorted = [...incidents].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  if (sorted.length === 0) {
    return (
      <div className="glass-card animate-fade-in">
        <div className="card-header">
          <h2>Incident Timeline</h2>
        </div>
        <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 'var(--space-xl)' }}>
          No incidents detected. The cluster is healthy.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-card animate-fade-in" id="incident-timeline">
      <div className="card-header">
        <h2>Incident Timeline</h2>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
          {sorted.length} total
        </span>
      </div>
      <div className="incident-list">
        {sorted.map((incident, index) => (
          <div
            key={incident.id}
            className={`incident-item${selectedId === incident.id ? ' active' : ''}`}
            onClick={() => onSelect(incident)}
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <div className="incident-icon">
              {statusIcons[incident.status] || '⚠️'}
            </div>
            <div className="incident-details">
              <div className="incident-title">{incident.title}</div>
              <div className="incident-meta">
                {incident.source} ·{' '}
                <span className={`status-pill ${incident.status.toLowerCase()}`}>
                  {incident.status}
                </span>
              </div>
            </div>
            <div className="incident-time">{timeAgo(incident.created_at)}</div>
          </div>
        ))}
      </div>
    </div>
  );
};
