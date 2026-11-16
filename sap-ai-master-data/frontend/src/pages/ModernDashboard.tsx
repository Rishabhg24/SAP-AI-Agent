import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Plus,
  Eye,
  Users,
  Sparkles,
  Search,
  X,
  RefreshCw,
  Package,
  ChevronLeft,
  ChevronRight,
  Copy,
  Check,
  FileText,
  Warehouse,
  ArrowRight,
  Clock,
  FileSpreadsheet,
  Loader2
} from 'lucide-react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import type { DashboardStats, SapHealthResponse, WorkflowSummary } from '../types';
import {
  ExportModal,
  AddWidgetModal,
  ShowDetailsModal,
  UpgradeModal,
  SapRecordInspectorModal
} from '../components/DashboardModals';
import { ExecutiveTimeSpotCard } from '../components/ExecutiveTimeSpotCard';
import { CustomDaysFilter } from '../components/CustomDaysFilter';

interface Props {
  onNavigateToModule?: (mod: string) => void;
}

type EntityTab = 'Items' | 'BusinessPartners' | 'Warehouses' | 'Workflows';

export const ModernDashboard: React.FC<Props> = ({ onNavigateToModule }) => {
  const { activeCompanyDb } = useAuth();
  // Live Backend & SAP State
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [sapHealth, setSapHealth] = useState<SapHealthResponse | null>(null);
  const [sapCounts, setSapCounts] = useState<{ Items: number; BusinessPartners: number; Warehouses: number } | null>(null);
  const [loadingStats, setLoadingStats] = useState(false);

  // Filters & State
  const [selectedDays, setSelectedDays] = useState<number | null>(30);
  const [dateRangeStr, setDateRangeStr] = useState('Last 30 days');

  // Active Widgets toggle state
  const [activeWidgets, setActiveWidgets] = useState<Record<string, boolean>>({
    kpis: true,
    masterDataTable: true,
  });

  // Modals state
  const [isExportOpen, setIsExportOpen] = useState(false);
  const [isAddWidgetOpen, setIsAddWidgetOpen] = useState(false);
  const [isShowDetailsOpen, setIsShowDetailsOpen] = useState(false);
  const [isUpgradeOpen, setIsUpgradeOpen] = useState(false);
  const [inspectedSapRecord, setInspectedSapRecord] = useState<{ type: string; data: any } | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Table Entity State
  const [activeEntityTab, setActiveEntityTab] = useState<EntityTab>('Items');
  const [records, setRecords] = useState<any[]>([]);
  const [recordsTotal, setRecordsTotal] = useState<number>(0);
  const [loadingRecords, setLoadingRecords] = useState(false);
  const [exportingDirect, setExportingDirect] = useState(false);
  const [page, setPage] = useState(0);
  const pageSize = 10;
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  // Direct 1-Click Excel Export for the Active Tab / Module
  const handleDirectExportExcel = async () => {
    setExportingDirect(true);
    try {
      const { blob, filename } = await api.downloadMasterDataExcel(
        activeEntityTab,
        selectedDays,
        debouncedSearch.trim() || undefined,
        5000
      );
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Failed direct export to excel', e);
      setIsExportOpen(true);
    } finally {
      setExportingDirect(false);
    }
  };

  // Debounce search
  const searchTimeout = useRef<any>(null);
  const handleSearchChange = (val: string) => {
    setSearchTerm(val);
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => {
      setDebouncedSearch(val);
      setPage(0);
    }, 350);
  };

  // Copy helper
  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  // Fetch Stats, Health, and Counts
  const fetchStatsAndHealth = useCallback(async (daysToFetch?: number | null) => {
    setLoadingStats(true);
    const targetDays = daysToFetch !== undefined ? daysToFetch : selectedDays;
    try {
      const [statsData, healthData, countsData] = await Promise.allSettled([
        api.getDashboardStats(targetDays),
        api.getSapHealth(),
        api.getSapCounts()
      ]);
      if (statsData.status === 'fulfilled') setStats(statsData.value);
      if (healthData.status === 'fulfilled') setSapHealth(healthData.value);
      if (countsData.status === 'fulfilled') setSapCounts(countsData.value);
    } catch (e) {
      console.error('Error loading dashboard metadata', e);
    } finally {
      setLoadingStats(false);
    }
  }, [selectedDays]);

  useEffect(() => {
    fetchStatsAndHealth();
  }, [fetchStatsAndHealth]);

  // Fetch Table Records based on active entity tab
  const fetchRecords = useCallback(async (daysToFetch?: number | null) => {
    setLoadingRecords(true);
    const targetDays = daysToFetch !== undefined ? daysToFetch : selectedDays;
    try {
      if (activeEntityTab === 'Items' || activeEntityTab === 'BusinessPartners' || activeEntityTab === 'Warehouses') {
        const res = await api.getSapRecords(activeEntityTab, pageSize, page * pageSize, debouncedSearch, targetDays);
        setRecords(res.records || []);
        setRecordsTotal(res.total || 0);
      } else if (activeEntityTab === 'Workflows') {
        const workflows = await api.getWorkflows(50, 0, targetDays);
        const filtered = debouncedSearch
          ? workflows.filter(w =>
            (w.filename || '').toLowerCase().includes(debouncedSearch.toLowerCase()) ||
            (w.workflow_id || '').toLowerCase().includes(debouncedSearch.toLowerCase()) ||
            (w.sap_object_id || '').toLowerCase().includes(debouncedSearch.toLowerCase())
          )
          : workflows;
        setRecords(filtered.slice(page * pageSize, (page + 1) * pageSize));
        setRecordsTotal(filtered.length);
      }
    } catch (err) {
      console.error('Failed to fetch records for tab:', activeEntityTab, err);
      setRecords([]);
      setRecordsTotal(0);
    } finally {
      setLoadingRecords(false);
    }
  }, [activeEntityTab, page, debouncedSearch, selectedDays]);

  useEffect(() => {
    fetchRecords();
  }, [fetchRecords]);

  const handleApplyDaysFilter = (days: number | null, label: string) => {
    setSelectedDays(days);
    setDateRangeStr(label);
    setPage(0);
    fetchStatsAndHealth(days);
    fetchRecords(days);
  };



  // Calculated Live Metrics
  const liveItemsCount = sapCounts?.Items ?? stats?.sap_counts?.Items ?? stats?.items_total ?? 0;
  const liveBpCount = sapCounts?.BusinessPartners ?? stats?.sap_counts?.BusinessPartners ?? stats?.business_partners_total ?? 0;
  const liveWhCount = sapCounts?.Warehouses ?? stats?.sap_counts?.Warehouses ?? stats?.warehouses_total ?? 0;
  const liveDocsCount = stats?.documents_processed ?? 0;
  const totalPages = Math.ceil(recordsTotal / pageSize);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* ==========================================================
          Header Bar (Live SAP Status & Controls)
          ========================================================== */}
      {/* ==========================================================
          TimeSpot Unified Top Navigation Bar
          ========================================================== */}
      <div className="timespot-top-navbar" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 16,
        marginBottom: 8,
        flexWrap: 'wrap'
      }}>
        {/* Left: Title + SAP Service Layer Connection */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <h1 style={{
            fontSize: 26,
            fontWeight: 800,
            letterSpacing: '-0.5px',
            color: '#0A0A0A',
            margin: 0,
            fontFamily: "'Outfit', 'Plus Jakarta Sans', sans-serif"
          }}>
            Dashboard
          </h1>

          {(() => {
            const isConn = Boolean(sapHealth?.connected || sapHealth?.status === 'CONNECTED' || (sapHealth as any)?.data?.connected);
            return (
              <div className={`md-sap-status-pill ${isConn ? '' : 'disconnected'}`} title="SAP Service Layer Connection">
                <span className={`md-status-dot-pulse ${isConn ? '' : 'disconnected'}`} />
                <span>
                  {isConn
                    ? `SAP: ${sapHealth?.company_db || stats?.database?.company_db || 'Connected'}`
                    : sapHealth?.status === 'DEVELOPMENT_SIMULATION'
                      ? 'SAP: Simulated Sandbox'
                      : 'SAP: Not Connected'}
                </span>
                <button
                  onClick={() => fetchStatsAndHealth()}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2, display: 'flex', color: 'var(--md-text-muted)' }}
                  title="Refresh connection status"
                >
                  <RefreshCw size={12} className={loadingStats ? 'pulse-animation' : ''} />
                </button>
              </div>
            );
          })()}

          {selectedDays !== null && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                padding: '4px 10px',
                borderRadius: 9999,
                background: '#FFF7ED',
                border: '1px solid #FFEDD5',
                color: '#C2410C',
                fontSize: 12,
                fontWeight: 600,
              }}
              title="Data retrieval is filtered by selected timeframe"
            >
              <Clock size={12} color="#EA580C" />
              <span>{dateRangeStr}</span>
              <button
                type="button"
                onClick={() => handleApplyDaysFilter(null, 'All time')}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 1,
                  display: 'flex',
                  color: '#9A3412',
                }}
                title="Clear filter (Show all records)"
              >
                <X size={12} />
              </button>
            </div>
          )}
        </div>



        {/* Right: Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {/* Hey CIRA Button */}
          <button
            onClick={() => onNavigateToModule?.('ai-agent')}
            className="md-pill-btn"
            style={{
              background: '#0A0A0A',
              color: '#FFFFFF',
              fontWeight: 700,
              gap: 6,
              border: 'none',
              boxShadow: '0 2px 10px rgba(10, 10, 10, 0.25)'
            }}
            title="Launch Hey CIRA (Autonomous SAP AI Agent)"
          >
            <Sparkles size={13} color="#FACC15" />
            <span>Hey CIRA</span>
          </button>

          {/* Custom Days & Preset Filter with Validation */}
          <CustomDaysFilter
            selectedDays={selectedDays}
            onApply={handleApplyDaysFilter}
            activeLabel={dateRangeStr}
            loading={loadingStats || loadingRecords}
          />

          {/* Primary CTA: Upload Document */}
          <button
            onClick={() => onNavigateToModule?.('upload')}
            className="md-pill-btn"
            style={{
              background: '#0A0A0A',
              color: '#FFFFFF',
              fontWeight: 600,
              border: 'none',
              boxShadow: '0 2px 10px rgba(10, 10, 10, 0.25)'
            }}
          >
            <Plus size={15} color="#FFFFFF" />
            <span>Upload Document</span>
          </button>
        </div>
      </div>

      {/* ==========================================================
          Executive TimeSpot Hero Layout (Ticking Clock & Live SAP Metrics)
          ========================================================== */}
      <ExecutiveTimeSpotCard
        stats={stats}
        sapHealth={sapHealth}
        sapCounts={sapCounts}
        activeEntityTab={activeEntityTab}
        onSelectEntityTab={(tab) => {
          setActiveEntityTab(tab);
          setPage(0);
        }}
        onOpenUpload={() => onNavigateToModule?.('upload')}
      />

      {/* ==========================================================
          Master Data Records & Workflows Explorer (Full Width Aligned)
          ========================================================== */}
      {(activeWidgets.masterDataTable !== false) && (
        <div className="md-card" style={{ width: '100%', boxSizing: 'border-box' }}>
          {/* Title & Count */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h2 className="md-card-title" style={{ margin: 0 }}>Master Data Records & Workflows</h2>
              <span style={{ fontSize: 12, color: 'var(--md-text-muted)', fontWeight: 500 }}>
                ({recordsTotal.toLocaleString()} {activeEntityTab === 'BusinessPartners' ? 'partners' : activeEntityTab === 'Items' ? 'items' : activeEntityTab === 'Warehouses' ? 'warehouses' : 'workflows'})
              </span>
            </div>
          </div>

          {/* Single Unified Line Toolbar: Tabs on Left + Search/Export/Create on Right */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 12,
            flexWrap: 'nowrap',
            marginBottom: 16,
            width: '100%'
          }}>
            {/* Entity Navigation Tabs */}
            <div className="md-table-tabs" style={{ flexShrink: 0, margin: 0 }}>
              <button
                onClick={() => {
                  setActiveEntityTab('Items');
                  setPage(0);
                }}
                className={`md-table-tab ${activeEntityTab === 'Items' ? 'active' : ''}`}
              >
                <Package size={13} />
                <span>Items</span>
                <span className="md-table-tab-badge">{liveItemsCount}</span>
              </button>

              <button
                onClick={() => {
                  setActiveEntityTab('BusinessPartners');
                  setPage(0);
                }}
                className={`md-table-tab ${activeEntityTab === 'BusinessPartners' ? 'active' : ''}`}
              >
                <Users size={13} />
                <span>Partners</span>
                <span className="md-table-tab-badge">{liveBpCount}</span>
              </button>

              <button
                onClick={() => {
                  setActiveEntityTab('Warehouses');
                  setPage(0);
                }}
                className={`md-table-tab ${activeEntityTab === 'Warehouses' ? 'active' : ''}`}
              >
                <Warehouse size={13} />
                <span>Warehouses</span>
                <span className="md-table-tab-badge">{liveWhCount}</span>
              </button>

              <button
                onClick={() => {
                  setActiveEntityTab('Workflows');
                  setPage(0);
                }}
                className={`md-table-tab ${activeEntityTab === 'Workflows' ? 'active' : ''}`}
              >
                <FileText size={13} />
                <span>Workflows</span>
                <span className="md-table-tab-badge">{liveDocsCount}</span>
              </button>
            </div>

            {/* Actions & Search: strictly aligned on the same horizontal line */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
              {/* Search Bar */}
              <div style={{ position: 'relative', width: 200 }}>
                <Search
                  size={14}
                  color="#94A3B8"
                  style={{ position: 'absolute', left: 10, top: '50%', transform: 'translateY(-50%)' }}
                />
                <input
                  type="text"
                  placeholder={
                    activeEntityTab === 'Items'
                      ? 'Search Items...'
                      : activeEntityTab === 'BusinessPartners'
                        ? 'Search Partners...'
                        : activeEntityTab === 'Warehouses'
                          ? 'Search Warehouses...'
                          : 'Search Workflows...'
                  }
                  value={searchTerm}
                  onChange={(e) => handleSearchChange(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '6px 28px 6px 30px',
                    borderRadius: 'var(--md-radius-full)',
                    border: '1px solid var(--md-border)',
                    fontSize: 12,
                    outline: 'none',
                    background: '#FAFBFD'
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
                      right: 8,
                      top: '50%',
                      transform: 'translateY(-50%)',
                      background: 'none',
                      border: 'none',
                      color: 'var(--md-text-muted)',
                      cursor: 'pointer',
                      padding: 2
                    }}
                  >
                    <X size={12} />
                  </button>
                )}
              </div>

              {/* Export Current Table to Excel */}
              <button
                onClick={handleDirectExportExcel}
                disabled={exportingDirect || loadingRecords}
                className="md-pill-btn"
                title={`Export live ${activeEntityTab} data (${dateRangeStr}) directly to Excel (.xlsx)`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  background: '#F0FDF4',
                  color: '#15803D',
                  border: '1px solid #BBF7D0',
                  fontWeight: 600,
                  padding: '5px 12px',
                  fontSize: 12,
                  cursor: exportingDirect ? 'wait' : 'pointer'
                }}
              >
                {exportingDirect ? (
                  <Loader2 size={13} className="animate-spin" color="#15803D" />
                ) : (
                  <FileSpreadsheet size={13} color="#15803D" />
                )}
                <span>Export Excel</span>
              </button>

              {/* Primary Action Button (Create Item / Create Partner / Create Warehouse) */}
              {activeEntityTab === 'Items' && (
                <button
                  onClick={() => onNavigateToModule?.('item-master')}
                  className="md-pill-btn"
                  style={{ background: '#0A0A0A', color: '#FFFFFF', fontWeight: 600, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }}
                >
                  <Plus size={13} />
                  <span>Create Item</span>
                </button>
              )}
              {activeEntityTab === 'BusinessPartners' && (
                <button
                  onClick={() => onNavigateToModule?.('business-partner')}
                  className="md-pill-btn"
                  style={{ background: '#0A0A0A', color: '#FFFFFF', fontWeight: 600, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }}
                >
                  <Plus size={13} />
                  <span>Create Partner</span>
                </button>
              )}
              {activeEntityTab === 'Warehouses' && (
                <button
                  onClick={() => onNavigateToModule?.('warehouse-master')}
                  className="md-pill-btn"
                  style={{ background: '#0A0A0A', color: '#FFFFFF', fontWeight: 600, border: 'none', boxShadow: '0 2px 8px rgba(0,0,0,0.15)' }}
                >
                  <Plus size={13} />
                  <span>Create Warehouse</span>
                </button>
              )}
            </div>
          </div>

          {/* Table Area */}
          <div className="md-table-wrap">
            {loadingRecords ? (
              <div style={{ textAlign: 'center', padding: '48px 12px', color: 'var(--md-text-secondary)' }}>
                <RefreshCw size={24} className="pulse-animation" style={{ margin: '0 auto 10px', color: '#2563EB' }} />
                <p style={{ fontSize: 13, fontWeight: 500 }}>Querying SAP Service Layer records...</p>
              </div>
            ) : records.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '48px 12px', color: 'var(--md-text-muted)' }}>
                <Package size={32} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
                <p style={{ fontSize: 13 }}>No records found matching "{debouncedSearch}".</p>
              </div>
            ) : (
              <table className="md-table">
                <thead>
                  {activeEntityTab === 'Items' && (
                    <tr>
                      <th>Item Code</th>
                      <th>Item Description</th>
                      <th>Item Group</th>
                      <th>Classification</th>
                      <th>Status</th>
                      <th style={{ textAlign: 'center', width: 120 }}>Actions</th>

                    </tr>
                  )}
                  {activeEntityTab === 'BusinessPartners' && (
                    <tr>
                      <th>Card Code</th>
                      <th>Partner Name</th>
                      <th>Partner Type</th>
                      <th>Tax ID</th>
                      <th>Status</th>
                      <th style={{ textAlign: 'center', width: 120 }}>Actions</th>
                    </tr>
                  )}
                  {activeEntityTab === 'Warehouses' && (
                    <tr>
                      <th>Warehouse Code</th>
                      <th>Warehouse Name</th>
                      <th>Location / City</th>
                      <th>Status</th>
                      <th style={{ textAlign: 'center', width: 120 }}>Actions</th>
                    </tr>
                  )}
                  {activeEntityTab === 'Workflows' && (
                    <tr>
                      <th>Document / File</th>
                      <th>Master Type</th>
                      <th>Workflow Status</th>
                      <th>Target Object ID</th>
                      <th>Timestamp</th>
                      <th style={{ textAlign: 'center', width: 120 }}>Actions</th>
                    </tr>
                  )}
                </thead>
                <tbody>
                  {/* Items Rows */}
                  {activeEntityTab === 'Items' && records.map((item: any, idx) => (
                    <tr key={idx}>
                      <td className="md-td-id">
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <span style={{ fontWeight: 600, color: '#2563EB', fontFamily: 'monospace' }}>
                            {item.ItemCode}
                          </span>
                          <button
                            onClick={() => handleCopy(item.ItemCode, `itm-${idx}`)}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2, color: copiedKey === `itm-${idx}` ? '#10B981' : '#94A3B8' }}
                            title="Copy Item Code"
                          >
                            {copiedKey === `itm-${idx}` ? <Check size={11} /> : <Copy size={11} />}
                          </button>
                        </div>
                      </td>
                      <td style={{ fontWeight: 500, maxWidth: 280 }}>
                        {item.ItemName || 'Unnamed Item'}
                      </td>
                      <td>
                        <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 4, background: '#F1F5F9', color: '#475569', fontWeight: 600 }}>
                          {item.ItemsGroupCode ? `Grp ${item.ItemsGroupCode}` : '-'}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: 4 }}>
                          {item.InventoryItem !== 'tNO' && <span style={{ fontSize: 10, padding: '2px 5px', borderRadius: 4, background: '#EFF6FF', color: '#2563EB', fontWeight: 600 }}>Inv</span>}
                          {item.SalesItem !== 'tNO' && <span style={{ fontSize: 10, padding: '2px 5px', borderRadius: 4, background: '#ECFDF5', color: '#059669', fontWeight: 600 }}>Sales</span>}
                          {item.PurchaseItem !== 'tNO' && <span style={{ fontSize: 10, padding: '2px 5px', borderRadius: 4, background: '#FAF5FF', color: '#7E22CE', fontWeight: 600 }}>Purch</span>}
                        </div>
                      </td>
                      <td>
                        <span className="md-status-dot green" />
                        <span style={{ fontSize: 12, fontWeight: 500, color: '#059669' }}>Active</span>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <button
                          onClick={() => setInspectedSapRecord({ type: 'Item Master', data: item })}
                          className="md-pill-btn"
                          style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', padding: '4px 12px', fontSize: 11, gap: 5 }}
                        >
                          <Eye size={12} />
                          <span>Inspect</span>
                        </button>
                      </td>
                    </tr>
                  ))}

                  {/* Business Partners Rows */}
                  {activeEntityTab === 'BusinessPartners' && records.map((bp: any, idx) => (
                    <tr key={idx}>
                      <td className="md-td-id">
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <span style={{ fontWeight: 600, color: '#7E22CE', fontFamily: 'monospace' }}>
                            {bp.CardCode}
                          </span>
                          <button
                            onClick={() => handleCopy(bp.CardCode, `bp-${idx}`)}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2, color: copiedKey === `bp-${idx}` ? '#10B981' : '#94A3B8' }}
                            title="Copy Card Code"
                          >
                            {copiedKey === `bp-${idx}` ? <Check size={11} /> : <Copy size={11} />}
                          </button>
                        </div>
                      </td>
                      <td style={{ fontWeight: 500, maxWidth: 280 }}>
                        {bp.CardName || 'Unnamed Business Partner'}
                      </td>
                      <td>
                        <span style={{
                          fontSize: 11,
                          padding: '2px 8px',
                          borderRadius: 4,
                          fontWeight: 600,
                          background: bp.CardType === 'cCustomer' ? '#EFF6FF' : '#FAF5FF',
                          color: bp.CardType === 'cCustomer' ? '#2563EB' : '#7E22CE'
                        }}>
                          {bp.CardType === 'cCustomer' ? 'Customer' : bp.CardType === 'cSupplier' ? 'Vendor' : (bp.CardType || 'Partner')}
                        </span>
                      </td>
                      <td style={{ fontSize: 11.5, fontFamily: 'monospace', color: 'var(--md-text-muted)' }}>
                        {bp.FederalTaxID || '—'}
                      </td>
                      <td>
                        <span className="md-status-dot green" />
                        <span style={{ fontSize: 12, fontWeight: 500, color: '#059669' }}>Active</span>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <button
                          onClick={() => setInspectedSapRecord({ type: 'Business Partner', data: bp })}
                          className="md-pill-btn"
                          style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', padding: '4px 12px', fontSize: 11, gap: 5 }}
                        >
                          <Eye size={12} />
                          <span>Inspect</span>
                        </button>
                      </td>
                    </tr>
                  ))}

                  {/* Warehouses Rows */}
                  {activeEntityTab === 'Warehouses' && records.map((wh: any, idx) => (
                    <tr key={idx}>
                      <td className="md-td-id">
                        <span style={{ fontWeight: 600, color: '#059669', fontFamily: 'monospace' }}>
                          {wh.WarehouseCode}
                        </span>
                      </td>
                      <td style={{ fontWeight: 500, maxWidth: 280 }}>
                        {wh.WarehouseName || 'Unnamed Warehouse'}
                      </td>
                      <td style={{ fontSize: 12, color: 'var(--md-text-secondary)' }}>
                        {wh.City || wh.Location || '—'}
                      </td>
                      <td>
                        <span className="md-status-dot green" />
                        <span style={{ fontSize: 12, fontWeight: 500, color: '#059669' }}>Active</span>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <button
                          onClick={() => setInspectedSapRecord({ type: 'Warehouse Master', data: wh })}
                          className="md-pill-btn"
                          style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', padding: '4px 12px', fontSize: 11, gap: 5 }}
                        >
                          <Eye size={12} />
                          <span>Inspect</span>
                        </button>
                      </td>
                    </tr>
                  ))}

                  {/* Workflows Rows */}
                  {activeEntityTab === 'Workflows' && records.map((wf: WorkflowSummary, idx) => (
                    <tr key={idx}>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <FileText size={15} color="#2563EB" />
                          <div>
                            <div style={{ fontWeight: 600, color: 'var(--md-text-primary)' }}>
                              {wf.filename || wf.display_name || 'workflow_doc'}
                            </div>
                            <div style={{ fontSize: 10.5, color: 'var(--md-text-muted)', fontFamily: 'monospace' }}>
                              {wf.workflow_id?.slice(0, 14)}...
                            </div>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span style={{ fontSize: 11, textTransform: 'capitalize', fontWeight: 600, color: '#475569' }}>
                          {wf.master_type}
                        </span>
                      </td>
                      <td>
                        <span style={{
                          fontSize: 10.5,
                          fontWeight: 700,
                          padding: '3px 8px',
                          borderRadius: 6,
                          background: wf.status === 'CREATED' ? '#ECFDF5' : wf.status === 'READY_FOR_CONFIRMATION' ? '#EFF6FF' : '#FEF2F2',
                          color: wf.status === 'CREATED' ? '#059669' : wf.status === 'READY_FOR_CONFIRMATION' ? '#2563EB' : '#DC2626'
                        }}>
                          {wf.status}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'monospace', fontSize: 12, color: '#2563EB' }}>
                        {wf.sap_object_id || 'Pending Post'}
                      </td>
                      <td style={{ fontSize: 11.5, color: 'var(--md-text-muted)' }}>
                        {wf.created_at ? new Date(wf.created_at).toLocaleDateString() : 'Today'}
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <button
                          onClick={() => onNavigateToModule?.('upload')}
                          className="md-pill-btn"
                          style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', padding: '4px 12px', fontSize: 11, gap: 5, background: '#EFF6FF', color: '#2563EB' }}
                        >
                          <span>Open Studio</span>
                          <ArrowRight size={11} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>

          {/* Pagination Toolbar */}
          {recordsTotal > pageSize && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingTop: 12,
              marginTop: 8,
              borderTop: '1px solid var(--md-border-light)',
              fontSize: 12,
              color: 'var(--md-text-secondary)'
            }}>
              <div>
                Showing {page * pageSize + 1} - {Math.min((page + 1) * pageSize, recordsTotal)} of {recordsTotal.toLocaleString()} records
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                <button
                  disabled={page === 0 || loadingRecords}
                  onClick={() => setPage(p => p - 1)}
                  className="md-pill-btn"
                  style={{ opacity: page === 0 ? 0.4 : 1, padding: '4px 10px' }}
                >
                  <ChevronLeft size={14} /> Prev
                </button>
                <button
                  disabled={page >= totalPages - 1 || loadingRecords}
                  onClick={() => setPage(p => p + 1)}
                  className="md-pill-btn"
                  style={{ opacity: page >= totalPages - 1 ? 0.4 : 1, padding: '4px 10px' }}
                >
                  Next <ChevronRight size={14} />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Modals */}
      <ExportModal
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
        selectedDays={selectedDays}
        activeEntityTab={activeEntityTab}
        dateRangeStr={dateRangeStr}
        searchTerm={debouncedSearch}
        dashboardData={{
          period: dateRangeStr,
          dateRange: dateRangeStr,
          days: selectedDays,
          kpis: {
            items: liveItemsCount,
            businessPartners: liveBpCount,
            warehouses: liveWhCount,
            documents: liveDocsCount
          },
          entity: activeEntityTab,
          records: records,
          database: {
            company_db: stats?.database?.company_db || activeCompanyDb || 'TEST_SHOES_10SEP26'
          }
        }}
      />

      <AddWidgetModal
        isOpen={isAddWidgetOpen}
        onClose={() => setIsAddWidgetOpen(false)}
        activeWidgets={activeWidgets}
        onToggleWidget={(key) =>
          setActiveWidgets((prev) => ({ ...prev, [key]: !prev[key] }))
        }
      />

      <ShowDetailsModal
        isOpen={isShowDetailsOpen}
        onClose={() => setIsShowDetailsOpen(false)}
      />

      <UpgradeModal
        isOpen={isUpgradeOpen}
        onClose={() => setIsUpgradeOpen(false)}
      />

      <SapRecordInspectorModal
        isOpen={!!inspectedSapRecord}
        onClose={() => setInspectedSapRecord(null)}
        record={inspectedSapRecord}
        onNavigateToModule={onNavigateToModule}
      />
    </div>
  );
};
