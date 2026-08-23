import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check } from './Icons';

interface YAMLViewerProps {
  code: string;
}

export const YAMLViewer: React.FC<YAMLViewerProps> = ({ code }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-lg overflow-hidden border border-[#1E293B] mt-2 shadow-lg">
      <div className="bg-[#111827] px-4 py-2 flex justify-between items-center border-b border-[#1E293B]">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-[#EF4444]" />
            <div className="w-3 h-3 rounded-full bg-[#F59E0B]" />
            <div className="w-3 h-3 rounded-full bg-[#10B981]" />
          </div>
          <span className="text-xs text-[#94A3B8] font-mono ml-3">proposed_patch.yaml</span>
        </div>
        <button 
          onClick={handleCopy}
          title="Copy to clipboard"
          className="flex items-center gap-1.5 text-xs text-[#94A3B8] hover:text-[#F8FAFC] transition-colors"
        >
          {copied ? (
            <>
              <Check size={14} className="text-[#10B981]" />
              <span className="text-[#10B981]">Copied!</span>
            </>
          ) : (
            <>
              <Copy size={14} />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <SyntaxHighlighter
        language="yaml"
        style={vscDarkPlus}
        showLineNumbers={true}
        customStyle={{
          margin: 0,
          padding: '16px',
          background: '#08060d', // Match the main darkest background
          fontSize: '0.8125rem',
          fontFamily: 'var(--font-mono)',
        }}
        lineNumberStyle={{
          minWidth: '2.5em',
          paddingRight: '1em',
          color: '#475569',
          textAlign: 'right',
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
};
