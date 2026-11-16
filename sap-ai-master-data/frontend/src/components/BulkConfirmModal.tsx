import React, { useState } from 'react';
import { ShieldCheck, X, AlertTriangle, Layers, Database } from 'lucide-react';
import type { WorkflowState } from '../types';
import { useAuth } from '../context/AuthContext';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (options: { skipDuplicates: boolean; continueOnError: boolean }) => void;
  workflow: WorkflowState;
  selectedCount: number;
  loading: boolean;
  readyCount?: number;
  needsDataCount?: number;
}

export const BulkConfirmModal: React.FC<Props> = ({
  isOpen,
  onClose,
  onConfirm,
  workflow,
  selectedCount,
  loading,
  readyCount,
  needsDataCount = 0,
}) => {
  const { activeCompanyDb } = useAuth();
  const [acknowledged, setAcknowledged] = useState(false);
  const [skipDuplicates, setSkipDuplicates] = useState(true);
  const [continueOnError, setContinueOnError] = useState(true);

  if (!isOpen) return null;

  const masterName = workflow.master_type.replace('_', ' ').toUpperCase();

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.55)',
        backdropFilter: 'blur(6px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
        padding: 20,
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: 580,
          background: '#FFFFFF',
          border: '1px solid #E2E8F0',
          boxShadow: '0 25px 50px -12px rgba(15, 23, 42, 0.2)',
          padding: 28,
          borderRadius: 'var(--radius-lg)',
          animation: 'fadeIn 0.2s ease',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div
              style={{
                width: 44,
                height: 44,
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#2563EB',
              }}
            >
              <Layers size={24} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#0F172A' }}>
                Bulk SAP Creation Confirmation Gate
              </h3>
              <p style={{ margin: 0, fontSize: 13, color: 'var(--text-secondary)' }}>
                Commit {selectedCount} {masterName} records to SAP Service Layer
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-secondary)',
              padding: 4,
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Warning Banner */}
        <div
          style={{
            backgroundColor: '#FEF3C7',
            border: '1px solid #FCD34D',
            borderRadius: 'var(--radius-md)',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: 12,
            marginBottom: 20,
          }}
        >
          <AlertTriangle size={20} color="#D97706" style={{ flexShrink: 0, marginTop: 2 }} />
          <div style={{ fontSize: 13, color: '#92400E', lineHeight: 1.5 }}>
            <strong>Security Gate Enforcement:</strong> You are about to initiate live batch writes directly into SAP. Zero writes occur without explicit consent.
          </div>
        </div>

        {/* Summary Table */}
        <div
          style={{
            background: 'var(--surface-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: 16,
            marginBottom: 20,
            display: 'flex',
            flexDirection: 'column',
            gap: 10,
            fontSize: 13,
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #E2E8F0', paddingBottom: 8 }}>
            <span style={{ color: 'var(--text-secondary)' }}>Target Entity:</span>
            <span style={{ fontWeight: 600, color: '#0F172A' }}>{masterName} Master</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #E2E8F0', paddingBottom: 8 }}>
            <span style={{ color: 'var(--text-secondary)' }}>Records to Create:</span>
            <span style={{ fontWeight: 700, color: '#15803D' }}>
              {selectedCount} Records{' '}
              {readyCount !== undefined && (
                <span style={{ fontSize: 12, fontWeight: 600 }}>
                  (<span style={{ color: '#15803D' }}>{readyCount} Mandatory Passed</span>
                  {needsDataCount !== undefined && needsDataCount > 0 ? (
                    <>, <span style={{ color: '#DC2626' }}>{needsDataCount} Mandatory Field Required</span></>
                  ) : ''})
                </span>
              )}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #E2E8F0', paddingBottom: 8 }}>
            <span style={{ color: 'var(--text-secondary)' }}>Connected Company DB:</span>
            <span style={{ fontWeight: 600, color: '#2563EB', display: 'flex', alignItems: 'center', gap: 5 }}>
              <Database size={13} /> {activeCompanyDb || 'TEST_SHOES_10SEP26'}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Execution Strategy:</span>
            <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>Concurrent Batch (Semaphore: 4)</span>
          </div>
        </div>

        {/* Options */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 22 }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontSize: 13, color: '#0F172A' }}>
            <input
              type="checkbox"
              checked={skipDuplicates}
              onChange={(e) => setSkipDuplicates(e.target.checked)}
              style={{ width: 16, height: 16, accentColor: '#2563EB', cursor: 'pointer' }}
            />
            <span>
              <strong>Skip duplicate records</strong> if already present in SAP
            </span>
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', fontSize: 13, color: '#0F172A' }}>
            <input
              type="checkbox"
              checked={continueOnError}
              onChange={(e) => setContinueOnError(e.target.checked)}
              style={{ width: 16, height: 16, accentColor: '#2563EB', cursor: 'pointer' }}
            />
            <span>
              <strong>Continue processing batch</strong> even if individual records fail
            </span>
          </label>

          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              cursor: 'pointer',
              fontSize: 13,
              color: '#065F46',
              marginTop: 4,
              padding: '8px 12px',
              background: '#ECFDF5',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid #A7F3D0',
            }}
          >
            <input
              type="checkbox"
              checked={acknowledged}
              onChange={(e) => setAcknowledged(e.target.checked)}
              style={{ width: 16, height: 16, accentColor: '#059669', cursor: 'pointer' }}
            />
            <span>
              I explicitly confirm and authorize bulk creation of these {selectedCount} records in SAP.
            </span>
          </label>
        </div>

        {/* Modal Actions */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="btn btn-secondary"
            style={{ padding: '10px 20px', fontSize: 13 }}
          >
            Cancel
          </button>

          <button
            type="button"
            onClick={() => onConfirm({ skipDuplicates, continueOnError })}
            disabled={!acknowledged || loading || selectedCount === 0}
            className="btn btn-success"
            style={{
              padding: '10px 24px',
              fontSize: 13,
              opacity: !acknowledged || loading ? 0.6 : 1,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <ShieldCheck size={18} />
            {loading ? 'Executing Bulk Creation...' : `Confirm & Bulk Create in SAP (${selectedCount})`}
          </button>
        </div>
      </div>
    </div>
  );
};
