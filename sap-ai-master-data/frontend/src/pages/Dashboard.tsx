import React, { useEffect, useState, useCallback, useRef } from 'react';
import { api } from '../services/api';
import type { DashboardStats, WorkflowSummary, AuditLogRecord } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import {
  FileText,
  Package,
  Users,
  Building2,
  AlertOctagon,
  ArrowUpRight,
  PlusCircle,
  Activity,
  Database,
  Search,
  RefreshCw,
  Eye,
  ChevronLeft,
  ChevronRight,
  Copy,
  Check,
  ShieldCheck,
  Layers,
  X,
  ArrowRight
} from 'lucide-react';

interface Props {
  onStartUpload: () => void;
  onViewAudit: () => void;
  onNavigateToModule?: (module: string) => void;
}

type EntityTab = 'Items' | 'BusinessPartners' | 'Warehouses' | 'Workflows' | 'AuditLogs';

export const Dashboard: React.FC<Props> = ({ onStartUpload, onViewAudit, onNavigateToModule }) => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [sapHealth, setSapHealth] = useState<{ connected: boolean; status: string; company_db?: string } | null>(null);
  const [loadingStats, setLoadingStats] = useState(true);

  // Master Data Records Explorer State
  const [activeTab, setActiveTab] = useState<EntityTab>('Items');
  const [records, setRecords] = useState<any[]>([]);
  const [recordsTotal, setRecordsTotal] = useState<number>(0);
  const [loadingRecords, setLoadingRecords] = useState(false);
  const [page, setPage] = useState(0);
  const pageSize = 12;
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  // Record Inspector Modal State
  const [inspectedRecord, setInspectedRecord] = useState<any | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Debounce search term
  const searchTimeout = useRef<any>(null);
  const handleSearchChange = (val: string) => {
    setSearchTerm(val);
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => {
      setDebouncedSearch(val);
      setPage(0);
    }, 400);
  };

  // Fetch Dashboard Stats (KPIs, recent workflows, audit logs)
  const fetchStats = useCallback(async () => {
    setLoadingStats(true);
    try {
      const [data, health] = await Promise.allSettled([
        api.getDashboardStats(),
        api.getSapHealth()
      ]);
      if (data.status === 'fulfilled') setStats(data.value);
      if (health.status === 'fulfilled') setSapHealth(health.value);
    } catch (err) {
      console.error('Failed to load dashboard metrics', err);
    } finally {
      setLoadingStats(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  // Fetch Records based on active tab
  const fetchRecords = useCallback(async () => {
    setLoadingRecords(true);
    try {
      if (activeTab === 'Items' || activeTab === 'BusinessPartners' || activeTab === 'Warehouses') {
        const res = await api.getSapRecords(activeTab, pageSize, page * pageSize, debouncedSearch);
        setRecords(res.records || []);
        setRecordsTotal(res.total || 0);
      } else if (activeTab === 'Workflows') {
        const workflows = await api.getWorkflows(50, 0);
        const filtered = debouncedSearch
          ? workflows.filter(w =>
            (w.filename || '').toLowerCase().includes(debouncedSearch.toLowerCase()) ||
            (w.workflow_id || '').toLowerCase().includes(debouncedSearch.toLowerCase()) ||
            (w.sap_object_id || '').toLowerCase().includes(debouncedSearch.toLowerCase())
          )
          : workflows;
        setRecords(filtered.slice(page * pageSize, (page + 1) * pageSize));
        setRecordsTotal(filtered.length);
      } else if (activeTab === 'AuditLogs') {
        const logs = await api.getAuditLogs({ limit: 100 });
        const filtered = debouncedSearch
          ? logs.filter(l =>
            (l.sap_object_id || '').toLowerCase().includes(debouncedSearch.toLowerCase()) ||
            (l.workflow_id || '').toLowerCase().includes(debouncedSearch.toLowerCase()) ||
            (l.master_type || '').toLowerCase().includes(debouncedSearch.toLowerCase())
          )
          : logs;
        setRecords(filtered.slice(page * pageSize, (page + 1) * pageSize));
        setRecordsTotal(filtered.length);
      }
    } catch (err) {
      console.error('Failed to load records for tab:', activeTab, err);
      setRecords([]);
      setRecordsTotal(0);
    } finally {
      setLoadingRecords(false);
    }
  }, [activeTab, page, debouncedSearch]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  // Copy helper
  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const totalPages = Math.ceil(recordsTotal / pageSize);

  // Live KPI metric cards values
  const itemsCount = stats?.items_total ?? stats?.sap_counts?.Items ?? stats?.items_created ?? 0;
  const bpCount = stats?.business_partners_total ?? stats?.sap_counts?.BusinessPartners ?? stats?.business_partners_created ?? 0;
  const whCount = stats?.warehouses_total ?? stats?.sap_counts?.Warehouses ?? stats?.warehouses_created ?? 0;
  const docsCount = stats?.documents_processed ?? 0;
  const failedOps = stats?.failed_operations ?? 0;

  const cards = [
    {
      title: 'Items in Database',
      value: itemsCount.toLocaleString(),
      subtitle: stats?.items_created ? `${stats.items_created} automated via platform` : 'SAP Master Catalog',
      icon: Package,
      color: '#10B981',
      bg: 'rgba(16, 185, 129, 0.12)',
      tabKey: 'Items' as EntityTab,
    },
    {
      title: 'Business Partners',
      value: bpCount.toLocaleString(),
      subtitle: 'Customers, Vendors & Leads',
      icon: Users,
      color: '#8B5CF6',
      bg: 'rgba(139, 92, 246, 0.12)',
      tabKey: 'BusinessPartners' as EntityTab,
    },
    {
      title: 'Warehouses in DB',
      value: whCount.toLocaleString(),
      subtitle: 'Distribution Centers & Storage',
      icon: Building2,
      color: '#06B6D4',
      bg: 'rgba(6, 182, 212, 0.12)',
      tabKey: 'Warehouses' as EntityTab,
    },
    {
      title: 'Documents Processed',
      value: docsCount.toLocaleString(),
      subtitle: 'PDF Extractions & Workflows',
      icon: FileText,
      color: '#3B82F6',
      bg: 'rgba(59, 130, 246, 0.12)',
      tabKey: 'Workflows' as EntityTab,
    },
    {
      title: 'Failed Operations',
      value: failedOps.toLocaleString(),
      subtitle: 'Protected by Deterministic Gate',
      icon: AlertOctagon,
      color: failedOps > 0 ? '#EF4444' : '#64748B',
      bg: failedOps > 0 ? 'rgba(239, 68, 68, 0.12)' : 'rgba(100, 116, 139, 0.12)',
      tabKey: 'AuditLogs' as EntityTab,
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      {/* Hero Welcome Banner */}
      <div className="glass-panel" style={{
        padding: '30px 32px',
        background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.85) 100%)',
        position: 'relative',
        overflow: 'hidden',
        border: '1px solid rgba(59, 130, 246, 0.25)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)'
      }}>
        <div style={{
          position: 'absolute',
          top: -60,
          right: -60,
          width: 260,
          height: 260,
          background: 'radial-gradient(circle, rgba(59, 130, 246, 0.2) 0%, transparent 70%)',
          borderRadius: '50%',
          pointerEvents: 'none'
        }} />

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 20 }}>
          <div style={{ maxWidth: 660 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8, flexWrap: 'wrap' }}>
              <span style={{
                fontSize: 11,
                fontWeight: 700,
                color: sapHealth?.connected ? '#60A5FA' : '#F87171',
                textTransform: 'uppercase',
                letterSpacing: 1.2,
                background: sapHealth?.connected ? 'rgba(59, 130, 246, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                padding: '4px 10px',
                borderRadius: '4px',
                border: `1px solid ${sapHealth?.connected ? 'rgba(59, 130, 246, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
              }}>
                {sapHealth?.connected ? 'SAP  10.0 • Connected' : 'SAP  • Not Connected'}
              </span>
              <span style={{
                fontSize: 11,
                fontWeight: 600,
                color: sapHealth?.connected ? '#34D399' : '#F87171',
                display: 'flex',
                alignItems: 'center',
                gap: 5
              }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: sapHealth?.connected ? '#10B981' : '#EF4444', display: 'inline-block' }} />
                {sapHealth?.connected ? (stats?.database?.company_db || 'Connected DB') : 'Not Connected'}
              </span>
            </div>
            <h2 style={{ fontSize: 26, fontWeight: 700, marginTop: 4, marginBottom: 8, letterSpacing: -0.5, color: '#F8FAFC' }}>
              Live Enterprise Master Data Orchestration
            </h2>
            <p style={{ fontSize: 13.5, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              Real-time synchronization with SAP database. Multi-engine PDF ingestion, deterministic validation, consensus resolution, and zero-SQL master data creation strictly through the SAP Service Layer.
            </p>
          </div>

          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <button
              onClick={() => { fetchStats(); fetchRecords(); }}
              className="btn btn-secondary"
              style={{ padding: '10px 16px', fontSize: 13, gap: 8 }}
              title="Refresh all metrics and database records"
            >
              <RefreshCw size={15} className={loadingStats || loadingRecords ? 'pulse-animation' : ''} />
              Refresh Data
            </button>
            <button onClick={onStartUpload} className="btn btn-primary" style={{ padding: '11px 20px', fontSize: 14 }}>
              <PlusCircle size={17} /> New Document Process
            </button>
          </div>
        </div>
      </div>

      {/* Dedicated Master Data Modules Bar */}
      {onNavigateToModule && (
        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
          {[
            { id: 'item-master', label: 'Item Master', icon: Package, color: '#38BDF8', desc: 'Direct posting & PDF spec upload' },
            { id: 'business-partner', label: 'Business Partner', icon: Users, color: '#A78BFA', desc: 'Vendors, customers & leads' },
            { id: 'warehouse-master', label: 'Warehouse Master', icon: Building2, color: '#34D399', desc: 'Depots & logistics facilities' },
          ].map((mod) => {
            const Icon = mod.icon;
            return (
              <button
                key={mod.id}
                onClick={() => onNavigateToModule(mod.id)}
                className="glass-panel"
                style={{
                  flex: '1 1 240px',
                  padding: '16px 20px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 14,
                  textAlign: 'left',
                  cursor: 'pointer',
                  border: `1px solid ${mod.color}33`,
                  background: `linear-gradient(135deg, ${mod.color}10 0%, rgba(15, 23, 42, 0.6) 100%)`,
                  transition: 'all 0.2s ease',
                }}
              >
                <div style={{
                  width: 40,
                  height: 40,
                  borderRadius: 8,
                  background: `${mod.color}22`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  <Icon size={20} color={mod.color} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: 14, color: '#F8FAFC' }}>{mod.label}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{mod.desc}</div>
                </div>
                <ArrowRight size={15} color={mod.color} />
              </button>
            );
          })}
        </div>
      )}

      {/* KPI Metric Cards */}
      <div className="grid-3" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))' }}>
        {cards.map((card, idx) => {
          const Icon = card.icon;
          const isSelected = activeTab === card.tabKey;
          return (
            <div
              key={idx}
              className="glass-panel"
              onClick={() => {
                setActiveTab(card.tabKey);
                setPage(0);
                setSearchTerm('');
                setDebouncedSearch('');
              }}
              style={{
                padding: '20px 22px',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                border: isSelected ? `1.5px solid ${card.color}` : '1px solid var(--border-subtle)',
                background: isSelected ? 'rgba(30, 41, 59, 0.85)' : undefined,
                boxShadow: isSelected ? `0 4px 20px ${card.color}25` : undefined
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                <span style={{ fontSize: 12.5, color: 'var(--text-secondary)', fontWeight: 600 }}>
                  {card.title}
                </span>
                <div style={{
                  width: 36,
                  height: 36,
                  borderRadius: 8,
                  background: card.bg,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Icon size={18} color={card.color} />
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginBottom: 4 }}>
                <span style={{ fontSize: 26, fontWeight: 700, letterSpacing: -0.5, color: '#F8FAFC' }}>
                  {loadingStats ? '...' : card.value}
                </span>
                <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>records</span>
              </div>
              <p style={{ fontSize: 11, color: isSelected ? card.color : 'var(--text-muted)', fontWeight: isSelected ? 600 : 400 }}>
                {card.subtitle}
              </p>
            </div>
          );
        })}
      </div>

      {/* Real Master Data Records Explorer */}
      <div className="glass-panel" style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 20 }}>
        {/* Header with Title and Entity Selector Tabs */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 36,
              height: 36,
              borderRadius: 8,
              background: 'rgba(59, 130, 246, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Database size={18} color="#3B82F6" />
            </div>
            <div>
              <h3 style={{ fontSize: 17, fontWeight: 700, letterSpacing: -0.3, display: 'flex', alignItems: 'center', gap: 8 }}>
                Live Database Master Records
                {stats?.database?.company_db && (
                  <span style={{
                    fontSize: 11,
                    fontWeight: 600,
                    color: '#10B981',
                    background: 'rgba(16, 185, 129, 0.1)',
                    padding: '2px 8px',
                    borderRadius: 12,
                    border: '1px solid rgba(16, 185, 129, 0.25)'
                  }}>
                    {stats.database.company_db}
                  </span>
                )}
              </h3>
              <p style={{ fontSize: 12.5, color: 'var(--text-secondary)' }}>
                Authoritative records queried directly from SAP database via Service Layer
              </p>
            </div>
          </div>

          {/* Quick Actions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <button
              onClick={fetchRecords}
              className="btn btn-secondary"
              style={{ padding: '7px 12px', fontSize: 12, gap: 6 }}
              title="Refresh table"
            >
              <RefreshCw size={13} className={loadingRecords ? 'pulse-animation' : ''} />
              Refresh
            </button>
            <button
              onClick={onViewAudit}
              className="btn btn-secondary"
              style={{ padding: '7px 14px', fontSize: 12, gap: 6 }}
            >
              Audit Trail <ArrowUpRight size={13} />
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div style={{
          display: 'flex',
          gap: 6,
          borderBottom: '1px solid var(--border-subtle)',
          paddingBottom: 2,
          overflowX: 'auto'
        }}>
          {[
            { key: 'Items' as EntityTab, label: 'Items Master', count: itemsCount, icon: Package, color: '#10B981' },
            { key: 'BusinessPartners' as EntityTab, label: 'Business Partners', count: bpCount, icon: Users, color: '#8B5CF6' },
            { key: 'Warehouses' as EntityTab, label: 'Warehouses', count: whCount, icon: Building2, color: '#06B6D4' },
            { key: 'Workflows' as EntityTab, label: 'Document Workflows', count: docsCount, icon: FileText, color: '#3B82F6' },
            { key: 'AuditLogs' as EntityTab, label: 'Audit Transactions', count: stats?.recent_activity?.length ?? 0, icon: Activity, color: '#F59E0B' },
          ].map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => {
                  setActiveTab(tab.key);
                  setPage(0);
                  setSearchTerm('');
                  setDebouncedSearch('');
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '10px 16px',
                  background: isActive ? 'rgba(30, 41, 59, 0.8)' : 'transparent',
                  border: 'none',
                  borderBottom: isActive ? `2px solid ${tab.color}` : '2px solid transparent',
                  color: isActive ? '#F8FAFC' : 'var(--text-secondary)',
                  fontWeight: isActive ? 600 : 500,
                  fontSize: 13,
                  cursor: 'pointer',
                  borderRadius: '6px 6px 0 0',
                  transition: 'all 0.15s ease',
                  whiteSpace: 'nowrap'
                }}
              >
                <Icon size={15} color={isActive ? tab.color : 'var(--text-muted)'} />
                <span>{tab.label}</span>
                <span style={{
                  fontSize: 11,
                  padding: '2px 7px',
                  borderRadius: 10,
                  background: isActive ? `${tab.color}25` : 'rgba(15, 23, 42, 0.6)',
                  color: isActive ? tab.color : 'var(--text-muted)',
                  fontWeight: 600
                }}>
                  {tab.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* Search & Filter Toolbar */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', flex: 1, minWidth: 260, maxWidth: 460 }}>
            <Search
              size={15}
              color="var(--text-muted)"
              style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)' }}
            />
            <input
              type="text"
              value={searchTerm}
              onChange={e => handleSearchChange(e.target.value)}
              placeholder={
                activeTab === 'Items'
                  ? 'Search by ItemCode or ItemName (e.g. OSWSFG01, core, timber)...'
                  : activeTab === 'BusinessPartners'
                    ? 'Search by CardCode or CardName (e.g. C0043, ABC Exports)...'
                    : activeTab === 'Warehouses'
                      ? 'Search by WarehouseCode or Name (e.g. Sec-63, Noida)...'
                      : 'Search by Filename, Object ID, or Workflow ID...'
              }
              style={{
                width: '100%',
                padding: '9px 34px 9px 36px',
                background: 'rgba(11, 17, 32, 0.8)',
                border: '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                color: '#F8FAFC',
                fontSize: 13,
                outline: 'none'
              }}
            />
            {searchTerm && (
              <button
                onClick={() => {
                  setSearchTerm('');
                  setDebouncedSearch('');
                  setPage(0);
                }}
                style={{
                  position: 'absolute',
                  right: 10,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: 2
                }}
              >
                <X size={14} />
              </button>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 12, color: 'var(--text-muted)' }}>
            <span>
              Showing {recordsTotal > 0 ? page * pageSize + 1 : 0} - {Math.min((page + 1) * pageSize, recordsTotal)} of {recordsTotal.toLocaleString()} records
            </span>
          </div>
        </div>

        {/* Dynamic Records Table */}
        <div style={{ overflowX: 'auto', minHeight: 340 }}>
          {loadingRecords ? (
            <div style={{ textAlign: 'center', padding: '60px 12px', color: 'var(--text-secondary)' }}>
              <RefreshCw size={28} className="pulse-animation" style={{ margin: '0 auto 12px', color: '#3B82F6' }} />
              <p style={{ fontSize: 14, fontWeight: 500 }}>Fetching live records from SAP Service Layer...</p>
              <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                Querying entity <code>{activeTab}</code> from company database <code>{stats?.database?.company_db || 'SAP'}</code>
              </p>
            </div>
          ) : records.length > 0 ? (
            <table className="data-table">
              <thead>
                {activeTab === 'Items' && (
                  <tr>
                    <th>Item Code</th>
                    <th>Item Description / Name</th>
                    <th>Groups</th>
                    <th>Created Date</th>
                    <th>Updated Date</th>
                    <th>SAP Database Status</th>
                    <th style={{ textAlign: 'center', width: 120 }}>Actions</th>
                  </tr>
                )}
                {activeTab === 'BusinessPartners' && (
                  <tr>
                    <th>Card Code</th>
                    <th>Business Partner Name</th>
                    <th>Type</th>
                    <th>Federal Tax ID</th>
                    <th>Created Date</th>
                    <th>Status</th>
                    <th style={{ textAlign: 'center', width: 120 }}>Actions</th>
                  </tr>
                )}
                {activeTab === 'Warehouses' && (
                  <tr>
                    <th>Warehouse Code</th>
                    <th>Warehouse Name</th>
                    <th>Location</th>
                    <th>City / State</th>
                    <th>State in SAP</th>
                    <th style={{ textAlign: 'center', width: 120 }}>Actions</th>
                  </tr>
                )}
                {activeTab === 'Workflows' && (
                  <tr>
                    <th>Document File</th>
                    <th>Master Type</th>
                    <th>Workflow Status</th>
                    <th>SAP Object ID</th>
                    <th>Created Timestamp</th>
                    <th style={{ textAlign: 'center', width: 120 }}>Actions</th>
                  </tr>
                )}
                {activeTab === 'AuditLogs' && (
                  <tr>
                    <th>Timestamp</th>
                    <th>Master Type</th>
                    <th>Action</th>
                    <th>SAP Identifier</th>
                    <th>Status</th>
                    <th>Payload Hash</th>
                    <th style={{ textAlign: 'center', width: 120 }}>Actions</th>
                  </tr>
                )}
              </thead>
              <tbody>
                {activeTab === 'Items' && records.map((item, idx) => (
                  <tr key={idx}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ fontWeight: 600, color: '#60A5FA', fontFamily: 'monospace' }}>
                          {item.ItemCode}
                        </span>
                        <button
                          onClick={() => handleCopy(item.ItemCode, `item-${idx}`)}
                          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2, color: copiedKey === `item-${idx}` ? '#10B981' : 'var(--text-muted)' }}
                          title="Copy ItemCode"
                        >
                          {copiedKey === `item-${idx}` ? <Check size={12} /> : <Copy size={12} />}
                        </button>
                      </div>
                    </td>
                    <td style={{ fontWeight: 500, color: '#F1F5F9', maxWidth: 300 }}>
                      {item.ItemName || 'Unnamed Item'}
                    </td>
                    <td>
                      <span className="badge badge-info" style={{ fontSize: 11 }}>
                        Group {item.ItemsGroupCode ?? 'N/A'}
                      </span>
                    </td>
                    <td style={{ fontSize: 12.5, color: 'var(--text-muted)' }}>
                      {item.CreateDate ? new Date(item.CreateDate).toLocaleDateString() : '—'}
                    </td>
                    <td style={{ fontSize: 12.5, color: 'var(--text-muted)' }}>
                      {item.UpdateDate ? new Date(item.UpdateDate).toLocaleDateString() : '—'}
                    </td>
                    <td>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 5,
                        fontSize: 11.5,
                        fontWeight: 600,
                        color: '#34D399',
                        background: 'rgba(16, 185, 129, 0.12)',
                        padding: '3px 8px',
                        borderRadius: 6
                      }}>
                        <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#10B981' }} />
                        Live in SAP
                      </span>
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <button
                        onClick={() => setInspectedRecord({ type: 'Item', data: item })}
                        className="btn btn-secondary"
                        style={{ padding: '4px 10px', fontSize: 11 }}
                      >
                        <Eye size={12} /> Inspect
                      </button>
                    </td>
                  </tr>
                ))}

                {activeTab === 'BusinessPartners' && records.map((bp, idx) => (
                  <tr key={idx}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ fontWeight: 600, color: '#A78BFA', fontFamily: 'monospace' }}>
                          {bp.CardCode}
                        </span>
                        <button
                          onClick={() => handleCopy(bp.CardCode, `bp-${idx}`)}
                          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2, color: copiedKey === `bp-${idx}` ? '#10B981' : 'var(--text-muted)' }}
                          title="Copy CardCode"
                        >
                          {copiedKey === `bp-${idx}` ? <Check size={12} /> : <Copy size={12} />}
                        </button>
                      </div>
                    </td>
                    <td style={{ fontWeight: 500, color: '#F1F5F9', maxWidth: 300 }}>
                      {bp.CardName || 'Unnamed Business Partner'}
                    </td>
                    <td>
                      <span style={{
                        fontSize: 11,
                        padding: '3px 8px',
                        borderRadius: 4,
                        fontWeight: 600,
                        background: bp.CardType === 'cCustomer' ? 'rgba(59, 130, 246, 0.15)' : 'rgba(139, 92, 246, 0.15)',
                        color: bp.CardType === 'cCustomer' ? '#60A5FA' : '#C084FC'
                      }}>
                        {bp.CardType === 'cCustomer' ? 'Customer' : bp.CardType === 'cSupplier' ? 'Vendor' : (bp.CardType || 'Partner')}
                      </span>
                    </td>
                    <td style={{ fontSize: 12, fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                      {bp.FederalTaxID || '—'}
                    </td>
                    <td style={{ fontSize: 12.5, color: 'var(--text-muted)' }}>
                      {bp.CreateDate ? new Date(bp.CreateDate).toLocaleDateString() : '—'}
                    </td>
                    <td>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 5,
                        fontSize: 11.5,
                        fontWeight: 600,
                        color: '#34D399',
                        background: 'rgba(16, 185, 129, 0.12)',
                        padding: '3px 8px',
                        borderRadius: 6
                      }}>
                        <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#10B981' }} />
                        Active
                      </span>
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <button
                        onClick={() => setInspectedRecord({ type: 'Business Partner', data: bp })}
                        className="btn btn-secondary"
                        style={{ padding: '4px 10px', fontSize: 11 }}
                      >
                        <Eye size={12} /> Inspect
                      </button>
                    </td>
                  </tr>
                ))}

                {activeTab === 'Warehouses' && records.map((wh, idx) => (
                  <tr key={idx}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ fontWeight: 600, color: '#38BDF8', fontFamily: 'monospace' }}>
                          {wh.WarehouseCode}
                        </span>
                        <button
                          onClick={() => handleCopy(wh.WarehouseCode, `wh-${idx}`)}
                          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2, color: copiedKey === `wh-${idx}` ? '#10B981' : 'var(--text-muted)' }}
                          title="Copy WarehouseCode"
                        >
                          {copiedKey === `wh-${idx}` ? <Check size={12} /> : <Copy size={12} />}
                        </button>
                      </div>
                    </td>
                    <td style={{ fontWeight: 500, color: '#F1F5F9', maxWidth: 300 }}>
                      {wh.WarehouseName || 'Unnamed Warehouse'}
                    </td>
                    <td style={{ fontSize: 12.5, color: 'var(--text-secondary)' }}>
                      {wh.City || '—'}
                    </td>
                    <td style={{ fontSize: 12.5, color: 'var(--text-muted)' }}>
                      {wh.State || '—'}
                    </td>
                    <td>
                      <span style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 5,
                        fontSize: 11.5,
                        fontWeight: 600,
                        color: wh.Inactive === 'tYES' ? '#F87171' : '#34D399',
                        background: wh.Inactive === 'tYES' ? 'rgba(239, 68, 68, 0.12)' : 'rgba(16, 185, 129, 0.12)',
                        padding: '3px 8px',
                        borderRadius: 6
                      }}>
                        <span style={{ width: 6, height: 6, borderRadius: '50%', background: wh.Inactive === 'tYES' ? '#EF4444' : '#10B981' }} />
                        {wh.Inactive === 'tYES' ? 'Inactive' : 'Active'}
                      </span>
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <button
                        onClick={() => setInspectedRecord({ type: 'Warehouse', data: wh })}
                        className="btn btn-secondary"
                        style={{ padding: '4px 10px', fontSize: 11 }}
                      >
                        <Eye size={12} /> Inspect
                      </button>
                    </td>
                  </tr>
                ))}

                {activeTab === 'Workflows' && records.map((wf: WorkflowSummary, idx) => (
                  <tr key={idx}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <FileText size={16} color="#3B82F6" />
                        <div>
                          <strong style={{ fontSize: 13, color: '#F1F5F9', display: 'block' }}>
                            {wf.filename || 'Uploaded Document'}
                          </strong>
                          <span style={{ fontSize: 11, fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                            {wf.workflow_id ? wf.workflow_id.substring(0, 12) + '...' : ''}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span style={{ textTransform: 'capitalize', fontWeight: 600 }}>
                        {wf.master_type}
                      </span>
                    </td>
                    <td>
                      <StatusBadge status={wf.status} />
                    </td>
                    <td style={{ fontWeight: 600, color: '#60A5FA', fontFamily: 'monospace' }}>
                      {wf.sap_object_id || '—'}
                    </td>
                    <td style={{ fontSize: 12.5, color: 'var(--text-muted)' }}>
                      {wf.created_at ? new Date(wf.created_at).toLocaleString() : '—'}
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <button
                        onClick={() => setInspectedRecord({ type: 'Workflow', data: wf })}
                        className="btn btn-secondary"
                        style={{ padding: '4px 10px', fontSize: 11 }}
                      >
                        <Eye size={12} /> Inspect
                      </button>
                    </td>
                  </tr>
                ))}

                {activeTab === 'AuditLogs' && records.map((log: AuditLogRecord, idx) => (
                  <tr key={idx}>
                    <td style={{ fontSize: 12.5, color: 'var(--text-muted)' }}>
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td>
                      <span style={{ textTransform: 'capitalize', fontWeight: 600 }}>
                        {log.master_type?.replace('_', ' ')}
                      </span>
                    </td>
                    <td>
                      <span className="badge badge-info">{log.action}</span>
                    </td>
                    <td style={{ fontWeight: 600, color: '#60A5FA', fontFamily: 'monospace' }}>
                      {log.sap_object_id || 'N/A'}
                    </td>
                    <td>
                      <StatusBadge status={log.success ? 'CREATED' : 'SAP_ERROR'} />
                    </td>
                    <td style={{ fontSize: 11.5, fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                      {log.payload_hash ? `${log.payload_hash.substring(0, 12)}...` : 'N/A'}
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <button
                        onClick={() => setInspectedRecord({ type: 'Audit Dispatch', data: log })}
                        className="btn btn-secondary"
                        style={{ padding: '4px 10px', fontSize: 11 }}
                      >
                        <Eye size={12} /> Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div style={{ textAlign: 'center', padding: '48px 12px', color: 'var(--text-secondary)' }}>
              <Layers size={36} color="var(--text-muted)" style={{ margin: '0 auto 12px' }} />
              <p style={{ fontSize: 14 }}>No records match your query.</p>
              <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
                {searchTerm ? 'Try adjusting your search criteria.' : 'No records exist for this master entity.'}
              </p>
            </div>
          )}
        </div>

        {/* Pagination Footer */}
        {recordsTotal > pageSize && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingTop: 14,
            borderTop: '1px solid var(--border-subtle)',
            flexWrap: 'wrap',
            gap: 12
          }}>
            <span style={{ fontSize: 12.5, color: 'var(--text-secondary)' }}>
              Page {page + 1} of {totalPages} ({recordsTotal.toLocaleString()} total entries)
            </span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                disabled={page === 0 || loadingRecords}
                onClick={() => setPage(p => Math.max(0, p - 1))}
                className="btn btn-secondary"
                style={{ padding: '6px 12px', fontSize: 12, opacity: page === 0 ? 0.5 : 1 }}
              >
                <ChevronLeft size={14} /> Previous
              </button>
              <button
                disabled={page >= totalPages - 1 || loadingRecords}
                onClick={() => setPage(p => p + 1)}
                className="btn btn-secondary"
                style={{ padding: '6px 12px', fontSize: 12, opacity: page >= totalPages - 1 ? 0.5 : 1 }}
              >
                Next <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Record Inspector Slide-Over / Modal */}
      {inspectedRecord && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(5, 8, 16, 0.85)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: 20
        }}>
          <div className="glass-panel" style={{
            width: '100%',
            maxWidth: 680,
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            padding: 24,
            boxShadow: '0 20px 50px rgba(0, 0, 0, 0.6)'
          }}>
            {/* Modal Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18, borderBottom: '1px solid var(--border-subtle)', paddingBottom: 14 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <ShieldCheck size={20} color="#10B981" />
                <h3 style={{ fontSize: 17, fontWeight: 700 }}>
                  {inspectedRecord.type} Record Details
                </h3>
              </div>
              <button
                onClick={() => setInspectedRecord(null)}
                className="btn btn-secondary"
                style={{ padding: '6px 10px', fontSize: 12 }}
              >
                <X size={15} />
              </button>
            </div>

            {/* Modal Body */}
            <div style={{ overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 16, paddingRight: 4 }}>
              <div className="grid-3" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))' }}>
                {Object.entries(inspectedRecord.data)
                  .filter(([k, v]) => typeof v !== 'object' && !k.startsWith('@odata'))
                  .slice(0, 9)
                  .map(([k, v], idx) => (
                    <div key={idx} style={{
                      background: 'rgba(11, 17, 32, 0.8)',
                      padding: 12,
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-subtle)'
                    }}>
                      <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'block', marginBottom: 4 }}>
                        {k.replace(/([A-Z])/g, ' $1').trim()}
                      </span>
                      <strong style={{ fontSize: 13, color: '#F1F5F9', wordBreak: 'break-word' }}>
                        {v !== null && v !== undefined && String(v) !== '' ? String(v) : '—'}
                      </strong>
                    </div>
                  ))}
              </div>

              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600 }}>Raw Database Payload JSON</span>
                  <button
                    onClick={() => handleCopy(JSON.stringify(inspectedRecord.data, null, 2), 'raw-json')}
                    className="btn btn-secondary"
                    style={{ padding: '4px 10px', fontSize: 11, gap: 5 }}
                  >
                    {copiedKey === 'raw-json' ? <Check size={12} color="#10B981" /> : <Copy size={12} />}
                    {copiedKey === 'raw-json' ? 'Copied' : 'Copy JSON'}
                  </button>
                </div>
                <pre style={{
                  background: '#070C18',
                  padding: 14,
                  borderRadius: 8,
                  fontSize: 12,
                  fontFamily: 'monospace',
                  color: '#93C5FD',
                  maxHeight: 240,
                  overflowY: 'auto',
                  border: '1px solid rgba(59, 130, 246, 0.2)'
                }}>
                  {JSON.stringify(inspectedRecord.data, null, 2)}
                </pre>
              </div>
            </div>

            {/* Modal Footer */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 18, paddingTop: 14, borderTop: '1px solid var(--border-subtle)' }}>
              <button onClick={() => setInspectedRecord(null)} className="btn btn-primary" style={{ padding: '8px 20px', fontSize: 13 }}>
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
