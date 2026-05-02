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

## 분석 코드 (재현용 + step 별 주석)

```python
import pandas as pd
import numpy as np
import re
from scipy.stats import pearsonr, spearmanr

# ===== STEP 0: 분석 대상 5 K-Beauty 브랜드 정의 =====
# - 사용자가 사전에 수집한 brand: items + reviews csv pair
# - 각 csv 는 ASIN (제품 ID) 단위로 정리됨
# - brand 명은 이후 TikTok 영상의 hash_tag/info_tag 매칭 키로 사용
amazon_path = '/Users/jun/GitStudy/Kbeauty_Analysis/data/amazon/'
brands = {
    'COSRX':            ('cosrx_items.csv', 'cosrx_reviews.csv'),
    'Dr.Jart+':         ('Dr_jart_items.csv', 'Dr_jart_reviews.csv'),
    "I'm From":         ('imfrom_items.csv', 'imfrom_reviews.csv'),
    'Beauty of Joseon': ('joseon_items.csv', 'joseon_reviews.csv'),
    'PURITO':           ('purito_items.csv', 'purito_reviews.csv'),
}


def extract_rating(s):
    """Amazon 리뷰의 별점 문자열에서 숫자만 추출.

    원본 형식 예시:
        "5.0 out of 5 stars"  → 5.0
        "1.0 out of 5 stars"  → 1.0
        "No review"           → NaN
        NaN                    → NaN

    왜 이 함수가 필요한가:
        Amazon 리뷰 csv 의 `review_rating` 컬럼은 string 형식 ("5.0 out of 5 stars").
        평균 계산을 위해 첫 숫자 (1.0~5.0) 만 추출. "No review" 같은 비숫자 값은 NaN 처리.
    """
    if pd.isna(s):
        return np.nan
    # 정규식: 첫 번째 (\d+\.?\d*) = 정수 또는 소수 패턴 매칭. "5.0 out of 5" → "5.0" 만 캡처
    m = re.search(r'(\d+\.?\d*)', str(s))
    return float(m.group(1)) if m else np.nan


# ===== STEP 1: Amazon 브랜드별 metric 집계 =====
# 5 브랜드 각각에 대해 items.csv + reviews.csv 두 파일 읽고 4 metric 산출:
#   - amazon_total_rating_count: 외부 (Amazon 전체 사용자) 의 인기도 시그널
#   - amazon_avg_rating: 제품별 별점 평균 (수집된 items 기준)
#   - amazon_n_reviews: 수집한 리뷰 row 수 (수집 효율 시그널)
#   - amazon_avg_review_rating: 수집한 리뷰의 별점 평균
amazon_summary = []
for brand, (item_fn, review_fn) in brands.items():
    # items.csv: 제품 단위 metadata (ASIN, title, brand, price, total_star_mean,
    #            global_rating_count 등 31 컬럼). 한 행 = 한 제품
    items = pd.read_csv(amazon_path + item_fn)

    # reviews.csv: 리뷰 단위 데이터 (review_num, ASIN, customer_id, review_rating,
    #              content 등 8 컬럼). 한 행 = 한 리뷰
    reviews = pd.read_csv(amazon_path + review_fn)

    # 숫자 컬럼이 string 으로 저장된 경우 강제 변환 (errors='coerce' = 변환 실패 시 NaN).
    # csv 에 따라 컬럼이 mixed dtype 으로 저장된 경우 mean() 호출 시 TypeError 발생 → 이를 방어
    items['total_star_mean']     = pd.to_numeric(items['total_star_mean'], errors='coerce')
    items['global_rating_count'] = pd.to_numeric(items['global_rating_count'], errors='coerce')

    # review_rating 은 "5.0 out of 5 stars" 형식 → 숫자만 추출
    reviews['rating_num'] = reviews['review_rating'].apply(extract_rating)

    amazon_summary.append({
        'brand': brand,
        # global_rating_count = 제품 페이지 상단의 "10,234 ratings" 숫자.
        # Amazon 전체 사용자 (수집한 리뷰 외 모두) 의 인기도 시그널 → 합산.
        # NaN 있을 수 있어 skipna=True (기본값이지만 명시)
        'amazon_total_rating_count': items['global_rating_count'].sum(skipna=True),

        # 제품별 평균 별점의 평균. 제품 단위 → 브랜드 평균 (제품 가중 X, 단순 평균)
        'amazon_avg_rating':         items['total_star_mean'].mean(),

        # 수집한 리뷰 row 수. 수집 한도 + 브랜드 인기 둘 다 영향 → 그래도 시그널
        'amazon_n_reviews':          len(reviews),

        # 수집한 리뷰 별점 평균. (수집 시 random sampling 가정하면 review 평균 ≈ 모집단 평균)
        'amazon_avg_review_rating':  reviews['rating_num'].mean(),
    })
amazon_df = pd.DataFrame(amazon_summary)

# ===== STEP 2: TikTok 영상 데이터 + 파생 metric =====
# tiktoker_final_df_0127.csv: 영상 단위 (한 행 = 한 영상). 1680 영상.
# 컬럼: name (인플루언서), follower_cnt, view_cnt, like_cnt, comment_cnt, save_cnt,
#        info_tag (영상 설명), hash_tag (해시태그)
tiktok = pd.read_csv('/Users/jun/GitStudy/Kbeauty_Analysis/data/tiktok/tiktoker_final_df_0127.csv')

# ERV (Engagement Rate per View) — 조회수 대비 참여율
# 정의: (좋아요 + 댓글 + 저장) / 조회수 × 100
# 왜 이 metric: ER (팔로워 기반) 보다 ERV (view 기반) 가 영상 단위 효율을 더 정확히 측정 (팔로워 외 시청자 포함)
tiktok['ERV'] = (tiktok['like_cnt'] + tiktok['comment_cnt'] + tiktok['save_cnt']) / tiktok['view_cnt'] * 100

# 결측치 제거 + view_cnt=0 이상치 제거 (분모가 0 이면 ERV 무한)
tiktok = tiktok.dropna(subset=['ERV', 'view_cnt']).copy()
tiktok = tiktok[tiktok['view_cnt'] > 0].copy()

# 상위 1% 윈저화 — 바이럴 outlier 가 평균 왜곡하는 것 방지.
# (예: ERV 200% 같은 극단값. 데이터 수집 오류 또는 super-viral 영상)
# tiktok_marketing_modeling_v2.ipynb 분석과 동일 정책
tiktok = tiktok[tiktok['ERV'] <= tiktok['ERV'].quantile(0.99)].copy()

# ===== STEP 3: TikTok 영상의 브랜드 매칭 =====
# 매칭 키: 영상의 info_tag (영상 설명) + hash_tag (해시태그) 결합 텍스트에서 브랜드 키워드 검색
# 한 영상이 여러 브랜드 언급 가능 (예: "I tried both #cosrx and #purito") → list 반환
brand_kw = {
    'COSRX':            ['cosrx'],
    'Dr.Jart+':         ['drjart', 'drjartplus', 'dr.jart'],     # 표기 다양성 대응
    "I'm From":         ['imfrom', "i'm from", 'im_from'],         # 공백/언더스코어 변종 대응
    'Beauty of Joseon': ['beautyofjoseon', 'joseon'],              # 짧은 'joseon' 도 허용
    'PURITO':           ['purito'],
}

# info_tag + hash_tag 결합 (info_tag 만 보면 해시태그 누락, hash_tag 만 보면 본문 누락)
tiktok['combined'] = tiktok['info_tag'].astype(str) + ' ' + tiktok['hash_tag'].astype(str)

# 영상마다 매칭된 브랜드 list — 0~5 개 가능. 매칭 안 된 영상은 빈 list
tiktok['brands'] = tiktok['combined'].apply(
    lambda t: [b for b, kws in brand_kw.items() if any(k in str(t).lower() for k in kws)]
)

# explode: 한 영상이 N 브랜드 언급 → N rows 로 펼침. 이후 groupby 시 각 브랜드별 집계 가능
# dropna(subset=['brands']): explode 후 빈 list 였던 영상은 NaN → 제거 (브랜드 매칭 안 된 영상 누락)
tex = tiktok.explode('brands').dropna(subset=['brands']).rename(columns={'brands': 'brand'})

# ===== STEP 4: TikTok 브랜드별 metric 집계 =====
# tex 에서 brand 로 groupby → 5 행 (5 브랜드)
tiktok_summary = tex.groupby('brand').agg(
    # n_videos: 매칭된 영상 수 (한 영상이 여러 브랜드 언급 시 각 브랜드에 카운트)
    tiktok_n_videos       = ('view_cnt', 'count'),
    # total_view: 매칭 영상의 총 조회수 합 → 브랜드의 TikTok 노출 규모 시그널
    tiktok_total_view     = ('view_cnt', 'sum'),
    # avg_ERV: 매칭 영상의 ERV 평균 → 브랜드 콘텐츠의 평균 참여율
    tiktok_avg_ERV        = ('ERV', 'mean'),
).reset_index()

# ===== STEP 5: Amazon × TikTok 결합 =====
# inner join — 5 브랜드 모두 양쪽에 존재하므로 결과 5 rows
merged = amazon_df.merge(tiktok_summary, on='brand')
print(merged)

# ===== STEP 6: 상관 분석 =====
# Pearson r: 선형 상관 (정규성 가정, 이상치에 민감)
# Spearman ρ: 순위 상관 (비선형/이상치에 robust, 작은 표본에서 안전)
# n=5 라 둘 다 검정력 매우 약함 — 패턴 시그널만 확인
r_p, p_p = pearsonr(merged['tiktok_total_view'], merged['amazon_total_rating_count'])
r_s, p_s = spearmanr(merged['tiktok_total_view'], merged['amazon_total_rating_count'])
print(f'TikTok view ↔ Amazon 인기도: Pearson r={r_p:.3f} (p={p_p:.3f}), Spearman ρ={r_s:.3f}')
# Spearman -0.80 = 5 브랜드 순위가 거의 정반대로 정렬됨 → "TikTok 화제 → Amazon 인기" 가설 반박
```

### 핵심 계산 step 요약

| Step | 무엇을 함 | 핵심 결정 |
|---|---|---|
| 0 | 5 브랜드 정의 + Amazon items/reviews csv pair | 매칭 키로 brand 명 사용 |
| 1 | Amazon brand 별 4 metric 집계 | items 의 `global_rating_count` 합 = "외부 인기도" 시그널 |
| 2 | TikTok 영상 ERV 정의 + 윈저화 + 결측 제거 | ERV = (like+comment+save)/view × 100, 상위 1% 컷 |
| 3 | 영상 → 브랜드 매칭 (info_tag + hash_tag) | 한 영상 → 여러 브랜드 가능, list 처리 후 explode |
| 4 | TikTok brand 별 3 metric 집계 | n_videos / total_view / avg_ERV |
| 5 | Amazon × TikTok inner merge | 5 rows |
| 6 | Pearson + Spearman 상관 | n=5 한계 인지, 패턴 시그널만 확인 |

## 관련 docs

- [`12_tiktok_recommendation_evolution.md`](12_tiktok_recommendation_evolution.md) — 추천 알고리즘 진화 + selection effect
- [`../../README.md`](../../README.md) — Causal Robustness 섹션 (selection effect 95% 발견) 과 같은 narrative 패턴
- [`../../notebooks/tiktok/tiktok_statistic_analysis.ipynb`](../../notebooks/tiktok/tiktok_statistic_analysis.ipynb) cell 158-162 (within-influencer FE + 토픽 일반성)
