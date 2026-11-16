import React, { useState, useEffect } from 'react';
import './styles/modern-dashboard.css';
import { ModernSidebar } from './components/ModernSidebar';
import { ModernDashboard } from './pages/ModernDashboard';
import { WorkflowUpload } from './pages/WorkflowUpload';
import { AuditLogs } from './pages/AuditLogs';
import { SapStatus } from './pages/SapStatus';
import { ItemMasterPage } from './pages/ItemMasterPage';
import { BusinessPartnerPage } from './pages/BusinessPartnerPage';
import { WarehouseMasterPage } from './pages/WarehouseMasterPage';
import { RagExplorer } from './pages/RagExplorer';
import { AiAgentPage } from './pages/AiAgentPage';
import { api } from './services/api';
import { ArrowLeft } from 'lucide-react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LoginPage } from './pages/LoginPage';

const AuthenticatedApp: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [sapCounts, setSapCounts] = useState<{ Items: number; BusinessPartners: number; Warehouses: number } | null>(null);
  const [docsCount, setDocsCount] = useState<number>(36);
  const [sapConnected, setSapConnected] = useState<boolean>(false);
  const [companyDb, setCompanyDb] = useState<string>('TEST_SHOES_10SEP26');

  // Load SAP Counts & Health for Sidebar Badges
  useEffect(() => {
    const fetchMetadata = async () => {
      try {
        const [counts, stats, health] = await Promise.allSettled([
          api.getSapCounts(),
          api.getDashboardStats(),
          api.getSapHealth()
        ]);
        if (counts.status === 'fulfilled' && counts.value) setSapCounts(counts.value);
        if (stats.status === 'fulfilled' && stats.value?.documents_processed) {
          setDocsCount(stats.value.documents_processed);
        }
        if (health.status === 'fulfilled' && health.value) {
          const isConn = Boolean(health.value.connected || health.value.status === 'CONNECTED' || (health.value as any)?.data?.connected);
          setSapConnected(isConn);
          if (health.value.company_db) {
            setCompanyDb(health.value.company_db);
          }
        } else if (stats.status === 'fulfilled' && stats.value?.database?.company_db) {
          setCompanyDb(stats.value.database.company_db);
        }
      } catch (e) {
        console.error('Failed to fetch platform metadata', e);
      }
    };
    fetchMetadata();
  }, []);

  const renderSubpageHeader = (breadcrumbTitle: string) => (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingBottom: 12,
        borderBottom: '1px solid rgba(0, 0, 0, 0.06)',
        marginBottom: 2,
        flexWrap: 'wrap',
        gap: 12,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13.5 }}>
        <button
          onClick={() => setActiveTab('dashboard')}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: '#71717A',
            fontWeight: 600,
            padding: 0,
            display: 'flex',
            alignItems: 'center',
            gap: 5,
            fontFamily: 'inherit',
            transition: 'color 0.15s ease',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = '#0A0A0A')}
          onMouseLeave={(e) => (e.currentTarget.style.color = '#71717A')}
        >
          <span>Dashboard</span>
        </button>
        <span style={{ color: '#A1A1AA', fontWeight: 500 }}>/</span>
        <span style={{ color: '#0A0A0A', fontWeight: 700, letterSpacing: '-0.2px' }}>
          {breadcrumbTitle}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div className={`md-sap-status-pill ${sapConnected ? '' : 'disconnected'}`}>
          <span className={`md-status-dot-pulse ${sapConnected ? '' : 'disconnected'}`} />
          <span>{sapConnected ? `SAP: ${companyDb}` : 'SAP: Not Connected'}</span>
        </div>
        <button onClick={() => setActiveTab('dashboard')} className="md-pill-btn">
          <ArrowLeft size={14} /> Back to Dashboard
        </button>
      </div>
    </div>
  );

  const renderActivePage = () => {
    switch (activeTab) {
      case 'dashboard':
        return <ModernDashboard onNavigateToModule={(mod) => setActiveTab(mod)} />;

      case 'ai-agent':
      case 'agent':
        return <AiAgentPage />;

      case 'orders':
      case 'content':
      case 'sap-studio':
      case 'upload':
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {renderSubpageHeader('Workflows & Document Extraction')}
            <WorkflowUpload />
          </div>
        );

      case 'products':
      case 'item-master':
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {renderSubpageHeader('Item Master')}
            <ItemMasterPage onNavigateToAudit={() => setActiveTab('audit')} />
          </div>
        );

      case 'customers':
      case 'business-partner':
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {renderSubpageHeader('Business Partner Master')}
            <BusinessPartnerPage onNavigateToAudit={() => setActiveTab('audit')} />
          </div>
        );

      case 'online-store':
      case 'warehouse-master':
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {renderSubpageHeader('Warehouse Master')}
            <WarehouseMasterPage onNavigateToAudit={() => setActiveTab('audit')} />
          </div>
        );

      case 'finances':
      case 'finances-invoices':
      case 'finances-transactions':
      case 'finances-reports':
      case 'analytics':
      case 'audit':
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {renderSubpageHeader('Immutable Audit Trail')}
            <AuditLogs />
          </div>
        );

      case 'discounts':
      case 'settings':
      case 'sap':
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {renderSubpageHeader('SAP Service Layer Configuration')}
            <SapStatus />
          </div>
        );

      case 'help':
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {renderSubpageHeader('SAP Knowledge Base & Documentation')}
            <RagExplorer />
          </div>
        );

      default:
        return <ModernDashboard onNavigateToModule={(mod) => setActiveTab(mod)} />;
    }
  };

  if (isLoading) {
    return null;
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <div className="md-layout">
      <div className="md-shell">
        <ModernSidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          orderCount={docsCount ?? 0}
          itemCount={sapCounts?.Items ?? 0}
          bpCount={sapCounts?.BusinessPartners ?? 0}
          whCount={sapCounts?.Warehouses ?? 0}
        />
        <main className="md-main">
          {renderActivePage()}
        </main>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <AuthenticatedApp />
    </AuthProvider>
  );
};

export default App;
