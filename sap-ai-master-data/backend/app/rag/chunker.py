"""
Document chunking and text cleaning for SAP documentation.
Splits markdown, HTML, and text into semantic chunks with source citations.
"""
import re
from typing import Any, Dict, List
from pathlib import Path

def clean_document_text(text: str) -> str:
    """Clean redundant whitespace, control characters, and normalize linebreaks."""
    # Replace carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Normalize multiple newlines to max 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove trailing/leading spaces on lines
    lines = [line.strip() for line in text.split("\n")]
    cleaned = "\n".join(lines).strip()
    return cleaned

def chunk_markdown_file(
    file_path: Path,
    chunk_size: int = 1500,
    chunk_overlap: int = 200
) -> List[Dict[str, Any]]:
    """
    Chunk a markdown/text file by section headers or sliding window,
    preserving metadata: source, document_type, entity, section.
    """
    raw_text = file_path.read_text(encoding="utf-8")
    cleaned_text = clean_document_text(raw_text)
    
    # Infer metadata from directory and filename
    parent_dir = file_path.parent.name
    doc_name = file_path.name
    
    entity_map = {
        "item_master": "Item",
        "business_partner": "BusinessPartner",
        "warehouse": "Warehouse",
        "service_layer": "ServiceLayer",
        "sdk": "SDK",
        "company_rules": "CompanyRules"
    }
    entity = entity_map.get(parent_dir, "General")

    # Split by markdown headers (# or ##)
    sections = re.split(r"(?m)(?=^#{1,3}\s+)", cleaned_text)
    
    chunks = []
    chunk_idx = 0
    
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
            
        # Extract section title if present
        first_line = sec.split("\n")[0]
        section_title = first_line.lstrip("#").strip() if first_line.startswith("#") else "General"
        
        if len(sec) <= chunk_size:
            chunks.append({
                "id": f"{file_path.stem}_{chunk_idx}",
                "text": sec,
                "metadata": {
                    "source": doc_name,
                    "document_type": parent_dir.replace("_", " ").title(),
                    "entity": entity,
                    "section": section_title,
                    "file_path": str(file_path)
                }
            })
            chunk_idx += 1
        else:
            # Sub-split long section with sliding window
            start = 0
            while start < len(sec):
                end = min(start + chunk_size, len(sec))
                sub_text = sec[start:end]
                chunks.append({
                    "id": f"{file_path.stem}_{chunk_idx}",
                    "text": sub_text,
                    "metadata": {
                        "source": doc_name,
                        "document_type": parent_dir.replace("_", " ").title(),
                        "entity": entity,
                        "section": f"{section_title} (Part {chunk_idx + 1})",
                        "file_path": str(file_path)
                    }
                })
                chunk_idx += 1
                start += (chunk_size - chunk_overlap)
                
    return chunks

def chunk_excel_file(
    file_path: Path,
    chunk_size: int = 1500,
    chunk_overlap: int = 200
) -> List[Dict[str, Any]]:
    """
    Chunk an Excel or CSV file by row representations,
    preserving metadata: source, document_type, entity, section.
    """
    from app.services.extraction_service import load_spreadsheet_rows
    rows = load_spreadsheet_rows(str(file_path))
    if not rows:
        return []

    parent_dir = file_path.parent.name
    doc_name = file_path.name

    entity_map = {
        "item_master": "Item",
        "business_partner": "BusinessPartner",
        "warehouse": "Warehouse",
        "service_layer": "ServiceLayer",
        "sdk": "SDK",
        "company_rules": "CompanyRules"
    }
    entity = entity_map.get(parent_dir, "General")

    lines = []
    for r in rows:
        non_empty = [c for c in r if c]
        if non_empty:
            lines.append(" | ".join(non_empty))
    full_text = "\n".join(lines)
    cleaned_text = clean_document_text(full_text)

    chunks = []
    chunk_idx = 0
    start = 0
    while start < len(cleaned_text):
        end = min(start + chunk_size, len(cleaned_text))
        sub_text = cleaned_text[start:end]
        chunks.append({
            "id": f"{file_path.stem}_{chunk_idx}",
            "text": sub_text,
            "metadata": {
                "source": doc_name,
                "document_type": parent_dir.replace("_", " ").title(),
                "entity": entity,
                "section": f"Spreadsheet Data (Part {chunk_idx + 1})",
                "file_path": str(file_path)
            }
        })
        chunk_idx += 1
        if end >= len(cleaned_text):
            break
        start += (chunk_size - chunk_overlap)

    return chunks
