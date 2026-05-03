# `.env` 통합 + prefix 컨벤션

repo 안에 흩어져있던 **28개의 `.env`** 를 root 한 곳으로 모으고, 변수명에 모듈 prefix 컨벤션 도입.

## 배경 / 의도

자동 발견된 `.env` 위치 28개:
```
src/rag_chatbot/0209/.env, .../indexing/.env, .../openaitest_0206/.env
src/rag_chatbot/cosmetic_rag_chat/.env, .../indexing/.env, .../openaitest_0206/.env
src/amazon_review_crawler/.env
data/project5/model/.env, .../graphrag_test_*/.env, .../graphragtest/.env
data/project5/final/3-beaty(3조) 코드 최종 제출본/Crawling/Amazon_Crawling/.env
data/project5/gdrive/2.데이터/Amazon_Crawling/.env
... (총 28개)
```
- 같은 변수가 여러 파일에 다른 값으로 박힘 — **어느 게 진짜인지 모름**
- 일부는 placeholder, 일부는 실제 시크릿
- 일부 파일에 **OpenAI 실제 키** + **개인 휴대폰/DB password** 노출

## 시도된 처리

### 1단계 — 위험도 분류 (28개 파일 일괄 검사)
| 카테고리 | 개수 | 처리 |
|---------|-----:|------|
| 더미 값 (`12345`, `ollama`, `your_api-key`, 빈 문자열) | 21 | 안전 |
| **실제 OpenAI API 키** (`sk-proj-...`) | 6 | 즉시 revoke 필요 |
| **개인 휴대폰 + 비밀번호 + DB password** | 1 | 즉시 정리 필요 |

### 2단계 — 통합 + 표준 prefix
모든 변수를 root `.env` 로 통합 + 모듈 prefix:

| Prefix | 용도 | 예시 |
|--------|------|------|
| `LLM_*` | 메인 LLM 설정 | `LLM_API_KEY`, `LLM_MODEL`, `LLM_PROVIDER`, `LLM_SERVICE_TYPE` |
| `EMBED_*` | 임베딩 모델 | `EMBED_API_KEY`, `EMBED_API_BASE`, `EMBED_MODEL` |
| `GRAPHRAG_*` | GraphRAG 인덱싱/쿼리 | `GRAPHRAG_API_KEY`, `GRAPHRAG_ROOT_DIR`, `GRAPHRAG_INPUT_DIR` |
| `API_*` | RAG API 서버 | `API_URL`, `API_PORT` |
| `CRAWLER_*` | Amazon 크롤러 + DB | `CRAWLER_ID`, `CRAWLER_DB_HOST`, `CRAWLER_DB_REPLICA_URL` |
| `SLACK_*` | Slack 알림 | `SLACK_WEBHOOK_URL` |
| `TIKTOK_*` | TikTok 크롤러 | `TIKTOK_EMAIL`, `TIKTOK_PASSWORD` |

### 3단계 — `.env.example` 추가
prefix 컨벤션 + placeholder 값으로 작성. git 에 커밋 → clone 한 사람이 복사해서 사용.

### 4단계 — 28개 옛 `.env` 삭제 + 코드의 변수명 일괄 마이그레이션
- 옛 `ID` / `PW` / `DB_*` → `CRAWLER_ID` / `CRAWLER_PW` / `CRAWLER_DB_*`
- 옛 `slack_key_url` (소문자!) → `SLACK_WEBHOOK_URL`
- 코드에서 `os.getenv("...")` 호출부 같이 변경
- `dotenv.load_dotenv()` → `load_dotenv(find_dotenv())` 로 — `find_dotenv()` 가 위로 올라가며 `.env` 자동 검색 (서브폴더에서도 root 의 .env 사용 가능)

### 5단계 — git history 검증
- 노출된 OpenAI 키 / 개인 정보가 git history 에 있는지 검사 (`git log --all -S '<value>' --oneline`)
- **결과: 0건** — `.gitignore` 가 `.env` 패턴을 처음부터 잡고 있어 commit 된 적 없음
- 단, 일부 데이터 파일 (`Amazon Crawler` 안 .env 같은) 은 .gitignore 우회 가능성 있어 별도 검증

## canonical 위치

```
.env                  (gitignored, 사용자 로컬 — 실제 값)
.env.example          (tracked, prefix 컨벤션 + placeholder)
.gitignore            (`.env*`, `*.env` 패턴 + `notion_page/` 등)
```

`src/util/slack.py` 같은 모듈은 `load_dotenv(find_dotenv())` 로 root .env 자동 발견.

## 학습 포인트

1. **`.gitignore` 가 첫 commit 부터 있어야**: 시크릿이 한 번이라도 commit 되면 history rewrite 필요. `.env` 패턴은 처음부터 들어있어야 안전.
2. **prefix 컨벤션의 효과**: 변수 이름만 봐도 어느 모듈에서 쓰는지 알 수 있음. typo/충돌 위험도 줄임.
3. **`find_dotenv()` 의 가치**: 서브 디렉터리에서 실행되는 스크립트도 root `.env` 자동 발견. `os.chdir()` 같은 잡일 없이 자연스럽게 동작.
4. **`.env.example` 은 placeholder + 설명**: 시크릿이 아니라 구조를 공유. clone 한 사람이 `cp .env.example .env` 로 시작 가능.
5. **위험도 검사는 grep 으로 빠르게**: `grep -E 'sk-[a-zA-Z0-9_-]{30,}'` 같은 패턴으로 28개 파일을 30초 안에 분류 가능.

## 관련 commits

- `7b169c3` — refactor: consolidate util/graphRAG, scrub lancedb tracking, prefix env vars
- (후속) `0af6cd3` — TikTok crawler: hardcoded credentials → TIKTOK_EMAIL/PASSWORD
- (후속) `43e21f5` — Amazon crawler: ID/PW/DB_* → CRAWLER_*