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

본 분석 이후 추가로 진행한 **within-influencer FE 분석** (`tiktok_statistic_analysis.ipynb` cell 158-159 + `tiktok_marketing_modeling_v2.ipynb` 추가 cells):

- 같은 인플루언서가 K-Beauty / non-K-Beauty 영상 모두 만든 케이스에서 within-비교
- LSDV (Least Squares Dummy Variable) + clustered SE 또는 PanelOLS

**결과**:
- 4 단어 정의 (`tiktok_statistic_analysis`): 단순 OLS 5.02 %p → FE **+0.24 %p** (p=0.75, 유의 X) → selection effect **95.3%**
- v2 정의 (3 단어, K-Beauty vs Generic Skincare, dual 30명): 단순 OLS 4.15 %p → FE **−0.85 %p** (p=0.60, 유의 X) → selection effect **100%+**

→ K-Beauty 키워드 효과의 대부분이 **인플루언서 selection effect** 임을 시사. 추가 robustness 검증.

**한계**:
- dual 인플루언서 30~42명 (전체의 75% 정도) — 표본 작아 검정력 일부 제한
- K-Beauty 전용 인플루언서 (within variation 없음) 의 효과는 measure 불가
- 단일 시점·단일 데이터셋

→ 포트폴리오 본문은 **노션 4.76 ~ 5.10 main**, 회고/한계 섹션에서 within-FE 후속 발견 명시 (B2 옵션).

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
