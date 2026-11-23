"""PDF text extraction with per-page offline Tesseract OCR fallback.

Requirements: pypdf, pymupdf, pillow, pytesseract, plus the Tesseract binary.
"""
import re

MAX_PAGES = 15
MAX_BYTES = 10 * 1024 * 1024
MIN_PAGE_CHARS = 55


def normalize(text: str) -> str:
    text = (text or "").replace("\x00", "")
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _ocr_page(page) -> str:
    """Render one PyMuPDF page and OCR it locally (nothing sent to AI here)."""
    import pytesseract
    import fitz
    from PIL import Image

    # ~180 dpi balances OCR accuracy against CPU/RAM on free hosting.
    pix = page.get_pixmap(matrix=fitz.Matrix(2.5, 2.5), colorspace=fitz.csRGB, alpha=False)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    try:
        return normalize(pytesseract.image_to_string(img, lang="eng", config="--psm 3", timeout=45))
    except (pytesseract.TesseractNotFoundError, pytesseract.TesseractError) as exc:
        raise ValueError("OCR 엔진을 실행할 수 없습니다. Streamlit Cloud의 packages.txt에 tesseract-ocr, tesseract-ocr-eng가 있는지 확인하세요.") from exc
    except RuntimeError as exc:
        raise ValueError("OCR 처리 시간이 초과되었습니다. 페이지 해상도나 이미지 크기를 줄여 다시 시도하세요.") from exc
    finally:
        img.close()


def extract_pages(data: bytes) -> list[str]:
    """Return normalized text for all PDF pages, OCRing only text-poor pages."""
    if not data:
        raise ValueError("PDF 파일이 비어 있습니다.")
    if len(data) > MAX_BYTES:
        raise ValueError("PDF 크기는 10MB 이하여야 합니다.")
    if not data.startswith(b"%PDF-"):
        raise ValueError("PDF 형식이 아닌 파일입니다.")

    import fitz
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise ValueError("PDF를 열 수 없습니다. 파일이 손상되었거나 지원하지 않는 형식일 수 있습니다.") from exc
    with doc:
        if doc.needs_pass:
            raise ValueError("암호화된 PDF는 지원하지 않습니다.")
        if not 1 <= len(doc) <= MAX_PAGES:
            raise ValueError(f"1~{MAX_PAGES}페이지 PDF만 지원합니다. 현재 {len(doc)}페이지입니다.")

        pages = []
        for i, page in enumerate(doc):
            text = normalize(page.get_text("text", sort=True))
            if len(text) < MIN_PAGE_CHARS:
                # PDF may contain scanned images or embedded fonts without usable Unicode.
                ocr_text = _ocr_page(page)
                if len(ocr_text) > len(text):
                    text = ocr_text
            pages.append(text)

    if sum(len(t) for t in pages) < 100:
        raise ValueError("OCR로도 충분한 글자를 추출하지 못했습니다. 이미지 해상도나 PDF 내용이 적절한지 확인하세요.")
    return pages


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
