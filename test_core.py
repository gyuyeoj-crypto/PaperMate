import unittest
from io import BytesIO
from reportlab.pdfgen import canvas
from papermate.pdf_utils import split_text, extract_pages, chunk_pages
from papermate.export import render_pdf, render_markdown

class CoreTests(unittest.TestCase):
    def test_split_preserves_words(self):
        content = "A short sentence. " * 350
        chunks = split_text(content)
        self.assertTrue(len(chunks) > 2)
        self.assertTrue(all(len(c) <= 1900 for c in chunks))

    def test_pdf_extraction(self):
        output = BytesIO()
        c = canvas.Canvas(output)
        c.drawString(30, 700, "PaperMate test document with enough text to be detected by parser. " * 2)
        c.save()
        pages = extract_pages(output.getvalue())
        self.assertEqual(len(pages), 1)
        self.assertIn("PaperMate", pages[0])
        self.assertTrue(chunk_pages(pages))

    def test_pdf_export(self):
        pdf = render_pdf("Test", {1: ["안녕하세요. 이 논문은 실험을 소개합니다."]}, "## 핵심 요약\n실험 성공")
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertIn("한국어", render_markdown("Test", {1: ["한국어"]}, "가이드"))

if __name__ == "__main__":
    unittest.main()
