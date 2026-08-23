import React, { useState } from 'react';
import { Check, XCircle } from './Icons';

interface ApprovalControlsProps {
  incidentId: string;
  onActionComplete: (newStatus: 'RESOLVED' | 'REJECTED') => void;
}

export const ApprovalControls: React.FC<ApprovalControlsProps> = ({ incidentId, onActionComplete }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleApprove = async () => {
    setIsSubmitting(true);
    try {
      const res = await fetch(`/api/incidents/${incidentId}/approve`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed to approve');
      onActionComplete('RESOLVED');
    } catch (e) {
      console.error(e);
      alert('Failed to approve patch');
      setIsSubmitting(false); // Re-enable if it failed
    }
  };

  const handleReject = async () => {
    setIsSubmitting(true);
    try {
      const res = await fetch(`/api/incidents/${incidentId}/reject`, { method: 'POST' });
      if (!res.ok) throw new Error('Failed to reject');
      onActionComplete('REJECTED');
    } catch (e) {
      console.error(e);
      alert('Failed to reject patch');
      setIsSubmitting(false); // Re-enable if it failed
    }
  };

  return (
    <div className="flex gap-4 pt-6 mt-6 border-t border-[#1E293B]">
      <button
        onClick={handleReject}
        disabled={isSubmitting}
        className="flex-1 px-4 py-3 rounded-lg border border-[#EF4444]/30 bg-[#EF4444]/10 text-[#EF4444] font-semibold text-sm transition-all hover:bg-[#EF4444]/20 hover:border-[#EF4444]/50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 group"
      >
        <XCircle size={18} className="group-hover:scale-110 transition-transform" />
        REJECT
      </button>
      
      <button
        onClick={handleApprove}
        disabled={isSubmitting}
        className="flex-1 px-4 py-3 rounded-lg border border-[#10B981]/30 bg-[#10B981]/10 text-[#10B981] font-semibold text-sm transition-all hover:bg-[#10B981]/20 hover:border-[#10B981]/50 shadow-[0_0_15px_rgba(16,185,129,0.1)] hover:shadow-[0_0_20px_rgba(16,185,129,0.2)] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 group"
      >
        <Check size={18} className="group-hover:scale-110 transition-transform" />
        APPROVE FIX & APPLY
      </button>
    </div>
  );
};
