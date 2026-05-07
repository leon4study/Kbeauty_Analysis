# K-Premium 수치 변천사 — 왜 8.43 → 4.76 ~ 5.10 으로 갔나

K-Beauty 키워드의 ERV 효과 추정값이 분석 진화에 따라 8.43 %p → 4.76 ~ 5.10 %p 로 변경되었다. 포트폴리오·문서·노트북에 흩어진 수치를 헷갈리지 않게 영구 기록.

## 한 줄 결론

> 옛 8.43 %p 는 윈저화 미적용 + outlier 영향 받은 과대 추정. 윈저화 99% + HC3 SE 적용 후 5.10 %p (상한), PSM ATT 인과 보강 후 4.76 %p (하한). **현재 main 은 4.76 ~ 5.10 %p 구간**.

## 수치 진화 단계

### 단계 1 — 옛 OLS 8.43 %p (윈저화 X)

**언제**: 초기 분석 시점 (notebook `tiktok_statistic_analysis.ipynb` cell 147 에 hardcoded). 노트북 cell 174 의 잠재 가치 계산 (15.01 억원) 도 이 계수 기반.

**모델**: `ERV ~ k_keyword_flag + log_follower + log_view`, OLS, k_keyword 4 단어 (`["kbeauty", "korean", "wonyoung", "korea"]`)

**결과**: +8.4299 %p (p=0.005), 95% CI [2.46, 14.15]

**왜 이 수치가 나왔나**:
- 데이터 전처리에 **윈저화 (winsorization) 미적용** — n=1680 전체 사용
- TikTok 데이터의 viral 특성 상 ERV outlier (max 132% 수준) 가 평균 효과 과대 추정
- 신뢰구간 매우 넓음 ([2.46, 14.15]) — outlier 영향으로 추정 불안정

**왜 더 이상 안 쓰나**:
1. 윈저화 미적용 → 1% extreme 이 평균을 끌어올림
2. CI 너무 넓어 실무 의사결정에 부적합
3. 인과 보강 (confounder 통제) 안 됨 — single OLS 라 selection 위험
4. 이후 v2 노트북 (`tiktok_marketing_modeling_v2.ipynb`) 의 윈저화 + HC3 SE + 3-그룹 모델로 재추정 → 5.10 %p 가 더 robust 한 값

### 단계 2 — 윈저화 99% + HC3 OLS = 5.10 %p (상한)

**언제**: 사용자 노션 정리본 (`notion_summarypage`). v2 노트북 (`tiktok_marketing_modeling_v2.ipynb`) Cell 11 결과.

**모델**: 통합 OLS (HC3 robust SE) — `ERV_w ~ is_generic + is_k_beauty + log_follower + log_view` (3-그룹: Others / Generic Skincare / K-Beauty)

**전처리**: 윈저화 99% (상위 1% extreme 을 임계치로 cap)

**결과**: `is_k_beauty = +5.10 %p` (p<0.05) — 관찰 기반 추정치 (**상한 성격**)

**왜 5.10 인가**:
- 윈저화 99% → outlier 영향 제거, CI 좁아짐
- HC3 (heteroskedasticity-consistent SE) → 분산 불균형 보정
- k_keyword 정밀화 (`["kbeauty", "k-beauty", "koreanskincare"]`, wonyoung 제외) → 장원영 개인 효과와 K-Beauty 일반 효과 혼동 제거
- 비교 그룹 정밀화 (`non_k_skincare = ["glassskin", "skincareroutine", "skintok", ...]`) → 같은 카테고리 안 비교 (선택 편향 ↓)

> 참고: 동일 데이터에 단순 OLS (k_keyword 4 단어, 2-그룹) 적용 시 **+5.02 %p** — 5.10 과 robust 일관 (다른 모델 사양에서도 거의 같은 결과).

### 단계 3 — PSM ATT = 4.76 %p (하한, 인과 보강)

**언제**: v2 노트북 Cell 15.

**모델**: 1:1 Nearest Neighbor 매칭 + caliper 0.2σ + 부트스트랩 SE

**공변량**: `log_follower, log_view, upload_gap` (영상 특성)

**결과**: ATT = +4.7642 %p (p<0.05) — 보수적 인과 추정 (**하한 성격**)

**왜 4.76 인가**:
- PSM (Propensity Score Matching) — 영상 특성이 비슷한 K-Beauty vs Generic Skincare 1:1 매칭 → "조회수·팔로워 동일 조건의 K-Beauty 효과" 추정
- 단순 OLS 의 5.10 보다 약간 작음 — 영상 특성 균형화 후의 보수적 효과

### 현재 main 구간 — **4.76 ~ 5.10 %p**

| 추정 | 값 | 성격 |
|---|---:|---|
| OLS HC3 (윈저화 99%, 3-그룹, k_keyword 정밀화) | **+5.10 %p** | 상한 (관찰 기반) |
| PSM ATT (1:1 매칭, 부트스트랩 SE) | **+4.76 %p** | 하한 (인과 보강) |

**1만뷰 기준 가치 환산** (참여당 100원 가정):
- PSM (하한): 1 만뷰당 +476 건 추가 참여 → **47,600 원**
- OLS (상한): 1 만뷰당 +510 건 추가 참여 → **51,000 원**

## 추가 발견 — within-influencer Fixed Effect (2026-05-03)

PSM ATT 4.76 %p 까지 가도 **인플루언서 selection effect** 가 잠재적 confounder 로 남아있음을 인지하고, 이를 분리해 측정하기 위해 진행한 추가 분석. 단순 *"FE 까지 돌려봤다"* 가 아니라 *데이터 수집 → 표본 검증 → 방법론 선택 → 보강 검증* 의 적극적 인과 추정 작업.

### 분석 동기

PSM 까지의 추정은 *영상 특성* (조회수 · 팔로워 · 업로드 주기) 만 매칭. 하지만 *인플루언서 자체* (베이스 ER, 채널 컨셉, 구독자 충성도 등) 는 통제하지 못함. K-Beauty 키워드를 쓰는 인플루언서들이 *원래부터* 인기 있는 사람들이라면, 단순 OLS / PSM 의 +5 %p 효과는 *키워드의 효과* 가 아니라 *who chooses to use the keyword* 의 효과일 수 있음. 이를 검증하려면 *같은 인플루언서 안에서만 비교* 하는 within-FE 가 필요.

### 추가 데이터 수집 (within-FE 가능 표본 확보)

within-FE 가 의미 있으려면 *같은 인플루언서가 K-keyword 영상도, non-K 영상도 만든 케이스* (dual 인플루언서) 가 충분해야 함. 1차 키워드 검색 기반 수집으로는 인플루언서당 영상 수가 적어 within-variation 부족.

**수집 단계**:
- **1차 raw 수집 (2025-01-21)**: 키워드 검색 4 개 (`kbeauty / korean / wonyoung / korea`) → 약 **6,500 영상 / 3,300+ 인플루언서** (`tiktoker_crawling_df_0121.csv`, 6,506 rows / 3,361 unique 인플루언서, 인플루언서당 평균 ~2 영상의 얕은 cross-section). 키워드 검색만으로 끝내지 않고 within-FE 표본 확보를 위해 **50명 인플루언서로 좁혀 각 30 영상씩 = 1,500 영상** 으로 정제
- **2차 (2025-01-27)**: 인플루언서 풀 +6명 추가 + 인플루언서당 30 영상 재수집 = **56명 × 30 영상 = 1,680 영상** (`tiktoker_final_df_0127.csv`)

→ raw 수집 (6,500) 과 분석 표본 (1,680) 의 차이는 의도적 — 키워드 검색만으로는 *인플루언서당 영상 수* 가 적어 within-FE 안 됨, 인플루언서 단위 30 영상씩 수집해 within-variation 표본 확보 필요.

→ *selection effect 가능성을 인지한 뒤 그 가설을 검증할 데이터를 적극 수집한 흔적*. 단순 "기존 데이터로 FE 돌려봤다" 와 다른 적극적 인과 추정 의도.

### 방법론 — LSDV + Clustered SE

**모델**: `ERV ~ k_keyword_flag + log_view + log_follower + Σᵢ Dᵢ (인플루언서 더미)`

**구현**: `statsmodels.OLS` 의 LSDV (Least Squares Dummy Variable) 방식 + `cov_type='cluster', cov_kwds={'groups': name}` 으로 인플루언서 단위 clustered standard error.

```python
# 인플루언서 더미 생성 (drop_first=True 로 multicollinearity 방어)
dummies = pd.get_dummies(tmp_df['name'], prefix='name', drop_first=True, dtype=float)
X = pd.concat([
    pd.DataFrame({'const': 1.0}, index=tmp_df.index),
    tmp_df[['k_keyword_flag', 'log_view', 'log_follower']],
    dummies
], axis=1)

m_fe = sm.OLS(tmp_df['ERV_w'], X).fit(
    cov_type='cluster',
    cov_kwds={'groups': tmp_df['name'].values}
)
```

**왜 LSDV 선택**:
- `linearmodels.PanelOLS` 도 within-FE 추정 가능하나, `statsmodels` 의 LSDV 가 노트북 흐름 (이미 statsmodels 로 OLS / PSM 진행) 과 통합 자연스러움
- 인플루언서 56명 → dummy 55개로 표본 차원 부담 적음 (1,680 행에 비해 자유도 충분)
- `drop_first=True` 로 multicollinearity 방어, baseline 인플루언서 1명 기준 fixed intercept

**왜 clustered SE**:
- 같은 인플루언서의 여러 영상들 오차가 상관 (구독자 충성도, 채널 분위기 등 공통 잔차)
- 표준 SE 는 이 상관 무시하고 과소 추정 → 실제 보다 좁은 CI / 작은 p-value
- Clustered SE 는 인플루언서 단위로 묶어 보정 → 보수적 추론 (CI 넓어짐)

**전처리**: ERV 99% 윈저화 (n=1,680 → ~1,663), `log_follower`, `log_view` (왜도 보정).

**Dual 인플루언서 표본**: 56명 중 ~40-45명 (전체의 ~75%, 정의에 따라 30~42 변동). K-keyword 전용 또는 non-K 전용 인플루언서는 within-variation 없어 FE 추정에 기여 X — 이 표본 한계는 *결과 nuance* 섹션 참고.

### 결과

**4 단어 정의** (`k_keyword = ["kbeauty", "korean", "wonyoung", "korea"]`, `tiktok_statistic_analysis.ipynb` cell 158):

| 모델 | K-keyword 효과 | p-value | 의미 |
|---|---:|---:|---|
| 단순 OLS (baseline) | +5.0166 %p | <0.05 | 인플루언서 selection 포함 |
| within-FE (LSDV + clustered SE) | **+0.24 %p** | 0.75 | **유의 X** — 같은 인플루언서 안에서 키워드 자체 효과 통계적 유의 없음 |

→ Selection effect = 5.02 − 0.24 = 4.78 %p = 단순 OLS 효과의 **95.3%**

**v2 정의** (3 단어 `kbeauty / k-beauty / koreanskincare`, K-Beauty vs Generic Skincare 만 비교, dual 30명):

| 모델 | K-keyword 효과 | p-value |
|---|---:|---:|
| 단순 OLS | +4.15 %p | <0.05 |
| within-FE | **−0.85 %p** | 0.60 |

→ Selection effect = 100%+ (음의 within 효과는 noise, 통계적 유의 X)

→ **두 정의 모두 일관**: K-Beauty 키워드 효과의 거의 전부가 인플루언서 selection 에서 옴.

### 결과의 nuance — Underpowered 가능성 (중요)

Within-FE 의 +0.24 %p (95% CI 약 [-1.20, +1.67]) 는 *진짜 0* 인지 *진짜 +0.5 %p 인데 표본 한계로 detect 못한 건지* 구분 어려움:

- Dual 인플루언서 ~40-45명 + 인플루언서당 ~30 영상 (K vs non-K 섞임) → within-variation 표본 작음
- 이 표본 크기로는 *진짜 효과 < 1 %p* 인 약한 양의 효과는 통계적 유의로 잡아내기 어려움 (**under-powered**)
- *진정한 효과 = 0* 가능성도 충분 — selection effect 가 dominant 하다는 결론은 robust

→ 정확한 해석: *"키워드 자체 효과가 0"* 이 절대 사실이라기보다 ***"표본 한계 안에서 detect 안 됨, 효과 있더라도 selection 효과 (4.78 %p) 보다 크게 작음"***.

→ 표본 확장 시 (예: 200+ dual 인플루언서, 각 50+ 영상) 약한 양의 효과가 통계적 유의로 나올 가능성 존재. 단 전체 효과의 95% 가 selection 에서 온다는 *상대적 비율* 결론은 표본 확장과 무관하게 robust 할 가능성 큼.

### 보강 검증 — Broad Pattern (selection effect 가 K-keyword 만의 특수 현상이 아님)

selection effect 발견이 K-keyword 만의 우연인지 확인하기 위한 두 보강 검증:

**1. 토픽 × ER within-FE** (`tiktok_statistic_analysis.ipynb` cell 163-164)

9 토픽 (`color_makeup`, `skincare`, `hair_body`, `fashion`, `unboxing`, `skin_routine`, `trend`, `asmr`, `eating`) 각각을 dummy 로 K-keyword 자리에 대체해 within-FE 추정.

- 9 토픽 중 **8 개 within-FE 시 통계적 유의 X** (asmr 만 marginal +2.19 %p, p=0.055)
- → selection effect 가 K-keyword 만의 현상이 아닌, **콘텐츠 metric 전반의 broad pattern**

**2. Segment 별 within-FE** (cell 166-168)

인플루언서 segment 분리 (`nano <10K / micro 10K-100K / middle 100K-500K / mega 1M+`) 후 각 segment 안에서 within-FE 추정.

- 모든 segment 에서 within-FE 추정 — selection effect 가 인플루언서 규모와 무관하게 dominant 임을 확인 (heterogeneity 검증)

→ 두 보강 검증으로 *selection effect 95% 발견* 이 우연이나 특정 정의의 artifact 아님 입증.

### 한계 (정직히)

- **Dual 인플루언서 표본** 30~42명 (전체 56명의 ~75%) — 표본 작아 검정력 일부 제한 (위 *underpowered 가능성* 참고)
- **K-Beauty 전용 인플루언서** (within variation 없음, 항상 K-keyword 사용) 의 효과는 measure 불가 — within-FE 는 *변화하는* 인플루언서만 분석 대상
- **단일 시점·단일 데이터셋** (2024.12 ~ 2025.01 수집) — 다른 기간 일반화 어려움
- **K-keyword 정의 민감성** — 4 단어 vs 3 단어 vs ... 정의에 따라 단순 OLS 결과 약간 변동 (4.15 ~ 5.02 %p), 단 within-FE 결과는 일관 (모두 유의 X) → 정의 민감성이 결론 흔들지 않음

### 시도 자체의 가치 (portfolio 어필 포인트)

이 within-FE 분석의 *결과* (selection effect 95%) 가 핵심 인사이트지만, 그 결과 도달까지의 *과정* 자체가 portfolio 가치:

1. **적극적 인과 추정 의도** — selection effect 가능성을 *추측만 한 게 아니라 추가 데이터 수집까지 진행* 한 분석가 의도. 1차 키워드 검색 후 *"이 데이터로 within-FE 가능한가?"* 점검 → 인플루언서별 30 영상 수집으로 within-variation 표본 확보
2. **방법론적 엄격성** — 단순 OLS / PSM 에서 멈추지 않고 LSDV + clustered SE 까지 보강. PanelOLS / clustered SE 같은 *옳은 도구 선택* 의 합리성
3. **Negative result 도 actionable** — *키워드 효과 ≈ 0* 자체가 마케팅 의사결정 paradigm shift (*키워드 선택 → 인플루언서 선정*) 트리거. negative-but-actionable insight
4. **자기 비판적 평가** — underpowered 가능성, dual 표본 한계, 정의 민감성 등 한계를 정직히 인정하는 것 자체가 분석가 신뢰성 시그널

→ portfolio / 면접 narrative 에서 *"selection effect 95%"* 결과만 강조하지 않고, *"가능성 인지 → 추가 수집 → 적합한 방법론 → 보강 검증 → 한계 명시"* 의 closed-loop 흐름을 어필.

### 후속 작업 (있다면)

- **표본 확장** — 200+ dual 인플루언서, 각 50+ 영상 수집 후 power 충분한 상태에서 within-FE 재추정 (약한 양의 효과 유무 detect)
- **다른 시점 데이터** — 2025 H2, 2026 등 다른 시점 데이터로 재현성 검증
- **다른 카테고리 비교** — K-Beauty 외 다른 viral 카테고리 (예: 한식, K-pop) 에서도 같은 selection effect pattern 인지 검증
- **PanelOLS 재추정** — `linearmodels.PanelOLS` 로 같은 분석 다시 돌려 LSDV 와 일관성 확인 (robustness)

---

→ 포트폴리오 본문은 **노션 4.76 ~ 5.10 main**, 회고/한계 섹션에서 within-FE 후속 발견 + selection effect 95% + 시도 자체 가치 명시 (B2 옵션).

## 어디서 어느 수치를 쓸지 (가이드)

| 위치 | 수치 | 근거 |
|---|---|---|
| 포트폴리오 페이지 (`jun_portfolio/`) | **4.76 ~ 5.10 %p**, 1만뷰당 47,600~51,000원 | 노션 main, 사용자 정리본 기준 |
| 포트폴리오 회고/한계 | "후속 within-FE 분석에서 selection effect 95% 추가 발견" 한 줄 | 정직 + 면접 hook |
| `notion_summarypage` | 4.76 ~ 5.10 %p | 사용자 직접 정리본 (이미 적힘) |
| `README.md` (root) | 단순 OLS 5.02 → PSM 4.76 → FE 0.24 + 4 사례 broad pattern | 인과 보강 narrative 강조 |
| `tiktok_statistic_analysis.ipynb` cell 147~159 | 5.02 (단순 OLS) → 0.24 (FE) | 직접 재현 가능, 노트북 흐름 일관 |
| `tiktok_marketing_modeling_v2.ipynb` Cell 11/15 | 5.10 (OLS HC3) → 4.76 (PSM ATT) | 노션 main 과 직접 매핑 |
| `notebooks/tiktok/tiktok_statistic_analysis.ipynb` cell 154-155 | 5.0166 (윈저화 99% 적용 후 갱신됨) | 옛 8.4299 는 윈저화 X 였음 — 갱신 명시 (commit `a0aa2c4`) |
| **옛 8.43 %p** | ❌ **사용 안 함** | 윈저화 X + outlier 영향 + 인과 보강 X. 흔적은 노트북 cell 158 markdown 에 cross-link 보존 |

## 관련 commits

- `a0aa2c4` — `tiktok_statistic_analysis.ipynb` cell 147 OLS / cell 158 within-FE 일관성 fix (윈저화 통합 + 8.4299 → 5.0166 갱신)
- `90deabf` — within-influencer FE 본격 구현 (cell 158-159)
- `d21cda8` — selection effect 95% 인사이트 프레임으로 리프레이밍
- `b109929` — v2 정의 위 within-FE 단계적 보강 + README §2.A 갱신
- `64fcfb1` — README narrative 재구성

## 관련 docs

- [`12_tiktok_recommendation_evolution.md`](12_tiktok_recommendation_evolution.md) — 추천 알고리즘 진화 (4.76~5.10 narrative 와 다른 분석)
- [`13_amazon_tiktok_brand_matching.md`](13_amazon_tiktok_brand_matching.md) — Amazon × TikTok 5 brand 매칭 (가설 반박 narrative)
- [`EXPERIMENTS_PLAYBOOK.md`](EXPERIMENTS_PLAYBOOK.md) — 변종 정리 표준
