# TikTok 분석 노트북

TikTok 영상/인플루언서 데이터 기반의 EDA + 토픽 모델링 + 추천 알고리즘 + 마케팅 모델링 노트북 모음.

## 두 갈래

| 갈래 | 단위 | 노트북 |
|---|---|---|
| **`tiktok_*`** | 영상/콘텐츠 단위 | `tiktok_EDA`, `tiktok_statistic_analysis`, `tiktok_marketing_modeling*` |
| **`tiktoker_*`** | 인플루언서 (틱톡커) 단위 | `tiktoker_EDA`, `tiktoker_topic_modeling`, `tiktoker_lableing`, `tiktoker_recommend` |

## 노트북 카탈로그

### 콘텐츠 단위 (`tiktok_*`)

| 노트북 | 무엇을 함 |
|---|---|
| `tiktok_EDA.ipynb` | 영상 단위 기본 EDA |
| `tiktok_statistic_analysis.ipynb` | 영상 통계 분석 |
| `tiktok_marketing_modeling.ipynb` (v1, 이전) | 그룹 라벨 `non_k_skincare_only`/`k_keyword`, sklearn `LogisticRegression` 기반 PSM, `run_models_compare` 함수 |
| `tiktok_marketing_modeling_v2.ipynb` (**v2, main**) | v1 refactor — 그룹 라벨 정리 (`Generic Skincare`/`K-Beauty`/`Others`), `required_cols` 입력 검증, `statsmodels` VIF 다중공선성 검사 추가, `run_premium_ols` 로 함수 단순화, ERV 가중치 `ERV_w` + `log_follower`/`log_view`/`view_to_follower_ratio` 파생 변수 |

### 인플루언서 단위 (`tiktoker_*`)

| 노트북 | 무엇을 함 |
|---|---|
| `tiktoker_EDA.ipynb` | 인플루언서 단위 EDA |
| `tiktoker_topic_modeling.ipynb` | LDA 등으로 인플루언서별 콘텐츠 토픽 추출 |
| `tiktoker_lableing.ipynb` | 토픽 모델 결과 → 카테고리 라벨링 (color/skincare/hair_body/...) → `tiktoker_top3_modeled_topic.csv` |
| `tiktoker_recommend.ipynb` | **추천 알고리즘** ver.1 → v2 → v3 + 회귀분석. ver.3 강점 6가지 + 한계 분석은 [docs/refactor/12](../../docs/refactor/12_tiktok_recommendation_evolution.md). selection effect 발견과 ER% 가중치의 정합성 — 사후 검증된 직관 |

## 데이터 위치

- 입력: `data/tiktok/tiktoker_crawling_df_*.csv`, `data/tiktok/cleaned_info_0130.xlsx`
- 중간/출력: `data/tiktok/tiktoker_top3_modeled_topic.csv`, `data/tiktok/merged_mean_0207.csv`
- 시각화 산출물: `data/tiktok/lda_per_tiktoker_0130/` (HTML)

## 변종 노트

`tiktok_marketing_modeling.ipynb` (v1) ↔ `_v2.ipynb` 차이 검증 완료 — v2 가 v1 의 refactor (그룹 라벨 + 함수 단순화 + VIF 검증 + ERV_w/log 변수). v2 가 main, v1 은 진화 흔적 (PLAYBOOK 패턴 C — README 카탈로그로 통합).

## 관련 docs

- [../../docs/refactor/12_tiktok_recommendation_evolution.md](../../docs/refactor/12_tiktok_recommendation_evolution.md) — 추천 알고리즘 ver.1/v2/v3 + 회귀분석 진화
- [../../docs/refactor/EXPERIMENTS_PLAYBOOK.md](../../docs/refactor/EXPERIMENTS_PLAYBOOK.md) — 변종 정리 표준
