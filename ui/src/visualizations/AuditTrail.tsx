import React, { useEffect, useState } from 'react';

interface AuditEntry {
  id: string;
  incident_id?: string;
  timestamp: string;
  action: string;
  actor: string;
  details?: Record<string, any>;
}

export const AuditTrail: React.FC = () => {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/audit/')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch audit logs');
        return res.json();
      })
      .then(data => {
        // Sort descending by timestamp
        const sorted = data.sort((a: AuditEntry, b: AuditEntry) => 
          new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        );
        setEntries(sorted);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', padding: 'var(--space-2xl)', color: 'var(--text-muted)' }}>Loading audit trail...</div>;
  }

  if (error) {
    return <div style={{ display: 'flex', justifyContent: 'center', padding: 'var(--space-2xl)', color: 'var(--status-red)' }}>Error: {error}</div>;
  }

  return (
    <div style={{ width: '100%', overflowX: 'auto', padding: 'var(--space-md)' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem', textAlign: 'left' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-secondary)' }}>
            <th style={{ padding: 'var(--space-sm) var(--space-md)', fontWeight: 600 }}>Timestamp</th>
            <th style={{ padding: 'var(--space-sm) var(--space-md)', fontWeight: 600 }}>Action</th>
            <th style={{ padding: 'var(--space-sm) var(--space-md)', fontWeight: 600 }}>Actor</th>
            <th style={{ padding: 'var(--space-sm) var(--space-md)', fontWeight: 600 }}>Incident ID</th>
            <th style={{ padding: 'var(--space-sm) var(--space-md)', fontWeight: 600 }}>Details</th>
          </tr>
        </thead>
        <tbody>
          {entries.length === 0 ? (
            <tr>
              <td colSpan={5} style={{ textAlign: 'center', padding: 'var(--space-xl)', color: 'var(--text-muted)' }}>
                No audit logs found.
              </td>
            </tr>
          ) : (
            entries.map(entry => (
              <tr key={entry.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.03)', transition: 'background-color 0.2s' }} className="hover:bg-gray-800/30">
                <td style={{ padding: 'var(--space-sm) var(--space-md)', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                  {new Date(entry.timestamp).toLocaleString()}
                </td>
                <td style={{ padding: 'var(--space-sm) var(--space-md)', color: 'var(--text-primary)', fontWeight: 500 }}>
                  {entry.action}
                </td>
                <td style={{ padding: 'var(--space-sm) var(--space-md)' }}>
                  <span style={{ 
                    backgroundColor: entry.actor === 'human-approver' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(59, 130, 246, 0.1)', 
                    color: entry.actor === 'human-approver' ? 'var(--status-green)' : 'var(--status-blue)',
                    padding: '2px 8px',
                    borderRadius: '12px',
                    fontSize: '0.75rem'
                  }}>
                    {entry.actor}
                  </span>
                </td>
                <td style={{ padding: 'var(--space-sm) var(--space-md)', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                  {entry.incident_id || '-'}
                </td>
                <td style={{ padding: 'var(--space-sm) var(--space-md)' }}>
                  {entry.details && Object.keys(entry.details).length > 0 ? (
                    <pre style={{ 
                      margin: 0, 
                      padding: '4px 8px', 
                      backgroundColor: 'rgba(0,0,0,0.2)', 
                      borderRadius: 'var(--radius-sm)', 
                      fontSize: '0.75rem',
                      color: 'var(--text-secondary)',
                      whiteSpace: 'pre-wrap'
                    }}>
                      {JSON.stringify(entry.details, null, 2)}
                    </pre>
                  ) : '-'}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};
