/**
 * Type definitions for SAP AI Master Data Automation Platform.
 */

export type MasterDataType = 'item' | 'business_partner' | 'warehouse' | 'unknown';

export type WorkflowStatus =
  | 'UPLOADED'
  | 'EXTRACTING'
  | 'EXTRACTION_CONFLICT'
  | 'EXTRACTED'
  | 'VALIDATING'
  | 'MISSING_FIELDS'
  | 'READY_FOR_CONFIRMATION'
  | 'CONFIRMED'
  | 'CREATING_IN_SAP'
  | 'CREATED'
  | 'DUPLICATE'
  | 'SAP_ERROR'
  | 'FAILED'
  | 'CANCELLED';

export type ConflictStatus = 'AGREED' | 'CONFLICT' | 'PARTIAL';

export interface FieldComparison {
  field_name: string;
  status: ConflictStatus;
  agreed_value?: any;
  extracted_values: Record<string, any>;
  distinct_values: any[];
  resolved_value?: any;
  is_resolved: boolean;
}

export interface ExtractionComparisonResult {
  status: ConflictStatus;
  master_type: MasterDataType;
  overall_confidence: number;
  field_comparisons: Record<string, FieldComparison>;
  agreed_data: Record<string, any>;
  conflicts: FieldComparison[];
  extra_fields: Record<string, any>;
  all_records?: Record<string, any>[];
  total_records?: number;
}

export interface MissingFieldInfo {
  field: string;
  label: string;
  reason: string;
  field_type?: string;
  example?: string;
}

export interface ValidationErrorItem {
  field: string;
  message: string;
  error_type: string;
  provided_value?: any;
}

export interface ValidationResult {
  valid: boolean;
  master_type: string;
  missing_fields: MissingFieldInfo[];
  invalid_fields: ValidationErrorItem[];
  warnings: string[];
  validated_data: Record<string, any>;
}

export interface BulkRecordResult {
  index: number;
  code: string;
  name: string;
  status: 'CREATED' | 'DUPLICATE' | 'VALIDATION_ERROR' | 'SAP_ERROR' | string;
  sap_object_id?: string;
  error?: string;
  duration_ms?: number;
}

export interface BulkCreationSummary {
  total_submitted: number;
  created_count: number;
  duplicate_count: number;
  failed_count: number;
  records: BulkRecordResult[];
  started_at: string;
  completed_at?: string;
}

export interface RecordValidationStatus {
  index: number;
  code: string;
  name: string;
  valid: boolean;
  missing_fields: string[];
  errors: string[];
}

export interface BulkValidationSummary {
  total: number;
  valid_count: number;
  invalid_count: number;
  missing_fields_summary: string[];
  record_statuses: RecordValidationStatus[];
}

export interface WorkflowState {
  workflow_id: string;
  filename?: string;
  file_path?: string;
  file_hash?: string;
  master_type: MasterDataType;
  status: WorkflowStatus;
  message: string;
  raw_extractions?: Record<string, any>;
  extraction_comparison?: ExtractionComparisonResult;
  normalized_data: Record<string, any>;
  extracted_records?: Record<string, any>[];
  total_records?: number;
  user_corrections?: Record<string, any>;
  validation_result?: ValidationResult;
  missing_fields: MissingFieldInfo[];
  bulk_validation?: BulkValidationSummary;
  final_payload: Record<string, any>;
  is_confirmed: boolean;
  sap_response_status?: number;
  sap_object_id?: string;
  sap_response_body?: Record<string, any>;
  error_details?: string;
  bulk_results?: BulkCreationSummary;
  created_at: string;
  updated_at: string;
}

export interface AuditLogRecord {
  id?: number;
  workflow_id?: string;
  master_type: string;
  action: string;
  activity?: string;
  timestamp: string;
  user_id?: string;
  user_identifier: string;
  company_db?: string;
  transaction_num?: string;
  previous_value?: string;
  updated_value?: string;
  payload_hash?: string;
  sap_response_status?: number;
  sap_object_id?: string;
  success: boolean;
  details?: string;
}

export interface WorkflowSummary {
  workflow_id: string;
  filename?: string;
  master_type: MasterDataType;
  status: WorkflowStatus;
  message?: string;
  is_confirmed: boolean | number;
  sap_response_status?: number;
  sap_object_id?: string;
  error_details?: string;
  created_at: string;
  updated_at: string;
  display_name?: string;
}

export interface SapRecordsResponse {
  entity: string;
  total: number;
  records: Record<string, any>[];
  database?: string;
  server?: string;
  error?: string;
}

export interface DashboardStats {
  documents_processed: number;
  items_created: number;
  business_partners_created: number;
  warehouses_created: number;
  failed_operations: number;
  recent_activity: AuditLogRecord[];
  sap_counts?: {
    Items: number;
    BusinessPartners: number;
    Warehouses: number;
  };
  items_total?: number;
  business_partners_total?: number;
  warehouses_total?: number;
  database?: {
    company_db: string;
    service_layer_url: string;
    is_configured: boolean;
  };
  recent_workflows?: WorkflowSummary[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  extracted_updates?: Record<string, any>;
  citations?: Array<{
    document: string;
    section?: string;
    score?: number;
    page?: number;
  }>;
}

export interface ChatMessageResponse {
  reply: string;
  citations?: Array<{
    document: string;
    section?: string;
    score?: number;
    page?: number;
  }>;
  extracted_updates?: Record<string, any>;
}

export interface RAGSearchResult {
  content: string;
  source: string;
  score: number;
  metadata: {
    entity: string;
    document_type: string;
    section: string;
    file_path?: string;
  };
}

export interface SapCompany {
  company_db: string;
  company_name: string;
  localization: string;
  currency: string;
  description: string;
  is_active?: boolean;
  service_layer_url?: string;
}

export interface SapHealthResponse {
  connected: boolean;
  status: string;
  message: string;
  service_layer_url: string;
  company_db: string;
  company_name?: string;
  username: string;
  available_companies?: SapCompany[];
}

export interface AuthUser {
  email: string;
  name: string;
  role: string;
  companyDb?: string;
  companyName?: string;
  avatarUrl?: string;
  loginTime: string;
}

export interface LoginCredentials {
  email: string;
  password?: string;
  companyDb?: string;
  rememberMe?: boolean;
}

export interface AgentHistoryRecord {
  id: number;
  workflow_id?: string;
  timestamp: string;
  user_id: string;
  company_db: string;
  action: 'CREATE' | 'UPDATE' | 'PATCH' | 'QUERY' | string;
  activity: string;
  entity: 'BusinessPartners' | 'Items' | 'Warehouses' | string;
  target_key?: string;
  sap_object_id?: string;
  sap_response_status?: number;
  success: boolean;
  payload_hash?: string;
  prompt?: string;
  old_values: Record<string, any>;
  new_values: Record<string, any>;
  updated_fields: string[];
  created_payload: Record<string, any>;
  details: Record<string, any>;
}

export interface AgentHistoryResponse {
  success: boolean;
  status: string;
  total: number;
  limit: number;
  offset: number;
  records: AgentHistoryRecord[];
}

export interface AgentHistoryStats {
  total_actions: number;
  creations: number;
  updates: number;
  successful: number;
  failed: number;
  success_rate: number;
  integrity_verified: boolean;
}

export interface AgentChatSession {
  session_id: string;
  title: string;
  user_id: string;
  company_db: string;
  action_count: number;
  created_at: string;
  updated_at: string;
  messages?: any[];
}


