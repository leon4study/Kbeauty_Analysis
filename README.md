# K-Beauty 미국 시장 분석 & 데이터 파이프라인 (Kbeauty_Analysis)

## 한줄 요약

Amazon 리뷰와 TikTok 콘텐츠를 통합 분석하여 제품·마케팅 인사이트와 인플루언서 시딩 로직을 도출한 엔드투엔드 데이터 파이프라인 및 분석 레포지토리.

---

## 핵심 요약

- Amazon 리뷰: 최대 6,000건 크롤링/적재
- TikTok: 해시태그 기반 콘텐츠 수집 및 ER(Engagement Rate) 분석
- 주요 정량 결과: k-beauty 태그 사용 시 ERV +8.43%p(유의) → 1만 뷰당 약 +843건 참여(약 8.43만원 가치) 추정, 표본 기준 전체 잠재 가치 약 15억 원
- 텍스트 분석: TF‑IDF, LDA(토픽 수: 20 ~ 25 권장, 실제 실험에서 22개 사용), GraphRAG 기반 지식그래프 + LLM 응답 프로토타입
- DB: MySQL 기반 정규화(제품/리뷰) + Upsert 처리, Slack 알림으로 배치 상태 모니터링

---

## 문제 정의

1. 미국 Amazon에서 잘 팔리는 K-Beauty 제품과 국내 제품의 소비자 반응 차이는 무엇인가?
2. TikTok의 콘텐츠 반응(조회·참여)이 실제 구매 고려(Amazon)로 이어지는 구조는 어떻게 되는가?
3. 인플루언서 마케팅을 데이터 기반으로 자동화/선별할 수 있는가?

---

## 폴더·파일별 역할

레포 내 파일들이 실제 분석·파이프라인에서 무엇을 하는지 핵심만 정리.

```
src/
├── amazon_review_crawler/
│   ├── main.py           # 크롤링 엔트리: 스크래퍼 실행 제어(파라미터, 로깅)
│   ├── items.py          # 상품 상세 파서 (상품 메타데이터 추출)
│   ├── reviews.py        # 리뷰 파서·정제·초기 feature 생성(clean_text 등)
│   ├── mysql1.py         # MySQL 연결 및 upsert 함수 집합
│   └── old_version_main.py
│
├── graphRAG_gradio/
│   └── graphRAG_gradio.py # GraphRAG 데모: 지식그래프 기반 질의응답 프로토타입
│
└── notebooks/
    ├── EDA.ipynb
    ├── amazon_tiktok_statistic_analysis.ipynb  # 통합 분석 노트북 (주요 분석 흐름, 의도적 단일 파일)
    └── results/
        └── ldavis_prepared_*.html             # LDA 시각화 결과(정적)
```

```
data/
├── amazon/   # 크롤링 결과 CSV/파케이(원시+정제 버전)
└── tiktok/   # 수집된 영상 메타/해시태그/계정 지표 CSV

docs/
- pipeline_overview.md, etl_pipeline.md 등: 설계 문서(아키텍처·스키마·알림)
```

요약: `src/.../reviews.py`에서 텍스트 전처리(번역→정규화→토큰화→lemmatize)에 사용되는 함수들을 `notebooks`에서 그대로 호출하거나 복사해 재사용하며, 중간 산출물(TF‑IDF 벡터, LDA 토픽, 토픽별 문서 리스트)을 노트북 내에서 바로 참조해 교차 분석을 수행한다.

---

## 데이터 파이프라인

1. 수집: Amazon(Selenium) / TikTok(해시태그 기반) → raw CSV/DB 적재
   - 주의: TikTok은 CAPTCHA/수동확인으로 완전 자동화 불가(README에 명시)
2. 정제(ETL): clean_text → lemmatize → stopword 제거 → n-gram 생성
3. 특성 생성: ER, ERV, log_follower, log_view 등 파생변수
4. 분석: TF‑IDF → LDA 토픽 → 토픽별 ER 비교 → 회귀(ERV ~ k_keyword + controls)
5. 제품/마케팅 인사이트 도출: TF‑IDF 및 LDA 결과로 강·약점 도출, GraphRAG로 근거 제시
6. 운영: MySQL upsert, Slack 알림(성공/실패), 결과 시각화는 Tableau/HTML export

---

## 분석 설계

- 데이터 성격 차이(정성 vs 행동)을 고려: 리뷰는 ‘사용 경험’, TikTok은 ‘인지·반응’. 둘을 토픽·키워드 단위로 연결하여 상호보완적 인사이트를 얻도록 설계.
- 단일 Notebook 유지 이유: 전처리·토픽·교차분석 과정에서 중간 산출물이 반복 참조되므로, 분리 시 컨텍스트 손실과 중복 연산 발생.

---

## 핵심 결과 요약

- LDA 토픽(예시): `피부 자극( redness / irritation )`, `흡수/제형( sticky / texture )`, `광채/사용감( glow / smooth )`, `가격/가성비( price )` 등으로 군집화 — 총 20 ~ 25 토픽 중 핵심 6 ~ 8개가 전략 의사결정 핵심
- 회귀(ERV 기준): `k_beauty` 태그 사용 계수 +8.43%p (p < 0.01) — 실무적으로는 1만뷰당 약 +843건 참여 → 약 8.43만원 가치로 환산(보수적 가정 하)
- 재현성 범위: 분석-모델링 재현 가능(노트북 기반), 원시 데이터 수집은 플랫폼 제약으로 수동 개입 필요 — README에 반복적으로 명시

---

## GraphRAG의 역할

- TF‑IDF/LDA는 통계적 토픽·키워드 가중치를 제공하지만, GraphRAG는 엔티티(성분, 효능, 부작용 등) 간 관계를 지식그래프로 연결해 LLM 질의응답에 근거를 제공함.
- 사용 사례: "히알루론산과 함께 쓰기 좋은 성분" 같은 질문에 리뷰 근거 + 성분연결 정보를 함께 제시하여 실무적 신뢰성 확보.

---

## 재현성·제약

- TikTok 수집은 반자동: CAPTCHA, 로그인, 계정 행위 제한 등으로 완전 자동화 불가.
- 데이터 스키마·샘플 필요: 분석 재현을 위해 `data/amazon/*.csv`, `data/tiktok/*.csv`의 동일 스키마 파일이 필요. 노트북 상단에 요구형식 표기됨.
- 환경/의존성: Python 3.10 권장, 주요 라이브러리( pandas, scikit‑learn, gensim, statsmodels, sqlalchemy ) — `requirements.txt`가 있으면 재현성↑(권장).

---

## 추후 작업

- [ ] `requirements.txt` 및 `.env.example` 추가
- [ ] `docs/db_schema.md`에 SQL DDL 추가
- [ ] 간단한 유닛테스트(pytest)로 parser/cleaner 검증
- [ ] Dockerfile + docker-compose (개발용 이미지)
- [ ] data schema 예시 CSV(샘플 10~100건) 제공 — 노트북 재현용

---

## 마무리

정성적 리뷰와 행동 기반 콘텐츠 신호를 토픽·키워드 단위로 통합해 제품/마케팅 의사결정에 직접 연결 가능한 인사이트와 프로토타입(추천 모델, GraphRAG 챗봇, 대시보드)을 제공한 실무형 분석 프로젝트입니다.

---

## License

MIT
