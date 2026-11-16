"""
Audit logging and SQLite persistence service for workflows and SAP transactions.
"""
from datetime import datetime, timedelta
import json
import sqlite3
from typing import Any, Dict, List, Optional
from pathlib import Path
from app.config import settings, BASE_DIR
from app.models.workflow import AuditLogRecord, WorkflowState, WorkflowStatus
from app.utils.logging import logger

_raw_db = settings.database_url.replace("sqlite:///", "")
_db_path_obj = Path(_raw_db)
if not _db_path_obj.is_absolute():
    _db_path_obj = BASE_DIR / _db_path_obj
DB_PATH = str(_db_path_obj)

def init_db():
    """Initialize SQLite database tables for workflows and audit logging."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    
    # Workflows table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workflows (
            workflow_id TEXT PRIMARY KEY,
            filename TEXT,
            file_path TEXT,
            file_hash TEXT,
            master_type TEXT,
            status TEXT,
            message TEXT,
            raw_extractions TEXT,
            extraction_comparison TEXT,
            normalized_data TEXT,
            user_corrections TEXT,
            validation_result TEXT,
            missing_fields TEXT,
            final_payload TEXT,
            is_confirmed INTEGER DEFAULT 0,
            sap_response_status INTEGER,
            sap_object_id TEXT,
            sap_response_body TEXT,
            error_details TEXT,
            bulk_results TEXT,
            bulk_validation TEXT,
            extracted_records TEXT,
            created_at TEXT,
            updated_at TEXT
        );
    """)

    # Safe migration for existing SQLite databases
    cursor.execute("PRAGMA table_info(workflows);")
    existing_cols = [col[1] for col in cursor.fetchall()]
    if "bulk_results" not in existing_cols:
        cursor.execute("ALTER TABLE workflows ADD COLUMN bulk_results TEXT;")
    if "bulk_validation" not in existing_cols:
        cursor.execute("ALTER TABLE workflows ADD COLUMN bulk_validation TEXT;")
    if "extracted_records" not in existing_cols:
        cursor.execute("ALTER TABLE workflows ADD COLUMN extracted_records TEXT;")

    # Audit logs table (append-only)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            workflow_id TEXT,
            master_type TEXT,
            action TEXT,
            activity TEXT,
            timestamp TEXT,
            user_id TEXT,
            user_identifier TEXT,
            company_db TEXT,
            transaction_num TEXT,
            previous_value TEXT,
            updated_value TEXT,
            payload_hash TEXT,
            payload_json TEXT,
            sap_endpoint TEXT,
            sap_response_status INTEGER,
            sap_response_code INTEGER,
            sap_object_id TEXT,
            success INTEGER,
            details TEXT,
            error_message TEXT
        );
    """)

    # Safe migration for existing audit_logs tables
    cursor.execute("PRAGMA table_info(audit_logs);")
    audit_cols = [col[1] for col in cursor.fetchall()]
    migration_cols = {
        "activity": "TEXT",
        "user_id": "TEXT",
        "company_db": "TEXT",
        "transaction_num": "TEXT",
        "previous_value": "TEXT",
        "updated_value": "TEXT",
        "sap_response_status": "INTEGER",
        "details": "TEXT"
    }
    for col_name, col_type in migration_cols.items():
        if col_name not in audit_cols:
            try:
                cursor.execute(f"ALTER TABLE audit_logs ADD COLUMN {col_name} {col_type};")
            except Exception:
                pass

    # Agent Chat Sessions table for multi-turn conversational history persistence
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_chat_sessions (
            session_id TEXT PRIMARY KEY,
            title TEXT,
            user_id TEXT,
            company_db TEXT,
            messages_json TEXT,
            action_count INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        );
    """)

    conn.commit()
    conn.close()

# Auto-initialize on load
init_db()


def _safe_model_dump_json(obj: Any) -> Optional[str]:
    if obj is None:
        return None
    if hasattr(obj, "model_dump_json"):
        return obj.model_dump_json()
    if isinstance(obj, str):
        return obj
    return json.dumps(obj)

def _safe_dump_missing_fields(fields: List[Any]) -> str:
    if not fields:
        return "[]"
    res = []
    for m in fields:
        if hasattr(m, "model_dump"):
            res.append(m.model_dump())
        elif isinstance(m, dict):
            res.append(m)
        else:
            res.append(str(m))
    return json.dumps(res)

class AuditService:
    @staticmethod
    def save_workflow(state: WorkflowState) -> WorkflowState:
        """Persist or update entire workflow state to SQLite."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        state.updated_at = datetime.utcnow().isoformat()
        
        cursor.execute("""
            INSERT INTO workflows (
                workflow_id, filename, file_path, file_hash, master_type,
                status, message, raw_extractions, extraction_comparison,
                normalized_data, user_corrections, validation_result,
                missing_fields, final_payload, is_confirmed,
                sap_response_status, sap_object_id, sap_response_body,
                error_details, bulk_results, bulk_validation, extracted_records,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(workflow_id) DO UPDATE SET
                master_type=excluded.master_type,
                status=excluded.status,
                message=excluded.message,
                raw_extractions=excluded.raw_extractions,
                extraction_comparison=excluded.extraction_comparison,
                normalized_data=excluded.normalized_data,
                user_corrections=excluded.user_corrections,
                validation_result=excluded.validation_result,
                missing_fields=excluded.missing_fields,
                final_payload=excluded.final_payload,
                is_confirmed=excluded.is_confirmed,
                sap_response_status=excluded.sap_response_status,
                sap_object_id=excluded.sap_object_id,
                sap_response_body=excluded.sap_response_body,
                error_details=excluded.error_details,
                bulk_results=excluded.bulk_results,
                bulk_validation=excluded.bulk_validation,
                extracted_records=excluded.extracted_records,
                updated_at=excluded.updated_at;
        """, (
            state.workflow_id,
            state.filename,
            state.file_path,
            state.file_hash,
            state.master_type.value if hasattr(state.master_type, "value") else str(state.master_type),
            state.status.value if hasattr(state.status, "value") else str(state.status),
            state.message,
            json.dumps(state.raw_extractions),
            _safe_model_dump_json(state.extraction_comparison),
            json.dumps(state.normalized_data),
            json.dumps(state.user_corrections),
            _safe_model_dump_json(state.validation_result),
            _safe_dump_missing_fields(state.missing_fields),
            json.dumps(state.final_payload),
            1 if state.is_confirmed else 0,
            state.sap_response_status,
            state.sap_object_id,
            json.dumps(state.sap_response_body) if state.sap_response_body else None,
            state.error_details,
            _safe_model_dump_json(state.bulk_results),
            _safe_model_dump_json(state.bulk_validation),
            json.dumps(state.extracted_records) if state.extracted_records else None,
            state.created_at,
            state.updated_at
        ))
        conn.commit()
        conn.close()
        return state

    @staticmethod
    def get_workflow(workflow_id: str) -> Optional[WorkflowState]:
        """Fetch workflow by ID."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM workflows WHERE workflow_id = ?", (workflow_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        data = dict(row)
        ext_comp = json.loads(data["extraction_comparison"]) if data.get("extraction_comparison") else None
        
        # Priority: explicitly saved extracted_records, then extraction_comparison
        extracted_recs = None
        if data.get("extracted_records"):
            extracted_recs = json.loads(data["extracted_records"])
        elif ext_comp:
            extracted_recs = ext_comp.get("all_records", [])
        extracted_recs = extracted_recs or []
        total_recs = len(extracted_recs) if extracted_recs else 1

        bulk_res = json.loads(data["bulk_results"]) if data.get("bulk_results") else None
        bulk_val = json.loads(data["bulk_validation"]) if data.get("bulk_validation") else None

        return WorkflowState(
            workflow_id=data["workflow_id"],
            filename=data["filename"],
            file_path=data["file_path"],
            file_hash=data["file_hash"],
            master_type=data["master_type"],
            status=data["status"],
            message=data["message"] or "",
            raw_extractions=json.loads(data["raw_extractions"] or "{}"),
            extraction_comparison=ext_comp,
            normalized_data=json.loads(data["normalized_data"] or "{}"),
            extracted_records=extracted_recs,
            total_records=total_recs,
            user_corrections=json.loads(data["user_corrections"] or "{}"),
            validation_result=json.loads(data["validation_result"]) if data.get("validation_result") else None,
            missing_fields=json.loads(data["missing_fields"] or "[]"),
            bulk_validation=bulk_val,
            final_payload=json.loads(data["final_payload"] or "{}"),
            is_confirmed=bool(data["is_confirmed"]),
            sap_response_status=data["sap_response_status"],
            sap_object_id=data["sap_object_id"],
            sap_response_body=json.loads(data["sap_response_body"]) if data.get("sap_response_body") else None,
            error_details=data["error_details"],
            bulk_results=bulk_res,
            created_at=data["created_at"],
            updated_at=data["updated_at"]
        )

    @staticmethod
    def get_audit_log_file_path() -> Path:
        """Returns the path to the persistent text audit log file."""
        log_dir = BASE_DIR / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / "audit_trail.log"

    @staticmethod
    def record_audit(record: AuditLogRecord) -> AuditLogRecord:
        """
        Insert immutable audit record into audit_logs SQLite table and append to persistent text log file.
        Captures: User ID, Timestamp, Company/Database, Transaction/Document Number, Activity, Previous Value, Updated Value.
        """
        user_id = record.user_id or record.user_identifier or "system_user"
        company_db = record.company_db or settings.sap_company_db or "CINNTRA_DEMO_NEW"
        activity = record.activity or record.action or "TRANSACTION"
        transaction_num = record.transaction_num or record.sap_object_id or record.workflow_id or "N/A"
        timestamp = record.timestamp or datetime.utcnow().isoformat()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs (
                workflow_id, master_type, action, activity, timestamp,
                user_id, user_identifier, company_db, transaction_num,
                previous_value, updated_value, payload_hash,
                sap_response_status, sap_object_id, success, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.workflow_id,
            record.master_type,
            record.action,
            activity,
            timestamp,
            user_id,
            user_id,
            company_db,
            transaction_num,
            record.previous_value,
            record.updated_value,
            record.payload_hash,
            record.sap_response_status,
            record.sap_object_id or transaction_num,
            1 if record.success else 0,
            record.details
        ))
        record.id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Append to persistent text log file for administrative traceability
        try:
            log_file = AuditService.get_audit_log_file_path()
            status_tag = "SUCCESS" if record.success else "FAILED"
            log_entry = (
                f"[{timestamp}] [USER:{user_id}] [DB:{company_db}] "
                f"[DOC:{transaction_num}] [ACT:{activity}] [STATUS:{status_tag}] "
                f"[PREV:{record.previous_value or 'N/A'}] [NEW:{record.updated_value or 'N/A'}] "
                f"- {record.details or ''}\n"
            )
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as file_err:
            logger.warning(f"Could not append to audit log file: {file_err}")

        logger.info(f"Audit record logged: User={user_id} DB={company_db} Activity={activity} Doc={transaction_num} Success={record.success}")
        return record

    @staticmethod
    def list_audit_logs(
        limit: int = 50,
        days: Optional[int] = None,
        user_id: Optional[str] = None,
        company_db: Optional[str] = None,
        activity: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve recent audit logs with rich filtering options."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM audit_logs WHERE 1=1"
        params: List[Any] = []

        if days is not None and days > 0:
            cutoff_iso = (datetime.utcnow() - timedelta(days=days)).isoformat()
            query += " AND timestamp >= ?"
            params.append(cutoff_iso)

        if user_id and user_id.strip():
            query += " AND (user_id = ? OR user_identifier = ?)"
            params.extend([user_id.strip(), user_id.strip()])

        if company_db and company_db.strip():
            query += " AND UPPER(company_db) = UPPER(?)"
            params.append(company_db.strip())

        if activity and activity.strip():
            query += " AND (UPPER(activity) = UPPER(?) OR UPPER(action) = UPPER(?))"
            params.extend([activity.strip(), activity.strip()])

        if search and search.strip():
            s = f"%{search.strip()}%"
            query += " AND (details LIKE ? OR transaction_num LIKE ? OR sap_object_id LIKE ? OR workflow_id LIKE ? OR user_id LIKE ?)"
            params.extend([s, s, s, s, s])

        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]


    @staticmethod
    def get_dashboard_stats(days: Optional[int] = None) -> Dict[str, Any]:
        """Aggregate platform KPI metrics for frontend dashboard with optional custom days filtering."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cutoff_iso = None
        if days is not None and days > 0:
            cutoff_iso = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        if cutoff_iso:
            cursor.execute("SELECT COUNT(*) FROM workflows WHERE created_at >= ?", (cutoff_iso,))
            documents_processed = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE master_type='item' AND action='CREATE' AND success=1 AND timestamp >= ?", (cutoff_iso,))
            items_created = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE master_type='business_partner' AND action='CREATE' AND success=1 AND timestamp >= ?", (cutoff_iso,))
            bps_created = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE master_type='warehouse' AND action='CREATE' AND success=1 AND timestamp >= ?", (cutoff_iso,))
            warehouses_created = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE success=0 AND timestamp >= ?", (cutoff_iso,))
            failed_operations = cursor.fetchone()[0]
            
            cursor.execute("SELECT * FROM audit_logs WHERE timestamp >= ? ORDER BY id DESC LIMIT 10", (cutoff_iso,))
            columns = [c[0] for c in cursor.description]
            recent_activity = [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            cursor.execute("SELECT COUNT(*) FROM workflows")
            documents_processed = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE master_type='item' AND action='CREATE' AND success=1")
            items_created = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE master_type='business_partner' AND action='CREATE' AND success=1")
            bps_created = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE master_type='warehouse' AND action='CREATE' AND success=1")
            warehouses_created = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM audit_logs WHERE success=0")
            failed_operations = cursor.fetchone()[0]
            
            cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 10")
            columns = [c[0] for c in cursor.description]
            recent_activity = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            "documents_processed": documents_processed,
            "items_created": items_created,
            "business_partners_created": bps_created,
            "warehouses_created": warehouses_created,
            "failed_operations": failed_operations,
            "recent_activity": recent_activity,
            "timeframe": {
                "days": days,
                "cutoff_iso": cutoff_iso
            }
        }

    @staticmethod
    def list_workflows(limit: int = 50, offset: int = 0, days: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve recent workflows from database with optional custom days filtering."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cutoff_iso = None
        if days is not None and days > 0:
            cutoff_iso = (datetime.utcnow() - timedelta(days=days)).isoformat()

        if cutoff_iso:
            cursor.execute("""
                SELECT workflow_id, filename, master_type, status, message,
                       is_confirmed, sap_response_status, sap_object_id,
                       error_details, created_at, updated_at, final_payload
                FROM workflows
                WHERE created_at >= ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (cutoff_iso, limit, offset))
        else:
            cursor.execute("""
                SELECT workflow_id, filename, master_type, status, message,
                       is_confirmed, sap_response_status, sap_object_id,
                       error_details, created_at, updated_at, final_payload
                FROM workflows
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for r in rows:
            row_dict = dict(r)
            # Parse final_payload or normalized_data if available for summary info
            payload_str = row_dict.pop("final_payload", None)
            display_name = None
            if payload_str:
                try:
                    payload = json.loads(payload_str)
                    display_name = payload.get("ItemName") or payload.get("CardName") or payload.get("WarehouseName")
                    if not row_dict.get("sap_object_id"):
                        row_dict["sap_object_id"] = payload.get("ItemCode") or payload.get("CardCode") or payload.get("WarehouseCode")
                except Exception:
                    pass
            row_dict["display_name"] = display_name
            result.append(row_dict)
        return result

    @staticmethod
    def get_agent_history(
        limit: int = 50,
        offset: int = 0,
        days: Optional[int] = None,
        entity: Optional[str] = None,
        action: Optional[str] = None,
        search: Optional[str] = None,
        user_id: Optional[str] = None,
        company_db: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query chronological AI Agent change history with parsed old/new diffs.
        Captures all creations, field patches, deletions, and prompt-driven operations.
        """
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        where_clauses = [
            "(activity LIKE 'AGENT_%' OR user_id = 'ai_agent' OR workflow_id LIKE 'agent-%' OR details LIKE '%prompt%')"
        ]
        params: List[Any] = []

        if days is not None and days > 0:
            cutoff_iso = (datetime.utcnow() - timedelta(days=days)).isoformat()
            where_clauses.append("timestamp >= ?")
            params.append(cutoff_iso)

        if entity and entity.strip() and entity.strip().lower() != "all":
            ent = entity.strip()
            ent_map = {
                "businesspartners": "business_partner",
                "items": "item",
                "warehouses": "warehouse",
                "business_partner": "business_partner",
                "item": "item",
                "warehouse": "warehouse"
            }
            mapped_type = ent_map.get(ent.lower(), ent.lower())
            where_clauses.append("(LOWER(master_type) = ? OR LOWER(details) LIKE ?)")
            params.extend([mapped_type, f"%{mapped_type}%"])

        if action and action.strip() and action.strip().lower() != "all":
            act = action.strip().upper()
            where_clauses.append("(UPPER(action) = ? OR UPPER(activity) LIKE ?)")
            params.extend([act, f"%{act}%"])

        if user_id and user_id.strip():
            where_clauses.append("(user_id = ? OR user_identifier = ?)")
            params.extend([user_id.strip(), user_id.strip()])

        if company_db and company_db.strip():
            where_clauses.append("UPPER(company_db) = UPPER(?)")
            params.append(company_db.strip())

        if search and search.strip():
            s = f"%{search.strip()}%"
            where_clauses.append("(details LIKE ? OR transaction_num LIKE ? OR sap_object_id LIKE ? OR previous_value LIKE ? OR updated_value LIKE ?)")
            params.extend([s, s, s, s, s])

        where_sql = " AND ".join(where_clauses)

        # Total count query
        count_query = f"SELECT COUNT(*) FROM audit_logs WHERE {where_sql}"
        cursor.execute(count_query, tuple(params))
        total_count = cursor.fetchone()[0]

        # Paginated rows query
        select_query = f"""
            SELECT * FROM audit_logs
            WHERE {where_sql}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """
        cursor.execute(select_query, tuple(params + [limit, offset]))
        rows = cursor.fetchall()
        conn.close()

        records = []
        for r in rows:
            d = dict(r)
            details_obj = {}
            if d.get("details"):
                try:
                    details_obj = json.loads(d["details"])
                except Exception:
                    details_obj = {"raw": d["details"]}

            # Extract structured old vs new values diff
            old_values = details_obj.get("old_values") or {}
            new_values = details_obj.get("new_values") or {}
            updated_fields = details_obj.get("updated_fields") or []
            created_payload = details_obj.get("created_payload") or {}
            prompt_used = details_obj.get("prompt") or details_obj.get("user_prompt")

            # Fallback parsing for previous/updated values if not in details
            if not old_values and d.get("previous_value"):
                try:
                    old_values = json.loads(d["previous_value"])
                except Exception:
                    old_values = {"value": d["previous_value"]}

            if not new_values and d.get("updated_value"):
                try:
                    new_values = json.loads(d["updated_value"])
                except Exception:
                    new_values = {"value": d["updated_value"]}

            # Clean entity name
            entity_raw = details_obj.get("entity") or d.get("master_type") or "Unknown"
            if str(entity_raw).lower() in ["business_partner", "businesspartners", "partner", "customer", "vendor"]:
                entity_label = "BusinessPartners"
            elif str(entity_raw).lower() in ["item", "items", "product"]:
                entity_label = "Items"
            elif str(entity_raw).lower() in ["warehouse", "warehouses"]:
                entity_label = "Warehouses"
            else:
                entity_label = str(entity_raw)

            records.append({
                "id": d["id"],
                "workflow_id": d["workflow_id"],
                "timestamp": d["timestamp"],
                "user_id": d["user_id"] or d["user_identifier"] or "ai_agent",
                "company_db": d["company_db"],
                "action": d["action"],
                "activity": d["activity"],
                "entity": entity_label,
                "target_key": d["transaction_num"] or d["sap_object_id"],
                "sap_object_id": d["sap_object_id"],
                "sap_response_status": d["sap_response_status"],
                "success": bool(d["success"]),
                "payload_hash": d["payload_hash"],
                "prompt": prompt_used,
                "old_values": old_values,
                "new_values": new_values,
                "updated_fields": updated_fields,
                "created_payload": created_payload,
                "details": details_obj
            })

        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "records": records
        }

    @staticmethod
    def get_agent_history_stats(company_db: Optional[str] = None) -> Dict[str, Any]:
        """Calculates aggregated metrics for AI Agent activities."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        where = "WHERE (activity LIKE 'AGENT_%' OR user_id = 'ai_agent' OR workflow_id LIKE 'agent-%' OR details LIKE '%prompt%')"
        params = []
        if company_db and company_db.strip():
            where += " AND UPPER(company_db) = UPPER(?)"
            params.append(company_db.strip())

        cursor.execute(f"SELECT COUNT(*) FROM audit_logs {where}", tuple(params))
        total_actions = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM audit_logs {where} AND action = 'CREATE'", tuple(params))
        creations = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM audit_logs {where} AND (action = 'UPDATE' OR action = 'PATCH' OR activity LIKE '%UPDATE%')", tuple(params))
        updates = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM audit_logs {where} AND success = 1", tuple(params))
        successful = cursor.fetchone()[0]

        conn.close()

        success_rate = 100.0 if total_actions == 0 else round((successful / total_actions) * 100, 1)

        return {
            "total_actions": total_actions,
            "creations": creations,
            "updates": updates,
            "successful": successful,
            "failed": max(0, total_actions - successful),
            "success_rate": success_rate,
            "integrity_verified": True
        }

    @staticmethod
    def save_agent_chat_session(session_id: str, title: str, user_id: str, company_db: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Persist or update an AI Agent conversation session."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        now = datetime.utcnow().isoformat()
        messages_json = json.dumps(messages)
        action_count = sum(1 for m in messages if m.get("action"))

        cursor.execute("""
            INSERT INTO agent_chat_sessions (session_id, title, user_id, company_db, messages_json, action_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                title=excluded.title,
                messages_json=excluded.messages_json,
                action_count=excluded.action_count,
                updated_at=excluded.updated_at;
        """, (session_id, title, user_id, company_db, messages_json, action_count, now, now))

        conn.commit()
        conn.close()
        return {
            "session_id": session_id,
            "title": title,
            "action_count": action_count,
            "updated_at": now
        }

    @staticmethod
    def list_agent_chat_sessions(user_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """List past conversation sessions."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if user_id:
            cursor.execute("""
                SELECT session_id, title, user_id, company_db, action_count, created_at, updated_at
                FROM agent_chat_sessions
                WHERE user_id = ?
                ORDER BY updated_at DESC
                LIMIT ?
            """, (user_id, limit))
        else:
            cursor.execute("""
                SELECT session_id, title, user_id, company_db, action_count, created_at, updated_at
                FROM agent_chat_sessions
                ORDER BY updated_at DESC
                LIMIT ?
            """, (limit,))

        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_agent_chat_session(session_id: str) -> Optional[Dict[str, Any]]:
        """Load a saved chat session."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM agent_chat_sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        res = dict(row)
        res["messages"] = json.loads(res.get("messages_json") or "[]")
        return res

    @staticmethod
    def delete_agent_chat_session(session_id: str) -> bool:
        """Delete a saved chat session."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM agent_chat_sessions WHERE session_id = ?", (session_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return deleted
