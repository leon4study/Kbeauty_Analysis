# K-Beauty 미국 시장 분석 및 데이터 파이프라인 (Kbeauty_Analysis)

Amazon 의 고객 리뷰(정성)와 TikTok 의 인플루언서 반응(정량/행동)을 통합 분석하여, 데이터 기반의 미국 시장 진출 전략 및 인플루언서 마케팅 효율을 도출한 엔드투엔드(End-to-End) 데이터 파이프라인 프로젝트입니다.

---

## 1. 프로젝트 목적 (Problem Definition)

1. **시장 분석**: 미국 Amazon 내 K-Beauty 제품에 대한 실제 소비자 반응과 핵심 키워드 파악을 통한 시장 경쟁력 진단.
2. **효율 측정**: TikTok 콘텐츠 반응(조회/참여)이 실제 마케팅 가치로 연결되는 구조를 통계적으로 분석.
3. **의사결정 지원**: 인플루언서 시딩(Seeding) 대상을 데이터 기반으로 자동 선별하고 마케팅 소구점을 제안하는 로직 구축.

---

## 2. 핵심 분석 성과 (Key Insights)

### K-Premium: 단순 OLS 5%p → 인플루언서 통제 시 0.24%p (selection effect 95%)

여러 추정 방법으로 K-beauty 키워드 효과를 검증한 결과 — **인과 추론 보강 단계에서 큰 반전**:

| 모델 | k_keyword_flag 계수 | p-value | 해석 |
|---|---:|---:|---|
| 영상 단위 OLS (단순) | +5.0166 %p | <0.0001 ✅ | 인플루언서 selection 포함 |
| 영상 단위 OLS Full + PSM ATT (보수적, 1:1 매칭) | +4.7642 %p | <0.01 ✅ | 영상 특성만 매칭 — 인플루언서 selection 미통제 |
| **+ 인플루언서 Fixed Effect** (LSDV + clustered SE) | **+0.2363 %p** | 0.7464 ❌ | **유의 X** (95% CI [-1.20, 1.67]) |
| Paired t-test (dual 42명 평균 비교) | +0.5569 %p | 0.4862 ❌ | 보조 검증 — 유의 X |

→ **단순 OLS 의 5%p 효과 중 약 95% (4.78 %p) 가 인플루언서 selection effect**. 같은 인플루언서가 K-beauty / non-K-beauty 영상을 모두 만든 케이스에서 within-비교하면 K-beauty 키워드 자체의 효과는 통계적으로 유의하지 않음.

**비즈니스 시사점 (갱신)**:
- ❌ "K-beauty 키워드 추가하면 ERV +5%p" — within 비교에서는 성립하지 않음
- ✅ **K-beauty 키워드를 쓰는 인플루언서들이 원래부터 ERV 가 높음** — selection effect
- ✅ **인플루언서 선정 > 키워드 선택**: 마케팅 의사결정에서 어떤 인플루언서를 쓸지가 키워드 전략보다 훨씬 중요

**한계 / 다음 단계**:
- dual 인플루언서 42명 (전체 56명의 75%) — 표본 작아 검정력 약할 수 있음
- K-beauty 전용 14명 (within variation 없음) 의 효과는 measure 불가
- 단일 시점·단일 데이터셋 — 다른 기간/집단으로 재현성 검증 필요
- 인플루언서 segment 별 (nano/micro/middle) 차이 검증 후속 단계
- 분석 노트북: [tiktok_statistic_analysis.ipynb](./notebooks/tiktok/tiktok_statistic_analysis.ipynb) cell idx 158-159 (within-influencer FE 결과)

> **이전 README 의 "잠재 8.47억원" 추정은 단순 OLS 기반이었음 → 인플루언서 selection 통제 후에는 효과 자체가 유의하지 않으므로 잠재 가치 추정도 재고됨.** 표본 안 영상 단위 합산 (옛 노트북 Cell 174) 보다 인플루언서 단위 효과 (FE 결과 ≈ 0) 가 인과적으로 더 정확.

### 텍스트 분석 및 지식그래프 구축

- **LDA 토픽 모델링**: 총 22 개 토픽 추출 (피부 자극, 흡수/제형, 광채/사용감, 가성비 등). 전략 의사결정에 핵심적인 6 ~ 8 개 테마를 집중 분석하여 제품 개발 및 마케팅 가이드라인 도출.
- **GraphRAG (지식그래프 + LLM)**: 성분(Ingredients) - 효능 - 부작용 간의 지식그래프를 구축하여 LLM 이 실제 리뷰에 근거한 정교한 답변을 내놓는 프로토타입 구현.

---

## 3. 분석 설계 (왜 이렇게 했나)

- **데이터 성격 차이 (정성 vs 행동)**: 리뷰는 '사용 경험' (심층), TikTok 은 '인지·반응' (광범위). 둘을 **토픽·키워드 단위로 연결** 하여 상호보완적 인사이트를 얻도록 설계.
- **단일 Notebook 유지 이유** (`amazon_tiktok_*` 통합 노트북): 전처리 → 토픽 → 교차분석 과정에서 중간 산출물 (TF-IDF 벡터, LDA 토픽, 토픽별 문서 리스트) 이 반복 참조됨. 분리 시 컨텍스트 손실 + 중복 연산 발생 → 의도적 단일 파일 설계.
- **추천 알고리즘은 점진적 진화**: TF-IDF cosine (v1) → ER% 가중치 (v2) → max(1) 안전장치 (v3) → 회귀분석 가중치 자동 탐색 — 한 노트북 안 셀 단위로 누적. 자세한 진화 흐름은 [docs/refactor/12_tiktok_recommendation_evolution.md](./docs/refactor/12_tiktok_recommendation_evolution.md).

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
- **인과 추론**: OLS 계수만으로는 confounder 통제 부족 → PSM 으로 1:1 매칭 후 ATT 산출. 추가로 within-influencer fixed effect 분석 보강 예정.
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

- [ ] **within-influencer fixed effect 분석** — K-Premium 추정의 인과성 보강 ([Cell 추가 완료, 코드 placeholder 상태](./notebooks/tiktok/tiktok_statistic_analysis.ipynb))
- [ ] 잠재 가치 추정 within-influencer 결과로 갱신
- [ ] 파서 / 클리너 유닛 테스트 (pytest) 추가
- [ ] Dockerfile + docker-compose (개발용 컨테이너)
- [ ] 재현용 샘플 데이터셋 (100 건 내외) 추가 제공
- [ ] `.env.example` 을 통한 환경 변수 관리 표준화
- [ ] amazon_tiktok 변종 6 개 통폐합 ([notebooks/amazon_tiktok/README.md](./notebooks/amazon_tiktok/README.md) 참고)

---

## License

MIT License.
