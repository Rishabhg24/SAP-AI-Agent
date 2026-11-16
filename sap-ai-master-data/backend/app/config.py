"""
Application configuration management using Pydantic Settings and dynamic connections.json.
Loads configuration dynamically from connections.json, environment variables, and .env file securely.
Allows runtime updates to all connection parameters without requiring source code edits.
"""
from typing import Any, Dict, Optional, Tuple
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
import os
import json
from pathlib import Path
from app.utils.logging import logger

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
PRIMARY_CONNECTIONS_FILE = BASE_DIR / "connections.json"
ROOT_CONNECTIONS_FILE = BASE_DIR.parent / "connections.json"

# Modification timestamps for hot-reloading
_last_connections_mtime: float = 0.0
_last_env_mtime: float = 0.0

def get_connections_file_path() -> Path:
    """
    Finds active connections.json configuration file path.
    Prioritizes ROOT_CONNECTIONS_FILE (at project root) or the most recently modified file.
    """
    if ROOT_CONNECTIONS_FILE.exists() and PRIMARY_CONNECTIONS_FILE.exists():
        try:
            if ROOT_CONNECTIONS_FILE.stat().st_mtime >= PRIMARY_CONNECTIONS_FILE.stat().st_mtime:
                return ROOT_CONNECTIONS_FILE
            return PRIMARY_CONNECTIONS_FILE
        except Exception:
            return ROOT_CONNECTIONS_FILE
    if ROOT_CONNECTIONS_FILE.exists():
        return ROOT_CONNECTIONS_FILE
    if PRIMARY_CONNECTIONS_FILE.exists():
        return PRIMARY_CONNECTIONS_FILE
    return ROOT_CONNECTIONS_FILE

def read_connections_json() -> Dict[str, Any]:
    """Reads connections.json if present and returns flattened environment dictionary."""
    file_path = get_connections_file_path()
    if not file_path.exists():
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        
        flat: Dict[str, Any] = {}
        server = raw.get("server", {})
        if "host" in server: flat["HOST"] = server["host"]
        if "port" in server: flat["PORT"] = int(server["port"])
        if "frontend_url" in server: flat["FRONTEND_URL"] = server["frontend_url"]
        if "frontend_port" in server: flat["FRONTEND_PORT"] = int(server["frontend_port"])
        if "cors_origins" in server:
            co = server["cors_origins"]
            flat["CORS_ORIGINS"] = ",".join(co) if isinstance(co, list) else str(co)
        if "environment" in server: flat["ENVIRONMENT"] = server["environment"]
        if "log_level" in server: flat["LOG_LEVEL"] = server["log_level"]

        sap = raw.get("sap", {})
        if "service_layer_url" in sap: flat["SAP_SERVICE_LAYER_URL"] = sap["service_layer_url"]
        if "company_db" in sap: flat["SAP_COMPANY_DB"] = sap["company_db"]
        if "username" in sap: flat["SAP_USERNAME"] = sap["username"]
        if "password" in sap: flat["SAP_PASSWORD"] = sap["password"]
        if "verify_ssl" in sap: flat["SAP_VERIFY_SSL"] = bool(sap["verify_ssl"])
        if "timeout_seconds" in sap: flat["SAP_TIMEOUT_SECONDS"] = float(sap["timeout_seconds"])

        ai = raw.get("ai", {})
        if "nvidia_api_key" in ai: flat["NVIDIA_API_KEY"] = ai["nvidia_api_key"]
        if "nvidia_base_url" in ai: flat["NVIDIA_BASE_URL"] = ai["nvidia_base_url"]
        if "nvidia_model" in ai: flat["NVIDIA_MODEL"] = ai["nvidia_model"]
        if "nvidia_temperature" in ai: flat["NVIDIA_TEMPERATURE"] = float(ai["nvidia_temperature"])
        if "nvidia_max_tokens" in ai: flat["NVIDIA_MAX_TOKENS"] = int(ai["nvidia_max_tokens"])
        if "nvidia_timeout_seconds" in ai: flat["NVIDIA_TIMEOUT_SECONDS"] = float(ai["nvidia_timeout_seconds"])

        db = raw.get("database", {})
        if "database_url" in db: flat["DATABASE_URL"] = db["database_url"]
        if "rag_collection_name" in db: flat["RAG_COLLECTION_NAME"] = db["rag_collection_name"]
        if "rag_db_path" in db: flat["RAG_DB_PATH"] = db["rag_db_path"]
        if "embedding_model" in db: flat["EMBEDDING_MODEL"] = db["embedding_model"]
        if "rag_top_k" in db: flat["RAG_TOP_K"] = int(db["rag_top_k"])
        if "max_file_size_mb" in db: flat["MAX_FILE_SIZE_MB"] = int(db["max_file_size_mb"])
        if "upload_dir" in db: flat["UPLOAD_DIR"] = db["upload_dir"]

        return flat
    except Exception as e:
        logger.error(f"Failed to read connections.json: {e}")
        return {}

class Settings(BaseSettings):
    # SAP Business One Service Layer
    sap_service_layer_url: str = Field(default="", alias="SAP_SERVICE_LAYER_URL")
    sap_company_db: str = Field(default="", alias="SAP_COMPANY_DB")
    sap_username: str = Field(default="", alias="SAP_USERNAME")
    sap_password: str = Field(default="", alias="SAP_PASSWORD")
    sap_verify_ssl: bool = Field(default=False, alias="SAP_VERIFY_SSL")
    sap_timeout_seconds: float = Field(default=30.0, alias="SAP_TIMEOUT_SECONDS")

    # NVIDIA Hosted LLM
    nvidia_api_key: str = Field(default="", alias="NVIDIA_API_KEY")
    nvidia_base_url: str = Field(default="https://integrate.api.nvidia.com/v1", alias="NVIDIA_BASE_URL")
    nvidia_model: str = Field(default="nvidia/nemotron-3.5-lightning-30b-a3b", alias="NVIDIA_MODEL")
    nvidia_temperature: float = Field(default=0.2, alias="NVIDIA_TEMPERATURE")
    nvidia_max_tokens: int = Field(default=2048, alias="NVIDIA_MAX_TOKENS")
    nvidia_timeout_seconds: float = Field(default=30.0, alias="NVIDIA_TIMEOUT_SECONDS")

    # Vector RAG Configuration
    rag_collection_name: str = Field(default="sap_knowledge", alias="RAG_COLLECTION_NAME")
    rag_db_path: str = Field(default="./chroma_db", alias="RAG_DB_PATH")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", alias="EMBEDDING_MODEL")
    rag_top_k: int = Field(default=5, alias="RAG_TOP_K")

    # General App & Web Server Settings
    environment: str = Field(default="development", alias="ENVIRONMENT")
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    frontend_url: str = Field(default="http://localhost:5173", alias="FRONTEND_URL")
    frontend_port: int = Field(default=5173, alias="FRONTEND_PORT")
    cors_origins: str = Field(default="", alias="CORS_ORIGINS")
    database_url: str = Field(default="sqlite:///./workflows.db", alias="DATABASE_URL")
    max_file_size_mb: int = Field(default=15, alias="MAX_FILE_SIZE_MB")
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def parsed_cors_origins(self) -> list[str]:
        """Returns normalized list of allowed CORS origins including frontend_url and custom origins."""
        origins: list[str] = []
        if self.frontend_url and self.frontend_url not in origins:
            origins.append(self.frontend_url)
        if self.cors_origins:
            if isinstance(self.cors_origins, list):
                for o in self.cors_origins:
                    cleaned = str(o).strip()
                    if cleaned and cleaned not in origins:
                        origins.append(cleaned)
            else:
                for o in str(self.cors_origins).split(","):
                    cleaned = o.strip()
                    if cleaned and cleaned not in origins:
                        origins.append(cleaned)
        # Development standard origins
        for dev_origin in [
            f"http://localhost:{self.frontend_port}",
            f"http://127.0.0.1:{self.frontend_port}",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:3000"
        ]:
            if dev_origin not in origins:
                origins.append(dev_origin)
        return origins

    @property
    def is_sap_configured(self) -> bool:
        """Returns True if SAP credentials are configured and not placeholder values."""
        return (
            bool(self.sap_service_layer_url)
            and "YOUR_SAP_SERVER" not in self.sap_service_layer_url
            and bool(self.sap_company_db)
            and bool(self.sap_username)
            and bool(self.sap_password)
            and self.sap_password != "YOUR_SAP_PASSWORD"
        )

    @property
    def is_nvidia_configured(self) -> bool:
        """Returns True if NVIDIA API key is not empty or default placeholder."""
        return (
            bool(self.nvidia_api_key)
            and self.nvidia_api_key != "YOUR_NEW_KEY"
            and self.nvidia_api_key != "YOUR_NEW_NVIDIA_API_KEY"
            and self.nvidia_api_key != "YOUR_NVIDIA_API_KEY"
        )

def create_settings() -> Settings:
    """Instantiates Settings layering values from connections.json and environment."""
    global _last_connections_mtime, _last_env_mtime
    s = Settings()
    json_data = read_connections_json()
    field_alias_map = {
        "HOST": "host",
        "PORT": "port",
        "FRONTEND_URL": "frontend_url",
        "FRONTEND_PORT": "frontend_port",
        "CORS_ORIGINS": "cors_origins",
        "ENVIRONMENT": "environment",
        "LOG_LEVEL": "log_level",
        "SAP_SERVICE_LAYER_URL": "sap_service_layer_url",
        "SAP_COMPANY_DB": "sap_company_db",
        "SAP_USERNAME": "sap_username",
        "SAP_PASSWORD": "sap_password",
        "SAP_VERIFY_SSL": "sap_verify_ssl",
        "SAP_TIMEOUT_SECONDS": "sap_timeout_seconds",
        "NVIDIA_API_KEY": "nvidia_api_key",
        "NVIDIA_BASE_URL": "nvidia_base_url",
        "NVIDIA_MODEL": "nvidia_model",
        "NVIDIA_TEMPERATURE": "nvidia_temperature",
        "NVIDIA_MAX_TOKENS": "nvidia_max_tokens",
        "DATABASE_URL": "database_url",
        "RAG_COLLECTION_NAME": "rag_collection_name",
        "RAG_DB_PATH": "rag_db_path",
        "EMBEDDING_MODEL": "embedding_model",
        "RAG_TOP_K": "rag_top_k",
        "MAX_FILE_SIZE_MB": "max_file_size_mb",
        "UPLOAD_DIR": "upload_dir",
    }
    for env_key, attr_name in field_alias_map.items():
        if env_key in os.environ and os.environ[env_key]:
            val = os.environ[env_key]
            field_type = type(getattr(s, attr_name))
            if field_type == bool:
                val = str(val).lower() in ("true", "1", "yes")
            elif field_type == int:
                val = int(val)
            elif field_type == float:
                val = float(val)
            setattr(s, attr_name, val)
        elif env_key in json_data and json_data[env_key] is not None:
            setattr(s, attr_name, json_data[env_key])

    conn_path = get_connections_file_path()
    if conn_path.exists():
        try:
            _last_connections_mtime = conn_path.stat().st_mtime
        except Exception:
            pass
    if ENV_FILE.exists():
        try:
            _last_env_mtime = ENV_FILE.stat().st_mtime
        except Exception:
            pass

    return s

# Global settings instance
settings = create_settings()

def reload_settings() -> Settings:
    """Reloads settings in-place so all existing imports update dynamically."""
    new_s = create_settings()
    for field_name in Settings.model_fields.keys():
        if hasattr(new_s, field_name):
            setattr(settings, field_name, getattr(new_s, field_name))
    
    # Invalidate and reset SAP client session & cache to pick up new credentials immediately
    try:
        from app.sap.client import sap_client
        sap_client.auth._session_cookies = {}
        sap_client.auth._is_authenticated = False
        sap_client._counts_cache = {}
        sap_client._counts_cache_time = 0.0
    except Exception as e:
        logger.debug(f"SAP client reset notification: {e}")

    logger.info("Application settings dynamically reloaded from connections configuration.")
    return settings

def check_and_auto_reload() -> bool:
    """
    Checks if active connections.json or .env was modified on disk since last load.
    If modified, reloads settings in-memory dynamically without restarting server.
    """
    global _last_connections_mtime, _last_env_mtime
    needs_reload = False
    conn_path = get_connections_file_path()
    if conn_path.exists():
        try:
            mtime = conn_path.stat().st_mtime
            if _last_connections_mtime > 0 and mtime > _last_connections_mtime:
                needs_reload = True
        except Exception:
            pass
    if ENV_FILE.exists():
        try:
            env_mtime = ENV_FILE.stat().st_mtime
            if _last_env_mtime > 0 and env_mtime > _last_env_mtime:
                needs_reload = True
        except Exception:
            pass
    if needs_reload:
        reload_settings()
        return True
    return False

AVAILABLE_SAP_COMPANIES = [
    {
        "company_db": "TEST_SHOES_10SEP26",
        "db_name": "TEST_SHOES_10SEP26",
        "company_name": "TEST_SHOES_10SEP26 (SAP Live)",
        "localization": "Global",
        "currency": "USD",
        "description": "Active configured SAP database instance."
    },
    {
        "company_db": "CINNTRA_DEMO_NEW",
        "db_name": "CINNTRA_DEMO_NEW",
        "company_name": "Cinntra Infotech Solutions (Demo)",
        "localization": "IN (India GST)",
        "currency": "INR",
        "description": "Primary SAP demo environment for automated master data workflows."
    },
    {
        "company_db": "SBODEMOUS",
        "db_name": "SBODEMOUS",
        "company_name": "SAP US Demonstration Inc.",
        "localization": "US (North America)",
        "currency": "USD",
        "description": "Standard US Chart of Accounts & US Tax Structure demonstration database."
    },
    {
        "company_db": "SBODEMOIN",
        "db_name": "SBODEMOIN",
        "company_name": "SAP India Demo Enterprise",
        "localization": "IN (India HSN/SAC)",
        "currency": "INR",
        "description": "Enterprise GST/TDS localization database for India operations."
    },
    {
        "company_db": "SAP_PROD_DB",
        "db_name": "SAP_PROD_DB",
        "company_name": "SAP Live Production",
        "localization": "Global",
        "currency": "INR",
        "description": "Enterprise live production database instance."
    },
    {
        "company_db": "SAP_TEST_DB",
        "db_name": "SAP_TEST_DB",
        "company_name": "SAP QA Sandbox",
        "localization": "Staging",
        "currency": "INR",
        "description": "Quality assurance and testing sandbox database."
    }
]

def get_available_companies() -> list[Dict[str, Any]]:
    """Returns list of configured companies with active status flag."""
    active_db = settings.sap_company_db or "TEST_SHOES_10SEP26"
    result = []
    found_active = False
    for comp in AVAILABLE_SAP_COMPANIES:
        is_active = comp["company_db"].upper() == active_db.upper()
        if is_active:
            found_active = True
        result.append({
            **comp,
            "company_db": comp["company_db"],
            "db_name": comp["company_db"],
            "is_active": is_active,
            "service_layer_url": settings.sap_service_layer_url
        })
    # If active_db is custom and not in default list, add it dynamically
    if not found_active and active_db:
        result.insert(0, {
            "company_db": active_db,
            "db_name": active_db,
            "company_name": f"{active_db} (Custom Active Database)",
            "localization": "Custom",
            "currency": "USD",
            "description": "Currently active custom SAP Business One database.",
            "is_active": True,
            "service_layer_url": settings.sap_service_layer_url
        })
    return result

def set_active_company_db(company_db: str) -> Tuple[bool, str]:
    """Dynamically sets the active SAP Company DB and updates configuration."""
    if not company_db or not str(company_db).strip():
        return False, "Company database name cannot be empty."
    cleaned_db = str(company_db).strip()
    return save_connections_dict({"sap": {"company_db": cleaned_db}})

def get_safe_connections_export() -> Dict[str, Any]:
    """Returns connections configuration with sensitive credentials safely masked."""
    check_and_auto_reload()
    return {
        "server": {
            "host": settings.host,
            "port": settings.port,
            "frontend_url": settings.frontend_url,
            "frontend_port": settings.frontend_port,
            "cors_origins": settings.parsed_cors_origins,
            "environment": settings.environment,
            "log_level": settings.log_level
        },
        "sap": {
            "service_layer_url": settings.sap_service_layer_url,
            "company_db": settings.sap_company_db,
            "username": settings.sap_username,
            "password_is_set": bool(settings.sap_password),
            "verify_ssl": settings.sap_verify_ssl,
            "timeout_seconds": settings.sap_timeout_seconds,
            "is_configured": settings.is_sap_configured,
            "available_companies": get_available_companies()
        },
        "ai": {
            "nvidia_base_url": settings.nvidia_base_url,
            "nvidia_model": settings.nvidia_model,
            "nvidia_temperature": settings.nvidia_temperature,
            "nvidia_max_tokens": settings.nvidia_max_tokens,
            "api_key_is_set": bool(settings.nvidia_api_key),
            "is_configured": settings.is_nvidia_configured
        },
        "database": {
            "database_url": settings.database_url,
            "rag_collection_name": settings.rag_collection_name,
            "rag_db_path": settings.rag_db_path,
            "embedding_model": settings.embedding_model,
            "rag_top_k": settings.rag_top_k,
            "max_file_size_mb": settings.max_file_size_mb,
            "upload_dir": settings.upload_dir
        },
        "active_config_file": str(get_connections_file_path())
    }

def save_connections_dict(updated: Dict[str, Any]) -> Tuple[bool, str]:
    """Updates connections.json file and reloads in-memory settings."""
    try:
        file_path = get_connections_file_path()
        current_data = {}
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    current_data = json.load(f)
            except Exception:
                current_data = {}

        if "server" in updated and isinstance(updated["server"], dict):
            srv_in = dict(updated["server"])
            if "cors_origins" in srv_in and isinstance(srv_in["cors_origins"], str):
                srv_in["cors_origins"] = [x.strip() for x in srv_in["cors_origins"].split(",") if x.strip()]
            current_data.setdefault("server", {}).update(srv_in)

        if "sap" in updated and isinstance(updated["sap"], dict):
            sap_in = dict(updated["sap"])
            if "password" in sap_in:
                # If password is empty or placeholder mask, keep existing password
                if not sap_in["password"] or sap_in["password"] == "••••••••":
                    sap_in.pop("password", None)
            current_data.setdefault("sap", {}).update(sap_in)

        if "ai" in updated and isinstance(updated["ai"], dict):
            ai_in = dict(updated["ai"])
            if "nvidia_api_key" in ai_in:
                if not ai_in["nvidia_api_key"] or ai_in["nvidia_api_key"].startswith("••••"):
                    ai_in.pop("nvidia_api_key", None)
            current_data.setdefault("ai", {}).update(ai_in)

        if "database" in updated and isinstance(updated["database"], dict):
            current_data.setdefault("database", {}).update(updated["database"])

        # Write to primary location
        with open(PRIMARY_CONNECTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(current_data, f, indent=2)

        # Always keep root location in sync
        try:
            with open(ROOT_CONNECTIONS_FILE, "w", encoding="utf-8") as f:
                json.dump(current_data, f, indent=2)
        except Exception:
            pass

        reload_settings()
        return True, "Connections configuration saved and applied successfully."
    except Exception as e:
        logger.error(f"Failed to save connections configuration: {e}")
        return False, str(e)

