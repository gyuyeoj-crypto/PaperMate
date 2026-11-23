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


def extract_pages(data: bytes) -> list[str]:
    if not data or len(data) > MAX_BYTES:
        raise ValueError("PDF 크기는 10MB 이하여야 합니다.")
    try:
        reader = PdfReader(BytesIO(data), strict=False)
        if reader.is_encrypted:
            raise ValueError("암호화된 PDF는 지원하지 않습니다.")
        if not 1 <= len(reader.pages) <= MAX_PAGES:
            raise ValueError(f"1~{MAX_PAGES}페이지 PDF만 지원합니다.")
        pages = []
        for page in reader.pages:
            pages.append(normalize(page.extract_text(extraction_mode="layout") or ""))
        if sum(len(p) for p in pages) < 100:
            raise ValueError("텍스트를 추출할 수 없습니다. 스캔 PDF는 현재 OCR을 지원하지 않습니다.")
        return pages
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("PDF 파싱에 실패했습니다. 유효한 텍스트 PDF인지 확인하세요.") from exc


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
