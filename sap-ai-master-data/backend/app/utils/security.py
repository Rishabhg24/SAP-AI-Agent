"""
Security and validation utilities.
Includes PDF validation, MIME type checking, payload hashing, and path sanitization.
"""
import hashlib
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any, Tuple

PDF_MAGIC_BYTES = b"%PDF-"
EXCEL_ZIP_MAGIC_BYTES = b"PK\x03\x04"
EXCEL_OLE_MAGIC_BYTES = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"

def generate_uuid() -> str:
    """Generate a clean UUID string."""
    return str(uuid.uuid4())

def sanitize_filename(filename: str) -> str:
    """Strip dangerous characters and path traversal patterns from filename."""
    # Remove directory separators and null bytes
    clean = re.sub(r'[/\\:\x00]', '_', filename)
    # Strip non-alphanumeric chars except safe ones
    clean = re.sub(r'[^a-zA-Z0-9._-]', '_', clean)
    return clean[:200]

def validate_pdf_content(content: bytes, max_size_mb: int = 15) -> Tuple[bool, str]:
    """
    Validate PDF content:
    - Non-empty
    - Under size limit
    - Magic bytes '%PDF-' check
    """
    if not content or len(content) == 0:
        return False, "Uploaded file is empty."
    
    max_bytes = max_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        return False, f"File size exceeds maximum allowed limit of {max_size_mb} MB."
    
    if not content.startswith(PDF_MAGIC_BYTES):
        return False, "File is not a valid PDF document (missing %PDF header)."
    
    return True, "Valid PDF"

def validate_document_content(content: bytes, filename: str, max_size_mb: int = 15) -> Tuple[bool, str, str]:
    """
    Validate uploaded document content (PDF, XLSX, XLS, CSV):
    - Non-empty
    - Under size limit
    - Magic bytes / content integrity check
    Returns: (is_valid: bool, message: str, doc_type: str)
    """
    if not content or len(content) == 0:
        return False, "Uploaded file is empty.", ""

    max_bytes = max_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        return False, f"File size exceeds maximum allowed limit of {max_size_mb} MB.", ""

    fn_lower = filename.lower()
    if fn_lower.endswith(".pdf"):
        if not content.startswith(PDF_MAGIC_BYTES):
            return False, "File is not a valid PDF document (missing %PDF header).", ""
        return True, "Valid PDF document.", "pdf"

    elif fn_lower.endswith(".xlsx"):
        if not content.startswith(EXCEL_ZIP_MAGIC_BYTES):
            return False, "File is not a valid Excel (.xlsx) workbook.", ""
        return True, "Valid Excel workbook (.xlsx).", "excel"

    elif fn_lower.endswith(".xls"):
        if not content.startswith(EXCEL_OLE_MAGIC_BYTES) and not content.startswith(EXCEL_ZIP_MAGIC_BYTES):
            return False, "File is not a valid Excel (.xls) document.", ""
        return True, "Valid Excel document (.xls).", "excel"

    elif fn_lower.endswith(".csv"):
        try:
            content[:2048].decode("utf-8")
            return True, "Valid CSV spreadsheet.", "excel"
        except UnicodeDecodeError:
            try:
                content[:2048].decode("latin-1")
                return True, "Valid CSV spreadsheet.", "excel"
            except Exception:
                return False, "CSV file encoding is invalid and unreadable.", ""

    return False, "Unsupported file format. Please upload a PDF (.pdf) or Excel (.xlsx, .xls, .csv) document.", ""

def hash_payload(data: Any) -> str:
    """
    Generate deterministic SHA-256 hash of a payload dictionary or object.
    Used for tamper-evident audit logs.
    """
    if isinstance(data, dict) or isinstance(data, list):
        serialized = json.dumps(data, sort_keys=True, default=str)
    else:
        serialized = str(data)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
