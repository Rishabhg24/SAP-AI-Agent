import React, { useState } from 'react';
import type { ExtractionComparisonResult, FieldComparison } from '../types';
import { CheckCircle2, AlertTriangle, Layers, ArrowRight } from 'lucide-react';

interface Props {
  comparison: ExtractionComparisonResult;
  onResolveConflict: (corrections: Record<string, any>) => void;
}

export const ExtractorCompareCard: React.FC<Props> = ({ comparison, onResolveConflict }) => {
  const [selectedValues, setSelectedValues] = useState<Record<string, any>>({});
  const [customInputs, setCustomInputs] = useState<Record<string, string>>({});

  const handleSelectValue = (field: string, val: any) => {
    setSelectedValues((prev) => ({ ...prev, [field]: val }));
  };

  const handleApplyResolution = () => {
    const finalCorrections: Record<string, any> = {};
    comparison.conflicts.forEach((c) => {
      const chosen = selectedValues[c.field_name];
      const custom = customInputs[c.field_name];
      if (custom && custom.trim()) {
        finalCorrections[c.field_name] = custom.trim();
      } else if (chosen !== undefined) {
        finalCorrections[c.field_name] = chosen;
      }
    });

    if (Object.keys(finalCorrections).length > 0) {
      onResolveConflict(finalCorrections);
    }
  };

  const hasUnresolvedConflicts = comparison.conflicts.some(
    (c) => selectedValues[c.field_name] === undefined && !customInputs[c.field_name]
  );

  return (
    <div className="glass-panel" style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 36,
            height: 36,
            borderRadius: 'var(--radius-md)',
            background: 'rgba(59, 130, 246, 0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Layers size={20} color="#3B82F6" />
          </div>
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 600 }}>Multi-Engine Extraction Consensus</h3>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              Independent cross-validation across 3 extraction engines (Grid, Table, & Layout for Excel; PyMuPDF, pdfplumber, & OCR for PDF)
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: 11, color: 'var(--text-secondary)', display: 'block' }}>Consensus Confidence</span>
            <strong style={{ fontSize: 16, color: comparison.overall_confidence > 0.8 ? '#34D399' : '#FBBF24' }}>
              {Math.round(comparison.overall_confidence * 100)}%
            </strong>
          </div>
        </div>
      </div>

      {/* Conflicts Section */}
      {comparison.conflicts.length > 0 && (
        <div style={{
          background: '#FEF3C7',
          border: '1px solid #FDE68A',
          borderRadius: 'var(--radius-md)',
          padding: 20,
          marginBottom: 24
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
            <AlertTriangle size={18} color="#D97706" />
            <h4 style={{ fontSize: 14, fontWeight: 600, color: '#92400E', margin: 0 }}>
              Extraction Disagreement Detected ({comparison.conflicts.length} fields)
            </h4>
          </div>
          <p style={{ fontSize: 13, color: '#475569', marginBottom: 16 }}>
            The independent extraction engines returned differing values for the fields below.
            In compliance with SAP safety rules, please select the correct value or enter it manually before continuing.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {comparison.conflicts.map((conflict: FieldComparison) => (
              <div
                key={conflict.field_name}
                style={{
                  background: '#FFFFFF',
                  padding: 16,
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid #E2E8F0',
                  boxShadow: '0 1px 3px rgba(15, 23, 42, 0.04)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                  <strong style={{ fontSize: 14, color: '#0F172A' }}>{conflict.field_name}</strong>
                  <span style={{ fontSize: 11, color: '#B45309', fontWeight: 600 }}>Action Required</span>
                </div>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, alignItems: 'center' }}>
                  {conflict.distinct_values.map((val, idx) => {
                    const isSelected = selectedValues[conflict.field_name] === val;
                    const engines = Object.entries(conflict.extracted_values || {})
                      .filter(([_, v]) => v === val)
                      .map(([m]) => {
                        const names: Record<string, string> = {
                          pymupdf: 'PyMuPDF',
                          pdfplumber: 'pdfplumber',
                          ocr_layout: 'OCR',
                          excel_grid: 'Excel Grid',
                          excel_table: 'Excel Table',
                          excel_text_layout: 'Excel Layout'
                        };
                        return names[m] || m;
                      });

                    return (
                      <button
                        key={idx}
                        onClick={() => handleSelectValue(conflict.field_name, val)}
                        className={`btn ${isSelected ? 'btn-primary' : 'btn-secondary'}`}
                        style={{ padding: '8px 14px', fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}
                      >
                        {isSelected && <CheckCircle2 size={14} />}
                        <span>{String(val)}</span>
                        {engines.length > 0 && (
                          <span style={{ fontSize: 10, opacity: 0.85, padding: '1px 5px', borderRadius: 3, background: isSelected ? 'rgba(255,255,255,0.2)' : '#EFF6FF', color: isSelected ? '#FFFFFF' : '#2563EB' }}>
                            {engines.join(', ')}
                          </span>
                        )}
                      </button>
                    );
                  })}

                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1, minWidth: 200 }}>
                    <input
                      type="text"
                      className="form-input"
                      placeholder="Or enter manually..."
                      value={customInputs[conflict.field_name] || ''}
                      onChange={(e) => {
                        const val = e.target.value;
                        setCustomInputs((prev) => ({ ...prev, [conflict.field_name]: val }));
                        if (val.trim()) {
                          setSelectedValues((prev) => ({ ...prev, [conflict.field_name]: val.trim() }));
                        }
                      }}
                      style={{ padding: '8px 12px', fontSize: 13 }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 16 }}>
            <button
              onClick={handleApplyResolution}
              disabled={hasUnresolvedConflicts}
              className="btn btn-primary"
            >
              Resolve Conflicts & Re-validate <ArrowRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Agreed Fields Preview */}
      <div>
        <h4 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 12 }}>
          Consensus Verified Fields ({Object.keys(comparison.agreed_data).length})
        </h4>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
          gap: 12
        }}>
          {Object.entries(comparison.agreed_data).map(([k, v]) => (
            <div
              key={k}
              style={{
                background: '#F8FAFC',
                padding: '10px 14px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid #E2E8F0',
                display: 'flex',
                flexDirection: 'column',
                gap: 4
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: 11, color: '#64748B' }}>{k}</span>
                <CheckCircle2 size={12} color="#166534" />
              </div>
              <strong style={{ fontSize: 13, color: '#0F172A', wordBreak: 'break-all' }}>
                {typeof v === 'boolean' ? (v ? 'Yes (True)' : 'No (False)') : String(v)}
              </strong>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
