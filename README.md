# K-Beauty 미국 시장 분석 및 데이터 파이프라인 (Kbeauty_Analysis)

Amazon의 고객 리뷰(정성)와 TikTok의 인플루언서 반응(정량)을 통합 분석하여, 데이터 기반의 미국 시장 진출 전략 및 인플루언서 마케팅 효율을 도출한 엔드투엔드(End-to-End) 데이터 파이프라인 프로젝트입니다.

---

## 1. 프로젝트 목적 (Problem Definition)

1. **시장 분석**: 미국 Amazon 내 K-Beauty 제품에 대한 실제 소비자 반응과 핵심 키워드 파악을 통한 시장 경쟁력 진단.
2. **효율 측정**: TikTok 콘텐츠 반응(조회/참여)이 실제 마케팅 가치로 연결되는 구조를 통계적으로 분석.
3. **의사결정 지원**: 인플루언서 시딩(Seeding) 대상을 데이터 기반으로 자동 선별하고 마케팅 소구점을 제안하는 로직 구축.

---

## 2. 핵심 분석 성과 (Key Insights)

### K-Premium: 일반 화장품 대비 +8%의 추가 반응률 산출

- **K-Beauty 프리미엄 확인**: 회귀 분석 결과, 일반 스킨케어(Generic Skincare) 콘텐츠 대비 K-Beauty 키워드를 사용한 콘텐츠의 조회수 대비 참여율(ERV)이 **약 8%p(+8.03%p)** 유의미하게 높음을 확인().
- **경제적 가치 환산**: 1만 뷰당 **약 800건**의 추가 참여 발생을 유도하며, 이는 약 **8만 원**의 마케팅 비용 절감 효과(1회 참여당 100원 가정)와 동일함.
- **비즈니스 시사점**: 단순 카테고리 효과를 넘어 'K-Beauty'라는 브랜드 정체성 자체가 탐색 유저의 반응을 이끌어내는 독립적인 트리거임을 입증함.

### 텍스트 분석 및 지식그래프 구축

- **LDA 토픽 모델링**: 총 22개 토픽 추출(피부 자극, 흡수/제형, 광채/사용감, 가성비 등). 전략 의사결정에 핵심적인 6~8개 테마를 집중 분석하여 제품 개발 및 마케팅 가이드라인 도출.
- **GraphRAG 활용**: 성분(Ingredients)-효능-부작용 간의 지식그래프를 구축하여 LLM이 실제 리뷰에 근거한 정교한 답변을 내놓는 프로토타입 구현.

---

## 3. 기술 스택 및 파이프라인 구조

### 데이터 파이프라인 단계

1. **Collection**: Amazon(Selenium 활용 리뷰 6천 건 이상 수집) 및 TikTok(해시태그 기반 반자동 수집).
2. **ETL**: `clean_text` → `lemmatize` → `stopword` 제거 및 `n-gram` 생성을 통한 데이터 정규화.
3. **Engineering**: ER(팔로워 기반), ERV(조회수 기반), log_view 등 통계 분석용 파생 변수 생성.
4. **Analysis**: 통계적 회귀 분석(OLS) 및 NLP(LDA, TF-IDF, GraphRAG).
5. **Serving**: MySQL(SQLAlchemy) Upsert 적재를 통한 데이터 최신성 유지 및 Slack 실시간 모니터링 연동.

### 상세 설계 문서

- [전체 파이프라인 개요](./docs/pipeline_overview.md)
- [Amazon Crawler 설계](./docs/amazon_crawler.md)
- [TikTok Crawler 및 지표 정의](./docs/tiktok_crawler.md)
- [ETL 및 데이터 적재 프로세스](./docs/etl_pipeline.md)
- [DB 스키마 설계](./docs/db_schema.md)
- [Slack 알림 모듈](./docs/slack_alert.md)

---

## 4. 프로젝트 구조 (Repository Structure)

```text
Kbeauty_Analysis/
├── src/
│   ├── amazon_review_crawler/   # Amazon 크롤링 및 파서 모듈
│   └── graphRAG_gradio/        # 리뷰 기반 GraphRAG 데모 (지식그래프+LLM)
├── notebooks/
│   ├── EDA.ipynb               # 기초 탐색적 데이터 분석
│   └── amazon_tiktok_analysis.ipynb # 통합 통계 분석 메인 노트북
├── data/                       # 데이터 샘플 (Amazon/TikTok)
├── docs/                       # 상세 설계 및 기술 문서
├── README.md
└── requirements.txt

```

> **Note**: `src/reviews.py`의 전처리 로직을 `notebooks`에서 호출하여 분석 컨텍스트 손실을 방지하고 코드 재사용성을 극대화함.

---

## 5. 제약 사항 및 재현성

- **수집 제약**: TikTok 데이터는 플랫폼 보안(CAPTCHA) 정책으로 인해 완전 자동화가 아닌 반자동 수집(수동 세션 관리) 방식을 채택함.
- **재현성**: 분석 결과 재현을 위해 `data/` 폴더 내 지정된 스키마를 준수하는 CSV 파일이 필요하며, Python 3.10 환경을 권장함.

---

## 6. 향후 계획 (Future Works)

- [ ] 파서(Parser) 및 클리너(Cleaner) 유닛 테스트(pytest) 추가
- [ ] 분석 환경 컨테이너화를 위한 Dockerfile 작성
- [ ] 재현용 샘플 데이터셋(100건 내외) 추가 제공
- [ ] .env.example을 통한 환경 변수 관리 표준화

---

## License

이 프로젝트는 **MIT License**를 따릅니다.
