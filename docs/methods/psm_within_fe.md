# [←](../../README.md) PSM + Within-FE — 인과 추정 기법 (TikTok K-Premium 분석 적용)

본 프로젝트의 *TikTok K-Beauty 키워드가 영상 ER (engagement rate) 에 얼마나 영향
주나* 추정에 사용된 두 인과 추정 기법 (PSM, within-influencer FE) 의 *교과서적
설명 + 본 프로젝트 적용 방식 + 한계*. 신규 reviewer 가 코드 보기 전 *방법론
정당성* 파악하는 entry point.

> 📍 **수치 변천 history** (8.43 → 4.76 ~ 5.10 → selection 95%) 는
> [`docs/refactor/14_kpremium_number_history.md`](../refactor/14_kpremium_number_history.md) 별도. 본 docs 는 *기법 자체* 설명 + 본 프로젝트 적용.

## 배경 — 왜 단순 OLS 로 부족?

TikTok 영상 1,680개 × 인플루언서 56명 데이터에서 `ERV ~ k_keyword_flag` 단순
회귀 시 K-keyword 효과 **+5.02 %p (p<0.05)**. 그런데 이 추정에는 두 가지
숨은 confounder:

1. **영상 특성 confounder** — K-keyword 쓰는 영상이 *원래부터* 조회수 많고
   업로드 빈도 다른 영상일 가능성. → **PSM** 으로 매칭
2. **인플루언서 selection confounder** — K-keyword 쓰는 인플루언서가
   *원래부터* 인기 있는 사람일 가능성. → **within-FE** 로 같은 인플루언서 안
   비교

두 기법을 단계적으로 적용해 *진정한 키워드 효과* 분리.

---

## 1. PSM (Propensity Score Matching)

### 개념

두 집단 (treatment / control) 의 *관찰 가능한 특성* (covariates) 분포 가 다르면
단순 비교는 confounded. PSM 은:

1. 각 관측치 i 의 *treatment 받을 확률* (propensity score) **p̂(Xᵢ) = P(T=1 | Xᵢ)** 추정 (보통 logistic regression)
2. propensity score 비슷한 treated–control 짝을 매칭
3. 매칭 짝 간 outcome 차이 평균 = **ATT (Average Treatment effect on the Treated)**

핵심 가정: **conditional independence** — 관찰 가능 X 가 같으면 treatment
배정은 outcome 과 독립 (= 모든 confounder 가 X 에 포함됨).

### 본 프로젝트 적용

| 요소 | 값 | 출처 |
|---|---|---|
| Treatment | `k_keyword_flag` (K-Beauty 키워드 포함 1, 일반 skincare 0) | `tiktok_marketing_modeling_v2.ipynb` Cell 15 |
| Outcome | `ERV_w` (윈저화 99% 적용 engagement rate) | 같음 |
| Covariates | `log_follower, log_view, upload_gap` (영상 특성) | 같음 |
| Matching | **1:1 Nearest Neighbor + caliper 0.2σ** | 보수적 매칭 (caliper 밖 pair drop) |
| SE | Bootstrap (1000 iter) | non-parametric, 표본 작을 때 robust |

### 핵심 수식 (간소화)

```
ATT = E[Y(1) − Y(0) | T=1]
    ≈ (1/N_T) · Σᵢ∈Treated  ( Yᵢ − Y_{m(i)} )
```

`m(i)` = 관측 i 의 매칭된 control (propensity score 가장 가까운 caliper 안).

### 결과

**ATT = +4.76 %p (p<0.05)** — 영상 특성 비슷한 K-Beauty / Generic 비교 시
K-Beauty 가 ER 약 4.76 %p 높음. 단순 OLS (+5.02 %p) 보다 약간 작아짐 — 영상
특성 매칭으로 selection 일부 보정됨.

### PSM 한계 (왜 within-FE 필요했나)

- **관찰 가능한 영상 특성만 매칭** — log_view, log_follower, upload_gap 까지
- **인플루언서 자체의 base ER, 채널 분위기, 구독자 충성도** 는 통제 X
- → K-keyword 쓰는 *인플루언서* 가 원래부터 다르다면 selection 잔존
- 다음 단계 (within-FE) 에서 본격 해소

### 라이브러리 / 참고

- 본 프로젝트는 **직접 구현** (logistic regression + caliper NN) — `psmpy` 같은 wrapper 미사용
- 교과서: Rosenbaum & Rubin (1983) "The Central Role of the Propensity Score..."
- Python wrapper 대안: [`psmpy`](https://github.com/adriennekline/psmpy), [`causalinference`](https://github.com/laurencium/causalinference)

---

## 2. Within-Influencer Fixed Effect (LSDV)

### 개념

같은 entity (여기선 인플루언서) 안에서 *반복 관측* (영상들) 이 있을 때,
entity-level 모든 *시간 불변 confounder* 를 통제하는 방법. *각 entity 마다 고유
intercept (fixed effect αᵢ)* 추정 → 비교는 αᵢ 안에서만 이뤄짐.

**LSDV (Least Squares Dummy Variable)**: entity 마다 dummy 변수 N-1 개
추가해 OLS. 56명 → dummy 55개 → 각 인플루언서마다 고유 base 효과 흡수.

대안:
- **Within-transformation** (demeaning): Yᵢₜ − Ȳᵢ 회귀. 동일 효과, dummy 부담 X
- **PanelOLS** (`linearmodels`): explicit panel API, entity_effects=True

### 본 프로젝트 적용

| 요소 | 값 | 출처 |
|---|---|---|
| Treatment | `k_keyword_flag` | `tiktok_statistic_analysis.ipynb` Cell 158-160 |
| Outcome | `ERV_w` (99% 윈저화) | 같음 |
| Time-varying covariates | `log_view, log_follower` | 같음 |
| Fixed effect | 인플루언서 더미 55개 (`name`, drop_first=True) | 같음 |
| SE | **Clustered (group=name)** | 같은 인플루언서 영상들의 오차 상관 보정 |

### 핵심 수식

```
Y_{it} = αᵢ + β · T_{it} + γ' · X_{it} + εᵢₜ
      = Σⱼ αⱼ · D_{ij} + β · T_{it} + γ' · X_{it} + εᵢₜ
```

- αᵢ: 인플루언서 i 의 고유 intercept (LSDV 로 추정)
- β: 키워드 효과 (within-FE 추정치)
- γ: 시간 가변 covariates 효과 (log_view, log_follower)

### 코드 snippet

```python
import statsmodels.api as sm

# 인플루언서 더미 (drop_first 로 multicollinearity 방어)
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

### 결과

| 모델 | K-keyword 효과 | p | 해석 |
|---|---:|---:|---|
| 단순 OLS (baseline) | **+5.02 %p** | <0.05 | selection 포함 |
| within-FE (LSDV + clustered SE) | **+0.24 %p** | 0.75 | **유의 X** — 같은 인플루언서 안 키워드 자체 효과 0 |

→ **Selection effect = 5.02 − 0.24 = 4.78 %p = 단순 OLS 효과의 95.3%**

### Clustered SE 가 왜 필요

- 같은 인플루언서의 여러 영상 = 오차 상관 (구독자 충성도, 채널 분위기 등 공통 잔차)
- 표준 SE 는 이 상관 무시 → 과소 추정 → CI 좁고 p-value 작게 (false positive 위험)
- **Clustered SE**: 인플루언서 단위 묶어 보정. **CI 넓어짐 / 보수적 추론**.

### within-FE 한계

- **Dual 인플루언서만 분석 대상** — K-Beauty 영상 *과* non-K 영상 둘 다 만든
  사람들 (56명 중 ~40-45명). K-Beauty 전용 인플루언서의 효과는 measure 불가
- **Underpowered 가능성** — 표본 작아 *진짜 효과 < 1 %p* 는 detect 어려움.
  `+0.24 %p, CI [-1.20, +1.67]` 는 *진짜 0* 인지 *진짜 작은 양 (+0.5 %p) 인데
  표본 한계인지* 구분 어려움
- **시간 가변 confounder** 통제 X — 영상별 trend, 시즌 등 (이번 데이터는
  단일 시점 ~1개월 수집이라 큰 문제 X)

### 라이브러리

- **`statsmodels.OLS` + clustered SE** (본 프로젝트 선택) — 노트북 흐름 (PSM, OLS 도 statsmodels) 과 통합 자연스러움
- **`linearmodels.PanelOLS`** (대안) — explicit panel API, `entity_effects=True`,
  더 큰 panel 데이터에 효율적. 본 프로젝트 56명 × 30 영상은 LSDV 로 충분

---

## 3. 두 기법 비교 + 선택 가이드

| 차원 | PSM | Within-FE |
|---|---|---|
| 통제 대상 | 관찰 가능 covariates (영상 특성) | 인플루언서 time-invariant 전부 (관찰 + 미관찰) |
| 가정 | Conditional independence (모든 confounder ∈ X) | Time-invariant unobserved confounder OK |
| 데이터 요구 | Cross-section OK | **Panel 필수 (같은 entity 반복 관측)** |
| 본 프로젝트 효과 | 4.76 %p | 0.24 %p (유의 X) |
| 한계 | 미관찰 confounder | Dual entity 표본만, time-varying confounder X |

**선택 가이드**:
- 같은 entity 반복 관측 *없는* cross-section → PSM (or IV / RDD)
- Panel 데이터 + entity-level unobserved confounder 의심 → **Within-FE 우선**
- 둘 다 가능하면 **단계적 적용** (이 프로젝트처럼 OLS → PSM → FE) — 각 단계에서 어떤 confounder 가 효과를 줄이는지 분리

---

## 4. 본 프로젝트 cross-link

- **수치 변천 history** (8.43 → 4.76~5.10 → 0.24): [`docs/refactor/14_kpremium_number_history.md`](../refactor/14_kpremium_number_history.md)
- **PSM 코드**: `notebooks/tiktok/06_tiktok_marketing_modeling_v2.ipynb` Cell 15
- **Within-FE 코드**: `notebooks/tiktok/07_tiktok_statistic_analysis.ipynb` Cell 158-160
- **보강 검증** (9 토픽 within-FE + segment 별 within-FE): [`refactor/14` §보강](../refactor/14_kpremium_number_history.md#보강-검증--broad-pattern-selection-effect-가-k-keyword-만의-특수-현상이-아님)

## 5. 참고 자료

- Rosenbaum, P. R. & Rubin, D. B. (1983). *The Central Role of the Propensity Score in Observational Studies for Causal Effects*. Biometrika 70(1).
- Wooldridge, J. M. (2010). *Econometric Analysis of Cross Section and Panel Data*. MIT Press. Ch. 10 (Fixed Effects).
- Imbens, G. W. & Rubin, D. B. (2015). *Causal Inference for Statistics, Social, and Biomedical Sciences*. Cambridge. Ch. 12-13 (Matching, Subclassification).
- Cameron, A. C. & Miller, D. L. (2015). *A Practitioner's Guide to Cluster-Robust Inference*. J. of Human Resources 50(2).
