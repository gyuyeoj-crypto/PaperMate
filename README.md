# PaperMate 2.0 — 무료 AI 논문 번역 공개 웹앱

Streamlit + Groq API를 이용한 공개 베타 MVP입니다. OpenAI API 사용하지 않습니다.
**무료 Groq tier는 한도가 있고, 한도 초과 시 요청이 실패합니다.** 이 코드는 무제한 무료 서비스를 보장하지 않습니다.

## 1. Windows에서 실행 (초보자)
1. Python 3.11 또는 3.12 설치: https://www.python.org/downloads/ (설치 시 PATH 추가)
2. ZIP 압축 해제
3. https://console.groq.com/keys 에서 Groq 계정 및 API 키 생성
4. `.streamlit/secrets.toml.example`을 같은 폴더의 `secrets.toml`로 **복사**하고, `GROQ_API_KEY` 값을 실제 키로 수정
5. `start_windows.bat` 더블클릭. 또는 명령 프롬프트에서:

```powershell
py -3 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

브라우저에서 `http://localhost:8501`에 접속하세요.

## 2. 누구나 접속 가능한 웹사이트로 배포 (Streamlit Community Cloud)
1. https://github.com 가입 → New repository → 새 저장소 생성
2. 이 폴더의 `app.py`, `papermate/`, `requirements.txt`, `.streamlit/config.toml` 등 프로젝트 파일을 업로드
3. **`secrets.toml`은 절대 GitHub에 업로드하지 마세요!** `.gitignore`에 제외됨
4. https://share.streamlit.io → Create app → GitHub 저장소와 브랜치 선택 → Main file path에 `app.py`
5. 배포 화면의 Advanced settings → Secrets에 다음 설정 입력:

```toml
GROQ_API_KEY = "gsk_실제_API_키"
GROQ_MODEL = "qwen/qwen3.8-27b"
DAILY_API_CALL_BUDGET = 180
```

6. Deploy! 완료 후 `https://....streamlit.app` 주소 공유.
7. Groq 계정에서 해당 모델의 **Free plan 모델 이용 가능 여부와 실제 요청 한도**를 확인하세요. 모델 ID는 변경될 수 있습니다. 모델 오류 시 https://console.groq.com/docs/models 목록에서 사용 가능한 모델로 변경하세요.

## 3. 주요 기능
- PDF 최대 10MB, 15페이지 (텍스트 PDF 전용; OCR 없음)
- 전체 PDF 페이지 분할 한국어 번역
- 각 번역 구간 메모를 조합하여 논문 요약, 쉬운 설명, 전문용어 정리
- 좌우 원문/번역 비교, 부분 완료 상태 이어하기(브라우저 세션 내)
- Markdown 및 한국어 PDF 내보내기 (PDF는 기본 CID 글꼴 사용; PDF 뷰어 호환성은 확인 필요)

## 4. 비용과 사용량
- Streamlit Community Cloud: 무료 배포 제공, 자원 사용 제한 있음
- Groq API: 계정의 무료 모델/요청 한도 내에서만 무료
- 번역 1개 청크당 번역 + 메모 AI 요청 2회, 마지막 통합 분석 요청 1회
- `DAILY_API_CALL_BUDGET=180`은 서버가 실행 중인 단일 인스턴스의 **최대 AI API 시도 예산**을 UTC 날짜 단위로 제한.
- 이 제한은 사용자별 한도가 아닙니다. 데이터베이스는 `/tmp`에 보관되어 서비스 재시작 시 초기화될 수 있으며, 다중 서버를 통합 제한하지 못합니다. Groq 계정 자체의 서버 측 제한을 추가 안전장치로 유지하세요.
- 무료 API에 서비스 수준의 과금/사용 차단이 자동 제공된다고 가정하지 마세요. 대시보드에서 플랜·사용량·결제 설정 확인 필요.

## 5. 개인정보와 저작권
업로드 문서 내용은 외부 Groq AI 서버로 전송됩니다. 비공개 연구자료, 개인정보, 기업 비밀을 업로드하지 마세요. 본 앱은 사용자의 PDF 파일을 디스크에 영구 저장하지 않으며, 번역은 브라우저 세션 내 메모리에 남을 수 있습니다. AI 제공자의 보관·학습 정책은 따로 확인하세요. 다른 사람의 논문 번역본을 허락 없이 공개 배포하지 마세요.

## 6. 기술적 제한
- 2단 레이아웃, 표, 수식, 참고문헌 추출 순서가 틀릴 수 있음. 스캔 PDF OCR 미지원.
- 논문의 모든 추출 텍스트를 번역하지만, 모든 수식/그림/표가 원형 그대로 복원되지는 않음.
- 요약은 **각 구간의 압축 메모**에 근거한 요약이며, 원문 전체를 직접 검증한 결과가 아님.
- 대형 논문은 Groq 무료 한도나 모델 최대 출력 토큰 제한으로 번역이 중간에 잘릴 수 있음. 반드시 원문과 대조하세요.
- PDF 기본 Korean CID font는 뷰어에 따라 표시에 차이가 날 수 있으며 원본 논문 레이아웃을 보존하지 않습니다.
- 모바일/다중 사용자 베타용 UI지만 운영 수준의 계정/레이트리밋/보안 감사/결제 시스템은 아직 없음.
- 상용 서비스 전 개인정보 처리방침, 이용약관, 모니터링, 분산형 사용량 제한 및 저작권/약관 검토 필요.

## 7. 테스트
```bash
python -m unittest discover -s tests -v
python -m compileall -q app.py papermate
```

## 문서 링크
- Groq 모델: https://console.groq.com/docs/models
- Groq 무료 한도: https://console.groq.com/docs/rate-limits
- Groq SDK: https://console.groq.com/docs/text-chat
- Streamlit 배포: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Streamlit Secrets: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
