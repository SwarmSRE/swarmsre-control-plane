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
    <div className="flex items-center gap-6 mt-8 p-6 bg-black/20 rounded-xl border border-[#1E293B]">
      <div className="flex-1">
        <h4 className="text-sm font-semibold text-[#F8FAFC] m-0 mb-1">
          Human-in-the-Loop Required
        </h4>
        <p className="text-xs text-[#94A3B8] m-0">
          Please review the proposed patch before the agent executes it on the cluster.
        </p>
      </div>
      <div className="flex gap-3">
        <button
          disabled={loading}
          onClick={() => handleAction('reject')}
          className={`px-4 py-2 bg-transparent text-[#00F0FF] border border-[#00F0FF] rounded-lg font-medium transition-all duration-200 hover:bg-[#00F0FF]/10 ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
        >
          REJECT
        </button>
        <button
          disabled={loading}
          onClick={() => handleAction('approve')}
          className={`px-4 py-2 bg-[#00F0FF] text-black font-semibold rounded-lg transition-all duration-200 hover:brightness-110 hover:shadow-[0_0_15px_rgba(0,240,255,0.4)] ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer flex items-center gap-2'}`}
        >
          {loading ? 'Processing...' : 'APPROVE FIX'}
        </button>
      </div>
    </div>
  );
};
