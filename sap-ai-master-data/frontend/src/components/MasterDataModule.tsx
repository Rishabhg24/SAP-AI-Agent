import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';
import type { BulkCreationSummary, MasterDataType, WorkflowState } from '../types';
import { ConfirmationModal } from './ConfirmationModal';
import { BulkConfirmModal } from './BulkConfirmModal';
import { BulkResultsViewer } from './BulkResultsViewer';
import {
  UploadCloud,
  FileCheck,
  CheckCircle,
  AlertCircle,
  ShieldCheck,
  RotateCcw,
  Sparkles,
  ArrowRight,
  Database,
  Search,
  RefreshCw,
  Package,
  Users,
  Warehouse,
  Send,
  Eye,
  FileSpreadsheet,
  Wand2,
  ClipboardList,
  CheckSquare,
  Square,
  X,
  Edit3,
} from 'lucide-react';

const ALL_MODULE_FIELDS: Record<MasterDataType, string[]> = {
  business_partner: [
    'CardCode',
    'CardName',
    'CardType',
    'FederalTaxID',
    'PANNo',
    'GSTNo',
    'Address',
    'TaxDetails',
    'PaymentTerms',
    'Currency',
    'ControlAccount',
    'EmailAddress',
    'Phone1',
    'Phone2',
  ],
  item: [
    'ItemCode',
    'ItemName',
    'ItemsGroupCode',
    'InventoryUOM',
    'ItemType',
    'TaxRate',
    'ItemManagementMethod',
    'ItemCategory',
    'MaterialType',
    'TaxCategory',
    'HSN',
    'SalesUnit',
    'PurchaseUnit',
    'BarCode',
    'SalesUnitWeight',
  ],
  warehouse: [
    'WarehouseCode',
    'WarehouseName',
    'Location',
    'Address',
    'Street',
    'City',
    'Country',
    'Inactive',
    'BinActivat',
  ],
  unknown: [],
};

const MANDATORY_MODULE_FIELDS: Record<MasterDataType, string[]> = {
  business_partner: [
    'CardCode',
    'CardName',
    'CardType',
  ],
  item: [
    'ItemCode',
    'ItemName',
  ],
  warehouse: [
    'WarehouseCode',
  ],
  unknown: [],
};

interface Props {
  masterType: MasterDataType;
  title: string;
  serviceLayerEndpoint: string;
  description: string;
  onNavigateToAudit?: () => void;
}

export const MasterDataModule: React.FC<Props> = ({
  masterType,
  title,
  serviceLayerEndpoint,
  description,
  onNavigateToAudit,
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'form' | 'pdf' | 'records'>('form');

  // Live count
  const [liveCount, setLiveCount] = useState<number | null>(null);

  // Form State
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const [schemaValidationResult, setSchemaValidationResult] = useState<any | null>(null);
  const [validatingSchema, setValidatingSchema] = useState(false);

  // PDF Upload & Extraction State
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [extractionStep, setExtractionStep] = useState<string | null>(null);
  const [extractedSummary, setExtractedSummary] = useState<any | null>(null);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Bulk Master Data State
  const [bulkWorkflow, setBulkWorkflow] = useState<WorkflowState | null>(null);
  const [bulkRecords, setBulkRecords] = useState<Record<string, any>[]>([]);
  const [selectedBulkRowIndices, setSelectedBulkRowIndices] = useState<Set<number>>(new Set());
  const [bulkPostingLoading, setBulkPostingLoading] = useState(false);
  const [bulkCreationSummary, setBulkCreationSummary] = useState<BulkCreationSummary | null>(null);
  const [isBulkConfirmOpen, setIsBulkConfirmOpen] = useState(false);
  const [bulkSearchFilter, setBulkSearchFilter] = useState('');
  const [bulkStatusFilter, setBulkStatusFilter] = useState<'ALL' | 'READY' | 'NEEDS_DATA'>('ALL');
  const [isDefaultsModalOpen, setIsDefaultsModalOpen] = useState(false);
  const [defaultsForm, setDefaultsForm] = useState<Record<string, any>>({});

  // Inline editing and expansion for bulk records
  const [expandedBulkRowIndex, setExpandedBulkRowIndex] = useState<number | null>(null);
  const [bulkRowDrafts, setBulkRowDrafts] = useState<Record<number, Record<string, any>>>({});
  const [isBulkTableEditMode, setIsBulkTableEditMode] = useState(false);
  const [bulkInlineEdits, setBulkInlineEdits] = useState<Record<number, Record<string, any>>>({});
  const [isSavingBulkRow, setIsSavingBulkRow] = useState(false);
  const [isSavingBulkTableEdits, setIsSavingBulkTableEdits] = useState(false);

  // Direct Bulk Paste State
  const [entryMode, setEntryMode] = useState<'single' | 'bulk_paste'>('single');
  const [pastedText, setPastedText] = useState('');
  const [parsedPasteRows, setParsedPasteRows] = useState<Record<string, any>[]>([]);
  const [pasteError, setPasteError] = useState<string | null>(null);
  const [isDirectBulkConfirmOpen, setIsDirectBulkConfirmOpen] = useState(false);

  // SAP Posting State
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [postingLoading, setPostingLoading] = useState(false);
  const [creationSuccess, setCreationSuccess] = useState<any | null>(null);
  const [postingError, setPostingError] = useState<string | null>(null);

  // Live Records Explorer State
  const [records, setRecords] = useState<any[]>([]);
  const [recordsTotal, setRecordsTotal] = useState<number>(0);
  const [loadingRecords, setLoadingRecords] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRecordDetails, setSelectedRecordDetails] = useState<any | null>(null);

  // Initialize default form values per master type
  useEffect(() => {
    resetForm();
    loadLiveCount();
  }, [masterType]);

  const loadLiveCount = async () => {
    try {
      const counts = await api.getSapCounts();
      if (masterType === 'item') setLiveCount(counts.Items);
      else if (masterType === 'business_partner') setLiveCount(counts.BusinessPartners);
      else if (masterType === 'warehouse') setLiveCount(counts.Warehouses);
    } catch {
      // ignore
    }
  };

  const resetForm = () => {
    if (masterType === 'item') {
      setFormData({
        ItemCode: '',
        ItemName: '',
        ItemsGroupCode: '',
        InventoryUOM: '',
        ItemType: '',
        TaxRate: '',
        ItemManagementMethod: '',
        ItemCategory: '',
        MaterialType: '',
        HSN: '',
        TaxCategory: '',
        InventoryItem: false,
        SalesItem: false,
        PurchaseItem: false,
        SalesUnit: '',
        PurchaseUnit: '',
        SalesUnitWeight: '',
        BarCode: '',
        ForeignName: '',
      });
    } else if (masterType === 'business_partner') {
      setFormData({
        CardCode: '',
        CardName: '',
        CardType: '',
        GroupCode: '',
        Address: '',
        TaxDetails: '',
        PaymentTerms: '',
        Currency: '',
        ControlAccount: '',
        GSTRegStatus: '',
        GSTNo: '',
        PANNo: '',
        EmailAddress: '',
        Phone1: '',
        Phone2: '',
        FederalTaxID: '',
      });
    } else if (masterType === 'warehouse') {
      setFormData({
        WarehouseCode: '',
        WarehouseName: '',
        Location: '',
        Address: '',
        WarehouseType: '',
        Street: '',
        City: '',
        Country: '',
        Inactive: false,
        BinActivat: false,
      });
    }
    setFormErrors({});
    setSchemaValidationResult(null);
    setCreationSuccess(null);
    setPostingError(null);
  };

  // Field change handler
  const handleInputChange = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear field-specific error
    if (formErrors[field]) {
      setFormErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
    setSchemaValidationResult(null);
  };

  // Validate form client-side
  const validateFormClient = (): boolean => {
    const errors: Record<string, string> = {};

    if (masterType === 'item') {
      if (!formData.ItemCode?.trim()) errors.ItemCode = 'Item Code is mandatory.';
      else if (formData.ItemCode.length > 50) errors.ItemCode = 'Item Code max 50 characters.';

      if (!formData.ItemName?.trim()) errors.ItemName = 'Item Name is mandatory.';
      else if (formData.ItemName.length > 100) errors.ItemName = 'Item Name max 100 characters.';

      if (!formData.ItemsGroupCode && formData.ItemsGroupCode !== 0) errors.ItemsGroupCode = 'Item Group is mandatory.';

      if (!formData.InventoryUOM?.trim()) errors.InventoryUOM = 'Unit of Measure (UoM) is mandatory.';

      if (!formData.ItemType?.trim() && !formData.InventoryItem && !formData.SalesItem && !formData.PurchaseItem) {
        errors.ItemType = 'Item Type (Inventory/Sales/Purchase) is mandatory.';
      }

      if (!formData.TaxRate && formData.TaxRate !== 0) errors.TaxRate = 'Tax Rate is mandatory (e.g. 18%).';

      if (!formData.ItemManagementMethod?.trim()) errors.ItemManagementMethod = 'Item Management Method is mandatory (Serial/Batch/None).';

      if (!formData.ItemCategory?.trim()) errors.ItemCategory = 'Item Category is mandatory (Service/Item).';

      if (!formData.MaterialType?.trim()) errors.MaterialType = 'Material Type is mandatory (RM/FG/Capital Goods).';

      if (!formData.HSN?.trim()) errors.HSN = 'HSN / SAC Code is mandatory.';

      if (!formData.TaxCategory?.trim()) errors.TaxCategory = 'Tax Category is mandatory.';
    } else if (masterType === 'business_partner') {
      const code = formData.CardCode?.trim();
      if (!code) errors.CardCode = 'Customer / Vendor Code is mandatory.';
      else if (code.length > 15) errors.CardCode = `CardCode exceeds 15 chars (provided ${code.length}).`;

      if (!formData.CardName?.trim()) errors.CardName = 'Business Partner Name is mandatory.';
      else if (formData.CardName.length > 100) errors.CardName = 'CardName max 100 characters.';

      if (!formData.Address?.trim()) errors.Address = 'Address is mandatory.';

      if (!formData.TaxDetails?.trim()) errors.TaxDetails = 'Tax Details is mandatory.';

      if (!formData.PaymentTerms && formData.PaymentTerms !== 0) errors.PaymentTerms = 'Payment Terms is mandatory.';

      if (!formData.Currency?.trim()) errors.Currency = 'Currency is mandatory.';

      if (!formData.ControlAccount?.trim()) errors.ControlAccount = 'Control Account is mandatory.';

      // GST No mandatory if registered
      const regStatus = (formData.GSTRegStatus || 'Registered').toLowerCase();
      if (regStatus !== 'unregistered') {
        const gstVal = formData.GSTNo?.trim();
        if (!gstVal) {
          errors.GSTNo = 'GST No is mandatory for registered parties.';
        }
      }

      const panVal = formData.PANNo?.trim();
      if (!panVal) {
        // Check if PAN can be taken from 15-char GSTIN
        const gstVal = formData.GSTNo?.trim() || '';
        if (gstVal.length !== 15) {
          errors.PANNo = 'PAN No is mandatory.';
        }
      }
    } else if (masterType === 'warehouse') {
      const code = formData.WarehouseCode?.trim();
      if (!code) errors.WarehouseCode = 'Warehouse Code is mandatory.';
      else if (code.length > 8) errors.WarehouseCode = `WarehouseCode exceeds 8 chars (provided ${code.length}).`;

      if (!formData.WarehouseName?.trim()) errors.WarehouseName = 'Warehouse Name is mandatory.';
      else if (formData.WarehouseName.length > 100) errors.WarehouseName = 'WarehouseName max 100 characters.';

      if (!formData.Location && formData.Location !== 0) errors.Location = 'Location is mandatory.';

      if (!formData.Address?.trim()) errors.Address = 'Address is mandatory.';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Deterministic server schema validation
  const handleValidateSchema = async () => {
    if (!validateFormClient()) return;
    setValidatingSchema(true);
    try {
      let res;
      if (masterType === 'item') res = await api.validateItem(formData);
      else if (masterType === 'business_partner') res = await api.validateBusinessPartner(formData);
      else if (masterType === 'warehouse') res = await api.validateWarehouse(formData);

      setSchemaValidationResult(res);
    } catch (err: any) {
      setPostingError(err.response?.data?.message || 'Deterministic schema validation failed');
    } finally {
      setValidatingSchema(false);
    }
  };

  // Document File Handling (PDF & Excel)
  const isExcelFile = (filename: string) => {
    const f = filename.toLowerCase();
    return f.endsWith('.xlsx') || f.endsWith('.xls') || f.endsWith('.csv');
  };

  const handleDocumentFile = (file: File) => {
    const f = file.name.toLowerCase();
    if (!f.endsWith('.pdf') && !f.endsWith('.xlsx') && !f.endsWith('.xls') && !f.endsWith('.csv')) {
      setPdfError('Please select a valid PDF or Excel file (.pdf, .xlsx, .xls, .csv).');
      return;
    }
    setPdfFile(file);
    setPdfError(null);
  };


  // Run PDF & Excel Extraction Pipeline
  const runPdfExtraction = async () => {
    if (!pdfFile) return;
    setExtracting(true);
    setPdfError(null);
    setExtractionStep('Uploading document & verifying MIME type...');

    try {
      setTimeout(() => setExtractionStep('Extracting data across 3 independent engines...'), 500);
      setTimeout(() => setExtractionStep('Normalizing values & verifying extraction consensus...'), 1200);

      const res = await api.uploadDocument(pdfFile, masterType);

      if (!res.success) {
        setPdfError(res.message || 'Extraction failed');
        setExtracting(false);
        setExtractionStep(null);
        return;
      }

      const agreedData = res.data?.data || {};
      const allRecords = res.data?.extracted_records || [];

      setExtractedSummary({
        workflowId: res.data?.workflow_id,
        confidence: res.data?.confidence || 1.0,
        fieldsCount: Object.keys(agreedData).length,
        totalRecords: allRecords.length,
        agreedData,
      });

      // If multi-row records detected: initialize Bulk Studio
      if (allRecords.length > 1) {
        setBulkRecords(allRecords);
        setSelectedBulkRowIndices(new Set(allRecords.map((_: any, idx: number) => idx)));
        try {
          const wf = await api.getWorkflow(res.data.workflow_id);
          setBulkWorkflow(wf);
        } catch (e) {
          // ignore
        }
      } else {
        setBulkRecords([]);
        setBulkWorkflow(null);
      }

      // Auto-populate form fields for active record!
      setFormData((prev) => {
        const merged = { ...prev };
        Object.entries(agreedData).forEach(([k, v]) => {
          if (v !== undefined && v !== null) {
            merged[k] = v;
          }
        });
        return merged;
      });

      setExtractionStep(null);
      setExtracting(false);
    } catch (err: any) {
      setPdfError(err.response?.data?.message || err.message || 'Extraction pipeline encountered an error.');
      setExtracting(false);
      setExtractionStep(null);
    }
  };

  // Bulk Workflow Actions
  const handleBulkConfirmAndPost = async (options: { skipDuplicates: boolean; continueOnError: boolean }) => {
    if (!bulkWorkflow) return;
    setBulkPostingLoading(true);
    setPostingError(null);
    try {
      await api.bulkConfirmWorkflow(bulkWorkflow.workflow_id);
      const res = await api.bulkCreateInSap(bulkWorkflow.workflow_id, {
        indices: Array.from(selectedBulkRowIndices),
        skipDuplicates: options.skipDuplicates,
        continueOnError: options.continueOnError,
      });
      if (res && res.success) {
        setBulkCreationSummary(res.data.summary);
        setIsBulkConfirmOpen(false);
        loadLiveCount();
      } else {
        setPostingError(res?.message || 'Bulk SAP creation failed.');
        setIsBulkConfirmOpen(false);
      }
    } catch (err: any) {
      setPostingError(err.response?.data?.message || err.message || 'Bulk creation failed.');
      setIsBulkConfirmOpen(false);
    } finally {
      setBulkPostingLoading(false);
    }
  };

  const openDefaultsModal = () => {
    setIsDefaultsModalOpen(true);
  };

  const handleApplyBatchDefaults = async (defaults: Record<string, any>) => {
    try {
      if (bulkWorkflow) {
        const res = await api.bulkApplyDefaults(bulkWorkflow.workflow_id, defaults);
        if (res && res.success) {
          setBulkWorkflow(res.data);
          if (res.data.extracted_records) {
            setBulkRecords(res.data.extracted_records);
          }
        }
      } else {
        const updated = bulkRecords.map((rec) => {
          const next = { ...rec };
          Object.entries(defaults).forEach(([k, v]) => {
            if (v !== undefined && v !== '' && (next[k] === undefined || next[k] === null || next[k] === '')) {
              next[k] = v;
            }
          });
          return next;
        });
        setBulkRecords(updated);
      }
      setIsDefaultsModalOpen(false);
    } catch (err: any) {
      setPostingError(err.response?.data?.message || 'Failed to apply defaults.');
    }
  };

  // Direct Bulk Paste Functions
  const handleParsePastedText = () => {
    if (!pastedText.trim()) {
      setParsedPasteRows([]);
      return;
    }
    try {
      setPasteError(null);
      const lines = pastedText.trim().split('\n').map((l) => l.trim()).filter(Boolean);
      if (lines.length < 2) {
        setPasteError('Please paste at least one header row and one data row.');
        return;
      }
      const firstLine = lines[0];
      const delimiter = firstLine.includes('\t') ? '\t' : ',';
      const headers = firstLine.split(delimiter).map((h) => h.trim().replace(/^["']|["']$/g, ''));

      const rows: Record<string, any>[] = [];
      for (let i = 1; i < lines.length; i++) {
        const parts = lines[i].split(delimiter).map((p) => p.trim().replace(/^["']|["']$/g, ''));
        const rowObj: Record<string, any> = {};
        headers.forEach((h, idx) => {
          if (idx < parts.length && parts[idx] !== '') {
            rowObj[h] = parts[idx];
          }
        });
        if (Object.keys(rowObj).length > 0) {
          rows.push(rowObj);
        }
      }
      setParsedPasteRows(rows);
    } catch (err: any) {
      setPasteError('Failed to parse pasted data: ' + err.message);
    }
  };


  const toggleBulkRow = (index: number) => {
    const next = new Set(selectedBulkRowIndices);
    if (next.has(index)) {
      next.delete(index);
    } else {
      next.add(index);
    }
    setSelectedBulkRowIndices(next);
  };

  const selectAllBulkRows = () => {
    setSelectedBulkRowIndices(new Set(bulkRecords.map((_, i) => i)));
  };

  const deselectAllBulkRows = () => {
    setSelectedBulkRowIndices(new Set());
  };

  const getRecordMissingFields = (rec: Record<string, any>, originalIdx?: number): string[] => {
    const effectiveRec =
      originalIdx !== undefined && bulkInlineEdits[originalIdx]
        ? { ...rec, ...bulkInlineEdits[originalIdx] }
        : rec;

    const requiredFields = MANDATORY_MODULE_FIELDS[masterType] || [];
    return requiredFields.filter((field) => {
      const val = effectiveRec[field];

      // Special case for ItemType: if boolean flags are explicitly set
      if (field === 'ItemType' && (effectiveRec.InventoryItem || effectiveRec.SalesItem || effectiveRec.PurchaseItem)) {
        return false;
      }
      // Special case for ItemManagementMethod
      if (field === 'ItemManagementMethod' && (effectiveRec.ManageSerialNumbers || effectiveRec.ManageBatchNumbers)) {
        return false;
      }
      // Special case for GSTNo: unregistered party
      if (field === 'GSTNo') {
        const reg = String(effectiveRec.GSTRegStatus || effectiveRec.RegistrationStatus || '').trim().toLowerCase();
        const raw = String(val || '').trim().toUpperCase();
        if (
          reg === 'unregistered' ||
          reg === 'urp' ||
          reg === 'no' ||
          reg === 'composition' ||
          raw === 'UNREGISTERED' ||
          raw === 'URP' ||
          raw === 'N/A'
        ) {
          return false;
        }
      }
      // Special case for PANNo: present in 15-char GSTIN
      if (field === 'PANNo') {
        const gst = String(effectiveRec.GSTNo || effectiveRec.FederalTaxID || '').trim().toUpperCase();
        if (gst.length === 15 && /^\d{2}[A-Z0-9]{10}/.test(gst)) {
          return false;
        }
      }

      return val === undefined || val === null || String(val).trim() === '';
    });
  };

  const isRecordReady = (rec: Record<string, any>, originalIdx?: number): boolean => {
    return getRecordMissingFields(rec, originalIdx).length === 0;
  };

  const bulkValidationSummary = bulkRecords.reduce(
    (acc, rec, idx) => {
      const isReady = isRecordReady(rec, idx);
      if (isReady) acc.readyCount++;
      else acc.needsDataCount++;
      return acc;
    },
    { readyCount: 0, needsDataCount: 0 }
  );

  const selectedReadyCount = Array.from(selectedBulkRowIndices).filter((idx) => {
    const rec = bulkRecords[idx];
    return rec ? isRecordReady(rec, idx) : false;
  }).length;
  const selectedNeedsDataCount = selectedBulkRowIndices.size - selectedReadyCount;

  const filteredBulkRecords = bulkRecords
    .map((rec, idx) => {
      const missing = getRecordMissingFields(rec, idx);
      const isReady = missing.length === 0;
      return { rec, originalIdx: idx, missing, isReady };
    })
    .filter(({ rec, isReady }) => {
      if (bulkStatusFilter === 'READY' && !isReady) return false;
      if (bulkStatusFilter === 'NEEDS_DATA' && isReady) return false;

      if (!bulkSearchFilter.trim()) return true;
      const q = bulkSearchFilter.toLowerCase();
      const code = String(rec.ItemCode || rec.CardCode || rec.WarehouseCode || '').toLowerCase();
      const name = String(rec.ItemName || rec.CardName || rec.WarehouseName || '').toLowerCase();
      return code.includes(q) || name.includes(q);
    });

  // Standard full fields definitions by master data type for MasterDataModule
  const standardBulkColumns = ALL_MODULE_FIELDS[masterType] || [];
  const extractedBulkKeys = new Set<string>();
  bulkRecords.forEach((r) => {
    if (r) Object.keys(r).forEach((k) => extractedBulkKeys.add(k));
  });
  const allBulkColumns = Array.from(new Set([...standardBulkColumns, ...extractedBulkKeys]));

  const handleToggleExpandBulkRow = (idx: number) => {
    if (expandedBulkRowIndex === idx) {
      setExpandedBulkRowIndex(null);
    } else {
      setExpandedBulkRowIndex(idx);
      const rec = bulkRecords[idx] || {};
      const currentDraft = bulkRowDrafts[idx] || {};
      setBulkRowDrafts((prev) => ({ ...prev, [idx]: { ...rec, ...currentDraft } }));
    }
  };

  const handleBulkRowDraftChange = (idx: number, field: string, value: any) => {
    setBulkRowDrafts((prev) => ({
      ...prev,
      [idx]: {
        ...(prev[idx] || {}),
        [field]: value,
      },
    }));
  };

  const handleSaveBulkRowDraft = async (idx: number) => {
    const draft = bulkRowDrafts[idx];
    if (!draft) return;
    setIsSavingBulkRow(true);
    try {
      const updated = [...bulkRecords];
      updated[idx] = { ...updated[idx], ...draft };
      setBulkRecords(updated);
      if (bulkWorkflow) {
        const res = await api.updateWorkflowRecord(bulkWorkflow.workflow_id, {
          index: idx,
          updates: draft,
        });
        if (res && res.data) {
          setBulkWorkflow(res.data);
          if (res.data.extracted_records) {
            setBulkRecords(res.data.extracted_records);
          }
        }
      }
      setExpandedBulkRowIndex(null);
    } catch (e) {
      console.error('Failed to save bulk row draft', e);
    } finally {
      setIsSavingBulkRow(false);
    }
  };

  const handleBulkInlineCellChange = (idx: number, field: string, value: any) => {
    setBulkInlineEdits((prev) => ({
      ...prev,
      [idx]: {
        ...(prev[idx] || {}),
        [field]: value,
      },
    }));
  };

  const handleSaveAllBulkTableEdits = async () => {
    setIsSavingBulkTableEdits(true);
    try {
      const updated = bulkRecords.map((rec, i) => {
        if (bulkInlineEdits[i]) {
          return { ...rec, ...bulkInlineEdits[i] };
        }
        return rec;
      });
      setBulkRecords(updated);
      if (bulkWorkflow) {
        const res = await api.updateWorkflowRecord(bulkWorkflow.workflow_id, {
          records: updated,
        });
        if (res && res.data) {
          setBulkWorkflow(res.data);
          if (res.data.extracted_records) {
            setBulkRecords(res.data.extracted_records);
          }
        }
      }
      setBulkInlineEdits({});
    } catch (e) {
      console.error('Failed to save table edits', e);
    } finally {
      setIsSavingBulkTableEdits(false);
    }
  };

  const handleExecuteDirectBulkPost = async () => {
    if (parsedPasteRows.length === 0) return;
    setPostingLoading(true);
    setPostingError(null);
    try {
      const res = await api.bulkCreateDirect(masterType, parsedPasteRows, {
        skipDuplicates: true,
        continueOnError: true,
      });
      if (res && res.success) {
        setBulkCreationSummary(res.data.summary);
        setIsDirectBulkConfirmOpen(false);
        loadLiveCount();
      } else {
        setPostingError(res?.message || 'Bulk creation failed.');
        setIsDirectBulkConfirmOpen(false);
      }
    } catch (err: any) {
      setPostingError(err.response?.data?.message || err.message || 'Direct bulk creation failed.');
      setIsDirectBulkConfirmOpen(false);
    } finally {
      setPostingLoading(false);
    }
  };

  // Confirm and Post directly to SAP
  const handleDirectPost = async () => {
    if (!validateFormClient()) return;
    setIsConfirmModalOpen(true);
  };

  const executeSapPost = async () => {
    setPostingLoading(true);
    setPostingError(null);

    // Prepare clean payload
    const payload: Record<string, any> = { ...formData };
    if (masterType === 'item') {
      payload.ItemCode = String(payload.ItemCode || '').trim().toUpperCase();
      payload.ItemName = String(payload.ItemName || '').trim();
      if (payload.ItemsGroupCode) payload.ItemsGroupCode = parseInt(payload.ItemsGroupCode, 10);
      if (payload.SalesUnitWeight) payload.SalesUnitWeight = parseFloat(payload.SalesUnitWeight);
    } else if (masterType === 'business_partner') {
      payload.CardCode = String(payload.CardCode || '').trim().toUpperCase();
      payload.CardName = String(payload.CardName || '').trim();
      if (payload.GroupCode) payload.GroupCode = parseInt(payload.GroupCode, 10);
    } else if (masterType === 'warehouse') {
      payload.WarehouseCode = String(payload.WarehouseCode || '').trim().toUpperCase();
      payload.WarehouseName = String(payload.WarehouseName || '').trim();
      if (payload.Location) payload.Location = parseInt(payload.Location, 10);
    }

    try {
      let res;
      if (masterType === 'item') {
        res = await api.createItemInSap(undefined, payload);
      } else if (masterType === 'business_partner') {
        res = await api.createBusinessPartnerInSap(undefined, payload);
      } else if (masterType === 'warehouse') {
        res = await api.createWarehouseInSap(undefined, payload);
      }

      if (res && res.success) {
        setCreationSuccess(res.data);
        setIsConfirmModalOpen(false);
        loadLiveCount();
      } else {
        const errorList = res?.errors?.join('; ') || res?.message || 'SAP creation failed.';
        setPostingError(errorList);
        setIsConfirmModalOpen(false);
      }
    } catch (err: any) {
      const msg = err.response?.data?.message || err.response?.data?.errors?.join('; ') || err.message;
      setPostingError(msg);
      setIsConfirmModalOpen(false);
    } finally {
      setPostingLoading(false);
    }
  };

  // Live Records Explorer fetcher
  const loadRecords = async () => {
    setLoadingRecords(true);
    try {
      const entityName =
        masterType === 'item' ? 'Items' : masterType === 'business_partner' ? 'BusinessPartners' : 'Warehouses';
      const data = await api.getSapRecords(entityName, 20, 0, searchQuery);
      setRecords(data.records || []);
      setRecordsTotal(data.total || 0);
    } catch (err) {
      console.error('Failed to load SAP records', err);
    } finally {
      setLoadingRecords(false);
    }
  };

  useEffect(() => {
    if (activeSubTab === 'records') {
      loadRecords();
    }
  }, [activeSubTab, searchQuery]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Module Header */}
      <div
        className="glass-panel"
        style={{
          padding: '24px 28px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 20,
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.7) 100%)',
          borderLeft: '4px solid #3B82F6',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div
            style={{
              width: 50,
              height: 50,
              borderRadius: 'var(--radius-md)',
              background: 'rgba(59, 130, 246, 0.15)',
              border: '1px solid rgba(59, 130, 246, 0.35)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            {masterType === 'item' && <Package size={26} color="#60A5FA" />}
            {masterType === 'business_partner' && <Users size={26} color="#A78BFA" />}
            {masterType === 'warehouse' && <Warehouse size={26} color="#34D399" />}
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
              <h2 style={{ fontSize: 22, fontWeight: 700, letterSpacing: -0.3 }}>{title}</h2>
            </div>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{description}</p>
          </div>
        </div>

        {/* Live Stat & Tab Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {liveCount !== null && (
            <div
              style={{
                textAlign: 'right',
                paddingRight: 16,
                borderRight: '1px solid var(--border-subtle)',
              }}
            >
              <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', textTransform: 'uppercase' }}>
                Active in SAP
              </span>
              <strong style={{ fontSize: 20, color: '#F8FAFC' }}>{liveCount} Records</strong>
            </div>
          )}

          {/* Action Tabs */}
          <div
            style={{
              display: 'flex',
              background: 'rgba(15, 23, 42, 0.7)',
              padding: 4,
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              gap: 4,
            }}
          >
            <button
              onClick={() => setActiveSubTab('form')}
              className="btn"
              style={{
                fontSize: 13,
                padding: '8px 14px',
                background: activeSubTab === 'form' ? 'rgba(59, 130, 246, 0.3)' : 'transparent',
                color: activeSubTab === 'form' ? '#93C5FD' : 'var(--text-secondary)',
                border: activeSubTab === 'form' ? '1px solid rgba(59, 130, 246, 0.5)' : '1px solid transparent',
              }}
            >
              Direct Posting & SAP Post
            </button>
            <button
              onClick={() => setActiveSubTab('pdf')}
              className="btn"
              style={{
                fontSize: 13,
                padding: '8px 14px',
                background: activeSubTab === 'pdf' ? 'rgba(59, 130, 246, 0.3)' : 'transparent',
                color: activeSubTab === 'pdf' ? '#93C5FD' : 'var(--text-secondary)',
                border: activeSubTab === 'pdf' ? '1px solid rgba(59, 130, 246, 0.5)' : '1px solid transparent',
              }}
            >
              Bulk Data & Spreadsheet Upload
            </button>
            <button
              onClick={() => setActiveSubTab('records')}
              className="btn"
              style={{
                fontSize: 13,
                padding: '8px 14px',
                background: activeSubTab === 'records' ? 'rgba(59, 130, 246, 0.3)' : 'transparent',
                color: activeSubTab === 'records' ? '#93C5FD' : 'var(--text-secondary)',
                border: activeSubTab === 'records' ? '1px solid rgba(59, 130, 246, 0.5)' : '1px solid transparent',
              }}
            >
              Live SAP Records
            </button>
          </div>
        </div>
      </div>

      {/* Global Posting Error Alert */}
      {postingError && (
        <div
          style={{
            padding: 16,
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            borderRadius: 'var(--radius-md)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 12,
            color: '#F87171',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <AlertCircle size={20} />
            <div style={{ fontSize: 13.5 }}>{postingError}</div>
          </div>
          <button
            onClick={() => setPostingError(null)}
            className="btn btn-secondary"
            style={{ fontSize: 12, padding: '4px 10px' }}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* SUCCESS SCREEN */}
      {creationSuccess && (
        <div
          className="glass-panel"
          style={{
            padding: 36,
            textAlign: 'center',
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(15, 23, 42, 0.85) 100%)',
            border: '1px solid rgba(16, 185, 129, 0.4)',
          }}
        >
          <div
            style={{
              width: 64,
              height: 64,
              borderRadius: '50%',
              background: 'rgba(16, 185, 129, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px',
              boxShadow: '0 0 24px rgba(16, 185, 129, 0.3)',
            }}
          >
            <CheckCircle size={36} color="#34D399" />
          </div>

          <h3 style={{ fontSize: 22, fontWeight: 700, color: '#34D399', marginBottom: 8 }}>
            Record Created Successfully in SAP!
          </h3>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 20 }}>
            Dispatched authoritative POST to <code>{serviceLayerEndpoint}</code> via SAP Service Layer with zero direct SQL writes.
          </p>

          <div
            style={{
              display: 'inline-flex',
              gap: 24,
              background: '#F8FAFC',
              padding: '16px 28px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid #E2E8F0',
              marginBottom: 24,
              textAlign: 'left',
              flexWrap: 'wrap',
            }}
          >
            <div>
              <span style={{ fontSize: 11, color: '#64748B', display: 'block' }}>SAP PRIMARY KEY</span>
              <strong style={{ fontSize: 16, color: '#2563EB' }}>{creationSuccess.sap_object_id}</strong>
            </div>
            <div>
              <span style={{ fontSize: 11, color: '#64748B', display: 'block' }}>TARGET ENTITY</span>
              <strong style={{ fontSize: 16, textTransform: 'capitalize', color: '#0F172A' }}>
                {title}
              </strong>
            </div>
            <div>
              <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block' }}>HTTP STATUS</span>
              <strong style={{ fontSize: 16, color: '#34D399' }}>201 Created</strong>
            </div>
            <div>
              <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block' }}>AUDIT STATUS</span>
              <strong style={{ fontSize: 16, color: '#34D399' }}>Logged & Verified</strong>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'center', gap: 12 }}>
            <button onClick={resetForm} className="btn btn-primary" style={{ padding: '10px 24px' }}>
              Create Another {title} <ArrowRight size={15} />
            </button>
            <button
              onClick={() => setActiveSubTab('records')}
              className="btn btn-secondary"
              style={{ padding: '10px 20px' }}
            >
              <Database size={15} /> View in Live SAP Catalog
            </button>
            {onNavigateToAudit && (
              <button onClick={onNavigateToAudit} className="btn btn-secondary" style={{ padding: '10px 20px' }}>
                Inspect Audit Log
              </button>
            )}
          </div>
        </div>
      )}

      {/* BULK CREATION AUDIT RESULTS SCREEN */}
      {bulkCreationSummary && (
        <BulkResultsViewer
          summary={bulkCreationSummary}
          masterType={masterType}
          onReset={() => {
            setBulkCreationSummary(null);
            setBulkWorkflow(null);
            setBulkRecords([]);
            setParsedPasteRows([]);
            setPastedText('');
            setPdfFile(null);
            setExtractedSummary(null);
          }}
        />
      )}

      {/* SUB-TAB 1: Direct Posting & SAP Post */}
      {!creationSuccess && !bulkCreationSummary && activeSubTab === 'form' && (
        <div className="grid-2" style={{ gridTemplateColumns: 'minmax(420px, 1.4fr) minmax(320px, 1fr)', gap: 24 }}>
          {/* Main Form Column */}
          <div className="glass-panel" style={{ padding: 28 }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                marginBottom: 20,
                borderBottom: '1px solid var(--border-subtle)',
                paddingBottom: 16,
                flexWrap: 'wrap',
                gap: 12,
              }}
            >
              <div>
                <h3 style={{ fontSize: 17, fontWeight: 700 }}>{title} Posting</h3>
                <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                  {entryMode === 'single'
                    ? 'Enter fields manually with strict SAP validation'
                    : 'Paste CSV or tabular data for multi-record batch creation'}
                </p>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                {/* Single Form vs Bulk Paste Toggle */}
                <div
                  style={{
                    display: 'flex',
                    background: 'rgba(15, 23, 42, 0.7)',
                    padding: 3,
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                    gap: 3,
                  }}
                >
                  <button
                    type="button"
                    onClick={() => setEntryMode('single')}
                    className="btn"
                    style={{
                      fontSize: 12,
                      padding: '5px 12px',
                      background: entryMode === 'single' ? 'rgba(59, 130, 246, 0.3)' : 'transparent',
                      color: entryMode === 'single' ? '#93C5FD' : 'var(--text-secondary)',
                      border: entryMode === 'single' ? '1px solid rgba(59, 130, 246, 0.5)' : '1px solid transparent',
                    }}
                  >
                    Single Record Form
                  </button>
                  <button
                    type="button"
                    onClick={() => setEntryMode('bulk_paste')}
                    className="btn"
                    style={{
                      fontSize: 12,
                      padding: '5px 12px',
                      background: entryMode === 'bulk_paste' ? 'rgba(59, 130, 246, 0.3)' : 'transparent',
                      color: entryMode === 'bulk_paste' ? '#93C5FD' : 'var(--text-secondary)',
                      border: entryMode === 'bulk_paste' ? '1px solid rgba(59, 130, 246, 0.5)' : '1px solid transparent',
                    }}
                  >
                    <ClipboardList size={13} style={{ marginRight: 4 }} />
                    Bulk Paste (CSV)
                  </button>
                </div>

                <button onClick={resetForm} className="btn btn-secondary" style={{ fontSize: 12, padding: '6px 12px' }}>
                  <RotateCcw size={13} /> Reset
                </button>
              </div>
            </div>

            {/* Single Record Mode */}
            {entryMode === 'single' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
                {/* ITEM MASTER FIELDS */}
                {masterType === 'item' && (
                  <>
                    <div className="grid-2" style={{ gap: 16 }}>
                      <div>
                        <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span>
                            Item Code <span style={{ color: '#EF4444' }}>*</span>
                          </span>
                          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>Max 50 chars</span>
                        </label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. ITM-10024"
                          value={formData.ItemCode || ''}
                          onChange={(e) => handleInputChange('ItemCode', e.target.value.toUpperCase())}
                          style={{
                            borderColor: formErrors.ItemCode ? '#EF4444' : undefined,
                            fontWeight: 600,
                          }}
                        />
                        {formErrors.ItemCode && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.ItemCode}</p>
                        )}
                      </div>

                      <div>
                        <label className="form-label">
                          Item Name / Description <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. Stainless Steel Hex Bolt M8x40"
                          value={formData.ItemName || ''}
                          onChange={(e) => handleInputChange('ItemName', e.target.value)}
                          style={{ borderColor: formErrors.ItemName ? '#EF4444' : undefined }}
                        />
                        {formErrors.ItemName && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.ItemName}</p>
                        )}
                      </div>
                    </div>

                    <div className="grid-2" style={{ gap: 16 }}>
                      <div>
                        <label className="form-label">
                          Item Group Code <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <input
                          type="number"
                          className="form-input"
                          placeholder="e.g. 100"
                          value={formData.ItemsGroupCode ?? ''}
                          onChange={(e) => handleInputChange('ItemsGroupCode', e.target.value === '' ? '' : parseInt(e.target.value, 10))}
                          style={{ borderColor: formErrors.ItemsGroupCode ? '#EF4444' : undefined }}
                        />
                        {formErrors.ItemsGroupCode && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.ItemsGroupCode}</p>
                        )}
                      </div>

                      <div>
                        <label className="form-label">
                          Inventory Unit of Measure (UoM) <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. PCS, BOX, KG, MTR"
                          value={formData.InventoryUOM || ''}
                          onChange={(e) => handleInputChange('InventoryUOM', e.target.value.toUpperCase())}
                          style={{ borderColor: formErrors.InventoryUOM ? '#EF4444' : undefined }}
                        />
                        {formErrors.InventoryUOM && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.InventoryUOM}</p>
                        )}
                      </div>
                    </div>

                    <div className="grid-2" style={{ gap: 16 }}>
                      <div>
                        <label className="form-label">
                          Item Type (Inventory/Sales/Purchase) <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. Inventory/Sales/Purchase"
                          value={formData.ItemType || ''}
                          onChange={(e) => handleInputChange('ItemType', e.target.value)}
                          style={{ borderColor: formErrors.ItemType ? '#EF4444' : undefined }}
                        />
                        {formErrors.ItemType && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.ItemType}</p>
                        )}
                      </div>

                      <div>
                        <label className="form-label">
                          Tax Rate (%) <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. 18% or 18"
                          value={formData.TaxRate || ''}
                          onChange={(e) => handleInputChange('TaxRate', e.target.value)}
                          style={{ borderColor: formErrors.TaxRate ? '#EF4444' : undefined }}
                        />
                        {formErrors.TaxRate && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.TaxRate}</p>
                        )}
                      </div>
                    </div>

                    <div className="grid-2" style={{ gap: 16 }}>
                      <div>
                        <label className="form-label">
                          Item Management Method <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <select
                          className="form-input"
                          value={formData.ItemManagementMethod || ''}
                          onChange={(e) => handleInputChange('ItemManagementMethod', e.target.value)}
                          style={{ borderColor: formErrors.ItemManagementMethod ? '#EF4444' : undefined }}
                        >
                          <option value="">Select Management Method...</option>
                          <option value="None">None (Standard Stock)</option>
                          <option value="Batch">Batch / Lot Managed</option>
                          <option value="Serial">Serial Number Managed</option>
                        </select>
                        {formErrors.ItemManagementMethod && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.ItemManagementMethod}</p>
                        )}
                      </div>

                      <div>
                        <label className="form-label">
                          Item Category <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <select
                          className="form-input"
                          value={formData.ItemCategory || ''}
                          onChange={(e) => handleInputChange('ItemCategory', e.target.value)}
                          style={{ borderColor: formErrors.ItemCategory ? '#EF4444' : undefined }}
                        >
                          <option value="">Select Item Category...</option>
                          <option value="Item">Item (Physical Good)</option>
                          <option value="Service">Service (Labor/Fee)</option>
                        </select>
                        {formErrors.ItemCategory && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.ItemCategory}</p>
                        )}
                      </div>
                    </div>

                    <div className="grid-3" style={{ gap: 16 }}>
                      <div>
                        <label className="form-label">
                          Material Type <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <select
                          className="form-input"
                          value={formData.MaterialType || ''}
                          onChange={(e) => handleInputChange('MaterialType', e.target.value)}
                          style={{ borderColor: formErrors.MaterialType ? '#EF4444' : undefined }}
                        >
                          <option value="">Select Material Type...</option>
                          <option value="RM">Raw Material (RM)</option>
                          <option value="FG">Finished Goods (FG)</option>
                          <option value="Capital Goods">Capital Goods</option>
                        </select>
                        {formErrors.MaterialType && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.MaterialType}</p>
                        )}
                      </div>

                      <div>
                        <label className="form-label">
                          HSN / SAC Code <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. 73181500"
                          value={formData.HSN || ''}
                          onChange={(e) => handleInputChange('HSN', e.target.value)}
                          style={{ borderColor: formErrors.HSN ? '#EF4444' : undefined }}
                        />
                        {formErrors.HSN && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.HSN}</p>
                        )}
                      </div>

                      <div>
                        <label className="form-label">
                          Tax Category <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. Taxable, Exempted"
                          value={formData.TaxCategory || ''}
                          onChange={(e) => handleInputChange('TaxCategory', e.target.value)}
                          style={{ borderColor: formErrors.TaxCategory ? '#EF4444' : undefined }}
                        />
                        {formErrors.TaxCategory && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.TaxCategory}</p>
                        )}
                      </div>
                    </div>

                    {/* Operational Item Flags */}
                    <div
                      style={{
                        background: 'rgba(15, 23, 42, 0.6)',
                        padding: 14,
                        borderRadius: 'var(--radius-md)',
                        border: '1px solid var(--border-subtle)',
                      }}
                    >
                      <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: 10 }}>
                        SAP Item Classification Flags
                      </span>
                      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
                        <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={Boolean(formData.InventoryItem)}
                            onChange={(e) => handleInputChange('InventoryItem', e.target.checked)}
                            style={{ width: 16, height: 16, accentColor: '#3B82F6' }}
                          />
                          Inventory Item
                        </label>

                        <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={Boolean(formData.SalesItem)}
                            onChange={(e) => handleInputChange('SalesItem', e.target.checked)}
                            style={{ width: 16, height: 16, accentColor: '#3B82F6' }}
                          />
                          Sales Item
                        </label>

                        <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer' }}>
                          <input
                            type="checkbox"
                            checked={Boolean(formData.PurchaseItem)}
                            onChange={(e) => handleInputChange('PurchaseItem', e.target.checked)}
                            style={{ width: 16, height: 16, accentColor: '#3B82F6' }}
                          />
                          Purchase Item
                        </label>
                      </div>
                    </div>

                    {/* Secondary Fields */}
                    <div className="grid-2" style={{ gap: 16 }}>
                      <div>
                        <label className="form-label">Sales Unit Weight (Kg)</label>
                        <input
                          type="number"
                          step="0.001"
                          className="form-input"
                          placeholder="0.250"
                          value={formData.SalesUnitWeight || ''}
                          onChange={(e) => handleInputChange('SalesUnitWeight', e.target.value)}
                        />
                      </div>
                      <div>
                        <label className="form-label">Barcode (EAN / UPC)</label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. 8904561237890"
                          value={formData.BarCode || ''}
                          onChange={(e) => handleInputChange('BarCode', e.target.value)}
                        />
                      </div>
                    </div>
                  </>
                )}

                {/* BUSINESS PARTNER FIELDS */}
                {masterType === 'business_partner' && (
                  <>
                    <div className="grid-2" style={{ gap: 16 }}>
                      <div>
                        <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span>
                            Customer / Vendor Code <span style={{ color: '#EF4444' }}>*</span>
                          </span>
                          <span
                            style={{
                              fontSize: 11,
                              color: (formData.CardCode?.length || 0) > 15 ? '#EF4444' : '#60A5FA',
                              fontWeight: 600,
                            }}
                          >
                            {formData.CardCode?.length || 0} / 15 chars max
                          </span>
                        </label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. V10024 or C20098"
                          maxLength={15}
                          value={formData.CardCode || ''}
                          onChange={(e) => handleInputChange('CardCode', e.target.value.toUpperCase())}
                          style={{
                            borderColor: formErrors.CardCode ? '#EF4444' : undefined,
                            fontWeight: 600,
                          }}
                        />
                        {formErrors.CardCode && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.CardCode}</p>
                        )}
                      </div>

                      <div>
                        <label className="form-label">
                          Business Partner Name <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. Apex Precision Components Ltd"
                          value={formData.CardName || ''}
                          onChange={(e) => handleInputChange('CardName', e.target.value)}
                          style={{ borderColor: formErrors.CardName ? '#EF4444' : undefined }}
                        />
                        {formErrors.CardName && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.CardName}</p>
                        )}
                      </div>
                    </div>

                    {/* CardType Selector */}
                    <div>
                      <label className="form-label">
                        Business Partner Type <span style={{ color: '#EF4444' }}>*</span>
                      </label>
                      <div style={{ display: 'flex', gap: 10 }}>
                        {[
                          { id: 'cSupplier', label: 'Supplier / Vendor' },
                          { id: 'cCustomer', label: 'Customer' },
                          { id: 'cLid', label: 'Lead' },
                        ].map((t) => (
                          <button
                            key={t.id}
                            type="button"
                            onClick={() => handleInputChange('CardType', t.id)}
                            className={`btn ${formData.CardType === t.id ? 'btn-primary' : 'btn-secondary'}`}
                            style={{ flex: 1, padding: '8px 12px', fontSize: 12.5 }}
                          >
                            {t.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Address (Mandatory) */}
                    <div>
                      <label className="form-label">
                        Registered Address / Facility <span style={{ color: '#EF4444' }}>*</span>
                      </label>
                      <input
                        type="text"
                        className="form-input"
                        placeholder="e.g. Plot 42, Industrial Area Phase 2, San Jose, CA"
                        value={formData.Address || ''}
                        onChange={(e) => handleInputChange('Address', e.target.value)}
                        style={{ borderColor: formErrors.Address ? '#EF4444' : undefined }}
                      />
                      {formErrors.Address && (
                        <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.Address}</p>
                      )}
                    </div>

                    {/* Tax Details, Payment Terms, Currency, Control Account */}
                    <div className="grid-2" style={{ gap: 16 }}>
                      <div>
                        <label className="form-label">
                          Tax Details / Structure <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. GST 18% or IGST 18%"
                          value={formData.TaxDetails || ''}
                          onChange={(e) => handleInputChange('TaxDetails', e.target.value)}
                          style={{ borderColor: formErrors.TaxDetails ? '#EF4444' : undefined }}
                        />
                        {formErrors.TaxDetails && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.TaxDetails}</p>
                        )}
                      </div>

                      <div>
                        <label className="form-label">
                          Payment Terms <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. Net 30, Cash, Immediate"
                          value={formData.PaymentTerms || ''}
                          onChange={(e) => handleInputChange('PaymentTerms', e.target.value)}
                          style={{ borderColor: formErrors.PaymentTerms ? '#EF4444' : undefined }}
                        />
                        {formErrors.PaymentTerms && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.PaymentTerms}</p>
                        )}
                      </div>
                    </div>

                    <div className="grid-2" style={{ gap: 16 }}>
                      <div>
                        <label className="form-label">
                          Default Currency <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <input
                          type="text"
                          className="form-input"
                          maxLength={3}
                          placeholder="INR, USD, EUR"
                          value={formData.Currency || ''}
                          onChange={(e) => handleInputChange('Currency', e.target.value.toUpperCase())}
                          style={{ borderColor: formErrors.Currency ? '#EF4444' : undefined }}
                        />
                        {formErrors.Currency && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.Currency}</p>
                        )}
                      </div>

                      <div>
                        <label className="form-label">
                          Control Account (GL Reconciliation) <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. 211000 (Accounts Payable/Receivable)"
                          value={formData.ControlAccount || ''}
                          onChange={(e) => handleInputChange('ControlAccount', e.target.value)}
                          style={{ borderColor: formErrors.ControlAccount ? '#EF4444' : undefined }}
                        />
                        {formErrors.ControlAccount && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.ControlAccount}</p>
                        )}
                      </div>
                    </div>

                    {/* GST No if Registered and PAN No */}
                    <div className="grid-3" style={{ gap: 16 }}>
                      <div>
                        <label className="form-label">GST Registration Status</label>
                        <select
                          className="form-input"
                          value={formData.GSTRegStatus || ''}
                          onChange={(e) => handleInputChange('GSTRegStatus', e.target.value)}
                        >
                          <option value="">Select Status...</option>
                          <option value="Registered">Registered (Regular/GSTIN)</option>
                          <option value="Unregistered">Unregistered (URP)</option>
                        </select>
                      </div>

                      <div>
                        <label className="form-label">
                          GST No {formData.GSTRegStatus !== 'Unregistered' && <span style={{ color: '#EF4444' }}>*</span>}
                        </label>
                        <input
                          type="text"
                          className="form-input"
                          maxLength={15}
                          placeholder="e.g. 27AABCU9603R1ZM"
                          value={formData.GSTNo || ''}
                          onChange={(e) => {
                            const v = e.target.value.toUpperCase();
                            handleInputChange('GSTNo', v);
                            // Auto-derive PAN if 15 chars GSTIN entered
                            if (v.length === 15 && !formData.PANNo) {
                              handleInputChange('PANNo', v.substring(2, 12));
                            }
                          }}
                          style={{ borderColor: formErrors.GSTNo ? '#EF4444' : undefined }}
                        />
                        {formErrors.GSTNo && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.GSTNo}</p>
                        )}
                      </div>

                      <div>
                        <label className="form-label">
                          PAN No (10 Chars) <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <input
                          type="text"
                          className="form-input"
                          maxLength={10}
                          placeholder="e.g. AABCU9603R"
                          value={formData.PANNo || ''}
                          onChange={(e) => handleInputChange('PANNo', e.target.value.toUpperCase())}
                          style={{ borderColor: formErrors.PANNo ? '#EF4444' : undefined }}
                        />
                        {formErrors.PANNo && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.PANNo}</p>
                        )}
                      </div>
                    </div>

                    <div className="grid-2" style={{ gap: 16 }}>
                      <div>
                        <label className="form-label">Email Address</label>
                        <input
                          type="email"
                          className="form-input"
                          placeholder="e.g. billing@company.com"
                          value={formData.EmailAddress || ''}
                          onChange={(e) => handleInputChange('EmailAddress', e.target.value)}
                        />
                      </div>

                      <div>
                        <label className="form-label">Telephone / Phone 1</label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="+1-800-555-0199"
                          value={formData.Phone1 || ''}
                          onChange={(e) => handleInputChange('Phone1', e.target.value)}
                        />
                      </div>
                    </div>
                  </>
                )}

                {/* WAREHOUSE MASTER FIELDS */}
                {masterType === 'warehouse' && (
                  <>
                    <div className="grid-2" style={{ gap: 16 }}>
                      <div>
                        <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span>
                            Warehouse Code <span style={{ color: '#EF4444' }}>*</span>
                          </span>
                          <span
                            style={{
                              fontSize: 11,
                              color: (formData.WarehouseCode?.length || 0) > 8 ? '#EF4444' : '#34D399',
                              fontWeight: 600,
                            }}
                          >
                            {formData.WarehouseCode?.length || 0} / 8 chars max
                          </span>
                        </label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. WH01, DEPOT02"
                          maxLength={8}
                          value={formData.WarehouseCode || ''}
                          onChange={(e) => handleInputChange('WarehouseCode', e.target.value.toUpperCase())}
                          style={{
                            borderColor: formErrors.WarehouseCode ? '#EF4444' : undefined,
                            fontWeight: 600,
                          }}
                        />
                        {formErrors.WarehouseCode && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.WarehouseCode}</p>
                        )}
                      </div>

                      <div>
                        <label className="form-label">
                          Warehouse Name <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. Central Distribution Center"
                          value={formData.WarehouseName || ''}
                          onChange={(e) => handleInputChange('WarehouseName', e.target.value)}
                          style={{ borderColor: formErrors.WarehouseName ? '#EF4444' : undefined }}
                        />
                        {formErrors.WarehouseName && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.WarehouseName}</p>
                        )}
                      </div>
                    </div>

                    <div className="grid-2" style={{ gap: 16 }}>
                      <div>
                        <label className="form-label">
                          Location Code <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <input
                          type="number"
                          className="form-input"
                          placeholder="e.g. 1"
                          value={formData.Location ?? ''}
                          onChange={(e) => handleInputChange('Location', e.target.value === '' ? '' : parseInt(e.target.value, 10))}
                          style={{ borderColor: formErrors.Location ? '#EF4444' : undefined }}
                        />
                        {formErrors.Location && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.Location}</p>
                        )}
                      </div>

                      <div>
                        <label className="form-label">
                          Warehouse Address <span style={{ color: '#EF4444' }}>*</span>
                        </label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. 100 Logistics Way, Industrial Park"
                          value={formData.Address || ''}
                          onChange={(e) => handleInputChange('Address', e.target.value)}
                          style={{ borderColor: formErrors.Address ? '#EF4444' : undefined }}
                        />
                        {formErrors.Address && (
                          <p style={{ fontSize: 11.5, color: '#EF4444', marginTop: 4 }}>{formErrors.Address}</p>
                        )}
                      </div>
                    </div>

                    <div className="grid-2" style={{ gap: 16 }}>
                      <div>
                        <label className="form-label">Warehouse Type</label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. Standard, Bonded, Quarantine"
                          value={formData.WarehouseType || ''}
                          onChange={(e) => handleInputChange('WarehouseType', e.target.value)}
                        />
                      </div>
                      <div>
                        <label className="form-label">City</label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="Seattle"
                          value={formData.City || ''}
                          onChange={(e) => handleInputChange('City', e.target.value)}
                        />
                      </div>
                    </div>

                    {/* Toggles */}
                    <div style={{ display: 'flex', gap: 24, padding: '8px 0' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={formData.BinActivat === true}
                          onChange={(e) => handleInputChange('BinActivat', e.target.checked)}
                          style={{ width: 16, height: 16, accentColor: '#3B82F6' }}
                        />
                        Enable Bin Locations
                      </label>

                      <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={formData.Inactive === true}
                          onChange={(e) => handleInputChange('Inactive', e.target.checked)}
                          style={{ width: 16, height: 16, accentColor: '#EF4444' }}
                        />
                        Inactive Warehouse
                      </label>
                    </div>
                  </>
                )}

                {/* Schema Validation Feedback */}
                {schemaValidationResult && (
                  <div
                    style={{
                      padding: 14,
                      borderRadius: 'var(--radius-md)',
                      background: schemaValidationResult.valid ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                      border: `1px solid ${schemaValidationResult.valid ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                    }}
                  >
                    {schemaValidationResult.valid ? (
                      <CheckCircle size={18} color="#34D399" />
                    ) : (
                      <AlertCircle size={18} color="#F87171" />
                    )}
                    <span style={{ fontSize: 13, color: schemaValidationResult.valid ? '#34D399' : '#F87171' }}>
                      {schemaValidationResult.message}
                    </span>
                  </div>
                )}

                {/* ACTION BUTTONS */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    marginTop: 10,
                    paddingTop: 16,
                    borderTop: '1px solid var(--border-subtle)',
                  }}
                >
                  <button
                    onClick={handleDirectPost}
                    className="btn btn-primary"
                    style={{ padding: '12px 24px', fontSize: 14, flex: 1 }}
                  >
                    <Send size={16} /> Post {title} to SAP
                  </button>

                  <button
                    type="button"
                    onClick={handleValidateSchema}
                    disabled={validatingSchema}
                    className="btn btn-secondary"
                    style={{ padding: '12px 18px', fontSize: 13 }}
                  >
                    <ShieldCheck size={16} />
                    {validatingSchema ? 'Checking...' : 'Check Schema'}
                  </button>
                </div>
              </div>
            )}

            {/* Direct Bulk Paste Mode */}
            {entryMode === 'bulk_paste' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div
                  style={{
                    padding: 14,
                    background: 'rgba(59, 130, 246, 0.08)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid rgba(59, 130, 246, 0.25)',
                    fontSize: 12.5,
                    color: 'var(--text-secondary)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                    <strong style={{ color: '#93C5FD', display: 'flex', alignItems: 'center', gap: 6 }}>
                      <FileSpreadsheet size={15} /> Paste Multi-Row CSV or Tabular Data
                    </strong>
                  </div>
                  <p style={{ margin: 0, fontSize: 12 }}>
                    Copy rows directly from Excel or Google Sheets (or CSV) and paste below. The first row must contain column headers.
                  </p>
                  <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text-muted)' }}>
                    <strong>Supported Headers:</strong>{' '}
                    {masterType === 'item' && 'ItemCode, ItemName, ItemsGroupCode, InventoryUOM, ItemType, TaxRate, ItemManagementMethod, ItemCategory, MaterialType, HSN, TaxCategory'}
                    {masterType === 'business_partner' && 'CardCode, CardName, Address, TaxDetails, PaymentTerms, Currency, ControlAccount, GSTNo, PANNo'}
                    {masterType === 'warehouse' && 'WarehouseCode, WarehouseName, Location, Address'}
                  </div>
                </div>

                <div>
                  <textarea
                    rows={7}
                    className="form-input"
                    style={{
                      fontFamily: 'monospace',
                      fontSize: 12,
                      width: '100%',
                      resize: 'vertical',
                      background: '#FFFFFF',
                      border: '1px solid #CBD5E1',
                      color: '#0F172A',
                    }}
                    placeholder={`Paste CSV or tab-separated data here...\nExample:\n${masterType === 'item'
                      ? 'ItemCode,ItemName,ItemsGroupCode,InventoryUOM,ItemType,TaxRate,ItemManagementMethod,ItemCategory,MaterialType,HSN,TaxCategory\nITM-9001,Hex Bolt M10,100,PCS,Inventory/Sales/Purchase,18%,None,Item,RM,73181500,Taxable\nITM-9002,Lock Nut M10,100,PCS,Inventory/Sales/Purchase,18%,None,Item,RM,73181500,Taxable'
                      : masterType === 'business_partner'
                        ? 'CardCode,CardName,Address,TaxDetails,PaymentTerms,Currency,ControlAccount,GSTNo,PANNo\nV-9001,Acme Supply,Plot 10 Industrial Area,GST 18%,Net 30,INR,211000,27AABCU9603R1ZM,AABCU9603R\nV-9002,Global Steel,Plot 20 Sector 4,GST 18%,Net 30,INR,211000,27AABCU9603R1ZM,AABCU9603R'
                        : 'WarehouseCode,WarehouseName,Location,Address\nWH-EAST,East Logistics,1,100 East Port Rd\nWH-WEST,West Hub,2,200 West Highway'
                      }`}
                    value={pastedText}
                    onChange={(e) => setPastedText(e.target.value)}
                  />
                </div>

                <div style={{ display: 'flex', gap: 10 }}>
                  <button
                    type="button"
                    onClick={handleParsePastedText}
                    className="btn btn-primary"
                    style={{ fontSize: 13, padding: '8px 18px' }}
                  >
                    <CheckCircle size={14} /> Parse & Preview Rows
                  </button>
                  {pastedText && (
                    <button
                      type="button"
                      onClick={() => {
                        setPastedText('');
                        setParsedPasteRows([]);
                        setPasteError(null);
                      }}
                      className="btn btn-secondary"
                      style={{ fontSize: 12, padding: '8px 12px' }}
                    >
                      Clear
                    </button>
                  )}
                </div>

                {pasteError && (
                  <div
                    style={{
                      padding: 12,
                      background: 'rgba(239, 68, 68, 0.12)',
                      border: '1px solid rgba(239, 68, 68, 0.35)',
                      borderRadius: 'var(--radius-md)',
                      color: '#F87171',
                      fontSize: 12.5,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                    }}
                  >
                    <AlertCircle size={16} />
                    {pasteError}
                  </div>
                )}

                {/* Parsed Rows Preview */}
                {parsedPasteRows.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        marginBottom: 10,
                      }}
                    >
                      <span style={{ fontSize: 13, fontWeight: 600, color: '#34D399' }}>
                        ✓ {parsedPasteRows.length} Rows Ready for SAP Posting
                      </span>
                    </div>

                    <div
                      style={{
                        maxHeight: 220,
                        overflowY: 'auto',
                        borderRadius: 'var(--radius-md)',
                        border: '1px solid #E2E8F0',
                        background: '#FFFFFF',
                      }}
                    >
                      <table className="data-table" style={{ fontSize: 12 }}>
                        <thead>
                          <tr>
                            <th>#</th>
                            <th>Code</th>
                            <th>Name / Description</th>
                            <th>Secondary Attributes</th>
                            <th>Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {parsedPasteRows.map((row, idx) => (
                            <tr key={idx}>
                              <td>{idx + 1}</td>
                              <td>
                                <strong style={{ color: '#60A5FA', fontFamily: 'monospace' }}>
                                  {row.ItemCode || row.CardCode || row.WarehouseCode || `Row #${idx + 1}`}
                                </strong>
                              </td>
                              <td style={{ color: '#F1F5F9' }}>
                                {row.ItemName || row.CardName || row.WarehouseName || '-'}
                              </td>
                              <td style={{ color: 'var(--text-muted)', fontSize: 11 }}>
                                {Object.entries(row)
                                  .filter(([k]) => !['ItemCode', 'ItemName', 'CardCode', 'CardName', 'WarehouseCode', 'WarehouseName'].includes(k))
                                  .map(([k, v]) => `${k}: ${v}`)
                                  .join(', ')}
                              </td>
                              <td>
                                <span
                                  style={{
                                    fontSize: 11,
                                    padding: '2px 8px',
                                    borderRadius: 8,
                                    background: 'rgba(16, 185, 129, 0.15)',
                                    color: '#34D399',
                                  }}
                                >
                                  Parsed
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    <div style={{ marginTop: 16 }}>
                      <button
                        type="button"
                        onClick={() => setIsDirectBulkConfirmOpen(true)}
                        className="btn btn-primary"
                        style={{ width: '100%', padding: '12px 20px', fontSize: 14 }}
                      >
                        <Send size={15} /> Confirm & Bulk Post to SAP ({parsedPasteRows.length} Records)
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* RIGHT: Quick Upload Shortcut & Service Layer Protection */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Quick Upload Shortcut Card */}
            <div className="glass-panel" style={{ padding: 24, border: '1px solid rgba(59, 130, 246, 0.25)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                <FileSpreadsheet size={20} color="#60A5FA" />
                <h3 style={{ fontSize: 15, fontWeight: 700 }}>Have a Spreadsheet or PDF?</h3>
              </div>
              <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', marginBottom: 16, lineHeight: 1.5 }}>
                Upload an Excel (.xlsx), CSV, or PDF specification document. Our 3-engine extraction pipeline automatically parses single or multi-row datasets with consensus validation.
              </p>
              <button
                type="button"
                onClick={() => setActiveSubTab('pdf')}
                className="btn btn-primary"
                style={{ width: '100%', fontSize: 13, padding: '10px 16px' }}
              >
                <UploadCloud size={15} /> Switch to Bulk Spreadsheet Upload
              </button>
            </div>

          </div>
        </div>
      )}

      {/* SUB-TAB 2: Bulk Data & Spreadsheet Upload */}
      {!creationSuccess && !bulkCreationSummary && activeSubTab === 'pdf' && (
        <div>
          {bulkRecords.length > 1 ? (
            /* Bulk Master Data Studio */
            <div className="glass-panel" style={{ padding: 28 }}>
              {/* Header */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: 20,
                  paddingBottom: 16,
                  borderBottom: '1px solid var(--border-subtle)',
                  flexWrap: 'wrap',
                  gap: 12,
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <FileSpreadsheet size={22} color="#10B981" />
                    <h3 style={{ fontSize: 18, fontWeight: 700 }}>
                      Bulk Master Data Studio ({bulkRecords.length} Records Extracted)
                    </h3>
                  </div>
                  <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', marginTop: 4 }}>
                    Review, apply batch defaults, and dispatch bulk creation directly to SAP Service Layer (<code>{serviceLayerEndpoint}</code>).
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <button
                    type="button"
                    onClick={() => {
                      setPdfFile(null);
                      setBulkRecords([]);
                      setBulkWorkflow(null);
                      setExtractedSummary(null);
                    }}
                    className="btn btn-secondary"
                    style={{ fontSize: 12, padding: '6px 12px' }}
                  >
                    <RotateCcw size={13} /> Upload Different File
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsBulkConfirmOpen(true)}
                    disabled={selectedBulkRowIndices.size === 0 || bulkPostingLoading}
                    className="btn btn-primary"
                    style={{ fontSize: 13, padding: '8px 18px' }}
                    title={
                      selectedNeedsDataCount > 0
                        ? `Warning: ${selectedNeedsDataCount} of ${selectedBulkRowIndices.size} selected records have missing mandatory SAP fields.`
                        : `Post ${selectedBulkRowIndices.size} records to SAP`
                    }
                  >
                    <Send size={14} /> Confirm & Post ({selectedBulkRowIndices.size}) in SAP
                  </button>
                </div>
              </div>

              {/* Metrics & Filter Toolbar */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  marginBottom: 16,
                  flexWrap: 'wrap',
                  gap: 12,
                  background: 'rgba(15, 23, 42, 0.6)',
                  padding: 12,
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    onClick={selectAllBulkRows}
                    className="btn btn-secondary"
                    style={{ fontSize: 12, padding: '4px 10px' }}
                  >
                    <CheckSquare size={13} /> Select All
                  </button>
                  <button
                    type="button"
                    onClick={deselectAllBulkRows}
                    className="btn btn-secondary"
                    style={{ fontSize: 12, padding: '4px 10px' }}
                  >
                    <Square size={13} /> Deselect All
                  </button>
                  <button
                    type="button"
                    onClick={openDefaultsModal}
                    className="btn btn-secondary"
                    style={{ fontSize: 12, padding: '4px 12px', color: '#60A5FA', borderColor: 'rgba(59, 130, 246, 0.4)' }}
                  >
                    <Wand2 size={13} /> Batch Defaults...
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsBulkTableEditMode((prev) => !prev)}
                    className={`btn ${isBulkTableEditMode ? 'btn-primary' : 'btn-secondary'}`}
                    style={{
                      fontSize: 12,
                      padding: '4px 12px',
                      fontWeight: 600,
                      background: isBulkTableEditMode ? '#2563EB' : undefined,
                      color: isBulkTableEditMode ? '#FFFFFF' : undefined,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                    title="Toggle spreadsheet editing across all table cells"
                  >
                    <Edit3 size={13} /> {isBulkTableEditMode ? 'Exit Table Edit' : 'Edit in Table (Spreadsheet)'}
                  </button>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                  {/* Filter Pills */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <button
                      type="button"
                      onClick={() => setBulkStatusFilter('ALL')}
                      className={`btn ${bulkStatusFilter === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
                      style={{ fontSize: 11, padding: '3px 10px' }}
                    >
                      All ({bulkRecords.length})
                    </button>
                    <button
                      type="button"
                      onClick={() => setBulkStatusFilter('READY')}
                      className={`btn ${bulkStatusFilter === 'READY' ? 'btn-primary' : 'btn-secondary'}`}
                      style={{
                        fontSize: 11,
                        padding: '3px 10px',
                        color: bulkStatusFilter === 'READY' ? '#FFFFFF' : '#34D399',
                        borderColor: 'rgba(16, 185, 129, 0.4)',
                      }}
                    >
                      Ready ({bulkValidationSummary.readyCount})
                    </button>
                    <button
                      type="button"
                      onClick={() => setBulkStatusFilter('NEEDS_DATA')}
                      className={`btn ${bulkStatusFilter === 'NEEDS_DATA' ? 'btn-primary' : 'btn-secondary'}`}
                      style={{
                        fontSize: 11,
                        padding: '3px 10px',
                        color: bulkStatusFilter === 'NEEDS_DATA' ? '#FFFFFF' : '#DC2626',
                        background: bulkStatusFilter === 'NEEDS_DATA' ? '#DC2626' : '#FEF2F2',
                        borderColor: '#FCA5A5',
                        fontWeight: 600,
                      }}
                    >
                      Mandatory Field Required ({bulkValidationSummary.needsDataCount})
                    </button>
                  </div>

                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                    Selected: <strong style={{ color: '#60A5FA' }}>{selectedBulkRowIndices.size}</strong> of{' '}
                    {bulkRecords.length}
                  </span>
                  <div style={{ position: 'relative', width: 200 }}>
                    <Search size={14} color="var(--text-muted)" style={{ position: 'absolute', left: 10, top: 10 }} />
                    <input
                      type="text"
                      className="form-input"
                      placeholder="Search extracted..."
                      value={bulkSearchFilter}
                      onChange={(e) => setBulkSearchFilter(e.target.value)}
                      style={{ paddingLeft: 30, fontSize: 12, height: 34 }}
                    />
                  </div>
                </div>
              </div>

              {/* Informative Alert Banner when mandatory fields are missing */}
              {bulkValidationSummary.needsDataCount > 0 && (
                <div
                  style={{
                    background: 'rgba(239, 68, 68, 0.08)',
                    border: '1px solid rgba(239, 68, 68, 0.25)',
                    borderRadius: 'var(--radius-md)',
                    padding: '10px 16px',
                    marginBottom: 14,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: 12,
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <AlertCircle size={18} color="#F87171" style={{ flexShrink: 0 }} />
                    <div style={{ fontSize: 12.5, color: '#FCA5A5' }}>
                      <strong>{bulkValidationSummary.needsDataCount} of {bulkRecords.length} records have missing mandatory SAP fields</strong>{' '}
                      (e.g. <code>{MANDATORY_MODULE_FIELDS[masterType]?.slice(2, 6).join(', ')}</code>).
                      They will be rejected by SAP  until these fields are provided.
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={openDefaultsModal}
                    className="btn btn-secondary"
                    style={{
                      fontSize: 11.5,
                      padding: '4px 12px',
                      color: '#60A5FA',
                      borderColor: 'rgba(59, 130, 246, 0.5)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    <Wand2 size={13} /> Batch Fill with Defaults
                  </button>
                </div>
              )}

              {/* Unsaved Table Edits Bar */}
              {Object.keys(bulkInlineEdits).length > 0 && (
                <div
                  style={{
                    background: '#FEF3C7',
                    border: '1px solid #FDE68A',
                    borderRadius: 'var(--radius-md)',
                    padding: '10px 16px',
                    marginBottom: 14,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <span style={{ fontSize: 12, fontWeight: 700, color: '#92400E' }}>
                    Unsaved edits in {Object.keys(bulkInlineEdits).length} row(s).
                  </span>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button
                      type="button"
                      onClick={() => setBulkInlineEdits({})}
                      className="btn btn-secondary"
                      style={{ fontSize: 11, padding: '4px 10px' }}
                    >
                      Discard
                    </button>
                    <button
                      type="button"
                      onClick={handleSaveAllBulkTableEdits}
                      disabled={isSavingBulkTableEdits}
                      className="btn btn-primary"
                      style={{ fontSize: 11, padding: '4px 14px' }}
                    >
                      {isSavingBulkTableEdits ? 'Saving...' : 'Save All Table Changes'}
                    </button>
                  </div>
                </div>
              )}

              {/* Interactive Multi-Row Table showing ALL fields */}
              <div style={{ overflowX: 'auto', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
                <table className="data-table" style={{ fontSize: 12.5 }}>
                  <thead>
                    <tr>
                      <th style={{ width: 40, textAlign: 'center' }}>
                        <input
                          type="checkbox"
                          checked={selectedBulkRowIndices.size === bulkRecords.length && bulkRecords.length > 0}
                          onChange={(e) => (e.target.checked ? selectAllBulkRows() : deselectAllBulkRows())}
                          style={{ accentColor: '#3B82F6' }}
                        />
                      </th>
                      <th style={{ width: 45 }}>#</th>
                      <th style={{ width: 115 }}>Status</th>
                      {allBulkColumns.map((colKey) => (
                        <th
                          key={colKey}
                          style={{ whiteSpace: 'nowrap', color: '#1E293B', fontWeight: 600, fontSize: 12 }}
                          title={colKey}
                        >
                          {colKey}
                        </th>
                      ))}
                      <th style={{ width: 100, textAlign: 'right' }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredBulkRecords.map(({ rec, originalIdx, missing, isReady }) => {
                      const isSelected = selectedBulkRowIndices.has(originalIdx);

                      return (
                        <React.Fragment key={originalIdx}>
                          <tr
                            style={{
                              background: isSelected ? 'rgba(59, 130, 246, 0.05)' : undefined,
                              cursor: 'pointer',
                            }}
                            onClick={() => toggleBulkRow(originalIdx)}
                          >
                            <td style={{ textAlign: 'center' }} onClick={(e) => e.stopPropagation()}>
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => toggleBulkRow(originalIdx)}
                                style={{ accentColor: '#3B82F6' }}
                              />
                            </td>
                            <td>{originalIdx + 1}</td>
                            <td>
                              {isReady ? (
                                <span
                                  style={{
                                    fontSize: 11,
                                    padding: '3px 8px',
                                    borderRadius: 6,
                                    background: '#DCFCE7',
                                    color: '#15803D',
                                    border: '1px solid #86EFAC',
                                    fontWeight: 700,
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: 4,
                                    whiteSpace: 'nowrap',
                                  }}
                                  title="All mandatory SAP fields are complete."
                                >
                                  <CheckCircle size={11} /> Mandatory Passed
                                </span>
                              ) : (
                                <span
                                  style={{
                                    fontSize: 11,
                                    padding: '3px 8px',
                                    borderRadius: 6,
                                    background: '#FEE2E2',
                                    color: '#DC2626',
                                    border: '1px solid #FCA5A5',
                                    fontWeight: 700,
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: 4,
                                    whiteSpace: 'nowrap',
                                  }}
                                  title={`Missing mandatory SAP fields: ${missing.join(', ')}`}
                                >
                                  <AlertCircle size={11} /> Mandatory Field Required ({missing.length})
                                </span>
                              )}
                            </td>

                            {allBulkColumns.map((colKey) => {
                              const cellVal = bulkInlineEdits[originalIdx]?.[colKey] ?? rec[colKey];
                              const hasEntry = cellVal !== undefined && cellVal !== null && String(cellVal).trim() !== '';
                              const isEdited = bulkInlineEdits[originalIdx]?.[colKey] !== undefined;

                              if (isBulkTableEditMode) {
                                return (
                                  <td
                                    key={colKey}
                                    style={{
                                      background: isEdited ? '#FEF3C7' : '#FFFFFF',
                                      padding: '4px 6px',
                                      minWidth: 100,
                                    }}
                                    onClick={(e) => e.stopPropagation()}
                                  >
                                    <input
                                      type="text"
                                      className="form-input"
                                      value={cellVal ?? ''}
                                      placeholder="—"
                                      onChange={(e) => handleBulkInlineCellChange(originalIdx, colKey, e.target.value)}
                                      style={{
                                        fontSize: 11,
                                        padding: '2px 6px',
                                        height: 26,
                                        width: '100%',
                                        minWidth: 80,
                                        borderRadius: 4,
                                        borderColor: isEdited ? '#D97706' : '#CBD5E1',
                                        background: isEdited ? '#FFFBEB' : '#FFFFFF',
                                      }}
                                    />
                                  </td>
                                );
                              }

                              return (
                                <td
                                  key={colKey}
                                  style={{
                                    color: hasEntry ? '#0F172A' : '#94A3B8',
                                    fontWeight: colKey === 'CardCode' || colKey === 'ItemCode' || colKey === 'WarehouseCode' ? 600 : 400,
                                    fontFamily: colKey === 'CardCode' || colKey === 'ItemCode' || colKey === 'WarehouseCode' ? 'monospace' : 'inherit',
                                    whiteSpace: 'nowrap',
                                    minWidth: 90,
                                  }}
                                >
                                  {hasEntry ? (
                                    typeof cellVal === 'boolean' ? (cellVal ? 'Yes' : 'No') : String(cellVal)
                                  ) : (
                                    <span style={{ color: '#94A3B8', fontWeight: 500, fontSize: 13 }}>—</span>
                                  )}
                                </td>
                              );
                            })}

                            <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }} onClick={(e) => e.stopPropagation()}>
                              <button
                                type="button"
                                onClick={() => handleToggleExpandBulkRow(originalIdx)}
                                className="btn btn-secondary"
                                style={{
                                  padding: '3px 8px',
                                  fontSize: 11,
                                  fontWeight: 600,
                                  color: '#2563EB',
                                  borderColor: 'rgba(59, 130, 246, 0.4)',
                                }}
                              >
                                {expandedBulkRowIndex === originalIdx ? 'Close' : 'Edit'}
                              </button>
                            </td>
                          </tr>

                          {/* Expandable Editable Fields for this row */}
                          {expandedBulkRowIndex === originalIdx && (
                            <tr>
                              <td colSpan={4 + allBulkColumns.length} style={{ padding: '16px 20px', background: '#F8FAFC' }}>
                                <div style={{ background: '#FFFFFF', border: '1.5px solid #3B82F6', borderRadius: 'var(--radius-md)', padding: 16 }}>
                                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                                    <strong style={{ fontSize: 13, color: '#1E293B' }}>
                                      Edit Record Fields - Row #{originalIdx + 1}
                                    </strong>
                                    <button
                                      type="button"
                                      onClick={() => setExpandedBulkRowIndex(null)}
                                      style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#64748B' }}
                                    >
                                      <X size={15} />
                                    </button>
                                  </div>

                                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10, marginBottom: 14 }}>
                                    {allBulkColumns.map((k) => {
                                      const currentVal = bulkRowDrafts[originalIdx]?.[k] ?? rec[k] ?? '';
                                      return (
                                        <div key={k} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                                          <label style={{ fontSize: 11, fontWeight: 600, color: '#475569' }}>{k}</label>
                                          <input
                                            type="text"
                                            className="form-input"
                                            value={currentVal}
                                            placeholder={`Enter ${k}...`}
                                            onChange={(e) => handleBulkRowDraftChange(originalIdx, k, e.target.value)}
                                            style={{ fontSize: 12, padding: '4px 8px', height: 30 }}
                                          />
                                        </div>
                                      );
                                    })}
                                  </div>

                                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                                    <button
                                      type="button"
                                      onClick={() => setExpandedBulkRowIndex(null)}
                                      className="btn btn-secondary"
                                      style={{ fontSize: 11, padding: '4px 12px' }}
                                    >
                                      Cancel
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => handleSaveBulkRowDraft(originalIdx)}
                                      disabled={isSavingBulkRow}
                                      className="btn btn-primary"
                                      style={{ fontSize: 11, padding: '5px 14px' }}
                                    >
                                      {isSavingBulkRow ? 'Saving...' : 'Save Row Changes'}
                                    </button>
                                  </div>
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Bottom Sticky Actions */}
              <div
                style={{
                  marginTop: 20,
                  paddingTop: 16,
                  borderTop: '1px solid var(--border-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: 12,
                }}
              >
                <div style={{ fontSize: 12.5, color: 'var(--text-muted)' }}>
                  Selected: <strong style={{ color: '#F1F5F9' }}>{selectedBulkRowIndices.size}</strong> records{' '}
                  ({selectedReadyCount} Mandatory Passed,{' '}
                  <span style={{ color: selectedNeedsDataCount > 0 ? '#DC2626' : undefined, fontWeight: selectedNeedsDataCount > 0 ? 600 : undefined }}>
                    {selectedNeedsDataCount} Mandatory Field Required
                  </span>).
                </div>

                <button
                  type="button"
                  onClick={() => setIsBulkConfirmOpen(true)}
                  disabled={selectedBulkRowIndices.size === 0 || bulkPostingLoading}
                  className="btn btn-primary"
                  style={{ padding: '10px 24px', fontSize: 13 }}
                  title={
                    selectedNeedsDataCount > 0
                      ? `Warning: ${selectedNeedsDataCount} of ${selectedBulkRowIndices.size} selected records have missing mandatory SAP fields.`
                      : `Create all ${selectedBulkRowIndices.size} records in SAP `
                  }
                >
                  <Send size={15} /> Confirm & Create All ({selectedBulkRowIndices.size}) in SAP
                </button>
              </div>
            </div>
          ) : (
            /* Dedicated Upload Sandbox (Single / Initial State) */
            <div className="grid-2" style={{ gridTemplateColumns: 'minmax(420px, 1.3fr) minmax(320px, 1fr)', gap: 24 }}>
              <div className="glass-panel" style={{ padding: 28 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <UploadCloud size={20} color="#3B82F6" />
                    <h3 style={{ fontSize: 16, fontWeight: 700 }}>Upload {title} File (Excel, CSV, or PDF)</h3>
                  </div>
                </div>
                <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', marginBottom: 20 }}>
                  Upload a multi-row Excel workbook (.xlsx), CSV dataset, or PDF specification document. Our 3-engine pipeline extracts, normalizes, and prepares records for batch SAP posting.
                </p>

                {/* Dropzone */}
                <div
                  className={`dropzone ${pdfFile ? 'active' : ''}`}
                  style={{ padding: 32, textAlign: 'center', cursor: 'pointer' }}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={(e) => e.target.files?.[0] && handleDocumentFile(e.target.files[0])}
                    accept=".pdf,.xlsx,.xls,.csv,application/pdf,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,text/csv"
                    style={{ display: 'none' }}
                  />

                  {pdfFile ? (
                    <div>
                      {isExcelFile(pdfFile.name) ? (
                        <FileSpreadsheet size={32} color="#10B981" style={{ margin: '0 auto 10px' }} />
                      ) : (
                        <FileCheck size={32} color="#10B981" style={{ margin: '0 auto 10px' }} />
                      )}
                      <strong style={{ fontSize: 15, color: '#F8FAFC', display: 'block' }}>{pdfFile.name}</strong>
                      <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                        {(pdfFile.size / 1024).toFixed(1)} KB • {isExcelFile(pdfFile.name) ? 'Spreadsheet Dataset' : 'PDF Document'}
                      </span>
                    </div>
                  ) : (
                    <div>
                      <UploadCloud size={32} color="#3B82F6" style={{ margin: '0 auto 10px' }} />
                      <strong style={{ fontSize: 15, display: 'block', marginBottom: 4 }}>
                        Select {title} Spreadsheet or PDF
                      </strong>
                      <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                        Drag & drop or click to browse (.xlsx, .csv, .pdf)
                      </span>
                    </div>
                  )}
                </div>

                {pdfError && (
                  <div style={{ marginTop: 12, padding: 12, background: 'rgba(239, 68, 68, 0.1)', color: '#F87171', borderRadius: 6, fontSize: 12 }}>
                    {pdfError}
                  </div>
                )}

                {/* Extraction Progress Indicator */}
                {extractionStep && (
                  <div style={{ marginTop: 16, textAlign: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginBottom: 6, color: '#60A5FA', fontSize: 12, fontWeight: 500 }}>
                      <span className="pulse-animation" style={{ width: 8, height: 8, borderRadius: '50%', background: '#3B82F6' }} />
                      {extractionStep}
                    </div>
                    <div style={{ height: 3, background: '#1E293B', borderRadius: 2, overflow: 'hidden' }}>
                      <div style={{ width: '85%', height: '100%', background: 'linear-gradient(90deg, #3B82F6, #60A5FA)' }} className="pulse-animation" />
                    </div>
                  </div>
                )}

                {/* Action Buttons for Document */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 20 }}>
                  <button
                    onClick={runPdfExtraction}
                    disabled={!pdfFile || extracting}
                    className="btn btn-primary"
                    style={{ padding: '12px 16px', fontSize: 14, width: '100%' }}
                  >
                    <Sparkles size={16} /> {extracting ? 'Extracting Records Across Engines...' : 'Extract Data & Build Dataset'}
                  </button>
                </div>
              </div>

              {/* RIGHT SIDE OF UPLOAD TAB */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                {extractedSummary && (
                  <div
                    className="glass-panel"
                    style={{
                      padding: 20,
                      background: 'rgba(16, 185, 129, 0.08)',
                      border: '1px solid rgba(16, 185, 129, 0.3)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                      <CheckCircle size={16} color="#34D399" />
                      <strong style={{ fontSize: 14, color: '#34D399' }}>
                        Single Record Extracted ({extractedSummary.fieldsCount} Fields)
                      </strong>
                    </div>
                    <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', marginBottom: 14 }}>
                      A single record was identified. Values have been populated into the Direct Posting form.
                    </p>
                    <button
                      type="button"
                      onClick={() => setActiveSubTab('form')}
                      className="btn btn-primary"
                      style={{ width: '100%', fontSize: 12.5, padding: '8px 14px' }}
                    >
                      Review & Post in Form <ArrowRight size={13} />
                    </button>
                  </div>
                )}

                <div
                  className="glass-panel"
                  style={{
                    padding: 20,
                    background: 'rgba(15, 23, 42, 0.6)',
                    border: '1px solid var(--border-subtle)',
                    fontSize: 12.5,
                    color: 'var(--text-muted)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8, color: '#93C5FD' }}>
                    <ShieldCheck size={16} />
                    <strong style={{ color: '#F8FAFC' }}>Service Layer Bulk Guarantee</strong>
                  </div>
                  <p style={{ margin: 0, lineHeight: 1.5 }}>
                    Bulk operations execute concurrent HTTP POST requests to <code>{serviceLayerEndpoint}</code> via SAP Service Layer. Each entry is validated by SAP  logic with zero direct database SQL manipulation.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* SUB-TAB 3: Live SAP Records Explorer */}
      {activeSubTab === 'records' && (
        <div className="glass-panel" style={{ padding: 24 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 16,
              flexWrap: 'wrap',
              gap: 12,
            }}
          >
            <div>
              <h3 style={{ fontSize: 17, fontWeight: 700 }}>Live SAP  {title} Catalog</h3>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                Authoritative records queried directly from SAP Service Layer ({recordsTotal} total records)
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ position: 'relative', width: 260 }}>
                <Search size={15} color="var(--text-muted)" style={{ position: 'absolute', left: 10, top: 11 }} />
                <input
                  type="text"
                  className="form-input"
                  placeholder={`Search ${title}...`}
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{ paddingLeft: 32, fontSize: 13 }}
                />
              </div>

              <button
                onClick={loadRecords}
                disabled={loadingRecords}
                className="btn btn-secondary"
                style={{ padding: '8px 12px', fontSize: 12 }}
              >
                <RefreshCw size={13} className={loadingRecords ? 'spin-animation' : ''} /> Refresh
              </button>

              <button
                onClick={() => setActiveSubTab('form')}
                className="btn btn-primary"
                style={{ padding: '8px 16px', fontSize: 12 }}
              >
                + Create New
              </button>
            </div>
          </div>

          {/* Records Table */}
          <div style={{ overflowX: 'auto', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <table className="data-table">
              <thead>
                <tr>
                  {masterType === 'item' && (
                    <>
                      <th>Item Code</th>
                      <th>Description</th>
                      <th>Group</th>
                      <th>Inventory UoM</th>
                      <th>Weight</th>
                      <th>Inventory Item</th>
                      <th>Actions</th>
                    </>
                  )}
                  {masterType === 'business_partner' && (
                    <>
                      <th>Card Code</th>
                      <th>Partner Name</th>
                      <th>Type</th>
                      <th>Email Address</th>
                      <th>Phone</th>
                      <th>Currency</th>
                      <th>Actions</th>
                    </>
                  )}
                  {masterType === 'warehouse' && (
                    <>
                      <th>Warehouse Code</th>
                      <th>Warehouse Name</th>
                      <th>Location</th>
                      <th>City</th>
                      <th>Country</th>
                      <th>Bin Locations</th>
                      <th>Actions</th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {records.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ textAlign: 'center', padding: 36, color: 'var(--text-muted)' }}>
                      {loadingRecords ? 'Loading authoritative records from SAP...' : 'No records found.'}
                    </td>
                  </tr>
                ) : (
                  records.map((rec: any, idx: number) => {
                    const primaryKey = rec.ItemCode || rec.CardCode || rec.WarehouseCode || idx;
                    return (
                      <tr key={primaryKey}>
                        {masterType === 'item' && (
                          <>
                            <td>
                              <strong style={{ color: '#60A5FA', fontFamily: 'monospace' }}>{rec.ItemCode}</strong>
                            </td>
                            <td style={{ color: '#F8FAFC' }}>{rec.ItemName}</td>
                            <td>{rec.ItemsGroupCode || '-'}</td>
                            <td>{rec.InventoryUOM || '-'}</td>
                            <td>{rec.SalesUnitWeight ? `${rec.SalesUnitWeight} kg` : '-'}</td>
                            <td>
                              <span
                                style={{
                                  fontSize: 11,
                                  padding: '2px 8px',
                                  borderRadius: 10,
                                  background: rec.InventoryItem === 'tYES' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                                  color: rec.InventoryItem === 'tYES' ? '#34D399' : '#F87171',
                                }}
                              >
                                {rec.InventoryItem === 'tYES' ? 'Yes' : 'No'}
                              </span>
                            </td>
                            <td>
                              <button
                                onClick={() => setSelectedRecordDetails(rec)}
                                className="btn btn-secondary"
                                style={{ padding: '4px 8px', fontSize: 11 }}
                              >
                                <Eye size={12} /> Inspect
                              </button>
                            </td>
                          </>
                        )}
                        {masterType === 'business_partner' && (
                          <>
                            <td>
                              <strong style={{ color: '#A78BFA', fontFamily: 'monospace' }}>{rec.CardCode}</strong>
                            </td>
                            <td style={{ color: '#F8FAFC' }}>{rec.CardName}</td>
                            <td>
                              <span
                                style={{
                                  fontSize: 11,
                                  padding: '2px 8px',
                                  borderRadius: 10,
                                  background:
                                    rec.CardType === 'cSupplier'
                                      ? 'rgba(59, 130, 246, 0.2)'
                                      : rec.CardType === 'cCustomer'
                                        ? 'rgba(16, 185, 129, 0.2)'
                                        : 'rgba(245, 158, 11, 0.2)',
                                  color:
                                    rec.CardType === 'cSupplier'
                                      ? '#93C5FD'
                                      : rec.CardType === 'cCustomer'
                                        ? '#34D399'
                                        : '#FBBF24',
                                }}
                              >
                                {rec.CardType === 'cSupplier' ? 'Supplier' : rec.CardType === 'cCustomer' ? 'Customer' : 'Lead'}
                              </span>
                            </td>
                            <td style={{ color: '#94A3B8' }}>{rec.EmailAddress || '-'}</td>
                            <td>{rec.Phone1 || '-'}</td>
                            <td>{rec.Currency || '-'}</td>
                            <td>
                              <button
                                onClick={() => setSelectedRecordDetails(rec)}
                                className="btn btn-secondary"
                                style={{ padding: '4px 8px', fontSize: 11 }}
                              >
                                <Eye size={12} /> Inspect
                              </button>
                            </td>
                          </>
                        )}
                        {masterType === 'warehouse' && (
                          <>
                            <td>
                              <strong style={{ color: '#34D399', fontFamily: 'monospace' }}>{rec.WarehouseCode}</strong>
                            </td>
                            <td style={{ color: '#F8FAFC' }}>{rec.WarehouseName}</td>
                            <td>{rec.Location || '-'}</td>
                            <td>{rec.City || '-'}</td>
                            <td>{rec.Country || '-'}</td>
                            <td>
                              <span
                                style={{
                                  fontSize: 11,
                                  padding: '2px 8px',
                                  borderRadius: 10,
                                  background: rec.BinActivat === 'tYES' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(148, 163, 184, 0.15)',
                                  color: rec.BinActivat === 'tYES' ? '#34D399' : '#94A3B8',
                                }}
                              >
                                {rec.BinActivat === 'tYES' ? 'Active' : 'Disabled'}
                              </span>
                            </td>
                            <td>
                              <button
                                onClick={() => setSelectedRecordDetails(rec)}
                                className="btn btn-secondary"
                                style={{ padding: '4px 8px', fontSize: 11 }}
                              >
                                <Eye size={12} /> Inspect
                              </button>
                            </td>
                          </>
                        )}
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Record Inspection Modal */}
      {selectedRecordDetails && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.75)',
            backdropFilter: 'blur(8px)',
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
              maxWidth: 640,
              width: '100%',
              maxHeight: '85vh',
              overflowY: 'auto',
              padding: 28,
              background: '#FFFFFF',
              border: '1px solid #E2E8F0',
              boxShadow: '0 20px 40px rgba(15, 23, 42, 0.15)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ fontSize: 18, fontWeight: 700, color: '#0F172A' }}>
                {title} Record Details
              </h3>
              <button
                onClick={() => setSelectedRecordDetails(null)}
                className="btn btn-secondary"
                style={{ padding: '4px 10px', fontSize: 12 }}
              >
                Close
              </button>
            </div>

            <pre
              style={{
                background: '#F8FAFC',
                padding: 16,
                borderRadius: 'var(--radius-md)',
                border: '1px solid #E2E8F0',
                fontSize: 12,
                color: '#1E293B',
                overflowX: 'auto',
              }}
            >
              {JSON.stringify(selectedRecordDetails, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* Authoritative Confirmation Gate Modal */}
      <ConfirmationModal
        isOpen={isConfirmModalOpen}
        masterType={masterType}
        payload={formData}
        onConfirm={executeSapPost}
        onCancel={() => setIsConfirmModalOpen(false)}
        loading={postingLoading}
      />

      {/* Workflow Bulk Confirm Modal */}
      {bulkWorkflow && (
        <BulkConfirmModal
          isOpen={isBulkConfirmOpen}
          onClose={() => setIsBulkConfirmOpen(false)}
          onConfirm={handleBulkConfirmAndPost}
          workflow={bulkWorkflow}
          selectedCount={selectedBulkRowIndices.size}
          loading={bulkPostingLoading}
          readyCount={selectedReadyCount}
          needsDataCount={selectedNeedsDataCount}
        />
      )}

      {/* Direct Bulk Paste Confirm Modal */}
      {isDirectBulkConfirmOpen && (
        <BulkConfirmModal
          isOpen={isDirectBulkConfirmOpen}
          onClose={() => setIsDirectBulkConfirmOpen(false)}
          onConfirm={handleExecuteDirectBulkPost}
          workflow={{
            workflow_id: 'direct-paste-batch',
            master_type: masterType,
            status: 'CONFIRMED',
            total_records: parsedPasteRows.length,
            valid_records: parsedPasteRows.length,
            invalid_records: 0,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          } as any}
          selectedCount={parsedPasteRows.length}
          loading={postingLoading}
        />
      )}

      {/* Batch Defaults Modal */}
      {isDefaultsModalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.55)',
            backdropFilter: 'blur(6px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: 20,
          }}
        >
          <div
            className="glass-panel"
            style={{
              maxWidth: 580,
              width: '100%',
              maxHeight: '90vh',
              display: 'flex',
              flexDirection: 'column',
              padding: 26,
              background: '#FFFFFF',
              border: '1px solid #E2E8F0',
              boxShadow: '0 20px 40px rgba(15, 23, 42, 0.15)',
              borderRadius: 'var(--radius-lg)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Wand2 size={18} color="#2563EB" />
                <h3 style={{ fontSize: 16, fontWeight: 700, color: '#0F172A' }}>Apply Batch Defaults</h3>
              </div>
              <button
                onClick={() => setIsDefaultsModalOpen(false)}
                className="btn btn-secondary"
                style={{ padding: '4px 8px', fontSize: 12 }}
              >
                <X size={14} />
              </button>
            </div>

            <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 14 }}>
              Fill in fallback defaults across all {bulkRecords.length} records. Existing non-empty values in individual rows will be preserved.
            </p>

            <div style={{ overflowY: 'auto', maxHeight: '55vh', paddingRight: 4, display: 'flex', flexDirection: 'column', gap: 12 }}>
              {masterType === 'item' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <label className="form-label">Inventory UoM</label>
                    <input
                      type="text"
                      className="form-input"
                      value={defaultsForm.InventoryUOM ?? ''}
                      placeholder="e.g. PCS, BOX, KG"
                      onChange={(e) => setDefaultsForm((prev) => ({ ...prev, InventoryUOM: e.target.value.toUpperCase() }))}
                    />
                  </div>
                  <div>
                    <label className="form-label">Item Group Code</label>
                    <input
                      type="number"
                      className="form-input"
                      value={defaultsForm.ItemsGroupCode ?? ''}
                      placeholder="e.g. 100"
                      onChange={(e) => setDefaultsForm((prev) => ({ ...prev, ItemsGroupCode: e.target.value === '' ? '' : parseInt(e.target.value, 10) }))}
                    />
                  </div>
                  <div>
                    <label className="form-label">Item Type</label>
                    <select
                      className="form-input"
                      value={defaultsForm.ItemType ?? ''}
                      onChange={(e) => setDefaultsForm((prev) => ({ ...prev, ItemType: e.target.value }))}
                    >
                      <option value="">Select Item Type...</option>
                      <option value="Inventory/Sales/Purchase">Inventory/Sales/Purchase</option>
                      <option value="Inventory">Inventory Only</option>
                      <option value="Sales">Sales Only</option>
                      <option value="Purchase">Purchase Only</option>
                    </select>
                  </div>
                  <div>
                    <label className="form-label">Item Category</label>
                    <select
                      className="form-input"
                      value={defaultsForm.ItemCategory ?? ''}
                      onChange={(e) => setDefaultsForm((prev) => ({ ...prev, ItemCategory: e.target.value }))}
                    >
                      <option value="">Select Category...</option>
                      <option value="Item">Item</option>
                      <option value="Service">Service</option>
                    </select>
                  </div>
                  <div>
                    <label className="form-label">Material Type</label>
                    <select
                      className="form-input"
                      value={defaultsForm.MaterialType ?? ''}
                      onChange={(e) => setDefaultsForm((prev) => ({ ...prev, MaterialType: e.target.value }))}
                    >
                      <option value="">Select Material Type...</option>
                      <option value="FG">Finished Goods (FG)</option>
                      <option value="RM">Raw Material (RM)</option>
                      <option value="Capital Goods">Capital Goods</option>
                    </select>
                  </div>
                  <div>
                    <label className="form-label">Tax Rate</label>
                    <input
                      type="text"
                      className="form-input"
                      value={defaultsForm.TaxRate ?? ''}
                      placeholder="e.g. 18%"
                      onChange={(e) => setDefaultsForm((prev) => ({ ...prev, TaxRate: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className="form-label">Tax Category</label>
                    <select
                      className="form-input"
                      value={defaultsForm.TaxCategory ?? ''}
                      onChange={(e) => setDefaultsForm((prev) => ({ ...prev, TaxCategory: e.target.value }))}
                    >
                      <option value="">Select Tax Category...</option>
                      <option value="Taxable">Taxable</option>
                      <option value="Exempted">Exempted</option>
                      <option value="Nil Rated">Nil Rated</option>
                    </select>
                  </div>
                  <div>
                    <label className="form-label">Management Method</label>
                    <select
                      className="form-input"
                      value={defaultsForm.ItemManagementMethod ?? ''}
                      onChange={(e) => setDefaultsForm((prev) => ({ ...prev, ItemManagementMethod: e.target.value }))}
                    >
                      <option value="">Select Method...</option>
                      <option value="None">None</option>
                      <option value="Batch">Batch</option>
                      <option value="Serial">Serial</option>
                    </select>
                  </div>
                  <div style={{ gridColumn: 'span 2' }}>
                    <label className="form-label">HSN / SAC Code</label>
                    <input
                      type="text"
                      className="form-input"
                      value={defaultsForm.HSN ?? ''}
                      placeholder="e.g. 84713010"
                      onChange={(e) => setDefaultsForm((prev) => ({ ...prev, HSN: e.target.value }))}
                    />
                  </div>
                </div>
              )}

              {masterType === 'business_partner' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <label className="form-label">Card Type</label>
                    <select
                      className="form-input"
                      value={defaultsForm.CardType ?? ''}
                      onChange={(e) => setDefaultsForm((prev) => ({ ...prev, CardType: e.target.value }))}
                    >
                      <option value="">Select Card Type...</option>
                      <option value="cSupplier">Supplier (Vendor)</option>
                      <option value="cCustomer">Customer</option>
                    </select>
                  </div>
                  <div>
                    <label className="form-label">Currency</label>
                    <input
                      type="text"
                      className="form-input"
                      value={defaultsForm.Currency ?? ''}
                      placeholder="e.g. INR, USD"
                      onChange={(e) => setDefaultsForm((prev) => ({ ...prev, Currency: e.target.value.toUpperCase() }))}
                    />
                  </div>
                  <div>
                    <label className="form-label">Payment Terms</label>
                    <select
                      className="form-input"
                      value={defaultsForm.PaymentTerms ?? ''}
                      onChange={(e) => setDefaultsForm((prev) => ({ ...prev, PaymentTerms: e.target.value }))}
                    >
                      <option value="">Select Payment Terms...</option>
                      <option value="Net 30">Net 30</option>
                      <option value="Net 60">Net 60</option>
                      <option value="Immediate">Immediate</option>
                    </select>
                  </div>
                  <div>
                    <label className="form-label">Control Account</label>
                    <input
                      type="text"
                      className="form-input"
                      value={defaultsForm.ControlAccount ?? ''}
                      placeholder="e.g. 211000"
                      onChange={(e) => setDefaultsForm((prev) => ({ ...prev, ControlAccount: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className="form-label">Tax Details</label>
                    <input
                      type="text"
                      className="form-input"
                      value={defaultsForm.TaxDetails ?? ''}
                      placeholder="e.g. GST 18%"
                      onChange={(e) => setDefaultsForm((prev) => ({ ...prev, TaxDetails: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className="form-label">Address</label>
                    <input
                      type="text"
                      className="form-input"
                      value={defaultsForm.Address ?? ''}
                      placeholder="Registered address"
                      onChange={(e) => setDefaultsForm((prev) => ({ ...prev, Address: e.target.value }))}
                    />
                  </div>
                </div>
              )}

              {masterType === 'warehouse' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                  <div>
                    <label className="form-label">Facility Location ID</label>
                    <input
                      type="number"
                      className="form-input"
                      value={defaultsForm.Location ?? ''}
                      placeholder="e.g. 1"
                      onChange={(e) => setDefaultsForm((prev) => ({ ...prev, Location: e.target.value === '' ? '' : parseInt(e.target.value, 10) }))}
                    />
                  </div>
                  <div>
                    <label className="form-label">City</label>
                    <input
                      type="text"
                      className="form-input"
                      value={defaultsForm.City ?? ''}
                      placeholder="e.g. Mumbai"
                      onChange={(e) => setDefaultsForm((prev) => ({ ...prev, City: e.target.value }))}
                    />
                  </div>
                  <div>
                    <label className="form-label">Country</label>
                    <input
                      type="text"
                      className="form-input"
                      value={defaultsForm.Country ?? ''}
                      placeholder="e.g. IN, US"
                      onChange={(e) => setDefaultsForm((prev) => ({ ...prev, Country: e.target.value.toUpperCase() }))}
                    />
                  </div>
                  <div>
                    <label className="form-label">Address</label>
                    <input
                      type="text"
                      className="form-input"
                      value={defaultsForm.Address ?? ''}
                      placeholder="Main Warehouse Depot address"
                      onChange={(e) => setDefaultsForm((prev) => ({ ...prev, Address: e.target.value }))}
                    />
                  </div>
                </div>
              )}
            </div>

            <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
              <button
                type="button"
                onClick={() => handleApplyBatchDefaults(defaultsForm)}
                className="btn btn-primary"
                style={{ flex: 1, padding: '10px 16px', fontSize: 13 }}
              >
                Apply to All Records
              </button>
              <button
                type="button"
                onClick={() => setIsDefaultsModalOpen(false)}
                className="btn btn-secondary"
                style={{ padding: '10px 16px', fontSize: 13 }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
