"""PaperMate 2.0 — Streamlit + Groq public beta."""
import hashlib
import os
from pathlib import Path

import streamlit as st
from papermate.ai import AIService
from papermate.export import render_markdown, render_pdf
from papermate.limits import LimitReached
from papermate.pdf_utils import MAX_BYTES, MAX_PAGES, chunk_pages, extract_pages

st.set_page_config(page_title="PaperMate | AI 논문 번역", page_icon="📚", layout="wide")


def config(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, os.environ.get(name, default))
    except (FileNotFoundError, KeyError):
        value = os.environ.get(name, default)
    return str(value)


KEY = config("GROQ_API_KEY")
MODEL = config("GROQ_MODEL", "qwen/qwen3.8-27b")
try:
    BUDGET = max(0, min(10000, int(config("DAILY_API_CALL_BUDGET", "180"))))
except ValueError:
    BUDGET = 0

st.title("📚 PaperMate")
st.caption("영어 논문을 한국어로 번역하고 핵심을 쉽게 이해하는 무료 베타 서비스")

with st.sidebar:
    st.header("서비스 안내")
    st.write(f"PDF 최대 **{MAX_PAGES}페이지 / {MAX_BYTES // (1024*1024)}MB**")
    st.write("텍스트 선택이 가능한 PDF만 지원합니다. 스캔본 OCR·원본 레이아웃 재현은 미지원입니다.")
    st.write("무료 AI 처리 예산은 방문자 모두가 공유합니다. 동시에 많은 요청이 오면 한도에 도달할 수 있습니다.")
    st.info("업로드한 텍스트는 AI 처리를 위해 Groq 서버로 전송됩니다. 비공개 연구자료나 개인정보가 포함된 논문은 올리지 마세요.")
    st.caption("AI 번역에 오류가 있을 수 있습니다. 논문 인용·실험 수치는 원문과 대조하세요.")
    st.caption(f"현재 관리자 설정 모델: `{MODEL}`")

if not KEY or KEY == "paste_your_groq_api_key_here":
    st.error("관리자의 Groq API 키 설정이 필요합니다. README의 배포 가이드를 참고하세요.")
    st.stop()

uploaded = st.file_uploader("분석할 영어 논문 PDF 업로드", type=["pdf"], accept_multiple_files=False)
if not uploaded:
    st.info("PDF를 선택하면 논문 분석을 시작할 수 있습니다.")
    st.stop()

pdf_data = uploaded.getvalue()
if not pdf_data.startswith(b"%PDF-"):
    st.error("PDF 형식이 아닌 파일입니다.")
    st.stop()
try:
    pages = extract_pages(pdf_data)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

fingerprint = hashlib.sha256(pdf_data).hexdigest()
if st.session_state.get("pdf_hash") != fingerprint:
    st.session_state["pdf_hash"] = fingerprint
    st.session_state["translated"] = {}  # {chunk index: text}
    st.session_state["notes"] = {}       # {chunk index: text}
    st.session_state["guide"] = ""

chunks = chunk_pages(pages)
if not chunks:
    st.error("번역할 내용이 없습니다.")
    st.stop()
st.success(f"파일 확인: {len(pages)}페이지 · 번역 단위 {len(chunks)}개")
with st.expander("추출된 원문 미리보기"):
    st.text_area("첫 페이지", pages[0][:5000], height=200, disabled=True)

st.caption("베타에서는 전체 논문 번역을 지원하지만, 처리량 제한 때문에 긴 논문은 중간에 멈출 수 있습니다. 진행 내역은 현재 브라우저 세션에 남습니다.")
run = st.button("✨ 논문 번역·분석 시작 / 이어하기", type="primary", use_container_width=True)

if run:
    service = AIService(KEY, MODEL, BUDGET)
    total = len(chunks) * 2 + 1
    progress = st.progress(0.0, text="분석 준비 중...")
    failed = False
    for index, (page_number, text) in enumerate(chunks):
        try:
            if index not in st.session_state["translated"]:
                progress.progress((2 * index) / total, text=f"{page_number}페이지 번역 중 · {index+1}/{len(chunks)}")
                st.session_state["translated"][index] = service.translate(text, page_number)
            if index not in st.session_state["notes"]:
                progress.progress((2 * index + 1) / total, text=f"{page_number}페이지 핵심 메모 생성 중")
                st.session_state["notes"][index] = service.section_note(st.session_state["translated"][index], page_number)
        except (RuntimeError, LimitReached) as exc:
            st.warning(str(exc))
            failed = True
            break
    if not failed and not st.session_state["guide"]:
        try:
            progress.progress((total - 1) / total, text="전체 요약·해설·용어집 작성 중")
            # The page notes are concise; cap total input to model context.
            notes = "\n\n".join(
                f"[P{chunks[i][0]} / 조각 {i+1}] {st.session_state['notes'][i]}" for i in range(len(chunks))
            )
            st.session_state["guide"] = service.study_guide(notes[:42000])
        except (RuntimeError, LimitReached) as exc:
            st.warning(str(exc))
            failed = True
    if not failed:
        progress.progress(1.0, text="완료")
        st.success("번역 및 논문 분석을 완료했습니다.")

translated = st.session_state["translated"]
if translated:
    st.subheader("원문 ↔ 한국어 번역")
    page_choice = st.selectbox("페이지 선택", list(range(1, len(pages) + 1)), format_func=lambda p: f"{p}페이지")
    left, right = st.columns(2)
    with left:
        st.markdown("**영어 원문**")
        st.text_area("원문", pages[page_choice - 1], height=500, disabled=True, label_visibility="collapsed")
    with right:
        st.markdown("**한국어 번역**")
        translations_for_page = [translated[i] for i, (p, _) in enumerate(chunks) if p == page_choice and i in translated]
        st.text_area("번역", "\n\n".join(translations_for_page) if translations_for_page else "번역되지 않은 페이지입니다.", height=500, disabled=True, label_visibility="collapsed")
    st.caption(f"번역 완료 {len(translated)}/{len(chunks)}개 구간 · AI 번역은 검수가 필요합니다.")

if st.session_state["guide"]:
    st.subheader("🧠 연구 내용 요약 · 쉬운 설명 · 전문용어")
    st.markdown(st.session_state["guide"])

if translated:
    per_page = {}
    for i, (p, _) in enumerate(chunks):
        if i in translated:
            per_page.setdefault(p, []).append(translated[i])
    file_title = Path(uploaded.name).stem[:90]
    guide = st.session_state["guide"] or "(분석 미완료: 완료된 번역분만 저장됨)"
    markdown = render_markdown(file_title, per_page, guide)
    st.subheader("결과 다운로드")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("⬇️ Markdown 저장", markdown.encode("utf-8"), file_name="papermate_result.md", mime="text/markdown", use_container_width=True)
    with c2:
        try:
            pdf = render_pdf(file_title, per_page, guide)
            st.download_button("⬇️ 한국어 PDF 저장", pdf, file_name="papermate_korean.pdf", mime="application/pdf", use_container_width=True)
        except Exception:
            st.warning("PDF 생성에 문제가 발생했습니다. Markdown 결과를 내려받아 주세요.")

st.divider()
st.caption("PaperMate 2.0 Beta · 공개 서비스용 소규모 MVP · 사용 내용은 현재 세션에서만 보관됩니다.")
