# K-Beauty 미국 시장 분석 및 데이터 파이프라인 (Kbeauty_Analysis)

Amazon 의 고객 리뷰(정성)와 TikTok 의 인플루언서 반응(정량/행동)을 통합 분석하여, 데이터 기반의 미국 시장 진출 전략 및 인플루언서 마케팅 효율을 도출한 엔드투엔드(End-to-End) 데이터 파이프라인 프로젝트입니다.

> **3-line 요약**:
> 단순 OLS 가 보여준 "K-beauty 키워드 +5%p ERV" 효과의 **95%가 인플루언서 selection effect** 임을 인과 추론 (PSM → Fixed Effect) 으로 발견. 같은 패턴이 토픽·Amazon×TikTok·시계열에서도 반복 (단순 분석의 함정 4 사례) → **마케팅 핵심 레버를 키워드 → 인플루언서 선정으로 이동**. 그 selection 자동화 알고리즘을 ver.1 → ver.4 자기 비판적 진화 + 정량 검증.

---

## 1. 프로젝트 목적 (Problem Definition)

1. **시장 분석**: 미국 Amazon 내 K-Beauty 제품에 대한 실제 소비자 반응과 핵심 키워드 파악을 통한 시장 경쟁력 진단.
2. **효율 측정**: TikTok 콘텐츠 반응(조회/참여)이 실제 마케팅 가치로 연결되는 구조를 통계적으로 분석.
3. **의사결정 지원**: 인플루언서 시딩(Seeding) 대상을 데이터 기반으로 자동 선별하고 마케팅 소구점을 제안하는 로직 구축.

---

## 2. 핵심 분석 성과 (Key Insights)

### A. K-Premium Causal Robustness — selection effect 95% 발견

처음에 단순 회귀로 추정한 K-Beauty 키워드 효과를 단계적으로 인과 보강 → **마케팅 의사결정의 핵심 레버를 키워드 → 인플루언서 선정으로 이동**:

| 추정 단계 | 모델 (v2 정의: 3-그룹 K-Beauty / Generic Skincare / Others, 윈저 cap) | K-Premium | p-value | 해석 |
|---|---|---:|---:|---|
| ① OLS Full | `ERV_w ~ is_generic + is_k_beauty + log_*` (incremental = K − Generic) | +4.859 %p | <0.001 ✅ | 일반 회귀 — 인플루언서 selection 포함 |
| ② PSM ATT (1:1 매칭) | 영상 특성 (`log_follower, log_view, upload_gap`) 매칭 후 ATT | +4.764 %p | <0.01 ✅ | 영상 단위 인과 보강 — 인플루언서 selection 미통제 |
| ③ **+ 인플루언서 Fixed Effect** (K-Beauty vs Generic Skincare, dual 30명) | LSDV + clustered SE | **−0.849 %p** | 0.60 | **인플루언서 통제 시 효과 사라짐** (음수, 유의 X). selection effect ~100%+ |

→ **PSM 으로 영상 특성 매칭해도 selection effect 잡지 못함** — 인플루언서 고유 특성 (베이스 ER, 채널 컨셉) 통제하는 within-influencer FE 가 가장 robust 한 인과 추정.

**🔍 broad pattern — 다른 group 정의에서도 같은 결론**:

| Group 정의 | 단순 OLS | within-FE | selection % |
|---|---:|---:|---:|
| **v2 정의** (3 단어 `kbeauty/k-beauty/koreanskincare` + non_k_skincare 비교 그룹, K-Beauty vs Generic Skincare) | +4.15 %p | **−0.85 %p** | **100%+** |
| **4 단어** (`kbeauty/korean/wonyoung/korea`, K-keyword vs others, trim winsorize) | +5.02 %p | **+0.24 %p** | **95.3%** |
| Paired t-test (4 단어 dual 42명, within 평균) | — | +0.56 %p (p=0.49) | — |

→ group 정의 / winsorize 방식 무관 **single OLS ~5%p → FE 통제 시 ≈ 0** 패턴 robust.

> 단순 OLS 만 보고 "K-beauty 키워드 추가 → ERV +5%p, 1만뷰당 47,642원" 결론 냈다면 잘못된 마케팅 의사결정. ③ Fixed Effect 까지 진행해서 selection 과 causal 효과 분리 → 진짜 레버 식별.

### B. "단순 분석의 함정" 4 사례 — Robustness 다각 검증

selection effect 발견 (사례 ①) 이 우연이 아니라 **broad pattern** 임을 3 개 추가 분석으로 입증:

| 사례 | 단순 분석 결론 | 보강 후 진실 | 발견 |
|---|---|---|---|
| **① Cross-sectional OLS vs FE** (메인) | K-keyword +5%p ✅ | within-influencer 0.24%p ❌ | selection effect 95% |
| **② 토픽 × ER** | asmr 19.13 vs eating 12.19 (7%p 차이) | 9 토픽 중 8 개 within-FE 시 통계적 유의 X (asmr 만 +2.19 marginal) | selection effect 가 K-keyword 만의 현상이 아닌 콘텐츠 metric 전반의 broad pattern |
| **③ Amazon × TikTok 5-brand 매칭** | "TikTok 화제 → Amazon 매출" (가설) | TikTok 총 view ↔ Amazon 인기도 = **Spearman -0.80** | established (COSRX, 324K rating) 는 TikTok 의존 ↓, 신생/성장 (PURITO, 281만 view) 가 TikTok 활발 → segment 차별 전략 시사 |
| **④ 시계열 lag (30 개월)** | "TikTok → Amazon" 인과 (원본 ρ=0.715) | Detrended 후 **lag=-3 의 ρ=0.79 최대** (Amazon 이 TikTok 3 개월 선행). FD 도 lag=-1 의 ρ=0.47 만 유의 | **인과 방향 정반대** — Amazon leading indicator. 시간 trend 가 spurious correlation 만든 사례 |

→ 4 사례 모두 단순 분석 → 보강 → 결론 뒤집힘 패턴. 분석가 가치는 단순 결과를 신뢰하지 않고 다각 검증한 데서 나옴.

### C. Segment heterogeneity — 평균 95% 뒤의 다른 패턴

selection effect 95% 가 모든 segment 에서 동일한가? 팔로워 규모별 분해:

| Segment | 비중 | selection 비율 | 콘텐츠 효과 (FE) | 마케팅 시사 |
|---|---:|---:|---|---|
| micro (10K-100K) + middle (100K-500K) | 78% | **90-100%** | 0 (유의 X) | 인플루언서 선정 캠페인 |
| mega (>1M) | — | 17% | +0.83%p (p<0.001, 작음) | ROI 작아 키워드 캠페인 가치 낮음 |
| nano (<10K) | — | — | +5.31%p (p<0.001, n_dual=3 한계) | 키워드 캠페인 가능성 (검증 필요) |

→ **평균 뒤 segment-specific heterogeneity**. 단일 마케팅 전략이 아닌 **segment 차별 전략** 도출.

### D. 솔루션 — 추천 알고리즘 ver.1 → ver.4 closed loop

selection effect 95% 발견 → 인플루언서 selection 자동화 알고리즘 가치 확인. 그 알고리즘을 자기 비판 → 개선 → 검증의 closed loop 으로 진화:

| 단계 | 내용 | 결과 |
|---|---|---|
| ver.1 → ver.3 | TF-IDF cosine + ER% 가중치 + max(1) 안전장치. 6 강점 분석 ([docs/refactor/12](./docs/refactor/12_tiktok_recommendation_evolution.md)) | 단일 selected (`krystallee2222, emchu_`) Top-10 = **2.32× random** (97.7 percentile) |
| **자기 비판 (stability + mechanism 분석)** | 1540 selected pair 모두 테스트 + ER% 가중치 mechanism 정량 측정 | (1) 평균 **1.25× random** (std 6.83) — 단일 결과는 lucky case. (2) Pearson selected-ER ↔ rec-ER = -0.12 → **ER% 가중치 의도대로 작동 X**. (3) `max(1)` 발동률 **84% (no.1) / 91% (no.2) / 96% (no.3)** — normalized_ER 분포 skewed 라 거의 모든 인플루언서 (1,1,1) 가중치 → **ver.3 ≈ ver.2** |
| **개선 ver.4** | TF inflation 제거 + score 단계 ER% 가중치 (`score = sim × (normalized_ER + 0.1)`) | 평균 **3.25× random** (std 4.35), **모든 selected 에서 random 능가 (100%)**, Precision@10 **60%** (vs ver.3 20%) |
| **정량 검증** | Paired t-test (v4 - v3) | **t=122.80, p<0.0001, 평균 +24.06%p** |

→ 자기 비판 → 개선 → 검증의 분석가 closed loop. selection effect 인사이트와 솔루션의 정량적 일치.

### 비즈니스 시사점

- 🎯 **인플루언서 선정 > 키워드 선택** (전 segment 평균)
- 🎯 **Segment 차별 전략** — micro/middle 은 인플루언서 캠페인, nano 는 키워드, mega 는 ROI 작음
- 🎯 **Amazon × TikTok 단계별 전략** — established 는 Amazon 중심, 신생은 TikTok 중심
- 🎯 **추천 알고리즘 ver.4** 로 인플루언서 선정 자동화 (Top-K 추천 = 무작위 대비 3.25× ER%)

### 한계

- dual 인플루언서 42명 (전체 56명의 75%) — 검정력 일부 제한
- K-beauty 전용 14명 (within variation 없음) — 측정 불가
- nano segment n_dual=3 — 검정력 제한
- Amazon×TikTok 매칭 n=5 brand — 일반화 어려움
- 단일 시점·단일 데이터셋 — 다른 기간/집단으로 재현성 검증 필요

### 텍스트 분석 및 지식그래프 (보조)

- **LDA 토픽 모델링**: 22 토픽 추출 (피부 자극, 흡수/제형, 광채/사용감, 가성비 등). 6~8 핵심 테마 집중 분석.
- **GraphRAG (지식그래프 + LLM)**: 성분-효능-부작용 지식그래프로 LLM 답변에 근거 제공.

---

## 3. 분석 설계 (왜 이렇게 했나)

- **데이터 성격 차이 (정성 vs 행동)**: 리뷰 = '사용 경험' (심층), TikTok = '인지·반응' (광범위). 둘을 토픽·키워드 단위로 연결.
- **단일 Notebook 유지 이유** (`amazon_tiktok_*` 통합 노트북): 전처리 → 토픽 → 교차분석 중간 산출물 (TF-IDF 벡터, LDA 토픽, 토픽별 문서 리스트) 반복 참조 → 의도적 단일 파일.
- **인과 추론 단계적 보강 (OLS → PSM → FE)**: 각 단계마다 통제 가능한 confounder 가 다름 → 단계 모두 진행해야 selection 과 causal 효과 분리 가능. 한 단계만 보면 §2.A 의 잘못된 결론 위험.
- **추천 알고리즘 점진적 진화** (한 노트북 안 셀 누적): TF-IDF cosine (v1) → ER% 가중치 (v2) → max(1) (v3) → vector scaling (v4). ver.3 강점 6 + 한계 + ver.4 개선 정량은 [docs/refactor/12](./docs/refactor/12_tiktok_recommendation_evolution.md).
- **현업과 일관**: ver.3 의 ER% 가중치가 selection effect 발견 (사후 검증) 과 동일 방향 — 사용자 직관이 인과 분석으로 검증된 사례.

### GraphRAG 의 차별점

TF-IDF / LDA = 통계적 토픽·키워드 가중치, GraphRAG = 엔티티 (성분, 효능, 부작용) 간 관계 → LLM 답변에 근거. 예: "히알루론산과 함께 쓰기 좋은 성분" 질의 시 리뷰 근거 + 성분 연결 정보 동시 제시.

---

## 4. 기술 스택 및 파이프라인

### 데이터 파이프라인 단계

1. **Collection**: Amazon (Selenium 리뷰 수집) + TikTok (해시태그 기반 반자동).
2. **ETL**: `clean_text` → `lemmatize` → `stopword` → `n-gram`.
3. **Feature Engineering**: ER (팔로워 기반), ERV (조회수 기반), log_view, log_follower 등.
4. **Analysis**: 회귀 (OLS, PSM ATT, LSDV with clustered SE) + NLP (LDA, TF-IDF, GraphRAG).
5. **Serving**: MySQL Upsert + Slack 모니터링.

### 상세 설계 문서

- [전체 파이프라인 개요](./docs/pipeline_overview.md)
- [Amazon Crawler 설계](./docs/amazon_crawler.md)
- [TikTok Crawler 및 지표 정의](./docs/tiktok_crawler.md)
- [ETL 및 데이터 적재 프로세스](./docs/etl_pipeline.md)
- [DB 스키마 설계](./docs/db_schema.md)
- [Slack 알림 모듈](./docs/slack_alert.md)

### 분석 / 정리 history

- [docs/refactor/12](./docs/refactor/12_tiktok_recommendation_evolution.md) — 추천 알고리즘 ver.1 → ver.4 진화 + 6 강점 + 정량 검증
- [docs/refactor/13](./docs/refactor/13_amazon_tiktok_brand_matching.md) — Amazon × TikTok 5 brand 매칭 + 시계열 lag
- [docs/refactor/EXPERIMENTS_PLAYBOOK.md](./docs/refactor/EXPERIMENTS_PLAYBOOK.md) — 변종 정리 표준
- [docs/refactor/](./docs/refactor/) 전체 — 정리 토픽별 결정 기록

---

## 5. 프로젝트 구조 (Repository Structure)

```text
Kbeauty_Analysis/
├── src/
│   ├── amazon_review_crawler/    # Amazon 크롤링·파서·MySQL upsert
│   ├── tiktok_crawler/           # TikTok 반자동 수집
│   ├── rag_chatbot/
│   │   ├── cosmetic_rag_chat/    # 메인 GraphRAG 챗봇 (OpenAI cloud)
│   │   └── ollama/               # 로컬 Ollama RAG 챗봇 (LanceDB + LlamaIndex)
│   ├── team_folder/              # 팀 작업 노트북 모음
│   └── util/                     # slack, repo_paths, data_io, plot 유틸
├── notebooks/
│   ├── EDA.ipynb                 # 기초 탐색
│   ├── lemmatized_full_pipeline.ipynb
│   ├── tiktok/                   # 영상/인플루언서 단위 분석 + 추천 알고리즘
│   └── amazon_tiktok/            # Amazon × TikTok 결합 통계 분석 (main + experiments/)
├── data/
│   ├── amazon/                   # 리뷰·아이템 CSV
│   ├── tiktok/                   # 영상·인플루언서·해시태그 CSV
│   ├── model/                    # GraphRAG 인덱싱 결과 (LanceDB, parquet)
│   ├── results/                  # LDA 시각화 HTML
│   ├── References/               # 참고 PDF
│   └── archive/                  # 제출용 산출물 모음
├── docs/                         # 설계 문서 + refactor history
├── pyproject.toml                # pip install -e . 기반 portable 경로
└── README.md
```

---

## 6. 제약 사항 및 재현성

- **수집 제약**: TikTok 데이터는 플랫폼 보안 (CAPTCHA, 로그인) 으로 완전 자동화 불가 — 반자동 수집 (수동 세션 관리).
- **인과 추론**: OLS → PSM ATT → within-influencer Fixed Effect 단계적 보강 완료. selection effect 95.3% 발견 (§2.A).
- **재현성**: `data/` 지정 스키마 CSV + Python 3.10 권장. 분석 결과는 노트북에 cell 단위로 저장 (실행 시 재현 가능).
- **포터빌리티**: 절대 경로 → `pyproject.toml` + `pip install -e .` 기반 `REPO_ROOT` 패턴 ([docs/refactor/02](./docs/refactor/02_path_portability.md)).

---

## 7. 본인 기여 (담당 역할)

### 인과 추론 / Robustness 분석
- OLS → PSM ATT → within-influencer Fixed Effect 단계적 보강 → **selection effect 95% 발견** (§2.A)
- 다각 검증 4 사례 (토픽, Amazon×TikTok, 시계열 lag) 로 broad pattern 입증 (§2.B)
- Segment heterogeneity 분석 → segment 차별 마케팅 전략 도출 (§2.C)

### 추천 알고리즘
- ver.1 → ver.4 점진적 진화 + 자기 비판적 stability 검증 → 개선 → 정량 검증 closed loop (§2.D)
- 1540 selected pair 비교, paired t-test t=122.8

### 데이터 파이프라인 / 엔지니어링
- Amazon Selenium 크롤러 설계 + 리뷰 파서 구현
- MySQL 스키마 설계 + Upsert 로직
- 텍스트 전처리 · TF-IDF 파이프라인
- LDA 토픽 모델링 + pyLDAvis 시각화

### 연구 / 프로토타입
- GraphRAG (지식그래프 + LLM) 데모 — 성분-효능-부작용 entity 관계 + LLM 답변 근거

---

## 8. 향후 계획 (Future Works)

### 분석 (선택, 외부 데이터 필요)
- [ ] 다른 시점/데이터셋으로 K-Premium / selection effect 재현성 검증
- [ ] Amazon × TikTok 매칭 brand 수 확장 (현재 n=5)
- [ ] 추천 알고리즘 ver.4 selected 의존도 ↓ (rank fusion 등 후속)

### 엔지니어링
- [ ] 파서 / 클리너 유닛 테스트 (pytest) 추가
- [ ] Dockerfile + docker-compose (개발용 컨테이너)
- [ ] 재현용 샘플 데이터셋 (100 건 내외) 추가 제공
- [ ] `.env.example` 환경 변수 관리 표준화

### 정리
- [x] **amazon_tiktok 변종 6 개 통폐합** — main + 발표용은 top-level, 4 진화 흔적은 [`experiments/`](./notebooks/amazon_tiktok/experiments/) 보존 (commit `22d4823`)
- [ ] team_folder 위치 이동 검토 (notebooks/team/ 또는 data/archive/team/)
- [ ] team_folder M/ PPTX 2개 (237MB) data/archive/ 이동 검토

---

## License

MIT License.
