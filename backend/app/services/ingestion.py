# backend/app/services/ingestion.py
from __future__ import annotations
import os
import re
import json
import hashlib
from typing import Any
import pandas as pd
from pypdf import PdfReader
from app.core.config import settings
from app.services.skill_normalizer import normalize_skills
from app.core.qdrant import get_qdrant_client
from app.services.vectorstore import COLLECTION_NAME
from app.services.patterns import JUNK, SKILL_HEADING_PATTERN

try:
    import spacy
    _nlp = spacy.load("en_core_web_sm")
except Exception:
    _nlp = None


def get_file_hash(filepath: str) -> str:
    """Calculate SHA256 hash of file contents efficiently."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_existing_file_hashes() -> dict[str, str]:
    """Fetch existing filename -> file_hash mappings from Qdrant in one batch."""
    client = get_qdrant_client()
    existing = {}
    try:
        # Fetch all records (limit 10000 is safe for most local/dev setups)
        records, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=10000,
            with_payload=["filename", "file_hash"],
            with_vectors=False
        )
        for r in records:
            if r.payload and "filename" in r.payload:
                existing[r.payload["filename"]
                         ] = r.payload.get("file_hash", "")
    except Exception:
        pass  # Collection might not exist yet
    return existing


def read_document_text(filepath: str) -> str:
    extension = os.path.splitext(filepath)[1].lower()
    try:
        if extension == ".pdf":
            reader = PdfReader(filepath)
            pages = []
            for page in reader.pages:
                try:
                    pages.append(page.extract_text() or "")
                except Exception:
                    continue
            return "\n".join(pages).strip()
        if extension == ".docx":
            from docx import Document
            document = Document(filepath)
            return "\n".join(p.text for p in document.paragraphs).strip()
        with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
            return file.read().strip()
    except Exception as exc:
        print(f"Document read error for {filepath}: {exc}")
        return ""


def extract_with_llm_open(text: str) -> dict | None:
    try:
        from app.core.llm import get_fast_llm
        from langchain_core.prompts import ChatPromptTemplate
        llm = get_fast_llm(temperature=0)
        if not llm:
            return None

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Resume Parser. Extract structured data.
Return ONLY valid JSON: {{"skills": ["ALL technical skills, tools, frameworks, libraries - open vocab, keep original names like React.js, Next.js 14, Helm, ArgoCD, K8s, EKS"], "experience_years": int, "location": ["city names"], "domains": ["e.g. Frontend, GenAI, DevOps"], "education": ["BACHELORS","MASTERS","PHD"], "summary": "2 line summary"}}
Rules:
- skills = exhaustive list, no limit, no predefined list
- include every tool mentioned
- Do not normalize, keep as written"""),
            ("human", "{resume_text}")
        ])
        chain = prompt | llm
        res = chain.invoke({"resume_text": text[:6000]})
        content = getattr(res, "content", str(res))
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1:
            return None
        data = json.loads(content[start:end+1])
        return data
    except Exception as e:
        print(f"LLM extraction failed: {e}")
        return None


def extract_skills_open_fallback(text: str) -> list[str]:
    m = re.search(
        rf"{SKILL_HEADING_PATTERN}[\s:]*\n?(.*?)(?:\n\n|EXPERIENCE|EDUCATION|PROJECTS|CERTIFICATIONS|SUMMARY|$)",
        text,
        re.I | re.S
    )
    section = m.group(1) if m else text[:4000]
    # includes \x7f , bullet, pipe, comma, newline
    parts = re.split(r"[\x7f\n,|•●\-·/;]+", section)
    out = []
    for p in parts:
        p = re.sub(r"^\W+", "", p.strip())
        if 2 <= len(p) <= 35 and p.upper() not in JUNK and len(p.split()) <= 4:
            out.append(p)
    # dedup preserve order
    seen = set()
    uniq = []
    for s in out:
        low = s.lower()
        if low not in seen:
            seen.add(low)
            uniq.append(s)
    return uniq[:80]


def extract_experience(text: str) -> int:
    values: list[float] = []
    patterns = [
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience|exp)",
        r"(?:experience|exp)[:\s]+(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)",
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)",
    ]

    # Loop through each pattern in your single-line list
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                values.append(float(match))
            except ValueError:
                pass

    return int(max(values)) if values else 0


def extract_email(text: str) -> str | None:
    matches = re.findall(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    return matches[0].strip().lower() if matches else None


def extract_phone(text: str) -> str | None:
    matches = re.findall(r"\+?\d[\d\s().-]{8,}\d", text)
    if matches:
        return re.sub(r"\s+", " ", matches[0].strip())
    return None


def extract_location_open(text: str) -> list[str]:
    if not _nlp:
        return []
    doc = _nlp(text[:2500])
    locs = [ent.text.title()
            for ent in doc.ents if ent.label_ in ("GPE", "LOC")]
    return sorted(set(locs))[:5]


def process_file(filename: str, file_hash: str) -> dict[str, Any] | None:
    filepath = os.path.join(settings.RESUME_DIR, filename)
    if not os.path.isfile(filepath):
        return None
    try:
        text = read_document_text(filepath)
        if not text:
            print(f"No text extracted from {filename}")
            return None

        llm_data = extract_with_llm_open(text)
        if llm_data:
            raw_skills = llm_data.get("skills", [])
            experience = int(llm_data.get("experience_years", 0)
                             or extract_experience(text))
            location = llm_data.get(
                "location", []) or extract_location_open(text)
            domains = llm_data.get("domains", [])
            education = llm_data.get("education", [])
        else:
            raw_skills = extract_skills_open_fallback(text)
            experience = extract_experience(text)
            location = extract_location_open(text)
            domains = []
            education = []

        normalized = normalize_skills(raw_skills)

        return {
            "filename": filename,
            "file_hash": file_hash,  # <-- NEW: Store hash in payload
            "name": os.path.splitext(filename)[0],
            "email": extract_email(text),
            "phone": extract_phone(text),
            "skills_raw": raw_skills,
            "skills": normalized,
            "experience": experience,
            "location": location,
            "domains": domains,
            "education": education,
            "text": text[:10000],
        }
    except Exception as exc:
        print(f"Error processing {filename}: {exc}")
        return None


def ingest_all() -> pd.DataFrame:
    if not os.path.isdir(settings.RESUME_DIR):
        print(f"Resume directory does not exist: {settings.RESUME_DIR}")
        return pd.DataFrame()

    allowed_extensions = {".pdf", ".docx", ".txt", ".md"}
    files = sorted(
        f for f in os.listdir(settings.RESUME_DIR)
        if os.path.splitext(f)[1].lower() in allowed_extensions
    )
    print(f"Found {len(files)} resume files in directory.")

    # 1. Fetch existing hashes from Qdrant (single fast network call)
    existing_hashes = get_existing_file_hashes()
    print(f"Found {len(existing_hashes)} existing records in Qdrant.")

    profiles = []
    skipped_count = 0

    # 2. Check each file
    for filename in files:
        filepath = os.path.join(settings.RESUME_DIR, filename)
        current_hash = get_file_hash(filepath)

        # 3. Skip if file exists and hash is identical
        if existing_hashes.get(filename) == current_hash:
            skipped_count += 1
            continue

        # 4. Process new or modified files
        profile = process_file(filename, current_hash)
        if profile:
            profiles.append(profile)

    print(f"✅ Skipped {skipped_count} unchanged files.")
    print(f"🚀 Processing {len(profiles)} new/modified files...")

    if not profiles:
        return pd.DataFrame()

    df = pd.DataFrame(profiles)
    print(f"Successfully processed {len(df)} resumes.")
    return df
