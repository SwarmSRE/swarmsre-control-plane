import { useState } from 'react';
import './index.css';
import { useIncidents } from './hooks/useIncidents';
import { StatusBanner } from './components/StatusBanner';
import { IncidentTimeline } from './components/IncidentTimeline';
import { RCAPanel } from './components/RCAPanel';
import { TopologyGraph } from './visualizations/TopologyGraph';
import type { TopologyData } from './visualizations/topology-data';
import type { Incident } from './hooks/useIncidents';

type Tab = 'dashboard' | 'topology' | 'audit';

function App() {
  const { incidents, loading, isConnected, getStatusCounts } = useIncidents();
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [topologyData, setTopologyData] = useState<TopologyData | null>(null);
  const counts = getStatusCounts();

  // Fetch topology data when tab is selected
  useState(() => {
    fetch('/api/topology')
      .then(res => res.json())
      .then(data => setTopologyData(data))
      .catch(console.error);
  });

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
            <RCAPanel 
              incident={selectedIncident} 
              onRefreshNeeded={() => {
                // If a manual fetch is needed, you can trigger it here.
                // Currently WebSocket will auto-update state in useIncidents.
              }} 
            />
          </div>
        )}

        {activeTab === 'topology' && (
          <div className="glass-card animate-fade-in" style={{ height: 'calc(100vh - 180px)', display: 'flex', flexDirection: 'column' }}>
            <div className="card-header">
              <h2>Service Topology</h2>
            </div>
            <div style={{ flex: 1, position: 'relative' }}>
              {topologyData ? (
                <TopologyGraph data={topologyData} />
              ) : (
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: 'var(--text-muted)' }}>
                  Loading topology...
                </div>
              )}
            </div>
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
