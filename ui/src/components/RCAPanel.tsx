import React from 'react';
import type { Incident } from '../hooks/useIncidents';
import { ConfidenceGauge } from './ConfidenceGauge';
import { YAMLViewer } from './YAMLViewer';
import { ApprovalControls } from './ApprovalControls';

interface RCAPanelProps {
  incident: Incident | null;
  onRefreshNeeded: () => void;
}

export const RCAPanel: React.FC<RCAPanelProps> = ({ incident, onRefreshNeeded }) => {
  if (!incident) {
    return (
      <div className="glass-card animate-fade-in" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '400px' }}>
        <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
          <p>Select an incident to view RCA</p>
        </div>
      </div>
    );
  }

  const isProposed = incident.status === 'PROPOSED';
  const confidence = incident.confidence_score ?? 0;

  return (
    <div className="glass-card animate-fade-in" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Header */}
      <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2 style={{ margin: '0 0 var(--space-xs) 0' }}>{incident.title}</h2>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0 }}>ID: <span style={{ fontFamily: 'var(--font-mono)' }}>{incident.id}</span></p>
        </div>
        {confidence > 0 && <ConfidenceGauge score={confidence} />}
      </div>

      {/* Content */}
      <div style={{ padding: 'var(--space-xl)', overflowY: 'auto', flex: 1 }} className="custom-scrollbar">
        
        {/* Status Alert if not PROPOSED (resolved, rejected, etc) */}
        {!isProposed && incident.status !== 'OPEN' && incident.status !== 'INVESTIGATING' && (
           <div style={{
             padding: 'var(--space-md)',
             borderRadius: 'var(--radius-md)',
             marginBottom: 'var(--space-xl)',
             border: `1px solid ${incident.status === 'RESOLVED' ? 'rgba(34, 197, 94, 0.3)' : incident.status === 'REJECTED' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(59, 130, 246, 0.3)'}`,
             backgroundColor: incident.status === 'RESOLVED' ? 'rgba(34, 197, 94, 0.1)' : incident.status === 'REJECTED' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(59, 130, 246, 0.1)',
             color: incident.status === 'RESOLVED' ? 'var(--status-green)' : incident.status === 'REJECTED' ? 'var(--status-red)' : 'var(--status-blue)',
           }}>
             <div style={{ fontWeight: 600 }}>{incident.status}</div>
             <div style={{ fontSize: '0.875rem', opacity: 0.8, marginTop: 'var(--space-xs)' }}>This incident has been {incident.status.toLowerCase()}.</div>
           </div>
        )}

        {/* Synthesis Details */}
        {incident.rca_summary && (
          <div style={{ marginBottom: 'var(--space-xl)' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-sm)', display: 'flex', alignItems: 'center', gap: 'var(--space-xs)' }}>
              <span style={{ color: 'var(--text-accent)' }}>🧠</span> Root Cause Analysis
            </h3>
            <div style={{ 
              backgroundColor: 'rgba(0,0,0,0.2)', 
              padding: 'var(--space-md)', 
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              fontSize: '0.875rem',
              color: 'var(--text-secondary)',
              lineHeight: 1.6,
              whiteSpace: 'pre-wrap'
            }}>
              {incident.rca_summary}
            </div>
          </div>
        )}

        {incident.proposed_patch && (
          <div style={{ marginBottom: 'var(--space-xl)' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 'var(--space-sm)', display: 'flex', alignItems: 'center', gap: 'var(--space-xs)' }}>
              <span style={{ color: 'var(--status-green)' }}>🛠️</span> Proposed Patch
            </h3>
            <YAMLViewer code={incident.proposed_patch} />
          </div>
        )}

        {/* Action Controls */}
        {isProposed && (
          <ApprovalControls incidentId={incident.id} onActionComplete={onRefreshNeeded} />
        )}
      </div>
    </div>
  );
};
