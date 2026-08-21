import React from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface YAMLViewerProps {
  code: string;
}

export const YAMLViewer: React.FC<YAMLViewerProps> = ({ code }) => {
  return (
    <div style={{
      borderRadius: 'var(--radius-md)',
      overflow: 'hidden',
      border: '1px solid var(--border-subtle)',
      marginTop: 'var(--space-sm)'
    }}>
      <div style={{
        backgroundColor: 'rgba(0,0,0,0.4)',
        padding: 'var(--space-sm) var(--space-md)',
        fontSize: '0.75rem',
        color: 'var(--text-muted)',
        fontFamily: 'var(--font-mono)',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span>proposed_patch.yaml</span>
        <button 
          onClick={() => navigator.clipboard.writeText(code)}
          title="Copy to clipboard"
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            padding: '2px',
          }}
        >
          <svg style={{ width: '16px', height: '16px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        </button>
      </div>
      <SyntaxHighlighter
        language="yaml"
        style={vscDarkPlus}
        customStyle={{
          margin: 0,
          padding: 'var(--space-md)',
          background: 'rgba(0,0,0,0.2)',
          fontSize: '0.875rem',
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
};
