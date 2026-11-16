"""
SAP Documentation Ingestion CLI.
Run: python -m app.rag.ingest
Loads documents/sap/, cleans text, chunks, embeds, and indexes into ChromaDB.
"""
import os
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings
from app.rag.chunker import chunk_excel_file, chunk_markdown_file
from app.rag.embeddings import embedding_provider

def ingest_documents():
    print("Loading documents...")
    base_docs_dir = Path(__file__).resolve().parent.parent.parent / "documents" / "sap"
    
    if not base_docs_dir.exists():
        print(f"Error: Directory not found at {base_docs_dir}")
        return 0

    all_files = list(base_docs_dir.glob("**/*.*"))
    supported_files = [f for f in all_files if f.suffix.lower() in [".md", ".txt", ".html", ".pdf", ".xlsx", ".csv"]]
    
    print(f"Found {len(supported_files)} knowledge documents.")
    print("Cleaning documents...")
    print("Chunking...")
    
    all_chunks = []
    for file_path in supported_files:
        if file_path.suffix.lower() in [".md", ".txt", ".html"]:
            file_chunks = chunk_markdown_file(file_path)
            all_chunks.extend(file_chunks)
        elif file_path.suffix.lower() in [".xlsx", ".csv"]:
            try:
                excel_chunks = chunk_excel_file(file_path)
                all_chunks.extend(excel_chunks)
            except Exception as e:
                print(f"Warning: Could not process spreadsheet {file_path}: {e}")
        # Note: PDF chunking could also use pdfplumber/fitz if PDFs placed in documents/sap/
        elif file_path.suffix.lower() == ".pdf":
            try:
                import fitz
                doc = fitz.open(str(file_path))
                pdf_text = ""
                for page in doc:
                    pdf_text += page.get_text() + "\n"
                temp_path = file_path.with_suffix(".temp.txt")
                temp_path.write_text(pdf_text, encoding="utf-8")
                pdf_chunks = chunk_markdown_file(temp_path)
                for c in pdf_chunks:
                    c["metadata"]["source"] = file_path.name
                temp_path.unlink()
                all_chunks.extend(pdf_chunks)
            except Exception as e:
                print(f"Warning: Could not extract PDF {file_path}: {e}")

    if not all_chunks:
        print("No document chunks created.")
        return 0

    print(f"Prepared {len(all_chunks)} semantic chunks.")
    print("Generating embeddings...")
    print("Creating Chroma collection...")
    
    # Initialize persistent Chroma client
    client = chromadb.PersistentClient(path=settings.rag_db_path)
    
    # Get or create collection with local ONNX embedding function
    collection = client.get_or_create_collection(
        name=settings.rag_collection_name,
        embedding_function=embedding_provider.get_embedding_function()
    )
    
    # Delete existing items to allow clean re-indexing
    existing_count = collection.count()
    if existing_count > 0:
        collection.delete(where={"source": {"$ne": ""}})

    ids = [c["id"] for c in all_chunks]
    documents = [c["text"] for c in all_chunks]
    metadatas = [c["metadata"] for c in all_chunks]

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )

    print(f"Ingested {len(all_chunks)} chunks.")
    print("SAP documents indexed successfully.")
    return len(all_chunks)

if __name__ == "__main__":
    ingest_documents()
