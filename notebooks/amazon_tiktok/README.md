# Amazon × TikTok 결합 분석 노트북

Amazon 리뷰 (정성) + TikTok 영상/인플루언서 데이터 (행동) 를 결합한 분석. **6 변종을 통폐합** ([EXPERIMENTS_PLAYBOOK](../../docs/refactor/EXPERIMENTS_PLAYBOOK.md) 패턴 C — README 카탈로그) — main + 발표용은 top-level, 나머지 진화 흔적은 [`experiments/`](experiments/) 보존.

## 폴더 구조

```
amazon_tiktok/
├── 🎯 amazon_tiktok_statistic_analysis_without_wonyoung.ipynb  (main, 가설 정식 검증)
├── 📄 amazon_tiktok_statistic_analysis_without_wonyoung copy.ipynb  (발표/보고용 정제본)
└── experiments/                                                (진화 흔적 보존)
    ├── amazon_tiktok_analysis.ipynb                  (시작점, Colab 기반 EDA)
    ├── amazon_tiktok_analysis_ngram_added.ipynb      (+ n-gram 분기, negation 적용 예시)
    ├── amazon_tiktok_statistic_analysis.ipynb        (+ 통계 분석 분기)
    └── amazon_tiktok_statistic_analysis_1228.ipynb   (12/28 시점 스냅샷)
```

## 진화 흐름 (시간순)

```
analysis (시작점, Colab 기반, 기본 EDA + lemmatize)
  ↓ + n-gram 피처 (spacy + PMI distribution)
analysis_ngram_added (local 경로로 전환)
  ↓ + 통계 분석 (회귀, ttest, mannwhitneyu)
  ↓ + plotly 시각화
statistic_analysis  (k_keyword = ["kbeauty", "korean", "wonyoung"])
  ↓ 시점 스냅샷 (12/28)
  ↓ k_keyword 에서 wonyoung 제거, "korea" 추가
statistic_analysis_1228
  ↓ wonyoung 정식 제외 + non_k_skincare 비교 그룹 정밀화
🎯 statistic_analysis_without_wonyoung   (main, 가설 정식 검증)
  ↓ 전처리/import 제거, 결과 위주 추출
📄 statistic_analysis_without_wonyoung copy   (발표/보고용 정제본)
```

## main 노트북 — `amazon_tiktok_statistic_analysis_without_wonyoung.ipynb`

| 항목 | 값 |
|---|---|
| 사이즈 | 57M |
| 핵심 가설 | 장원영 (wonyoung) 이상치 제외 + non_k_skincare 비교 그룹 정밀화 → 더 정확한 K-Premium 효과 추정 |
| `k_keyword` | `["kbeauty", "koreanskincare"]` (정밀화) |
| `non_k_skincare` | `["glassskin", "makeup", "skincareroutine", "skincare", "skintok"]` |
| 분석 단계 | EDA → n-gram + lemmatize → 통계 검정 (Kruskal-Wallis + Mann-Whitney + ttest) → 회귀 + ER% / ERV 비교 |
| 후속 인과 분석 | [`../tiktok/tiktok_marketing_modeling_v2.ipynb`](../tiktok/tiktok_marketing_modeling_v2.ipynb) PSM ATT (4.7642 %p) → [`../tiktok/tiktok_statistic_analysis.ipynb`](../tiktok/tiktok_statistic_analysis.ipynb) within-FE (selection 95%) |

## 발표용 노트북 — `_without_wonyoung copy.ipynb`

위 main 의 PART 1 (전처리) 제거, import 대부분 제거 (ast, nltk, langdetect, vaderSentiment, pyLDAvis 등). 결과/시각화 위주 추출 (15M, 261줄). 발표·리뷰용.

## experiments/ — 4 진화 흔적

| 노트북 | 역할 | 핵심 차이 | 라인 수 (.py 기준) |
|---|---|---|---:|
| `amazon_tiktok_analysis.ipynb` | **시작점** | Colab 기반 (`google.colab.drive`), 기본 lemmatize + word counts | 558 |
| `amazon_tiktok_analysis_ngram_added.ipynb` | **+ n-gram 피처** | local 경로 (`util.repo_paths.AMAZON`), spacy `en_core_web_sm`, `expand_negation`, `join_phrasal_verbs`, PMI distribution. **+ 부정어 처리 표준 모듈 적용 예시** ([`src/util/negation.py`](../../src/util/negation.py)) | 607 |
| `amazon_tiktok_statistic_analysis.ipynb` | **+ 통계 분기** | plotly.express, 회귀, `shapiro`/`levene`/`ttest_ind`/`mannwhitneyu`, tiktoker_size 그룹. `k_keyword` 4 단어 (wonyoung 포함) | 697 |
| `amazon_tiktok_statistic_analysis_1228.ipynb` | **12/28 시점 스냅샷** | tag_df/tag_count 추출. **k_keyword 에서 `wonyoung` 제거, `korea` 추가** | 701 |

## 주요 가설 검증 흐름

1. **n-gram 피처가 의미 있는가?** → `experiments/analysis_ngram_added` 에서 PMI 기반 검증 (이전 시도 점수 안 좋음 → [`src/util/negation.py`](../../src/util/negation.py) 모듈로 보완)
2. **K-Beauty 키워드 효과**: 처음엔 `wonyoung` 도 K-keyword 로 묶었으나, 장원영 개인 영향력이 K-Beauty 일반 효과와 섞여 분석 왜곡 가능 → **이상치 가설** 로 정식 제외 (main `without_wonyoung`)
3. **비교 그룹 정밀화**: 그냥 "non-K" 가 아니라 `non_k_skincare = [glassskin, skincareroutine, skintok ...]` 로 **같은 카테고리(스킨케어) 내** 비교 (선택 편향 ↓)
4. **결과 정제**: `copy` 에서 전처리 제거, 결과만 추출 — 발표/리뷰용

> ⚠️ **인과 추론 보강 진행 흐름**: 이 노트북들의 OLS 결과 → [`../tiktok/tiktok_marketing_modeling_v2.ipynb`](../tiktok/tiktok_marketing_modeling_v2.ipynb) PSM ATT (4.7642 %p) → [`../tiktok/tiktok_statistic_analysis.ipynb`](../tiktok/tiktok_statistic_analysis.ipynb) within-influencer Fixed Effect (cell 158-159).
>
> **최종 발견**: 단순 OLS 의 5%p 효과 중 **95.3% 가 인플루언서 selection effect**. 인플루언서 통제 시 K-beauty 키워드 자체 효과는 통계적으로 유의하지 않음 (0.24 %p, p=0.75). 자세히는 root [`../../README.md`](../../README.md) 의 "Causal Robustness 분석" 섹션 + [`../../docs/refactor/12`](../../docs/refactor/12_tiktok_recommendation_evolution.md).

## 변종 비교 명령어 (재검증 시)

```bash
# markdown 헤더 + import + 변수 할당 추출 (50M+ ipynb 도 30초)
cd notebooks/amazon_tiktok
for f in *.ipynb experiments/*.ipynb; do
  out="/tmp/$(basename "$f" .ipynb | tr ' ()' '___').summary"
  jupyter nbconvert --to script --stdout "$f" 2>/dev/null \
    | grep -E "^# ###|^# ##|^[a-z_]+ =|^def |^from |^import " > "$out"
done
diff /tmp/amazon_tiktok_statistic_analysis.summary /tmp/amazon_tiktok_statistic_analysis_without_wonyoung.summary
```

## 관련 docs

- [../../docs/refactor/EXPERIMENTS_PLAYBOOK.md](../../docs/refactor/EXPERIMENTS_PLAYBOOK.md) — 변종 정리 표준 + 통폐합 패턴 C (이 README 가 사례)
- [../../README.md](../../README.md) — 프로젝트 전체 + Causal Robustness 분석
- [../tiktok/tiktok_marketing_modeling_v2.ipynb](../tiktok/tiktok_marketing_modeling_v2.ipynb) — PSM ATT 인과 보강
- [../../src/util/negation.py](../../src/util/negation.py) — 부정어 처리 표준 모듈 (`ngram_added` 의 이전 시도 보완)
