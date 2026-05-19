# Amazon 분석 노트북

Amazon 5브랜드 (COSRX · PURITO · Beauty of Joseon · I'm From · Dr.Jart+) 리뷰·아이템·성분 분석 노트북 모음.

## 실행 순서

| 순서 | 노트북 | 단위 | 입력 | 출력 |
|---|---|---|---|---|
| 01 | `01_amazon_preprocessing.ipynb` | bronze → silver | `bronze/amazon/{brand}_items.csv` + `{brand}_reviews.csv` + `skinsort_0115.csv` | `silver/amazon/amazon_reviews_lemmatized.csv`, `amazon_items_processed.csv`, `skinsort_processed.csv` |
| 02 | `02_amazon_eda.ipynb` | silver 소비 | silver 3 파일 | 시각화 (영상) |
| 03 | `03_amazon_topic_modeling.ipynb` | silver → gold | silver 3 파일 | `gold/amazon/lda_topics_overall.csv` |

## 실행 흐름

```
bronze/amazon/  ──[01_preprocessing]──→  silver/amazon/  ──[02_eda]──→ 시각화
                                                          ──[03_topic_modeling]──→ gold/amazon/
```

순서 의존: 01 먼저 → silver 생성 → 02, 03 어느 쪽이든 가능.

## CLI 대체 (script 파이프라인)

01 의 변환 로직은 `src/pipelines/build_silver_amazon.py` 로 추출됨:

```bash
python src/pipelines/build_silver_amazon.py --overwrite
```

→ 02, 03 만 노트북으로 돌리고 싶을 때 사용. 01 노트북은 EDA 친화적 (cell 단위 검토), script 는 batch 친화적.

## 데이터 위치

- 입력: `data/bronze/amazon/` (5브랜드 items/reviews + skinsort)
- 중간/출력: `data/silver/amazon/`
- 최종 분석 input: `data/gold/amazon/`

## 진화 흔적

- 원본 monolithic: `notebooks/archive/lemmatized_full_pipeline.ipynb` (195 cells)
- 3-stage split 결정: `docs/refactor/11_project_code_dissolution.md`
- archive 보존 이유: `notebooks/archive/README.md`

## 관련 docs

- [`../../docs/refactor/11_project_code_dissolution.md`](../../docs/refactor/11_project_code_dissolution.md) — Phase 8 split 결정
- [`../../docs/refactor/16_silver_artifact_origin.md`](../../docs/refactor/16_silver_artifact_origin.md) — silver 단계 설계
- [`../../docs/bm25_for_tfidf_consideration.md`](../../docs/bm25_for_tfidf_consideration.md) — TF-IDF / BM25 비교 분석
