import React from 'react';

export const ConfidenceGauge: React.FC<{ score: number }> = ({ score }) => {
  const getColor = () => {
    if (score >= 90) return 'text-[#10B981] shadow-[#10B981]/20';
    if (score >= 70) return 'text-[#F59E0B] shadow-[#F59E0B]/20';
    return 'text-[#EF4444] shadow-[#EF4444]/20';
  };

  const getBgColor = () => {
    if (score >= 90) return 'bg-[#10B981]';
    if (score >= 70) return 'bg-[#F59E0B]';
    return 'bg-[#EF4444]';
  };

  return (
    <div className="flex flex-col items-end gap-1.5">
      <div className={`text-2xl font-bold font-mono tracking-tight leading-none ${getColor().split(' ')[0]}`}>
        {score}%
      </div>
      <div className="text-[0.6rem] uppercase tracking-widest text-[#94A3B8] font-semibold">
        AI Confidence
      </div>
      <div className="w-24 h-1.5 bg-black/40 rounded-full mt-1 overflow-hidden border border-[#1E293B]">
        <div 
          className={`h-full transition-all duration-1000 ease-out rounded-full ${getBgColor()} shadow-[0_0_10px_currentColor]`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
};
