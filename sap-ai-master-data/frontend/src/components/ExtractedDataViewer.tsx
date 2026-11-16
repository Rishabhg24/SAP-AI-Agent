import React, { useState, useEffect } from 'react';
import type { WorkflowState } from '../types';
import { api } from '../services/api';
import {
  FileText,
  Database,
  Search,
  CheckCircle2,
  AlertTriangle,
  Code2,
  Sparkles,
  Check,
  ShieldCheck,
  Wand2,
  X,
  Edit3,
  Save,
  Copy,
  ClipboardCopy,
  Calendar,
  Hash,
  ArrowRightLeft,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Maximize2,
} from 'lucide-react';


interface Props {
  workflow: WorkflowState;
  onSelectRecord?: (index: number) => void;
  onBulkCreate?: (indices: number[]) => void;
  onApplyDefaults?: (defaults: Record<string, any>) => Promise<void>;
  onUpdateRecord?: (payload: {
    updates?: Record<string, any>;
    index?: number;
    apply_to_all?: boolean;
    records?: Record<string, any>[];
  }) => Promise<void>;
}

const FIELD_FRIENDLY_LABELS: Record<string, string> = {
  // Business Partner
  CardCode: 'Customer / Vendor Code (CardCode)',
  CardName: 'Business Partner Name (CardName)',
  CardType: 'Partner Type (Customer/Supplier)',
  Address: 'Street / Billing / Facility Address',
  TaxDetails: 'Tax Details / Structure (VatGroup)',
  PaymentTerms: 'Payment Terms (PayTermsGrpCode)',
  Currency: 'Default Currency',
  ControlAccount: 'GL Control Account (Reconciliation)',
  GSTNo: 'GST No / GSTIN (LicTradNum)',
  PANNo: 'PAN No (Permanent Account Number)',
  FederalTaxID: 'Federal Tax ID / GSTIN',
  EmailAddress: 'Email Address (MailAddress)',
  Phone1: 'Primary Phone (Phone1)',
  Phone2: 'Secondary Phone (Phone2)',

  // Items
  ItemCode: 'Item Code (ItemCode)',
  ItemName: 'Item Name / Description (ItemName)',
  ItemsGroupCode: 'Item Group (ItemsGroupCode)',
  InventoryUOM: 'Unit of Measure (UoM)',
  ItemType: 'Item Type (Inventory/Sales/Purchase)',
  TaxRate: 'Tax Rate (%)',
  ItemManagementMethod: 'Management Method (Serial/Batch/None)',
  ItemCategory: 'Item Category (Service/Item)',
  MaterialType: 'Material Type (RM/FG/Capital Goods)',
  HSN: 'HSN / SAC Code',
  TaxCategory: 'Tax Category (Taxable/Exempted)',
  InventoryItem: 'Inventory Item (Manage Stock)',
  SalesItem: 'Sales Item (Sellable)',
  PurchaseItem: 'Purchase Item (Purchasable)',
  SalesUnit: 'Sales Unit of Measure',
  PurchaseUnit: 'Purchase Unit of Measure',
  BarCode: 'Barcode (EAN/UPC)',
  SalesUnitWeight: 'Sales Unit Weight (Gross Weight)',

  // Warehouses
  WarehouseCode: 'Warehouse Code',
  WarehouseName: 'Warehouse Name',
  Location: 'Location Code',
  Inactive: 'Inactive Status',
  BinActivat: 'Bin Locations Activated',
  Street: 'Street',
  City: 'City',
  Country: 'Country',
};

const ENUM_OPTIONS: Record<string, { label: string; value: string }[]> = {
  CardType: [
    { label: 'Customer', value: 'Customer' },
    { label: 'Supplier', value: 'Supplier' },
  ],
  ItemType: [
    { label: 'Inventory/Sales/Purchase', value: 'Inventory/Sales/Purchase' },
    { label: 'Inventory', value: 'Inventory' },
    { label: 'Sales', value: 'Sales' },
    { label: 'Purchase', value: 'Purchase' },
  ],
  ItemManagementMethod: [
    { label: 'None', value: 'None' },
    { label: 'Batch', value: 'Batch' },
    { label: 'Serial', value: 'Serial' },
  ],
  ItemCategory: [
    { label: 'Item', value: 'Item' },
    { label: 'Service', value: 'Service' },
  ],
  MaterialType: [
    { label: 'RM', value: 'RM' },
    { label: 'FG', value: 'FG' },
    { label: 'Capital Goods', value: 'Capital Goods' },
  ],
  TaxCategory: [
    { label: 'Taxable', value: 'Taxable' },
    { label: 'Exempted', value: 'Exempted' },
  ],
  TaxDetails: [
    { label: 'GST 18%', value: 'GST 18%' },
    { label: 'GST 12%', value: 'GST 12%' },
    { label: 'GST 5%', value: 'GST 5%' },
    { label: 'Exempt', value: 'Exempt' },
  ],
  PaymentTerms: [
    { label: 'Net 30', value: 'Net 30' },
    { label: 'Net 60', value: 'Net 60' },
    { label: 'Immediate', value: 'Immediate' },
  ],
  Currency: [
    { label: 'INR', value: 'INR' },
    { label: 'USD', value: 'USD' },
    { label: 'EUR', value: 'EUR' },
  ],
};

const getFieldCategory = (fieldKey: string, _masterType?: string): 'GENERAL' | 'CONTACT' | 'FINANCIAL' | 'UDF' => {
  if (
    fieldKey.startsWith('U_') ||
    fieldKey.startsWith('u_') ||
    fieldKey.includes('UDF') ||
    (![
      'CardCode', 'CardName', 'CardType', 'Currency', 'ItemCode', 'ItemName', 'ItemsGroupCode', 'InventoryUOM', 'ItemType',
      'WarehouseCode', 'WarehouseName', 'Location', 'Address', 'City', 'Country', 'ZipCode', 'State', 'Phone1', 'Phone2',
      'EmailAddress', 'ContactPerson', 'Street', 'Building', 'Block', 'FederalTaxID', 'PANNo', 'GSTNo', 'ControlAccount',
      'PaymentTerms', 'TaxDetails', 'TaxRate', 'TaxCategory', 'HSN', 'Price', 'PriceList', 'CreateDate', 'DocDate'
    ].includes(fieldKey))
  ) {
    return 'UDF';
  }
  const general = [
    'CardCode', 'CardName', 'CardType', 'Currency',
    'ItemCode', 'ItemName', 'ItemsGroupCode', 'InventoryUOM', 'ItemType',
    'WarehouseCode', 'WarehouseName', 'Location', 'CreateDate', 'DocDate'
  ];
  if (general.includes(fieldKey)) return 'GENERAL';

  const contact = [
    'Address', 'City', 'Country', 'ZipCode', 'State',
    'Phone1', 'Phone2', 'EmailAddress', 'ContactPerson',
    'Street', 'Building', 'Block'
  ];
  if (contact.includes(fieldKey)) return 'CONTACT';

  const financial = [
    'FederalTaxID', 'PANNo', 'GSTNo', 'ControlAccount',
    'PaymentTerms', 'TaxDetails', 'TaxRate', 'TaxCategory', 'HSN', 'Price', 'PriceList'
  ];
  if (financial.includes(fieldKey)) return 'FINANCIAL';

  return 'GENERAL';
};

export const ExtractedDataViewer: React.FC<Props> = ({
  workflow,
  onSelectRecord,
  onBulkCreate,
  onApplyDefaults,
  onUpdateRecord,
}) => {
  const [activeTab, setActiveTab] = useState<'fields' | 'records' | 'engines'>('records');
  const [searchFilter, setSearchFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'VALID' | 'INVALID'>('ALL');
  const [selectedRecordIndex, setSelectedRecordIndex] = useState<number>(0);
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set());

  // Missing fields inline editing and expansion states
  const [isTableEditMode, setIsTableEditMode] = useState(false);
  const [expandedRowIndex, setExpandedRowIndex] = useState<number | null>(null);
  const [inlineEdits, setInlineEdits] = useState<Record<number, Record<string, any>>>({});
  const [rowDrafts, setRowDrafts] = useState<Record<number, Record<string, any>>>({});
  const [isSavingTableEdits, setIsSavingTableEdits] = useState(false);
  const [isSavingRow, setIsSavingRow] = useState(false);

  // Focused Quick Edit Modal state (Eliminates horizontal scrolling!)
  const [modalEditIndex, setModalEditIndex] = useState<number | null>(null);
  const [modalSearch, setModalSearch] = useState('');
  const [modalCategory, setModalCategory] = useState<'ALL' | 'MISSING' | 'GENERAL' | 'CONTACT' | 'FINANCIAL' | 'UDF'>('ALL');

  // Batch defaults modal state
  const [isDefaultsModalOpen, setIsDefaultsModalOpen] = useState(false);
  const [cardTypeDefault, setCardTypeDefault] = useState('');
  const [cardNamePrefixDefault, setCardNamePrefixDefault] = useState('');
  const [emailDefault, setEmailDefault] = useState('');
  const [itemsGroupCodeDefault, setItemsGroupCodeDefault] = useState<number | ''>('');
  const [isApplyingDefaults, setIsApplyingDefaults] = useState(false);

  const records = workflow.extracted_records || [];
  const hasMultipleRecords = records.length > 1;
  const activeData = workflow.normalized_data || {};
  const rawExtractions = workflow.raw_extractions || {};
  const bulkVal = workflow.bulk_validation;

  // Full standard fields definitions by master data type
  const ALL_MASTER_FIELDS: Record<string, string[]> = {
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
  };

  const defaultMandatoryByMaster: Record<string, string[]> = {
    business_partner: ['CardName', 'CardType', 'Address', 'TaxDetails', 'PaymentTerms', 'EmailAddress'],
    item: ['ItemName', 'ItemsGroupCode', 'InventoryUOM', 'ItemType', 'TaxRate', 'ItemManagementMethod', 'ItemCategory', 'MaterialType', 'TaxCategory', 'HSN'],
    warehouse: ['WarehouseName', 'Location', 'Address'],
  };

  const standardFields = ALL_MASTER_FIELDS[workflow.master_type] || [];

  // Collect all unique keys present across all extracted records
  const extractedKeys = new Set<string>();
  records.forEach((r) => {
    if (r) {
      Object.keys(r).forEach((k) => extractedKeys.add(k));
    }
  });

  // Collect any fields identified in validation
  const missingKeys = new Set<string>([
    ...(bulkVal?.missing_fields_summary || []),
    ...(workflow.missing_fields?.map((mf) => mf.field) || []),
  ]);

  // Build the complete unified columns list showing all fields on the table
  const allTableColumns: string[] = [];

  // 1. Primary identifiers and names first
  const primaryKeys =
    workflow.master_type === 'business_partner'
      ? ['CardCode', 'CardName', 'CardType']
      : workflow.master_type === 'item'
      ? ['ItemCode', 'ItemName', 'ItemsGroupCode']
      : ['WarehouseCode', 'WarehouseName', 'Location'];

  primaryKeys.forEach((k) => {
    if (!allTableColumns.includes(k)) allTableColumns.push(k);
  });

  // 2. Any keys that were extracted in the file that are not added yet
  Array.from(extractedKeys).forEach((k) => {
    if (!allTableColumns.includes(k)) allTableColumns.push(k);
  });

  // 3. Remaining standard fields for the master type
  standardFields.forEach((k) => {
    if (!allTableColumns.includes(k)) allTableColumns.push(k);
  });

  // 4. Any other missing keys from validation
  Array.from(missingKeys).forEach((k) => {
    if (!allTableColumns.includes(k)) allTableColumns.push(k);
  });

  // Initialize selected indices to all rows when records load
  useEffect(() => {
    if (records.length > 0 && selectedIndices.size === 0) {
      setSelectedIndices(new Set(records.map((_, i) => i)));
    }
  }, [records.length]);

  // If single record, default active tab to 'fields'
  useEffect(() => {
    if (!hasMultipleRecords) {
      setActiveTab('fields');
    }
  }, [hasMultipleRecords]);

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIndices(new Set(records.map((_, i) => i)));
    } else {
      setSelectedIndices(new Set());
    }
  };

  const handleToggleRow = (idx: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const next = new Set(selectedIndices);
    if (next.has(idx)) {
      next.delete(idx);
    } else {
      next.add(idx);
    }
    setSelectedIndices(next);
  };

  const handleRecordClick = (idx: number) => {
    setSelectedRecordIndex(idx);
    if (onSelectRecord) {
      onSelectRecord(idx);
    }
  };

  const handleToggleExpandRow = (idx: number) => {
    if (expandedRowIndex === idx) {
      setExpandedRowIndex(null);
    } else {
      setExpandedRowIndex(idx);
      // Initialize rowDraft with current values
      const rec = records[idx] || {};
      const currentDraft = rowDrafts[idx] || {};
      const initial: Record<string, any> = { ...rec, ...currentDraft };
      setRowDrafts((prev) => ({ ...prev, [idx]: initial }));
    }
  };

  const handleRowDraftChange = (idx: number, field: string, value: any) => {
    setRowDrafts((prev) => ({
      ...prev,
      [idx]: {
        ...(prev[idx] || {}),
        [field]: value,
      },
    }));
  };

  const handleSaveSingleRowDraft = async (idx: number) => {
    if (!onUpdateRecord) return;
    const draft = rowDrafts[idx] || {};
    setIsSavingRow(true);
    try {
      await onUpdateRecord({
        index: idx,
        updates: draft,
      });
      setExpandedRowIndex(null);
    } catch (e) {
      console.error('Failed to update row', e);
    } finally {
      setIsSavingRow(false);
    }
  };

  // Get per-row validation status helper
  const getRowValidation = (idx: number) => {
    if (!bulkVal || !bulkVal.record_statuses) return null;
    return bulkVal.record_statuses[idx] || null;
  };

  const handleOpenEditModal = (idx: number) => {
    setModalEditIndex(idx);
    const rec = records[idx] || {};
    const currentDraft = rowDrafts[idx] || {};
    const initial: Record<string, any> = { ...rec, ...currentDraft };
    setRowDrafts((prev) => ({ ...prev, [idx]: initial }));
    setModalSearch('');
    const rowVal = getRowValidation(idx);
    const missing = rowVal?.missing_fields || [];
    setModalCategory(missing.length > 0 ? 'MISSING' : 'ALL');
  };

  const handleSaveModalDraft = async (idx: number, advanceToNext: boolean = false) => {
    if (!onUpdateRecord) return;
    const draft = rowDrafts[idx] || {};
    setIsSavingRow(true);
    try {
      await onUpdateRecord({
        index: idx,
        updates: draft,
      });
      setCopyToast(`Row #${idx + 1} updated and re-validated`);
      setTimeout(() => setCopyToast(null), 3000);
      if (advanceToNext && idx < records.length - 1) {
        handleOpenEditModal(idx + 1);
      } else if (!advanceToNext) {
        setModalEditIndex(null);
      }
    } catch (e) {
      console.error('Failed to update row', e);
    } finally {
      setIsSavingRow(false);
    }
  };

  const handleJumpToMissingCell = () => {
    for (let i = 0; i < records.length; i++) {
      const rowVal = getRowValidation(i);
      const missing = rowVal?.missing_fields || [];
      if (missing.length > 0) {
        const firstMissing = missing[0];
        const el = document.getElementById(`inline-cell-${i}-${firstMissing}`);
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
          el.focus();
          return;
        }
      }
    }
    setCopyToast('No missing fields detected in table!');
    setTimeout(() => setCopyToast(null), 2500);
  };

  // Keyboard accessibility for Quick Edit Modal
  useEffect(() => {
    if (modalEditIndex === null) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setModalEditIndex(null);
      } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        handleSaveModalDraft(modalEditIndex, false);
      } else if (e.altKey && e.key === 'ArrowLeft') {
        e.preventDefault();
        if (modalEditIndex > 0) handleOpenEditModal(modalEditIndex - 1);
      } else if (e.altKey && e.key === 'ArrowRight') {
        e.preventDefault();
        if (modalEditIndex < records.length - 1) handleOpenEditModal(modalEditIndex + 1);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [modalEditIndex, records.length, rowDrafts]);


  const handleInlineCellChange = (idx: number, col: string, value: any) => {
    setInlineEdits((prev) => ({
      ...prev,
      [idx]: {
        ...(prev[idx] || {}),
        [col]: value,
      },
    }));
  };

  const handleSaveAllTableEdits = async () => {
    if (!onUpdateRecord) return;
    setIsSavingTableEdits(true);
    try {
      const updatedRecords = records.map((rec, i) => {
        if (inlineEdits[i]) {
          return { ...rec, ...inlineEdits[i] };
        }
        return rec;
      });
      await onUpdateRecord({
        records: updatedRecords,
      });
      setInlineEdits({});
    } catch (e) {
      console.error('Failed to save table edits', e);
    } finally {
      setIsSavingTableEdits(false);
    }
  };

  const getRowEditableFields = (rec: Record<string, any>, rowVal: any) => {
    const standardDefs = defaultMandatoryByMaster[workflow.master_type] || [];
    const missingKeys = new Set(rowVal?.missing_fields || []);
    const allKeys = Array.from(new Set([...Object.keys(rec), ...standardDefs]));
    return allKeys.sort((a, b) => {
      const aMissing = missingKeys.has(a);
      const bMissing = missingKeys.has(b);
      if (aMissing && !bMissing) return -1;
      if (!aMissing && bMissing) return 1;
      return 0;
    });
  };

  const handleApplyDefaultsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!onApplyDefaults) return;
    setIsApplyingDefaults(true);
    try {
      const defaults: Record<string, any> = {};
      if (workflow.master_type === 'business_partner') {
        if (cardTypeDefault) defaults.CardType = cardTypeDefault;
        if (cardNamePrefixDefault) defaults.CardNamePrefix = cardNamePrefixDefault;
        if (emailDefault) defaults.EmailAddress = emailDefault;
      } else if (workflow.master_type === 'item') {
        if (itemsGroupCodeDefault !== '') defaults.ItemsGroupCode = itemsGroupCodeDefault;
      }
      await onApplyDefaults(defaults);
      setIsDefaultsModalOpen(false);
    } catch (err) {
      console.error('Failed to apply batch defaults', err);
    } finally {
      setIsApplyingDefaults(false);
    }
  };


  const getViewerMissingFields = (rec: Record<string, any>, rowIdx: number): string[] => {
    const effectiveRec = inlineEdits[rowIdx] ? { ...rec, ...inlineEdits[rowIdx] } : rec;
    const mandatoryFields =
      workflow.master_type === 'item'
        ? ['ItemCode', 'ItemName']
        : workflow.master_type === 'warehouse'
        ? ['WarehouseCode']
        : ['CardCode', 'CardName', 'CardType'];

    return mandatoryFields.filter((field) => {
      const val = effectiveRec[field];
      if (field === 'ItemType' && (effectiveRec.InventoryItem || effectiveRec.SalesItem || effectiveRec.PurchaseItem)) {
        return false;
      }
      if (field === 'ItemManagementMethod' && (effectiveRec.ManageSerialNumbers || effectiveRec.ManageBatchNumbers)) {
        return false;
      }
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
      if (field === 'PANNo') {
        const gst = String(effectiveRec.GSTNo || effectiveRec.FederalTaxID || '').trim().toUpperCase();
        if (gst.length === 15 && /^\d{2}[A-Z0-9]{10}/.test(gst)) {
          return false;
        }
      }

      return val === undefined || val === null || String(val).trim() === '';
    });
  };

  // Filter records in multi-record view
  const filteredRecords = records
    .map((rec, idx) => {
      const rowVal = getRowValidation(idx);
      const missing = getViewerMissingFields(rec, idx);
      const isRecordValid = rowVal ? rowVal.valid && missing.length === 0 : missing.length === 0;
      return { rec, idx, rowVal, missing, isRecordValid };
    })
    .filter(({ rec, isRecordValid }) => {
      // Status filter
      if (statusFilter === 'VALID' && !isRecordValid) return false;
      if (statusFilter === 'INVALID' && isRecordValid) return false;

      // Keyword search
      if (!searchFilter.trim()) return true;
      const q = searchFilter.toLowerCase();
      return Object.values(rec).some((val) => String(val).toLowerCase().includes(q));
    });

  const recordValidationList = records.map((rec, idx) => {
    const rowVal = getRowValidation(idx);
    const missing = getViewerMissingFields(rec, idx);
    return rowVal ? rowVal.valid && missing.length === 0 : missing.length === 0;
  });
  const validCount = recordValidationList.filter(Boolean).length;
  const invalidCount = recordValidationList.length - validCount;

  const [copyToast, setCopyToast] = useState<string | null>(null);

  // Validation functions for copied Item Number and Date
  const validateItemCode = (code: any) => {
    if (!code || !String(code).trim()) {
      return { valid: false, message: 'Item number is missing' };
    }
    const clean = String(code).trim();
    if (clean.length > 50) {
      return { valid: false, message: 'Exceeds SAP max length (50 chars)' };
    }
    if (!/^[A-Za-z0-9_\-\.\/]+$/.test(clean)) {
      return { valid: false, message: 'Invalid SAP characters (letters/digits/-/_ only)' };
    }
    return { valid: true, message: 'Valid SAP ItemCode format' };
  };

  const validateDate = (dateStr: any) => {
    if (!dateStr || !String(dateStr).trim()) {
      return { valid: false, message: 'Date is missing' };
    }
    const clean = String(dateStr).trim();
    const d = new Date(clean);
    if (isNaN(d.getTime())) {
      return { valid: false, message: 'Invalid date format (Use YYYY-MM-DD)' };
    }
    const isoDate = d.toISOString().slice(0, 10);
    return { valid: true, message: `Valid Date (${isoDate})`, iso: isoDate };
  };

  const isUdf = (key: string) => {
    return (
      key.startsWith('U_') ||
      key.startsWith('u_') ||
      (!standardFields.includes(key) &&
        !['CreateDate', 'DocDate', 'UpdateDate', '_simulated', 'Index', 'CreationDate'].includes(key))
    );
  };

  const handleCopyValue = async (text: string, label: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopyToast(`Copied ${label}: ${text}`);
      setTimeout(() => setCopyToast(null), 3000);
      api.logUserAction({
        workflow_id: workflow.workflow_id,
        master_type: workflow.master_type,
        action: 'COPY',
        activity: 'COPY_VALUE',
        details: `User copied ${label}: '${text}' to clipboard`,
        updated_value: text,
      });
    } catch (e) {
      console.warn('Clipboard error:', e);
    }
  };

  const handleCopyDateAndItem = async (itemCode: string, dateStr: string, idx?: number) => {
    const itemVal = validateItemCode(itemCode);
    const dateVal = validateDate(dateStr);
    const copyText = `Item Code: ${itemCode} | Date: ${dateVal.iso || dateStr}`;
    try {
      await navigator.clipboard.writeText(copyText);
      setCopyToast(`Copied Item #${itemCode} & Date ${dateVal.iso || dateStr}`);
      setTimeout(() => setCopyToast(null), 3500);

      api.logUserAction({
        workflow_id: workflow.workflow_id,
        master_type: workflow.master_type,
        action: 'COPY',
        activity: 'COPY_DATE_AND_ITEM',
        transaction_num: itemCode,
        previous_value: `Row ${idx !== undefined ? idx + 1 : 'Active'}`,
        updated_value: copyText,
        details: `Copied Date & Item # for Row ${idx !== undefined ? idx + 1 : 'Active'}: Item=${itemCode} Date=${dateVal.iso || dateStr} (ValidItem: ${itemVal.valid}, ValidDate: ${dateVal.valid})`,
      });
    } catch (e) {
      console.warn('Clipboard error:', e);
    }
  };

  const handleTransferToActive = async (sourceItemCode: string, sourceDate: string) => {
    if (!onUpdateRecord) return;
    const activeIdx = selectedRecordIndex;
    const targetRec = records[activeIdx] || {};
    const prevVal = JSON.stringify({
      ItemCode: targetRec.ItemCode || targetRec.CardCode || '',
      CreateDate: targetRec.CreateDate || targetRec.DocDate || '',
    });

    const updates: Record<string, any> = {};
    if (workflow.master_type === 'item') {
      updates.ItemCode = sourceItemCode;
      updates.CreateDate = sourceDate;
    } else if (workflow.master_type === 'business_partner') {
      updates.CardCode = sourceItemCode;
      updates.CreateDate = sourceDate;
    } else {
      updates.WarehouseCode = sourceItemCode;
    }

    try {
      await onUpdateRecord({
        index: activeIdx,
        updates,
      });
      setCopyToast(`Transferred Item #${sourceItemCode} & Date to Row #${activeIdx + 1}`);
      setTimeout(() => setCopyToast(null), 3500);

      api.logUserAction({
        workflow_id: workflow.workflow_id,
        master_type: workflow.master_type,
        action: 'TRANSFER',
        activity: 'TRANSFER_DATE_AND_ITEM',
        transaction_num: sourceItemCode,
        previous_value: prevVal,
        updated_value: JSON.stringify(updates),
        details: `Transferred Date & Item # into Row #${activeIdx + 1} (${workflow.master_type})`,
      });
    } catch (e) {
      console.error('Transfer error:', e);
    }
  };

  return (
    <div className="glass-panel" style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Toast Notification for Clipboard Copy */}
      {copyToast && (
        <div
          style={{
            padding: '8px 16px',
            borderRadius: 'var(--radius-md)',
            background: '#047857',
            color: '#FFFFFF',
            fontSize: 12,
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 4px 12px rgba(4, 120, 87, 0.3)',
            animation: 'fadeIn 0.2s ease',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <CheckCircle2 size={16} />
            <span>{copyToast}</span>
          </div>
          <button
            onClick={() => setCopyToast(null)}
            style={{ background: 'none', border: 'none', color: '#FFFFFF', cursor: 'pointer' }}
          >
            <X size={14} />
          </button>
        </div>
      )}

      {/* Header Banner */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 14 }}>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div
            style={{
              width: 42,
              height: 42,
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.25) 0%, rgba(139, 92, 246, 0.25) 100%)',
              border: '1px solid rgba(139, 92, 246, 0.4)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Database size={22} color="#A78BFA" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <h3 style={{ fontSize: 17, fontWeight: 700, color: 'var(--md-text-primary, #0F172A)' }}>Extracted Master Data</h3>
              <span
                style={{
                  fontSize: 11,
                  padding: '2px 8px',
                  borderRadius: 12,
                  background: 'rgba(59, 130, 246, 0.12)',
                  border: '1px solid rgba(59, 130, 246, 0.25)',
                  color: '#2563EB',
                  fontWeight: 600,
                  textTransform: 'capitalize',
                }}
              >
                {workflow.master_type.replace('_', ' ')} Master
              </span>
              {hasMultipleRecords && (
                <span
                  style={{
                    fontSize: 11,
                    padding: '2px 8px',
                    borderRadius: 12,
                    background: '#DCFCE7',
                    border: '1px solid #BBF7D0',
                    color: '#166534',
                    fontWeight: 600,
                  }}
                >
                  {records.length} Records Detected
                </span>
              )}
            </div>
            <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
              Extracted from <strong>{workflow.filename || 'uploaded file'}</strong> with multi-engine consensus verification
            </p>
          </div>
        </div>

        {/* Quick Copy Date & Item Number Toolbar */}
      {(() => {
        const activeRec = records[selectedRecordIndex] || activeData || {};
        const sourceItemCode = activeRec.ItemCode || activeRec.CardCode || activeRec.WarehouseCode || '';
        const sourceDate = activeRec.CreateDate || activeRec.DocDate || (workflow.created_at ? workflow.created_at.slice(0, 10) : new Date().toISOString().slice(0, 10));
        const itemVal = validateItemCode(sourceItemCode);
        const dateVal = validateDate(sourceDate);

        return (
          <div
            style={{
              padding: '10px 14px',
              borderRadius: 'var(--radius-md)',
              background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: 12,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <ClipboardCopy size={15} color="#60A5FA" />
                <span style={{ fontSize: 12, fontWeight: 700, color: '#F1F5F9' }}>
                  Quick Copy Date &amp; Item #:
                </span>
              </div>

              {/* Item Code Pill */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#0F172A', padding: '3px 8px', borderRadius: 6, border: '1px solid #334155' }}>
                <Hash size={12} color="#38BDF8" />
                <span style={{ fontSize: 11, color: '#94A3B8' }}>Code:</span>
                <strong style={{ fontSize: 11.5, color: '#60A5FA', fontFamily: 'monospace' }}>
                  {sourceItemCode || 'N/A'}
                </strong>
                <span style={{
                  fontSize: 9,
                  padding: '1px 5px',
                  borderRadius: 3,
                  background: itemVal.valid ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  color: itemVal.valid ? '#34D399' : '#F87171',
                  fontWeight: 600,
                  border: `1px solid ${itemVal.valid ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
                }}>
                  {itemVal.valid ? 'Valid Code' : itemVal.message}
                </span>
              </div>

              {/* Date Pill */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, background: '#0F172A', padding: '3px 8px', borderRadius: 6, border: '1px solid #334155' }}>
                <Calendar size={12} color="#A78BFA" />
                <span style={{ fontSize: 11, color: '#94A3B8' }}>Date:</span>
                <strong style={{ fontSize: 11.5, color: '#C4B5FD', fontFamily: 'monospace' }}>
                  {dateVal.iso || sourceDate}
                </strong>
                <span style={{
                  fontSize: 9,
                  padding: '1px 5px',
                  borderRadius: 3,
                  background: dateVal.valid ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  color: dateVal.valid ? '#34D399' : '#F87171',
                  fontWeight: 600,
                  border: `1px solid ${dateVal.valid ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
                }}>
                  {dateVal.valid ? 'Valid Date' : dateVal.message}
                </span>
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
              <button
                type="button"
                onClick={() => handleCopyValue(sourceItemCode, 'Item Number')}
                disabled={!sourceItemCode}
                className="btn btn-secondary"
                style={{ padding: '4px 9px', fontSize: 11, display: 'flex', alignItems: 'center', gap: 4 }}
                title="Copy Item Number to clipboard"
              >
                <Copy size={11} /> Copy Code
              </button>

              <button
                type="button"
                onClick={() => handleCopyValue(dateVal.iso || sourceDate, 'Date')}
                disabled={!sourceDate}
                className="btn btn-secondary"
                style={{ padding: '4px 9px', fontSize: 11, display: 'flex', alignItems: 'center', gap: 4 }}
                title="Copy Date to clipboard"
              >
                <Copy size={11} /> Copy Date
              </button>

              <button
                type="button"
                onClick={() => handleCopyDateAndItem(sourceItemCode, sourceDate, selectedRecordIndex)}
                disabled={!sourceItemCode && !sourceDate}
                className="btn btn-primary"
                style={{ padding: '4px 11px', fontSize: 11, display: 'flex', alignItems: 'center', gap: 4 }}
                title="Copy both Date & Item Number to clipboard and record audit event"
              >
                <ClipboardCopy size={11} /> Copy Both
              </button>
            </div>
          </div>
        );
      })()}

      {/* Tab Navigation */}
      <div style={{ display: 'flex', gap: 6, background: '#F1F5F9', padding: 4, borderRadius: 'var(--radius-md)', border: '1px solid #E2E8F0' }}>
        {hasMultipleRecords && (
          <button
            type="button"
            onClick={() => setActiveTab('records')}
            className={`btn ${activeTab === 'records' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ padding: '6px 14px', fontSize: 12 }}
          >
            <Database size={14} /> All Records ({records.length})
          </button>
        )}
        <button
          type="button"
          onClick={() => setActiveTab('fields')}
          className={`btn ${activeTab === 'fields' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ padding: '6px 14px', fontSize: 12 }}
        >
          <FileText size={14} /> Active Record Fields ({allTableColumns.length})
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('engines')}
          className={`btn ${activeTab === 'engines' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ padding: '6px 14px', fontSize: 12 }}
        >
          <Code2 size={14} /> 3-Engine Inspector
        </button>
      </div>
      </div>

      {/* Tab 1: All Records Table (Spreadsheets with multiple entries) */}
      {activeTab === 'records' && hasMultipleRecords && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Batch Actions & Controls Bar */}
          <div
            style={{
              padding: '12px 16px',
              background: '#F8FAFC',
              borderRadius: 'var(--radius-md)',
              border: '1px solid #E2E8F0',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: 12,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 12, fontWeight: 600, color: '#0F172A' }}>
                <input
                  type="checkbox"
                  checked={selectedIndices.size === records.length && records.length > 0}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                  style={{ width: 16, height: 16, accentColor: '#2563EB', cursor: 'pointer' }}
                />
                <span>Select All ({selectedIndices.size}/{records.length})</span>
              </label>

              {/* Status Filters */}
              <div style={{ display: 'flex', gap: 4, background: '#E2E8F0', padding: 2, borderRadius: 'var(--radius-sm)' }}>
                <button
                  type="button"
                  onClick={() => setStatusFilter('ALL')}
                  className={`btn ${statusFilter === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{ padding: '3px 10px', fontSize: 11 }}
                >
                  All ({records.length})
                </button>
                <button
                  type="button"
                  onClick={() => setStatusFilter('VALID')}
                  className={`btn ${statusFilter === 'VALID' ? 'btn-primary' : 'btn-secondary'}`}
                  style={{
                    padding: '3px 10px',
                    fontSize: 11,
                    color: statusFilter === 'VALID' ? '#FFFFFF' : '#15803D',
                    fontWeight: 600,
                    background: statusFilter === 'VALID' ? '#16A34A' : '#F0FDF4',
                    borderColor: '#86EFAC',
                  }}
                >
                  Valid ({validCount})
                </button>
                {invalidCount > 0 && (
                  <button
                    type="button"
                    onClick={() => setStatusFilter('INVALID')}
                    className={`btn ${statusFilter === 'INVALID' ? 'btn-primary' : 'btn-secondary'}`}
                    style={{
                      padding: '3px 10px',
                      fontSize: 11,
                      color: statusFilter === 'INVALID' ? '#FFFFFF' : '#DC2626',
                      fontWeight: 600,
                      background: statusFilter === 'INVALID' ? '#DC2626' : '#FEF2F2',
                      borderColor: '#FCA5A5',
                    }}
                  >
                    Mandatory Field Required ({invalidCount})
                  </button>
                )}
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              {/* Batch Defaults Button */}
              {onApplyDefaults && invalidCount > 0 && (
                <button
                  type="button"
                  onClick={() => setIsDefaultsModalOpen(true)}
                  className="btn btn-secondary"
                  style={{
                    padding: '6px 12px',
                    fontSize: 12,
                    background: '#FEF2F2',
                    border: '1px solid #FCA5A5',
                    color: '#DC2626',
                    fontWeight: 600,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <Wand2 size={13} color="#DC2626" /> Batch Enrich / Fill Missing Fields
                </button>
              )}

              {/* Toggle Inline Spreadsheet Edit Mode */}
              {onUpdateRecord && (
                <button
                  type="button"
                  onClick={() => setIsTableEditMode((prev) => !prev)}
                  className={`btn ${isTableEditMode ? 'btn-primary' : 'btn-secondary'}`}
                  style={{
                    padding: '6px 12px',
                    fontSize: 12,
                    fontWeight: 600,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    background: isTableEditMode ? '#2563EB' : '#F8FAFC',
                    color: isTableEditMode ? '#FFFFFF' : '#334155',
                    border: isTableEditMode ? '1px solid #1D4ED8' : '1px solid #CBD5E1',
                  }}
                  title="Toggle inline cell editing directly across all table columns"
                >
                  <Edit3 size={13} /> {isTableEditMode ? 'Exit Table Edit Mode' : 'Edit in Table (Spreadsheet)'}
                </button>
              )}

              {/* Quick Jump to Missing Cell button in Table Edit Mode */}
              {isTableEditMode && onUpdateRecord && (
                <button
                  type="button"
                  onClick={handleJumpToMissingCell}
                  className="btn btn-secondary"
                  style={{
                    padding: '6px 12px',
                    fontSize: 12,
                    fontWeight: 600,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                    background: '#FFFBEB',
                    color: '#B45309',
                    border: '1px solid #FCD34D',
                  }}
                  title="Automatically scroll to the next missing cell needing attention"
                >
                  <AlertTriangle size={13} color="#D97706" /> Jump to Missing Cell
                </button>
              )}

              {/* Quick Bulk Create in SAP button */}
              {onBulkCreate && (
                <button
                  type="button"
                  onClick={() => onBulkCreate(Array.from(selectedIndices))}
                  disabled={selectedIndices.size === 0}
                  className="btn btn-success"
                  style={{
                    padding: '6px 16px',
                    fontSize: 12,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <ShieldCheck size={14} /> Bulk Create in SAP ({selectedIndices.size})
                </button>
              )}

              {/* Search Filter */}
              <div style={{ position: 'relative', minWidth: 180 }}>
                <Search size={13} color="#64748B" style={{ position: 'absolute', left: 8, top: '50%', transform: 'translateY(-50%)' }} />
                <input
                  type="text"
                  className="form-input"
                  placeholder="Filter rows..."
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  style={{ paddingLeft: 26, fontSize: 11, height: 28 }}
                />
              </div>
            </div>
          </div>

          {/* Unsaved Table Changes Bar */}
          {Object.keys(inlineEdits).length > 0 && (
            <div
              style={{
                background: '#FEF3C7',
                border: '1px solid #FDE68A',
                borderRadius: 'var(--radius-md)',
                padding: '10px 16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <AlertTriangle size={15} color="#D97706" />
                <span style={{ fontSize: 12, fontWeight: 700, color: '#92400E' }}>
                  You have unsaved edits in {Object.keys(inlineEdits).length} row(s).
                </span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <button
                  type="button"
                  onClick={() => setInlineEdits({})}
                  className="btn btn-secondary"
                  style={{ fontSize: 11, padding: '4px 10px' }}
                >
                  Discard
                </button>
                <button
                  type="button"
                  onClick={handleSaveAllTableEdits}
                  disabled={isSavingTableEdits}
                  className="btn btn-primary"
                  style={{ fontSize: 11, padding: '4px 14px', display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  <Save size={13} /> {isSavingTableEdits ? 'Saving...' : 'Save All Table Changes'}
                </button>
              </div>
            </div>
          )}

          {/* Records Table */}
          <div
            style={{
              background: '#FFFFFF',
              borderRadius: 'var(--radius-md)',
              border: '1px solid #E2E8F0',
              overflowX: 'auto',
              maxHeight: 440,
            }}
          >
            <table className="data-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
              <thead>
                <tr>
                  <th style={{ width: 40, textAlign: 'center', position: 'sticky', left: 0, zIndex: 12, background: '#F8FAFC' }}>
                    <input
                      type="checkbox"
                      checked={selectedIndices.size === records.length && records.length > 0}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                      style={{ width: 14, height: 14, accentColor: '#2563EB', cursor: 'pointer' }}
                    />
                  </th>
                  <th style={{ width: 45, position: 'sticky', left: 40, zIndex: 12, background: '#F8FAFC' }}>#</th>
                  <th style={{ minWidth: 175, width: 175, position: 'sticky', left: 85, zIndex: 12, background: '#F8FAFC', borderRight: '1px solid #E2E8F0' }}>Validation</th>
                  {allTableColumns.map((colKey) => {
                    const udf = isUdf(colKey);
                    return (
                      <th
                        key={colKey}
                        style={{
                          whiteSpace: 'nowrap',
                          color: udf ? '#7E22CE' : '#334155',
                          fontWeight: 600,
                          fontSize: 12,
                        }}
                        title={FIELD_FRIENDLY_LABELS[colKey] || colKey}
                      >
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                          <span>{colKey}</span>
                          {udf && (
                            <span
                              style={{
                                fontSize: 9,
                                fontWeight: 700,
                                padding: '1px 4px',
                                borderRadius: 3,
                                background: '#F3E8FF',
                                color: '#7E22CE',
                                border: '1px solid #E9D5FF',
                              }}
                              title="User-Defined Field (UDF) automatically carried forward"
                            >
                              UDF
                            </span>
                          )}
                        </div>
                      </th>
                    );
                  })}
                  <th style={{ width: 190, textAlign: 'right', position: 'sticky', right: 0, zIndex: 12, background: '#F8FAFC', borderLeft: '1px solid #E2E8F0', boxShadow: '-6px 0 12px rgba(0, 0, 0, 0.05)' }}>Actions</th>
                </tr>
              </thead>

              <tbody>
                {filteredRecords.map(({ rec, idx, rowVal, missing, isRecordValid }) => {
                  const isRowActive = selectedRecordIndex === idx;
                  const isChecked = selectedIndices.has(idx);
                  const isValid = isRecordValid;
                  const rowBg = isRowActive ? '#EFF6FF' : '#FFFFFF';

                  return (
                    <React.Fragment key={idx}>
                      <tr
                        style={{
                          background: rowBg,
                          cursor: 'pointer',
                        }}
                        onClick={() => handleRecordClick(idx)}
                      >
                        <td style={{ textAlign: 'center', position: 'sticky', left: 0, zIndex: 10, background: rowBg }} onClick={(e) => handleToggleRow(idx, e)}>
                          <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={() => {}}
                            style={{ width: 14, height: 14, accentColor: '#2563EB', cursor: 'pointer' }}
                          />
                        </td>
                        <td style={{ fontWeight: 600, color: isRowActive ? '#2563EB' : '#64748B', position: 'sticky', left: 40, zIndex: 10, background: rowBg }}>
                          {idx + 1}
                        </td>
                        <td style={{ position: 'sticky', left: 85, zIndex: 10, background: rowBg, borderRight: '1px solid #E2E8F0' }}>
                          {isRecordValid ? (
                            <span
                              style={{
                                padding: '3px 8px',
                                borderRadius: 8,
                                background: '#DCFCE7',
                                color: '#15803D',
                                border: '1px solid #86EFAC',
                                fontSize: 11,
                                fontWeight: 700,
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: 4,
                                whiteSpace: 'nowrap',
                              }}
                              title="All mandatory SAP fields are complete."
                            >
                              <CheckCircle2 size={11} /> Mandatory Passed
                            </span>
                          ) : (
                            <span
                              style={{
                                padding: '3px 8px',
                                borderRadius: 8,
                                background: '#FEE2E2',
                                color: '#DC2626',
                                border: '1px solid #FCA5A5',
                                fontSize: 11,
                                fontWeight: 700,
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: 4,
                                whiteSpace: 'nowrap',
                              }}
                              title={`Missing mandatory fields: ${missing.join(', ')}`}
                            >
                              <AlertTriangle size={11} /> Mandatory Field Required ({missing.length})
                            </span>
                          )}
                        </td>
                        {/* All fields rendered directly on the table */}
                        {allTableColumns.map((colKey) => {
                          const cellVal = inlineEdits[idx]?.[colKey] ?? rec[colKey];
                          const hasEntry = cellVal !== undefined && cellVal !== null && String(cellVal).trim() !== '';
                          const isEdited = inlineEdits[idx]?.[colKey] !== undefined;
                          const enumOpts = ENUM_OPTIONS[colKey];

                          // When table edit mode is active, render inline cell inputs directly
                          if (isTableEditMode) {
                            return (
                              <td
                                key={colKey}
                                style={{
                                  background: isEdited ? '#FEF3C7' : '#FFFFFF',
                                  padding: '4px 6px',
                                  minWidth: 110,
                                }}
                                onClick={(e) => e.stopPropagation()}
                              >
                                {enumOpts ? (
                                  <select
                                    id={`inline-cell-${idx}-${colKey}`}
                                    className="form-input"
                                    value={cellVal ?? ''}
                                    onChange={(e) => handleInlineCellChange(idx, colKey, e.target.value)}
                                    style={{
                                      fontSize: 11,
                                      padding: '2px 4px',
                                      height: 26,
                                      width: '100%',
                                      borderRadius: 4,
                                      borderColor: isEdited ? '#D97706' : '#CBD5E1',
                                      background: isEdited ? '#FFFBEB' : '#FFFFFF',
                                      fontWeight: cellVal ? 600 : 400,
                                    }}
                                  >
                                    <option value="">--</option>
                                    {enumOpts.map((opt) => (
                                      <option key={opt.value} value={opt.value}>
                                        {opt.value}
                                      </option>
                                    ))}
                                  </select>
                                ) : (
                                  <input
                                    id={`inline-cell-${idx}-${colKey}`}
                                    type={colKey.toLowerCase().includes('email') ? 'email' : 'text'}
                                    className="form-input"
                                    value={cellVal ?? ''}
                                    placeholder="—"
                                    onChange={(e) => handleInlineCellChange(idx, colKey, e.target.value)}
                                    style={{
                                      fontSize: 11,
                                      padding: '2px 6px',
                                      height: 26,
                                      width: '100%',
                                      minWidth: 90,
                                      borderRadius: 4,
                                      borderColor: isEdited ? '#D97706' : '#CBD5E1',
                                      background: isEdited ? '#FFFBEB' : '#FFFFFF',
                                    }}
                                  />
                                )}
                              </td>
                            );
                          }

                          // Standard view mode: formatted value or dash '—' if empty
                          return (
                            <td
                              key={colKey}
                              style={{
                                color: isRowActive ? '#1E3A8A' : '#0F172A',
                                fontWeight: isRowActive && hasEntry ? 600 : 400,
                                whiteSpace: 'nowrap',
                                minWidth: 90,
                              }}
                            >
                              {hasEntry ? (
                                typeof cellVal === 'boolean' ? (
                                  cellVal ? 'Yes' : 'No'
                                ) : (
                                  String(cellVal)
                                )
                              ) : (
                                <span style={{ color: '#94A3B8', fontWeight: 500, fontSize: 13 }}>
                                  —
                                </span>
                              )}
                            </td>
                          );
                        })}

                        <td
                          style={{
                            textAlign: 'right',
                            whiteSpace: 'nowrap',
                            position: 'sticky',
                            right: 0,
                            zIndex: 10,
                            background: rowBg,
                            borderLeft: '1px solid #E2E8F0',
                            boxShadow: '-6px 0 12px rgba(0, 0, 0, 0.05)',
                            padding: '6px 10px',
                          }}
                        >
                          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
                            {/* Copy Date & Item button */}
                            {(() => {
                              const rCode = rec.ItemCode || rec.CardCode || rec.WarehouseCode || '';
                              const rDate = rec.CreateDate || rec.DocDate || (workflow.created_at ? workflow.created_at.slice(0, 10) : '');
                              return (
                                <>
                                  <button
                                    type="button"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleCopyDateAndItem(rCode, rDate, idx);
                                    }}
                                    className="btn btn-secondary"
                                    style={{ padding: '3px 7px', fontSize: 11, background: '#F1F5F9', border: '1px solid #CBD5E1' }}
                                    title={`Copy Item #${rCode} and Date (${rDate}) for this row`}
                                  >
                                    <Copy size={11} /> Copy
                                  </button>
                                  {onUpdateRecord && idx !== selectedRecordIndex && (
                                    <button
                                      type="button"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleTransferToActive(rCode, rDate);
                                      }}
                                      className="btn btn-secondary"
                                      style={{ padding: '3px 7px', fontSize: 11, background: '#EFF6FF', border: '1px solid #BFDBFE', color: '#1D4ED8' }}
                                      title={`Transfer this row's Code & Date into active Row #${selectedRecordIndex + 1}`}
                                    >
                                      <ArrowRightLeft size={11} /> Transfer
                                    </button>
                                  )}
                                </>
                              );
                            })()}

                            {onUpdateRecord && (
                              <div style={{ display: 'inline-flex', alignItems: 'center', gap: 2 }}>
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleOpenEditModal(idx);
                                  }}
                                  className="btn btn-secondary"
                                  style={{
                                    padding: '3px 9px',
                                    fontSize: 11,
                                    background: isValid ? '#F0FDF4' : '#FFFBEB',
                                    border: isValid ? '1px solid #BBF7D0' : '1px solid #FDE68A',
                                    color: isValid ? '#166534' : '#92400E',
                                    fontWeight: 600,
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    gap: 4,
                                  }}
                                  title="Open Quick Focused Edit Modal (Zero horizontal scroll)"
                                >
                                  <Edit3 size={11} /> Edit
                                </button>
                                <button
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleToggleExpandRow(idx);
                                  }}
                                  style={{
                                    background: expandedRowIndex === idx ? '#E2E8F0' : 'transparent',
                                    border: '1px solid transparent',
                                    color: '#64748B',
                                    cursor: 'pointer',
                                    padding: '3px 4px',
                                    borderRadius: 4,
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                  }}
                                  title={expandedRowIndex === idx ? "Collapse inline preview" : "Expand inline preview"}
                                >
                                  <ChevronDown size={13} style={{ transform: expandedRowIndex === idx ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s' }} />
                                </button>
                              </div>
                            )}
                            <button
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleRecordClick(idx);
                              }}
                              className={`btn ${isRowActive ? 'btn-primary' : 'btn-secondary'}`}
                              style={{ padding: '3px 10px', fontSize: 11 }}
                            >
                              {isRowActive ? (
                                <>
                                  <Check size={12} /> Active
                                </>
                              ) : (
                                'Select'
                              )}
                            </button>
                          </div>
                        </td>
                      </tr>

                      {/* Expandable Editable Fields (Viewport Sticky & 2-Column Compact Grid) */}
                      {expandedRowIndex === idx && (
                        <tr style={{ background: isValid ? '#F0FDF4' : '#FFFDF5' }}>
                          <td
                            colSpan={4 + allTableColumns.length}
                            style={{
                              padding: '16px 20px',
                              borderBottom: isValid ? '2px solid #86EFAC' : '2px solid #FCD34D',
                            }}
                          >
                            <div
                              style={{
                                position: 'sticky',
                                left: 24,
                                width: 'fit-content',
                                maxWidth: 'min(980px, calc(100vw - 260px))',
                                background: '#FFFFFF',
                                border: isValid ? '1.5px solid #10B981' : '1.5px solid #F59E0B',
                                borderRadius: 'var(--radius-md)',
                                padding: 18,
                                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.12)',
                              }}
                            >
                              <div
                                style={{
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'space-between',
                                  marginBottom: 14,
                                  flexWrap: 'wrap',
                                  gap: 8,
                                }}
                              >
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                                  {isValid ? (
                                    <CheckCircle2 size={16} color="#16A34A" />
                                  ) : (
                                    <AlertTriangle size={16} color="#DC2626" />
                                  )}
                                  <strong
                                    style={{
                                      fontSize: 13,
                                      color: isValid ? '#166534' : '#991B1B',
                                    }}
                                  >
                                    {isValid ? 'Edit Valid Entry' : 'Fill Missing & Edit Fields'} - Row #{idx + 1}
                                    {rec.CardCode ? ` (${rec.CardCode})` : ''}
                                    {rec.ItemCode ? ` (${rec.ItemCode})` : ''}
                                  </strong>
                                  <span
                                    style={{
                                      fontSize: 11,
                                      padding: '2px 8px',
                                      borderRadius: 10,
                                      background: isValid ? '#DCFCE7' : '#FEE2E2',
                                      color: isValid ? '#15803D' : '#DC2626',
                                      border: isValid ? '1px solid #86EFAC' : '1px solid #FCA5A5',
                                      fontWeight: 700,
                                    }}
                                  >
                                    {isValid ? 'Valid Entry' : `${rowVal?.missing_fields?.length || 0} Mandatory Field${(rowVal?.missing_fields?.length || 0) > 1 ? 's' : ''} Required`}
                                  </span>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                  <button
                                    type="button"
                                    onClick={() => handleOpenEditModal(idx)}
                                    className="btn btn-secondary"
                                    style={{ padding: '3px 8px', fontSize: 11, display: 'inline-flex', alignItems: 'center', gap: 4 }}
                                    title="Open in Focused Full Modal"
                                  >
                                    <Maximize2 size={11} /> Open in Modal
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => setExpandedRowIndex(null)}
                                    style={{
                                      background: 'transparent',
                                      border: 'none',
                                      color: '#64748B',
                                      cursor: 'pointer',
                                      padding: 4,
                                    }}
                                  >
                                    <X size={15} />
                                  </button>
                                </div>
                              </div>

                              {/* 2-Column Compact Grid of fields (Minimum Scroll!) */}
                              <div
                                style={{
                                  display: 'grid',
                                  gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                                  gap: 10,
                                  maxHeight: 380,
                                  overflowY: 'auto',
                                  paddingRight: 4,
                                  marginBottom: 14,
                                }}
                              >
                                {getRowEditableFields(rec, rowVal).map((fieldKey) => {
                                  const label = FIELD_FRIENDLY_LABELS[fieldKey] || fieldKey;
                                  const currentVal = rowDrafts[idx]?.[fieldKey] ?? rec[fieldKey] ?? '';
                                  const enumOpts = ENUM_OPTIONS[fieldKey];
                                  const isMissing = (rowVal?.missing_fields || []).includes(fieldKey);
                                  const isFilled = String(currentVal).trim() !== '';

                                  return (
                                    <div
                                      key={fieldKey}
                                      style={{
                                        background: isMissing ? '#FEF2F2' : '#F8FAFC',
                                        border: isMissing ? '1.5px solid #FCA5A5' : '1px solid #E2E8F0',
                                        borderRadius: 8,
                                        padding: '8px 10px',
                                        display: 'flex',
                                        flexDirection: 'column',
                                        gap: 4,
                                      }}
                                    >
                                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 4 }}>
                                        <span style={{ fontSize: 11, fontWeight: 700, color: '#0F172A' }}>{label}</span>
                                        {isMissing ? (
                                          <span style={{ fontSize: 9, background: '#FEE2E2', color: '#DC2626', padding: '1px 5px', borderRadius: 3, fontWeight: 700 }}>* Required</span>
                                        ) : isFilled ? (
                                          <span style={{ fontSize: 9, color: '#16A34A', fontWeight: 600 }}>✓ Valid</span>
                                        ) : null}
                                      </div>
                                      <code style={{ fontSize: 9.5, color: '#2563EB', background: '#EFF6FF', padding: '1px 4px', borderRadius: 3, width: 'fit-content' }}>
                                        {fieldKey}
                                      </code>
                                      {enumOpts ? (
                                        <select
                                          className="form-input"
                                          value={currentVal}
                                          onChange={(e) =>
                                            handleRowDraftChange(idx, fieldKey, e.target.value)
                                          }
                                          style={{ fontSize: 12, height: 30, padding: '2px 6px', marginTop: 2 }}
                                        >
                                          <option value="">-- Select {fieldKey} --</option>
                                          {enumOpts.map((opt) => (
                                            <option key={opt.value} value={opt.value}>
                                              {opt.label}
                                            </option>
                                          ))}
                                        </select>
                                      ) : (
                                        <input
                                          type={
                                            fieldKey.toLowerCase().includes('email')
                                              ? 'email'
                                              : fieldKey === 'ItemsGroupCode' || fieldKey === 'Location'
                                              ? 'number'
                                              : 'text'
                                          }
                                          className="form-input"
                                          value={currentVal}
                                          placeholder={`Enter ${label}...`}
                                          onChange={(e) =>
                                            handleRowDraftChange(idx, fieldKey, e.target.value)
                                          }
                                          style={{ fontSize: 12, height: 30, padding: '2px 8px', marginTop: 2 }}
                                        />
                                      )}
                                    </div>
                                  );
                                })}
                              </div>

                              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                                <button
                                  type="button"
                                  onClick={() => setExpandedRowIndex(null)}
                                  className="btn btn-secondary"
                                  style={{ fontSize: 11, padding: '4px 12px' }}
                                >
                                  Cancel
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleSaveSingleRowDraft(idx)}
                                  disabled={isSavingRow}
                                  className="btn btn-primary"
                                  style={{
                                    fontSize: 11,
                                    padding: '5px 14px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 6,
                                    background: isValid ? '#2563EB' : '#16A34A',
                                    borderColor: isValid ? '#1D4ED8' : '#15803D',
                                  }}
                                >
                                  <Save size={12} /> {isSavingRow ? 'Saving...' : `Save & Re-validate Row #${idx + 1}`}
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
        </div>
      )}

      {/* Tab 2: Active Record Fields Grid */}
      {activeTab === 'fields' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
            Showing fields for active record #{selectedRecordIndex + 1}:
          </div>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: 12,
            }}
          >
            {allTableColumns.map((key) => {
              const val = activeData[key];
              const friendlyLabel = FIELD_FRIENDLY_LABELS[key] || key;
              const hasVal = val !== undefined && val !== null && String(val).trim() !== '';
              const isMissing = (workflow.missing_fields || []).some((mf) => mf.field === key);
              const udf = isUdf(key);

              return (
                <div
                  key={key}
                  style={{
                    background: udf ? '#FAF5FF' : '#FFFFFF',
                    border: udf ? '1px solid #D8B4FE' : isMissing ? '1px solid #FDE68A' : '1px solid #E2E8F0',
                    borderRadius: 'var(--radius-md)',
                    padding: 14,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 6,
                    boxShadow: '0 1px 3px rgba(15, 23, 42, 0.03)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                      <span style={{ fontSize: 11, fontWeight: 600, color: udf ? '#7E22CE' : '#64748B', textTransform: 'uppercase' }}>
                        {friendlyLabel}
                      </span>
                      {udf && (
                        <span
                          style={{
                            fontSize: 9,
                            padding: '1px 5px',
                            borderRadius: 3,
                            background: '#F3E8FF',
                            color: '#7E22CE',
                            fontWeight: 700,
                            border: '1px solid #E9D5FF'
                          }}
                          title="User-Defined Field (UDF) - Automatically carried forward to posted document"
                        >
                          UDF
                        </span>
                      )}
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      {hasVal && (
                        <button
                          type="button"
                          onClick={() => handleCopyValue(String(val), friendlyLabel)}
                          style={{
                            background: 'none',
                            border: 'none',
                            color: '#94A3B8',
                            cursor: 'pointer',
                            padding: 2,
                            display: 'flex',
                            alignItems: 'center'
                          }}
                          title={`Copy ${friendlyLabel} to clipboard`}
                        >
                          <Copy size={12} />
                        </button>
                      )}

                      {hasVal ? (
                        <span
                          style={{
                            fontSize: 10,
                            padding: '1px 6px',
                            borderRadius: 8,
                            background: '#DCFCE7',
                            border: '1px solid #BBF7D0',
                            color: '#166534',
                            fontWeight: 600,
                          }}
                        >
                          Extracted
                        </span>
                      ) : (
                        <span
                          style={{
                            fontSize: 10,
                            padding: '1px 6px',
                            borderRadius: 8,
                            background: isMissing ? '#FEF3C7' : '#F1F5F9',
                            border: isMissing ? '1px solid #FCD34D' : '1px solid #E2E8F0',
                            color: isMissing ? '#92400E' : '#64748B',
                            fontWeight: 600,
                          }}
                        >
                          {isMissing ? 'Missing' : 'Empty'}
                        </span>
                      )}
                    </div>
                  </div>
                  <strong style={{ fontSize: 13.5, color: hasVal ? (udf ? '#6B21A8' : '#0F172A') : '#94A3B8', wordBreak: 'break-all' }}>
                    {hasVal
                      ? typeof val === 'boolean'
                        ? val
                          ? 'Yes (True)'
                          : 'No (False)'
                        : String(val)
                      : '—'}
                  </strong>
                </div>
              );
            })}

          </div>
        </div>
      )}

      {/* Tab 3: 3-Engine & Raw Text Inspector */}
      {activeTab === 'engines' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 14 }}>
            {Object.entries(rawExtractions).map(([method, result]: [string, any]) => (
              <div key={method} className="glass-panel" style={{ padding: 16, background: '#FFFFFF', border: '1px solid #E2E8F0' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: '#2563EB', textTransform: 'uppercase' }}>
                    Engine: {method}
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                    {result?.total_records ? `${result.total_records} rows` : `${Object.keys(result?.data || {}).length} fields`}
                  </span>
                </div>
                <div
                  style={{
                    background: '#F8FAFC',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid #E2E8F0',
                    padding: 10,
                    fontSize: 11,
                    fontFamily: 'monospace',
                    color: '#1E293B',
                    maxHeight: 160,
                    overflowY: 'auto',
                  }}
                >
                  <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                    {JSON.stringify(result?.data || result?.records || {}, null, 2)}
                  </pre>
                </div>
              </div>
            ))}
          </div>

          <div>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: 8 }}>
              Raw Document Text Stream Sample:
            </span>
            <div
              style={{
                background: '#F8FAFC',
                border: '1px solid #E2E8F0',
                borderRadius: 'var(--radius-md)',
                padding: 14,
                fontFamily: 'monospace',
                fontSize: 11,
                color: '#1E293B',
                maxHeight: 180,
                overflowY: 'auto',
                whiteSpace: 'pre-wrap',
              }}
            >
              {(workflow as any).raw_text || (workflow as any).extracted_text || JSON.stringify(records, null, 2)}
            </div>
          </div>
        </div>
      )}

      {/* Batch Defaults Enrichment Modal */}
      {isDefaultsModalOpen && (
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
              maxWidth: 520,
              background: '#FFFFFF',
              border: '1px solid #E2E8F0',
              boxShadow: '0 20px 40px rgba(15, 23, 42, 0.15)',
              padding: 24,
              borderRadius: 'var(--radius-lg)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <Wand2 size={20} color="#D97706" />
                <h3 style={{ fontSize: 16, fontWeight: 700, color: '#0F172A' }}>
                  Batch Enrich / Fill Missing Fields
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setIsDefaultsModalOpen(false)}
                style={{ background: 'transparent', border: 'none', color: '#64748B', cursor: 'pointer' }}
              >
                <X size={18} />
              </button>
            </div>

            <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 16 }}>
              Apply default attributes across all {records.length} records in this document so that every row passes
              deterministic validation.
            </p>

            <form onSubmit={handleApplyDefaultsSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {workflow.master_type === 'business_partner' && (
                <>
                  <div>
                    <label className="form-label" style={{ fontSize: 12, marginBottom: 4 }}>
                      Partner Type (CardType)
                    </label>
                    <select
                      className="form-input"
                      value={cardTypeDefault}
                      onChange={(e) => setCardTypeDefault(e.target.value)}
                      style={{ fontSize: 12 }}
                    >
                      <option value="">Select Partner Type...</option>
                      <option value="Customer">Customer (cCustomer - Series 89)</option>
                      <option value="Supplier">Supplier / Vendor (cSupplier - Series 88)</option>
                    </select>
                  </div>

                  <div>
                    <label className="form-label" style={{ fontSize: 12, marginBottom: 4 }}>
                      CardName Generator Prefix
                    </label>
                    <input
                      type="text"
                      className="form-input"
                      value={cardNamePrefixDefault}
                      onChange={(e) => setCardNamePrefixDefault(e.target.value)}
                      placeholder="e.g. Client or Account "
                      style={{ fontSize: 12 }}
                    />
                    {cardNamePrefixDefault && (
                      <span style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2, display: 'block' }}>
                        Generates: "{cardNamePrefixDefault}[CardCode]" for rows missing a name
                      </span>
                    )}
                  </div>

                  <div>
                    <label className="form-label" style={{ fontSize: 12, marginBottom: 4 }}>
                      Default Email Address
                    </label>
                    <input
                      type="email"
                      className="form-input"
                      value={emailDefault}
                      onChange={(e) => setEmailDefault(e.target.value)}
                      placeholder="e.g. billing@company.com"
                      style={{ fontSize: 12 }}
                    />
                  </div>
                </>
              )}

              {workflow.master_type === 'item' && (
                <div>
                  <label className="form-label" style={{ fontSize: 12, marginBottom: 4 }}>
                    Default Item Group Code (ItemsGroupCode)
                  </label>
                  <input
                    type="number"
                    className="form-input"
                    value={itemsGroupCodeDefault}
                    onChange={(e) => setItemsGroupCodeDefault(e.target.value === '' ? '' : Number(e.target.value))}
                    placeholder="e.g. 100"
                    style={{ fontSize: 12 }}
                  />
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 12 }}>
                <button
                  type="button"
                  onClick={() => setIsDefaultsModalOpen(false)}
                  className="btn btn-secondary"
                  style={{ fontSize: 12 }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isApplyingDefaults}
                  className="btn btn-primary"
                  style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  <Sparkles size={14} /> {isApplyingDefaults ? 'Applying...' : `Enrich All ${records.length} Records`}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Focused Quick Edit Modal (Zero Horizontal Scroll & Minimum Effort Editing) */}
      {modalEditIndex !== null && (() => {
        const idx = modalEditIndex;
        const rec = records[idx] || {};
        const rowVal = getRowValidation(idx);
        const missing = rowVal?.missing_fields || [];
        const isValid = missing.length === 0 && (rowVal ? rowVal.valid : true);
        const allKeys = getRowEditableFields(rec, rowVal);
        const currentDraft = rowDrafts[idx] || {};

        const generalFieldsList = allKeys.filter((k) => getFieldCategory(k, workflow.master_type) === 'GENERAL');
        const contactFieldsList = allKeys.filter((k) => getFieldCategory(k, workflow.master_type) === 'CONTACT');
        const financialFieldsList = allKeys.filter((k) => getFieldCategory(k, workflow.master_type) === 'FINANCIAL');
        const udfFieldsList = allKeys.filter((k) => getFieldCategory(k, workflow.master_type) === 'UDF');

        const filteredFields = allKeys.filter((key) => {
          const isMissing = missing.includes(key);
          const cat = getFieldCategory(key, workflow.master_type);

          if (modalCategory === 'MISSING' && !isMissing) return false;
          if (modalCategory === 'GENERAL' && cat !== 'GENERAL') return false;
          if (modalCategory === 'CONTACT' && cat !== 'CONTACT') return false;
          if (modalCategory === 'FINANCIAL' && cat !== 'FINANCIAL') return false;
          if (modalCategory === 'UDF' && cat !== 'UDF') return false;

          if (modalSearch.trim()) {
            const q = modalSearch.toLowerCase();
            const label = (FIELD_FRIENDLY_LABELS[key] || key).toLowerCase();
            const val = String(currentDraft[key] ?? rec[key] ?? '').toLowerCase();
            return label.includes(q) || key.toLowerCase().includes(q) || val.includes(q);
          }
          return true;
        });

        const recordTitle = rec.CardCode || rec.ItemCode || rec.WarehouseCode || `Row #${idx + 1}`;
        const recordSubtitle = rec.CardName || rec.ItemName || rec.WarehouseName || '';

        return (
          <div
            style={{
              position: 'fixed',
              inset: 0,
              backgroundColor: 'rgba(10, 25, 49, 0.65)',
              backdropFilter: 'blur(6px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 9999,
              padding: 16,
              animation: 'fadeIn 0.15s ease-out',
            }}
            onClick={() => setModalEditIndex(null)}
          >
            <div
              className="glass-panel"
              style={{
                width: '100%',
                maxWidth: 960,
                maxHeight: '92vh',
                background: '#FFFFFF',
                borderRadius: 20,
                boxShadow: '0 25px 60px -15px rgba(0, 28, 61, 0.4), 0 0 0 1px rgba(226, 238, 250, 0.9)',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
              }}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Sticky Top Header Bar */}
              <div
                style={{
                  padding: '16px 24px',
                  background: 'linear-gradient(180deg, #F8FAFD 0%, #FFFFFF 100%)',
                  borderBottom: '1px solid #E2EEFA',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 12,
                }}
              >
                {/* Upper row: Title, Carousel stepper, and Close */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div
                      style={{
                        padding: '6px 10px',
                        borderRadius: 10,
                        background: isValid ? '#DCFCE7' : '#FEF2F2',
                        border: isValid ? '1px solid #BBF7D0' : '1px solid #FECACA',
                        color: isValid ? '#166534' : '#DC2626',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        fontWeight: 700,
                        fontSize: 12,
                      }}
                    >
                      {isValid ? <CheckCircle2 size={15} /> : <AlertTriangle size={15} />}
                      <span>{isValid ? 'Ready for SAP' : `${missing.length} Missing`}</span>
                    </div>

                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <h3 style={{ fontSize: 16, fontWeight: 800, color: '#0A1931', margin: 0 }}>
                          Edit Record — Row #{idx + 1}
                        </h3>
                        <span style={{ fontSize: 13, fontWeight: 700, color: '#1A56DB' }}>
                          {recordTitle}
                        </span>
                        {recordSubtitle && (
                          <span style={{ fontSize: 12, color: '#64748B' }}>
                            • {recordSubtitle}
                          </span>
                        )}
                      </div>
                      <span style={{ fontSize: 11, color: '#64748B' }}>
                        Deterministic SAP validation updates dynamically on save. No horizontal scrolling required.
                      </span>
                    </div>
                  </div>

                  {/* Stepper Navigation: Previous / Next Row without closing! */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ display: 'flex', alignItems: 'center', background: '#F1F5F9', borderRadius: 8, padding: 2, border: '1px solid #CBD5E1' }}>
                      <button
                        type="button"
                        onClick={() => handleOpenEditModal(idx - 1)}
                        disabled={idx === 0}
                        className="btn btn-secondary"
                        style={{
                          padding: '3px 8px',
                          fontSize: 11,
                          opacity: idx === 0 ? 0.4 : 1,
                          display: 'flex',
                          alignItems: 'center',
                          gap: 4,
                          background: 'transparent',
                          border: 'none',
                        }}
                        title="Previous record (Alt+Left)"
                      >
                        <ChevronLeft size={13} /> Prev
                      </button>
                      <span style={{ fontSize: 11, fontWeight: 700, color: '#334155', padding: '0 8px' }}>
                        {idx + 1} / {records.length}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleOpenEditModal(idx + 1)}
                        disabled={idx === records.length - 1}
                        className="btn btn-secondary"
                        style={{
                          padding: '3px 8px',
                          fontSize: 11,
                          opacity: idx === records.length - 1 ? 0.4 : 1,
                          display: 'flex',
                          alignItems: 'center',
                          gap: 4,
                          background: 'transparent',
                          border: 'none',
                        }}
                        title="Next record (Alt+Right)"
                      >
                        Next <ChevronRight size={13} />
                      </button>
                    </div>

                    <button
                      type="button"
                      onClick={() => setModalEditIndex(null)}
                      style={{
                        background: '#F1F5F9',
                        border: '1px solid #E2E8F0',
                        borderRadius: 8,
                        color: '#64748B',
                        cursor: 'pointer',
                        padding: '6px 8px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                      title="Close editor (Esc)"
                    >
                      <X size={16} />
                    </button>
                  </div>
                </div>

                {/* Filter and Category Tabs row */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
                  <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                    <button
                      type="button"
                      onClick={() => setModalCategory('ALL')}
                      style={{
                        padding: '4px 10px',
                        borderRadius: 6,
                        fontSize: 11,
                        fontWeight: 600,
                        border: modalCategory === 'ALL' ? '1px solid #1A56DB' : '1px solid #E2E8F0',
                        background: modalCategory === 'ALL' ? '#1A56DB' : '#FFFFFF',
                        color: modalCategory === 'ALL' ? '#FFFFFF' : '#475569',
                        cursor: 'pointer',
                      }}
                    >
                      All Fields ({allKeys.length})
                    </button>
                    {missing.length > 0 && (
                      <button
                        type="button"
                        onClick={() => setModalCategory('MISSING')}
                        style={{
                          padding: '4px 10px',
                          borderRadius: 6,
                          fontSize: 11,
                          fontWeight: 700,
                          border: modalCategory === 'MISSING' ? '1px solid #DC2626' : '1px solid #FECACA',
                          background: modalCategory === 'MISSING' ? '#DC2626' : '#FEF2F2',
                          color: modalCategory === 'MISSING' ? '#FFFFFF' : '#DC2626',
                          cursor: 'pointer',
                        }}
                      >
                        ⚠️ Missing Fields ({missing.length})
                      </button>
                    )}
                    {generalFieldsList.length > 0 && (
                      <button
                        type="button"
                        onClick={() => setModalCategory('GENERAL')}
                        style={{
                          padding: '4px 10px',
                          borderRadius: 6,
                          fontSize: 11,
                          fontWeight: 600,
                          border: modalCategory === 'GENERAL' ? '1px solid #1A56DB' : '1px solid #E2E8F0',
                          background: modalCategory === 'GENERAL' ? '#1A56DB' : '#FFFFFF',
                          color: modalCategory === 'GENERAL' ? '#FFFFFF' : '#475569',
                          cursor: 'pointer',
                        }}
                      >
                        General ({generalFieldsList.length})
                      </button>
                    )}
                    {contactFieldsList.length > 0 && (
                      <button
                        type="button"
                        onClick={() => setModalCategory('CONTACT')}
                        style={{
                          padding: '4px 10px',
                          borderRadius: 6,
                          fontSize: 11,
                          fontWeight: 600,
                          border: modalCategory === 'CONTACT' ? '1px solid #1A56DB' : '1px solid #E2E8F0',
                          background: modalCategory === 'CONTACT' ? '#1A56DB' : '#FFFFFF',
                          color: modalCategory === 'CONTACT' ? '#FFFFFF' : '#475569',
                          cursor: 'pointer',
                        }}
                      >
                        Contact & Address ({contactFieldsList.length})
                      </button>
                    )}
                    {financialFieldsList.length > 0 && (
                      <button
                        type="button"
                        onClick={() => setModalCategory('FINANCIAL')}
                        style={{
                          padding: '4px 10px',
                          borderRadius: 6,
                          fontSize: 11,
                          fontWeight: 600,
                          border: modalCategory === 'FINANCIAL' ? '1px solid #1A56DB' : '1px solid #E2E8F0',
                          background: modalCategory === 'FINANCIAL' ? '#1A56DB' : '#FFFFFF',
                          color: modalCategory === 'FINANCIAL' ? '#FFFFFF' : '#475569',
                          cursor: 'pointer',
                        }}
                      >
                        Financial & Tax ({financialFieldsList.length})
                      </button>
                    )}
                    {udfFieldsList.length > 0 && (
                      <button
                        type="button"
                        onClick={() => setModalCategory('UDF')}
                        style={{
                          padding: '4px 10px',
                          borderRadius: 6,
                          fontSize: 11,
                          fontWeight: 600,
                          border: modalCategory === 'UDF' ? '1px solid #7E22CE' : '1px solid #F3E8FF',
                          background: modalCategory === 'UDF' ? '#7E22CE' : '#FAF5FF',
                          color: modalCategory === 'UDF' ? '#FFFFFF' : '#7E22CE',
                          cursor: 'pointer',
                        }}
                      >
                        UDFs ({udfFieldsList.length})
                      </button>
                    )}
                  </div>

                  {/* Real-time Field Search */}
                  <div style={{ position: 'relative', width: 220 }}>
                    <Search size={13} color="#64748B" style={{ position: 'absolute', left: 8, top: '50%', transform: 'translateY(-50%)' }} />
                    <input
                      type="text"
                      className="form-input"
                      placeholder="Quick find field..."
                      value={modalSearch}
                      onChange={(e) => setModalSearch(e.target.value)}
                      style={{ paddingLeft: 26, fontSize: 11, height: 28 }}
                    />
                    {modalSearch && (
                      <button
                        type="button"
                        onClick={() => setModalSearch('')}
                        style={{ position: 'absolute', right: 6, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer', padding: 2 }}
                      >
                        <X size={11} />
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Scrollable Form Body (Compact 2-Column Responsive Grid) */}
              <div
                style={{
                  padding: '20px 24px',
                  overflowY: 'auto',
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 16,
                  background: '#F8FAFD',
                }}
              >
                {/* Priority Missing Fields Callout Banner */}
                {missing.length > 0 && modalCategory !== 'MISSING' && (
                  <div
                    style={{
                      padding: '10px 14px',
                      background: '#FFF5F5',
                      border: '1.5px solid #FECACA',
                      borderRadius: 12,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: 10,
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <AlertTriangle size={15} color="#DC2626" />
                      <span style={{ fontSize: 12, color: '#991B1B', fontWeight: 600 }}>
                        {missing.length} Mandatory SAP field(s) require attention: {missing.join(', ')}
                      </span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setModalCategory('MISSING')}
                      className="btn btn-secondary"
                      style={{ padding: '3px 8px', fontSize: 11, background: '#FEF2F2', borderColor: '#FCA5A5', color: '#DC2626', fontWeight: 700 }}
                    >
                      Filter to Missing
                    </button>
                  </div>
                )}

                {filteredFields.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '40px 20px', color: '#64748B' }}>
                    <Search size={24} style={{ opacity: 0.5, marginBottom: 8 }} />
                    <p style={{ fontSize: 13, fontWeight: 600 }}>No fields matched your filter or search.</p>
                    <button
                      type="button"
                      onClick={() => { setModalSearch(''); setModalCategory('ALL'); }}
                      className="btn btn-secondary"
                      style={{ marginTop: 8, fontSize: 11 }}
                    >
                      Clear Filters
                    </button>
                  </div>
                ) : (
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))',
                      gap: 12,
                    }}
                  >
                    {filteredFields.map((fieldKey) => {
                      const label = FIELD_FRIENDLY_LABELS[fieldKey] || fieldKey;
                      const currentVal = rowDrafts[idx]?.[fieldKey] ?? rec[fieldKey] ?? '';
                      const enumOpts = ENUM_OPTIONS[fieldKey];
                      const isMissing = missing.includes(fieldKey);
                      const isFilled = String(currentVal).trim() !== '';
                      const udf = isUdf(fieldKey);

                      return (
                        <div
                          key={fieldKey}
                          style={{
                            background: isMissing ? '#FEF2F2' : '#FFFFFF',
                            border: isMissing ? '1.5px solid #F87171' : '1px solid #E2EEFA',
                            borderRadius: 12,
                            padding: '10px 14px',
                            boxShadow: '0 2px 6px rgba(0, 28, 61, 0.03)',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 6,
                            transition: 'all 0.15s ease',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 6 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                              <span style={{ fontSize: 12.5, fontWeight: 700, color: '#0A1931' }}>
                                {label}
                              </span>
                              {udf && (
                                <span
                                  style={{
                                    fontSize: 9,
                                    padding: '1px 5px',
                                    borderRadius: 4,
                                    background: '#F3E8FF',
                                    color: '#7E22CE',
                                    fontWeight: 700,
                                    border: '1px solid #E9D5FF',
                                  }}
                                >
                                  UDF
                                </span>
                              )}
                            </div>

                            <div>
                              {isMissing ? (
                                <span
                                  style={{
                                    fontSize: 9.5,
                                    padding: '1px 6px',
                                    borderRadius: 4,
                                    background: '#FEE2E2',
                                    color: '#DC2626',
                                    fontWeight: 700,
                                    border: '1px solid #FCA5A5',
                                  }}
                                >
                                  * Mandatory
                                </span>
                              ) : isFilled ? (
                                <span style={{ fontSize: 9.5, color: '#16A34A', fontWeight: 600 }}>
                                  ✓ Valid
                                </span>
                              ) : (
                                <span style={{ fontSize: 9.5, color: '#94A3B8' }}>
                                  Optional
                                </span>
                              )}
                            </div>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <code style={{ fontSize: 10, color: '#2563EB', background: '#EFF6FF', padding: '1px 5px', borderRadius: 4 }}>
                              {fieldKey}
                            </code>
                            {isFilled && (
                              <button
                                type="button"
                                onClick={() => handleRowDraftChange(idx, fieldKey, '')}
                                style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer', fontSize: 10 }}
                                title="Clear field"
                              >
                                Clear
                              </button>
                            )}
                          </div>

                          {enumOpts ? (
                            <select
                              className="form-input"
                              value={currentVal}
                              onChange={(e) => handleRowDraftChange(idx, fieldKey, e.target.value)}
                              style={{
                                fontSize: 12.5,
                                height: 34,
                                padding: '4px 8px',
                                background: '#FFFFFF',
                                borderColor: isMissing ? '#F87171' : '#CBD5E1',
                              }}
                            >
                              <option value="">-- Select {fieldKey} --</option>
                              {enumOpts.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                  {opt.label}
                                </option>
                              ))}
                            </select>
                          ) : (
                            <input
                              type={
                                fieldKey.toLowerCase().includes('email')
                                  ? 'email'
                                  : fieldKey === 'ItemsGroupCode' || fieldKey === 'Location'
                                  ? 'number'
                                  : 'text'
                              }
                              className="form-input"
                              value={currentVal}
                              placeholder={`Enter ${label}...`}
                              onChange={(e) => handleRowDraftChange(idx, fieldKey, e.target.value)}
                              style={{
                                fontSize: 12.5,
                                height: 34,
                                padding: '4px 10px',
                                background: '#FFFFFF',
                                borderColor: isMissing ? '#F87171' : '#CBD5E1',
                              }}
                            />
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Sticky Bottom Actions Bar */}
              <div
                style={{
                  padding: '14px 24px',
                  background: '#FFFFFF',
                  borderTop: '1px solid #E2EEFA',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  flexWrap: 'wrap',
                  gap: 12,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: '#64748B', fontSize: 11 }}>
                  <span>Shortcuts:</span>
                  <code style={{ background: '#F1F5F9', padding: '1px 5px', borderRadius: 4 }}>Ctrl + Enter</code>
                  <span>to save</span>
                  <span>•</span>
                  <code style={{ background: '#F1F5F9', padding: '1px 5px', borderRadius: 4 }}>Esc</code>
                  <span>to close</span>
                  <span>•</span>
                  <code style={{ background: '#F1F5F9', padding: '1px 5px', borderRadius: 4 }}>Alt + ←/→</code>
                  <span>to switch rows</span>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <button
                    type="button"
                    onClick={() => setModalEditIndex(null)}
                    className="btn btn-secondary"
                    style={{ fontSize: 12, padding: '7px 14px' }}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={() => handleSaveModalDraft(idx, false)}
                    disabled={isSavingRow}
                    className="btn btn-secondary"
                    style={{
                      fontSize: 12,
                      padding: '7px 14px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                    title="Save changes to this row and keep modal open"
                  >
                    <Save size={13} /> {isSavingRow ? 'Saving...' : 'Save Draft'}
                  </button>
                  {idx < records.length - 1 && (
                    <button
                      type="button"
                      onClick={() => handleSaveModalDraft(idx, true)}
                      disabled={isSavingRow}
                      className="btn btn-secondary"
                      style={{
                        fontSize: 12,
                        padding: '7px 14px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        background: '#EFF6FF',
                        borderColor: '#BFDBFE',
                        color: '#1D4ED8',
                        fontWeight: 600,
                      }}
                      title={`Save this row and immediately advance to Row #${idx + 2}`}
                    >
                      Save &amp; Next Row →
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => handleSaveModalDraft(idx, false)}
                    disabled={isSavingRow}
                    className="btn btn-primary"
                    style={{
                      fontSize: 12,
                      padding: '7px 18px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                      background: isValid ? '#1A56DB' : '#16A34A',
                      borderColor: isValid ? '#1648BA' : '#15803D',
                      fontWeight: 700,
                    }}
                  >
                    <Check size={14} /> {isSavingRow ? 'Saving...' : `Save & Close Row #${idx + 1}`}
                  </button>
                </div>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};
