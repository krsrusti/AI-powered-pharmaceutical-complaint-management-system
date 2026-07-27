"""
Document text extraction for uploaded complaint documents.

Per assignment scope: "Production-grade OCR is not required... simple text
extraction is sufficient." This module deliberately keeps things lightweight:
  - PDF   -> pypdf text extraction (no layout/table reconstruction)
  - Email -> Python's built-in email parser (.eml files), plain-text body only
  - Image -> pytesseract OCR (Tesseract must be installed on the host machine)

Known limitation (worth stating in README): scanned/image-based PDFs with no
embedded text layer will return empty text via pypdf. A production system
would fall back to OCR-per-page in that case; out of scope here.
"""

import io
from email import policy
from email.parser import BytesParser
from typing import Optional

from pypdf import PdfReader
from PIL import Image
import pytesseract


class DocumentParsingError(Exception):
    """Raised when a document's text cannot be extracted."""


def extract_text(file_bytes: bytes, filename: str) -> str:
    """Dispatches to the right extractor based on file extension."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext == "pdf":
        return _extract_pdf(file_bytes)
    elif ext == "eml":
        return _extract_email(file_bytes)
    elif ext in ("png", "jpg", "jpeg", "webp", "bmp"):
        return _extract_image(file_bytes)
    elif ext in ("txt", "md"):
        return file_bytes.decode("utf-8", errors="ignore")
    else:
        raise DocumentParsingError(
            f"Unsupported file type: .{ext}. Supported: pdf, eml, png, jpg, jpeg, webp, bmp, txt"
        )


def _extract_pdf(file_bytes: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        text_parts = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(text_parts).strip()
        if not text:
            raise DocumentParsingError(
                "No text could be extracted from this PDF — it may be a scanned "
                "image with no embedded text layer. Try uploading a screenshot "
                "of the relevant page instead (image OCR is supported)."
            )
        return text
    except DocumentParsingError:
        raise
    except Exception as e:
        raise DocumentParsingError(f"Failed to parse PDF: {e}")


def _extract_email(file_bytes: bytes) -> str:
    try:
        msg = BytesParser(policy=policy.default).parsebytes(file_bytes)
        subject = msg.get("subject", "")
        sender = msg.get("from", "")

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_content()
                    break
        else:
            body = msg.get_content()

        return f"Subject: {subject}\nFrom: {sender}\n\n{body}".strip()
    except Exception as e:
        raise DocumentParsingError(f"Failed to parse email: {e}")


def _extract_image(file_bytes: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(file_bytes))
        text = pytesseract.image_to_string(image).strip()
        if not text:
            raise DocumentParsingError(
                "No text could be detected in this image via OCR. Try a "
                "clearer image or describe the complaint in the chat instead."
            )
        return text
    except DocumentParsingError:
        raise
    except Exception as e:
        raise DocumentParsingError(f"Failed to OCR image: {e}")