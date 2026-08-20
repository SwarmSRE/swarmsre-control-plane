import { useState } from 'react';
import './index.css';
import { useIncidents } from './hooks/useIncidents';
import { StatusBanner } from './components/StatusBanner';
import { IncidentTimeline } from './components/IncidentTimeline';
import type { Incident } from './hooks/useIncidents';

type Tab = 'dashboard' | 'topology' | 'audit';

function App() {
  const { incidents, loading, isConnected, getStatusCounts } = useIncidents();
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const counts = getStatusCounts();

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar" id="sidebar">
        <div className="sidebar-logo">
          <div>
            <h1>SwarmSRE</h1>
            <span>AI Control Plane</span>
          </div>
        </div>
        <nav className="sidebar-nav">
          <button
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
            id="nav-dashboard"
          >
            <span className="nav-icon">📊</span>
            Dashboard
          </button>
          <button
            className={`nav-item ${activeTab === 'topology' ? 'active' : ''}`}
            onClick={() => setActiveTab('topology')}
            id="nav-topology"
          >
            <span className="nav-icon">🗺️</span>
            Topology
          </button>
          <button
            className={`nav-item ${activeTab === 'audit' ? 'active' : ''}`}
            onClick={() => setActiveTab('audit')}
            id="nav-audit"
          >
            <span className="nav-icon">📋</span>
            Audit Trail
          </button>
        </nav>
        <div style={{ marginTop: 'auto', paddingTop: 'var(--space-lg)', borderTop: '1px solid var(--border-subtle)' }}>
          <div className="nav-item" style={{ cursor: 'default' }}>
            <span className="nav-icon">{isConnected ? '🟢' : '🔴'}</span>
            <span style={{ fontSize: '0.75rem' }}>{isConnected ? 'Connected' : 'Disconnected'}</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <StatusBanner
          totalIncidents={counts.total}
          openIncidents={counts.open}
          investigatingIncidents={counts.investigating}
          isConnected={isConnected}
        />

        {activeTab === 'dashboard' && (
          <div className="dashboard-grid">
            <IncidentTimeline
              incidents={incidents}
              onSelect={setSelectedIncident}
              selectedId={selectedIncident?.id}
            />
            <div className="glass-card animate-fade-in" id="rca-panel-placeholder">
              <div className="card-header">
                <h2>RCA Panel</h2>
              </div>
              {selectedIncident ? (
                <div>
                  <h3 style={{ marginBottom: 'var(--space-md)', fontSize: '0.95rem' }}>
                    {selectedIncident.title}
                  </h3>
                  <div style={{ marginBottom: 'var(--space-md)' }}>
                    <span className={`status-pill ${selectedIncident.status.toLowerCase()}`}>
                      {selectedIncident.status}
                    </span>
                  </div>
                  {selectedIncident.rca_summary && (
                    <div style={{ marginBottom: 'var(--space-md)' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 'var(--space-xs)' }}>
                        Root Cause Analysis
                      </div>
                      <p style={{ fontSize: '0.875rem', lineHeight: 1.6 }}>
                        {selectedIncident.rca_summary}
                      </p>
                    </div>
                  )}
                  {selectedIncident.confidence_score != null && (
                    <div style={{ marginBottom: 'var(--space-md)' }}>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 'var(--space-xs)' }}>
                        Confidence
                      </div>
                      <div style={{
                        fontSize: '1.5rem',
                        fontWeight: 700,
                        color: selectedIncident.confidence_score >= 0.8 ? 'var(--status-green)' : selectedIncident.confidence_score >= 0.5 ? 'var(--status-yellow)' : 'var(--status-red)'
                      }}>
                        {(selectedIncident.confidence_score * 100).toFixed(0)}%
                      </div>
                    </div>
                  )}
                  {selectedIncident.proposed_patch && (
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: 'var(--space-xs)' }}>
                        Proposed Patch
                      </div>
                      <pre style={{
                        background: 'rgba(0,0,0,0.3)',
                        padding: 'var(--space-md)',
                        borderRadius: 'var(--radius-md)',
                        fontSize: '0.75rem',
                        fontFamily: 'var(--font-mono)',
                        overflowX: 'auto',
                        color: 'var(--status-green)',
                      }}>
                        {selectedIncident.proposed_patch}
                      </pre>
                    </div>
                  )}
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 'var(--space-xl)' }}>
                  Select an incident to view the Root Cause Analysis.
                </p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'topology' && (
          <div className="glass-card animate-fade-in">
            <div className="card-header">
              <h2>Service Topology</h2>
            </div>
            <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 'var(--space-2xl)' }}>
              D3.js topology graph will be added in Sprint 11.
            </p>
          </div>
        )}

        {activeTab === 'audit' && (
          <div className="glass-card animate-fade-in">
            <div className="card-header">
              <h2>Audit Trail</h2>
            </div>
            <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: 'var(--space-2xl)' }}>
              Full audit trail viewer will be added in Sprint 13.
            </p>
          </div>
        )}

        {loading && (
          <div style={{ textAlign: 'center', padding: 'var(--space-2xl)', color: 'var(--text-muted)' }}>
            Loading incidents...
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
