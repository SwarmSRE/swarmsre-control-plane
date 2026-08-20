import React, { useState } from 'react';

interface ApprovalControlsProps {
  incidentId: string;
  onActionComplete: () => void;
}

export const ApprovalControls: React.FC<ApprovalControlsProps> = ({ incidentId, onActionComplete }) => {
  const [loading, setLoading] = useState(false);

  const handleAction = async (action: 'approve' | 'reject') => {
    setLoading(true);
    try {
      const res = await fetch(`/api/incidents/${incidentId}/${action}`, {
        method: 'POST',
      });
      if (res.ok) {
        onActionComplete();
      } else {
        console.error(`Failed to ${action} patch:`, await res.text());
      }
    } catch (e) {
      console.error(`Error during ${action}:`, e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--space-lg)',
      marginTop: 'var(--space-xl)',
      padding: 'var(--space-lg)',
      backgroundColor: 'rgba(0,0,0,0.2)',
      borderRadius: 'var(--radius-lg)',
      border: '1px solid var(--border-subtle)',
    }}>
      <div style={{ flex: 1 }}>
        <h4 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)', margin: '0 0 var(--space-xs) 0' }}>
          Human-in-the-Loop Required
        </h4>
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', margin: 0 }}>
          Please review the proposed patch before the agent executes it on the cluster.
        </p>
      </div>
      <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
        <button
          disabled={loading}
          onClick={() => handleAction('reject')}
          className="btn-danger"
          style={{
            padding: 'var(--space-sm) var(--space-md)',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            color: 'var(--status-red)',
            border: '1px solid rgba(239, 68, 68, 0.2)',
            borderRadius: 'var(--radius-md)',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.5 : 1
          }}
        >
          Reject
        </button>
        <button
          disabled={loading}
          onClick={() => handleAction('approve')}
          style={{
            padding: 'var(--space-sm) var(--space-md)',
            backgroundColor: 'var(--status-green)',
            color: '#000',
            fontWeight: 600,
            border: 'none',
            borderRadius: 'var(--radius-md)',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.5 : 1,
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-xs)'
          }}
        >
          {loading ? 'Processing...' : 'Approve & Apply'}
        </button>
      </div>
    </div>
  );
};
