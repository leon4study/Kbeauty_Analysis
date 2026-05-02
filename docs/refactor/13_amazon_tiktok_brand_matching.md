# Amazon × TikTok 브랜드 매칭 분석

본 프로젝트의 핵심 가치 (Amazon 정성 + TikTok 행동 통합) 를 직접 검증하는 분석. 5 K-Beauty 브랜드 (COSRX, Dr.Jart+, I'm From, Beauty of Joseon, PURITO) 를 매칭 키로 사용해 두 데이터의 상관 분석.

## 가설

> "TikTok 에서 화제가 된 브랜드 → Amazon 에서도 인기 / 매출 ↑"

이게 본 프로젝트의 raison d'être 인 통합 분석의 핵심 가설.

## 평가 설계

- **매칭 키**: 5 브랜드 (Amazon 의 `brand` 컬럼 ↔ TikTok 의 `info_tag + hash_tag` 키워드 매칭)
- **Amazon metric**:
  - `n_items`: 수집된 제품 수
  - `total_rating_count`: 제품별 `global_rating_count` 합산 (외부에서 본 인기도)
  - `n_reviews`: 수집한 리뷰 row 수
  - `avg_rating`: 제품별 별점 평균
  - `avg_review_rating`: 리뷰 별점 평균 (`"5.0 out of 5 stars"` 에서 숫자 추출)
- **TikTok metric**:
  - `n_videos`: 매칭된 영상 수
  - `total_view`, `total_like`: 합산
  - `avg_ERV`: 평균 참여율
  - `unique_creators`: 매칭 고유 인플루언서 수

## 결과 — 5 브랜드 매칭

| 브랜드 | Amazon items | Amazon total rating count | Amazon avg rating | TikTok n_videos | TikTok total_view | TikTok avg ERV |
|---|---:|---:|---:|---:|---:|---:|
| COSRX | 79 | **324,802** | 4.49 | 2 | 82,900 | 7.54 |
| Beauty of Joseon | 24 | 32,893 | 4.50 | 7 | 742,679 | 9.85 |
| I'm From | 58 | 24,029 | 4.48 | 7 | 104,672 | **15.90** |
| PURITO | 52 | 18,735 | 4.44 | **18** | **2,812,186** | 8.63 |
| Dr.Jart+ | 50 | 11,280 | 4.40 | 1 | 2,800,000 | 0.05 |

## 상관 분석 (n=5)

| 비교 | Pearson r | p | Spearman ρ |
|---|---:|---:|---:|
| **TikTok view ↔ Amazon total rating count** | -0.530 | 0.359 | **-0.800** |
| TikTok view ↔ 수집 리뷰수 | -0.384 | 0.523 | -0.300 |
| TikTok 영상수 ↔ Amazon 인기도 | -0.406 | 0.498 | 0.051 |
| TikTok total like ↔ Amazon 인기도 | -0.363 | 0.548 | 0.100 |
| TikTok 인플루언서수 ↔ Amazon 인기도 | -0.431 | 0.469 | 0.100 |
| **TikTok ERV ↔ Amazon avg rating** | **+0.745** | 0.149 | +0.500 |
| TikTok ERV ↔ Amazon 리뷰 평점 | -0.045 | 0.943 | +0.300 |

## 🔍 핵심 발견 — 가설 반박 + 양극화

### 1. 가설 반박: TikTok 활발도 ↔ Amazon 인기도 = **음의 상관** (Spearman -0.80)

원래 가설 ("TikTok 화제 → Amazon 매출") 의 정반대 방향. 5 브랜드 패턴 분석:

- **COSRX**: Amazon 압도적 (324K rating count, 평균의 14배) but TikTok 매칭 적음 (2 영상)
- **PURITO**: Amazon 중간 (18K) but TikTok **18 영상 / 281만 view / 196K like** — TikTok 활발 1위
- **Dr.Jart+**: Amazon 11K + TikTok 1 영상이 280만 view — 단일 바이럴
- **I'm From / Beauty of Joseon**: 중간

→ 패턴: **TikTok 활발도 = "성장중 / 신생 브랜드의 마케팅 채널"**, 이미 established 브랜드 (COSRX) 는 organic Amazon 인기 + TikTok 의존 ↓.

### 2. TikTok ERV ↔ Amazon 평점 양의 상관 (+0.745, marginal)

콘텐츠 참여율 (ERV) 와 제품 별점이 정렬됨 — "콘텐츠 품질 = 제품 품질" 가설 약하게 지지. 단 n=5 + p=0.149 라 robust 단정 어려움.

## Narrative — selection effect 와 같은 패턴

이번 발견도 **"단순 가정의 함정"** 패턴과 일치:

| 발견 | 단순 가정 | 인과/매칭 후 진실 |
|---|---|---|
| K-Premium (within-influencer FE) | "K-keyword → ERV +5%p" | selection effect 95% (이전 분석) |
| 토픽 효과 (within-influencer FE) | "asmr 가 ERV 가장 높음" | 8 토픽 중 7개 통제 시 유의 X (이전 분석) |
| **Amazon × TikTok 매칭** | **"TikTok 화제 → Amazon 매출"** | **음의 상관 — 신생/established 브랜드 양극화 (이번 분석)** |

→ 분석 보강 단계마다 **단순 가정이 깨지고 진짜 mechanism 이 드러남**. 분석가가 단순 metric 만 보지 않고 인과 / 매칭 / 통제까지 가야 정확한 의사결정 가능.

## 비즈니스 시사점

- 🎯 **TikTok 마케팅 효과는 신생/성장 브랜드에서 클 수 있음** (이미 established 한 브랜드는 organic 인기)
- 🎯 단순 "TikTok 트렌드 = Amazon 매출" 으로 KPI 잡으면 신생 브랜드 마케팅 효과 과소 평가 위험
- 🎯 **브랜드 단계별 (성장 stage) 차별 전략 필요** — established 는 retention, 신생/성장은 TikTok awareness

## 한계 (정직하게)

| 한계 | 설명 |
|---|---|
| **n=5 표본** | 5 브랜드만으로 통계적 유의성 약함 (모든 p > 0.1). 패턴 정도만 |
| **매칭 키 노이즈** | hash_tag/info_tag 키워드 매칭 — 브랜드 명시 안 한 영상 누락. 더 정교한 NER 가능 |
| **시간 차원 미반영** | TikTok 업로드 날짜 vs Amazon 리뷰 날짜 → 시계열 lag 분석 가능. 이번엔 단순 cross-sectional |
| **Confounder 통제 X** | 브랜드 가격, 출시 연도, Amazon 광고 비용 등 통제 못 함 |
| **수집 편향** | 수집된 5 브랜드는 사용자 선정. 무작위 sampling 아님 |

## 후속 분석 가능성

1. **시계열 매칭**: TikTok 업로드 → 그 이후 Amazon 리뷰 폭증 lag 분석. 진짜 인과 추론 가능
2. **더 많은 브랜드 매칭**: 30~50 브랜드로 확장 → 통계적 검정력 ↑
3. **브랜드 stage 통제**: 신생 / 성장 / established 분류 후 stage 별 효과 측정
4. **TikTok 영상 단위 매칭**: 브랜드 외에 제품명 (ASIN/title) 매칭 → 영상 단위 → Amazon 리뷰 영향
5. **TikTok ERV ↔ Amazon 평점 +0.745** 의 robust 검증 — 더 큰 샘플로

## 분석 코드

```python
import pandas as pd
import numpy as np
import re

amazon_path = '/Users/jun/GitStudy/Kbeauty_Analysis/data/amazon/'
brands = {
    'COSRX':            ('cosrx_items.csv', 'cosrx_reviews.csv'),
    'Dr.Jart+':         ('Dr_jart_items.csv', 'Dr_jart_reviews.csv'),
    "I'm From":         ('imfrom_items.csv', 'imfrom_reviews.csv'),
    'Beauty of Joseon': ('joseon_items.csv', 'joseon_reviews.csv'),
    'PURITO':           ('purito_items.csv', 'purito_reviews.csv'),
}

def extract_rating(s):
    if pd.isna(s): return np.nan
    m = re.search(r'(\d+\.?\d*)', str(s))
    return float(m.group(1)) if m else np.nan

# Amazon 집계
amazon_summary = []
for brand, (item_fn, review_fn) in brands.items():
    items = pd.read_csv(amazon_path + item_fn)
    reviews = pd.read_csv(amazon_path + review_fn)
    items['total_star_mean'] = pd.to_numeric(items['total_star_mean'], errors='coerce')
    items['global_rating_count'] = pd.to_numeric(items['global_rating_count'], errors='coerce')
    reviews['rating_num'] = reviews['review_rating'].apply(extract_rating)
    amazon_summary.append({
        'brand': brand,
        'amazon_total_rating_count': items['global_rating_count'].sum(skipna=True),
        'amazon_avg_rating': items['total_star_mean'].mean(),
        'amazon_n_reviews': len(reviews),
        'amazon_avg_review_rating': reviews['rating_num'].mean(),
    })
amazon_df = pd.DataFrame(amazon_summary)

# TikTok 매칭
tiktok = pd.read_csv('/Users/jun/GitStudy/Kbeauty_Analysis/data/tiktok/tiktoker_final_df_0127.csv')
tiktok['ERV'] = (tiktok['like_cnt']+tiktok['comment_cnt']+tiktok['save_cnt']) / tiktok['view_cnt'] * 100
tiktok = tiktok.dropna(subset=['ERV','view_cnt']).copy()
tiktok = tiktok[(tiktok['view_cnt'] > 0) & (tiktok['ERV'] <= tiktok['ERV'].quantile(0.99))]

brand_kw = {
    'COSRX': ['cosrx'], 'Dr.Jart+': ['drjart','drjartplus','dr.jart'],
    "I'm From": ['imfrom',"i'm from",'im_from'], 'Beauty of Joseon': ['beautyofjoseon','joseon'],
    'PURITO': ['purito']
}
tiktok['combined'] = tiktok['info_tag'].astype(str) + ' ' + tiktok['hash_tag'].astype(str)
tiktok['brands'] = tiktok['combined'].apply(lambda t: [b for b, kws in brand_kw.items() if any(k in str(t).lower() for k in kws)])
tex = tiktok.explode('brands').dropna(subset=['brands']).rename(columns={'brands':'brand'})

tiktok_summary = tex.groupby('brand').agg(
    tiktok_n_videos=('view_cnt', 'count'),
    tiktok_total_view=('view_cnt', 'sum'),
    tiktok_avg_ERV=('ERV', 'mean'),
).reset_index()

merged = amazon_df.merge(tiktok_summary, on='brand')
print(merged)

# 상관
from scipy.stats import pearsonr, spearmanr
r_p, p_p = pearsonr(merged['tiktok_total_view'], merged['amazon_total_rating_count'])
r_s, p_s = spearmanr(merged['tiktok_total_view'], merged['amazon_total_rating_count'])
print(f'TikTok view ↔ Amazon 인기도: Pearson r={r_p:.3f}, Spearman ρ={r_s:.3f}')
```

## 관련 docs

- [`12_tiktok_recommendation_evolution.md`](12_tiktok_recommendation_evolution.md) — 추천 알고리즘 진화 + selection effect
- [`../../README.md`](../../README.md) — Causal Robustness 섹션 (selection effect 95% 발견) 과 같은 narrative 패턴
- [`../../notebooks/tiktok/tiktok_statistic_analysis.ipynb`](../../notebooks/tiktok/tiktok_statistic_analysis.ipynb) cell 158-162 (within-influencer FE + 토픽 일반성)
