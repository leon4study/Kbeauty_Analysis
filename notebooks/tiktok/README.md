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
| `tiktok_marketing_modeling.ipynb` (v1) | 마케팅 효과 모델링 v1 |
| `tiktok_marketing_modeling_v2.ipynb` (v2) | 마케팅 효과 모델링 v2 (v1 다음 단계, **차이 검증 필요**) |

### 인플루언서 단위 (`tiktoker_*`)

| 노트북 | 무엇을 함 |
|---|---|
| `tiktoker_EDA.ipynb` | 인플루언서 단위 EDA |
| `tiktoker_topic_modeling.ipynb` | LDA 등으로 인플루언서별 콘텐츠 토픽 추출 |
| `tiktoker_lableing.ipynb` | 토픽 모델 결과 → 카테고리 라벨링 (color/skincare/hair_body/...) → `tiktoker_top3_modeled_topic.csv` |
| `tiktoker_recommend.ipynb` | **추천 알고리즘** ver.1 → v2 → v3 + 회귀분석. 자세한 진화는 [docs/refactor/12](../../docs/refactor/12_tiktok_recommendation_evolution.md) |

## 데이터 위치

- 입력: `data/tiktok/tiktoker_crawling_df_*.csv`, `data/tiktok/cleaned_info_0130.xlsx`
- 중간/출력: `data/tiktok/tiktoker_top3_modeled_topic.csv`, `data/tiktok/merged_mean_0207.csv`
- 시각화 산출물: `data/tiktok/lda_per_tiktoker_0130/` (HTML)

## 변종 노트

`tiktok_marketing_modeling.ipynb` (v1) ↔ `_v2.ipynb` 차이는 아직 정밀 검증 안 됨 — 별도 큐레이션 세션에서 확인 후 [EXPERIMENTS_PLAYBOOK](../../docs/refactor/EXPERIMENTS_PLAYBOOK.md) 패턴 A/C 적용 예정.

## 관련 docs

- [../../docs/refactor/12_tiktok_recommendation_evolution.md](../../docs/refactor/12_tiktok_recommendation_evolution.md) — 추천 알고리즘 ver.1/v2/v3 + 회귀분석 진화
- [../../docs/refactor/EXPERIMENTS_PLAYBOOK.md](../../docs/refactor/EXPERIMENTS_PLAYBOOK.md) — 변종 정리 표준
