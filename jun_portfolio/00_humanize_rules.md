# im-not-ai 도구 룰 — 포트폴리오 작성 시 AI 톤 제거

본 프로젝트의 포트폴리오 (`01_만능_프로젝트정리페이지`, `03_데이터분석_트랙_v2`, `04_면접_예상답변`) 작성·수정 시 적용하는 AI 톤 제거 룰. github.com/epoko77-ai/im-not-ai 의 4 원칙 + 10 카테고리 기반.

## 왜 필요한가

AI 가 작성한 portfolio 초안이 사용자 직접 작성한 reference (양액펌프 portfolio) 대비 영어 jargon, emoji, bold, 정형 표현이 과도해서 *AI 가 만든 글* 처럼 보이는 문제 해결. 사용자 직접 톤과 일치시키기 위함.

## 4 원칙

1. **Meaning Preservation**: 정량 데이터·고유명사·claims 그대로 보존 (4.76, 5.10, 8.43, 1,540, 3.25배 등 변경 X)
2. **Evidence-Based**: 검출된 패턴만 수정 (전면 재작성보다 surgical edit)
3. **Genre Consistency**: 원본 스타일 유지 (포트폴리오 → 포트폴리오)
4. **Anti-Over-Editing**: 30% 변경 시 경고, 50% 시 중단

## 10 카테고리

| ID | 카테고리 | 검출 패턴 | 변경 방향 |
|---|---|---|---|
| A | 번역체 | "~를 통해" / "~에 대해" | 자연 한국어 |
| B | 영어 인용 과다 | stability, robustness, mechanism, closed loop, PSM, HC3 | 한국어 풀어쓰기 (영어 괄호 한 번만) |
| C | 기계적 AI 구조 | bullet/emoji 남용 | 산문 위주, 표는 비교 정보만 |
| D | AI 특유 정형구 | "결론적으로", "~이라고 봅니다" 반복 | 다양화 (한 글 2회 이하) |
| E | 리듬 단조 | "~한 경험이었습니다" 종결 반복 | 종결 다양화 |
| F | 수식 잉여 | "매우/정말/직접/정량으로" | 줄이기 |
| G | 헷지 과다 | "~할 수 있을 것으로 보인다" 다층 | 단정 또는 한 번만 |
| H | 접속어 과다 | "또한/따라서/즉" 반복 | "또"/"그런데" 자연 사용 |
| I | 명사화 표현 | "것이다/점/필요가 있다" 정형 | 동사화 |
| J | 시각 포맷 남용 | bold/emoji/표 과다 | bold 핵심만, emoji 0 (portfolio), 표는 비교만 |

## Severity

- **S1**: 항상 제거 (emoji 남용, "결론적으로")
- **S2**: 1-2회 OK, 3+ 시 제거 ("라고 봅니다", "직접 확인")
- **S3**: overlapping 시만 문제

## 가장 큰 효과 (K-Beauty v2 사례)

1. **B**: 영어 jargon 한국어 풀이 (stability/mechanism/PSM/HC3 등)
2. **J**: emoji 13 → 0, bold 30+ → 10 미만
3. **C**: TL;DR 박스 / 입사 키워드 박스 → 두괄식 한 단락
4. **D**: "라고 봅니다" 4회 → 2회
5. **E**: 종결 패턴 다양화

## 양액펌프 톤 (정답 reference)

사용자가 직접 작성한 양액펌프 portfolio 의 톤 — 본 프로젝트 portfolio 가 따라야 할 기준:

- emoji **0**
- bold 적당 (핵심 의사결정만)
- "라고 봅니다" 적당 (반복 X)
- 한국어 위주 + 영어 jargon 은 괄호 풀이 한 번만
- 자연 종결 ("그 뒤로 ~ 규칙을 세웠고", "그때 생긴 습관입니다")
- 두괄식 한 단락 (박스 X)

## 적용 시기

- ✅ portfolio (`01_`, `03_`, `04_`)
- ✅ 이력서, 자기소개서
- ✅ 노션 페이지 (외부 공유용)
- ❌ 코드 주석, 기술 docs/refactor/ (정확한 jargon 필요)
- ❌ README 의 기술 사양 부분
- ❌ 내부 분석 메모

## 처리 모드 (도구)

- **Fast** (≤5,000 chars 기본): 단일 호출 humanize-monolith 에이전트
- **Strict** (`--strict` 또는 ≥8,000 chars): 5-에이전트 파이프라인 (감지 + 재작성 + fidelity audit + naturalness review)

## K-Beauty v2 적용 사례

| 항목 | Before (commit `4f3b53e`) | After (commit `ee953a7`) |
|---|---|---|
| 길이 | 185 줄 | 143 줄 |
| emoji | 13 (🎯🔍⚙️📊🔝🔻💰📊🤖🕷🛢🧠💻📋📑📂) | 0 |
| bold | 30+ | 10 미만 |
| "라고 봅니다" | 4 회 | 2 회 |
| 영어 jargon | stability, robustness, mechanism, closed loop, paired t-test 등 | 한국어 풀이 |
| 두괄식 | TL;DR 박스 + "입사 시그널 키워드" 박스 | 한 단락 산문 |
| 정량 데이터 | 보존 ✅ | 보존 ✅ |
| 비교 표 | 6+ | 2 (Before/After + 4 단계 진화) |

## 참고

- 도구: github.com/epoko77-ai/im-not-ai
- 메모리 피드백: `feedback_im_not_ai_humanize.md` (Claude memory)
- 적용 commit: `ee953a7` (K-Beauty v2)