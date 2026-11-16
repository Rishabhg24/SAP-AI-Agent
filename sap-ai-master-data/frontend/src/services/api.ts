/**
 * API service for communicating with FastAPI backend.
 * Zero credentials or API keys exposed on client.
 */
import axios from 'axios';
import type {
  AuditLogRecord,
  ChatMessageResponse,
  DashboardStats,
  RAGSearchResult,
  SapHealthResponse,
  SapRecordsResponse,
  WorkflowState,
  WorkflowSummary,
  AgentHistoryResponse,
  AgentHistoryStats,
  AgentChatSession,
} from '../types';

// Dynamic API Base resolution: window config -> vite env -> config.json -> relative fallback '/api'
let dynamicApiBase =
  (typeof window !== 'undefined' && (window as any).__APP_CONFIG__?.apiBase) ||
  import.meta.env.VITE_API_BASE ||
  '/api';

const client = axios.create({
  baseURL: dynamicApiBase,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to ensure every request uses current dynamic baseURL and passes active user ID
client.interceptors.request.use((config) => {
  config.baseURL = dynamicApiBase;
  try {
    const userStr = typeof window !== 'undefined' ? localStorage.getItem('sap_ai_master_data_user') : null;
    if (userStr) {
      const userObj = JSON.parse(userStr);
      if (userObj?.email) {
        config.headers['X-User-Id'] = userObj.email;
      }
    }
  } catch (e) {}
  return config;
});

// Asynchronously load public/config.json if available and not explicitly overridden by VITE_API_BASE
if (typeof window !== 'undefined' && !import.meta.env.VITE_API_BASE) {
  fetch('/config.json')
    .then((res) => (res.ok ? res.json() : null))
    .then((data) => {
      if (data?.apiBase && data.apiBase !== dynamicApiBase) {
        dynamicApiBase = data.apiBase;
        client.defaults.baseURL = data.apiBase;
      }
    })
    .catch(() => {});
}

export const api = {
  // Health & Connectivity
  getHealth: async () => {
    const res = await client.get('/health');
    return res.data;
  },

  getSapHealth: async (): Promise<SapHealthResponse> => {
    const res = await client.get('/sap/health');
    return res.data;
  },

  getSapCompanies: async () => {
    const res = await client.get('/sap/companies');
    return res.data;
  },

  selectSapCompany: async (companyDb: string, userId?: string) => {
    const res = await client.post('/sap/select-company', {
      company_db: companyDb,
      user_id: userId
    });
    return res.data;
  },


  // Document Upload & Multi-Engine Extraction
  uploadDocument: async (file: File, masterType?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (masterType && masterType !== 'auto') {
      formData.append('master_type', masterType);
    }
    const res = await client.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000,
    });
    return res.data;
  },

  getSamplePdf: async (masterType: string): Promise<File> => {
    const res = await client.get(`/documents/sample/${masterType}?format=pdf`, {
      responseType: 'blob',
    });
    const filename =
      masterType === 'item'
        ? 'sample_item.pdf'
        : masterType === 'business_partner'
        ? 'sample_supplier.pdf'
        : 'sample_warehouse.pdf';
    return new File([res.data], filename, { type: 'application/pdf' });
  },

  getSampleExcel: async (masterType: string, mode: 'single' | 'bulk' = 'bulk'): Promise<File> => {
    const res = await client.get(`/documents/sample/${masterType}?format=excel&mode=${mode}`, {
      responseType: 'blob',
    });
    const filename =
      mode === 'bulk'
        ? masterType === 'item'
          ? 'sample_items_bulk.xlsx'
          : masterType === 'business_partner'
          ? 'sample_suppliers_bulk.xlsx'
          : 'sample_warehouses_bulk.xlsx'
        : masterType === 'item'
        ? 'sample_item.xlsx'
        : masterType === 'business_partner'
        ? 'sample_supplier.xlsx'
        : 'sample_warehouse.xlsx';
    return new File([res.data], filename, {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });
  },

  getSampleCsv: async (masterType: string): Promise<File> => {
    const res = await client.get(`/documents/sample/${masterType}?format=csv&mode=bulk`, {
      responseType: 'blob',
    });
    const filename =
      masterType === 'item'
        ? 'sample_items_bulk.csv'
        : masterType === 'business_partner'
        ? 'sample_suppliers_bulk.csv'
        : 'sample_warehouses_bulk.csv';
    return new File([res.data], filename, { type: 'text/csv' });
  },

  getWorkflow: async (workflowId: string): Promise<WorkflowState> => {
    const res = await client.get(`/workflows/${workflowId}`);
    return res.data.data;
  },

  resolveConflict: async (workflowId: string, corrections: Record<string, any>) => {
    const res = await client.post(`/workflows/${workflowId}/resolve-conflict`, {
      corrections,
    });
    return res.data;
  },

  selectWorkflowRecord: async (workflowId: string, index: number, record?: Record<string, any>) => {
    const res = await client.post(`/workflows/${workflowId}/select-record`, {
      index,
      record,
    });
    return res.data;
  },

  bulkApplyDefaults: async (workflowId: string, defaults: Record<string, any>) => {
    const res = await client.post(`/workflows/${workflowId}/bulk-apply-defaults`, {
      defaults,
    });
    return res.data;
  },

  updateWorkflowRecord: async (
    workflowId: string,
    payload: {
      updates?: Record<string, any>;
      index?: number;
      apply_to_all?: boolean;
      records?: Record<string, any>[];
    }
  ) => {
    const res = await client.post(`/workflows/${workflowId}/update-record`, payload);
    return res.data;
  },

  // Deterministic Validation
  validateItem: async (data: Record<string, any>) => {
    const res = await client.post('/validation/item', data);
    return res.data;
  },

  validateBusinessPartner: async (data: Record<string, any>) => {
    const res = await client.post('/validation/business-partner', data);
    return res.data;
  },

  validateWarehouse: async (data: Record<string, any>) => {
    const res = await client.post('/validation/warehouse', data);
    return res.data;
  },

  // Conversational Assistant
  sendChatMessage: async (
    message: string,
    workflowId?: string,
    history?: { role: 'user' | 'assistant'; content: string }[]
  ): Promise<ChatMessageResponse> => {
    const res = await client.post('/chat/message', {
      workflow_id: workflowId,
      message,
      history,
    });
    return res.data.data;
  },

  sendMessage: async (
    workflowId: string,
    message: string,
    history?: { role: 'user' | 'assistant'; content: string }[]
  ): Promise<ChatMessageResponse> => {
    const res = await client.post('/chat/message', {
      workflow_id: workflowId,
      message,
      history,
    });
    return res.data.data;
  },

  // RAG Knowledge Base
  searchRag: async (query: string, topK = 5, entity?: string): Promise<RAGSearchResult[]> => {
    const res = await client.post('/rag/search', {
      query,
      top_k: topK,
      entity,
    });
    return res.data.data.results;
  },

  askRag: async (question: string, entity?: string, topK = 5) => {
    const res = await client.post('/rag/ask', {
      question,
      entity,
      top_k: topK,
    });
    return res.data.data;
  },

  // Confirmation & SAP Posting
  confirmWorkflow: async (workflowId: string) => {
    const res = await client.post(`/master-data/${workflowId}/confirm`, {
      confirmed: true,
    });
    return res.data;
  },

  bulkConfirmWorkflow: async (workflowId: string) => {
    const res = await client.post(`/master-data/${workflowId}/bulk-confirm`, {
      confirmed: true,
    });
    return res.data;
  },

  bulkCreateInSap: async (
    workflowId: string,
    options?: { indices?: number[]; skipDuplicates?: boolean; continueOnError?: boolean; confirmed?: boolean }
  ) => {
    const res = await client.post(`/master-data/${workflowId}/bulk-create`, {
      indices: options?.indices,
      skip_duplicates: options?.skipDuplicates ?? true,
      continue_on_error: options?.continueOnError ?? true,
      confirmed: options?.confirmed ?? true,
    });
    return res.data;
  },

  bulkCreateDirect: async (
    masterType: string,
    records: Record<string, any>[],
    options?: { skipDuplicates?: boolean; continueOnError?: boolean }
  ) => {
    const res = await client.post('/master-data/bulk-create-direct', {
      master_type: masterType,
      records,
      skip_duplicates: options?.skipDuplicates ?? true,
      continue_on_error: options?.continueOnError ?? true,
      confirmed: true,
    });
    return res.data;
  },

  createItemInSap: async (workflowId?: string, data?: Record<string, any>) => {
    const res = await client.post('/master-data/item/create', {
      workflow_id: workflowId,
      data,
    });
    return res.data;
  },

  createBusinessPartnerInSap: async (workflowId?: string, data?: Record<string, any>) => {
    const res = await client.post('/master-data/business-partner/create', {
      workflow_id: workflowId,
      data,
    });
    return res.data;
  },

  createWarehouseInSap: async (workflowId?: string, data?: Record<string, any>) => {
    const res = await client.post('/master-data/warehouse/create', {
      workflow_id: workflowId,
      data,
    });
    return res.data;
  },

  // Live SAP Master Data Records & Counts
  getSapCounts: async (): Promise<{ Items: number; BusinessPartners: number; Warehouses: number }> => {
    const res = await client.get('/sap/counts');
    return res.data.data;
  },

  getSapRecords: async (
    entity: 'Items' | 'BusinessPartners' | 'Warehouses',
    top = 15,
    skip = 0,
    search?: string,
    days?: number | null
  ): Promise<SapRecordsResponse> => {
    const params: Record<string, any> = { entity, top, skip };
    if (search && search.trim()) {
      params.search = search.trim();
    }
    if (days && days > 0) {
      params.days = days;
    }
    const res = await client.get('/sap/records', { params });
    return res.data.data;
  },

  getWorkflows: async (limit = 20, offset = 0, days?: number | null): Promise<WorkflowSummary[]> => {
    let url = `/workflows?limit=${limit}&offset=${offset}`;
    if (days && days > 0) {
      url += `&days=${days}`;
    }
    const res = await client.get(url);
    return res.data.data;
  },

  // Audit Logs & Dashboard Stats
  getAuditLogs: async (options?: {
    limit?: number;
    days?: number | null;
    userId?: string;
    companyDb?: string;
    activity?: string;
    search?: string;
  }): Promise<AuditLogRecord[]> => {
    const params: Record<string, any> = {
      limit: options?.limit ?? 100,
    };
    if (options?.days && options.days > 0) params.days = options.days;
    if (options?.userId && options.userId.trim()) params.user_id = options.userId.trim();
    if (options?.companyDb && options.companyDb.trim()) params.company_db = options.companyDb.trim();
    if (options?.activity && options.activity.trim()) params.activity = options.activity.trim();
    if (options?.search && options.search.trim()) params.search = options.search.trim();

    const res = await client.get('/audit/logs', { params });
    return res.data.data;
  },

  logUserAction: async (payload: {
    workflow_id?: string;
    master_type?: string;
    action?: string;
    activity: string;
    user_id?: string;
    company_db?: string;
    transaction_num?: string;
    previous_value?: any;
    updated_value?: any;
    details?: string;
  }) => {
    const res = await client.post('/audit/log-action', payload);
    return res.data;
  },

  downloadAuditLogFile: async (): Promise<{ blob: Blob; filename: string }> => {
    const res = await client.get('/audit/download-log', {
      responseType: 'blob',
    });
    let filename = `SAP_Audit_Trail_${new Date().toISOString().slice(0, 10)}.log`;
    const disposition = res.headers['content-disposition'] || res.headers['Content-Disposition'];
    if (disposition && typeof disposition === 'string') {
      const match = disposition.match(/filename="?([^"]+)"?/);
      if (match && match[1]) {
        filename = match[1];
      }
    }
    return { blob: res.data, filename };
  },

  getDashboardStats: async (days?: number | null): Promise<DashboardStats> => {
    const url = days && days > 0 ? `/dashboard/stats?days=${days}` : '/dashboard/stats';
    const res = await client.get(url);
    return res.data.data;
  },


  // Dynamic Connections Configuration (connections.json)
  getConnectionsConfig: async () => {
    const res = await client.get('/config/connections');
    return res.data.data;
  },

  updateConnectionsConfig: async (payload: any) => {
    const res = await client.post('/config/connections', payload);
    return res.data;
  },

  reloadConnectionsConfig: async () => {
    const res = await client.post('/config/reload');
    return res.data;
  },

  // Autonomous SAP AI Agent API
  sendAgentMessage: async (message: string, history?: any[]) => {
    const res = await client.post('/agent/chat', { message, history });
    return res.data;
  },

  updateEntityField: async (entity: string, key: string, fields: Record<string, any>) => {
    const res = await client.post('/agent/update-field', { entity, key, fields });
    return res.data;
  },

  confirmCreateMasterData: async (entity: string, data: Record<string, any>) => {
    const res = await client.post('/agent/confirm-create', { entity, data });
    return res.data;
  },

  getAgentSuggestions: async () => {
    const res = await client.get('/agent/suggestions');
    return res.data;
  },

  transcribeAudio: async (audioBlob: Blob, language = 'en'): Promise<{ success: boolean; text: string; message?: string }> => {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    formData.append('language', language);
    const res = await client.post('/agent/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    });
    return res.data;
  },

  // Master Data Export (Live SAP & Workflows)
  downloadMasterDataExcel: async (
    entity: string,
    days?: number | null,
    search?: string,
    limit = 5000
  ): Promise<{ blob: Blob; filename: string }> => {
    const params: Record<string, any> = { entity, limit };
    if (days && days > 0) {
      params.days = days;
    }
    if (search && search.trim()) {
      params.search = search.trim();
    }
    const res = await client.get('/export/excel', {
      params,
      responseType: 'blob'
    });
    
    // Extract filename from Content-Disposition header if available
    let filename = `SAP_${entity}_${days ? `last_${days}_days` : 'all_time'}_${new Date().toISOString().slice(0, 10)}.xlsx`;
    const disposition = res.headers['content-disposition'] || res.headers['Content-Disposition'];
    if (disposition && typeof disposition === 'string') {
      const match = disposition.match(/filename="?([^"]+)"?/);
      if (match && match[1]) {
        filename = match[1];
      }
    }
    
    return { blob: res.data, filename };
  },

  downloadMasterDataCsv: async (
    entity: string,
    days?: number | null,
    search?: string,
    limit = 2000
  ): Promise<{ blob: Blob; filename: string }> => {
    const params: Record<string, any> = { entity, limit };
    if (days && days > 0) {
      params.days = days;
    }
    if (search && search.trim()) {
      params.search = search.trim();
    }
    const res = await client.get('/export/csv', {
      params,
      responseType: 'blob'
    });
    
    // Extract filename from Content-Disposition header if available
    let filename = `SAP_${entity}_${days ? `last_${days}_days` : 'all_time'}_${new Date().toISOString().slice(0, 10)}.csv`;
    const disposition = res.headers['content-disposition'] || res.headers['Content-Disposition'];
    if (disposition && typeof disposition === 'string') {
      const match = disposition.match(/filename="?([^"]+)"?/);
      if (match && match[1]) {
        filename = match[1];
      }
    }
    
    return { blob: res.data, filename };
  },

  downloadMasterDataJson: async (
    entity: string,
    days?: number | null,
    search?: string,
    limit = 2000
  ): Promise<{ data: any; filename: string }> => {
    const params: Record<string, any> = { entity, limit };
    if (days && days > 0) {
      params.days = days;
    }
    if (search && search.trim()) {
      params.search = search.trim();
    }
    const res = await client.get('/export/json', { params });
    const filename = `SAP_${entity}_${days ? `last_${days}_days` : 'all_time'}_${new Date().toISOString().slice(0, 10)}.json`;
    return { data: res.data, filename };
  },

  // Autonomous AI Agent History & Action Ledger
  getAgentHistory: async (params?: {
    limit?: number;
    offset?: number;
    days?: number | null;
    entity?: string;
    action?: string;
    search?: string;
    user_id?: string;
    company_db?: string;
  }): Promise<AgentHistoryResponse> => {
    const cleanParams: Record<string, any> = {};
    if (params) {
      if (params.limit) cleanParams.limit = params.limit;
      if (params.offset) cleanParams.offset = params.offset;
      if (params.days && params.days > 0) cleanParams.days = params.days;
      if (params.entity && params.entity !== 'all') cleanParams.entity = params.entity;
      if (params.action && params.action !== 'all') cleanParams.action = params.action;
      if (params.search && params.search.trim()) cleanParams.search = params.search.trim();
      if (params.user_id) cleanParams.user_id = params.user_id;
      if (params.company_db) cleanParams.company_db = params.company_db;
    }
    const res = await client.get('/agent/history', { params: cleanParams });
    return res.data;
  },

  getAgentHistoryStats: async (company_db?: string): Promise<AgentHistoryStats> => {
    const params = company_db ? { company_db } : {};
    const res = await client.get('/agent/history/stats', { params });
    return res.data;
  },

  saveAgentSession: async (data: {
    session_id: string;
    title?: string;
    user_id?: string;
    company_db?: string;
    messages: any[];
  }): Promise<any> => {
    const res = await client.post('/agent/sessions', data);
    return res.data;
  },

  listAgentSessions: async (user_id?: string, limit = 20): Promise<{ sessions: AgentChatSession[] }> => {
    const params: Record<string, any> = { limit };
    if (user_id) params.user_id = user_id;
    const res = await client.get('/agent/sessions', { params });
    return res.data;
  },

  getAgentSession: async (session_id: string): Promise<{ session: AgentChatSession }> => {
    const res = await client.get(`/agent/sessions/${session_id}`);
    return res.data;
  },

  deleteAgentSession: async (session_id: string): Promise<{ success: boolean }> => {
    const res = await client.delete(`/agent/sessions/${session_id}`);
    return res.data;
  },

  getApiBase: () => dynamicApiBase,
  setApiBase: (url: string) => {
    dynamicApiBase = url;
    client.defaults.baseURL = url;
  },
};
