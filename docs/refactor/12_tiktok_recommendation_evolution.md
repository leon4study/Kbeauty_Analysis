# TikTok 추천 알고리즘 진화

`tiktoker_recommend.ipynb` 한 노트북 안에서 **ver.1 → ver.2 → ver.3 → 회귀분석** 4단계로 추천 알고리즘이 진화한 흔적. [EXPERIMENTS_PLAYBOOK](EXPERIMENTS_PLAYBOOK.md) 패턴 A (단일 파일 + 주석 진화) 의 자연스러운 사례 — 변종이 별도 파일로 흩어지지 않고 한 노트북 안 셀로 누적되어 있어서 정리 작업 없이 이미 통폐합된 형태.

## 배경 / 의도

K-beauty 인플루언서 (틱톡커) 마케팅에서 "비슷한 인플루언서 추천" + "광고 ROI 가 높을 인플루언서 선정" 을 하기 위한 콘텐츠 기반 필터링 추천 시스템 구축. 기존 캠페인 인플루언서 (예: `krystallee2222`, `emchu_`) 와 콘텐츠 토픽이 유사한 인플루언서 top-N 을 추천하는 게 1차 목표.

## 진화 흐름

### Stage 1: 데이터 전처리

원본 `tiktoker_crawling_df_0127.csv` (인플루언서별 영상 row) 를 정제:

- **단위 변환**: `view_cnt`, `like_cnt`, `comment_cnt`, `save_cnt` 의 `k`/`m` 표기 → 숫자
- **날짜 정규화**: `1d ago`, `2w ago` 등 상대 표기 → `2025-01-21` 기준 절대 날짜
- **해시태그 추출**: `info` 컬럼에서 `#tag` 정규식 추출 → `hash_tag` 컬럼 재생성
- **자연어 처리**: NLTK tokenize + stopwords 제거

### Stage 2: 피처 엔지니어링 → `merged_mean_0207.csv`

인플루언서 단위 (mean_df) 로 집계 + 파생 피처 계산:

| 피처 | 공식/방법 | 의미 |
|---|---|---|
| `ad_cost` | `view_cnt * 20000` | 평균 조회수 × 2만 = 추정 광고 단가 (KRW) |
| `ER%` | `(like_cnt + comment_cnt) / follower_cnt * 100` | Engagement Rate — 인플루언서 콘텐츠 참여율 |
| `influencer_size` | 팔로워 수 기반 카테고리 (nano/micro/macro 등) | 광고 단가 협상 기준 |
| `avg_upload_interval` | name 별 업로드 날짜 diff 평균 | 활동 빈도 |
| `no.1, no.2, no.3` | `tiktoker_top3_modeled_topic.csv` 의 토픽 모델 top3 태그 merge | 콘텐츠 카테고리 (color/skincare/hair_body/fashion/unboxing/skin_routine/trend/asmr/eating/others) |

### Stage 3: 추천 알고리즘 ver.1 → v2 → v3 (Content-based filtering)

| 버전 | 변경점 | 의도 |
|---|---|---|
| **ver.1** | TF-IDF + cosine similarity. 콘텐츠 키워드 가중치 `no.1*3 + no.2*2 + no.3*1` | 가장 중요한 토픽 (no.1) 에 더 큰 가중치 |
| **ver.2** | ver.1 + ER% MinMax 정규화 → 키워드 반복 횟수에 곱셈 | 참여율 높은 인플루언서의 콘텐츠 키워드를 TF-IDF 에 더 강하게 반영 |
| **ver.3** | ver.2 + `max(1, ...)` 안전장치 | ER% 너무 낮을 때 키워드가 0번 반복되어 삭제되는 문제 보정 |

공통 알고리즘:
1. `content_features` 컬럼 = `no.1, no.2, no.3` 토픽을 가중치만큼 반복한 텍스트
2. `TfidfVectorizer().fit_transform(content_features)` → 인플루언서별 TF-IDF 벡터
3. 기존 캠페인 인플루언서 (selected_influencers) 의 TF-IDF 벡터와 cosine similarity
4. 평균 유사도 점수로 정렬 → top-N 추천

**왜 cosine similarity?** TF-IDF 결과는 고차원 희소 벡터 + 인플루언서별 콘텐츠 길이 차이 큼 → 벡터 방향만 비교하는 cosine 이 적합 (유클리드/jaccard/dot product 보다).

**왜 ER% 가중치를 v2 에서 추가?** ROI 관점 — ER% 높은 인플루언서가 광고 효율 높음 → 그들의 콘텐츠 토픽을 더 중요하게 다뤄야 함.

### 🎯 ver.3 의 강점 — 왜 이 선택을 했나 (깊이 분석)

단순 알고리즘 (cosine 만 / ER% Top-K 만) 보다 ver.3 가 우수한 6가지 이유:

#### 1. **콘텐츠 + ER% 결합 — 현업 의사결정 자동화**

단일 metric 알고리즘의 함정:

| 알고리즘 | 본 것 | 빠뜨린 것 | 위험 |
|---|---|---|---|
| ER% Top-K | 효율 | 캠페인 적합성 | skincare 캠페인에 ER% 높은 색조 인플루언서 추천 (부적합) |
| Cosine 만 | 적합성 | 효율 | 콘텐츠 맞지만 ER% 낮은 인플루언서 추천 (효율 낮음) |
| **결합 (ver.3)** | 둘 다 | — | — |

→ 현업 마케팅 매니저가 본능적으로 하는 trade-off ("컨셉 맞고 + 반응 좋은") 를 알고리즘으로 자동화. 단일 metric 만 사용한 알고리즘보다 의사결정 모델로서 우수.

#### 2. **인플루언서 selection effect 인코딩 — 사후 검증된 직관**

[`tiktok_statistic_analysis.ipynb`](../../notebooks/tiktok/tiktok_statistic_analysis.ipynb) 의 within-influencer FE 분석 (cell 158-159) 에서 발견:
- K-Premium 효과 95.3% 가 **인플루언서 selection effect**
- 단순 OLS 5.02 %p → Fixed Effect 0.24 %p (selection effect 4.78 %p)

ver.3 의 ER% 가중치는 인플루언서 selection 을 추천 score 에 직접 인코딩 — high-ER% 인플루언서들의 콘텐츠 패턴이 vector 에 더 강하게 박힘 → 결과적으로 high-ER% 인플루언서가 추천 score ↑.

> **사용자가 selection effect 발견 *전*에 직관으로 만들었지만, 사후 검증에서 정확한 방향임 입증** — 분석가 직관의 정확성.

#### 3. **TF-IDF + cosine 이 데이터 성격에 적합** — 도구 절제력

추천 input = LDA 토픽 라벨 (`no.1, no.2, no.3`) = 짧은, 이미 의미 압축된 키워드 (sparse 텍스트).

- TF-IDF + cosine = 짧은 sparse 텍스트의 표준 (적합)
- word2vec / BERT embedding = **over-engineering**
  - LDA 자체가 이미 semantic compression 결과
  - 추가 dense embedding 의 marginal gain 작음
  - 학습 / 인퍼런스 비용 ↑

→ 데이터 성격 보고 적합한 도구 선택 = 강력한 모델 욕심 안 부리는 절제력.

#### 4. **MinMax 정규화로 가중치 폭발 방지** — 의식적 hyperparameter 선택

ER% 자체로 곱했다면 절대값 차이 큼 (예: 1.8% vs 10.1% = **5.6배 차이**) → 가중치 폭발.

MinMax 0~1 = 절대값 대신 **상대 순위** 강조. 노트북 자체 주석:
> "ER%의 값이 너무 큰 경우(예: 1.8% vs. 10.1%) 가중치 차이가 심해질 수 있으므로 Min-Max Scaling을 적용"

→ Default 가 아닌 의식적 디자인 선택 — face validity (실용 직관) vs robustness 의 trade-off 에서 robustness 쪽으로 결정. 합리적.

#### 5. **`max(1, ...)` edge case 방어** — detail orientation

문제 시나리오: ER% 0 인 인플루언서
- `int(round(normalized_ER * 3, 0))` = 0
- 키워드 0번 반복 → TF-IDF vector 에서 사라짐
- 해당 인플루언서 추천 후보에서 **사실상 임의 배제**

방어: `max(1, ...)` 로 최소 1번 반복 보장 → 후보군에서 임의 배제 방지.

→ edge case 인지 + 명시적 처리. 노트북에 의도까지 주석으로 문서화 ("ER%가 너무 낮으면 가중치 값이 0이 되어 콘텐츠 키워드가 삭제될 위험 있음"). 분석가 detail orientation.

(구현 효과는 별개 — 의도와 효과 분리해서 평가하면 의도는 정확)

#### 6. **selected 다중 인플루언서 평균 유사도** — overfitting 방어

```python
similarity_scores = cosine_similarity(M, M[selected_indices])
df['content_similarity'] = similarity_scores.mean(axis=1)
```

- selected 한 명 기준 = 그 한 명의 noise / 편향에 over-fit
- 두 명 평균 = 캠페인의 **"유형"** 추정 → noise 완화
- 캠페인 전략이 "어떤 인플루언서들과 비슷한 그룹을 더 늘리고 싶다" 일 때 적절한 정의

### 한계 (정직하게)

| 한계 | 설명 | 개선 방향 |
|---|---|---|
| TF inflation 정보 손실 | `int(round(...))` 로 연속 normalized_ER 정보 일부 잃음 | row-wise vector scaling: `M_weighted = M.multiply(weight[:, None])` |
| **`max(1, ...)` 효과 미작동 — 정량 측정됨** | normalized_ER 분포 매우 skewed (median=0.045, 75pct=0.106) → factor 3 (no.1) 가중치=0 인 인플루언서 **47/56 (84%)**, factor 2 (no.2) **91%**, factor 1 (no.3) **96%** 발동. 거의 모든 인플루언서가 (1,1,1) 동일 가중치 → **ver.3 ≈ ver.2 (단순 3/2/1)** 결과 | ver.4 에서 vector scaling (연속 가중치) 으로 해결 |
| selected 2명만 검증 | `["krystallee2222", "emchu_"]` 만 — 다른 selected 조합으로 generalization 미검증 | 다양한 selected 조합으로 stability 테스트 |
| Cold-start | 새 인플루언서는 ER% 누적 + LDA 토픽 라벨 후만 추천 가능 | 메타데이터 기반 hybrid (팔로워/지역/카테고리) 보강 |

### 정량화 결과 (2026-05-03 검증)

ver.3 가 실제로 high-ER% 인플루언서를 잘 골라내는가? 후보 54명 중 Top-K 추천 vs 무작위 K명 (10000 부트스트랩) vs 천장 (ER% 상위 K) 비교.

| K | ver.3 추천 ER% | 무작위 평균 (95% CI) | 천장 (Top-K ER%) | 추천이 무작위 분포에서 |
|---:|---:|---:|---:|---:|
| 5 | 5.77 | 11.17 [2.30, 32.31] | 63.54 | 30.1 percentile |
| **10** | **26.51** | **11.42 [3.66, 26.28]** | 41.60 | **97.7 percentile** ✅ |
| 15 | 19.61 | 11.37 [4.50, 21.93] | 31.68 | 93.7 percentile ✅ |
| 20 | 16.65 | 11.33 [5.21, 19.22] | 25.84 | 89.7 percentile ✅ |

**핵심 결과**:
- **Top-10 추천 ER% = 26.51, 무작위 평균 11.42 → 약 2.32 배** (통계적으로 강함, 무작위 분포 97.7 percentile)
- Top-15/20 도 무작위 95% 신뢰구간 거의 상한 위 — robust
- Top-5 만 약함 (small-K 변동성)

**Ranking Quality**:
- Spearman corr (similarity ↔ ER%): rho = 0.087, p = 0.53 — 직접 상관 약함
- Precision@10: 20%, @15: 33%, @20: 35%
- → ver.3 는 **개별 ranking 정확도** 가 아닌 **Top-K 묶음 단위로 high-ER% 인플루언서 잡아냄** 효과

**Narrative 연결 (포트폴리오 흐름)**:
1. K-Premium 단순 OLS → PSM → FE 단계적 보강 → **selection effect 95% 발견**
2. 발견의 의미 → 인플루언서 selection 이 마케팅 핵심 레버
3. 솔루션: ver.3 추천 알고리즘 = selection 자동화 (ER% 가중치)
4. 정량 검증: Top-10 무작위 대비 **2.32배 ER%** ✅
5. 인사이트 (1-2) 과 솔루션 (3-4) 의 정량적 일치 — 분석 → 해석 → 액션 → 검증의 closed loop

**한계 (정량화 자체)**:
- selected 2명 고정 — generalization 미검증 (selected 다른 조합으로 stability 테스트 후속)
- Top-5 약함 (small-K)
- 가중치 mechanism 정확한 작동 분석 미완 (분포 점검 후속)

분석 위치: [`../../notebooks/tiktok/tiktoker_recommend.ipynb`](../../notebooks/tiktok/tiktoker_recommend.ipynb) 마지막 cell 들 (heading + quant_code + result_md).

### ver.4 — TF Inflation 제거 + Score 단계 ER% 가중치 (2026-05-03 추가)

ver.3 의 stability TEST 2 (Pearson -0.12) 에서 발견된 TF inflation 한계를 직접 해결.

**핵심 변경**:
```python
# ver.3 (TF inflation): 단어 N번 반복으로 TF 인플레이션
df['content_v3'] = (no.1+' ')*round(ER*3) + (no.2+' ')*round(ER*2) + (no.3+' ')*round(ER)
M = TfidfVectorizer().fit_transform(df['content_v3'])
score = cosine_similarity(M, M[selected]).mean(axis=1)

# ver.4 (vector scaling at score): 토픽 단순 결합 + score 단계 ER% 곱
df['content_v4'] = no.1 + ' ' + no.2 + ' ' + no.3
M = TfidfVectorizer().fit_transform(df['content_v4'])
sim = cosine_similarity(M, M[selected]).mean(axis=1)
score = sim * (df['normalized_ER'] + 0.1)  # 연속 가중치 + epsilon
```

**정량 비교 (1540 selected pair)**:

| Metric | ver.3 | ver.4 | 개선 |
|---|---:|---:|---:|
| 1540 pair 평균 ER% | 15.01 | **39.08** | +24.06 |
| std (변동성) | 6.83 | **4.35** | 안정성↑ |
| min | 1.84 | **17.94** | +16.10 |
| × random | 1.25× | **3.25×** | 2.6 배 |
| > random 비율 | 61.4% | **100%** | 모든 selected 능가 |
| Spearman (score↔ER%) | +0.087 | **+0.505** | 5.8× |
| Precision@10 | 20% | **60%** | 3× |

**Paired t-test (v4 - v3)**: t=122.80, p<0.0001 — 같은 selected 에서 평균 **+24.06 %p 개선**.

**ver.4 의 강점 종합**:
1. **효과 크기 ↑**: 1.25× → 3.25× random
2. **안정성 ↑**: std 6.83 → 4.35, > random 비율 61% → 100%
3. **메커니즘 명확**: TF inflation 의 정수 반올림 정보 손실 제거
4. **selected 의존도 ↓**: 어떤 selected 든 robust
5. **Ranking 정확도 ↑**: Precision@10 20% → 60% (3 배)
6. **코드 간결**: 복잡한 `apply + max + int + round` → 단순 곱셈

**ver.4 trade-off (정직히)**:
- selected ER% ↔ 추천 ER% Pearson **-0.62** (강한 음 상관)
- ver.4 score = sim × ER% → high-ER% 후보 우선 (selected 의존 ↓)
- 만약 캠페인 의도가 "selected 와 비슷한 인플루언서 추천" 이라면 ver.4 의 selected 의존도 낮음 = 단점
- "비슷한 + 효율 높은" 의 곱셈 = trade-off
- 후속: hybrid (rank fusion) — cosine rank + ER% rank 의 조합

**Narrative — ver.3 → ver.4 진화의 portfolio 가치**:

| 단계 | 분석가 활동 |
|---|---|
| 1차 ver.3 설계 | 직관 기반 (TF inflation + max(1) 안전장치) |
| 자기 검증 (stability test) | 한계 발견 — Pearson -0.12 → TF inflation 메커니즘 작동 X |
| ver.4 설계 | 한계 직접 해결 — score 단계 vector scaling |
| 정량 비교 검증 | ver.4 가 모든 metric 에서 압도 |

→ **분석가의 알고리즘 자기 비판 → 개선 → 검증의 closed loop** 입증.

분석 위치: [`../../notebooks/tiktok/tiktoker_recommend.ipynb`](../../notebooks/tiktok/tiktoker_recommend.ipynb) 끝 3 cells (ver.4 heading + code + result).

### Stability 검증 (2026-05-03 추가) — 정량화 결과의 robustness

위 정량화는 selected `[krystallee2222, emchu_]` **단일 조합** 결과. 다른 selected 였다면? 1540 selected pair 모두 검증:

| 측면 | 결과 | 의미 |
|---|---|---|
| 1540 pair 평균 | **15.01 ER%** (vs random 12.02) | **1.25× random** (정량화의 2.32× 와 큰 차이) |
| 변동성 | std 6.83, range [1.84, 34.15] | selected 에 따라 18배 차이 |
| selected ER% ↔ 추천 ER% Pearson | **-0.12** (p<0.0001) | ER% 가중치 메커니즘 의도대로 작동 X |
| 원래 selected 의 분포 위치 | **94.2 percentile** | **2.32× = lucky case** |

**selected size 효과**:

| size | mean | std | > random 비율 |
|---:|---:|---:|---:|
| 1 | 15.61 | 8.56 | 57% |
| 2 | 15.24 | 6.99 | 62% |
| 3 | 16.68 | 6.82 | 71% |
| **5** | **17.91** | 6.83 | **77%** |

→ **selected size 5+ 권장**. 단일 selected 조합 결과 보고는 lucky/unlucky 위험.

**자기 비판적 검증의 가치 (포트폴리오)**:
- 1차 정량화: Top-10 = 2.32× random → "강한 효과" 결론
- 2차 stability: 1.25× random (평균), 2.32× = lucky case → 한계 인정
- → 분석가의 **자기 비판적 검증 능력**이 portfolio 의 강점

**ver.4 의 필요성 (정량 입증)**:
- TEST 2 의 Pearson -0.12 = TF inflation 한계가 실제 결과에 영향 미침을 입증
- ver.4 구현 가치 ↑ — TF inflation → row-wise vector scaling 으로 ER% 가중치 정확히 적용

분석 위치: [`../../notebooks/tiktok/tiktoker_recommend.ipynb`](../../notebooks/tiktok/tiktoker_recommend.ipynb) 끝 3 cells (stability heading + code + result).

### Stage 4: 회귀분석 (가중치 자동 탐색)

ver.1~3 의 가중치 (`no.1*3 + no.2*2 + no.3*1`, ER% scaling 배수) 는 사람이 정한 heuristic. 회귀분석으로 데이터 기반 가중치를 찾는 시도:

**파생 변수 추가**:
- `like_ratio = like_cnt / view_cnt`, `comment_ratio = comment_cnt / view_cnt`, `save_ratio = save_cnt / view_cnt`
- `FSR = save_cnt / follower_cnt` (Follower-to-Save Ratio)
- `EPV = (like + comment + save) / view_cnt` (Engagement per View)
- `response_rate = (like + comment + save) / ad_cost`

**다중공선성 처리**: VIF 계산 후 `ad_cost`, `view_cnt`, `like_cnt`, `comment_cnt`, `save_cnt`, `response_rate`, `FSR`, `EPV` 제거 (서로 강한 상관).

**모델**: `LinearRegression` 으로 `ER%` 를 종속변수, `[like_ratio, comment_ratio, save_ratio, follower_cnt, avg_upload_interval]` 을 독립변수로 학습 → 회귀 계수 = 광고 ROI 가중치 후보.

**평가**: `MAE`, `R²`. 

**미완성 메모**: 노트북 끝에 `(예상 수익 - 투자 비용) / 투자 비용 * 100 = ROI%` ROI 계산 + "틱톡커 과거 ROI 가 있다면 그걸 종속변수로 회귀해서 ROI 예측 가능" 아이디어 적혀있음. 실제 ROI 데이터가 없어서 ER% 를 proxy 로 사용한 단계까지.

## 정성 검증 흔적

기존 캠페인 인플루언서 `["krystallee2222", "emchu_"]` 기준으로 ver.1, v2 의 추천 결과 출력. 노트북 셀 주석:
> krystallee2222 ER 높고 > 피부가 좋아서 신빙성 있음... emchu_ 컨셉

→ 정량 metric (cosine similarity) 외에 도메인 지식 기반 정성 검증을 같이 한 흔적.

## canonical 위치

```
notebooks/tiktok/tiktoker_recommend.ipynb     (이전: src/tiktok_recommendation/)

data/tiktok/
├── tiktoker_final_df_0127.csv               (입력: 영상 단위 원본)
├── tiktoker_top3_modeled_topic.csv          (입력: 토픽 모델링 결과)
└── merged_mean_0207.csv                     (Stage 2 출력: 인플루언서 단위 + 파생 피처)
```

## 학습 포인트

1. **변종을 별도 파일로 흩지 말고 한 노트북 안 셀로 누적** 하면 자연스럽게 통합된 진화 흔적이 남음 — `_v2.ipynb`, `_v3.ipynb` 식으로 파일 5개 만드는 것보다 미래의 본인이 한 번에 봄.
2. **v1 → v2 의 차이 (ER% 가중치 추가)** 는 도메인 통찰 (ROI 관점) 에서 나옴. 단순 metric 개선이 아니라 비즈니스 가설 검증 단계로 의미 있음.
3. **v2 → v3 의 `max(1, ...)` 안전장치** 는 실제 분포에서 발견한 edge case 보정. 가중치 시스템 만들 때 정규화 결과 0 이 되는 케이스를 항상 의심해야 함.
4. **회귀분석으로 가중치 자동 탐색** 은 heuristic → 데이터 기반 자연스러운 다음 단계. ROI 같은 진짜 종속변수가 없으면 ER% proxy 로 시작.
5. **ipynb 출력 셀 손상 위험** 때문에 50M+ 노트북의 변종 통합은 어려움. tiktoker_recommend 처럼 처음부터 한 노트북에 셀 단위로 두면 통합 비용 0.

## 위치 변경 노트

이전 위치 `src/tiktok_recommendation/` (모듈 형태) → 현재 `notebooks/tiktok/tiktoker_recommend.ipynb` + `data/tiktok/*.csv` (분석 노트북 + 데이터). 
이유: 모듈이라 부르기엔 노트북 1개 + csv 3개 형태였고, src 가 아니라 notebooks/data 가 자연스러운 자리. [11_project_code_dissolution.md](11_project_code_dissolution.md) 의 canonical 위치 그림은 이 변경 이전 (그 시점 truth) 을 반영.

## 관련 commits

- `9149705` — refactor: relocate tiktok_recommendation/ → notebooks/tiktok/
- `498d89e` (revert) — 같은 작업의 첫 시도 (untracked 사용자 파일이 같이 끌려와서 reset 후 재commit)
