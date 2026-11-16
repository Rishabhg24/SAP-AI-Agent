import React, { useState, useEffect } from 'react';
import type { MissingFieldInfo, MasterDataType } from '../types';
import {
  AlertTriangle,
  CheckCircle2,
  Sparkles,
  Save,
  RotateCcw,
  Check,
} from 'lucide-react';

interface Props {
  missingFields: MissingFieldInfo[];
  masterType: MasterDataType;
  activeRecordIndex: number;
  totalRecords: number;
  activeRecordData: Record<string, any>;
  onSave: (updates: Record<string, any>, applyToAll: boolean) => Promise<void>;
  isSaving?: boolean;
}

interface FieldDef {
  field: string;
  label: string;
  reason: string;
  example?: string;
  isMandatory: boolean;
}

const STANDARD_FIELDS: Record<string, FieldDef[]> = {
  business_partner: [
    { field: 'CardCode', label: 'Customer / Vendor Code', reason: 'Primary account code in SAP  (max 15 chars)', example: 'C000101', isMandatory: true },
    { field: 'CardName', label: 'Business Partner Name', reason: 'Official legal entity name required on all SAP documents', example: 'Apex Precision Components Ltd', isMandatory: true },
    { field: 'CardType', label: 'Partner Type', reason: 'Customer (Series 89) or Supplier/Vendor (Series 88)', example: 'Customer', isMandatory: true },
    { field: 'FederalTaxID', label: 'Federal Tax ID / GSTIN', reason: '15-character GST identification number', example: '10ABCDE1234F1Z5', isMandatory: false },
    { field: 'PANNo', label: 'PAN No', reason: '10-character Permanent Account Number for tax reporting', example: 'ABCDE1234F', isMandatory: false },
    { field: 'GSTNo', label: 'GST Number', reason: '15-digit GST registration code', example: '10ABCDE1234F1Z5', isMandatory: false },
    { field: 'Address', label: 'Registered Address', reason: 'Street or facility address for correspondence & tax invoices', example: '100 Business Boulevard, Industrial Zone', isMandatory: true },
    { field: 'TaxDetails', label: 'Tax Details / Group', reason: 'Applicable GST/VAT tax group structure in SAP', example: 'GST 18%', isMandatory: true },
    { field: 'PaymentTerms', label: 'Payment Terms', reason: 'Standard payment credit terms (e.g. Net 30, Cash)', example: 'Net 30', isMandatory: true },
    { field: 'Currency', label: 'Currency', reason: 'Default transaction currency in SAP', example: 'INR', isMandatory: false },
    { field: 'ControlAccount', label: 'GL Control Account', reason: 'General Ledger reconciliation control account', example: '211000', isMandatory: false },
    { field: 'EmailAddress', label: 'Email Address', reason: 'Official billing and dispatch email address', example: 'billing@client.com', isMandatory: true },
    { field: 'Phone1', label: 'Primary Phone', reason: 'Primary contact phone number', example: '+91-9876543210', isMandatory: false },
  ],
  item: [
    { field: 'ItemCode', label: 'Item Code', reason: 'Unique identifier for inventory item (max 50 chars)', example: 'ITM-10024', isMandatory: true },
    { field: 'ItemName', label: 'Item Name / Description', reason: 'Catalog description for orders & inventory in SAP', example: 'Stainless Steel Hex Bolt M8x40', isMandatory: true },
    { field: 'ItemsGroupCode', label: 'Item Group Code', reason: 'Item group code for GL general ledger account determination', example: '100', isMandatory: true },
    { field: 'InventoryUOM', label: 'Unit of Measure (UoM)', reason: 'Stock tracking unit (PCS, KG, BOX, MTR)', example: 'PCS', isMandatory: true },
    { field: 'ItemType', label: 'Item Type', reason: 'Operational classification (Inventory/Sales/Purchase)', example: 'Inventory/Sales/Purchase', isMandatory: true },
    { field: 'TaxRate', label: 'Tax Rate (%)', reason: 'Applicable GST/VAT percentage in SAP', example: '18%', isMandatory: true },
    { field: 'ItemManagementMethod', label: 'Management Method', reason: 'Tracking method: None, Batch, or Serial', example: 'None', isMandatory: true },
    { field: 'ItemCategory', label: 'Item Category', reason: 'Specifies tangible Item or Service in SAP', example: 'Item', isMandatory: true },
    { field: 'MaterialType', label: 'Material Type', reason: 'Classification: RM, FG, or Capital Goods', example: 'RM', isMandatory: true },
    { field: 'TaxCategory', label: 'Tax Category', reason: 'Tax status under tax regulations: Taxable or Exempted', example: 'Taxable', isMandatory: true },
    { field: 'HSN', label: 'HSN / SAC Code', reason: 'Regulatory tariff code required for GST invoicing', example: '73181500', isMandatory: true },
    { field: 'SalesUnit', label: 'Sales Unit of Measure', reason: 'Packaging unit for sales transactions', example: 'PCS', isMandatory: false },
    { field: 'PurchaseUnit', label: 'Purchase Unit of Measure', reason: 'Packaging unit for vendor purchase orders', example: 'BOX', isMandatory: false },
    { field: 'BarCode', label: 'Barcode (EAN/UPC)', reason: 'Universal Product Code or EAN standard barcode', example: '8901234567890', isMandatory: false },
    { field: 'SalesUnitWeight', label: 'Sales Unit Weight', reason: 'Gross weight per sales unit in kg', example: '1.25', isMandatory: false },
  ],
  warehouse: [
    { field: 'WarehouseCode', label: 'Warehouse Code', reason: 'Unique storage facility code in SAP (max 8 chars)', example: 'WH01', isMandatory: true },
    { field: 'WarehouseName', label: 'Warehouse Name', reason: 'Descriptive facility name in SAP', example: 'Central Distribution Depot', isMandatory: true },
    { field: 'Location', label: 'Location Code', reason: 'Physical facility location code', example: '1', isMandatory: true },
    { field: 'Address', label: 'Facility Address', reason: 'Physical warehouse street address', example: 'Plot 42, Logistics Gateway', isMandatory: true },
    { field: 'Street', label: 'Street', reason: 'Street name or physical facility sub-address', example: 'Highway 10, Logistics Hub', isMandatory: false },
    { field: 'City', label: 'City', reason: 'Operational facility city', example: 'Mumbai', isMandatory: false },
    { field: 'Country', label: 'Country', reason: '2-character ISO country code', example: 'IN', isMandatory: false },
    { field: 'Inactive', label: 'Inactive Status', reason: 'Mark facility inactive (tYES/tNO)', example: 'tNO', isMandatory: false },
    { field: 'BinActivat', label: 'Bin Locations Activated', reason: 'Enable bin tracking (tYES/tNO)', example: 'tNO', isMandatory: false },
  ],
};

const ENUM_OPTIONS: Record<string, { label: string; value: string }[]> = {
  CardType: [
    { label: 'Customer (Series 89)', value: 'Customer' },
    { label: 'Supplier / Vendor (Series 88)', value: 'Supplier' },
  ],
  ItemType: [
    { label: 'Inventory / Sales / Purchase (Full Item)', value: 'Inventory/Sales/Purchase' },
    { label: 'Inventory Only', value: 'Inventory' },
    { label: 'Sales Only', value: 'Sales' },
    { label: 'Purchase Only', value: 'Purchase' },
  ],
  ItemManagementMethod: [
    { label: 'None (Standard Stock)', value: 'None' },
    { label: 'Batch (Lot Controlled)', value: 'Batch' },
    { label: 'Serial (Serial Number Controlled)', value: 'Serial' },
  ],
  ItemCategory: [
    { label: 'Item (Tangible Product)', value: 'Item' },
    { label: 'Service (Intangible / Labor)', value: 'Service' },
  ],
  MaterialType: [
    { label: 'RM (Raw Material)', value: 'RM' },
    { label: 'FG (Finished Goods)', value: 'FG' },
    { label: 'Capital Goods', value: 'Capital Goods' },
    { label: 'Spares / Consumables', value: 'Spares' },
  ],
  TaxCategory: [
    { label: 'Taxable (Standard GST/VAT)', value: 'Taxable' },
    { label: 'Exempted (Zero Tax)', value: 'Exempted' },
    { label: 'Nil Rated', value: 'Nil Rated' },
  ],
  TaxDetails: [
    { label: 'GST 18% (Standard Rate)', value: 'GST 18%' },
    { label: 'GST 12%', value: 'GST 12%' },
    { label: 'GST 5%', value: 'GST 5%' },
    { label: 'GST 28% (Luxury / High Rate)', value: 'GST 28%' },
    { label: 'Exempt 0%', value: 'Exempt' },
  ],
  PaymentTerms: [
    { label: 'Net 30 (30 Days Credit)', value: 'Net 30' },
    { label: 'Net 60 (60 Days Credit)', value: 'Net 60' },
    { label: 'Net 15 (15 Days Credit)', value: 'Net 15' },
    { label: 'Immediate / Due on Receipt', value: 'Immediate' },
    { label: 'Cash', value: 'Cash' },
  ],
  Currency: [
    { label: 'INR (Indian Rupee)', value: 'INR' },
    { label: 'USD (US Dollar)', value: 'USD' },
    { label: 'EUR (Euro)', value: 'EUR' },
    { label: 'GBP (British Pound)', value: 'GBP' },
  ],
  InventoryUOM: [
    { label: 'PCS (Pieces)', value: 'PCS' },
    { label: 'KG (Kilograms)', value: 'KG' },
    { label: 'BOX (Boxes)', value: 'BOX' },
    { label: 'MTR (Meters)', value: 'MTR' },
    { label: 'SET (Sets)', value: 'SET' },
    { label: 'LTR (Liters)', value: 'LTR' },
  ],
};

export const MissingFieldsTable: React.FC<Props> = ({
  missingFields,
  masterType,
  activeRecordIndex,
  totalRecords,
  activeRecordData,
  onSave,
  isSaving = false,
}) => {
  const [fieldValues, setFieldValues] = useState<Record<string, any>>({});
  const [applyToAll, setApplyToAll] = useState(totalRecords > 1);
  const [cardNamePrefix, setCardNamePrefix] = useState('Client ');
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);
  const [viewFilter, setViewFilter] = useState<'ALL' | 'MISSING'>(
    missingFields.length > 0 ? 'ALL' : 'ALL'
  );

  const isCurrentRecordValid = missingFields.length === 0;

  // Build complete list of fields for this master type + record data
  const standardDefs = STANDARD_FIELDS[masterType] || [];
  const missingFieldKeys = new Set(missingFields.map((mf) => mf.field));

  // Collect all unique field keys
  const allFieldKeys = Array.from(
    new Set([
      ...standardDefs.map((sd) => sd.field),
      ...Object.keys(activeRecordData),
      ...missingFields.map((mf) => mf.field),
    ])
  );

  // Map each field key to its metadata
  const fieldList: FieldDef[] = allFieldKeys.map((key) => {
    const fromMissing = missingFields.find((mf) => mf.field === key);
    const fromStandard = standardDefs.find((sd) => sd.field === key);
    return {
      field: key,
      label: fromMissing?.label || fromStandard?.label || key,
      reason: fromMissing?.reason || fromStandard?.reason || `SAP  field for ${masterType}`,
      example: fromMissing?.example || fromStandard?.example,
      isMandatory: fromMissing ? true : fromStandard ? fromStandard.isMandatory : false,
    };
  });

  // Sort fields: missing mandatory fields at the top, then remaining
  const sortedFields = [...fieldList].sort((a, b) => {
    const aMissing = missingFieldKeys.has(a.field);
    const bMissing = missingFieldKeys.has(b.field);
    if (aMissing && !bMissing) return -1;
    if (!aMissing && bMissing) return 1;
    return 0;
  });

  // Filtered fields based on view filter
  const displayedFields = sortedFields.filter((f) => {
    if (viewFilter === 'MISSING') {
      return missingFieldKeys.has(f.field);
    }
    return true;
  });

  // Initialize field values when record or data changes
  useEffect(() => {
    const initial: Record<string, any> = {};
    allFieldKeys.forEach((key) => {
      if (activeRecordData[key] !== undefined && activeRecordData[key] !== null && activeRecordData[key] !== '') {
        initial[key] = activeRecordData[key];
      } else {
        initial[key] = '';
      }
    });
    setFieldValues(initial);
    setSaveSuccessMsg(null);
    // If has missing fields, default to ALL so user sees both existing and missing
    if (missingFields.length > 0) {
      setViewFilter('ALL');
    }
  }, [missingFields.length, activeRecordIndex, activeRecordData]);

  const handleInputChange = (field: string, value: any) => {
    setFieldValues((prev) => ({
      ...prev,
      [field]: value,
    }));
  };


  const handleReset = () => {
    const resetValues: Record<string, any> = {};
    allFieldKeys.forEach((key) => {
      resetValues[key] = activeRecordData[key] ?? '';
    });
    setFieldValues(resetValues);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const payload: Record<string, any> = {};
    Object.entries(fieldValues).forEach(([k, v]) => {
      if (v !== undefined && v !== null && String(v).trim() !== '') {
        if (k === 'ItemsGroupCode' || k === 'Location') {
          const num = Number(v);
          payload[k] = isNaN(num) ? v : num;
        } else {
          payload[k] = v;
        }
      }
    });

    if (applyToAll && masterType === 'business_partner' && cardNamePrefix) {
      payload.CardNamePrefix = cardNamePrefix;
    }

    try {
      await onSave(payload, applyToAll);
      setSaveSuccessMsg(
        applyToAll
          ? `Saved and re-validated all ${totalRecords} records!`
          : `Saved and re-validated Record #${activeRecordIndex + 1}!`
      );
      setTimeout(() => setSaveSuccessMsg(null), 4000);
    } catch {
      // Handled by parent
    }
  };

  const getQuickChips = (field: string) => {
    const code = activeRecordData.CardCode || activeRecordData.ItemCode || `${activeRecordIndex + 1}`;
    switch (field) {
      case 'CardName':
        return [
          { label: `Client ${code}`, value: `Client ${code}` },
          { label: `Account ${code}`, value: `Account ${code}` },
        ];
      case 'PaymentTerms':
        return [
          { label: 'Net 30', value: 'Net 30' },
          { label: 'Immediate', value: 'Immediate' },
        ];
      case 'TaxDetails':
        return [
          { label: 'GST 18%', value: 'GST 18%' },
          { label: 'Exempt', value: 'Exempt' },
        ];
      case 'Currency':
        return [
          { label: 'INR', value: 'INR' },
          { label: 'USD', value: 'USD' },
        ];
      case 'ControlAccount':
        return [
          { label: '211000', value: '211000' },
          { label: '111000', value: '111000' },
        ];
      case 'EmailAddress':
        return [
          { label: `billing@${String(code).toLowerCase()}.com`, value: `billing@${String(code).toLowerCase()}.com` },
        ];
      case 'InventoryUOM':
        return [
          { label: 'PCS', value: 'PCS' },
          { label: 'KG', value: 'KG' },
          { label: 'BOX', value: 'BOX' },
        ];
      case 'HSN':
        return [
          { label: '73181500', value: '73181500' },
          { label: '84713010', value: '84713010' },
        ];
      default:
        return [];
    }
  };

  return (
    <div
      style={{
        background: '#FFFFFF',
        border: isCurrentRecordValid ? '1.5px solid #10B981' : '1.5px solid #F59E0B',
        borderRadius: 'var(--radius-lg, 12px)',
        boxShadow: isCurrentRecordValid
          ? '0 4px 20px -2px rgba(16, 185, 129, 0.12), 0 2px 6px -1px rgba(0, 0, 0, 0.05)'
          : '0 4px 20px -2px rgba(245, 158, 11, 0.12), 0 2px 6px -1px rgba(0, 0, 0, 0.05)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Table Card Header */}
      <div
        style={{
          background: isCurrentRecordValid
            ? 'linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%)'
            : 'linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%)',
          borderBottom: isCurrentRecordValid ? '1px solid #BBF7D0' : '1px solid #FDE68A',
          padding: '16px 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 8,
              background: isCurrentRecordValid ? '#BBF7D0' : '#FDE68A',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: isCurrentRecordValid ? '#15803D' : '#B45309',
            }}
          >
            {isCurrentRecordValid ? <CheckCircle2 size={20} /> : <AlertTriangle size={20} />}
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <h4
                style={{
                  margin: 0,
                  fontSize: 15,
                  fontWeight: 700,
                  color: isCurrentRecordValid ? '#166534' : '#92400E',
                }}
              >
                {isCurrentRecordValid ? 'Editable Record Master Data' : 'Fill Missing & Edit Record Fields'}
              </h4>

              {/* Status Badge */}
              {isCurrentRecordValid ? (
                <span
                  style={{
                    fontSize: 11,
                    padding: '2px 8px',
                    borderRadius: 12,
                    background: '#DCFCE7',
                    border: '1px solid #86EFAC',
                    color: '#15803D',
                    fontWeight: 700,
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 3,
                  }}
                >
                  <Check size={11} /> Mandatory Passed
                </span>
              ) : (
                <span
                  style={{
                    fontSize: 11,
                    padding: '2px 8px',
                    borderRadius: 12,
                    background: '#FEE2E2',
                    border: '1px solid #FCA5A5',
                    color: '#DC2626',
                    fontWeight: 700,
                  }}
                >
                  Mandatory Field Required ({missingFields.length})
                </span>
              )}

              <span
                style={{
                  fontSize: 11,
                  padding: '2px 8px',
                  borderRadius: 12,
                  background: '#E0E7FF',
                  border: '1px solid #C7D2FE',
                  color: '#3730A3',
                  fontWeight: 600,
                }}
              >
                Record #{activeRecordIndex + 1}
                {activeRecordData.CardCode ? ` (${activeRecordData.CardCode})` : ''}
                {activeRecordData.ItemCode ? ` (${activeRecordData.ItemCode})` : ''}
              </span>
            </div>
            <p
              style={{
                margin: '4px 0 0',
                fontSize: 12,
                color: isCurrentRecordValid ? '#14532D' : '#78350F',
              }}
            >
              {isCurrentRecordValid
                ? 'All mandatory SAP checks passed. You can edit any field below to update this entry directly.'
                : 'Deterministic validation requires values for missing fields below. You can fill and edit every field here.'}
            </p>
          </div>
        </div>

        {/* Header Toolbar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          {/* View Filter if there are missing fields */}
          {missingFields.length > 0 && (
            <div style={{ display: 'flex', gap: 4, background: '#FFFFFF', padding: 2, borderRadius: 6, border: '1px solid #CBD5E1' }}>
              <button
                type="button"
                onClick={() => setViewFilter('ALL')}
                className={`btn ${viewFilter === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ padding: '3px 9px', fontSize: 11 }}
              >
                All Fields ({allFieldKeys.length})
              </button>
              <button
                type="button"
                onClick={() => setViewFilter('MISSING')}
                className={`btn ${viewFilter === 'MISSING' ? 'btn-primary' : 'btn-secondary'}`}
                style={{
                  padding: '3px 9px',
                  fontSize: 11,
                  color: viewFilter === 'MISSING' ? '#FFFFFF' : '#B45309',
                  fontWeight: 600,
                }}
              >
                Missing ({missingFields.length})
              </button>
            </div>
          )}

          <button
            type="button"
            onClick={handleReset}
            className="btn btn-secondary"
            style={{
              fontSize: 12,
              padding: '6px 10px',
              background: '#FFFFFF',
              border: '1px solid #E2E8F0',
              color: '#64748B',
            }}
            title="Reset to initial values"
          >
            <RotateCcw size={13} />
          </button>
        </div>
      </div>

      {/* Form & Table */}
      <form onSubmit={handleSubmit} style={{ margin: 0, display: 'flex', flexDirection: 'column' }}>
        <div style={{ overflowX: 'auto', maxHeight: 460 }}>
          <table
            className="data-table"
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: 12,
              textAlign: 'left',
            }}
          >
            <thead>
              <tr style={{ background: '#F1F5F9', borderBottom: '1px solid #CBD5E1' }}>
                <th style={{ width: 36, textAlign: 'center', color: '#475569', padding: '10px 8px' }}>#</th>
                <th style={{ width: '28%', color: '#1E293B', padding: '10px 12px' }}>SAP Master Field</th>
                <th style={{ width: '30%', color: '#1E293B', padding: '10px 12px' }}>Description & Rules</th>
                <th style={{ color: '#1E293B', padding: '10px 12px' }}>Value (Edit / Fill Here)</th>
                <th style={{ width: 85, textAlign: 'center', color: '#1E293B', padding: '10px 8px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {displayedFields.map((f, idx) => {
                const currentVal = fieldValues[f.field] ?? '';
                const isFilled = String(currentVal).trim() !== '';
                const isMissing = missingFieldKeys.has(f.field);
                const enumOptions = ENUM_OPTIONS[f.field];
                const chips = getQuickChips(f.field);

                return (
                  <tr
                    key={f.field}
                    style={{
                      background: isMissing ? (isFilled ? '#FAFCFF' : '#FFFDF5') : '#FFFFFF',
                      borderBottom: '1px solid #E2E8F0',
                      transition: 'background 0.2s',
                    }}
                  >
                    {/* Index Column */}
                    <td style={{ textAlign: 'center', fontWeight: 600, color: '#94A3B8' }}>
                      {idx + 1}
                    </td>

                    {/* Field Name Column */}
                    <td style={{ padding: '10px 12px', verticalAlign: 'top' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                          <span style={{ fontWeight: 700, color: '#0F172A', fontSize: 13 }}>
                            {f.label}
                          </span>
                          {isMissing && (
                            <span
                              style={{
                                fontSize: 10,
                                background: '#FEE2E2',
                                color: '#DC2626',
                                border: '1px solid #FCA5A5',
                                padding: '1px 6px',
                                borderRadius: 4,
                                fontWeight: 700,
                              }}
                            >
                              * Mandatory Field Required
                            </span>
                          )}
                          {!isMissing && f.isMandatory && (
                            <span
                              style={{
                                fontSize: 10,
                                background: '#DCFCE7',
                                color: '#15803D',
                                border: '1px solid #86EFAC',
                                padding: '1px 6px',
                                borderRadius: 4,
                                fontWeight: 700,
                              }}
                            >
                              Mandatory Passed
                            </span>
                          )}
                        </div>
                        <code
                          style={{
                            fontSize: 11,
                            color: '#2563EB',
                            background: '#EFF6FF',
                            padding: '1px 5px',
                            borderRadius: 4,
                            width: 'fit-content',
                          }}
                        >
                          {f.field}
                        </code>
                      </div>
                    </td>

                    {/* Reason / Requirement Column */}
                    <td style={{ padding: '10px 12px', verticalAlign: 'top' }}>
                      <p style={{ margin: 0, fontSize: 11.5, color: '#475569', lineHeight: 1.4 }}>
                        {f.reason}
                      </p>
                      {f.example && (
                        <div style={{ marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                          <span style={{ fontSize: 10, color: '#64748B', fontWeight: 600 }}>Example:</span>
                          <code
                            style={{
                              fontSize: 10.5,
                              color: '#475569',
                              background: '#F1F5F9',
                              padding: '1px 4px',
                              borderRadius: 3,
                            }}
                          >
                            {f.example}
                          </code>
                        </div>
                      )}
                    </td>

                    {/* Input Value Column */}
                    <td style={{ padding: '8px 12px', verticalAlign: 'top' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {enumOptions ? (
                          <select
                            className="form-input"
                            value={currentVal}
                            onChange={(e) => handleInputChange(f.field, e.target.value)}
                            style={{
                              fontSize: 12,
                              padding: '6px 10px',
                              borderRadius: 6,
                              borderColor: isFilled ? '#10B981' : isMissing ? '#F59E0B' : '#CBD5E1',
                              background: isFilled ? '#F0FDF4' : '#FFFFFF',
                              fontWeight: isFilled ? 600 : 400,
                            }}
                          >
                            <option value="">-- Select {f.label} --</option>
                            {enumOptions.map((opt) => (
                              <option key={opt.value} value={opt.value}>
                                {opt.label}
                              </option>
                            ))}
                          </select>
                        ) : f.field.toLowerCase().includes('email') ? (
                          <input
                            type="email"
                            className="form-input"
                            placeholder={f.example || 'billing@company.com'}
                            value={currentVal}
                            onChange={(e) => handleInputChange(f.field, e.target.value)}
                            style={{
                              fontSize: 12,
                              padding: '6px 10px',
                              borderRadius: 6,
                              borderColor: isFilled ? '#10B981' : isMissing ? '#F59E0B' : '#CBD5E1',
                              background: isFilled ? '#F0FDF4' : '#FFFFFF',
                            }}
                          />
                        ) : f.field === 'ItemsGroupCode' || f.field === 'Location' ? (
                          <input
                            type="number"
                            className="form-input"
                            placeholder={f.example || '100'}
                            value={currentVal}
                            onChange={(e) => handleInputChange(f.field, e.target.value)}
                            style={{
                              fontSize: 12,
                              padding: '6px 10px',
                              borderRadius: 6,
                              borderColor: isFilled ? '#10B981' : isMissing ? '#F59E0B' : '#CBD5E1',
                              background: isFilled ? '#F0FDF4' : '#FFFFFF',
                            }}
                          />
                        ) : (
                          <input
                            type="text"
                            className="form-input"
                            placeholder={f.example ? `e.g. ${f.example}` : `Enter ${f.label}...`}
                            value={currentVal}
                            onChange={(e) => handleInputChange(f.field, e.target.value)}
                            style={{
                              fontSize: 12,
                              padding: '6px 10px',
                              borderRadius: 6,
                              borderColor: isFilled ? '#10B981' : isMissing ? '#F59E0B' : '#CBD5E1',
                              background: isFilled ? '#F0FDF4' : '#FFFFFF',
                            }}
                          />
                        )}

                        {/* Quick Chips */}
                        {chips.length > 0 && (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 4, flexWrap: 'wrap' }}>
                            <span style={{ fontSize: 10, color: '#94A3B8' }}>Quick set:</span>
                            {chips.map((chip) => (
                              <button
                                key={chip.label}
                                type="button"
                                onClick={() => handleInputChange(f.field, chip.value)}
                                style={{
                                  fontSize: 10,
                                  background: currentVal === chip.value ? '#2563EB' : '#F1F5F9',
                                  color: currentVal === chip.value ? '#FFFFFF' : '#334155',
                                  border: '1px solid #CBD5E1',
                                  borderRadius: 10,
                                  padding: '1px 7px',
                                  cursor: 'pointer',
                                  fontWeight: 500,
                                }}
                              >
                                {chip.label}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </td>

                    {/* Status Column */}
                    <td style={{ textAlign: 'center', verticalAlign: 'middle', padding: '8px' }}>
                      {isFilled ? (
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 3,
                            color: '#16A34A',
                            fontSize: 11,
                            fontWeight: 600,
                            background: '#DCFCE7',
                            padding: '3px 8px',
                            borderRadius: 12,
                            border: '1px solid #BBF7D0',
                          }}
                        >
                          <Check size={12} /> Valid
                        </span>
                      ) : isMissing ? (
                        <span
                          style={{
                            color: '#B45309',
                            fontSize: 11,
                            fontWeight: 600,
                            background: '#FEF3C7',
                            padding: '3px 8px',
                            borderRadius: 12,
                            border: '1px solid #FDE68A',
                          }}
                        >
                          Required
                        </span>
                      ) : (
                        <span
                          style={{
                            color: '#64748B',
                            fontSize: 11,
                            background: '#F1F5F9',
                            padding: '3px 8px',
                            borderRadius: 12,
                          }}
                        >
                          Optional
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Card Footer Actions */}
        <div
          style={{
            background: '#F8FAFC',
            borderTop: '1px solid #E2E8F0',
            padding: '14px 20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: 12,
          }}
        >
          {/* Batch Options (Multi-record documents) */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexWrap: 'wrap' }}>
            {totalRecords > 1 ? (
              <label
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  fontSize: 12,
                  fontWeight: 600,
                  color: '#0F172A',
                  cursor: 'pointer',
                  userSelect: 'none',
                }}
              >
                <input
                  type="checkbox"
                  checked={applyToAll}
                  onChange={(e) => setApplyToAll(e.target.checked)}
                  style={{ width: 16, height: 16, accentColor: '#2563EB', cursor: 'pointer' }}
                />
                <span>Apply values to all {totalRecords} records in this document</span>
              </label>
            ) : (
              <span style={{ fontSize: 12, color: '#64748B' }}>
                Edit fields and click Save to re-run deterministic validation.
              </span>
            )}

            {applyToAll && masterType === 'business_partner' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#475569' }}>
                <span>Partner Name prefix:</span>
                <input
                  type="text"
                  value={cardNamePrefix}
                  onChange={(e) => setCardNamePrefix(e.target.value)}
                  className="form-input"
                  style={{ width: 90, height: 26, fontSize: 11, padding: '2px 6px' }}
                  placeholder="Client "
                />
                <span style={{ color: '#94A3B8' }}>(Generates "{cardNamePrefix}[CardCode]")</span>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {saveSuccessMsg && (
              <span
                style={{
                  fontSize: 12,
                  color: '#16A34A',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                }}
              >
                <CheckCircle2 size={14} /> {saveSuccessMsg}
              </span>
            )}

            <button
              type="submit"
              disabled={isSaving}
              className="btn btn-primary"
              style={{
                padding: '8px 18px',
                fontSize: 13,
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                background: isCurrentRecordValid ? '#16A34A' : '#2563EB',
                borderColor: isCurrentRecordValid ? '#15803D' : '#1D4ED8',
              }}
            >
              {isSaving ? (
                <>Saving & Validating...</>
              ) : applyToAll ? (
                <>
                  <Sparkles size={15} /> Apply & Validate All {totalRecords} Records
                </>
              ) : (
                <>
                  <Save size={15} /> Save & Validate Record #{activeRecordIndex + 1}
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
