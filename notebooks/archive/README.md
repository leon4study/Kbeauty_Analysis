# notebooks/archive/

split / refactor 전의 monolithic 노트북 원본 보존.

## 파일

| 파일 | 사이즈 | 정체 | 현재 대체본 |
|---|---|---|---|
| `lemmatized_full_pipeline.ipynb` | 19.7M | Amazon 5브랜드 전처리 + EDA + LDA 토픽 모델링 195 cells 통합 노트북. 99.4% 가 cell outputs (그림·dataframe) | `notebooks/amazon/01_amazon_preprocessing.ipynb` + `02_amazon_eda.ipynb` + `03_amazon_topic_modeling.ipynb` |

## 왜 보존

- 통합 시점의 execution snapshot (출력물 포함) — split 직전 결과 비교용
- `docs/refactor/11_project_code_dissolution.md` 의 dissolution 흐름 증거
- 옛 분석 코드/주석에서 line 번호로 참조하는 경우 (예: `docs/bm25_for_tfidf_consideration.md`) 의 fallback

## 왜 split 함 (Phase 8)

`lemmatized_full_pipeline.ipynb` 195 cells = 한 노트북에 모든 단계가 섞임:
- run-all 시 전처리 + EDA + 모델링이 한 번에 → 실패 시 전체 재실행
- 각 단계 의존성 불명확
- 단일 책임 원칙 위반

→ medallion 패턴 (bronze/silver/gold) 에 맞춰 단계별 분리:
- `01_amazon_preprocessing.ipynb`: bronze → silver
- `02_amazon_eda.ipynb`: silver 소비, EDA
- `03_amazon_topic_modeling.ipynb`: silver 소비, LDA → gold

## 관련

- `docs/refactor/11_project_code_dissolution.md` — dissolution + Phase 8 split 결정 기록
- `notebooks/amazon/` — split 결과 (canonical)
