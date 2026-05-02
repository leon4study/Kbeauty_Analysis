# K-Beauty 미국 시장 분석 및 데이터 파이프라인 (Kbeauty_Analysis)

Amazon 의 고객 리뷰(정성)와 TikTok 의 인플루언서 반응(정량/행동)을 통합 분석하여, 데이터 기반의 미국 시장 진출 전략 및 인플루언서 마케팅 효율을 도출한 엔드투엔드(End-to-End) 데이터 파이프라인 프로젝트입니다.

---

## 1. 프로젝트 목적 (Problem Definition)

1. **시장 분석**: 미국 Amazon 내 K-Beauty 제품에 대한 실제 소비자 반응과 핵심 키워드 파악을 통한 시장 경쟁력 진단.
2. **효율 측정**: TikTok 콘텐츠 반응(조회/참여)이 실제 마케팅 가치로 연결되는 구조를 통계적으로 분석.
3. **의사결정 지원**: 인플루언서 시딩(Seeding) 대상을 데이터 기반으로 자동 선별하고 마케팅 소구점을 제안하는 로직 구축.

---

## 2. 핵심 분석 성과 (Key Insights)

### Causal Robustness 분석 — selection effect 95% 발견 → "인플루언서 선정 > 키워드 선택"

처음에 단순 회귀로 추정한 K-Beauty 키워드 효과를 단계적으로 인과 보강한 결과, **마케팅 의사결정의 핵심 레버를 키워드 → 인플루언서 선정으로 옮기는 인사이트** 도출:

| 추정 단계 | 모델 | K-Premium 계수 | p-value | 해석 |
|---|---|---:|---:|---|
| ① 영상 단위 OLS | `ERV ~ k_keyword + log_view + log_follower` | +5.0166 %p | <0.0001 ✅ | 일반적으로 보고되는 효과 — 단, 인플루언서 selection 포함 |
| ② PSM ATT (1:1 매칭) | 영상 특성 매칭 후 ATT 추정 | +4.7642 %p | <0.01 ✅ | 영상 단위 인과 보강 — 인플루언서 selection 은 미통제 |
| ③ **+ 인플루언서 Fixed Effect** | LSDV + clustered SE (인플루언서별 dummy) | **+0.2363 %p** | 0.7464 | **같은 인플루언서 내 효과 ≈ 0** (95% CI [-1.20, 1.67]) |
| ④ Paired t-test (dual 42명) | 보조 검증 — within 평균 비교 | +0.5569 %p | 0.4862 | ③ 과 동일 결론 |

**🔍 발견된 인사이트**: 단순 OLS 의 5.02 %p 중 **4.78 %p (95.3%) 가 인플루언서 selection effect** — 즉, K-beauty 키워드를 쓰는 인플루언서들이 *원래부터* ERV 가 높은 인플루언서들이고, 키워드 자체의 추가 효과는 거의 0.

**📈 selection effect 의 일반성 — broad pattern 입증**:
같은 분석을 9개 토픽 (skincare, asmr, color_makeup 등) 에 적용 → 동일 패턴 발견. 단순 평균 비교에서 보이던 토픽 간 ERV 차이 (asmr 19.13 vs eating 12.19, 약 7%p) 의 **대부분이 within-influencer 통제 시 사라짐** (8개 중 7개 통계적 유의 X, asmr 만 +2.19 marginal p=0.055). → K-keyword 가 아닌 **콘텐츠 metric 전반에서 인플루언서 selection 이 핵심 결정 요인**임. ([cell 160-162](./notebooks/tiktok/tiktok_statistic_analysis.ipynb))

**🔄 Amazon × TikTok 통합 매칭 — 또 다른 가설 반박**:
본 프로젝트의 핵심 가치 (Amazon 정성 + TikTok 행동 통합) 를 5 K-Beauty 브랜드 매칭으로 검증. 결과: **"TikTok 화제 → Amazon 매출" 가설 반박** — TikTok 총 view ↔ Amazon 인기도 = **Spearman -0.80** (음의 상관). 패턴: **established 브랜드 (COSRX, Amazon 324K rating count) 는 TikTok 의존 ↓, 신생/성장 브랜드 (PURITO, TikTok 18 영상 281만 view) 는 TikTok 활발**. → "TikTok 마케팅 효과 = 신생/성장 브랜드에서 큼" 의 단계별 차별 전략 시사. n=5 한계는 정직히 명시. 자세히는 [docs/refactor/13](./docs/refactor/13_amazon_tiktok_brand_matching.md).

**왜 중요한가** — 인과 추론 단계 없이 ① 만 봤다면 잘못된 마케팅 결론 도출:
- ❌ ① 만 보고 결론: "K-beauty 키워드 추가 → ERV +5 %p, 1 만뷰당 47,642 원 가치" (옛 README)
- ✅ ③ 까지 가서 도출한 결론: **"K-beauty 키워드 추가 효과는 통계적으로 유의하지 않음. 진짜 효과는 인플루언서 선정에서 나온다"**

**비즈니스 시사점 (인과적으로 정확한 버전)**:
- 🎯 **인플루언서 선정 > 키워드 선택**: 마케팅 예산 배분 시 *어떤 인플루언서를 쓸지* 가 *어떤 키워드를 쓸지* 보다 훨씬 중요
- 🎯 **K-beauty 키워드 사용 인플루언서들의 베이스 ERV 가 높은 이유** 가 진짜 분석 대상 — 채널 컨셉, 팔로워 충성도, 콘텐츠 일관성 등
- 🎯 **시딩 추천 알고리즘** ([`tiktoker_recommend.ipynb`](./notebooks/tiktok/tiktoker_recommend.ipynb), [`docs/refactor/12`](./docs/refactor/12_tiktok_recommendation_evolution.md)) 의 가치 정량 입증 — **ver.3 Top-10 추천 시 무작위 대비 2.32배 ER%** (97.7 percentile, 10000 부트스트랩). selection effect 인사이트와 솔루션의 정량적 일치

**분석가 가치 측면**:
- 단순 OLS 만 보고 결론 내렸다면 5 %p 효과를 그대로 비즈니스에 권고 → 잘못된 의사결정
- ③ Fixed Effect 까지 진행했기에 selection 과 causal 효과를 분리, 진짜 레버 식별
- 자세한 결과 + 한계: [tiktok_statistic_analysis.ipynb](./notebooks/tiktok/tiktok_statistic_analysis.ipynb) cell idx 158-159

**한계**:
- dual 인플루언서 42명 (전체 56명의 75%) — 검정력 일부 제한
- K-beauty 전용 14명 (within variation 없음) 의 효과는 measure 불가
- 단일 데이터셋 — 다른 기간/집단으로 재현성 검증 필요
- 후속: 인플루언서 segment 별 (nano/micro/middle) FE 효과 + 다른 시점 데이터 재현

### 텍스트 분석 및 지식그래프 구축

- **LDA 토픽 모델링**: 총 22 개 토픽 추출 (피부 자극, 흡수/제형, 광채/사용감, 가성비 등). 전략 의사결정에 핵심적인 6 ~ 8 개 테마를 집중 분석하여 제품 개발 및 마케팅 가이드라인 도출.
- **GraphRAG (지식그래프 + LLM)**: 성분(Ingredients) - 효능 - 부작용 간의 지식그래프를 구축하여 LLM 이 실제 리뷰에 근거한 정교한 답변을 내놓는 프로토타입 구현.

---

## 3. 분석 설계 (왜 이렇게 했나)

- **데이터 성격 차이 (정성 vs 행동)**: 리뷰는 '사용 경험' (심층), TikTok 은 '인지·반응' (광범위). 둘을 **토픽·키워드 단위로 연결** 하여 상호보완적 인사이트를 얻도록 설계.
- **단일 Notebook 유지 이유** (`amazon_tiktok_*` 통합 노트북): 전처리 → 토픽 → 교차분석 과정에서 중간 산출물 (TF-IDF 벡터, LDA 토픽, 토픽별 문서 리스트) 이 반복 참조됨. 분리 시 컨텍스트 손실 + 중복 연산 발생 → 의도적 단일 파일 설계.
- **추천 알고리즘은 점진적 진화**: TF-IDF cosine (v1) → ER% 가중치 (v2) → max(1) 안전장치 (v3) → 회귀분석 가중치 자동 탐색 — 한 노트북 안 셀 단위로 누적. ver.3 의 강점 6가지 (콘텐츠+ER% 결합 / selection effect 인코딩 / 도구 절제력 / MinMax 가중치 안정화 / edge case 방어 / overfitting 완화) + 한계 + 개선 방향은 [docs/refactor/12](./docs/refactor/12_tiktok_recommendation_evolution.md#-ver3-의-강점--왜-이-선택을-했나-깊이-분석).
- **현업과 일관**: ver.3 의 ER% 가중치는 selection effect 발견 (위 K-Premium 섹션) 과 동일 방향 — 인플루언서 selection 을 추천 score 에 직접 인코딩. 사용자 직관이 사후 인과 분석으로 검증된 사례.

### GraphRAG 의 차별점

TF-IDF / LDA 는 **통계적 토픽·키워드 가중치** 를 제공하지만, GraphRAG 는 **엔티티 (성분, 효능, 부작용 등) 간 관계** 를 지식그래프로 연결해 LLM 질의응답에 근거를 제공.

> 예: "히알루론산과 함께 쓰기 좋은 성분" 같은 질문에 **리뷰 근거 + 성분 연결 정보** 를 함께 제시하여 실무적 신뢰성 확보.

---

## 4. 기술 스택 및 파이프라인

### 데이터 파이프라인 단계

1. **Collection**: Amazon (Selenium 활용 리뷰 수집) 및 TikTok (해시태그 기반 반자동 수집).
2. **ETL**: `clean_text` → `lemmatize` → `stopword` 제거 → `n-gram` 생성으로 정규화.
3. **Feature Engineering**: ER (팔로워 기반), ERV (조회수 기반), log_view, log_follower 등 통계 분석용 파생 변수.
4. **Analysis**: 통계적 회귀 분석 (OLS, PSM ATT) 및 NLP (LDA, TF-IDF, GraphRAG).
5. **Serving**: MySQL (SQLAlchemy) Upsert 적재 + Slack 실시간 모니터링 연동.

### 상세 설계 문서

- [전체 파이프라인 개요](./docs/pipeline_overview.md)
- [Amazon Crawler 설계](./docs/amazon_crawler.md)
- [TikTok Crawler 및 지표 정의](./docs/tiktok_crawler.md)
- [ETL 및 데이터 적재 프로세스](./docs/etl_pipeline.md)
- [DB 스키마 설계](./docs/db_schema.md)
- [Slack 알림 모듈](./docs/slack_alert.md)

### 정리/리팩터링 history

- [docs/refactor/](./docs/refactor/) — 정리 토픽별 결정 기록 (변종 정리, 경로 포터빌리티, 구조 평면화 등)
- [docs/refactor/EXPERIMENTS_PLAYBOOK.md](./docs/refactor/EXPERIMENTS_PLAYBOOK.md) — 변종 정리 표준 (폴더 우선, 통폐합 패턴, 결정 트리)

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
│   └── amazon_tiktok/            # Amazon × TikTok 결합 통계 분석
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

- **수집 제약**: TikTok 데이터는 플랫폼 보안 (CAPTCHA, 로그인, 계정 행위 제한) 으로 완전 자동화 불가 — 반자동 수집 (수동 세션 관리) 방식 채택.
- **인과 추론**: OLS → PSM ATT → within-influencer Fixed Effect 단계적 보강 완료. **selection effect 95.3% 발견** — 위 "Causal Robustness 분석" 섹션 참고.
- **재현성**: 분석 재현을 위해 `data/` 폴더 내 지정 스키마를 준수하는 CSV 필요, Python 3.10 권장.
- **포터빌리티**: 절대 경로 → `pyproject.toml` + `pip install -e .` 기반 `REPO_ROOT` 패턴. [docs/refactor/02_path_portability.md](./docs/refactor/02_path_portability.md) 참고.

---

## 7. 본인 기여 (담당 역할)

- Amazon 크롤러 설계 및 리뷰 파서 구현
- MySQL 스키마 설계 및 Upsert 로직 구현
- 텍스트 전처리 · TF-IDF 파이프라인 구현
- LDA 토픽 모델링 및 pyLDAvis 시각화 생성
- GraphRAG 프로토타입 (지식그래프 + LLM) 데모 구현
- 분석 통합 (리포트, 대시보드 구성요약)

---

## 8. 향후 계획 (Future Works)

### 완료된 분석
- [x] **within-influencer fixed effect 분석** — K-Premium selection effect 95.3% 발견 ([tiktok_statistic_analysis.ipynb](./notebooks/tiktok/tiktok_statistic_analysis.ipynb) cell 158-159)
- [x] **추천 알고리즘 ver.3 강점/한계 깊이 분석** — 6 강점 + 4 한계 ([docs/refactor/12](./docs/refactor/12_tiktok_recommendation_evolution.md))
- [x] **추천 알고리즘 가치 정량화** — ver.3 **Top-10 추천 시 무작위 대비 2.32배 ER%** (97.7 percentile, 10000 부트스트랩). selection effect 발견 (인플루언서 selection 이 핵심) → 그 selection 을 자동화한 알고리즘이 정량적으로 효과 입증. [tiktoker_recommend.ipynb 끝](./notebooks/tiktok/tiktoker_recommend.ipynb)
- [x] **토픽 × ER within-influencer 분석** — 9 토픽 중 8개 통제 시 통계적 유의 X (asmr 만 +2.19 marginal). selection effect 가 K-keyword 만의 특수 현상이 아닌 **broad pattern** 임을 입증 ([tiktok_statistic_analysis.ipynb cell 160-162](./notebooks/tiktok/tiktok_statistic_analysis.ipynb))
- [x] **Amazon × TikTok 5 브랜드 매칭 분석** — "TikTok 화제 → Amazon 매출" 가설 반박: 음의 상관 (Spearman -0.80). 신생/성장 브랜드는 TikTok 활발 + Amazon 중간, established (COSRX) 는 Amazon 압도 + TikTok 적음. **본 프로젝트의 통합 데이터 활용 핵심 분석**. 자세히는 [docs/refactor/13](./docs/refactor/13_amazon_tiktok_brand_matching.md)

### 후속 분석 (선택)
- [ ] **추천 알고리즘 ver.4** — TF inflation → row-wise vector scaling, `int(round)` 정보 손실 제거
- [ ] selected 인플루언서 변동 시 ver.3 stability 검증
- [ ] 인플루언서 segment (nano/micro/middle) 별 FE 효과 차이
- [ ] 다른 시점/데이터셋으로 K-Premium / selection effect 재현성 검증
- [ ] Amazon × TikTok 매칭 (TikTok 바이럴 → Amazon 매출)

### 엔지니어링
- [ ] 파서 / 클리너 유닛 테스트 (pytest) 추가
- [ ] Dockerfile + docker-compose (개발용 컨테이너)
- [ ] 재현용 샘플 데이터셋 (100 건 내외) 추가 제공
- [ ] `.env.example` 을 통한 환경 변수 관리 표준화
- [ ] amazon_tiktok 변종 6 개 통폐합 ([notebooks/amazon_tiktok/README.md](./notebooks/amazon_tiktok/README.md) 참고)

---

## License

MIT License.
