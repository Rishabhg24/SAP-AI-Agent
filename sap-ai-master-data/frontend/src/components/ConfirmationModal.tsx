import React, { useState } from 'react';
import type { MasterDataType } from '../types';
import { ShieldAlert, CheckCircle, X, ArrowRight, Layers } from 'lucide-react';

interface Props {
  isOpen: boolean;
  masterType: MasterDataType;
  payload?: Record<string, any>;
  records?: Record<string, any>[];
  isBulk?: boolean;
  onConfirm: (options?: { skipDuplicates: boolean; continueOnError: boolean }) => void;
  onCancel: () => void;
  loading: boolean;
}

export const ConfirmationModal: React.FC<Props> = ({
  isOpen,
  masterType,
  payload = {},
  records,
  isBulk = false,
  onConfirm,
  onCancel,
  loading,
}) => {
  const [skipDuplicates, setSkipDuplicates] = useState(true);
  const [continueOnError, setContinueOnError] = useState(true);

  if (!isOpen) return null;

  const isBulkMode = isBulk || (records && records.length > 1);
  const recordsList = records && records.length > 0 ? records : [payload];

  const formatKey = (k: string) => {
    return k.replace(/([A-Z])/g, ' $1').trim();
  };

  const getEntityTitle = (type: MasterDataType) => {
    switch (type) {
      case 'item':
        return 'Item Master';
      case 'business_partner':
        return 'Business Partner';
      case 'warehouse':
        return 'Warehouse';
      default:
        return 'Master Data Record';
    }
  };

  const getRecordCode = (rec: Record<string, any>) => {
    return rec.ItemCode || rec.CardCode || rec.WarehouseCode || '-';
  };

  const getRecordName = (rec: Record<string, any>) => {
    return rec.ItemName || rec.CardName || rec.WarehouseName || '-';
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(15, 23, 42, 0.55)',
        backdropFilter: 'blur(6px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 100,
        padding: 20,
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: isBulkMode ? 780 : 680,
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          background: '#FFFFFF',
          border: '1px solid #E2E8F0',
          boxShadow: '0 25px 50px -12px rgba(15, 23, 42, 0.2)',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '20px 24px',
            borderBottom: '1px solid #E2E8F0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: '#FFFFFF',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div
              style={{
                width: 38,
                height: 38,
                borderRadius: 8,
                background: isBulkMode ? '#EFF6FF' : '#DCFCE7',
                border: isBulkMode ? '1px solid #BFDBFE' : '1px solid #BBF7D0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {isBulkMode ? (
                <Layers size={20} color="#2563EB" />
              ) : (
                <CheckCircle size={20} color="#166534" />
              )}
            </div>
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 700, color: '#0F172A' }}>
                {isBulkMode
                  ? `Explicit User Confirmation (${recordsList.length} Records)`
                  : 'Explicit User Confirmation'}
              </h3>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                Target Entity: {getEntityTitle(masterType)}
              </p>
            </div>
          </div>
          <button
            onClick={onCancel}
            disabled={loading}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Notice Banner */}
        <div
          style={{
            padding: '12px 24px',
            background: '#EFF6FF',
            borderBottom: '1px solid #BFDBFE',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <ShieldAlert size={18} color="#2563EB" />
          <p style={{ fontSize: 12, color: '#1E40AF', margin: 0 }}>
            <strong>Deterministic SAP Safety Gate:</strong>{' '}
            {isBulkMode
              ? `Submitting ${recordsList.length} records safely via concurrent Service Layer worker pool. No direct database writes will occur.`
              : 'This action will send an authoritative POST request to the SAP Service Layer. No direct database writes will occur.'}
          </p>
        </div>

        {/* Content Body */}
        <div style={{ padding: 24, overflowY: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: 16 }}>
          {isBulkMode && (
            <div
              style={{
                display: 'flex',
                gap: 20,
                flexWrap: 'wrap',
                padding: '12px 16px',
                background: '#F8FAFC',
                borderRadius: 'var(--radius-md)',
                border: '1px solid #E2E8F0',
              }}
            >
              <label
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  fontSize: 13,
                  cursor: 'pointer',
                  color: '#0F172A',
                }}
              >
                <input
                  type="checkbox"
                  checked={skipDuplicates}
                  onChange={(e) => setSkipDuplicates(e.target.checked)}
                  style={{ accentColor: '#2563EB' }}
                />
                Skip duplicates in SAP (Safe idempotent creation)
              </label>

              <label
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  fontSize: 13,
                  cursor: 'pointer',
                  color: '#0F172A',
                }}
              >
                <input
                  type="checkbox"
                  checked={continueOnError}
                  onChange={(e) => setContinueOnError(e.target.checked)}
                  style={{ accentColor: '#2563EB' }}
                />
                Continue on individual record error
              </label>
            </div>
          )}

          <h4
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: 'var(--text-secondary)',
              textTransform: 'uppercase',
              letterSpacing: 0.5,
            }}
          >
            {isBulkMode ? `Batch Records Preview (${recordsList.length})` : 'Verified Master Data Payload'}
          </h4>

          {isBulkMode ? (
            <div
              style={{
                background: '#FFFFFF',
                border: '1px solid #E2E8F0',
                borderRadius: 'var(--radius-md)',
                overflow: 'hidden',
                maxHeight: 280,
                overflowY: 'auto',
              }}
            >
              <table className="data-table" style={{ width: '100%', fontSize: 12 }}>
                <thead>
                  <tr>
                    <th style={{ width: 45 }}>#</th>
                    <th>Code</th>
                    <th>Name / Description</th>
                    <th>Key Attributes</th>
                  </tr>
                </thead>
                <tbody>
                  {recordsList.map((rec, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: 600, color: '#64748B' }}>{idx + 1}</td>
                      <td style={{ fontWeight: 600, color: '#2563EB' }}>{getRecordCode(rec)}</td>
                      <td style={{ color: '#0F172A', fontWeight: 500 }}>{getRecordName(rec)}</td>
                      <td style={{ color: '#64748B', fontSize: 11 }}>
                        {Object.entries(rec)
                          .filter(
                            ([k]) =>
                              !['ItemCode', 'ItemName', 'CardCode', 'CardName', 'WarehouseCode', 'WarehouseName'].includes(
                                k
                              )
                          )
                          .slice(0, 3)
                          .map(([k, v]) => `${k}: ${String(v)}`)
                          .join(' • ')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div
              style={{
                background: '#FFFFFF',
                border: '1px solid #E2E8F0',
                borderRadius: 'var(--radius-md)',
                overflow: 'hidden',
              }}
            >
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ width: '40%' }}>Field</th>
                    <th>Value</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(payload).map(([k, v]) => (
                    <tr key={k}>
                      <td style={{ fontWeight: 600, color: '#475569' }}>{formatKey(k)}</td>
                      <td style={{ color: '#0F172A', fontWeight: 600 }}>
                        {typeof v === 'boolean' ? (v ? 'Yes (True)' : 'No (False)') : String(v)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '16px 24px',
            borderTop: '1px solid #E2E8F0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: 12,
            background: '#F8FAFC',
          }}
        >
          <button onClick={onCancel} disabled={loading} className="btn btn-secondary">
            Cancel
          </button>
          <button
            onClick={() => onConfirm({ skipDuplicates, continueOnError })}
            disabled={loading}
            className="btn btn-success"
            style={{ minWidth: 200 }}
          >
            {loading ? (
              'Creating in SAP...'
            ) : (
              <>
                {isBulkMode ? `Confirm & Create All (${recordsList.length}) in SAP` : 'Confirm & Create in SAP'}
                <ArrowRight size={16} />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
