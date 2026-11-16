"""
Document and PDF Upload and Validation Service.
Validates magic bytes, file size, integrity, and manages storage with secure UUID naming
for both PDF documents and Excel/CSV spreadsheets.
"""
import io
import os
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile
import fitz  # PyMuPDF
import openpyxl
from app.config import settings
from app.utils.logging import logger
from app.utils.security import (
    generate_uuid,
    hash_payload,
    sanitize_filename,
    validate_document_content,
    validate_pdf_content,
)

class DocumentService:
    def __init__(self):
        up_dir = Path(settings.upload_dir)
        if not up_dir.is_absolute():
            backend_dir = Path(__file__).resolve().parent.parent.parent
            if (backend_dir / "uploads").exists():
                up_dir = backend_dir / "uploads"
            else:
                up_dir = (backend_dir / up_dir).resolve()
        self.upload_dir = up_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_and_validate_document(self, file: UploadFile) -> Tuple[bool, str, dict]:
        """
        Validate and save uploaded PDF or Excel document.
        Returns: (success: bool, message: str, file_info: dict)
        """
        filename = sanitize_filename(file.filename or "document.pdf")

        # Read content
        try:
            content = await file.read()
        except Exception as e:
            return False, f"Failed to read uploaded file: {str(e)}", {}

        # Validate content & format using security validator
        is_valid, err_msg, doc_type = validate_document_content(
            content, filename, max_size_mb=settings.max_file_size_mb
        )
        if not is_valid:
            return False, err_msg, {}

        page_count = 1
        fn_lower = filename.lower()

        # Format-specific integrity checks
        if doc_type == "pdf":
            try:
                doc = fitz.open(stream=content, filetype="pdf")
                page_count = len(doc)
                if page_count == 0:
                    doc.close()
                    return False, "PDF document contains no pages.", {}
                doc.close()
            except Exception as e:
                return False, f"Uploaded PDF is corrupted or unreadable: {str(e)}", {}

        elif fn_lower.endswith(".xlsx"):
            try:
                wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
                sheet_names = wb.sheetnames
                if not sheet_names:
                    wb.close()
                    return False, "Excel workbook contains no worksheets.", {}
                page_count = len(sheet_names)
                wb.close()
            except Exception as e:
                return False, f"Uploaded Excel file is corrupted or unreadable: {str(e)}", {}

        elif fn_lower.endswith(".csv"):
            try:
                try:
                    text = content.decode("utf-8")
                except UnicodeDecodeError:
                    text = content.decode("latin-1")
                lines = [l for l in text.splitlines() if l.strip()]
                if not lines:
                    return False, "Uploaded CSV file is empty.", {}
                page_count = 1
            except Exception as e:
                return False, f"Uploaded CSV file is corrupted: {str(e)}", {}

        # Save with unique UUID maintaining file extension
        ext = Path(filename).suffix.lower()
        if not ext:
            ext = ".pdf" if doc_type == "pdf" else ".xlsx"

        file_uuid = generate_uuid()
        saved_filename = f"{file_uuid}{ext}"
        saved_path = self.upload_dir / saved_filename

        try:
            with open(saved_path, "wb") as f:
                f.write(content)
        except Exception as e:
            return False, f"Failed to save document on server: {str(e)}", {}

        file_hash = hash_payload(content)
        logger.info(
            f"Saved valid {doc_type.upper()} {filename} as {saved_filename} "
            f"(Units: {page_count}, Hash: {file_hash[:12]}...)"
        )

        file_info = {
            "uuid": file_uuid,
            "original_filename": filename,
            "saved_filename": saved_filename,
            "saved_path": str(saved_path.resolve()),
            "file_hash": file_hash,
            "file_type": doc_type,
            "page_count": page_count,
            "size_bytes": len(content),
            "extension": ext
        }

        return True, f"{doc_type.upper()} uploaded and verified successfully.", file_info

    def extract_raw_text(self, file_path: str, max_chars: int = 12000) -> str:
        """
        Extract raw text/tabular string from PDF, Excel (.xlsx), or CSV files for LLM ingestion.
        """
        p = Path(file_path)
        if not p.exists():
            return ""
        
        ext = p.suffix.lower()
        extracted_lines = []

        try:
            if ext == ".pdf":
                doc = fitz.open(file_path)
                for page_idx in range(min(len(doc), 10)):
                    page = doc[page_idx]
                    text = page.get_text()
                    if text.strip():
                        extracted_lines.append(f"--- Page {page_idx + 1} ---\n{text}")
                doc.close()

            elif ext == ".xlsx":
                wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
                for sheetname in wb.sheetnames[:3]:
                    sheet = wb[sheetname]
                    extracted_lines.append(f"--- Sheet: {sheetname} ---")
                    for row in sheet.iter_rows(values_only=True):
                        row_vals = [str(c).strip() if c is not None else "" for c in row]
                        if any(row_vals):
                            extracted_lines.append(" | ".join(row_vals))
                wb.close()

            elif ext in [".csv", ".txt"]:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                except UnicodeDecodeError:
                    with open(file_path, "r", encoding="latin-1") as f:
                        lines = f.readlines()
                for line in lines[:100]:
                    if line.strip():
                        extracted_lines.append(line.strip())

        except Exception as e:
            logger.warning(f"Error extracting raw text from {file_path}: {e}")

        combined = "\n".join(extracted_lines)
        return combined[:max_chars]

PDFService = DocumentService
document_service = DocumentService()
pdf_service = document_service
