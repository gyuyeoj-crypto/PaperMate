"""PaperMate: resilient text extraction from research PDFs."""
from io import BytesIO
import re
from pypdf import PdfReader

MAX_PAGES = 15
MAX_BYTES = 10 * 1024 * 1024


def normalize(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_pypdf(data: bytes) -> list[str]:
    reader = PdfReader(BytesIO(data), strict=False)
    if reader.is_encrypted:
        raise ValueError("암호화된 PDF는 지원하지 않습니다.")
    if not 1 <= len(reader.pages) <= MAX_PAGES:
        raise ValueError(f"1~{MAX_PAGES}페이지 PDF만 지원합니다. 현재 {len(reader.pages)}페이지입니다.")
    pages = []
    for page in reader.pages:
        try:
            content = page.extract_text(extraction_mode="layout") or ""
        except Exception:
            # The layout extractor is fragile on some scientific PDFs.
            try:
                content = page.extract_text() or ""
            except Exception:
                content = ""
        pages.append(normalize(content))
    return pages


def _extract_pymupdf(data: bytes) -> list[str]:
    import fitz
    with fitz.open(stream=data, filetype="pdf") as doc:
        if doc.needs_pass:
            raise ValueError("암호화된 PDF는 지원하지 않습니다.")
        if not 1 <= len(doc) <= MAX_PAGES:
            raise ValueError(f"1~{MAX_PAGES}페이지 PDF만 지원합니다. 현재 {len(doc)}페이지입니다.")
        return [normalize(page.get_text("text", sort=True)) for page in doc]


def extract_pages(data: bytes) -> list[str]:
    if not data:
        raise ValueError("PDF 파일이 비어 있습니다.")
    if len(data) > MAX_BYTES:
        raise ValueError("PDF 크기는 10MB 이하여야 합니다.")
    if not data.startswith(b"%PDF-"):
        raise ValueError("PDF 형식이 아닌 파일입니다.")

    errors = []
    try:
        pages = _extract_pypdf(data)
        if sum(map(len, pages)) >= 100:
            return pages
    except ValueError as exc:
        # A page-limit or encrypted-PDF error should not be masked.
        raise
    except Exception as exc:
        errors.append(f"pypdf: {type(exc).__name__}")

    try:
        pages = _extract_pymupdf(data)
        if sum(map(len, pages)) >= 100:
            return pages
    except ValueError:
        raise
    except Exception as exc:
        errors.append(f"PyMuPDF: {type(exc).__name__}")

    if errors:
        raise ValueError("PDF 텍스트 추출에 실패했습니다 (" + ", ".join(errors) + "). PDF를 다시 다운로드하거나 PDF로 다시 저장해 보세요.")
    raise ValueError("PDF에서 충분한 텍스트를 찾지 못했습니다. 스캔 PDF이거나 글자가 이미지로 저장된 경우 OCR이 필요합니다.")


def split_text(text: str, size: int = 1900) -> list[str]:
    if size < 100:
        raise ValueError("chunk size too small")
    text = text.strip()
    if not text:
        return []
    chunks = []
    while len(text) > size:
        window = text[:size + 1]
        choices = [window.rfind("\n\n", size // 2, size + 1), window.rfind(". ", size // 2, size + 1), window.rfind("\n", size // 2, size + 1), window.rfind(" ", size // 2, size + 1)]
        pos = next((i + (2 if window[i:i + 2] == '. ' else 0) for i in choices if i > 0), size)
        chunks.append(text[:pos].strip())
        text = text[pos:].strip()
    if text:
        chunks.append(text)
    return chunks


def chunk_pages(pages: list[str]) -> list[tuple[int, str]]:
    return [(i, chunk) for i, page in enumerate(pages, 1) for chunk in split_text(page)]
