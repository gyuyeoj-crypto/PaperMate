"""Unicode PDF using PDF standard Korean CID font (viewer support varies)."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))


def render_pdf(title: str, translations: dict[int, list[str]], guide: str) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=43, rightMargin=43, topMargin=44, bottomMargin=45,
                            title="PaperMate 한국어 학습자료")
    body = ParagraphStyle("body_ko", fontName="HYSMyeongJo-Medium", fontSize=9.2, leading=15,
                          spaceAfter=6, alignment=TA_LEFT, wordWrap="CJK")
    heading = ParagraphStyle("head_ko", parent=body, fontSize=15, leading=23, spaceAfter=12, textColor=colors.HexColor("#173E82"))
    sub = ParagraphStyle("sub_ko", parent=body, fontSize=12, leading=18, spaceBefore=12, spaceAfter=8)
    story = [Paragraph(escape(title[:150]), heading), Paragraph("PaperMate AI 번역본 — 원문과 반드시 대조하세요.", body), Spacer(1, 10)]
    for page, chunks in sorted(translations.items()):
        story.append(Paragraph(f"{page}페이지 번역", sub))
        for chunk in chunks:
            for paragraph in chunk.split("\n"):
                paragraph = paragraph.strip()
                if paragraph:
                    story.append(Paragraph(escape(paragraph), body))
    story += [PageBreak(), Paragraph("AI 논문 학습 가이드", heading)]
    for line in guide.splitlines():
        clean = line.strip()
        if not clean:
            story.append(Spacer(1, 6))
        elif clean.startswith("##"):
            story.append(Paragraph(escape(clean.lstrip("# ")), sub))
        else:
            story.append(Paragraph(escape(clean), body))
    doc.build(story)
    return buf.getvalue()


def render_markdown(title: str, translations: dict[int, list[str]], guide: str) -> str:
    out = [f"# {title}", "\n> PaperMate AI 번역본입니다. 중요한 주장·수식·수치는 원문과 대조하세요.\n"]
    for page, chunks in sorted(translations.items()):
        out.extend([f"\n## {page}페이지 번역\n", "\n\n".join(chunks)])
    out.extend(["\n# 논문 학습 가이드\n", guide])
    return "\n".join(out)
