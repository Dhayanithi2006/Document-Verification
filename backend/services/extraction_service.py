# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Intelligent Document Processing (IDP) Service (backend/services/extraction_service.py)

import os
import re
import uuid
import logging
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone

from pypdf import PdfReader
import pdfplumber
from PIL import Image

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.core.config import settings
from backend.core.database import utc_now
from backend.models.document import Document, DocumentVersion
from backend.models.extraction import DocumentProcessingRun, ExtractedField, DocumentPage
from backend.models.user import User
from backend.services.audit_service import create_audit_event

logger = logging.getLogger("aicte-extraction")

# Environment configurations for PaddleOCR on Windows CPU with ONNXRuntime
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_enable_pir_api"] = "0"

PROCESSOR_VERSION = "idp-pipeline-v1.0.0"

_OCR_ENGINE_SINGLETON = None


def get_ocr_engine():
    """Lazily initializes and caches the PaddleOCR ONNXRuntime CPU inference engine."""
    global _OCR_ENGINE_SINGLETON
    if _OCR_ENGINE_SINGLETON is None:
        try:
            import torch  # Ensure torch DLLs load before Paddle to avoid Windows runtime conflict
            from paddleocr import PaddleOCR
            logger.info("Initializing PaddleOCR engine with ONNXRuntime...")
            _OCR_ENGINE_SINGLETON = PaddleOCR(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                lang="en",
                engine="onnxruntime"
            )
            logger.info("PaddleOCR engine initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR engine: {e}", exc_info=True)
            _OCR_ENGINE_SINGLETON = False
    return _OCR_ENGINE_SINGLETON if _OCR_ENGINE_SINGLETON is not False else None


# -------------------------------------------------------------------------
# Document-Type Field Extraction Definitions & Schemas
# -------------------------------------------------------------------------

DOCUMENT_FIELD_SCHEMAS: Dict[str, List[Dict[str, Any]]] = {
    "FIRE_SAFETY_NOC": [
        {"key": "valid_until_date", "label": "Fire NOC Expiry Date", "type": "DATE", "required": True},
        {"key": "issue_date", "label": "Fire NOC Issue Date", "type": "DATE", "required": False},
        {"key": "noc_number", "label": "Fire NOC Registration / Reference Number", "type": "STRING", "required": True},
        {"key": "issuing_fire_station", "label": "Issuing Fire Station / Authority", "type": "STRING", "required": False},
    ],
    "LAND_TITLE_DEED": [
        {"key": "contiguous_land_area_acres", "label": "Contiguous Land Area (Acres)", "type": "FLOAT", "required": True},
        {"key": "survey_numbers_list", "label": "Survey / Khasra Numbers", "type": "STRING", "required": True},
        {"key": "registration_date", "label": "Title Deed Registration Date", "type": "DATE", "required": False},
        {"key": "land_owner_name", "label": "Registered Owner / Trust Name", "type": "STRING", "required": False},
        {"key": "lease_duration_years", "label": "Registered Lease Duration (Years)", "type": "INTEGER", "required": False},
        {"key": "permissible_far", "label": "Permissible FSI / FAR", "type": "FLOAT", "required": False},
    ],
    "LAND_USE_CERTIFICATE": [
        {"key": "survey_numbers_list", "label": "Converted Survey / Khasra Numbers", "type": "STRING", "required": True},
        {"key": "issuing_authority", "label": "Land Use Issuing Authority", "type": "STRING", "required": True},
        {"key": "conversion_order_number", "label": "NA Conversion Order Number", "type": "STRING", "required": False},
        {"key": "order_date", "label": "Conversion Order Date", "type": "DATE", "required": False},
    ],
    "APPROVED_BUILDING_PLAN": [
        {"key": "sanctioned_builtup_area_sqm", "label": "Sanctioned Built-up Area (Sq.m)", "type": "FLOAT", "required": True},
        {"key": "approval_authority", "label": "Plan Sanctioning Authority", "type": "STRING", "required": True},
        {"key": "plan_approval_number", "label": "Building Plan Approval Number", "type": "STRING", "required": False},
        {"key": "approval_date", "label": "Plan Sanction Date", "type": "DATE", "required": False},
        {"key": "permissible_far", "label": "Sanctioned FSI / FAR", "type": "FLOAT", "required": False},
    ],
    "BUILDING_COMPLETION": [
        {"key": "completed_builtup_area_sqm", "label": "Completed Built-up Area (Sq.m)", "type": "FLOAT", "required": True},
        {"key": "certificate_issuing_authority", "label": "BCC Issuing Authority", "type": "STRING", "required": True},
        {"key": "certificate_number", "label": "BCC / Occupancy Certificate Number", "type": "STRING", "required": False},
        {"key": "completion_status", "label": "Completion Status", "type": "STRING", "required": True},
        {"key": "issue_date", "label": "BCC Issue Date", "type": "DATE", "required": False},
        {"key": "provisional_duration_years", "label": "Provisional Occupancy Duration (Years)", "type": "INTEGER", "required": False},
        {"key": "has_major_modifications", "label": "Major Modifications Reported", "type": "BOOLEAN", "required": False},
    ],
    "STRUCTURAL_STABILITY": [
        {"key": "engineer_registration_number", "label": "Structural Engineer Registration No.", "type": "STRING", "required": True},
        {"key": "engineer_name", "label": "Certified Structural Engineer Name", "type": "STRING", "required": False},
        {"key": "structural_soundness_certified", "label": "Structural Soundness Certification", "type": "BOOLEAN", "required": True},
        {"key": "certificate_date", "label": "Stability Certificate Date", "type": "DATE", "required": False},
        {"key": "has_major_modifications", "label": "Major Modifications Addressed", "type": "BOOLEAN", "required": False},
    ],
    "PREV_AICTE_APPROVAL": [
        {"key": "previous_eoa_reference", "label": "Previous AICTE EoA Reference Number", "type": "STRING", "required": True},
        {"key": "academic_year", "label": "Previous Approved Academic Year", "type": "STRING", "required": True},
        {"key": "approved_total_intake", "label": "Previously Approved Total Intake", "type": "INTEGER", "required": True},
        {"key": "issue_date", "label": "Previous EoA Issue Date", "type": "DATE", "required": False},
    ],
    "FACULTY_ROSTER": [
        {"key": "total_qualified_faculty_count", "label": "Total Qualified Faculty Count", "type": "INTEGER", "required": True},
        {"key": "professors_count", "label": "Professors Count", "type": "INTEGER", "required": False},
        {"key": "associate_professors_count", "label": "Associate Professors Count", "type": "INTEGER", "required": False},
        {"key": "assistant_professors_count", "label": "Assistant Professors Count", "type": "INTEGER", "required": False},
        {"key": "roster_certification_date", "label": "Faculty Roster Certification Date", "type": "DATE", "required": False},
    ]
}

MONTH_MAP = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9, "october": 10, "oct": 10,
    "november": 11, "nov": 11, "december": 12, "dec": 12
}


def parse_iso_date(text: str) -> Optional[str]:
    """Extracts and normalizes dates into canonical ISO-8601 YYYY-MM-DD string."""
    clean = text.strip()
    # Match YYYY-MM-DD
    m = re.search(r"\b(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\b", clean)
    if m:
        try:
            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Match DD/MM/YYYY or DD-MM-YYYY
    m = re.search(r"\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\b", clean)
    if m:
        try:
            day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
            dt = datetime(year, month, day)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Match DDth Month YYYY or Month DD, YYYY (e.g., 31st March 2026, April 12, 2025)
    pattern1 = r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s*,?\s*(\d{4})\b"
    m1 = re.search(pattern1, clean, re.IGNORECASE)
    if m1:
        d_str, m_str, y_str = m1.group(1), m1.group(2).lower(), m1.group(3)
        if m_str in MONTH_MAP:
            try:
                dt = datetime(int(y_str), MONTH_MAP[m_str], int(d_str))
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

    pattern2 = r"\b([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?\s*,?\s*(\d{4})\b"
    m2 = re.search(pattern2, clean, re.IGNORECASE)
    if m2:
        m_str, d_str, y_str = m2.group(1).lower(), m2.group(2), m2.group(3)
        if m_str in MONTH_MAP:
            try:
                dt = datetime(int(y_str), MONTH_MAP[m_str], int(d_str))
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

    return None


def parse_float_value(text: str) -> Optional[float]:
    """Safely parses positive numeric float values from text snippets."""
    m = re.search(r"(\d+(?:\.\d+)?)", text.replace(",", ""))
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def parse_int_value(text: str) -> Optional[int]:
    """Safely parses integer counts from text snippets."""
    m = re.search(r"\b(\d+)\b", text.replace(",", ""))
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    return None


# -------------------------------------------------------------------------
# Core IDP Engine Class
# -------------------------------------------------------------------------

class DocumentProcessingPipeline:
    def __init__(self, db: Session):
        self.db = db

    def resolve_physical_file(self, file_path_str: str) -> Path:
        """Safely locates physical file on disk relative to workspace."""
        path = Path(file_path_str)
        if path.exists():
            return path
        rel_path = Path(".") / path
        if rel_path.exists():
            return rel_path
        raise FileNotFoundError(f"Physical file not found in private storage: {file_path_str}")

    def render_page_to_image(self, file_path: Path, page_index: int) -> Image.Image:
        """Renders a PDF page to a PIL RGB Image using pypdfium2 at 200 DPI."""
        import pypdfium2
        pdf = pypdfium2.PdfDocument(str(file_path))
        try:
            if page_index < 0 or page_index >= len(pdf):
                raise ValueError(f"Page index {page_index} out of bounds (total pages: {len(pdf)})")
            page = pdf[page_index]
            # scale=1.5 corresponds to ~110 DPI, optimal for OCR token recognition on CPU
            bitmap = page.render(scale=1.5)
            return bitmap.to_pil().convert("RGB")
        finally:
            pdf.close()

    def process_document(
        self,
        document_id: str,
        version_number: Optional[int] = None,
        force_reprocess: bool = False,
        current_user: Optional[User] = None
    ) -> DocumentProcessingRun:
        """Executes the full Intelligent Document Processing (IDP) pipeline."""
        # 1. Fetch logical document
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        # 2. Fetch specific or latest version
        if version_number:
            version = self.db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id,
                DocumentVersion.version_number == version_number
            ).first()
        else:
            version = self.db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id
            ).order_by(DocumentVersion.version_number.desc()).first()

        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No uploaded file version exists for this document."
            )

        # 3. Idempotency Check
        existing_run = self.db.query(DocumentProcessingRun).filter(
            DocumentProcessingRun.document_version_id == version.id,
            DocumentProcessingRun.status.in_(["COMPLETED", "COMPLETED_WITH_WARNINGS"])
        ).order_by(DocumentProcessingRun.created_at.desc()).first()

        if existing_run and not force_reprocess:
            logger.info(f"Returning cached processing run {existing_run.id} for doc {doc.id} v{version.version_number}")
            return existing_run

        # 4. Resolve physical file path
        try:
            physical_file = self.resolve_physical_file(version.file_path)
        except FileNotFoundError as fnf:
            logger.error(str(fnf))
            # Create failed run
            failed_run = DocumentProcessingRun(
                document_id=doc.id,
                document_version_id=version.id,
                status="FAILED",
                processor_version=PROCESSOR_VERSION,
                error_message=f"Storage error: File missing from private disk repository."
            )
            self.db.add(failed_run)
            self.db.commit()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=failed_run.error_message)

        # 5. Initialize Processing Run Record
        run = DocumentProcessingRun(
            document_id=doc.id,
            document_version_id=version.id,
            status="PROCESSING",
            processor_version=PROCESSOR_VERSION,
            extraction_method="HYBRID",
            created_at=utc_now()
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        # Delete any previous pages or extracted fields for this version if forced reprocess
        if force_reprocess:
            self.db.query(ExtractedField).filter(ExtractedField.document_version_id == version.id).delete()
            self.db.query(DocumentPage).filter(DocumentPage.document_version_id == version.id).delete()
            self.db.commit()

        # 6. Execute Hybrid PDF Parsing & OCR
        try:
            # Check for encryption/password protection
            try:
                reader = PdfReader(str(physical_file))
                if reader.is_encrypted:
                    run.status = "FAILED"
                    run.error_message = "PDF is encrypted or password-protected. Unencrypted documents required."
                    run.completed_at = utc_now()
                    self.db.commit()
                    self.db.refresh(run)
                    return run
                page_count = len(reader.pages)
            except Exception as read_err:
                run.status = "FAILED"
                run.error_message = f"Malformed or unreadable PDF structure: {str(read_err)}"
                run.completed_at = utc_now()
                self.db.commit()
                self.db.refresh(run)
                return run

            if page_count == 0:
                run.status = "FAILED"
                run.error_message = "PDF document has 0 pages (empty structure)."
                run.completed_at = utc_now()
                self.db.commit()
                self.db.refresh(run)
                return run

            pages_data: List[Dict[str, Any]] = []
            pages_digital = 0
            pages_ocr = 0
            total_token_conf = 0.0
            total_token_count = 0

            # Open with pdfplumber for digital text layer
            with pdfplumber.open(str(physical_file)) as pdf:
                for idx, page in enumerate(pdf.pages):
                    page_num = idx + 1
                    raw_text = page.extract_text() or ""
                    clean_chars = "".join(c for c in raw_text if c.isprintable())
                    char_count = len(clean_chars.strip())
                    
                    # ROUTING DECISION:
                    # If character count > 40, treat as digital PDF text layer
                    if char_count > 40:
                        method = "DIGITAL_PDF_TEXT"
                        words = page.extract_words()
                        page_tokens = []
                        p_width = float(page.width or 612.0)
                        p_height = float(page.height or 792.0)
                        
                        for w in words:
                            w_text = w.get("text", "").strip()
                            if not w_text:
                                continue
                            box = {
                                "ymin": round(float(w["top"]) / p_height, 4),
                                "xmin": round(float(w["x0"]) / p_width, 4),
                                "ymax": round(float(w["bottom"]) / p_height, 4),
                                "xmax": round(float(w["x1"]) / p_width, 4),
                            }
                            page_tokens.append({
                                "text": w_text,
                                "box": box,
                                "confidence": 1.0
                            })
                            total_token_conf += 1.0
                            total_token_count += 1

                        pages_digital += 1
                        page_conf = 1.0
                        pages_data.append({
                            "page_number": page_num,
                            "method": method,
                            "text": raw_text,
                            "tokens": page_tokens,
                            "confidence": page_conf,
                            "char_count": len(raw_text),
                            "word_count": len(page_tokens)
                        })
                    else:
                        # Scanned / Image-based Page -> Route to PaddleOCR with ONNXRuntime
                        method = "OCR"
                        ocr_engine = get_ocr_engine()
                        if ocr_engine is None:
                            logger.warning(f"OCR engine requested for page {page_num} but engine unavailable. Recording limitations.")
                            method = "UNPROCESSED_SCANNED_PAGE"
                            page_conf = 0.0
                            pages_data.append({
                                "page_number": page_num,
                                "method": method,
                                "text": "[SCANNED PAGE: OCR engine unavailable]",
                                "tokens": [],
                                "confidence": 0.0,
                                "char_count": 0,
                                "word_count": 0
                            })
                            continue

                        # Render page image
                        img = self.render_page_to_image(physical_file, idx)
                        img_w, img_h = img.size

                        # Run real OCR (PaddleOCR requires numpy.ndarray)
                        import numpy as np
                        img_np = np.array(img)
                        ocr_results = list(ocr_engine.predict(img_np))
                        ocr_text_parts = []
                        page_tokens = []
                        page_conf_sum = 0.0
                        page_token_count = 0

                        if ocr_results:
                            res_item = ocr_results[0]
                            rec_texts = res_item.get("rec_texts", [])
                            rec_scores = res_item.get("rec_scores", [])
                            rec_boxes = res_item.get("rec_boxes", [])

                            for t_idx, (t_text, t_score) in enumerate(zip(rec_texts, rec_scores)):
                                if not t_text.strip():
                                    continue
                                ocr_text_parts.append(t_text)
                                t_conf = float(t_score)
                                page_conf_sum += t_conf
                                page_token_count += 1
                                total_token_conf += t_conf
                                total_token_count += 1

                                # Extract bounding box
                                box = None
                                if t_idx < len(rec_boxes):
                                    b = rec_boxes[t_idx]
                                    # rec_boxes can be [xmin, ymin, xmax, ymax]
                                    if len(b) >= 4:
                                        box = {
                                            "ymin": round(float(b[1]) / img_h, 4),
                                            "xmin": round(float(b[0]) / img_w, 4),
                                            "ymax": round(float(b[3]) / img_h, 4),
                                            "xmax": round(float(b[2]) / img_w, 4),
                                        }

                                page_tokens.append({
                                    "text": t_text,
                                    "box": box,
                                    "confidence": t_conf
                                })

                        full_ocr_text = "\n".join(ocr_text_parts)
                        page_conf = (page_conf_sum / page_token_count) if page_token_count > 0 else 0.0
                        pages_ocr += 1

                        pages_data.append({
                            "page_number": page_num,
                            "method": method,
                            "text": full_ocr_text,
                            "tokens": page_tokens,
                            "confidence": page_conf,
                            "char_count": len(full_ocr_text),
                            "word_count": len(page_tokens)
                        })

            # Update DocumentVersion scanned status
            version.is_scanned = (pages_ocr > 0)
            version.page_count = len(pages_data)

            # Persist DocumentPage rows
            for p in pages_data:
                db_page = DocumentPage(
                    document_version_id=version.id,
                    page_number=p["page_number"],
                    extraction_method=p["method"],
                    text_content=p["text"],
                    confidence=round(p["confidence"], 4),
                    char_count=p["char_count"],
                    word_count=p["word_count"]
                )
                self.db.add(db_page)

            # 7. Execute Structured Field Extraction according to Document Catalog
            extracted_fields_list = self.extract_fields_for_document_type(
                document_type=doc.document_type,
                pages_data=pages_data,
                doc_id=doc.id,
                version_id=version.id,
                run_id=run.id
            )

            for ef in extracted_fields_list:
                self.db.add(ef)

            # 8. Complete Processing Run
            overall_avg_conf = (total_token_conf / total_token_count) if total_token_count > 0 else 1.0
            
            run.pages_processed = len(pages_data)
            run.pages_digital = pages_digital
            run.pages_ocr = pages_ocr
            run.average_confidence = round(overall_avg_conf, 4)
            run.completed_at = utc_now()

            # Determine final status
            if pages_digital > 0 and pages_ocr > 0:
                run.extraction_method = "HYBRID"
            elif pages_ocr > 0:
                run.extraction_method = "OCR"
            else:
                run.extraction_method = "DIGITAL_PDF_TEXT"

            missing_reqs = any(
                f.raw_value in ["ABSENT", "UNREADABLE"] 
                for f in extracted_fields_list 
                if getattr(f, "_is_required", False)
            )

            if missing_reqs or overall_avg_conf < 0.60:
                run.status = "COMPLETED_WITH_WARNINGS"
            else:
                run.status = "COMPLETED"

            doc.status = "PROCESSED"
            self.db.commit()
            self.db.refresh(run)

            # Audit Event
            actor_id = current_user.id if current_user else "SYSTEM_WORKER"
            actor_role = current_user.role if current_user else "SYSTEM"
            create_audit_event(
                db=self.db,
                actor_user_id=actor_id,
                actor_role=actor_role,
                action="DOCUMENT_PROCESSED",
                entity_type="DOCUMENT",
                entity_id=doc.id,
                payload={
                    "document_id": doc.id,
                    "version_number": version.version_number,
                    "document_type": doc.document_type,
                    "pages_processed": run.pages_processed,
                    "pages_digital": run.pages_digital,
                    "pages_ocr": run.pages_ocr,
                    "extraction_method": run.extraction_method,
                    "average_confidence": run.average_confidence,
                    "status": run.status
                }
            )

            return run

        except Exception as proc_err:
            logger.error(f"Processing failed for document {document_id}: {proc_err}", exc_info=True)
            try:
                run.status = "FAILED"
                run.error_message = str(proc_err)
                run.completed_at = utc_now()
                self.db.add(run)
                self.db.commit()
                self.db.refresh(run)
            except Exception:
                pass
            return run

    process_document_version = process_document

    # ---------------------------------------------------------------------
    # Field Extraction by Document Type
    # ---------------------------------------------------------------------

    def extract_fields_for_document_type(
        self,
        document_type: str,
        pages_data: List[Dict[str, Any]],
        doc_id: str,
        version_id: str,
        run_id: str
    ) -> List[ExtractedField]:
        """Extracts structured regulatory parameters with spatial evidence anchoring."""
        schema = DOCUMENT_FIELD_SCHEMAS.get(document_type, [])
        extracted_entities: List[ExtractedField] = []

        # Combine text and tokens with page references
        full_doc_text = "\n".join(f"[PAGE {p['page_number']}]\n{p['text']}" for p in pages_data)

        for field_def in schema:
            f_key = field_def["key"]
            f_label = field_def["label"]
            f_type = field_def["type"]
            f_req = field_def.get("required", False)

            val_raw, val_norm, page_num, box, conf, method = self._find_field_value(
                field_key=f_key,
                field_type=f_type,
                document_type=document_type,
                pages_data=pages_data,
                full_text=full_doc_text
            )

            ef = ExtractedField(
                processing_run_id=run_id,
                document_id=doc_id,
                document_version_id=version_id,
                field_key=f_key,
                field_label=f_label,
                raw_value=val_raw or "ABSENT",
                normalized_value=val_norm or "ABSENT",
                data_type=f_type,
                page_number=page_num or 1,
                box_ymin=box.get("ymin") if box else None,
                box_xmin=box.get("xmin") if box else None,
                box_ymax=box.get("ymax") if box else None,
                box_xmax=box.get("xmax") if box else None,
                confidence=round(conf, 4),
                extraction_method=method
            )
            setattr(ef, "_is_required", f_req)
            extracted_entities.append(ef)

        return extracted_entities

    def _find_field_value(
        self,
        field_key: str,
        field_type: str,
        document_type: str,
        pages_data: List[Dict[str, Any]],
        full_text: str
    ) -> Tuple[Optional[str], Optional[str], int, Optional[Dict[str, float]], float, str]:
        """Inspects pages and tokens to detect the specific regulatory field with coordinates."""
        default_method = pages_data[0]["method"] if pages_data else "DIGITAL_PDF_TEXT"
        
        # 1. Fire Safety NOC Expiry Date
        if field_key == "valid_until_date" or field_key.endswith("expiry_date"):
            patterns = [
                r"(?:valid\s+(?:until|up\s*to|till)(?:\s+date)?|validity\s+period\s+up\s+to|expires\s+on|expiry\s+date|period\s+ending\s+on)\s*[:\-]?\s*([A-Za-z0-9\s,/.\-]+?)(?:\.|\n|$)",
                r"(?:date\s+of\s+expiry|validity\s+till)\s*[:\-]?\s*([A-Za-z0-9\s,/.\-]+?)(?:\.|\n|$)"
            ]
            for pat in patterns:
                for p in pages_data:
                    m = re.search(pat, p["text"], re.IGNORECASE)
                    if m:
                        raw = m.group(1).strip()
                        iso = parse_iso_date(raw)
                        if iso:
                            box = self._find_token_box(p["tokens"], m.group(1))
                            return raw, iso, p["page_number"], box, p["confidence"], p["method"]

        # 2. General Issue Date / Order Date / Registration Date
        if field_key in ["issue_date", "order_date", "registration_date", "approval_date", "certificate_date", "roster_certification_date"]:
            patterns = [
                r"(?:date\s+of\s+issue|issued\s+on|dated|issue\s+date|date|registration\s+date|sanction\s+date)\s*[:\-]?\s*([A-Za-z0-9\s,/.\-]+?)(?:\.|\n|$)",
                r"\bdated\s+the\s+([A-Za-z0-9\s,/.\-]+?)(?:\.|\n|$)"
            ]
            for pat in patterns:
                for p in pages_data:
                    m = re.search(pat, p["text"], re.IGNORECASE)
                    if m:
                        raw = m.group(1).strip()
                        iso = parse_iso_date(raw)
                        if iso:
                            box = self._find_token_box(p["tokens"], m.group(1))
                            return raw, iso, p["page_number"], box, p["confidence"], p["method"]

        # 3. Contiguous Land Area in Acres
        if field_key == "contiguous_land_area_acres":
            patterns = [
                r"(?:contiguous\s+land\s+area|total\s+land\s+area|land\s+area|extent\s+of\s+land|total\s+extent)\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:acres|acre|ac)",
                r"(\d+(?:\.\d+)?)\s*(?:acres|acre|ac)\b",
                r"(?:land\s+measuring|area)\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:acres|acre)"
            ]
            for pat in patterns:
                for p in pages_data:
                    m = re.search(pat, p["text"], re.IGNORECASE)
                    if m:
                        raw = m.group(0).strip()
                        val = parse_float_value(m.group(1))
                        if val is not None:
                            box = self._find_token_box(p["tokens"], m.group(1))
                            return raw, str(val), p["page_number"], box, p["confidence"], p["method"]

        # 4. Survey / Khasra Numbers
        if field_key == "survey_numbers_list":
            patterns = [
                r"(?:survey\s*(?:numbers|number|nos|no)|khasra\s*(?:numbers|number|nos|no)|sy\s*no)\s*[:\-.]?\s*([0-9a-zA-Z/\-, ]+)",
                r"(?:bearing\s+survey\s+numbers?)\s*[:\-.]?\s*([0-9a-zA-Z/\-, ]+)"
            ]
            for pat in patterns:
                for p in pages_data:
                    m = re.search(pat, p["text"], re.IGNORECASE)
                    if m:
                        raw = m.group(1).strip().rstrip(",.")
                        # Normalize survey numbers into clean comma-separated list
                        surveys = [s.strip() for s in re.split(r"[,;]|\band\b", raw) if s.strip()]
                        norm_str = ", ".join(surveys) if surveys else raw
                        box = self._find_token_box(p["tokens"], raw)
                        return raw, norm_str, p["page_number"], box, p["confidence"], p["method"]

        # 5. Sanctioned Built-up Area / Completed Built-up Area (Sq.m)
        if field_key in ["sanctioned_builtup_area_sqm", "completed_builtup_area_sqm"]:
            patterns = [
                r"(?:built[- ]?up\s+area|carpet\s+area|total\s+covered\s+area|instructional\s+area|completed\s+area|sanctioned\s+area)\s*[:\-]?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:sq\.?\s*m|sqm|square\s+meters?)",
                r"(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:sq\.?\s*m|sqm|square\s+meters?)"
            ]
            for pat in patterns:
                for p in pages_data:
                    m = re.search(pat, p["text"], re.IGNORECASE)
                    if m:
                        raw = m.group(0).strip()
                        val = parse_float_value(m.group(1))
                        if val is not None:
                            box = self._find_token_box(p["tokens"], m.group(1))
                            return raw, str(val), p["page_number"], box, p["confidence"], p["method"]

        # 6. Faculty Counts
        if field_key == "total_qualified_faculty_count":
            patterns = [
                r"(?:total\s+(?:qualified\s+)?(?:full[- ]?time\s+)?faculty(?:\s+cadre)?(?:\s+count)?|faculty\s+strength|total\s+teaching\s+staff|total\s+faculty)\s*[:\-]?\s*(\d+)",
                r"(?:total\s+staff\s+count)\s*[:\-]?\s*(\d+)",
                r"(?:qualified\s+faculty\s+count)\s*[:\-]?\s*(\d+)"
            ]
            for pat in patterns:
                for p in pages_data:
                    m = re.search(pat, p["text"], re.IGNORECASE)
                    if m:
                        raw = m.group(0).strip()
                        val = parse_int_value(m.group(1))
                        if val is not None:
                            box = self._find_token_box(p["tokens"], m.group(1))
                            return raw, str(val), p["page_number"], box, p["confidence"], p["method"]

        if field_key == "professors_count":
            patterns = [r"(?:professors?|cadre\s+professor)\s*[:\-]?\s*(\d+)"]
            for pat in patterns:
                for p in pages_data:
                    m = re.search(pat, p["text"], re.IGNORECASE)
                    if m:
                        raw = m.group(0).strip()
                        val = parse_int_value(m.group(1))
                        if val is not None:
                            box = self._find_token_box(p["tokens"], m.group(1))
                            return raw, str(val), p["page_number"], box, p["confidence"], p["method"]

        if field_key == "associate_professors_count":
            patterns = [r"(?:associate\s+professors?|assoc\.?\s+prof)\s*[:\-]?\s*(\d+)"]
            for pat in patterns:
                for p in pages_data:
                    m = re.search(pat, p["text"], re.IGNORECASE)
                    if m:
                        raw = m.group(0).strip()
                        val = parse_int_value(m.group(1))
                        if val is not None:
                            box = self._find_token_box(p["tokens"], m.group(1))
                            return raw, str(val), p["page_number"], box, p["confidence"], p["method"]

        if field_key == "assistant_professors_count":
            patterns = [r"(?:assistant\s+professors?|asst\.?\s+prof)\s*[:\-]?\s*(\d+)"]
            for pat in patterns:
                for p in pages_data:
                    m = re.search(pat, p["text"], re.IGNORECASE)
                    if m:
                        raw = m.group(0).strip()
                        val = parse_int_value(m.group(1))
                        if val is not None:
                            box = self._find_token_box(p["tokens"], m.group(1))
                            return raw, str(val), p["page_number"], box, p["confidence"], p["method"]

        # 7. AICTE Approved Total Intake
        if field_key == "approved_total_intake":
            patterns = [
                r"(?:approved\s+intake|total\s+approved\s+intake|sanctioned\s+intake|total\s+intake)\s*[:\-]?\s*(\d+)",
                r"(?:intake\s+capacity)\s*[:\-]?\s*(\d+)"
            ]
            for pat in patterns:
                for p in pages_data:
                    m = re.search(pat, p["text"], re.IGNORECASE)
                    if m:
                        raw = m.group(0).strip()
                        val = parse_int_value(m.group(1))
                        if val is not None:
                            box = self._find_token_box(p["tokens"], m.group(1))
                            return raw, str(val), p["page_number"], box, p["confidence"], p["method"]

        # 8. Structural Stability Affirmation
        if field_key == "structural_soundness_certified":
            patterns = [
                r"(structurally\s+sound|safe\s+and\s+sound|soundness\s+certified|satisfies\s+safety\s+norms|fit\s+for\s+occupation)",
                r"(earthquake\s+resistant|seismic\s+zone)"
            ]
            for pat in patterns:
                for p in pages_data:
                    m = re.search(pat, p["text"], re.IGNORECASE)
                    if m:
                        raw = m.group(0).strip()
                        box = self._find_token_box(p["tokens"], raw)
                        return raw, "true", p["page_number"], box, p["confidence"], p["method"]

        # 9. Reference / License / Registration Numbers
        if field_key in ["noc_number", "engineer_registration_number", "previous_eoa_reference", "certificate_number", "plan_approval_number", "conversion_order_number"]:
            patterns = [
                r"(?:ref(?:erence)?\s*(?:no|number)|reg(?:istration)?\s*(?:no|number)|file\s*no|noc\s*no|order\s*no|certificate\s*no|license\s*no)\s*[:\-]?\s*([A-Za-z0-9/\-._]+)",
                r"\b([A-Z]{2,}[/-][A-Za-z0-9/-]+)\b"
            ]
            for pat in patterns:
                for p in pages_data:
                    m = re.search(pat, p["text"], re.IGNORECASE)
                    if m:
                        raw = m.group(1).strip()
                        if len(raw) >= 4 and not raw.startswith("http"):
                            box = self._find_token_box(p["tokens"], raw)
                            return raw, raw, p["page_number"], box, p["confidence"], p["method"]

        # 10. Issuing Authorities / Names
        if field_key in ["issuing_authority", "certificate_issuing_authority", "approval_authority", "issuing_fire_station", "land_owner_name", "engineer_name", "completion_status", "academic_year"]:
            if field_key == "completion_status":
                for p in pages_data:
                    txt = p["text"]
                    if re.search(r"\bform\s*[- ]?d\b", txt, re.IGNORECASE):
                        return "Form D Completion", "FORM_D", p["page_number"], None, p["confidence"], p["method"]
                    elif re.search(r"completion\s+certificate", txt, re.IGNORECASE):
                        return "Completion Certificate", "COMPLETION_CERTIFICATE", p["page_number"], None, p["confidence"], p["method"]
                    elif re.search(r"full\s+completion|fully\s+completed|100%\s+complete", txt, re.IGNORECASE):
                        return "Fully Completed", "FULL_COMPLETION", p["page_number"], None, p["confidence"], p["method"]
                    elif re.search(r"provisional\s+(?:occupancy|completion)", txt, re.IGNORECASE):
                        return "Provisional Occupancy Certificate", "PROVISIONAL_OCCUPANCY", p["page_number"], None, p["confidence"], p["method"]
                    elif re.search(r"occupancy\s+certificate|fit\s+for\s+occupation|occupancy\s+permitted", txt, re.IGNORECASE):
                        return "Occupancy Certificate", "OCCUPANCY_CERTIFICATE", p["page_number"], None, p["confidence"], p["method"]
                    elif re.search(r"building\s+license|building\s+permit", txt, re.IGNORECASE):
                        return "Building License", "BUILDING_LICENSE", p["page_number"], None, p["confidence"], p["method"]
                    elif re.search(r"pwd\s+structural\s+clearance|structural\s+clearance\s+certificate", txt, re.IGNORECASE):
                        return "PWD Structural Clearance", "PWD_STRUCTURAL_CLEARANCE", p["page_number"], None, p["confidence"], p["method"]
                    elif re.search(r"phase\s+completion|sanctioned\s+phase|partial", txt, re.IGNORECASE):
                        return "Phase Completed", "SANCTIONED_PHASE_COMPLETE", p["page_number"], None, p["confidence"], p["method"]

            if field_key == "academic_year":
                m = re.search(r"\b(202\d[-/ ]202\d|202\d[-/ ]\d{2})\b", full_text)
                if m:
                    return m.group(1), m.group(1).replace(" ", "-").replace("/", "-"), 1, None, 1.0, default_method

            # Generic authority matching
            for p in pages_data:
                # Check explicit prefix first
                m = re.search(r"(?:issued\s+by|competent\s+authority|sanctioning\s+authority|issuing\s+authority)\s*[:\-]?\s*([A-Za-z0-9\s,.\-&()]+?)(?:\.|\n|$)", p["text"], re.IGNORECASE)
                if m:
                    raw = m.group(1).strip()
                    if len(raw) > 3:
                        return raw, raw, p["page_number"], None, p["confidence"], p["method"]
                # Detect well-known authority names in document header
                auth_m = re.search(r"\b(Bruhat Bengaluru Mahanagara Palike|BBMP|Municipal Corporation|Town Planning Department|Urban Development Authority|City Corporation|Gram Panchayat|Public Works Department|PWD)\b", p["text"], re.IGNORECASE)
                if auth_m:
                    return auth_m.group(1).strip(), auth_m.group(1).strip(), p["page_number"], None, p["confidence"], p["method"]

        # 11. Lease Duration in Years
        if field_key in ["lease_duration_years", "lease_period_years"]:
            patterns = [
                r"(?:lease\s+(?:period|duration|term)|period\s+of\s+lease)\s*[:\-]?\s*(\d+)\s*(?:years|yrs)",
                r"(?:for\s+a\s+period\s+of)\s*(\d+)\s*(?:years|yrs)\s+lease",
                r"(\d+)\s*(?:years|yrs)\s+registered\s+lease"
            ]
            for pat in patterns:
                for p in pages_data:
                    m = re.search(pat, p["text"], re.IGNORECASE)
                    if m:
                        raw = m.group(0).strip()
                        val = parse_int_value(m.group(1))
                        if val is not None:
                            box = self._find_token_box(p["tokens"], m.group(1))
                            return raw, str(val), p["page_number"], box, p["confidence"], p["method"]

        # 12. Permissible FSI / FAR
        if field_key in ["permissible_far", "far", "fsi"]:
            patterns = [
                r"(?:sanctioned\s+)?(?:permissible\s+)?(?:fsi\s*[/\\-]\s*far|far\s*[/\\-]\s*fsi|fsi|far|floor\s+area\s+ratio|floor\s+space\s+index)\s*[:\-]?\s*(\d+(?:\.\d+)?)",
                r"\b(?:fsi\s*[/\\-]\s*far|far\s*[/\\-]\s*fsi|fsi|far)\s*[:\-]?\s*(\d+(?:\.\d+)?)\b"
            ]
            for pat in patterns:
                for p in pages_data:
                    m = re.search(pat, p["text"], re.IGNORECASE)
                    if m:
                        raw = m.group(0).strip()
                        val = parse_float_value(m.group(1))
                        if val is not None:
                            box = self._find_token_box(p["tokens"], m.group(1))
                            return raw, str(val), p["page_number"], box, p["confidence"], p["method"]

        # 13. Provisional Occupancy Duration in Years
        if field_key in ["provisional_duration_years"]:
            patterns = [
                r"provisional\s+(?:validity|period|duration)\s*[:\-]?\s*(\d+)\s*(?:academic\s+years?|years?|yrs)",
                r"valid\s+provisionally\s+for\s*(\d+)\s*(?:academic\s+years?|years?|yrs)",
                r"provisional\s+occupancy\s+year\s*[:\-]?\s*(\d+)"
            ]
            for pat in patterns:
                for p in pages_data:
                    m = re.search(pat, p["text"], re.IGNORECASE)
                    if m:
                        raw = m.group(0).strip()
                        val = parse_int_value(m.group(1))
                        if val is not None:
                            box = self._find_token_box(p["tokens"], m.group(1))
                            return raw, str(val), p["page_number"], box, p["confidence"], p["method"]

        # 14. Major Structural Modifications
        if field_key in ["has_major_modifications"]:
            patterns = [
                r"(major\s+(?:structural\s+)?(?:modification|alteration|renovation|addition|vertical\s+expansion))",
                r"(structural\s+retrofit|additional\s+floors?\s+constructed)"
            ]
            for pat in patterns:
                for p in pages_data:
                    m = re.search(pat, p["text"], re.IGNORECASE)
                    if m:
                        raw = m.group(0).strip()
                        box = self._find_token_box(p["tokens"], raw)
                        return raw, "true", p["page_number"], box, p["confidence"], p["method"]

        # Field Not Found
        return None, None, 1, None, 0.0, default_method

    def _find_token_box(self, tokens: List[Dict[str, Any]], target_subtext: str) -> Optional[Dict[str, float]]:
        """Matches a target text subtext to spatial token bounding boxes."""
        target_words = [w.lower() for w in re.split(r"\s+", target_subtext.strip()) if w]
        if not target_words or not tokens:
            return None

        matched_boxes = []
        for t in tokens:
            t_clean = t["text"].lower()
            if any(tw in t_clean for tw in target_words):
                if t.get("box"):
                    matched_boxes.append(t["box"])

        if not matched_boxes:
            return None

        # Calculate bounding envelope [ymin, xmin, ymax, xmax]
        ymin = min(b["ymin"] for b in matched_boxes)
        xmin = min(b["xmin"] for b in matched_boxes)
        ymax = max(b["ymax"] for b in matched_boxes)
        xmax = max(b["xmax"] for b in matched_boxes)

        return {
            "ymin": round(ymin, 4),
            "xmin": round(xmin, 4),
            "ymax": round(ymax, 4),
            "xmax": round(xmax, 4),
        }
