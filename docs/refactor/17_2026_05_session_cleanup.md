# 17 — 2026-05 medallion 마무리 + data legacy + 온보딩 정리

2026-05-17 ~ 2026-05-20 사이 PR #5 ~ #14 흐름에서 진행된 정리 작업의 종합 기록.
medallion 아키텍처 (Phase 8/9) 위에서 data legacy 청소 + bronze 네이밍 + team_folder
이동 + 온보딩 마찰 제거까지. 포트폴리오 트레일.

## 배경 / 의도

`docs/refactor/16_silver_artifact_origin.md` 의 silver 단계 도입 (2026-05-07) 이후:

- 본질적 medallion 구조는 잡혔지만 leftover 정리 미진
- `data/amazon/` + `data/tiktok/` 에 legacy CSV / 옛 출력물 산재
- 신규 사용자가 README 따라 챗봇 실행 시 마찰 (data gitignored → 입력 데이터 없음)
- `src/team_folder/` (옛 팀 노트북) 가 코드 모듈 폴더에 섞여있음
- `bronze/tiktok/` 파일명이 모호 (`cleaned_info.xlsx` 등)

→ 11 개 PR 에 걸쳐 단계별 정리.

## PR 흐름 (시간순)

| PR | 제목 | 핵심 변경 |
|---|---|---|
| #5 | lemmatized_full_pipeline 3분할 + silver bridge (Phase 8/9) | 195 cell monolithic → notebooks/amazon/01-03 분리. silver bridge 3 파일 |
| #6 | gold layer 추가 + main.py docstring | gold/amazon/lda_topics_overall.csv 신설 |
| #7 | notebooks/tiktok 실행 순서 번호 + 경로 오류 3 건 | 01-07 prefix, hardcoded path 제거 |
| #8 | build_silver_amazon.py CLI 파이프라인 | Amazon bronze → silver 변환 모듈화 |
| #9 | docs temp 삭제 + RAG indexing/input/ 생성 + db_schema 보강 | 챗봇 indexing 폴더 누락 fix |
| #10 | TikTok 노트북 4 개 medallion 경로 정합화 | TIKTOK → BRONZE_TIKTOK / SILVER_TIKTOK. broken symlink 4 개 제거 |
| #11 | bronze/tiktok 파일명 의도 명확화 | cleaned_info.xlsx → tiktoker_videos_cleaned.xlsx, _v1 통일 |
| #12 | Phase 8/Phase 7 후속 문서화 | notebooks/{archive,amazon}/README 신설, 인덱스 14-16 추가, src/README pipelines/ 추가 |
| #13 | src/team_folder/ → data/archive/team_folder/ | 297M (PPTX 235M 포함) 이동. src/ 컨벤션 회복 |
| #14 | 온보딩 마찰 제거 + data/model legacy 정리 | examples/graphrag_input/ 신설, .env.example default Ollama 통일, data/model 9 개 stale dir archive |

## 카테고리별 정리 결과

### A. data/ legacy 정리

**Amazon legacy 5 CSV** (43M, 메인 노트북 read 0, 전부 주석/CWD-write):
- `amazon_df_v1.csv`, `amazon_df_v2.csv` (items × reviews 조인본 v1/v2)
- `amazon_items_df.csv`, `amazon_reviews_df.csv` (5 브랜드 통합)
- `amazon_koreaOnly_translated.csv` (번역본)
→ `data/archive/legacy_amazon_intermediate/` (README 포함)

**TikTok 파일 재배치**:
- 3 CSV (`merged_mean_0207`, `tiktoker_top3_modeled`, `tiktoker_top5_hashtags`) → silver/tiktok/
- `cleaned_info.xlsx` → bronze/tiktok/ + rename `tiktoker_videos_cleaned.xlsx`
- 2 PDF (참고 논문) → References/
- `dashboards/` (3 .twbx) → gold/tiktok/dashboards/
- `result/` (autogluon log), `influencer.png`, `cleaned_info_0130.xlsx` (0 refs) → archive/orphan_outputs/
- `logs.log` (2.5M), `catboost_info/` 삭제

**data/model legacy 9 개 dir + gradio_insert** → `data/archive/legacy_graphrag_models/`.
남은 active: `graphrag_t_2/` (Ollama), `openaitest_0206/` (OpenAI) 만.

**broken symlink 4 개 제거** (data/tiktok/popular_tag, tag_count, tiktoker_crawling_df_012{1,7}).

### B. medallion 경로 정합화 (코드)

| 노트북 | 옛 경로 | 새 경로 |
|---|---|---|
| 02_tiktoker_eda | `TIKTOK / 'tiktoker_top5_hashtags.csv'` | `SILVER_TIKTOK / ...` |
| 03_tiktoker_topic_modeling | `TIKTOK / 'tiktoker_crawling_df_0127.csv'` (broken) | `BRONZE_TIKTOK / 'tiktokers_raw.csv'` |
| 04_tiktoker_labeling | `TIKTOK / 'cleaned_info.xlsx'`, CWD write | `BRONZE_TIKTOK / 'tiktoker_videos_cleaned.xlsx'`, `SILVER_TIKTOK / ...` |
| 05_tiktoker_recommend | 5 곳 `TIKTOK / 'merged_mean_0207.csv'` 등 | `SILVER_TIKTOK / ...`. `from src.util.repo_paths` → 표준 `from util.repo_paths` |

### C. 파일명 명확화 (bronze/tiktok)

| 옛 | 신규 | 이유 |
|---|---|---|
| `tiktok_search_cleanbeauty.csv` | `tiktok_search_cleanbeauty_v1.csv` | v2 와 짝 |
| `cleaned_info.xlsx` | `tiktoker_videos_cleaned.xlsx` | 단위 (인플루언서×영상) + 정제 상태 명시 |
| `tiktoker_crawling_df_0127.csv` (이미 #5 에서) | `tiktokers_raw.csv` | rename 통일 |

### D. 폴더 배치 정정

- `src/team_folder/` (297M, 노트북 + PPTX) → `data/archive/team_folder/`
  - src/ 컨벤션: 코드 모듈만
  - team_folder 는 historical archive 성격
- `cleaned_info_0130.xlsx` (0 refs) → archive/orphan_outputs/

### E. 온보딩 (fresh-clone 사용자 마찰 제거)

**문제 4 가지**:
1. **인덱싱 input txt 가 data/ (gitignored) 에만 있어 fresh clone 시 없음**
   → `examples/graphrag_input/` 신설 (5brand_graphrag_part.txt 100K + brand_50_sample.txt 44K + README)
2. **`.env.example` default 가 README 권장값과 불일치** (mistral-large vs gemma2)
   → Ollama 권장값 (gemma2 + nomic-embed-text + dummy key) 으로 통일. OpenAI 변형은 주석 alternative
3. **placeholder 절대경로** (`/absolute/path/to/...`)
   → 주석 처리 (모듈 자체 default 사용)
4. **두 챗봇 README 의 indexing input 경로 분산**
   → examples/ 에서 cp 하는 통일된 절차

**Root README** 에 fresh-clone Quick Start 8 줄 섹션 신설.

### F. 종합 문서화

신설된 README:
- `notebooks/archive/README.md` — Phase 8 split 직전 monolithic 보존 이유
- `notebooks/amazon/README.md` — 3 단계 실행 순서 + bronze/silver/gold flow + CLI 대체
- `data/bronze/tiktok/README.md` — 4 파일 카탈로그 + 단위 구분
- `data/archive/legacy_amazon_intermediate/README.md` — 옛 산출물 보존 이유
- `data/archive/legacy_graphrag_models/README.md` — 옛 인덱스 보존 이유
- `data/tiktok/lda_per_tiktoker_0130/README.md` — 251 LDA 시각화 deliverable
- `examples/graphrag_input/README.md` — 인덱싱 input 사용법

업데이트된 README:
- Root README — 노트북 카운트, gold/References 폴더, fresh-clone Quick Start
- `src/README.md` — pipelines/ 모듈 추가, medallion 경로 정정, BRONZE/SILVER 상수
- `docs/refactor/README.md` — 14, 15, 16, 17 인덱스 추가
- `docs/bm25_for_tfidf_consideration.md` — Phase 8 split 후 위치 정정
- `docs/db_schema.md` — 실제 컬럼 기준 보강
- `docs/slack_alert.md` — 오타 fix + 환경변수/관련 파일

## 최종 medallion 구조

```
data/
├── bronze/
│   ├── amazon/          ← 5 브랜드 items/reviews + skinsort (raw)
│   └── tiktok/          ← 4 파일 (검색 csv + 인플루언서 raw + 정제본)
├── silver/
│   ├── amazon/          ← (build_silver_amazon.py 실행 시 생성)
│   └── tiktok/          ← tiktok_videos_silver, tiktokers_silver (artifact) + 3 분석 output
├── gold/
│   ├── amazon/          ← lda_topics_overall.csv
│   └── tiktok/dashboards/  ← 3 Tableau .twbx
├── model/
│   ├── graphrag_t_2/    ← Ollama 인덱스
│   └── openaitest_0206/ ← OpenAI 인덱스
├── References/          ← 참고 논문 PDF 4
└── archive/             ← legacy + orphan + team_folder + 옛 graphrag models
```

## 학습 포인트

1. **gitignored 데이터의 함정** — data/ 통째 ignore 가 fresh clone 사용성을 망침. 핵심 sample input 은 `examples/` 처럼 별도 위치에 commit 해야 함.

2. **rename 작업의 검증 패턴** — 옛 이름 grep 잔존 0 + 새 이름 파일 존재 확인 + import-read 경로 일치 검증의 3 단계.

3. **변종 폴더 위치는 의미를 반영해야 함** — `src/team_folder/` 처럼 코드 폴더에 archive 성격이 섞이면 의도 불명확. `data/archive/` 로 이동해야 한눈에 보임.

4. **broken symlink 는 잘 안 보이는 함정** — 이전 세션에서 만든 symlink 가 stale 해도 노트북이 깨질 때까지 발견 안 됨. medallion migration 시 symlink 도 같이 추적.

5. **placeholder 와 default 의 차이** — `.env.example` 의 default 는 *그대로 cp 만 해도 동작* 해야 함. placeholder (`/absolute/path/to/...`) 는 user 가 반드시 편집해야 한다는 신호 → 가능한 default 로 대체.

## 관련 commits

```
faba5c2 feat(onboarding): fresh-clone 챗봇 실행 마찰 제거 + 5순위 data/model 정리 (#14)
0dde401 chore: src/team_folder/ → data/archive/team_folder/ 이동 (#13)
571a51f docs: 종합 .md 정리 — Phase 8 split + Phase 7 naming 후속 문서화 (#12)
8616706 refactor(bronze/tiktok): 파일명 의도 명확화 + README 신설 (#11)
9b55367 refactor: TikTok 노트북 4개 medallion 경로 정합화 + broken symlink 정리 (#10)
79b5756 docs: temp 파일 삭제 + RAG 챗봇 실행 경로 보완 + db_schema/slack_alert 보강 (#9)
9730aa5 feat(pipelines): build_silver_amazon.py — Amazon bronze → silver CLI 파이프라인 (#8)
9b8fe0d refactor(notebooks/tiktok): 실행 순서 번호 추가 + 경로 오류 3건 수정 (#7)
105f10e docs: gold layer 추가 + main.py 전체 docstring 보강 (#6)
86a6b27 refactor: lemmatized_full_pipeline 3분할 + silver bridge + docs (Phase 8/9) (#5)
```

## 관련 docs

- [`11_project_code_dissolution.md`](11_project_code_dissolution.md) — src/project_code 해체 (이번 정리의 시작점)
- [`16_silver_artifact_origin.md`](16_silver_artifact_origin.md) — silver 단계 설계 (이번 정리의 base)
- [`EXPERIMENTS_PLAYBOOK.md`](EXPERIMENTS_PLAYBOOK.md) — 변종 정리 표준 (이번 정리에 적용)
