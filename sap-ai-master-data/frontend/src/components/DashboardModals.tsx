import React, { useState, useEffect } from 'react';
import {
  X,
  Download,
  FileSpreadsheet,
  FileCode,
  Printer,
  Check,
  Shield,
  Package,
  Database,
  Loader2,
  AlertCircle,
  CheckCircle2
} from 'lucide-react';
import { api } from '../services/api';

/* ==========================================================
   1. Export Modal
   ========================================================== */
interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  dashboardData?: any;
  selectedDays?: number | null;
  activeEntityTab?: string;
  dateRangeStr?: string;
  searchTerm?: string;
}

export const ExportModal: React.FC<ExportModalProps> = ({
  isOpen,
  onClose,
  dashboardData,
  selectedDays: initialDays,
  activeEntityTab = 'Items',
  dateRangeStr,
  searchTerm = '',
}) => {
  // Format selection: 'excel' as primary default
  const [format, setFormat] = useState<'excel' | 'csv' | 'json' | 'print'>('excel');
  const [downloading, setDownloading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Selected Module / Entity
  const [selectedEntity, setSelectedEntity] = useState<string>(activeEntityTab || 'Items');

  // Selected Timeframe (Days)
  const [days, setDays] = useState<number | null>(
    initialDays !== undefined ? initialDays : (dashboardData?.days ?? 30)
  );
  const [showCustomInput, setShowCustomInput] = useState<boolean>(false);
  const [customDaysVal, setCustomDaysVal] = useState<string>('');

  // Search Filter
  const [includeSearchFilter, setIncludeSearchFilter] = useState<boolean>(true);

  useEffect(() => {
    if (isOpen) {
      const d = initialDays !== undefined ? initialDays : (dashboardData?.days ?? 30);
      setDays(d);
      setSelectedEntity(activeEntityTab || 'Items');
      setFormat('excel');
      if (d !== null && d !== 7 && d !== 30 && d !== 90) {
        setShowCustomInput(true);
        setCustomDaysVal(String(d));
      } else {
        setShowCustomInput(false);
        setCustomDaysVal('');
      }
      setErrorMsg(null);
      setSuccessMsg(null);
    }
  }, [isOpen, initialDays, dashboardData, activeEntityTab]);

  if (!isOpen) return null;

  const handleApplyDays = (val: number | null) => {
    setDays(val);
    setShowCustomInput(false);
    setErrorMsg(null);
  };

  const handleCustomDaysChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setCustomDaysVal(val);
    const num = parseInt(val, 10);
    if (!isNaN(num) && num > 0 && num <= 730) {
      setDays(num);
      setErrorMsg(null);
    }
  };

  // Field definitions preview for transparency
  const moduleFieldsPreview: Record<string, { title: string; countLabel?: string; fields: string[] }> = {
    Items: {
      title: 'Items Master Catalog',
      countLabel: dashboardData?.kpis?.items ? `${dashboardData.kpis.items.toLocaleString()} records` : undefined,
      fields: ['Item Code', 'Item Description', 'Item Group Code', 'Inventory Item', 'Sales Item', 'Purchase Item', 'Sales Unit (UoM)', 'Purchase Unit', 'Bar Code', 'Tax Rate (%)', 'Create Date', 'Update Date', 'Status']
    },
    BusinessPartners: {
      title: 'Business Partners',
      countLabel: dashboardData?.kpis?.businessPartners ? `${dashboardData.kpis.businessPartners.toLocaleString()} records` : undefined,
      fields: ['Card Code', 'Partner Name', 'Card Type', 'GSTIN / Federal Tax ID', 'Phone Number', 'Email Address', 'Currency', 'Street Address', 'City', 'Zip Code', 'Create Date', 'Update Date', 'Status']
    },
    Warehouses: {
      title: 'Warehouses Facilities',
      countLabel: dashboardData?.kpis?.warehouses ? `${dashboardData.kpis.warehouses.toLocaleString()} records` : undefined,
      fields: ['Warehouse Code', 'Warehouse Name', 'City', 'State', 'Street Address', 'Zip Code', 'Country', 'Inactive Flag', 'Status']
    },
    Workflows: {
      title: 'Workflows & Ingestions',
      countLabel: dashboardData?.kpis?.documents ? `${dashboardData.kpis.documents.toLocaleString()} records` : undefined,
      fields: ['Workflow ID', 'Filename', 'Master Type', 'Processing Status', 'SAP Object ID', 'SAP Response Status', 'User Confirmed', 'Created At', 'Updated At', 'Execution Details']
    },
    Dashboard: {
      title: 'Complete Executive Dashboard (Multi-Sheet Workbook)',
      countLabel: 'All Master Data + Workflows',
      fields: ['Sheet 1: Executive Overview & KPIs', 'Sheet 2: Items Master', 'Sheet 3: Business Partners', 'Sheet 4: Warehouses', 'Sheet 5: Workflows Audit']
    }
  };

  const handleExport = async () => {
    setErrorMsg(null);
    setSuccessMsg(null);

    if (format === 'print') {
      window.print();
      onClose();
      return;
    }

    setDownloading(true);
    const searchParam = (includeSearchFilter && searchTerm.trim()) ? searchTerm.trim() : undefined;

    try {
      if (format === 'excel') {
        const { blob, filename } = await api.downloadMasterDataExcel(selectedEntity, days, searchParam, 5000);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        setSuccessMsg(`Successfully downloaded ${filename}`);
        setTimeout(() => {
          onClose();
        }, 1400);
      } else if (format === 'csv') {
        const { blob, filename } = await api.downloadMasterDataCsv(selectedEntity, days, searchParam, 5000);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        setSuccessMsg(`Successfully downloaded ${filename}`);
        setTimeout(() => {
          onClose();
        }, 1400);
      } else if (format === 'json') {
        const { data, filename } = await api.downloadMasterDataJson(selectedEntity, days, searchParam, 5000);
        const jsonStr = JSON.stringify(data || dashboardData, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        setSuccessMsg(`Successfully downloaded ${filename}`);
        setTimeout(() => {
          onClose();
        }, 1400);
      }
    } catch (err: any) {
      console.error('Failed to export SAP master data', err);
      // Fallback for JSON using live dashboard data if server export is unreachable
      if (format === 'json' && dashboardData) {
        try {
          const jsonStr = JSON.stringify(dashboardData, null, 2);
          const blob = new Blob([jsonStr], { type: 'application/json' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `SAP_Dashboard_Report_${days ? `last_${days}_days` : 'all_time'}_${new Date().toISOString().slice(0, 10)}.json`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
          setSuccessMsg('Downloaded dashboard report');
          setTimeout(() => onClose(), 1200);
          return;
        } catch {
          // ignore
        }
      }
      const msg =
        err.response?.data?.detail ||
        err.message ||
        'Unable to export master data. Verify SAP Service Layer connectivity.';
      setErrorMsg(msg);
    } finally {
      setDownloading(false);
    }
  };

  const timeframeLabel = dateRangeStr || (days ? `Last ${days} days` : 'All time records');
  const activeModuleInfo = moduleFieldsPreview[selectedEntity] || moduleFieldsPreview['Items'];

  return (
    <div className="md-modal-backdrop" onClick={onClose}>
      <div className="md-modal-content" style={{ maxWidth: 580, maxHeight: '90vh', overflowY: 'auto' }} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <h3 style={{ fontSize: 18, fontWeight: 700, margin: 0, color: '#0F172A' }}>Export Master Data & Reports</h3>
              <span style={{ fontSize: 11, background: '#DCFCE7', color: '#15803D', padding: '2px 8px', borderRadius: 9999, fontWeight: 700 }}>
                Excel .XLSX
              </span>
            </div>
            <p style={{ fontSize: 12, color: 'var(--md-text-secondary)', marginTop: 3, margin: 0 }}>
              Export live SAP catalog records and dashboard metrics with clean, formatted columns
            </p>
          </div>
          <button onClick={onClose} className="md-more-btn" aria-label="Close export modal">
            <X size={18} />
          </button>
        </div>

        {/* Live SAP Environment Indicator */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '7px 12px',
            borderRadius: 8,
            background: 'rgba(16, 185, 129, 0.08)',
            border: '1px solid rgba(16, 185, 129, 0.2)',
            marginBottom: 14,
            fontSize: 12,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600, color: '#065F46' }}>
            <Database size={14} />
            <span>Target: SAP Service Layer ({dashboardData?.database?.company_db || 'TEST_SHOES_10SEP26'})</span>
          </div>
          <span style={{ color: '#047857', fontWeight: 600 }}>Live Master Data</span>
        </div>

        {/* Step 1: Select Module / Data Scope */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
            <label style={{ fontSize: 12, fontWeight: 700, color: '#374151' }}>
              1. Select Module / Data Scope
            </label>
            <span style={{ fontSize: 11.5, color: '#2563EB', fontWeight: 600 }}>
              {activeModuleInfo.title}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 6 }}>
            {[
              { id: 'Items', label: 'Items Master', icon: Package, badge: dashboardData?.kpis?.items },
              { id: 'BusinessPartners', label: 'Business Partners', icon: Database, badge: dashboardData?.kpis?.businessPartners },
              { id: 'Warehouses', label: 'Warehouses', icon: Database, badge: dashboardData?.kpis?.warehouses },
              { id: 'Workflows', label: 'Workflows & Ingestion', icon: FileCode, badge: dashboardData?.kpis?.documents },
            ].map((m) => {
              const isSelected = selectedEntity === m.id;
              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => setSelectedEntity(m.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '8px 12px',
                    borderRadius: 8,
                    border: isSelected ? '1.5px solid #0F172A' : '1px solid var(--md-border)',
                    background: isSelected ? '#F8FAFC' : '#FFFFFF',
                    color: isSelected ? '#0F172A' : '#4B5563',
                    fontWeight: isSelected ? 700 : 500,
                    cursor: 'pointer',
                    textAlign: 'left',
                    fontSize: 12,
                    boxShadow: isSelected ? '0 1px 3px rgba(0,0,0,0.06)' : 'none'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ color: isSelected ? '#2563EB' : '#94A3B8' }}>•</span>
                    <span>{m.label}</span>
                  </div>
                  {m.badge !== undefined && (
                    <span style={{
                      fontSize: 10.5,
                      fontWeight: 700,
                      background: isSelected ? '#0F172A' : '#F1F5F9',
                      color: isSelected ? '#FFFFFF' : '#64748B',
                      padding: '1px 6px',
                      borderRadius: 10
                    }}>
                      {m.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </div>

          {/* Option for Complete Multi-Sheet Workbook */}
          <button
            type="button"
            onClick={() => setSelectedEntity('Dashboard')}
            style={{
              marginTop: 6,
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '8px 12px',
              borderRadius: 8,
              border: selectedEntity === 'Dashboard' ? '2px solid #2563EB' : '1px dashed #CBD5E1',
              background: selectedEntity === 'Dashboard' ? '#EFF6FF' : '#FBFDFF',
              color: selectedEntity === 'Dashboard' ? '#1D4ED8' : '#475569',
              fontWeight: selectedEntity === 'Dashboard' ? 700 : 600,
              cursor: 'pointer',
              fontSize: 12,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <FileSpreadsheet size={15} color="#2563EB" />
              <span>All Modules (Full Multi-Sheet Excel Workbook: Items + Partners + Warehouses + Workflows)</span>
            </div>
            {selectedEntity === 'Dashboard' && <Check size={16} color="#2563EB" />}
          </button>
        </div>

        {/* Step 2: Timeframe & Search Scope */}
        <div style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
            <label style={{ fontSize: 12, fontWeight: 700, color: '#374151' }}>
              2. Timeframe Filter
            </label>
            <span style={{ fontSize: 11.5, color: '#EA580C', fontWeight: 600 }}>
              {timeframeLabel}
            </span>
          </div>

          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {[
              { label: 'All Time', val: null },
              { label: 'Last 7d', val: 7 },
              { label: 'Last 30d', val: 30 },
              { label: 'Last 90d', val: 90 },
            ].map((t) => {
              const isSelected = !showCustomInput && days === t.val;
              return (
                <button
                  key={t.label}
                  type="button"
                  onClick={() => handleApplyDays(t.val)}
                  style={{
                    padding: '4px 12px',
                    fontSize: 11.5,
                    borderRadius: 20,
                    border: isSelected ? '1.5px solid #EA580C' : '1px solid var(--md-border)',
                    background: isSelected ? '#FFF7ED' : '#F9FAFB',
                    color: isSelected ? '#C2410C' : '#4B5563',
                    fontWeight: isSelected ? 700 : 500,
                    cursor: 'pointer',
                  }}
                >
                  {t.label}
                </button>
              );
            })}
            <button
              type="button"
              onClick={() => {
                setShowCustomInput(true);
                if (!customDaysVal && days) setCustomDaysVal(String(days));
              }}
              style={{
                padding: '4px 12px',
                fontSize: 11.5,
                borderRadius: 20,
                border: showCustomInput ? '1.5px solid #EA580C' : '1px solid var(--md-border)',
                background: showCustomInput ? '#FFF7ED' : '#F9FAFB',
                color: showCustomInput ? '#C2410C' : '#4B5563',
                fontWeight: showCustomInput ? 700 : 500,
                cursor: 'pointer',
              }}
            >
              Custom days...
            </button>
          </div>

          {showCustomInput && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8 }}>
              <input
                type="number"
                min="1"
                max="730"
                placeholder="Number of days (e.g. 15)"
                value={customDaysVal}
                onChange={handleCustomDaysChange}
                style={{
                  padding: '5px 10px',
                  fontSize: 12,
                  borderRadius: 6,
                  border: '1px solid #D1D5DB',
                  width: 160,
                }}
              />
              <span style={{ fontSize: 11, color: 'var(--md-text-secondary)' }}>
                Filtering records created in the last {customDaysVal || 'N'} days
              </span>
            </div>
          )}

          {/* Active Search Filter indicator */}
          {searchTerm && searchTerm.trim() && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginTop: 8,
              padding: '6px 10px',
              borderRadius: 6,
              background: '#F1F5F9',
              fontSize: 11.5
            }}>
              <span style={{ color: '#475569' }}>
                Active Search Filter: <strong>"{searchTerm}"</strong>
              </span>
              <label style={{ display: 'flex', alignItems: 'center', gap: 4, cursor: 'pointer', fontWeight: 600, color: '#1E293B' }}>
                <input
                  type="checkbox"
                  checked={includeSearchFilter}
                  onChange={(e) => setIncludeSearchFilter(e.target.checked)}
                />
                <span>Apply to export</span>
              </label>
            </div>
          )}
        </div>

        {/* Step 3: Format Selection (Excel as Default) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 14 }}>
          <label style={{ fontSize: 12, fontWeight: 700, color: '#374151', marginBottom: 2 }}>
            3. Choose Export Format
          </label>

          {/* Excel Format - PRIMARY */}
          <label
            onClick={() => setFormat('excel')}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '10px 14px',
              borderRadius: 'var(--md-radius-md)',
              border: format === 'excel' ? '2px solid #10B981' : '1px solid var(--md-border)',
              background: format === 'excel' ? '#F0FDF4' : '#FFFFFF',
              cursor: 'pointer',
              boxShadow: format === 'excel' ? '0 2px 6px rgba(16, 185, 129, 0.15)' : 'none'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{
                background: '#10B981',
                borderRadius: 8,
                width: 34,
                height: 34,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#FFFFFF'
              }}>
                <FileSpreadsheet size={19} />
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 13.5, color: '#065F46', display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span>Microsoft Excel Workbook (.xlsx)</span>
                  <span style={{ fontSize: 10, background: '#10B981', color: '#FFFFFF', padding: '1px 6px', borderRadius: 4 }}>
                    RECOMMENDED
                  </span>
                </div>
                <div style={{ fontSize: 11.5, color: '#374151' }}>
                  Professional spreadsheet with styled headers, alternating rows, auto widths & proper SAP master fields
                </div>
              </div>
            </div>
            {format === 'excel' && <Check size={20} color="#10B981" />}
          </label>

          {/* CSV Format */}
          <label
            onClick={() => setFormat('csv')}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '8px 14px',
              borderRadius: 'var(--md-radius-md)',
              border: format === 'csv' ? '2px solid #0A0A0A' : '1px solid var(--md-border)',
              background: format === 'csv' ? '#FFF7ED' : '#FFFFFF',
              cursor: 'pointer',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <FileSpreadsheet size={18} color="#64748B" />
              <div>
                <div style={{ fontWeight: 600, fontSize: 13 }}>CSV Spreadsheet (.csv)</div>
                <div style={{ fontSize: 11, color: 'var(--md-text-secondary)' }}>
                  Plain text comma-separated values compatible with any database or spreadsheet tool
                </div>
              </div>
            </div>
            {format === 'csv' && <Check size={18} color="#EA580C" />}
          </label>

          {/* JSON Format */}
          <label
            onClick={() => setFormat('json')}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '8px 14px',
              borderRadius: 'var(--md-radius-md)',
              border: format === 'json' ? '2px solid #0A0A0A' : '1px solid var(--md-border)',
              background: format === 'json' ? '#FFF7ED' : '#FFFFFF',
              cursor: 'pointer',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <FileCode size={18} color="#EA580C" />
              <div>
                <div style={{ fontWeight: 600, fontSize: 13 }}>Raw Data JSON (.json)</div>
                <div style={{ fontSize: 11, color: 'var(--md-text-secondary)' }}>
                  Structured JSON objects for API pipelines, AI analysis, and automation
                </div>
              </div>
            </div>
            {format === 'json' && <Check size={18} color="#EA580C" />}
          </label>

          {/* Print Format */}
          <label
            onClick={() => setFormat('print')}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '8px 14px',
              borderRadius: 'var(--md-radius-md)',
              border: format === 'print' ? '2px solid #0A0A0A' : '1px solid var(--md-border)',
              background: format === 'print' ? '#FFF7ED' : '#FFFFFF',
              cursor: 'pointer',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <Printer size={18} color="#8B5CF6" />
              <div>
                <div style={{ fontWeight: 600, fontSize: 13 }}>Print / PDF Document</div>
                <div style={{ fontSize: 11, color: 'var(--md-text-secondary)' }}>
                  Print-ready presentation of dashboard metrics and master records
                </div>
              </div>
            </div>
            {format === 'print' && <Check size={18} color="#EA580C" />}
          </label>
        </div>

        {/* Fields Included Preview */}
        <div style={{
          padding: '8px 12px',
          borderRadius: 8,
          background: '#F8FAFC',
          border: '1px solid #E2E8F0',
          marginBottom: 16
        }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#475569', marginBottom: 4 }}>
            FIELDS INCLUDED IN EXCEL EXPORT:
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {activeModuleInfo.fields.map((f, i) => (
              <span
                key={i}
                style={{
                  fontSize: 10.5,
                  background: '#FFFFFF',
                  color: '#334155',
                  padding: '2px 7px',
                  borderRadius: 4,
                  border: '1px solid #E2E8F0',
                  fontWeight: 500
                }}
              >
                {f}
              </span>
            ))}
          </div>
        </div>

        {/* Feedback Alerts */}
        {errorMsg && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 12px',
              borderRadius: 6,
              background: '#FEE2E2',
              color: '#991B1B',
              fontSize: 12,
              marginBottom: 14,
            }}
          >
            <AlertCircle size={16} />
            <span>{errorMsg}</span>
          </div>
        )}

        {successMsg && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 12px',
              borderRadius: 6,
              background: '#DCFCE7',
              color: '#166534',
              fontSize: 12,
              marginBottom: 14,
            }}
          >
            <CheckCircle2 size={16} />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Action Buttons */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
          <button onClick={onClose} className="md-pill-btn" disabled={downloading}>
            Cancel
          </button>
          <button
            onClick={handleExport}
            disabled={downloading}
            className="md-btn-export"
            style={{
              opacity: downloading ? 0.7 : 1,
              cursor: downloading ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: format === 'excel' ? '#0F172A' : undefined
            }}
          >
            {downloading ? (
              <>
                <Loader2 size={15} className="animate-spin" />
                <span>Generating {format.toUpperCase()} export...</span>
              </>
            ) : (
              <>
                <Download size={15} />
                <span>Download {format === 'excel' ? 'Excel (.xlsx)' : format.toUpperCase()}</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

/* ==========================================================
   2. Add Widget Modal
   ========================================================== */
interface AddWidgetModalProps {
  isOpen: boolean;
  onClose: () => void;
  activeWidgets: Record<string, boolean>;
  onToggleWidget: (key: string) => void;
}

export const AddWidgetModal: React.FC<AddWidgetModalProps> = ({
  isOpen,
  onClose,
  activeWidgets,
  onToggleWidget
}) => {
  if (!isOpen) return null;

  const widgetList = [
    { key: 'kpis', label: 'KPI Stat Metrics', desc: 'Catalog items, business partners, documents, and consensus accuracy' },
    { key: 'masterDataTable', label: 'Master Data & Workflows Explorer', desc: 'Full-width live SAP catalog table with search, entity tabs, and pagination' },
  ];

  return (
    <div className="md-modal-backdrop" onClick={onClose}>
      <div className="md-modal-content" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
          <div>
            <h3 style={{ fontSize: 18, fontWeight: 700 }}>Customize Dashboard Widgets</h3>
            <p style={{ fontSize: 12, color: 'var(--md-text-secondary)', marginTop: 2 }}>
              Choose which modules appear on your main analytics dashboard
            </p>
          </div>
          <button onClick={onClose} className="md-more-btn"><X size={18} /></button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 24 }}>
          {widgetList.map((w) => {
            const isEnabled = activeWidgets[w.key] ?? true;
            return (
              <div
                key={w.key}
                onClick={() => onToggleWidget(w.key)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 16px',
                  borderRadius: 'var(--md-radius-md)',
                  border: isEnabled ? '1px solid #BFDBFE' : '1px solid var(--md-border)',
                  background: isEnabled ? '#FAFBFD' : '#F8FAFC',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: 13.5, color: isEnabled ? '#0F172A' : '#94A3B8' }}>
                    {w.label}
                  </div>
                  <div style={{ fontSize: 11.5, color: 'var(--md-text-secondary)' }}>{w.desc}</div>
                </div>
                <div style={{
                  width: 22,
                  height: 22,
                  borderRadius: 6,
                  border: isEnabled ? '2px solid #2563EB' : '2px solid #CBD5E1',
                  background: isEnabled ? '#2563EB' : 'transparent',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  {isEnabled && <Check size={14} color="#FFFFFF" />}
                </div>
              </div>
            );
          })}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button onClick={onClose} className="md-btn-export">Done</button>
        </div>
      </div>
    </div>
  );
};

/* ==========================================================
   3. Show Details (Consensus Accuracy & Validation) Modal
   ========================================================== */
interface ShowDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ShowDetailsModal: React.FC<ShowDetailsModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="md-modal-backdrop" onClick={onClose}>
      <div className="md-modal-content" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div>
            <h3 style={{ fontSize: 18, fontWeight: 700 }}>Consensus Accuracy & Validation</h3>
            <p style={{ fontSize: 12, color: 'var(--md-text-secondary)' }}>
              Current 3-Engine Consensus Rate: 98.4% across all documents
            </p>
          </div>
          <button onClick={onClose} className="md-more-btn"><X size={18} /></button>
        </div>

        <div style={{
          background: '#EFF6FF',
          border: '1px solid #BFDBFE',
          borderRadius: 'var(--md-radius-md)',
          padding: '14px 18px',
          marginBottom: 20
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: '#1E40AF' }}>3-Engine Consensus Match</span>
            <span style={{ fontSize: 13, fontWeight: 700, color: '#2563EB' }}>98.4% / 100%</span>
          </div>
          <div style={{ height: 8, background: '#DBEAFE', borderRadius: 4, overflow: 'hidden' }}>
            <div style={{ width: '98.4%', height: '100%', background: '#2563EB', borderRadius: 4 }}></div>
          </div>
        </div>

        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 10 }}>Extraction Engine Reliability Breakdown</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[
              { label: 'Deterministic Rules Validation', val: '99.4%', count: 'Pydantic mandatory schema compliance' },
              { label: 'LLM Heuristic Extractor', val: '98.1%', count: 'NVIDIA Nemotron 30B structural parsing' },
              { label: 'OCR & Table Parser Engine', val: '97.8%', count: 'PDF & Excel multi-format extraction' },
              { label: 'Cryptographic SHA-256 Hashes', val: '100.0%', count: 'Immutable audit trail verification' },
            ].map((c, idx) => (
              <div key={idx} style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                background: '#FAFBFD',
                border: '1px solid var(--md-border)',
                borderRadius: 'var(--md-radius-sm)'
              }}>
                <div>
                  <div style={{ fontSize: 12.5, fontWeight: 600 }}>{c.label}</div>
                  <div style={{ fontSize: 11, color: 'var(--md-text-secondary)' }}>{c.count}</div>
                </div>
                <span style={{ fontSize: 13, fontWeight: 700, color: '#10B981' }}>{c.val}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button onClick={onClose} className="md-btn-export">Close Details</button>
        </div>
      </div>
    </div>
  );
};

/* ==========================================================
   4. Upgrade to Premium Modal
   ========================================================== */
interface UpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const UpgradeModal: React.FC<UpgradeModalProps> = ({ isOpen, onClose }) => {
  const [upgraded, setUpgraded] = useState(false);

  if (!isOpen) return null;

  return (
    <div className="md-modal-backdrop" onClick={onClose}>
      <div className="md-modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: 620 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 40,
              height: 40,
              borderRadius: 10,
              background: 'linear-gradient(135deg, #2563EB, #1E40AF)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Shield size={20} color="#FFFFFF" />
            </div>
            <div>
              <h3 style={{ fontSize: 18, fontWeight: 700 }}>Upgrade to Enterprise Suite</h3>
              <p style={{ fontSize: 12, color: 'var(--md-text-secondary)' }}>
                Unlock high-throughput SAP automation and unlimited AI agent conversations
              </p>
            </div>
          </div>
          <button onClick={onClose} className="md-more-btn"><X size={18} /></button>
        </div>

        {upgraded ? (
          <div style={{ textAlign: 'center', padding: '30px 20px' }}>
            <div style={{
              width: 56,
              height: 56,
              borderRadius: '50%',
              background: '#E6FBF2',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: 16
            }}>
              <Check size={28} color="#10B981" />
            </div>
            <h4 style={{ fontSize: 18, fontWeight: 700, marginBottom: 6 }}>Account Upgraded!</h4>
            <p style={{ fontSize: 13, color: 'var(--md-text-secondary)', marginBottom: 20 }}>
              Your workspace now has access to Enterprise Pro Service Layer features and priority AI quotas.
            </p>
            <button onClick={onClose} className="md-btn-export" style={{ margin: '0 auto' }}>Back to Dashboard</button>
          </div>
        ) : (
          <div>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: 16,
              marginBottom: 24
            }}>
              <div style={{
                padding: '20px 18px',
                borderRadius: 'var(--md-radius-md)',
                border: '1px solid var(--md-border)',
                background: '#FAFBFD'
              }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--md-text-muted)', textTransform: 'uppercase' }}>Standard</div>
                <div style={{ fontSize: 24, fontWeight: 800, margin: '8px 0 12px' }}>$0 <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--md-text-secondary)' }}>/ month</span></div>
                <ul style={{ listStyle: 'none', fontSize: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <li>✓ Multi-doc extraction</li>
                  <li>✓ Standard deterministic validation</li>
                  <li>✓ 50 AI queries / day</li>
                </ul>
              </div>

              <div style={{
                padding: '20px 18px',
                borderRadius: 'var(--md-radius-md)',
                border: '2px solid #0A0A0A',
                background: '#FFF7ED',
                position: 'relative'
              }}>
                <span style={{
                  position: 'absolute',
                  top: -10,
                  right: 14,
                  background: '#0A0A0A',
                  color: '#FFFFFF',
                  fontSize: 10,
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: 10
                }}>POPULAR</span>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#EA580C', textTransform: 'uppercase' }}>Enterprise Pro</div>
                <div style={{ fontSize: 24, fontWeight: 800, margin: '8px 0 12px', color: '#0A0A0A' }}>$99 <span style={{ fontSize: 12, fontWeight: 500, color: '#EA580C' }}>/ month</span></div>
                <ul style={{ listStyle: 'none', fontSize: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <li>✓ Unlimited SAP Service Layer writes</li>
                  <li>✓ Fast NVIDIA Nemotron 30B LLM</li>
                  <li>✓ Batch Excel & CSV multi-engine OCR</li>
                  <li>✓ 24/7 dedicated Service Layer support</li>
                </ul>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button onClick={onClose} className="md-pill-btn">Cancel</button>
              <button
                onClick={() => setUpgraded(true)}
                className="md-btn-upgrade"
                style={{ width: 'auto', padding: '10px 24px' }}
              >
                Upgrade to Enterprise Pro
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

/* ==========================================================
   6. SAP Record Inspector Modal
   ========================================================== */
interface SapRecordInspectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  record: { type: string; data: any } | null;
  onNavigateToModule?: (mod: string) => void;
}

export const SapRecordInspectorModal: React.FC<SapRecordInspectorModalProps> = ({
  isOpen,
  onClose,
  record,
  onNavigateToModule
}) => {
  const [copied, setCopied] = useState(false);

  if (!isOpen || !record || !record.data) return null;

  const data = record.data;
  const isItem = record.type.toLowerCase().includes('item');
  const isBP = record.type.toLowerCase().includes('partner') || record.type.toLowerCase().includes('business');
  const isWhs = record.type.toLowerCase().includes('warehouse');

  const titleCode = data.ItemCode || data.CardCode || data.WarehouseCode || data.workflow_id || 'RECORD';
  const titleName = data.ItemName || data.CardName || data.WarehouseName || data.filename || 'SAP Object';

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="md-modal-backdrop" onClick={onClose}>
      <div
        className="md-modal-content"
        style={{ maxWidth: 680 }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, borderBottom: '1px solid var(--md-border)', paddingBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 38,
              height: 38,
              borderRadius: 'var(--md-radius-sm)',
              background: '#0A0A0A',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#FFFFFF'
            }}>
              <Shield size={20} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <h3 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>{titleCode}</h3>
                <span style={{
                  fontSize: 10.5,
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: 9999,
                  background: '#FFF7ED',
                  color: '#EA580C',
                  border: '1px solid #FFEDD5'
                }}>
                  {record.type}
                </span>
              </div>
              <p style={{ fontSize: 12, color: 'var(--md-text-secondary)', margin: '2px 0 0' }}>{titleName}</p>
            </div>
          </div>
          <button onClick={onClose} className="md-more-btn"><X size={18} /></button>
        </div>

        {/* Primary Field Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: 10,
          marginBottom: 16
        }}>
          {Object.entries(data)
            .filter(([k, v]) => typeof v !== 'object' && !k.startsWith('@odata'))
            .slice(0, 9)
            .map(([k, v], idx) => (
              <div key={idx} className="md-inspector-card">
                <span style={{ fontSize: 10.5, color: 'var(--md-text-muted)', textTransform: 'uppercase', fontWeight: 600, display: 'block', marginBottom: 2 }}>
                  {k.replace(/([A-Z])/g, ' $1').trim()}
                </span>
                <strong style={{ fontSize: 12.5, color: 'var(--md-text-primary)', wordBreak: 'break-word' }}>
                  {v !== null && v !== undefined && String(v) !== '' ? String(v) : '—'}
                </strong>
              </div>
            ))}
        </div>

        {/* Raw Database Payload JSON */}
        <div style={{ marginBottom: 18 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
            <span style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--md-text-secondary)' }}>
              Raw SAP Service Layer Payload (JSON)
            </span>
            <button
              onClick={handleCopyJson}
              className="md-pill-btn"
              style={{ fontSize: 11, padding: '4px 10px', gap: 4 }}
            >
              {copied ? <Check size={12} color="#10B981" /> : <Package size={12} />}
              <span>{copied ? 'Copied to Clipboard!' : 'Copy JSON'}</span>
            </button>
          </div>
          <pre className="md-json-block">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>

        {/* Footer Actions */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--md-border)', paddingTop: 12 }}>
          {onNavigateToModule && (isItem || isBP || isWhs) && (
            <button
              onClick={() => {
                onClose();
                if (isItem) onNavigateToModule('item-master');
                else if (isBP) onNavigateToModule('business-partner');
                else if (isWhs) onNavigateToModule('warehouse-master');
              }}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#EA580C',
                fontSize: 12,
                fontWeight: 600,
                cursor: 'pointer',
                textDecoration: 'underline'
              }}
            >
              Open in full {record.type} module →
            </button>
          )}
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            <button onClick={onClose} className="md-btn-export">Close</button>
          </div>
        </div>
      </div>
    </div>
  );
};

