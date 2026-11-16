import React, { useState, useEffect, useRef, useCallback } from 'react';
import '../styles/ai-agent.css';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import type { AgentHistoryRecord, AgentHistoryStats } from '../types';
import { VoiceInputButton } from '../components/VoiceInputButton';
import {
  Sparkles,
  Send,
  User,
  Users,
  RotateCcw,
  Edit3,
  X,
  Search,
  Building2,
  Package,
  Store,
  Zap,
  Lock,
  Copy,
  Check,
  Clock,
  ShieldCheck,
  History,
  MessageSquare,
  Filter,
  RefreshCw,
  ChevronRight,
  Plus,
  ArrowUp,
  BookOpen
} from 'lucide-react';

export interface MissingFieldItem {
  field: string;
  label: string;
  example?: string;
  reason?: string;
  max_length?: number;
}

export interface GranularAnswerData {
  attribute: string;
  value: string;
  code: string;
  name: string;
}

export interface ChatTurn {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  action?: string;
  entity?: 'BusinessPartners' | 'Items' | 'Warehouses' | string;
  records?: Record<string, any>[];
  total?: number;
  update_result?: {
    key: string;
    entity: string;
    updated_fields: Record<string, any>;
    old_values: Record<string, any>;
    new_values: Record<string, any>;
    hash?: string;
  };
  creation_draft?: Record<string, any>;
  missing_fields?: MissingFieldItem[];
  is_creation_ready?: boolean;
  granular_answer?: GranularAnswerData;
  suggestions?: string[];
  prompt?: string;
  query_type?: string;
  filters?: Record<string, any>;
  sources?: Array<{ document: string; section?: string; score?: number; page?: number }>;
}

/**
 * Rich Semantic Markdown Renderer.
 */
export const MarkdownRenderer: React.FC<{ text: string }> = ({ text }) => {
  if (!text) return null;

  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  let currentList: React.ReactNode[] = [];
  let listType: 'ul' | 'ol' | null = null;

  const renderInline = (lineText: string, keyPrefix: string): React.ReactNode[] => {
    const parts: React.ReactNode[] = [];
    const regex = /(\*\*.*?\*\*|\*.*?\*|`.*?`|https?:\/\/[^\s]+)/g;
    let lastIndex = 0;
    let match: RegExpExecArray | null;
    let partIdx = 0;

    while ((match = regex.exec(lineText)) !== null) {
      if (match.index > lastIndex) {
        parts.push(lineText.substring(lastIndex, match.index));
      }
      const token = match[0];
      const partKey = `${keyPrefix}-part-${partIdx++}`;

      if (token.startsWith('**') && token.endsWith('**')) {
        parts.push(
          <strong key={partKey} className="md-bold">
            {token.slice(2, -2)}
          </strong>
        );
      } else if (token.startsWith('*') && token.endsWith('*')) {
        parts.push(
          <em key={partKey} className="md-italic">
            {token.slice(1, -1)}
          </em>
        );
      } else if (token.startsWith('`') && token.endsWith('`')) {
        parts.push(
          <code key={partKey} className="md-code-pill">
            {token.slice(1, -1)}
          </code>
        );
      } else if (token.startsWith('http')) {
        parts.push(
          <a
            key={partKey}
            href={token}
            target="_blank"
            rel="noopener noreferrer"
            className="md-link"
          >
            {token}
          </a>
        );
      }
      lastIndex = regex.lastIndex;
    }

    if (lastIndex < lineText.length) {
      parts.push(lineText.substring(lastIndex));
    }
    return parts;
  };

  const flushList = () => {
    if (currentList.length > 0) {
      if (listType === 'ul') {
        elements.push(
          <ul key={`ul-${elements.length}`} className="md-list-ul">
            {currentList}
          </ul>
        );
      } else if (listType === 'ol') {
        elements.push(
          <ol key={`ol-${elements.length}`} className="md-list-ol">
            {currentList}
          </ol>
        );
      }
      currentList = [];
      listType = null;
    }
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();

    if (!trimmed) {
      flushList();
      return;
    }

    if (/^[•\-\*]\s+/.test(trimmed)) {
      if (listType !== 'ul') flushList();
      listType = 'ul';
      const cleanContent = trimmed.replace(/^[•\-\*]\s+/, '');
      currentList.push(
        <li key={`li-${idx}`} className="md-list-item">
          {renderInline(cleanContent, `li-${idx}`)}
        </li>
      );
    } else if (/^\d+\.\s+/.test(trimmed)) {
      if (listType !== 'ol') flushList();
      listType = 'ol';
      const cleanContent = trimmed.replace(/^\d+\.\s+/, '');
      currentList.push(
        <li key={`li-${idx}`} className="md-list-item">
          {renderInline(cleanContent, `li-${idx}`)}
        </li>
      );
    } else if (trimmed.startsWith('### ')) {
      flushList();
      elements.push(
        <h4 key={`h4-${idx}`} className="md-h4">
          {renderInline(trimmed.replace(/^###\s+/, ''), `h4-${idx}`)}
        </h4>
      );
    } else if (trimmed.startsWith('## ')) {
      flushList();
      elements.push(
        <h3 key={`h3-${idx}`} className="md-h3">
          {renderInline(trimmed.replace(/^##\s+/, ''), `h3-${idx}`)}
        </h3>
      );
    } else if (trimmed.startsWith('# ')) {
      flushList();
      elements.push(
        <h2 key={`h2-${idx}`} className="md-h2">
          {renderInline(trimmed.replace(/^#\s+/, ''), `h2-${idx}`)}
        </h2>
      );
    } else if (trimmed.startsWith('> ')) {
      flushList();
      elements.push(
        <blockquote key={`quote-${idx}`} className="md-quote">
          {renderInline(trimmed.replace(/^>\s+/, ''), `quote-${idx}`)}
        </blockquote>
      );
    } else {
      flushList();
      elements.push(
        <p key={`p-${idx}`} className="md-paragraph">
          {renderInline(trimmed, `p-${idx}`)}
        </p>
      );
    }
  });

  flushList();

  return <div className="md-rendered-content">{elements}</div>;
};

export const INITIAL_MESSAGES: ChatTurn[] = [
  {
    id: 'welcome-1',
    role: 'assistant',
    content: `👋 **Welcome to Hey CIRA — Your Autonomous SAP AI Agent!**\n\nConnected directly to **SAP Service Layer (Company DB: CINNTRA_DEMO_NEW)**.\n\n### **What you can trigger in natural language:**\n• **Dynamic Prompt Creation**: *"Create Business Partner"*, *"Add new Item"*, *"Register warehouse"*\n  *(Hey CIRA dynamically audits and asks for missing mandatory fields!)*\n• **Dynamic Field Updates**: *"Update customer phone & GST"*, *"Change phone to 9876543210 and GST to 27AABCU9603R1ZM for customer C20000"*\n• **Granular Querying**: *"What is the address of customer C20000?"*, *"What is the tax rate of item ITM-001?"*, *"Where is warehouse WH01 located?"*\n• **Live Master Data Tables**: *"List all Business Partners"*, *"List all Items"*, *"List all Warehouses"*\n\nType naturally or click any suggestion below to begin!`,
    timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    action: 'EXPLAIN',
    suggestions: [
      'Create Business Partner',
      'Add new Item',
      'Update customer phone & GST',
      'give items whose hsn code is not available',
      'What is the address of customer C20000?',
      'List all Business Partners'
    ]
  }
];

export interface PromptLibraryItem {
  id: string;
  category: 'items' | 'bp' | 'creation' | 'updates';
  badge: string;
  badgeBg: string;
  badgeColor: string;
  title: string;
  prompt: string;
  description: string;
}

export const ALL_TRAINED_PROMPTS: PromptLibraryItem[] = [
  // 8 Item Master Audits
  {
    id: 'item-1',
    category: 'items',
    badge: '📦 Active Items',
    badgeBg: '#ECFDF5',
    badgeColor: '#047857',
    title: 'Active Items Master Data',
    prompt: 'Show me all active items with Item Code, Item Name, Item Group and Inventory UoM.',
    description: 'Lists all unblocked, active items with codes, descriptions, group numbers, and stocking UoM.'
  },
  {
    id: 'item-2',
    category: 'items',
    badge: '⚠️ Compliance',
    badgeBg: '#FEF2F2',
    badgeColor: '#DC2626',
    title: 'Missing HSN or Inventory UoM',
    prompt: 'Find items where the HSN or Inventory UoM is missing.',
    description: 'Audits item master records with missing or invalid HSN codes or undefined inventory UoM.'
  },
  {
    id: 'item-3',
    category: 'items',
    badge: '🔍 Deduplication',
    badgeBg: '#EFF6FF',
    badgeColor: '#1A56DB',
    title: 'Duplicate / Similar Item Names',
    prompt: 'Find duplicate or similar item names in the Item Master.',
    description: 'Identifies clusters of identical or closely matching item descriptions across the database.'
  },
  {
    id: 'item-4',
    category: 'items',
    badge: '🗓️ Recent 30 Days',
    badgeBg: '#F3E8FF',
    badgeColor: '#7C3AED',
    title: 'Items Created in Last 30 Days',
    prompt: 'Show me all items created in the last 30 days with their creation date and creator.',
    description: 'Chronological timeline of newly onboarded items with creation dates and creator user IDs.'
  },
  {
    id: 'item-5',
    category: 'items',
    badge: '🚨 Blocked Stock Risk',
    badgeBg: '#FFFBEB',
    badgeColor: '#B45309',
    title: 'Inactive Items with Available Stock',
    prompt: 'Show me items that are inactive but still have stock available.',
    description: 'Detects frozen/inactive items that still hold physical warehouse inventory.'
  },
  {
    id: 'item-6',
    category: 'items',
    badge: '🏭 Warehouse Stock',
    badgeBg: '#EEF2FF',
    badgeColor: '#4F46E5',
    title: 'Stock in Each Warehouse',
    prompt: 'List items with stock available in each warehouse, including total quantity.',
    description: 'Per-warehouse inventory distribution and total stock across all active storage locations.'
  },
  {
    id: 'item-7',
    category: 'items',
    badge: '📊 Safety Stock',
    badgeBg: '#F0FDF4',
    badgeColor: '#15803D',
    title: 'Minimum & Maximum Item Details',
    prompt: 'Find the minimum and maximum item details',
    description: 'Compares on-hand stock against configured safety reorder thresholds (Min & Max stock).'
  },
  {
    id: 'item-8',
    category: 'items',
    badge: '🚚 Supply Chain',
    badgeBg: '#FDF4FF',
    badgeColor: '#A21CAF',
    title: 'Ordered & Committed Quantities',
    prompt: 'List item with ordered and committed quantity',
    description: 'Calculates net available stock considering customer purchase orders and vendor PO supply.'
  },

  // 8 Business Partner Audits
  {
    id: 'bp-1',
    category: 'bp',
    badge: '👥 Active Partners',
    badgeBg: '#EFF6FF',
    badgeColor: '#1A56DB',
    title: 'Active Customers & Vendors',
    prompt: 'Show me all active customers and vendors with their master data details.',
    description: 'Live active customers and suppliers with account balances, currency, and tax IDs.'
  },
  {
    id: 'bp-2',
    category: 'bp',
    badge: '📋 Incomplete Master',
    badgeBg: '#FEF2F2',
    badgeColor: '#DC2626',
    title: 'Incomplete Customer / Vendor Data',
    prompt: 'Find customers and vendors with missing or incomplete master data such as GSTIN, PAN, payment terms, currency or contact details.',
    description: 'Highlights critical data quality defects across GST, PAN, payment terms, and phone numbers.'
  },
  {
    id: 'bp-3',
    category: 'bp',
    badge: '🔍 Deduplication',
    badgeBg: '#EFF6FF',
    badgeColor: '#1A56DB',
    title: 'Duplicate Customer & Vendor Records',
    prompt: 'Identify duplicate or similar customer and vendor master records.',
    description: 'Scans for duplicate company names, phone numbers, and shared GSTIN/PAN registrations.'
  },
  {
    id: 'bp-4',
    category: 'bp',
    badge: '🗓️ Recent 30 Days',
    badgeBg: '#F3E8FF',
    badgeColor: '#7C3AED',
    title: 'Partners Created in Last 30 Days',
    prompt: 'Show me customers and vendors created in the last 30 days, including creation date and creator.',
    description: 'Recent onboarding history of customers and suppliers with creator information.'
  },
  {
    id: 'bp-5',
    category: 'bp',
    badge: '🇮🇳 GST / PAN Audit',
    badgeBg: '#FFF7ED',
    badgeColor: '#C2410C',
    title: 'Missing or Incorrect GSTIN / PAN',
    prompt: 'Find customers and vendors with missing or incorrect GSTIN/PAN details.',
    description: 'Statutory compliance validation checking 15-character GSTIN and 10-character PAN syntax.'
  },
  {
    id: 'bp-6',
    category: 'bp',
    badge: '🏦 Banking & Terms',
    badgeBg: '#EEF2FF',
    badgeColor: '#4338CA',
    title: 'Vendors Missing Payment Terms / Bank',
    prompt: 'Show me vendors with missing payment terms, bank details or payment methods.',
    description: 'Ensures accounts payable governance by catching vendors with unconfigured payment methods.'
  },
  {
    id: 'bp-7',
    category: 'bp',
    badge: '⚠️ Inactive Balance',
    badgeBg: '#FEF3C7',
    badgeColor: '#D97706',
    title: 'Inactive Partners with Outstanding Balances',
    prompt: 'Identify inactive customers or vendors who still have outstanding balances.',
    description: 'Flags inactive accounts with trapped receivables or uncleared supplier liability.'
  },
  {
    id: 'bp-8',
    category: 'bp',
    badge: '⏳ Aging Analysis',
    badgeBg: '#F0F9FF',
    badgeColor: '#0369A1',
    title: 'Overdue Balances & Aging Details',
    prompt: 'Show me customers and vendors with overdue balances and their aging details.',
    description: 'Lists accounts receivable & payable aging delay days and delinquent accounts.'
  },

  // Creation Studio & Updates
  {
    id: 'create-1',
    category: 'creation',
    badge: '✨ Fast Creation',
    badgeBg: '#F5F3FF',
    badgeColor: '#6D28D9',
    title: 'Create Business Partner',
    prompt: 'Create a Business Partner',
    description: 'Launches interactive slot-filling creation workflow for customers or suppliers.'
  },
  {
    id: 'create-2',
    category: 'creation',
    badge: '✨ Fast Creation',
    badgeBg: '#F5F3FF',
    badgeColor: '#6D28D9',
    title: 'Create Item Master',
    prompt: 'Create an Item Master',
    description: 'Interactive conversational draft creation for items with UoM, pricing, and grouping.'
  },
  {
    id: 'create-3',
    category: 'creation',
    badge: '✨ Fast Creation',
    badgeBg: '#F5F3FF',
    badgeColor: '#6D28D9',
    title: 'Create Warehouse Master',
    prompt: 'Create a Warehouse',
    description: 'Registers a new warehouse location directly into SAP Business One Service Layer.'
  },
  {
    id: 'update-1',
    category: 'updates',
    badge: '⚡ Field Patch',
    badgeBg: '#FEF3C7',
    badgeColor: '#B45309',
    title: 'Update Customer Phone & GST',
    prompt: 'Update customer phone & GST',
    description: 'Prompts for Customer Code, Phone, and GSTIN to dynamically patch SAP Business Partner.'
  },
  {
    id: 'update-2',
    category: 'updates',
    badge: '⚡ Field Patch',
    badgeBg: '#FEF3C7',
    badgeColor: '#B45309',
    title: 'Update Item Name & Price',
    prompt: 'Update item name and price',
    description: 'Dynamically prompts for ItemCode, new ItemName, and Price to patch Item Master.'
  }
];

export const PROMPT_CATEGORIES = [
  {
    title: '📦 Item Master Audits',
    items: [
      { label: 'Active Items', prompt: 'Show me all active items with Item Code, Item Name, Item Group and Inventory UoM.' },
      { label: 'Missing HSN / UoM', prompt: 'Find items where the HSN or Inventory UoM is missing.' },
      { label: 'Duplicate Items', prompt: 'Find duplicate or similar item names in the Item Master.' },
      { label: 'Created in 30 Days', prompt: 'Show me all items created in the last 30 days with their creation date and creator.' },
      { label: 'Inactive with Stock', prompt: 'Show me items that are inactive but still have stock available.' },
      { label: 'Warehouse Stock', prompt: 'List items with stock available in each warehouse, including total quantity.' },
      { label: 'Min & Max Details', prompt: 'Find the minimum and maximum item details' },
      { label: 'Ordered & Committed', prompt: 'List item with ordered and committed quantity' }
    ]
  },
  {
    title: '👥 Business Partner Audits',
    items: [
      { label: 'Active Partners', prompt: 'Show me all active customers and vendors with their master data details.' },
      { label: 'Incomplete Master Data', prompt: 'Find customers and vendors with missing or incomplete master data such as GSTIN, PAN, payment terms, currency or contact details.' },
      { label: 'Duplicate Records', prompt: 'Identify duplicate or similar customer and vendor master records.' },
      { label: 'Created in 30 Days', prompt: 'Show me customers and vendors created in the last 30 days, including creation date and creator.' },
      { label: 'GSTIN / PAN Audit', prompt: 'Find customers and vendors with missing or incorrect GSTIN/PAN details.' },
      { label: 'Missing Terms & Bank', prompt: 'Show me vendors with missing payment terms, bank details or payment methods.' },
      { label: 'Inactive with Balance', prompt: 'Identify inactive customers or vendors who still have outstanding balances.' },
      { label: 'Overdue Aging', prompt: 'Show me customers and vendors with overdue balances and their aging details.' }
    ]
  },
  {
    title: '✨ Creation Studio',
    items: [
      { label: 'New Business Partner', prompt: 'Create Business Partner' },
      { label: 'New Item Master', prompt: 'Add new Item' },
      { label: 'New Warehouse', prompt: 'Create a Warehouse' }
    ]
  },
  {
    title: '⚡ Field Updates & Health',
    items: [
      { label: 'Update Customer Phone & GST', prompt: 'Update customer phone & GST' },
      { label: 'Update Item Name & Price', prompt: 'Update item name and price' },
      { label: 'Check SAP Health', prompt: 'Check SAP Health' }
    ]
  }
];

export const AVAILABLE_ENTITY_FIELDS: Record<string, { field: string; label: string }[]> = {
  BusinessPartners: [
    { field: 'CardCode', label: 'Customer / Vendor Code (CardCode)' },
    { field: 'CardName', label: 'Company / Partner Name (CardName)' },
    { field: 'Address', label: 'Registered Address (Address)' },
    { field: 'City', label: 'City' },
    { field: 'State', label: 'State' },
    { field: 'ZipCode', label: 'Zip / Postal Code' },
    { field: 'Country', label: 'Country' },
    { field: 'Phone1', label: 'Primary Phone (Phone1)' },
    { field: 'EmailAddress', label: 'Email Address' },
    { field: 'GSTNo', label: 'GST Number (GSTIN)' },
    { field: 'PANNo', label: 'PAN Number (PANNo)' },
    { field: 'CardType', label: 'Type (cCustomer / cSupplier)' },
    { field: 'PaymentTerms', label: 'Payment Terms' },
    { field: 'Currency', label: 'Currency (INR / USD / EUR)' },
    { field: 'ControlAccount', label: 'GL Control Account' }
  ],
  Items: [
    { field: 'ItemCode', label: 'Item Code / SKU (ItemCode)' },
    { field: 'ItemName', label: 'Item Name / Description (ItemName)' },
    { field: 'InventoryUOM', label: 'Unit of Measure (InventoryUOM)' },
    { field: 'ItemsGroupCode', label: 'Item Group Code (ItemsGroupCode)' },
    { field: 'TaxRate', label: 'Tax Rate % (TaxRate)' },
    { field: 'HSN', label: 'HSN / SAC Code (HSN)' },
    { field: 'Price', label: 'Standard Price' },
    { field: 'ItemType', label: 'Item Type (Inventory/Sales/Purchase)' },
    { field: 'MaterialType', label: 'Material Type (RM/FG)' },
    { field: 'ItemManagementMethod', label: 'Management Method (None/Batch/Serial)' }
  ],
  Warehouses: [
    { field: 'WarehouseCode', label: 'Warehouse Code (WarehouseCode)' },
    { field: 'WarehouseName', label: 'Warehouse Name (WarehouseName)' },
    { field: 'Address', label: 'Physical Street Address (Address)' },
    { field: 'City', label: 'City' },
    { field: 'State', label: 'State' },
    { field: 'Location', label: 'Location Code' }
  ]
};

interface EmbeddedTableProps {
  turnId: string;
  entity: 'BusinessPartners' | 'Items' | 'Warehouses' | string;
  records: Record<string, any>[];
  total?: number;
  companyDb: string;
  onQuickEdit: (record: Record<string, any>, entity: string) => void;
  isUpdateRecord?: boolean;
  prompt?: string;
  queryType?: string;
}

interface ColumnDef {
  key: string;
  header: string;
  isEssential?: boolean;
  essentialTag?: string;
  render: (row: Record<string, any>) => React.ReactNode;
}

const buildDynamicColumns = (
  entity: string,
  prompt: string = '',
  records: Record<string, any>[],
  queryType?: string,
  onQuickEdit?: (record: Record<string, any>, entity: string) => void
): ColumnDef[] => {
  const p = prompt.toLowerCase().trim();
  const hasField = (f: string) => records.some((r) => r[f] !== undefined && r[f] !== null);

  // Intent Detection Flags
  const isHsnPrompt = p.includes('hsn') || p.includes('sac') || p.includes('tariff') || p.includes('chapter') || queryType === 'missing_hsn_uom' || hasField('HSN');
  const isActivePrompt = p.includes('active') || p.includes('inactive') || p.includes('status') || p.includes('frozen') || p.includes('valid') || p.includes('deactivat') || queryType === 'active_items' || queryType === 'inactive_items_with_stock' || queryType === 'active_customers_vendors' || queryType === 'inactive_bp_with_balance' || hasField('Status') || entity === 'Warehouses';
  const isBalancePrompt = p.includes('balance') || p.includes('overdue') || p.includes('aging') || p.includes('debt') || p.includes('receivable') || p.includes('payable') || queryType === 'inactive_bp_with_balance' || queryType === 'overdue_aging_bp' || hasField('Aging_0_30') || hasField('FormattedBalance');
  const isAgingPrompt = p.includes('aging') || p.includes('overdue') || queryType === 'overdue_aging_bp' || hasField('Aging_0_30');
  const isStockPrompt = p.includes('stock') || p.includes('inventory') || p.includes('quantity') || p.includes('onhand') || p.includes('available') || p.includes('qty');
  const isPricePrompt = p.includes('price') || p.includes('cost') || p.includes('rate') || p.includes('expensive') || p.includes('cheap');
  const isGstPanPrompt = p.includes('gst') || p.includes('pan') || p.includes('tax') || p.includes('urp') || p.includes('unregistered') || queryType === 'missing_incorrect_gstin_pan';
  const isPanSpecific = p.includes('pan') || hasField('PANNo') || hasField('U_panno');
  const isLocationPrompt = p.includes('address') || p.includes('city') || p.includes('state') || p.includes('street') || p.includes('delhi') || p.includes('mumbai') || p.includes('pune') || p.includes('bangalore') || p.includes('kolkata') || p.includes('chennai') || p.includes('hyderabad') || p.includes('gurgaon');
  const isDatePrompt = p.includes('creat') || p.includes('date') || p.includes('last 30') || p.includes('recent') || queryType === 'items_last_30_days' || queryType === 'bp_last_30_days' || hasField('CreateDate');
  const isTermsPrompt = p.includes('payment') || p.includes('term') || p.includes('bank') || queryType === 'vendors_missing_terms_bank' || hasField('PaymentTerms') || hasField('HouseBank');
  const isUomPrompt = p.includes('uom') || p.includes('unit') || queryType === 'missing_hsn_uom';
  const isMinMaxPrompt = p.includes('minimum') || p.includes('maximum') || p.includes('min') || p.includes('max') || queryType === 'min_max_items' || hasField('MinInventory');
  const isOrderCommitPrompt = p.includes('ordered') || p.includes('committed') || queryType === 'ordered_committed_items' || hasField('QuantityOrderedByCustomers');
  const isDuplicatePrompt = p.includes('duplicate') || p.includes('similar') || queryType === 'duplicate_items' || queryType === 'duplicate_bp' || hasField('Similarity');

  const cols: ColumnDef[] = [];
  const added = new Set<string>();

  const addCol = (col: ColumnDef) => {
    if (!added.has(col.key)) {
      added.add(col.key);
      cols.push(col);
    }
  };

  if (entity === 'Items') {
    // Primary identifiers
    addCol({
      key: 'ItemCode',
      header: 'Item Code',
      render: (r) => <span className="table-code-pill item">{r.ItemCode || r._key || '—'}</span>
    });
    addCol({
      key: 'ItemName',
      header: 'Item Description',
      render: (r) => <span style={{ fontWeight: 600 }}>{r.ItemName || '—'}</span>
    });

    // 1. HSN Column (Prominently placed if HSN prompt!)
    if (isHsnPrompt) {
      addCol({
        key: 'HSN',
        header: 'HSN / SAC Code',
        isEssential: true,
        essentialTag: 'HSN Target',
        render: (r) => {
          const raw = r.HSN || (r.ChapterID && r.ChapterID !== -1 && r.ChapterID !== '-1' ? String(r.ChapterID) : null);
          const isMissing = !raw || ['none', 'null', '-1', 'not assigned (-1)', '', '0'].includes(String(raw).trim().toLowerCase());
          return isMissing ? (
            <span className="agent-badge-missing">⚠️ Missing HSN</span>
          ) : (
            <span className="table-code-pill hsn">{raw}</span>
          );
        }
      });
    }

    // 2. Status Column (Active / Inactive)
    if (isActivePrompt) {
      addCol({
        key: 'Status',
        header: 'Status',
        isEssential: true,
        essentialTag: p.includes('inactive') ? 'Inactive Filter' : 'Active Status',
        render: (r) => {
          let isActive = true;
          if (r.Status) {
            const s = String(r.Status).toLowerCase();
            isActive = !s.includes('inactive') && !s.includes('frozen') && !s.includes('🔴');
          } else {
            isActive = r.Valid !== 'tNO' && r.Frozen !== 'tYES' && r.Inactive !== 'tYES';
          }
          return isActive ? (
            <span className="agent-status-tag active">🟢 Active</span>
          ) : (
            <span className="agent-status-tag inactive">🔴 Inactive</span>
          );
        }
      });
    }

    // 3. Ordered & Committed
    if (isOrderCommitPrompt) {
      addCol({
        key: 'Committed',
        header: 'Committed Qty',
        isEssential: true,
        render: (r) => <span style={{ fontWeight: 700, color: '#2563EB' }}>{r.QuantityOrderedByCustomers ?? r.Committed ?? 0}</span>
      });
      addCol({
        key: 'Ordered',
        header: 'Ordered Qty',
        isEssential: true,
        render: (r) => <span style={{ fontWeight: 700, color: '#D97706' }}>{r.QuantityOrderedFromVendors ?? r.Ordered ?? 0}</span>
      });
    }

    // 5. Min / Max
    if (isMinMaxPrompt) {
      addCol({
        key: 'MinInventory',
        header: 'Min Stock',
        isEssential: true,
        render: (r) => <span style={{ fontWeight: 600 }}>{r.MinInventory ?? 0}</span>
      });
      addCol({
        key: 'MaxInventory',
        header: 'Max Stock',
        isEssential: true,
        render: (r) => <span style={{ fontWeight: 600 }}>{r.MaxInventory ?? 0}</span>
      });
    }

    // 6. Duplicate / Similar
    if (isDuplicatePrompt) {
      addCol({
        key: 'MatchType',
        header: 'Match Classification',
        isEssential: true,
        render: (r) => <span className="agent-badge-audit">{r.MatchType || 'Duplicate'}</span>
      });
      addCol({
        key: 'Similarity',
        header: 'Similarity',
        isEssential: true,
        render: (r) => <span style={{ fontWeight: 700, color: '#DC2626' }}>{r.Similarity || '100%'}</span>
      });
    }

    // 7. Created Date
    if (isDatePrompt) {
      addCol({
        key: 'CreateDate',
        header: 'Created Date',
        isEssential: true,
        render: (r) => <span style={{ fontSize: 11.5 }}>{r.CreateDate ? String(r.CreateDate).split('T')[0] : '—'}</span>
      });
    }

    // Secondary & contextual columns
    addCol({
      key: 'InventoryUOM',
      header: 'UoM',
      isEssential: isUomPrompt,
      essentialTag: isUomPrompt ? 'UoM Spec' : undefined,
      render: (r) => <span className="agent-uom-tag">{r.InventoryUOM || r.SalesUnit || 'PCS'}</span>
    });

    addCol({
      key: 'QuantityOnStock',
      header: 'In Stock',
      isEssential: isStockPrompt,
      essentialTag: isStockPrompt ? 'Stock Level' : undefined,
      render: (r) => {
        const stk = r.QuantityOnStock ?? r.OnHand ?? '—';
        return <span style={{ fontWeight: 700, color: Number(stk) > 0 ? '#047857' : '#EF4444' }}>{stk}</span>;
      }
    });

    addCol({
      key: 'Price',
      header: 'Price',
      isEssential: isPricePrompt,
      essentialTag: isPricePrompt ? 'Price Query' : undefined,
      render: (r) => {
        const pr = r.Price ?? r.MovingAveragePrice;
        return pr !== undefined && pr !== null ? `₹${Number(pr).toLocaleString('en-IN')}` : '—';
      }
    });

    if (cols.length < 7) {
      addCol({
        key: 'ItemsGroupCode',
        header: 'Group',
        render: (r) => <span>{r.ItemsGroupCode || '100'}</span>
      });
    }

    // Always ensure Status is shown if not already added and space permits
    if (!added.has('Status') && cols.length < 8) {
      addCol({
        key: 'Status',
        header: 'Status',
        render: (r) => {
          const isActive = r.Valid !== 'tNO' && r.Frozen !== 'tYES' && r.Inactive !== 'tYES';
          return isActive ? (
            <span className="agent-status-tag active">🟢 Active</span>
          ) : (
            <span className="agent-status-tag inactive">🔴 Inactive</span>
          );
        }
      });
    }

  } else if (entity === 'BusinessPartners') {
    // Primary identifiers
    addCol({
      key: 'CardCode',
      header: 'Code',
      render: (r) => <span className="table-code-pill bp">{r.CardCode || r._key || '—'}</span>
    });
    addCol({
      key: 'CardName',
      header: 'Partner Name',
      render: (r) => <span style={{ fontWeight: 600 }}>{r.CardName || '—'}</span>
    });

    // 1. Status Column (Active / Inactive)
    if (isActivePrompt) {
      addCol({
        key: 'Status',
        header: 'Status',
        isEssential: true,
        essentialTag: p.includes('inactive') ? 'Inactive Filter' : 'Active Status',
        render: (r) => {
          let isActive = true;
          if (r.Status) {
            const s = String(r.Status).toLowerCase();
            isActive = !s.includes('inactive') && !s.includes('frozen') && !s.includes('🔴');
          } else {
            isActive = r.Valid !== 'tNO' && r.Frozen !== 'tYES' && r.Inactive !== 'tYES';
          }
          return isActive ? (
            <span className="agent-status-tag active">🟢 Active</span>
          ) : (
            <span className="agent-status-tag inactive">🔴 Inactive</span>
          );
        }
      });
    }

    // 2. Balance Column
    if (isBalancePrompt) {
      addCol({
        key: 'CurrentAccountBalance',
        header: isAgingPrompt ? 'Total Overdue' : 'Account Balance',
        isEssential: true,
        essentialTag: 'Balance Audit',
        render: (r) => {
          const raw = r.CurrentAccountBalance ?? r.Balance ?? 0;
          const num = typeof raw === 'number' ? raw : parseFloat(String(raw).replace(/[^0-9.-]/g, '')) || 0;
          return (
            <span style={{ fontWeight: 700, color: num > 0 ? '#DC2626' : num < 0 ? '#2563EB' : '#059669' }}>
              {r.FormattedBalance || `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
            </span>
          );
        }
      });

      if (isAgingPrompt && hasField('Aging_0_30')) {
        addCol({
          key: 'Aging_0_30',
          header: '0-30 Days',
          isEssential: true,
          render: (r) => <span>{r.Aging_0_30 || '₹0'}</span>
        });
        addCol({
          key: 'Aging_31_60',
          header: '31-60 Days',
          isEssential: true,
          render: (r) => <span>{r.Aging_31_60 || '₹0'}</span>
        });
        addCol({
          key: 'Aging_61_90',
          header: '61-90 Days',
          isEssential: true,
          render: (r) => <span>{r.Aging_61_90 || '₹0'}</span>
        });
        addCol({
          key: 'Aging_90_plus',
          header: '90+ Days',
          isEssential: true,
          render: (r) => <span style={{ color: '#DC2626', fontWeight: 600 }}>{r.Aging_90_plus || '₹0'}</span>
        });
        addCol({
          key: 'AvgLateDays',
          header: 'Avg Late',
          render: (r) => <span>{r.AvgLateDays || 'Current'}</span>
        });
      }
    }

    // 3. GSTIN / Tax ID
    if (isGstPanPrompt) {
      addCol({
        key: 'GSTNo',
        header: 'GSTIN / Tax ID',
        isEssential: true,
        essentialTag: 'GSTIN Audit',
        render: (r) => {
          const tax = r.GSTNo || r.FederalTaxID;
          const isMissing = !tax || ['NONE', 'NULL', 'UNREGISTERED', 'URP', 'N/A', 'NA', ''].includes(String(tax).trim().toUpperCase());
          return isMissing ? (
            <span className="agent-badge-missing">⚠️ Missing / URP</span>
          ) : (
            <code style={{ fontSize: 11, fontWeight: 700 }}>{tax}</code>
          );
        }
      });

      if (isPanSpecific || hasField('PANNo') || hasField('U_panno')) {
        addCol({
          key: 'PANNo',
          header: 'PAN Number',
          isEssential: true,
          essentialTag: 'PAN Audit',
          render: (r) => {
            const pan = r.PANNo || r.U_panno;
            const isMissing = !pan || ['NONE', 'NULL', 'N/A', 'NA', ''].includes(String(pan).trim().toUpperCase());
            return isMissing ? (
              <span className="agent-badge-missing">⚠️ Missing</span>
            ) : (
              <code style={{ fontSize: 11, fontWeight: 700 }}>{pan}</code>
            );
          }
        });
      }
    }

    // 4. Payment Terms & Bank
    if (isTermsPrompt) {
      addCol({
        key: 'PaymentTerms',
        header: 'Payment Terms',
        isEssential: true,
        render: (r) => {
          const terms = r.PaymentTerms || r.PayTermsGrpCode;
          return !terms || terms === 'None' || terms === 'Missing' ? (
            <span className="agent-badge-missing">⚠️ Missing Terms</span>
          ) : (
            <span>{terms}</span>
          );
        }
      });
      if (hasField('HouseBank') || p.includes('bank')) {
        addCol({
          key: 'HouseBank',
          header: 'Bank Details',
          isEssential: true,
          render: (r) => {
            const b = r.HouseBank || r.HouseBankAccount;
            return !b || b === 'None' || b === 'Missing' ? (
              <span className="agent-badge-missing">⚠️ Missing Bank</span>
            ) : (
              <span>{b}</span>
            );
          }
        });
      }
    }

    // 6. Created Date
    if (isDatePrompt) {
      addCol({
        key: 'CreateDate',
        header: 'Created Date',
        isEssential: true,
        render: (r) => <span style={{ fontSize: 11.5 }}>{r.CreateDate ? String(r.CreateDate).split('T')[0] : '—'}</span>
      });
    }

    // 7. Duplicate / Similarity
    if (isDuplicatePrompt) {
      addCol({
        key: 'MatchType',
        header: 'Match Type',
        isEssential: true,
        render: (r) => <span className="agent-badge-audit">{r.MatchType || 'Duplicate'}</span>
      });
      addCol({
        key: 'Similarity',
        header: 'Similarity',
        isEssential: true,
        render: (r) => <span style={{ fontWeight: 700, color: '#DC2626' }}>{r.Similarity || '100%'}</span>
      });
    }

    // Secondary & contextual columns
    addCol({
      key: 'CardType',
      header: 'Type',
      isEssential: p.includes('customer') || p.includes('vendor') || p.includes('supplier'),
      render: (r) => <span className="agent-status-tag">{r.CardType === 'cCustomer' || r.CardType === 'Customer' ? 'Customer' : 'Supplier'}</span>
    });

    addCol({
      key: 'Phone1',
      header: 'Phone',
      isEssential: p.includes('phone') || p.includes('contact'),
      render: (r) => <span>{r.Phone1 || r.Phone || '—'}</span>
    });

    if (!added.has('GSTNo')) {
      addCol({
        key: 'GSTNo',
        header: 'GST/Tax',
        render: (r) => <code style={{ fontSize: 11 }}>{r.GSTNo || r.FederalTaxID || '—'}</code>
      });
    }

    addCol({
      key: 'City',
      header: 'City',
      isEssential: isLocationPrompt,
      essentialTag: isLocationPrompt ? 'Location' : undefined,
      render: (r) => <span>{r.City || r.Address || '—'}</span>
    });

    if (isLocationPrompt && (p.includes('address') || p.includes('street'))) {
      addCol({
        key: 'Address',
        header: 'Address',
        isEssential: true,
        render: (r) => <span>{r.Address || r.Street || '—'}</span>
      });
    }

    if (!added.has('CurrentAccountBalance') && cols.length < 8) {
      addCol({
        key: 'CurrentAccountBalance',
        header: 'Balance',
        render: (r) => {
          const raw = r.CurrentAccountBalance ?? r.Balance ?? 0;
          const num = typeof raw === 'number' ? raw : parseFloat(String(raw).replace(/[^0-9.-]/g, '')) || 0;
          return <span>₹{num.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>;
        }
      });
    }

    if (!added.has('Status') && cols.length < 8) {
      addCol({
        key: 'Status',
        header: 'Status',
        render: (r) => {
          const isActive = r.Valid !== 'tNO' && r.Frozen !== 'tYES' && r.Inactive !== 'tYES';
          return isActive ? (
            <span className="agent-status-tag active">🟢 Active</span>
          ) : (
            <span className="agent-status-tag inactive">🔴 Inactive</span>
          );
        }
      });
    }

  } else {
    // Warehouses
    addCol({
      key: 'WarehouseCode',
      header: 'Whs Code',
      render: (r) => <span className="table-code-pill wh">{r.WarehouseCode || r._key || '—'}</span>
    });
    addCol({
      key: 'WarehouseName',
      header: 'Warehouse Name',
      render: (r) => <span style={{ fontWeight: 600 }}>{r.WarehouseName || '—'}</span>
    });

    addCol({
      key: 'City',
      header: 'City',
      isEssential: isLocationPrompt,
      essentialTag: isLocationPrompt ? 'Location' : undefined,
      render: (r) => <span>{r.City || '—'}</span>
    });

    addCol({
      key: 'State',
      header: 'State',
      isEssential: isLocationPrompt,
      render: (r) => <span>{r.State || '—'}</span>
    });

    if (isLocationPrompt || p.includes('address') || p.includes('street')) {
      addCol({
        key: 'Street',
        header: 'Physical Street Address',
        isEssential: true,
        essentialTag: 'Address',
        render: (r) => <span>{r.Street || r.Address || '—'}</span>
      });
    }

    addCol({
      key: 'Location',
      header: 'Location Code',
      render: (r) => <span>{r.Location || '1'}</span>
    });

    addCol({
      key: 'Status',
      header: 'Status',
      isEssential: isActivePrompt,
      essentialTag: isActivePrompt ? 'Status' : undefined,
      render: (r) => {
        const isActive = r.Inactive !== 'tYES' && r.Inactive !== 'Inactive';
        return isActive ? (
          <span className="agent-status-tag active">🟢 Active</span>
        ) : (
          <span className="agent-status-tag inactive">🔴 Inactive</span>
        );
      }
    });
  }

  // Action button is always last
  addCol({
    key: '__action__',
    header: 'Action',
    render: (r) => (
      <button
        type="button"
        onClick={() => onQuickEdit && onQuickEdit(r, entity)}
        className="agent-table-action-btn"
        title="Quick Edit Field"
      >
        <Edit3 size={13} /> Edit
      </button>
    )
  });

  return cols;
};

const InteractiveMasterDataTable: React.FC<EmbeddedTableProps> = ({
  entity,
  records,
  total,
  companyDb,
  onQuickEdit,
  isUpdateRecord,
  prompt = '',
  queryType
}) => {
  const [filterText, setFilterText] = useState('');

  if (!records || records.length === 0) return null;

  const columns = buildDynamicColumns(entity, prompt, records, queryType, onQuickEdit);

  const filtered = records.filter((r) => {
    if (!filterText.trim()) return true;
    const q = filterText.toLowerCase();
    return Object.values(r).some((v) => String(v).toLowerCase().includes(q));
  });

  const essentialCols = columns.filter((c) => c.isEssential && c.key !== '__action__');

  return (
    <div className={`agent-embedded-table-card ${isUpdateRecord ? 'update-highlight' : ''}`}>
      <div className="agent-embedded-table-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          {entity === 'BusinessPartners' ? <Building2 size={16} color="#2563EB" /> : entity === 'Items' ? <Package size={16} color="#059669" /> : <Store size={16} color="#7C3AED" />}
          <span style={{ fontWeight: 700, fontSize: 13, color: '#0F172A' }}>
            {entity === 'BusinessPartners' ? 'Live Business Partners Catalog' : entity === 'Items' ? 'Live Item Master Catalog' : 'Live Warehouse Depots'}
          </span>
          <span className="agent-embedded-count-badge">
            {total || records.length} records • {companyDb}
          </span>
          {essentialCols.map((c) => (
            <span key={c.key} className="essential-header-badge" style={{ fontSize: 10, padding: '2px 7px' }}>
              🎯 {c.header} ({c.essentialTag || 'Prompt Target'})
            </span>
          ))}
        </div>

        <div className="table-search-input-box">
          <Search size={13} color="#94A3B8" />
          <input
            type="text"
            placeholder="Search records..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            className="table-search-field"
          />
        </div>
      </div>

      <div className="agent-embedded-table-body">
        <table className="agent-rich-table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col.key} className={col.isEssential ? 'essential-col-th' : ''}>
                  <div style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                    <span>{col.header}</span>
                    {col.isEssential && (
                      <span className="essential-header-badge" title={col.essentialTag || 'Prompt Target'}>
                        ★ {col.essentialTag || 'Target'}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((row, idx) => (
              <tr key={idx}>
                {columns.map((col) => (
                  <td key={col.key} className={col.isEssential ? 'essential-col-td' : ''}>
                    {col.render(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export const AiAgentPage: React.FC = () => {
  // Mode switch: 'copilot' (interactive dialogue) vs 'history' (audit ledger)
  const { activeCompanyDb } = useAuth();
  const [activeView, setActiveView] = useState<'copilot' | 'history'>('copilot');

  // Copilot Chat State
  const [messages, setMessages] = useState<ChatTurn[]>(() => {
    const saved = localStorage.getItem('cinntra_ai_chat_history');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.some((m) => m.role === 'user')) return parsed;
      } catch (e) {}
    }
    return [];
  });

  const [inputValue, setInputValue] = useState('');
  const [voiceAutoSend, setVoiceAutoSend] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [companyDb, setCompanyDb] = useState(activeCompanyDb || 'TEST_SHOES_10SEP26');
  const [sapConnected, setSapConnected] = useState(true);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showPlusMenu, setShowPlusMenu] = useState(false);
  const [speechLanguage, setSpeechLanguage] = useState('en-IN');

  useEffect(() => {
    if (!showPlusMenu) return;
    const handleDocClick = () => setShowPlusMenu(false);
    window.addEventListener('click', handleDocClick);
    return () => window.removeEventListener('click', handleDocClick);
  }, [showPlusMenu]);

  // Quick edit modal
  const [editingRecord, setEditingRecord] = useState<Record<string, any> | null>(null);
  const [editingEntity, setEditingEntity] = useState<string>('BusinessPartners');
  const [editFieldName, setEditFieldName] = useState<string>('CardName');
  const [editFieldValue, setEditFieldValue] = useState<string>('');
  const [isUpdatingField, setIsUpdatingField] = useState(false);

  // AI Agent History & Ledger State
  const [historyRecords, setHistoryRecords] = useState<AgentHistoryRecord[]>([]);
  const [historyTotal, setHistoryTotal] = useState<number>(0);
  const [historyStats, setHistoryStats] = useState<AgentHistoryStats | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [historyEntityFilter, setHistoryEntityFilter] = useState<string>('all');
  const [historyActionFilter, setHistoryActionFilter] = useState<string>('all');
  const [historySearch, setHistorySearch] = useState<string>('');
  const [historyDays, setHistoryDays] = useState<number | null>(30);

  // Prompt Library Modal State
  const [showPromptModal, setShowPromptModal] = useState(false);
  const [promptCategoryFilter, setPromptCategoryFilter] = useState<'all' | 'items' | 'bp' | 'creation' | 'updates'>('all');
  const [promptSearchTerm, setPromptSearchTerm] = useState('');

  const chatEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Filtered list of certified master data prompts
  const filteredPrompts = ALL_TRAINED_PROMPTS.filter((p) => {
    const matchesCat = promptCategoryFilter === 'all' || p.category === promptCategoryFilter;
    const term = promptSearchTerm.toLowerCase().trim();
    const matchesSearch =
      !term ||
      p.prompt.toLowerCase().includes(term) ||
      p.title.toLowerCase().includes(term) ||
      p.description.toLowerCase().includes(term);
    return matchesCat && matchesSearch;
  });

  // Save chat to localStorage on change
  useEffect(() => {
    try {
      localStorage.setItem('cinntra_ai_chat_history', JSON.stringify(messages));
    } catch (e) { }
  }, [messages]);

  // Fetch history records & stats
  const fetchHistory = useCallback(async () => {
    setLoadingHistory(true);
    try {
      const [histRes, statsRes] = await Promise.allSettled([
        api.getAgentHistory({
          limit: 100,
          days: historyDays,
          entity: historyEntityFilter !== 'all' ? historyEntityFilter : undefined,
          action: historyActionFilter !== 'all' ? historyActionFilter : undefined,
          search: historySearch.trim() || undefined
        }),
        api.getAgentHistoryStats()
      ]);

      if (histRes.status === 'fulfilled' && histRes.value) {
        setHistoryRecords(histRes.value.records || []);
        setHistoryTotal(histRes.value.total || 0);
      }
      if (statsRes.status === 'fulfilled' && statsRes.value) {
        setHistoryStats(statsRes.value);
      }
    } catch (err) {
      console.error('Failed to load agent history', err);
    } finally {
      setLoadingHistory(false);
    }
  }, [historyDays, historyEntityFilter, historyActionFilter, historySearch]);

  useEffect(() => {
    checkHealth();
    fetchHistory();
  }, [fetchHistory]);

  useEffect(() => {
    if (activeView === 'copilot') {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading, activeView]);

  const checkHealth = async () => {
    try {
      const res = await api.getSapHealth();
      if (res.company_db) setCompanyDb(res.company_db);
      setSapConnected(Boolean(res.connected || res.status === 'CONNECTED' || (res as any)?.data?.connected));
      if ((res as any).latency_ms) setLatencyMs(Math.round((res as any).latency_ms));
    } catch {
      // Keep optimistic defaults
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSendMessage = async (customPrompt?: string) => {
    const promptToSend = customPrompt || inputValue;
    if (!promptToSend.trim() || isLoading) return;

    const userTurn: ChatTurn = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: promptToSend.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const newHistory = [...messages, userTurn];
    setMessages(newHistory);
    setInputValue('');
    setIsLoading(true);

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    try {
      const historyPayload = newHistory.map((m) => ({
        role: m.role,
        content: m.content,
        action: m.action,
        entity: m.entity,
        creation_draft: m.creation_draft,
        missing_fields: m.missing_fields,
        is_creation_ready: m.is_creation_ready
      }));

      const response = await api.sendAgentMessage(promptToSend.trim(), historyPayload);

      const assistantTurn: ChatTurn = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        prompt: promptToSend.trim(),
        action: response.action,
        entity: response.entity,
        records: response.records || [],
        total: response.total,
        query_type: response.query_type,
        filters: response.filters,
        update_result: response.update_result,
        creation_draft: response.creation_draft,
        missing_fields: response.missing_fields,
        is_creation_ready: response.is_creation_ready,
        granular_answer: response.granular_answer,
        suggestions: response.suggestions,
        sources: response.sources || []
      };

      setMessages((prev) => [...prev, assistantTurn]);

      // If an action was executed (create / update), refresh history
      if (response.action === 'CREATE_SUCCESS' || response.action === 'UPDATE') {
        fetchHistory();
      }
    } catch (err: any) {
      const errorTurn: ChatTurn = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: `❌ **SAP Communication Error**: ${err.message || 'Failed to process request.'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        action: 'ERROR'
      };
      setMessages((prev) => [...prev, errorTurn]);
    } finally {
      setIsLoading(false);
    }
  };


  const handleConfirmPostDraft = async (turn: ChatTurn) => {
    if (turn.creation_draft && turn.entity) {
      setIsLoading(true);
      try {
        const res = await api.confirmCreateMasterData(turn.entity, turn.creation_draft);
        const isSuccess = Boolean(res.success && res.action === 'CREATE_SUCCESS');
        const assistantTurn: ChatTurn = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: res.reply,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          action: res.action || (isSuccess ? 'CREATE_SUCCESS' : 'CREATE_FAILED'),
          entity: (res.entity || turn.entity) as any,
          records: res.records || [],
          total: res.total || 1,
          creation_draft: res.creation_draft || turn.creation_draft,
          missing_fields: res.missing_fields || [],
          is_creation_ready: isSuccess,
          suggestions: res.suggestions || []
        };
        setMessages((prev) => [...prev, assistantTurn]);
        if (isSuccess) {
          fetchHistory();
        }
      } catch (err: any) {
        const errorMsg = err.response?.data?.detail || err.message || 'Failed to post record to SAP.';
        const errorTurn: ChatTurn = {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: `❌ **SAP Communication Error**: ${errorMsg}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          action: 'CREATE_FAILED',
          entity: turn.entity,
          creation_draft: turn.creation_draft,
          is_creation_ready: false
        };
        setMessages((prev) => [...prev, errorTurn]);
      } finally {
        setIsLoading(false);
      }
    } else {
      handleSendMessage('Post to SAP');
    }
  };

  const handleOpenEditModal = (record: Record<string, any>, ent: string) => {
    setEditingRecord(record);
    setEditingEntity(ent);
    if (ent === 'BusinessPartners') {
      setEditFieldName('CardName');
      setEditFieldValue(record.CardName || '');
    } else if (ent === 'Items') {
      setEditFieldName('ItemName');
      setEditFieldValue(record.ItemName || '');
    } else {
      setEditFieldName('WarehouseName');
      setEditFieldValue(record.WarehouseName || '');
    }
  };

  const handleFieldSelectChange = (fieldName: string) => {
    setEditFieldName(fieldName);
    if (editingRecord) {
      setEditFieldValue(editingRecord[fieldName] !== undefined ? String(editingRecord[fieldName]) : '');
    }
  };

  const handleExecuteFieldUpdate = async () => {
    if (!editingRecord || !editFieldName || isUpdatingField) return;
    setIsUpdatingField(true);

    const key = editingRecord.CardCode || editingRecord.ItemCode || editingRecord.WarehouseCode;
    const promptCommand = `Change ${editFieldName} to ${editFieldValue} for ${editingEntity === 'BusinessPartners' ? 'customer' : (editingEntity === 'Items' ? 'item' : 'warehouse')} ${key}`;

    setEditingRecord(null);
    setIsUpdatingField(false);
    await handleSendMessage(promptCommand);
  };

  const handleTextareaInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const renderVocalynComposer = (customStyle?: React.CSSProperties) => (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        handleSendMessage();
      }}
      className="vocalyn-card"
      style={customStyle}
    >
      <div className="vocalyn-card-top">
        <Sparkles size={18} className="vocalyn-sparkle-icon" />
        <textarea
          ref={textareaRef}
          rows={1}
          value={inputValue}
          onChange={handleTextareaInput}
          onKeyDown={handleKeyDown}
          placeholder="Ask Hey CIRA to create customers, add items, audit missing HSN codes..."
          className="vocalyn-textarea"
          disabled={isLoading}
        />
      </div>

      <div className="vocalyn-card-bottom">
        <div className="vocalyn-plus-wrapper" onClick={(e) => e.stopPropagation()}>
          <button
            type="button"
            onClick={() => setShowPlusMenu(!showPlusMenu)}
            className="vocalyn-plus-btn"
            title="Tools, Certified Prompts & Templates (+)"
          >
            <Plus size={16} />
          </button>

          {showPlusMenu && (
            <div className="vocalyn-plus-popover">
              <button
                type="button"
                className="vocalyn-popover-item"
                onClick={() => {
                  setShowPromptModal(true);
                  setShowPlusMenu(false);
                }}
              >
                <Sparkles size={14} color="#8B5CF6" />
                <span>16 Certified Prompts</span>
              </button>
              <button
                type="button"
                className="vocalyn-popover-item"
                onClick={() => {
                  setVoiceAutoSend(!voiceAutoSend);
                  setShowPlusMenu(false);
                }}
              >
                <Zap size={14} color="#F59E0B" />
                <span>Auto-Send Voice: {voiceAutoSend ? 'ON' : 'OFF'}</span>
              </button>
              <div className="vocalyn-popover-divider" />
              <button
                type="button"
                className="vocalyn-popover-item"
                onClick={() => {
                  setInputValue('Create Business Partner');
                  setShowPlusMenu(false);
                  if (textareaRef.current) textareaRef.current.focus();
                }}
              >
                <Building2 size={14} color="#3B82F6" />
                <span>Create Business Partner</span>
              </button>
              <button
                type="button"
                className="vocalyn-popover-item"
                onClick={() => {
                  setInputValue('Add new Item');
                  setShowPlusMenu(false);
                  if (textareaRef.current) textareaRef.current.focus();
                }}
              >
                <Package size={14} color="#10B981" />
                <span>Create Item Master</span>
              </button>
              <button
                type="button"
                className="vocalyn-popover-item"
                onClick={() => {
                  setInputValue('give items whose hsn code is not available');
                  setShowPlusMenu(false);
                  if (textareaRef.current) textareaRef.current.focus();
                }}
              >
                <Filter size={14} color="#EC4899" />
                <span>Audit Missing HSN</span>
              </button>
              <div className="vocalyn-popover-divider" />
              <button
                type="button"
                className="vocalyn-popover-item"
                onClick={() => {
                  setMessages([]);
                  localStorage.removeItem('cinntra_ai_chat_history');
                  setShowPlusMenu(false);
                }}
              >
                <RotateCcw size={14} color="#64748B" />
                <span>New Chat Session</span>
              </button>
            </div>
          )}
        </div>

        <div className="vocalyn-card-right">
          <VoiceInputButton
            variant="vocalyn"
            disabled={isLoading}
            autoSendEnabled={voiceAutoSend}
            onAutoSendToggle={(enabled) => setVoiceAutoSend(enabled)}
            activeLanguage={speechLanguage}
            onLanguageChange={(lang) => setSpeechLanguage(lang)}
            onTranscript={(spokenText) => {
              setInputValue(spokenText);
              if (textareaRef.current) {
                textareaRef.current.style.height = 'auto';
                textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
              }
            }}
            onSendDirectly={(spokenText) => {
              handleSendMessage(spokenText);
            }}
          />

          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="vocalyn-send-circle-btn"
            title="Send to Hey CIRA"
          >
            <ArrowUp size={18} strokeWidth={2.4} />
          </button>
        </div>
      </div>
    </form>
  );

  return (
    <div className="vocalyn-wrapper">
      {/* Top Subtle Navigation Bar in Vocalyn Theme */}
      <div className="vocalyn-top-bar">
        <div className="vocalyn-brand-group">
          <div className="vocalyn-mini-orb" />
          <span className="vocalyn-brand-title">Hey CIRA</span>
          <span className="vocalyn-brand-badge">SAP v2.0</span>
          {activeView === 'copilot' && messages.length > 0 && (
            <span className="vocalyn-brand-badge" style={{ background: '#EFF6FF', color: '#1A56DB', borderColor: '#BFDBFE' }}>
              {messages.length} messages
            </span>
          )}
        </div>

        <div className="vocalyn-top-actions">
          <div className="agent-mode-tabs" style={{ background: '#F1F5F9', padding: '3px', borderRadius: '9999px' }}>
            <button
              type="button"
              onClick={() => setActiveView('copilot')}
              className={`agent-mode-tab ${activeView === 'copilot' ? 'active' : ''}`}
            >
              <MessageSquare size={13} />
              <span>Copilot</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setActiveView('history');
                fetchHistory();
              }}
              className={`agent-mode-tab ${activeView === 'history' ? 'active' : ''}`}
            >
              <History size={13} />
              <span>History Ledger ({historyTotal})</span>
            </button>
          </div>

          <div className={sapConnected ? "agent-badge-live" : "agent-badge-engine"}>
            <span className="live-pulse-dot" />
            <span>{sapConnected ? `SAP Connected (${companyDb})` : `SAP Disconnected`}</span>
            {latencyMs && <span className="agent-latency-chip">{latencyMs}ms</span>}
          </div>

          {activeView === 'copilot' && (
            <button
              type="button"
              onClick={() => {
                setMessages([]);
                localStorage.removeItem('cinntra_ai_chat_history');
              }}
              className="vocalyn-nav-btn"
              title="Start fresh conversation"
            >
              <Plus size={13} />
              <span>New Chat</span>
            </button>
          )}

          <button
            type="button"
            onClick={() => setShowPromptModal(true)}
            className="vocalyn-nav-btn"
            title="Browse 16 Certified SAP Prompts"
          >
            <Sparkles size={13} color="#8B5CF6" />
            <span>Prompts</span>
          </button>
        </div>
      </div>

      {/* ==========================================================
          VIEW 1: LIVE CONVERSATIONAL COPILOT
          ========================================================== */}
      {activeView === 'copilot' && (
        <>
          {messages.length === 0 ? (
            /* ==========================================================
               HERO EMPTY STATE (What can Hey CIRA do for you?)
               ========================================================== */
            <div className="vocalyn-hero-container">
              {/* 3D Iridescent Holographic Morphing Orb */}
              <div className="vocalyn-orb-stage" title="Hey CIRA Autonomous AI Agent">
                <div className="vocalyn-3d-orb" />
                <div className="vocalyn-orb-shadow" />
              </div>

              <h1 className="vocalyn-headline">What can Hey CIRA do for you?</h1>
              <p className="vocalyn-subheadline">Hey CIRA transforms your voice into actions instantly.</p>

              {/* Vocalyn Centered Input Card */}
              {renderVocalynComposer()}

              {/* Vocalyn Pills Row - Easy to Understand SAP Master Data Prompts */}
              <div className="vocalyn-pills-row">
                <button
                  type="button"
                  className="vocalyn-pill-btn"
                  onClick={() => handleSendMessage('Create Business Partner')}
                  disabled={isLoading}
                  title="Create a new business partner in SAP"
                >
                  <Building2 size={14} color="#10B981" />
                  <span>Create Business Partner</span>
                </button>
                <button
                  type="button"
                  className="vocalyn-pill-btn"
                  onClick={() => handleSendMessage('Add new Item')}
                  disabled={isLoading}
                  title="Add a new item to SAP Item Master"
                >
                  <Package size={14} color="#8B5CF6" />
                  <span>Add New Item</span>
                </button>
                <button
                  type="button"
                  className="vocalyn-pill-btn"
                  onClick={() => handleSendMessage('give items whose hsn code is not available')}
                  disabled={isLoading}
                  title="Audit items missing statutory HSN codes"
                >
                  <Filter size={14} color="#EF4444" />
                  <span>Missing HSN Codes</span>
                </button>
                <button
                  type="button"
                  className="vocalyn-pill-btn"
                  onClick={() => handleSendMessage('Update customer phone & GST')}
                  disabled={isLoading}
                  title="Update customer phone or GSTIN in SAP"
                >
                  <Edit3 size={14} color="#3B82F6" />
                  <span>Update Customer Phone & GST</span>
                </button>
                <button
                  type="button"
                  className="vocalyn-pill-btn"
                  onClick={() => handleSendMessage('List all Business Partners')}
                  disabled={isLoading}
                  title="View active customers and vendors from SAP"
                >
                  <Users size={14} color="#0EA5E9" />
                  <span>List Business Partners</span>
                </button>
                <button
                  type="button"
                  className="vocalyn-pill-btn"
                  onClick={() => handleSendMessage('List all Warehouses')}
                  disabled={isLoading}
                  title="View configured warehouse locations"
                >
                  <Store size={14} color="#F59E0B" />
                  <span>List Warehouses</span>
                </button>
              </div>
            </div>
          ) : (
            /* ==========================================================
               ACTIVE DIALOGUE CONSOLE (With Vocalyn Floating Composer)
               ========================================================== */
            <div className="vocalyn-chat-container">
              {/* Message Stream */}
              <div className="vocalyn-chat-messages">
                <div className="vocalyn-chat-inner">
                  {messages.map((m, mIdx) => {
                const isUser = m.role === 'user';

                return (
                  <div key={m.id} className={`chat-msg ${m.role}`}>
                    <div className={`chat-avatar ${m.role}`}>
                      {isUser ? <User size={16} /> : <Sparkles size={16} />}
                    </div>

                    <div className="chat-bubble-container">
                      <div className="chat-bubble">
                        {/* Action Header Pill */}
                        {!isUser && m.action && (
                          <div className={`agent-action-pill ${m.action.toLowerCase()}`}>
                            {m.action === 'CREATE_READY' && '⚡ READY FOR SAP POSTING (100%)'}
                            {m.action === 'CREATE_DRAFT' && '🤖 AI CONVERSATIONAL CREATION'}
                            {m.action === 'CREATE_SUCCESS' && '🎉 SUCCESSFULLY POSTED TO SAP'}
                            {m.action === 'CREATE_FAILED' && '⚠️ SAP POSTING NOTICE'}
                            {m.action === 'UPDATE' && '🔄 SERVICE LAYER FIELD PATCH'}
                            {m.action === 'QUERY' && '🔍 REAL-TIME MASTER DATA RETRIEVAL'}
                            {m.action === 'EXPLAIN' && 'ℹ️ SAP COPILOT GUIDANCE'}
                          </div>
                        )}

                        {/* Rich Typography Markdown Renderer */}
                        <MarkdownRenderer text={m.content} />

                        {/* Interactive AI Agent Inquiry / Quick Answers Card */}
                        {!isUser && m.missing_fields && m.missing_fields.length > 0 && m.action !== 'CREATE_SUCCESS' && (
                          <div className="agent-missing-fields-card">
                            <div className="agent-missing-fields-header">
                              <span className="agent-missing-pill agent-inquiry-pill">
                                💬 AI Agent Inquiries ({m.missing_fields.length} details needed)
                              </span>
                              <span className="agent-missing-sub">
                                Click any quick option below or reply directly in chat
                              </span>
                            </div>
                            <div className="agent-missing-fields-grid">
                              {m.missing_fields.map((mf, mfIdx) => {
                                if (mf.field === 'CardType') {
                                  return (
                                    <div key={mfIdx} className="agent-missing-field-row card-type-selector">
                                      <div className="agent-missing-field-info">
                                        <span className="agent-missing-field-label">Partner Type</span>
                                        <code className="agent-missing-field-code">CardType</code>
                                      </div>
                                      <div className="agent-quick-choice-btns">
                                        <button
                                          type="button"
                                          className="agent-quick-btn customer"
                                          onClick={() => {
                                            setInputValue('It is a Customer');
                                            if (textareaRef.current) textareaRef.current.focus();
                                          }}
                                          title="Select Customer"
                                        >
                                          🏢 Customer
                                        </button>
                                        <button
                                          type="button"
                                          className="agent-quick-btn vendor"
                                          onClick={() => {
                                            setInputValue('It is a Vendor');
                                            if (textareaRef.current) textareaRef.current.focus();
                                          }}
                                          title="Select Vendor"
                                        >
                                          🏭 Vendor
                                        </button>
                                      </div>
                                    </div>
                                  );
                                }

                                return (
                                  <button
                                    key={mfIdx}
                                    type="button"
                                    className="agent-missing-field-row"
                                    onClick={() => {
                                      const sample = mf.example || '';
                                      setInputValue(`${mf.label || mf.field} is ${sample}`.trim());
                                      if (textareaRef.current) textareaRef.current.focus();
                                    }}
                                    title={`Click to fill ${mf.label} (e.g. ${mf.example || ''})`}
                                  >
                                    <div className="agent-missing-field-info">
                                      <span className="agent-missing-field-label">{mf.label}</span>
                                      <code className="agent-missing-field-code">{mf.field}</code>
                                    </div>
                                    {mf.example && (
                                      <span className="agent-missing-field-example">
                                        e.g. <code>{mf.example}</code>
                                      </span>
                                    )}
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        )}

                        {/* Granular Attribute Highlight Card */}
                        {m.granular_answer && (
                          <div className="agent-granular-card">
                            <div className="agent-granular-meta">
                              <span className="agent-granular-attr-name">
                                📍 {m.granular_answer.attribute}
                              </span>
                              <span className="agent-granular-code">
                                {m.granular_answer.code} • {m.granular_answer.name}
                              </span>
                            </div>

                            <div className="agent-granular-val-row">
                              <div className="agent-granular-val">
                                {m.granular_answer.value}
                              </div>
                              <button
                                type="button"
                                className="agent-copy-btn"
                                onClick={() => copyToClipboard(m.granular_answer!.value, m.id)}
                                title="Copy answer"
                              >
                                {copiedId === m.id ? (
                                  <>
                                    <Check size={13} color="#10B981" />
                                    <span>Copied!</span>
                                  </>
                                ) : (
                                  <>
                                    <Copy size={13} />
                                    <span>Copy</span>
                                  </>
                                )}
                              </button>
                            </div>
                          </div>
                        )}

                        {/* Interactive Post to SAP Trigger Button (Only shown when creation is 100% ready) */}
                        {m.is_creation_ready && m.action !== 'CREATE_SUCCESS' && (
                          <div className="agent-post-sap-banner" style={{ marginTop: 12 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                              <Zap size={18} color="#10B981" />
                              <span style={{ fontSize: 13, fontWeight: 700, color: '#065F46' }}>
                                All required details validated. Ready to commit to SAP!
                              </span>
                            </div>
                            <button
                              type="button"
                              onClick={() => handleConfirmPostDraft(m)}
                              disabled={isLoading}
                              className="agent-post-sap-btn"
                              title="Post this record directly to SAP Service Layer"
                            >
                              <Zap size={16} />
                              <span>Post to SAP</span>
                            </button>
                          </div>
                        )}

                        {/* Interactive Master Data Table View */}
                        {m.records && m.records.length > 0 && m.entity && (
                          <InteractiveMasterDataTable
                            turnId={m.id}
                            entity={m.entity}
                            records={m.records}
                            total={m.total}
                            companyDb={companyDb}
                            onQuickEdit={handleOpenEditModal}
                            isUpdateRecord={m.action === 'UPDATE'}
                            prompt={m.prompt || (mIdx > 0 && messages[mIdx - 1]?.role === 'user' ? messages[mIdx - 1]?.content : '')}
                            queryType={m.query_type}
                          />
                        )}

                        {/* RAG Knowledge Base Sources & Citations */}
                        {m.sources && m.sources.length > 0 && (
                          <div className="agent-sources-banner">
                            <div className="agent-sources-header">
                              <BookOpen size={13} color="#6366F1" />
                              <span>Verified Knowledge Sources & Policy Guidelines ({m.sources.length})</span>
                            </div>
                            <div className="agent-sources-chips">
                              {m.sources.map((src, sIdx) => (
                                <span key={sIdx} className="agent-source-chip" title={src.document}>
                                  📄 <strong>{src.document}</strong> {src.section && src.section !== 'General' ? `• ${src.section}` : ''}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Context-Aware Dynamic Suggestions (Only shown when not ready to post, preventing duplicate buttons) */}
                        {!m.is_creation_ready && m.suggestions && m.suggestions.length > 0 && (
                          <div className="agent-msg-suggestions">
                            <span className="agent-msg-suggestions-label">
                              <Sparkles size={12} color="#1A56DB" />
                              <span>Recommended Next Prompts:</span>
                            </span>
                            <div className="agent-msg-suggestions-grid">
                              {m.suggestions.map((sug, sIdx) => (
                                <button
                                  key={sIdx}
                                  type="button"
                                  className="agent-msg-suggestion-chip"
                                  onClick={() => handleSendMessage(sug)}
                                  disabled={isLoading}
                                >
                                  <Sparkles size={11} className="sug-icon" />
                                  <span>{sug}</span>
                                </button>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Message Timestamp */}
                        <div className="chat-time-tag">
                          <Clock size={11} style={{ marginRight: 4, opacity: 0.7 }} />
                          <span>{m.timestamp}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Streaming / Typing Indicator */}
              {isLoading && (
                <div className="chat-msg assistant">
                  <div className="chat-avatar assistant">
                    <Sparkles size={16} />
                  </div>
                  <div className="chat-bubble-container">
                    <div className="chat-bubble" style={{ padding: '12px 18px' }}>
                      <div className="agent-typing-indicator">
                        <div className="agent-typing-dot" />
                        <div className="agent-typing-dot" />
                        <div className="agent-typing-dot" />
                        <span style={{ fontSize: 12, color: '#64748B', marginLeft: 8, fontWeight: 500 }}>
                          Hey CIRA is synthesizing Service Layer response...
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
                  <div ref={chatEndRef} />
                </div>
              </div>

              {/* Vocalyn Docked Composer in Dialogue */}
              <div className="vocalyn-chat-footer">
                <div className="vocalyn-chat-footer-inner">
                  {renderVocalynComposer({ maxWidth: 860, width: '100%', margin: '0 auto' })}
                </div>
              </div>
            </div>
        )}
      </>
    )}

      {/* ==========================================================
          VIEW 2: DEDICATED AI AGENT CHANGE HISTORY & LEDGER
          ========================================================== */}
      {activeView === 'history' && (
        <div className="agent-history-view">
          {/* 4 KPI Summary Cards */}
          <div className="agent-history-kpi-grid">
            <div className="agent-history-kpi-card">
              <div className="agent-history-kpi-title">
                <span>Total AI Actions</span>
                <Sparkles size={14} color="#1A56DB" />
              </div>
              <div className="agent-history-kpi-val">
                {historyStats?.total_actions ?? historyTotal}
              </div>
              <div className="agent-history-kpi-sub">
                Prompt-driven operations recorded
              </div>
            </div>

            <div className="agent-history-kpi-card">
              <div className="agent-history-kpi-title">
                <span>Records Created</span>
                <Package size={14} color="#059669" />
              </div>
              <div className="agent-history-kpi-val" style={{ color: '#059669' }}>
                {historyStats?.creations ?? 0}
              </div>
              <div className="agent-history-kpi-sub">
                BPs, Items &amp; Warehouses created
              </div>
            </div>

            <div className="agent-history-kpi-card">
              <div className="agent-history-kpi-title">
                <span>Fields Modified</span>
                <Edit3 size={14} color="#D97706" />
              </div>
              <div className="agent-history-kpi-val" style={{ color: '#D97706' }}>
                {historyStats?.updates ?? 0}
              </div>
              <div className="agent-history-kpi-sub">
                Granular field patches committed
              </div>
            </div>

            <div className="agent-history-kpi-card">
              <div className="agent-history-kpi-title">
                <span>Audit Integrity</span>
                <ShieldCheck size={14} color="#10B981" />
              </div>
              <div className="agent-history-kpi-val" style={{ color: '#10B981' }}>
                {historyStats?.success_rate ?? 100}%
              </div>
              <div className="agent-history-kpi-sub">
                SHA-256 Ledger Verified
              </div>
            </div>
          </div>

          {/* History Filter Toolbar */}
          <div className="agent-history-toolbar">
            <div className="agent-history-filters-group">
              <span style={{ fontSize: 12, fontWeight: 700, color: '#64748B', display: 'flex', alignItems: 'center', gap: 4 }}>
                <Filter size={13} /> Entity:
              </span>
              {['all', 'BusinessPartners', 'Items', 'Warehouses'].map((ent) => (
                <button
                  key={ent}
                  type="button"
                  onClick={() => setHistoryEntityFilter(ent)}
                  className={`agent-filter-pill-btn ${historyEntityFilter === ent ? 'active' : ''}`}
                >
                  {ent === 'all' ? 'All Entities' : ent === 'BusinessPartners' ? 'Partners' : ent}
                </button>
              ))}

              <div style={{ width: 1, height: 18, background: '#E2EEFA', margin: '0 4px' }} />

              <span style={{ fontSize: 12, fontWeight: 700, color: '#64748B' }}>Action:</span>
              {['all', 'CREATE', 'UPDATE'].map((act) => (
                <button
                  key={act}
                  type="button"
                  onClick={() => setHistoryActionFilter(act)}
                  className={`agent-filter-pill-btn ${historyActionFilter === act ? 'active' : ''}`}
                >
                  {act === 'all' ? 'All Actions' : act === 'CREATE' ? 'Creations' : 'Field Updates'}
                </button>
              ))}

              <div style={{ width: 1, height: 18, background: '#E2EEFA', margin: '0 4px' }} />

              <span style={{ fontSize: 12, fontWeight: 700, color: '#64748B' }}>Timeframe:</span>
              {[
                { label: '7 Days', val: 7 },
                { label: '30 Days', val: 30 },
                { label: 'All Time', val: null }
              ].map((tf) => (
                <button
                  key={tf.label}
                  type="button"
                  onClick={() => setHistoryDays(tf.val)}
                  className={`agent-filter-pill-btn ${historyDays === tf.val ? 'active' : ''}`}
                >
                  {tf.label}
                </button>
              ))}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div className="agent-history-search-wrapper">
                <Search size={14} color="#94A3B8" style={{ position: 'absolute', left: 10 }} />
                <input
                  type="text"
                  placeholder="Search prompt, code, or field..."
                  value={historySearch}
                  onChange={(e) => setHistorySearch(e.target.value)}
                  className="agent-history-search-input"
                />
              </div>

              <button
                type="button"
                onClick={fetchHistory}
                className="agent-filter-pill-btn"
                title="Refresh history"
                style={{ display: 'flex', alignItems: 'center', gap: 4 }}
              >
                <RefreshCw size={12} className={loadingHistory ? 'pulse-animation' : ''} />
                <span>Refresh</span>
              </button>
            </div>
          </div>

          {/* History Feed List */}
          {loadingHistory ? (
            <div className="agent-history-empty">
              <RefreshCw size={24} className="pulse-animation" style={{ margin: '0 auto 8px', color: '#1A56DB' }} />
              <p style={{ margin: 0, fontWeight: 600 }}>Loading AI Agent change history...</p>
            </div>
          ) : historyRecords.length === 0 ? (
            <div className="agent-history-empty">
              <History size={32} style={{ margin: '0 auto 8px', color: '#94A3B8' }} />
              <h3 style={{ fontSize: 16, fontWeight: 700, color: '#0A1931', margin: '0 0 4px' }}>
                No AI Agent Actions Found
              </h3>
              <p style={{ fontSize: 13, color: '#64748B', margin: '0 0 16px' }}>
                No recorded AI operations matched the active filters.
              </p>
              <button
                type="button"
                onClick={() => {
                  setHistoryEntityFilter('all');
                  setHistoryActionFilter('all');
                  setHistorySearch('');
                }}
                className="agent-filter-pill-btn active"
              >
                Clear Filters
              </button>
            </div>
          ) : (
            <div className="agent-history-feed">
              {historyRecords.map((rec) => {
                const isCreation = rec.action === 'CREATE';
                const isUpdate = rec.action === 'UPDATE' || rec.action === 'PATCH';
                const hasDiff = Object.keys(rec.new_values || {}).length > 0;

                return (
                  <div key={rec.id} className="agent-history-card">
                    {/* Header Row */}
                    <div className="agent-history-card-header">
                      <div className="agent-history-meta-left">
                        <span className={`agent-action-tag ${isCreation ? 'create' : isUpdate ? 'update' : 'query'}`}>
                          {rec.action}
                        </span>

                        <span className="agent-entity-tag">
                          {rec.entity === 'BusinessPartners' ? <Building2 size={14} color="#1A56DB" /> : rec.entity === 'Items' ? <Package size={14} color="#059669" /> : <Store size={14} color="#7C3AED" />}
                          <strong>{rec.entity}</strong>
                        </span>

                        {rec.target_key && (
                          <span className="agent-target-key-pill" title="SAP Object Code">
                            {rec.target_key}
                          </span>
                        )}

                        <span style={{ fontSize: 11, color: '#94A3B8' }}>
                          • DB: <strong>{rec.company_db}</strong>
                        </span>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <span className="agent-history-timestamp">
                          <Clock size={12} />
                          {new Date(rec.timestamp).toLocaleString([], {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit'
                          })}
                        </span>
                      </div>
                    </div>

                    {/* Trigger Prompt if present */}
                    {rec.prompt && (
                      <div className="agent-history-prompt-quote">
                        <Sparkles size={13} color="#1A56DB" />
                        <span>Prompt: "{rec.prompt}"</span>
                      </div>
                    )}

                    {/* Visual Old vs New Field Diff Comparison */}
                    {isUpdate && hasDiff && (
                      <div className="agent-diff-container">
                        <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: '#64748B', letterSpacing: '0.4px', marginBottom: 2 }}>
                          Field Level Changes (Before &rarr; After)
                        </div>
                        {Object.entries(rec.new_values).map(([fKey, newVal]) => {
                          const oldVal = rec.old_values ? rec.old_values[fKey] : '—';
                          return (
                            <div key={fKey} className="agent-diff-row">
                              <span className="agent-diff-field-name">
                                <code>{fKey}</code>
                              </span>
                              <div className="agent-diff-values">
                                <span className="agent-diff-old" title="Original Value">
                                  {String(oldVal ?? 'None')}
                                </span>
                                <span className="agent-diff-arrow">&rarr;</span>
                                <span className="agent-diff-new" title="New Value Committed to SAP">
                                  {String(newVal)}
                                </span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}

                    {/* Creation Payload Summary Grid */}
                    {isCreation && Object.keys(rec.created_payload || {}).length > 0 && (
                      <div className="agent-diff-container">
                        <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: '#64748B', letterSpacing: '0.4px', marginBottom: 2 }}>
                          Created Master Data Attributes
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                          {Object.entries(rec.created_payload).map(([k, v]) => (
                            <span
                              key={k}
                              style={{
                                fontSize: 11.5,
                                background: '#FFFFFF',
                                border: '1px solid #E2EEFA',
                                padding: '2px 8px',
                                borderRadius: 6,
                                color: '#0A1931'
                              }}
                            >
                              <strong>{k}</strong>: <code>{String(v)}</code>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Footer Row: Ledger Hash & Quick Action */}
                    <div className="agent-history-footer-row">
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        {rec.payload_hash && (
                          <span className="agent-hash-badge" title={`Full SHA-256 Hash: ${rec.payload_hash}`}>
                            <Lock size={11} color="#10B981" />
                            Hash: <code>{rec.payload_hash.slice(0, 16)}...</code>
                          </span>
                        )}
                        <span style={{ color: rec.success ? '#047857' : '#DC2626', fontWeight: 600, fontSize: 11 }}>
                          {rec.success ? '✓ SAP Committed' : '✕ Operation Failed'}
                        </span>
                      </div>

                      <button
                        type="button"
                        onClick={() => {
                          setActiveView('copilot');
                          if (rec.target_key) {
                            handleSendMessage(`What is the details of ${rec.entity === 'BusinessPartners' ? 'customer' : rec.entity === 'Items' ? 'item' : 'warehouse'} ${rec.target_key}?`);
                          }
                        }}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: '#1A56DB',
                          fontSize: 12,
                          fontWeight: 700,
                          cursor: 'pointer',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 4,
                          padding: '2px 6px',
                          borderRadius: 4
                        }}
                      >
                        <span>Ask AI About This</span>
                        <ChevronRight size={13} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Quick Edit Single Field Modal */}
      {editingRecord && (
        <div
          className="agent-edit-modal-backdrop"
          onClick={() => setEditingRecord(null)}
        >
          <div
            className="agent-edit-modal-card"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="agent-edit-modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Edit3 size={18} color="#2563EB" />
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#0F172A' }}>
                  Update {editingEntity === 'BusinessPartners' ? 'Business Partner' : editingEntity === 'Items' ? 'Item Master' : 'Warehouse'} Field
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setEditingRecord(null)}
                className="agent-modal-close-btn"
              >
                <X size={16} />
              </button>
            </div>

            <div className="agent-edit-modal-body">
              <div className="agent-edit-target-badge">
                <span style={{ fontSize: 11, color: '#64748B', display: 'block' }}>Target SAP Record Code</span>
                <strong style={{ fontSize: 14, color: '#0F172A' }}>
                  {editingRecord.CardCode || editingRecord.ItemCode || editingRecord.WarehouseCode}
                </strong>
                <span style={{ fontSize: 12, color: '#475569', marginLeft: 8 }}>
                  ({editingRecord.CardName || editingRecord.ItemName || editingRecord.WarehouseName})
                </span>
              </div>

              <div className="agent-form-field">
                <label className="agent-form-label">Select Field to Update</label>
                <select
                  value={editFieldName}
                  onChange={(e) => handleFieldSelectChange(e.target.value)}
                  className="agent-form-select"
                >
                  {editingEntity === 'BusinessPartners' ? (
                    <>
                      <option value="CardName">CardName (Company/Customer Name)</option>
                      <option value="Phone1">Phone1 (Primary Phone)</option>
                      <option value="GSTNo">GSTNo (GST Identification Number)</option>
                      <option value="FederalTaxID">FederalTaxID (PAN Number)</option>
                      <option value="EmailAddress">EmailAddress (Contact Email)</option>
                      <option value="Address">Address (Street Address)</option>
                      <option value="City">City</option>
                      <option value="ZipCode">ZipCode / Postal Code</option>
                      <option value="Valid">Valid (Active Status: tYES/tNO)</option>
                    </>
                  ) : editingEntity === 'Items' ? (
                    <>
                      <option value="ItemName">ItemName (Product Description)</option>
                      <option value="InventoryUOM">InventoryUOM (Unit of Measure)</option>
                      <option value="TaxRate">TaxRate (Tax Percentage %)</option>
                      <option value="HSN">HSN (HSN / Tariff Code)</option>
                      <option value="Price">Price (Standard Unit Price)</option>
                      <option value="Valid">Valid (Active Status: tYES/tNO)</option>
                    </>
                  ) : (
                    <>
                      <option value="WarehouseName">WarehouseName (Depot Name)</option>
                      <option value="City">City (Facility City)</option>
                      <option value="State">State</option>
                      <option value="Address">Address (Physical Location)</option>
                      <option value="Inactive">Inactive (Inactive Flag: tYES/tNO)</option>
                    </>
                  )}
                </select>
              </div>

              <div className="agent-form-field">
                <label className="agent-form-label">New Value for <code>{editFieldName}</code></label>
                <input
                  type="text"
                  value={editFieldValue}
                  onChange={(e) => setEditFieldValue(e.target.value)}
                  placeholder={`Enter new ${editFieldName}...`}
                  className="agent-form-input"
                  autoFocus
                />
              </div>
            </div>

            <div className="agent-edit-modal-footer">
              <button
                type="button"
                onClick={() => setEditingRecord(null)}
                className="agent-btn-secondary"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleExecuteFieldUpdate}
                disabled={isUpdatingField || !editFieldValue.trim()}
                className="agent-btn-primary"
              >
                {isUpdatingField ? 'Updating...' : 'Save & Execute in SAP'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==========================================================
          PROMPT LIBRARY MODAL: 16 CERTIFIED SAP MASTER DATA PROMPTS
          ========================================================== */}
      {showPromptModal && (
        <div className="agent-prompt-modal-backdrop" onClick={() => setShowPromptModal(false)}>
          <div className="agent-prompt-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="agent-prompt-modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div className="agent-orb-icon" style={{ width: 36, height: 36, borderRadius: 10 }}>
                  <Sparkles size={18} color="#FFFFFF" />
                </div>
                <div>
                  <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#0F172A' }}>
                    Hey CIRA Prompt Library
                  </h3>
                  <p style={{ margin: 0, fontSize: 12, color: '#64748B' }}>
                    16 Certified Autonomous Prompts for SAP Master Data Audits & Operations
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowPromptModal(false)}
                className="agent-modal-close-btn"
                title="Close Prompt Library"
              >
                <X size={16} />
              </button>
            </div>

            {/* Filter Tabs */}
            <div className="agent-prompt-modal-tabs">
              {[
                { id: 'all', label: 'All Prompts (16+)' },
                { id: 'items', label: '📦 Item Master (8)' },
                { id: 'bp', label: '👥 Customers & Vendors (8)' },
                { id: 'creation', label: '✨ Creation Studio' },
                { id: 'updates', label: '⚡ Field Updates' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  className={`agent-prompt-tab-btn ${promptCategoryFilter === tab.id ? 'active' : ''}`}
                  onClick={() => setPromptCategoryFilter(tab.id as any)}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Search Bar */}
            <div className="agent-prompt-search-bar">
              <Search size={16} color="#94A3B8" />
              <input
                type="text"
                value={promptSearchTerm}
                onChange={(e) => setPromptSearchTerm(e.target.value)}
                placeholder="Filter prompts by keyword (e.g. stock, HSN, duplicate, aging, warehouse, GSTIN)..."
                className="agent-prompt-search-input"
              />
              {promptSearchTerm && (
                <button
                  type="button"
                  onClick={() => setPromptSearchTerm('')}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94A3B8', padding: 4 }}
                >
                  <X size={14} />
                </button>
              )}
            </div>

            {/* Prompts Body */}
            <div className="agent-prompt-modal-body">
              {filteredPrompts.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '36px 16px', color: '#64748B' }}>
                  No prompts found matching "{promptSearchTerm}".
                </div>
              ) : (
                filteredPrompts.map((item) => (
                  <div key={item.id} className="agent-prompt-card-item">
                    <div className="agent-prompt-card-meta">
                      <span
                        className="agent-prompt-card-badge"
                        style={{ background: item.badgeBg, color: item.badgeColor }}
                      >
                        {item.badge}
                      </span>
                      <div className="agent-prompt-card-text">
                        "{item.prompt}"
                      </div>
                      <div style={{ fontSize: 12, color: '#64748B', marginTop: 4 }}>
                        {item.description}
                      </div>
                    </div>

                    <div className="agent-prompt-card-actions">
                      <button
                        type="button"
                        onClick={() => {
                          setShowPromptModal(false);
                          setInputValue(item.prompt);
                          if (textareaRef.current) {
                            textareaRef.current.focus();
                          }
                        }}
                        className="agent-prompt-insert-btn"
                        title="Insert prompt into input box"
                      >
                        <Edit3 size={13} />
                        <span>Insert</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setShowPromptModal(false);
                          handleSendMessage(item.prompt);
                        }}
                        className="agent-prompt-run-btn"
                        title="Execute prompt directly in Hey CIRA"
                        disabled={isLoading}
                      >
                        <Send size={13} />
                        <span>Run Now</span>
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AiAgentPage;
