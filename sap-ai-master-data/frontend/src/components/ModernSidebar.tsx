import React from 'react';
import {
  LayoutDashboard,
  ShoppingBag,
  Package,
  Users,
  Store,
  Settings,
  HelpCircle,
  LogOut,
  Sparkles
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import cinntraLogo from '../assets/cinntra_logo.png';

interface Props {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  orderCount?: number;
  itemCount?: number;
  bpCount?: number;
  whCount?: number;
}

export const ModernSidebar: React.FC<Props> = ({
  activeTab,
  setActiveTab,
  orderCount = 0,
  itemCount = 0,
  bpCount = 0,
  whCount = 0
}) => {
  const { user, logout } = useAuth();

  return (
    <aside className="md-sidebar">
      <div>
        {/* CINNTRA Brand Header in Midnight Navy Rail */}
        <div
          onClick={() => setActiveTab('dashboard')}
          className="md-brand-header"
          style={{
            padding: '14px 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'rgba(255, 255, 255, 0.07)',
            borderRadius: 16,
            border: '1px solid rgba(255, 255, 255, 0.15)',
            marginBottom: 20,
            boxShadow: '0 6px 18px rgba(0, 0, 0, 0.28)',
            cursor: 'pointer',
            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
          }}
          title="CINNTRA • SAP Master Data Automation Platform"
        >
          <img
            src={cinntraLogo}
            alt="CINNTRA"
            style={{
              height: 40,
              width: 'auto',
              maxWidth: 165,
              objectFit: 'contain',
              display: 'block',
              filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.25))'
            }}
          />
          <span style={{
            fontSize: 12,
            fontWeight: 800,
            padding: '4px 11px',
            borderRadius: 9999,
            background: '#1A56DB',
            color: '#FFFFFF',
            border: '1px solid rgba(255, 255, 255, 0.25)',
            letterSpacing: '0.8px',
            textTransform: 'uppercase',
            boxShadow: '0 2px 8px rgba(26, 86, 219, 0.45)'
          }}>
            SAP
          </span>
        </div>

        {/* Navigation Items Group */}
        <div className="md-nav-group">
          {/* Dashboard */}
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`md-nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
          >
            <div className="md-nav-item-left">
              <LayoutDashboard size={18} color={activeTab === 'dashboard' ? '#FFFFFF' : '#94A3B8'} />
              <span>Dashboard</span>
            </div>
          </button>

          {/* Hey CIRA - Autonomous SAP AI Agent */}
          <button
            onClick={() => setActiveTab('ai-agent')}
            className={`md-nav-item ${activeTab === 'ai-agent' ? 'active' : ''}`}
            title="Hey CIRA (Universal Field Updates & Master Data Queries)"
          >
            <div className="md-nav-item-left">
              <Sparkles size={18} color={activeTab === 'ai-agent' ? '#FFFFFF' : '#60A5FA'} />
              <span style={{ fontWeight: activeTab === 'ai-agent' ? 700 : 500 }}>Hey CIRA</span>
            </div>
            <span style={{
              fontSize: 10,
              fontWeight: 700,
              padding: '2px 7px',
              borderRadius: 9999,
              background: activeTab === 'ai-agent' ? 'rgba(255, 255, 255, 0.25)' : '#1A56DB',
              color: '#FFFFFF',
              letterSpacing: '0.4px',
              boxShadow: '0 2px 6px rgba(26, 86, 219, 0.3)'
            }}>AI</span>
          </button>

          {/* Orders / Workflows (with badge) */}
          <button
            onClick={() => setActiveTab('upload')}
            className={`md-nav-item ${activeTab === 'upload' || activeTab === 'orders' ? 'active' : ''}`}
            title="Master Data Upload & Extraction Workflows"
          >
            <div className="md-nav-item-left">
              <ShoppingBag size={18} color={activeTab === 'upload' || activeTab === 'orders' ? '#FFFFFF' : '#94A3B8'} />
              <span>Workflows & Upload</span>
            </div>
            <span style={{
              fontSize: 11,
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: 9999,
              background: (activeTab === 'upload' || activeTab === 'orders') ? 'rgba(255, 255, 255, 0.25)' : 'rgba(255, 255, 255, 0.1)',
              color: (activeTab === 'upload' || activeTab === 'orders') ? '#FFFFFF' : '#93C5FD',
              border: (activeTab === 'upload' || activeTab === 'orders') ? '1px solid rgba(255,255,255,0.3)' : '1px solid rgba(255, 255, 255, 0.15)'
            }}>{orderCount}</span>
          </button>

          {/* Products / Item Master */}
          <button
            onClick={() => setActiveTab('item-master')}
            className={`md-nav-item ${activeTab === 'item-master' || activeTab === 'products' ? 'active' : ''}`}
            title="SAP Item Master"
          >
            <div className="md-nav-item-left">
              <Package size={18} color={activeTab === 'item-master' || activeTab === 'products' ? '#FFFFFF' : '#94A3B8'} />
              <span>Items</span>
            </div>
            <span style={{
              fontSize: 10.5,
              fontWeight: 700,
              padding: '2px 7px',
              borderRadius: 9999,
              background: (activeTab === 'item-master' || activeTab === 'products') ? 'rgba(255, 255, 255, 0.25)' : 'rgba(255, 255, 255, 0.1)',
              color: (activeTab === 'item-master' || activeTab === 'products') ? '#FFFFFF' : '#93C5FD',
              border: (activeTab === 'item-master' || activeTab === 'products') ? '1px solid rgba(255, 255, 255, 0.3)' : '1px solid rgba(255, 255, 255, 0.15)'
            }}>{itemCount}</span>
          </button>

          {/* Customers / Business Partner */}
          <button
            onClick={() => setActiveTab('business-partner')}
            className={`md-nav-item ${activeTab === 'business-partner' || activeTab === 'customers' ? 'active' : ''}`}
            title="SAP Business Partners (Customers, Suppliers, Leads)"
          >
            <div className="md-nav-item-left">
              <Users size={18} color={activeTab === 'business-partner' || activeTab === 'customers' ? '#FFFFFF' : '#94A3B8'} />
              <span>Partners</span>
            </div>
            <span style={{
              fontSize: 10.5,
              fontWeight: 700,
              padding: '2px 7px',
              borderRadius: 9999,
              background: (activeTab === 'business-partner' || activeTab === 'customers') ? 'rgba(255, 255, 255, 0.25)' : 'rgba(255, 255, 255, 0.1)',
              color: (activeTab === 'business-partner' || activeTab === 'customers') ? '#FFFFFF' : '#93C5FD',
              border: (activeTab === 'business-partner' || activeTab === 'customers') ? '1px solid rgba(255, 255, 255, 0.3)' : '1px solid rgba(255, 255, 255, 0.15)'
            }}>{bpCount}</span>
          </button>

          {/* Warehouses */}
          <button
            onClick={() => setActiveTab('warehouse-master')}
            className={`md-nav-item ${activeTab === 'warehouse-master' || activeTab === 'online-store' ? 'active' : ''}`}
            title="SAP Warehouse Master"
          >
            <div className="md-nav-item-left">
              <Store size={18} color={activeTab === 'warehouse-master' || activeTab === 'online-store' ? '#FFFFFF' : '#94A3B8'} />
              <span>Warehouses</span>
            </div>
            <span style={{
              fontSize: 10.5,
              fontWeight: 700,
              padding: '2px 7px',
              borderRadius: 9999,
              background: (activeTab === 'warehouse-master' || activeTab === 'online-store') ? 'rgba(255, 255, 255, 0.25)' : 'rgba(255, 255, 255, 0.1)',
              color: (activeTab === 'warehouse-master' || activeTab === 'online-store') ? '#FFFFFF' : '#93C5FD',
              border: (activeTab === 'warehouse-master' || activeTab === 'online-store') ? '1px solid rgba(255, 255, 255, 0.3)' : '1px solid rgba(255, 255, 255, 0.15)'
            }}>{whCount}</span>
          </button>
        </div>
      </div>

      {/* Bottom Area: Settings, Help & Support, User Profile */}
      <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: 6, paddingTop: 12 }}>
        <div className="md-nav-group">
          <button
            onClick={() => setActiveTab('sap')}
            className={`md-nav-item ${activeTab === 'sap' || activeTab === 'settings' ? 'active' : ''}`}
            title="SAP Service Layer Connection Manager"
            style={{ padding: '8px 12px' }}
          >
            <div className="md-nav-item-left">
              <Settings size={17} color={activeTab === 'sap' || activeTab === 'settings' ? '#FFFFFF' : '#94A3B8'} />
              <span>Settings (SAP Config)</span>
            </div>
          </button>

          <button
            onClick={() => setActiveTab('help')}
            className={`md-nav-item ${activeTab === 'help' ? 'active' : ''}`}
            title="SAP Documentation & RAG Knowledge Base"
            style={{ padding: '8px 12px' }}
          >
            <div className="md-nav-item-left">
              <HelpCircle size={17} color={activeTab === 'help' ? '#FFFFFF' : '#94A3B8'} />
              <span>Help (SAP RAG Docs)</span>
            </div>
          </button>
        </div>

        {/* User Profile & Sign Out Footer */}
        {user && (
          <div
            style={{
              padding: '8px 10px',
              background: 'rgba(255, 255, 255, 0.07)',
              borderRadius: 14,
              border: '1px solid rgba(255, 255, 255, 0.12)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: 8,
              boxShadow: '0 2px 6px rgba(0,0,0,0.15)'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
              <div
                style={{
                  width: 30,
                  height: 30,
                  borderRadius: '50%',
                  background: '#1A56DB',
                  color: '#FFFFFF',
                  fontSize: 12,
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}
              >
                {user.name ? user.name.charAt(0).toUpperCase() : 'A'}
              </div>
              <div style={{ minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 12,
                    fontWeight: 600,
                    color: '#FFFFFF',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}
                  title={user.name}
                >
                  {user.name}
                </div>
                <div
                  style={{
                    fontSize: 10,
                    color: '#94A3B8',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}
                  title={user.email}
                >
                  {user.email}
                </div>
              </div>
            </div>

            <button
              onClick={logout}
              title="Sign Out"
              style={{
                background: 'none',
                border: 'none',
                color: '#94A3B8',
                cursor: 'pointer',
                padding: '5px',
                borderRadius: 7,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                transition: 'all 0.15s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = '#EF4444';
                e.currentTarget.style.background = 'rgba(239, 68, 68, 0.15)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = '#94A3B8';
                e.currentTarget.style.background = 'none';
              }}
            >
              <LogOut size={15} />
            </button>
          </div>
        )}
      </div>

    </aside>
  );
};
