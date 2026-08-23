import React, { useEffect, useState } from 'react';

interface AuditLog {
  id: string;
  incident_id?: string;
  action: string;
  actor: string;
  timestamp: string;
  details?: Record<string, any>;
}

export const AuditTrail: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/audit/')
      .then(res => res.json())
      .then(data => {
        // Sort descending
        const sorted = data.sort((a: AuditLog, b: AuditLog) => 
          new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        );
        setLogs(sorted);
        setLoading(false);
      })
      .catch(e => {
        console.error(e);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="text-[#94A3B8] p-8 text-center bg-[#111827]/50 rounded-xl border border-[#1E293B]">Loading audit logs...</div>;
  }

  return (
    <div className="bg-[#111827]/50 backdrop-blur-md rounded-xl border border-[#1E293B] overflow-hidden">
      <div className="p-6 pb-4 border-b border-[#1E293B] bg-[#111827]/80">
        <h2 className="text-[#F8FAFC] font-semibold text-lg m-0">Audit Trail</h2>
        <p className="text-xs text-[#94A3B8] m-0 mt-1">Immutable log of AI and human actions</p>
      </div>
      <div className="overflow-x-auto custom-scrollbar max-h-[600px]">
        <table className="w-full text-left text-sm text-[#CBD5E1]">
          <thead className="bg-[#0B1120]/50 text-xs uppercase font-semibold text-[#94A3B8] sticky top-0 z-10">
            <tr>
              <th className="px-6 py-4 border-b border-[#1E293B]">Timestamp</th>
              <th className="px-6 py-4 border-b border-[#1E293B]">Actor</th>
              <th className="px-6 py-4 border-b border-[#1E293B]">Action</th>
              <th className="px-6 py-4 border-b border-[#1E293B]">Incident ID</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#1E293B]">
            {logs.map((log) => (
              <tr key={log.id} className="hover:bg-white/5 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap font-mono text-xs text-[#94A3B8]">{new Date(log.timestamp).toLocaleString()}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-md text-xs font-semibold ${
                    log.actor === 'HUMAN' 
                      ? 'bg-[#8B5CF6]/20 text-[#8B5CF6] border border-[#8B5CF6]/30' 
                      : 'bg-[#00F0FF]/10 text-[#00F0FF] border border-[#00F0FF]/30'
                  }`}>
                    {log.actor}
                  </span>
                </td>
                <td className="px-6 py-4 font-medium text-[#E2E8F0]">{log.action}</td>
                <td className="px-6 py-4 font-mono text-xs text-[#94A3B8]">{log.incident_id || '-'}</td>
              </tr>
            ))}
            {logs.length === 0 && (
              <tr>
                <td colSpan={4} className="px-6 py-12 text-center text-[#64748B]">
                  No audit logs found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
