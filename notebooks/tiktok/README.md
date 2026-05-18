# TikTok 분석 노트북

TikTok 영상/인플루언서 데이터 기반의 EDA + 토픽 모델링 + 추천 알고리즘 + 마케팅 모델링 노트북 모음.

## 실행 순서

| 순서 | 노트북 | 단위 |
|---|---|---|
| 01 | `01_tiktok_eda.ipynb` | 영상 EDA |
| 02 | `02_tiktoker_eda.ipynb` | 인플루언서 EDA |
| 03 | `03_tiktoker_topic_modeling.ipynb` | 인플루언서 토픽 모델링 |
| 04 | `04_tiktoker_labeling.ipynb` | 토픽 → 카테고리 라벨링 |
| 05 | `05_tiktoker_recommend.ipynb` | 추천 알고리즘 |
| 06 | `06_tiktok_marketing_modeling_v2.ipynb` | K-Premium OLS/PSM |
| 07 | `07_tiktok_statistic_analysis.ipynb` | within-FE (selection effect) |

## 노트북 카탈로그

### 콘텐츠 단위 (`tiktok_*`)

| 노트북 | 무엇을 함 |
|---|---|
| `01_tiktok_eda.ipynb` | 영상 단위 기본 EDA |
| `06_tiktok_marketing_modeling_v2.ipynb` (**main**) | v1 refactor — 그룹 라벨 정리 (`Generic Skincare`/`K-Beauty`/`Others`), `required_cols` 입력 검증, `statsmodels` VIF 다중공선성 검사 추가, `run_premium_ols` 로 함수 단순화, ERV 가중치 `ERV_w` + `log_follower`/`log_view`/`view_to_follower_ratio` 파생 변수 |
| `07_tiktok_statistic_analysis.ipynb` | within-FE — selection effect 95% 발견 |
| `experiments/tiktok_marketing_modeling_v1.ipynb` (이전) | 그룹 라벨 `non_k_skincare_only`/`k_keyword`, sklearn `LogisticRegression` 기반 PSM, `run_models_compare` 함수. v2 가 refactor 한 후 진화 흔적 |

### 인플루언서 단위 (`tiktoker_*`)

| 노트북 | 무엇을 함 |
|---|---|
| `02_tiktoker_eda.ipynb` | 인플루언서 단위 EDA |
| `03_tiktoker_topic_modeling.ipynb` | LDA 등으로 인플루언서별 콘텐츠 토픽 추출 |
| `04_tiktoker_labeling.ipynb` | 토픽 모델 결과 → 카테고리 라벨링 (color/skincare/hair_body/...) → `tiktoker_top3_modeled_topic.csv` |
| `05_tiktoker_recommend.ipynb` | **추천 알고리즘** ver.1 → v2 → v3 + 회귀분석 + **정량화 (Top-10 무작위 대비 2.32배 ER%, 97.7 percentile)**. ver.3 강점 6 + 한계 분석은 [docs/refactor/12](../../docs/refactor/12_tiktok_recommendation_evolution.md). selection effect 인사이트 → 추천 알고리즘 솔루션 → 정량 검증의 closed loop |

## 데이터 위치

- 입력: `data/tiktok/tiktoker_crawling_df_*.csv`, `data/tiktok/cleaned_info_0130.xlsx`
- 중간/출력: `data/tiktok/tiktoker_top3_modeled_topic.csv`, `data/tiktok/merged_mean_0207.csv`
- 시각화 산출물: `data/tiktok/lda_per_tiktoker_0130/` (HTML)

## 변종 노트

`06_tiktok_marketing_modeling_v2.ipynb` (main) ↔ `experiments/tiktok_marketing_modeling_v1.ipynb` (이전) 차이 검증 완료 — v2 가 v1 의 refactor (그룹 라벨 + 함수 단순화 + VIF 검증 + ERV_w/log 변수). v1 은 진화 흔적으로 `experiments/` 보존 (amazon_tiktok 패턴 동일).

## 관련 docs

- [../../docs/refactor/12_tiktok_recommendation_evolution.md](../../docs/refactor/12_tiktok_recommendation_evolution.md) — 추천 알고리즘 ver.1/v2/v3 + 회귀분석 진화
- [../../docs/refactor/EXPERIMENTS_PLAYBOOK.md](../../docs/refactor/EXPERIMENTS_PLAYBOOK.md) — 변종 정리 표준
