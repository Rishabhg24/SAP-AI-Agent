import React from 'react';
import cinntraLogo from '../assets/cinntra_logo.png';
import {
  LayoutDashboard,
  Package,
  Users,
  Warehouse,
  FileUp,
  MessageSquareText,
  History,
  Server,
  Layers
} from 'lucide-react';

interface Props {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  hasActiveWorkflow?: boolean;
}

interface NavSection {
  title?: string;
  items: {
    id: string;
    label: string;
    icon: React.ComponentType<{ size?: number; color?: string }>;
    badge?: string | null;
    badgeColor?: string;
  }[];
}

export const Sidebar: React.FC<Props> = ({ activeTab, setActiveTab, hasActiveWorkflow }) => {
  const sections: NavSection[] = [
    {
      items: [
        { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
      ],
    },
    {
      title: 'Master Data Modules',
      items: [
        { id: 'item-master', label: 'Item Master', icon: Package },
        { id: 'business-partner', label: 'Business Partner', icon: Users },
        { id: 'warehouse-master', label: 'Warehouse Master', icon: Warehouse },
      ],
    },
    {
      items: [
        { id: 'upload', label: 'Multi-Doc Workflow', icon: FileUp, badge: hasActiveWorkflow ? 'Active' : null },
        { id: 'chat', label: 'Conversational AI', icon: MessageSquareText },
        { id: 'audit', label: 'Audit Trail', icon: History },
        { id: 'sap', label: 'Service Layer Config', icon: Server },
      ],
    },
  ];

  return (
    <aside className="sidebar">
      <div style={{ padding: '16px 16px 14px', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{
          padding: '12px 16px',
          background: '#0A0A0A',
          borderRadius: 14,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <img src={cinntraLogo} alt="CINNTRA" style={{ height: 38, width: 'auto', maxWidth: 160, objectFit: 'contain', display: 'block' }} />
          <span style={{ fontSize: 12, fontWeight: 800, padding: '4px 10px', borderRadius: 9999, background: '#1A56DB', color: '#FFFFFF', letterSpacing: '0.8px' }}>SAP</span>
        </div>
      </div>

      <nav style={{ padding: '16px 12px', display: 'flex', flexDirection: 'column', gap: 16, flex: 1, overflowY: 'auto' }}>
        {sections.map((section, sIdx) => (
          <div key={sIdx} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {section.title && (
              <div style={{
                padding: '4px 14px 6px',
                fontSize: 11,
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: 0.8,
                color: 'var(--text-muted)'
              }}>
                {section.title}
              </div>
            )}
            {section.items.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-md)',
                    background: isActive ? 'linear-gradient(90deg, rgba(59, 130, 246, 0.18) 0%, rgba(59, 130, 246, 0.05) 100%)' : 'transparent',
                    color: isActive ? '#60A5FA' : 'var(--text-secondary)',
                    border: isActive ? '1px solid rgba(59, 130, 246, 0.35)' : '1px solid transparent',
                    fontWeight: isActive ? 600 : 500,
                    fontSize: 13.5,
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <Icon size={18} color={isActive ? '#3B82F6' : 'currentColor'} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span style={{
                      fontSize: 10,
                      fontWeight: 700,
                      padding: '2px 7px',
                      borderRadius: 10,
                      background: item.badgeColor ? `${item.badgeColor}22` : 'rgba(59, 130, 246, 0.25)',
                      color: item.badgeColor || '#93C5FD',
                      border: `1px solid ${item.badgeColor ? `${item.badgeColor}44` : 'rgba(59, 130, 246, 0.3)'}`
                    }}>
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      <div style={{ padding: '16px 20px', borderTop: '1px solid var(--border-subtle)', fontSize: 12, color: 'var(--text-muted)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
          <Layers size={13} color="#10B981" />
          <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>SAP v10.0</span>
        </div>
        <p style={{ marginTop: 2, fontSize: 11 }}>Zero Direct SQL Writes Enforced</p>
      </div>
    </aside>
  );
};

