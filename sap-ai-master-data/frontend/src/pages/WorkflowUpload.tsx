import React, { useState, useRef } from 'react';
import { api } from '../services/api';
import type { BulkCreationSummary, WorkflowState } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { ExtractorCompareCard } from '../components/ExtractorCompareCard';
import { ExtractedDataViewer } from '../components/ExtractedDataViewer';
import { ChatDrawer } from '../components/ChatDrawer';
import { ConfirmationModal } from '../components/ConfirmationModal';
import { BulkConfirmModal } from '../components/BulkConfirmModal';
import { BulkResultsViewer } from '../components/BulkResultsViewer';
import { MissingFieldsTable } from '../components/MissingFieldsTable';
import {
  UploadCloud,
  FileCheck,
  AlertCircle,
  CheckCircle,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  RotateCcw,
  Check,
  FileSpreadsheet,
  Layers,
} from 'lucide-react';

export const WorkflowUpload: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedType, setSelectedType] = useState<string>('auto');
  const [uploadProgressStep, setUploadProgressStep] = useState<string | null>(null);
  const [workflow, setWorkflow] = useState<WorkflowState | null>(null);
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [postingLoading, setPostingLoading] = useState(false);
  const [creationSuccess, setCreationSuccess] = useState<any | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Bulk Master Data State
  const [isBulkConfirmModalOpen, setIsBulkConfirmModalOpen] = useState(false);
  const [selectedBulkIndices, setSelectedBulkIndices] = useState<number[] | null>(null);
  const [isBulkPosting, setIsBulkPosting] = useState(false);
  const [bulkCreationSummary, setBulkCreationSummary] = useState<BulkCreationSummary | null>(null);
  const [activeRecordIndex, setActiveRecordIndex] = useState<number>(0);
  const [isUpdatingRecord, setIsUpdatingRecord] = useState<boolean>(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const isExcelFile = (filename: string) => {
    const f = filename.toLowerCase();
    return f.endsWith('.xlsx') || f.endsWith('.xls') || f.endsWith('.csv');
  };

  const isValidDocumentFile = (file: File) => {
    const f = file.name.toLowerCase();
    return f.endsWith('.pdf') || f.endsWith('.xlsx') || f.endsWith('.xls') || f.endsWith('.csv');
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (isValidDocumentFile(file)) {
        setSelectedFile(file);
        setErrorMessage(null);
      } else {
        setErrorMessage('Please upload a valid PDF or Excel document (.pdf, .xlsx, .xls, .csv).');
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (isValidDocumentFile(file)) {
        setSelectedFile(file);
        setErrorMessage(null);
      } else {
        setErrorMessage('Please upload a valid PDF or Excel document (.pdf, .xlsx, .xls, .csv).');
      }
    }
  };


  const startExtractionPipeline = async () => {
    if (!selectedFile) return;

    setErrorMessage(null);
    setUploadProgressStep('Uploading document...');

    try {
      // Step 1: Uploading
      setTimeout(() => setUploadProgressStep('Reading document across 3 independent engines...'), 600);
      setTimeout(() => setUploadProgressStep('Normalizing values & checking extraction consensus...'), 1200);
      setTimeout(() => setUploadProgressStep('Running deterministic SAP validation...'), 1800);

      const res = await api.uploadDocument(selectedFile, selectedType);

      if (!res.success) {
        setErrorMessage(res.message || 'Validation error during upload.');
        setUploadProgressStep(null);
        return;
      }

      // Fetch complete workflow state
      const wfState = await api.getWorkflow(res.data.workflow_id);
      setWorkflow(wfState);
      setUploadProgressStep(null);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.message || err.message || 'Failed to process document');
      setUploadProgressStep(null);
    }
  };

  const handleResolveConflict = async (corrections: Record<string, any>) => {
    if (!workflow) return;
    try {
      await api.resolveConflict(workflow.workflow_id, corrections);
      const updated = await api.getWorkflow(workflow.workflow_id);
      setWorkflow(updated);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.message || 'Failed to resolve conflicts.');
    }
  };

  const handleSelectRecord = async (index: number) => {
    if (!workflow) return;
    try {
      setErrorMessage(null);
      setActiveRecordIndex(index);
      const res = await api.selectWorkflowRecord(workflow.workflow_id, index);
      if (res && res.success) {
        setWorkflow(res.data);
      }
    } catch (err: any) {
      setErrorMessage(err.response?.data?.message || 'Failed to switch active record.');
    }
  };

  const handleUpdateRecord = async (payload: {
    updates?: Record<string, any>;
    index?: number;
    apply_to_all?: boolean;
    records?: Record<string, any>[];
  }) => {
    if (!workflow) return;
    setIsUpdatingRecord(true);
    try {
      setErrorMessage(null);
      const res = await api.updateWorkflowRecord(workflow.workflow_id, {
        ...payload,
        index: payload.index ?? activeRecordIndex,
      });
      if (res && res.success) {
        setWorkflow(res.data);
      } else {
        setErrorMessage(res?.message || 'Failed to update record.');
      }
    } catch (err: any) {
      const msg = err.response?.data?.message || err.response?.data?.detail || err.message;
      setErrorMessage(msg || 'Failed to update record.');
      throw err;
    } finally {
      setIsUpdatingRecord(false);
    }
  };

  const refreshWorkflow = async () => {
    if (!workflow) return;
    try {
      const updated = await api.getWorkflow(workflow.workflow_id);
      setWorkflow(updated);
    } catch (e) {
      console.error('Failed to refresh workflow', e);
    }
  };

  const handleConfirmAndPost = async () => {
    if (!workflow) return;
    setPostingLoading(true);
    setErrorMessage(null);

    try {
      // Step 1: Confirm gate
      await api.confirmWorkflow(workflow.workflow_id);

      // Step 2: Post to Service Layer based on master type
      let createRes;
      if (workflow.master_type === 'item') {
        createRes = await api.createItemInSap(workflow.workflow_id);
      } else if (workflow.master_type === 'business_partner') {
        createRes = await api.createBusinessPartnerInSap(workflow.workflow_id);
      } else if (workflow.master_type === 'warehouse') {
        createRes = await api.createWarehouseInSap(workflow.workflow_id);
      }

      if (createRes && createRes.success) {
        setCreationSuccess(createRes.data);
        setIsConfirmModalOpen(false);
        const updated = await api.getWorkflow(workflow.workflow_id);
        setWorkflow(updated);
      } else {
        setErrorMessage(createRes?.message || 'SAP creation failed.');
        setIsConfirmModalOpen(false);
      }
    } catch (err: any) {
      const msg = err.response?.data?.message || err.response?.data?.detail || err.message;
      setErrorMessage(msg);
      setIsConfirmModalOpen(false);
    } finally {
      setPostingLoading(false);
    }
  };

  const handleBulkCreateTrigger = (indices: number[]) => {
    setSelectedBulkIndices(indices);
    setIsBulkConfirmModalOpen(true);
  };

  const handleBulkConfirmAndPost = async (options: { skipDuplicates: boolean; continueOnError: boolean }) => {
    if (!workflow) return;
    setIsBulkPosting(true);
    setErrorMessage(null);

    try {
      // Step 1: Bulk confirm gate
      await api.bulkConfirmWorkflow(workflow.workflow_id);

      // Step 2: Post bulk to Service Layer
      const res = await api.bulkCreateInSap(workflow.workflow_id, {
        indices: selectedBulkIndices ?? undefined,
        skipDuplicates: options.skipDuplicates,
        continueOnError: options.continueOnError,
      });

      if (res && res.success) {
        setBulkCreationSummary(res.data.summary);
        setIsBulkConfirmModalOpen(false);
        const updated = await api.getWorkflow(workflow.workflow_id);
        setWorkflow(updated);
      } else {
        setErrorMessage(res?.message || 'Bulk SAP creation failed.');
        setIsBulkConfirmModalOpen(false);
      }
    } catch (err: any) {
      const msg = err.response?.data?.message || err.response?.data?.detail || err.message;
      setErrorMessage(msg);
      setIsBulkConfirmModalOpen(false);
    } finally {
      setIsBulkPosting(false);
    }
  };

  const handleApplyDefaults = async (defaults: Record<string, any>) => {
    if (!workflow) return;
    try {
      const res = await api.bulkApplyDefaults(workflow.workflow_id, defaults);
      if (res && res.success) {
        setWorkflow(res.data);
      }
    } catch (err: any) {
      setErrorMessage(err.response?.data?.message || 'Failed to apply batch defaults.');
    }
  };

  const resetProcess = () => {
    setSelectedFile(null);
    setWorkflow(null);
    setCreationSuccess(null);
    setBulkCreationSummary(null);
    setSelectedBulkIndices(null);
    setErrorMessage(null);
    setUploadProgressStep(null);
    setActiveRecordIndex(0);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      {/* Page Title */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: 24, fontWeight: 700, letterSpacing: -0.4 }}>
            Document Upload & Master Data Pipeline
          </h2>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            Extract master data from specifications or invoices with multi-method consensus verification
          </p>
        </div>
        {workflow && (
          <button onClick={resetProcess} className="btn btn-secondary" style={{ fontSize: 13 }}>
            <RotateCcw size={15} /> Upload Another Document
          </button>
        )}
      </div>

      {/* Error Alert */}
      {errorMessage && (
        <div style={{
          padding: 16,
          background: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          color: '#F87171'
        }}>
          <AlertCircle size={20} />
          <div style={{ fontSize: 14 }}>{errorMessage}</div>
        </div>
      )}

      {/* Success Screen (Single Record) */}
      {creationSuccess && !bulkCreationSummary && (
        <div className="glass-panel" style={{
          padding: 36,
          textAlign: 'center',
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(15, 23, 42, 0.8) 100%)',
          border: '1px solid rgba(16, 185, 129, 0.4)'
        }}>
          <div style={{
            width: 64,
            height: 64,
            borderRadius: '50%',
            background: 'rgba(16, 185, 129, 0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 16px',
            boxShadow: '0 0 24px rgba(16, 185, 129, 0.3)'
          }}>
            <CheckCircle size={36} color="#34D399" />
          </div>

          <h3 style={{ fontSize: 22, fontWeight: 700, color: '#34D399', marginBottom: 8 }}>
            Master Data Created Successfully in SAP!
          </h3>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 20 }}>
            Authoritative Service Layer POST dispatched and confirmed with zero SQL writes.
          </p>

          <div style={{
            display: 'inline-flex',
            gap: 24,
            background: '#F8FAFC',
            padding: '16px 28px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid #E2E8F0',
            marginBottom: 24,
            textAlign: 'left'
          }}>
            <div>
              <span style={{ fontSize: 11, color: '#64748B', display: 'block' }}>SAP IDENTIFIER</span>
              <strong style={{ fontSize: 16, color: '#2563EB' }}>{creationSuccess.sap_object_id}</strong>
            </div>
            <div>
              <span style={{ fontSize: 11, color: '#64748B', display: 'block' }}>MASTER TYPE</span>
              <strong style={{ fontSize: 16, textTransform: 'capitalize', color: '#0F172A' }}>
                {creationSuccess.master_type?.replace('_', ' ')}
              </strong>
            </div>
            <div>
              <span style={{ fontSize: 11, color: '#64748B', display: 'block' }}>AUDIT STATUS</span>
              <strong style={{ fontSize: 16, color: '#166534' }}>Logged & Verified</strong>
            </div>
          </div>

          <div>
            <button onClick={resetProcess} className="btn btn-primary" style={{ padding: '12px 24px' }}>
              Create Another Record <ArrowRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Bulk Results Screen */}
      {bulkCreationSummary && workflow && (
        <BulkResultsViewer
          summary={bulkCreationSummary}
          masterType={workflow.master_type}
          onReset={resetProcess}
        />
      )}

      {/* Upload Screen (If no active workflow or success or bulk summary) */}
      {!workflow && !creationSuccess && !bulkCreationSummary && (
        <div className="glass-panel" style={{ padding: 32 }}>
          {/* Master Data Type Selection */}
          <div style={{ marginBottom: 24 }}>
            <label className="form-label" style={{ marginBottom: 10, fontSize: 14 }}>
              Select Master Data Target (or leave as Auto-Detect)
            </label>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              {[
                { id: 'auto', label: 'Auto-Detect from Document' },
                { id: 'item', label: 'Item Master' },
                { id: 'business_partner', label: 'Business Partner' },
                { id: 'warehouse', label: 'Warehouse Master' },
              ].map((opt) => (
                <button
                  key={opt.id}
                  onClick={() => setSelectedType(opt.id)}
                  className={`btn ${selectedType === opt.id ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '10px 18px', fontSize: 13 }}
                >
                  {selectedType === opt.id && <Check size={14} />}
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Dropzone */}
          <div
            className={`dropzone ${selectedFile ? 'active' : ''}`}
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleFileDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept=".pdf,.xlsx,.xls,.csv,application/pdf,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,text/csv"
              style={{ display: 'none' }}
            />

            <div style={{
              width: 56,
              height: 56,
              borderRadius: '50%',
              background: 'rgba(59, 130, 246, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px'
            }}>
              {selectedFile && isExcelFile(selectedFile.name) ? (
                <FileSpreadsheet size={28} color="#10B981" />
              ) : (
                <UploadCloud size={28} color="#3B82F6" />
              )}
            </div>

            {selectedFile ? (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginBottom: 4 }}>
                  {isExcelFile(selectedFile.name) ? (
                    <FileSpreadsheet size={18} color="#10B981" />
                  ) : (
                    <FileCheck size={18} color="#10B981" />
                  )}
                  <strong style={{ fontSize: 16, color: '#F8FAFC' }}>{selectedFile.name}</strong>
                  <span style={{
                    fontSize: 10,
                    fontWeight: 700,
                    padding: '2px 8px',
                    borderRadius: 4,
                    background: isExcelFile(selectedFile.name) ? 'rgba(16, 185, 129, 0.2)' : 'rgba(59, 130, 246, 0.2)',
                    color: isExcelFile(selectedFile.name) ? '#34D399' : '#60A5FA'
                  }}>
                    {isExcelFile(selectedFile.name) ? 'EXCEL / SPREADSHEET' : 'PDF DOCUMENT'}
                  </span>
                </div>
                <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                  {(selectedFile.size / 1024).toFixed(1)} KB • Ready for extraction
                </p>
              </div>
            ) : (
              <div>
                <strong style={{ fontSize: 16, display: 'block', marginBottom: 6 }}>
                  Drag & Drop Master Data PDF or Excel file here
                </strong>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                  or click to browse your files (supports PDF documents, Excel workbooks <code>.xlsx</code>, and CSV spreadsheets)
                </p>
              </div>
            )}
          </div>

          {/* Action Button & Progress */}
          <div style={{ marginTop: 28, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14 }}>
            {uploadProgressStep && (
              <div style={{ width: '100%', maxWidth: 440, textAlign: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginBottom: 8, color: '#60A5FA', fontSize: 13, fontWeight: 500 }}>
                  <span className="pulse-animation" style={{ width: 8, height: 8, borderRadius: '50%', background: '#3B82F6' }} />
                  {uploadProgressStep}
                </div>
                <div style={{ height: 4, background: '#1E293B', borderRadius: 2, overflow: 'hidden' }}>
                  <div style={{ width: '80%', height: '100%', background: 'linear-gradient(90deg, #3B82F6, #60A5FA)', borderRadius: 2 }} className="pulse-animation" />
                </div>
              </div>
            )}

            <button
              onClick={startExtractionPipeline}
              disabled={!selectedFile || uploadProgressStep !== null}
              className="btn btn-primary"
              style={{ padding: '12px 36px', fontSize: 15 }}
            >
              Start Automated Extraction & Validation <ArrowRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Active Workflow Workspace */}
      {workflow && !creationSuccess && !bulkCreationSummary && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Workflow Header Status Banner */}
          <div className="glass-panel" style={{ padding: '20px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                <StatusBadge status={workflow.status} />
                <span style={{ fontSize: 13, fontWeight: 600, color: '#60A5FA' }}>
                  Workflow #{workflow.workflow_id.substring(0, 8)}
                </span>
                <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>•</span>
                <span style={{ fontSize: 13, textTransform: 'capitalize', color: 'var(--text-secondary)' }}>
                  {workflow.master_type.replace('_', ' ')} Master
                </span>
                {(workflow.extracted_records?.length || 0) > 1 && (
                  <>
                    <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>•</span>
                    <span style={{
                      fontSize: 12,
                      padding: '2px 10px',
                      borderRadius: 12,
                      background: 'rgba(59, 130, 246, 0.2)',
                      border: '1px solid rgba(59, 130, 246, 0.4)',
                      color: '#93C5FD',
                      fontWeight: 600,
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 4
                    }}>
                      <Layers size={13} /> Bulk Mode ({(workflow.extracted_records || []).length} Records)
                    </span>
                  </>
                )}
              </div>
              <p style={{ fontSize: 14, color: 'var(--text-primary)' }}>
                {workflow.message}
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
              {(workflow.extracted_records?.length || 0) > 1 ? (
                <>
                  <button
                    onClick={() => handleBulkCreateTrigger(Array.from(Array((workflow.extracted_records || []).length).keys()))}
                    className="btn btn-success"
                    style={{
                      padding: '10px 22px',
                      fontSize: 14,
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      boxShadow: '0 0 16px rgba(16, 185, 129, 0.35)',
                    }}
                  >
                    <ShieldCheck size={18} /> Confirm & Create All ({(workflow.extracted_records || []).length}) in SAP
                  </button>
                  {workflow.status === 'READY_FOR_CONFIRMATION' && (
                    <button
                      onClick={() => setIsConfirmModalOpen(true)}
                      className="btn btn-secondary"
                      style={{ padding: '10px 16px', fontSize: 13 }}
                    >
                      Create Active Record Only
                    </button>
                  )}
                </>
              ) : (
                workflow.status === 'READY_FOR_CONFIRMATION' && (
                  <button
                    onClick={() => setIsConfirmModalOpen(true)}
                    className="btn btn-success"
                    style={{ padding: '10px 20px', fontSize: 14 }}
                  >
                    <ShieldCheck size={18} /> Confirm & Create in SAP
                  </button>
                )
              )}
            </div>
          </div>

          {/* Section 1: Primary Document Extracted Data, Multi-Record Table & 3-Engine Inspector */}
          <ExtractedDataViewer
            workflow={workflow}
            onSelectRecord={handleSelectRecord}
            onBulkCreate={handleBulkCreateTrigger}
            onApplyDefaults={handleApplyDefaults}
            onUpdateRecord={handleUpdateRecord}
          />

          {/* Section 2: Extraction Conflict Resolver (Shown if engines disagree) */}
          {workflow.extraction_comparison && workflow.extraction_comparison.conflicts && workflow.extraction_comparison.conflicts.length > 0 && (
            <ExtractorCompareCard
              comparison={workflow.extraction_comparison}
              onResolveConflict={handleResolveConflict}
            />
          )}

          {/* Section 2: Split Layout (Preview Table vs Conversational Chat) */}
          <div className="grid-2" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', alignItems: 'start' }}>
            {/* Left Column: Deterministic Validation Preview */}
            <div className="glass-panel" style={{ padding: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <h3 style={{ fontSize: 16, fontWeight: 600 }}>Deterministic Field Preview</h3>
                <StatusBadge status={workflow.validation_result?.valid ? 'AGREED' : 'MISSING_FIELDS'} />
              </div>

              {/* Validation Status Banner if Valid */}
              {workflow.validation_result?.valid && (
                <div
                  style={{
                    background: '#F0FDF4',
                    border: '1px solid #BBF7D0',
                    borderRadius: 'var(--radius-md)',
                    padding: '12px 16px',
                    marginBottom: 16,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                  }}
                >
                  <div
                    style={{
                      width: 30,
                      height: 30,
                      borderRadius: '50%',
                      background: '#DCFCE7',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#16A34A',
                      flexShrink: 0,
                    }}
                  >
                    <CheckCircle2 size={17} />
                  </div>
                  <div>
                    <strong style={{ fontSize: 13, color: '#166534', display: 'block' }}>
                      All Deterministic Validation Rules Passed
                    </strong>
                    <span style={{ fontSize: 12, color: '#475569' }}>
                      All mandatory SAP fields are present. You can edit any field below before confirming to SAP.
                    </span>
                  </div>
                </div>
              )}

              {/* Master Data Field Editor - rendered for EVERY record (both valid and unvalid) */}
              <div style={{ marginBottom: 20 }}>
                <MissingFieldsTable
                  missingFields={workflow.missing_fields || []}
                  masterType={workflow.master_type}
                  activeRecordIndex={activeRecordIndex}
                  totalRecords={workflow.extracted_records?.length || 1}
                  activeRecordData={workflow.normalized_data || {}}
                  onSave={async (updates, applyToAll) => {
                    await handleUpdateRecord({
                      updates,
                      index: activeRecordIndex,
                      apply_to_all: applyToAll,
                    });
                  }}
                  isSaving={isUpdatingRecord}
                />
              </div>

              {/* Normalized Data Table */}
              <div style={{
                background: '#FFFFFF',
                borderRadius: 'var(--radius-md)',
                border: '1px solid #E2E8F0',
                overflow: 'hidden'
              }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th style={{ width: '45%' }}>Field Name</th>
                      <th>Extracted Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Array.from(new Set([
                      ...(workflow.master_type === 'business_partner'
                        ? ['CardCode', 'CardName', 'CardType', 'FederalTaxID', 'PANNo', 'GSTNo', 'Address', 'TaxDetails', 'PaymentTerms', 'EmailAddress', 'Phone1', 'Currency', 'ControlAccount']
                        : workflow.master_type === 'item'
                          ? ['ItemCode', 'ItemName', 'ItemsGroupCode', 'InventoryUOM', 'ItemType', 'TaxRate', 'ItemManagementMethod', 'ItemCategory', 'MaterialType', 'TaxCategory', 'HSN']
                          : ['WarehouseCode', 'WarehouseName', 'Location', 'Address']),
                      ...Object.keys(workflow.normalized_data || {}),
                      ...(workflow.missing_fields?.map((m) => m.field) || []),
                    ])).map((k) => {
                      const v = workflow.normalized_data ? workflow.normalized_data[k] : undefined;
                      const hasV = v !== undefined && v !== null && String(v).trim() !== '';
                      return (
                        <tr key={k}>
                          <td style={{ fontWeight: 600, color: '#475569' }}>{k}</td>
                          <td style={{ color: hasV ? '#0F172A' : '#94A3B8', fontWeight: hasV ? 600 : 400, wordBreak: 'break-all' }}>
                            {hasV ? (typeof v === 'boolean' ? (v ? 'Yes' : 'No') : String(v)) : '—'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Right Column: AI Conversational Data Collection & Assistance */}
            <ChatDrawer
              workflowId={workflow.workflow_id}
              missingFields={workflow.missing_fields}
              onDataUpdated={refreshWorkflow}
            />
          </div>
        </div>
      )}

      {/* Explicit Confirmation Modal (Single Record) */}
      {workflow && (
        <ConfirmationModal
          isOpen={isConfirmModalOpen}
          masterType={workflow.master_type}
          payload={workflow.final_payload || workflow.normalized_data}
          onConfirm={handleConfirmAndPost}
          onCancel={() => setIsConfirmModalOpen(false)}
          loading={postingLoading}
        />
      )}

      {/* Explicit Bulk Confirmation Modal */}
      {workflow && (
        <BulkConfirmModal
          isOpen={isBulkConfirmModalOpen}
          onClose={() => setIsBulkConfirmModalOpen(false)}
          onConfirm={handleBulkConfirmAndPost}
          workflow={workflow}
          selectedCount={selectedBulkIndices?.length || (workflow.extracted_records?.length || 1)}
          loading={isBulkPosting}
        />
      )}
    </div>
  );
};
