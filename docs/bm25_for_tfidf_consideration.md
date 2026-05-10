# BM25 알고리즘 — TF-IDF 대체 검토 (미래 보강 옵션)

K-Beauty 분석 프로젝트 안 TF-IDF 사용처를 BM25 로 바꾸면 어떤 효과가 있을지 사전 검토 영구 기록. 지금 당장 적용은 아니고, 나중에 프로젝트 보강 필요할 때 *선택지 중 하나로* 꺼낼 수 있도록 정리.

## 배경

`sklearn.feature_extraction.text.TfidfVectorizer` 로 텍스트를 벡터화한 뒤 (a) 키워드 빈도 분석 (b) cosine similarity 기반 추천 두 갈래로 사용 중. TF-IDF 가 정상 작동하지만 *문서 길이 편차* 가 큰 데이터 (Amazon 리뷰 1~500 단어, TikTok info 5~50 단어) 에선 BM25 가 더 정밀할 가능성.

## TF-IDF vs BM25

| 항목 | TF-IDF | BM25 |
|---|---|---|
| TF 처리 | 단순 빈도 (반복 = 선형 가중) | **포화도 곡선** (k1 파라미터로 조절). 한 단어 30 번 반복해도 5 번보다 약간만 더 가중 |
| 문서 길이 | 정규화 없음 (긴 문서가 자동 가점) | **b 파라미터로 정규화**. 평균 길이 대비 짧으면 가점, 길면 감점 |
| IDF | 표준 idf | 변형된 idf (음수 방지) |
| 구현 | sklearn 표준 | `rank_bm25` 라이브러리 또는 직접 구현 |

**BM25 가 더 우수한 상황**:
1. 문서 길이 편차 큼 (짧은 글 + 긴 글 섞임)
2. 한 단어 과도 반복 (e.g. 광고성 리뷰의 키워드 도배)
3. 검색·추천 정밀도가 중요할 때

**TF-IDF 가 충분한 상황**:
1. 문서 길이 균일 (e.g. 같은 형식의 트윗)
2. 단순 키워드 빈도 분석만
3. 빠른 prototype, sklearn 호환 파이프라인

## 핵심 수식 (개념만)

BM25 score(query, document) =
- IDF (단어가 얼마나 희귀한가)
- × TF 포화 항 (`(k1+1)·tf / (k1·norm + tf)`)
- norm = `(1-b) + b·(doc_len/avg_doc_len)` ← 문서 길이 정규화

**파라미터**:
- `k1 = 1.2~2.0` (default 1.5): TF 영향력. 높을수록 빈도 의존
- `b = 0.75`: 문서 길이 정규화 강도. 0 이면 길이 무시, 1 이면 완전 정규화

대부분의 검색 엔진 default (`k1=1.5, b=0.75`) 가 일반 텍스트에서 잘 작동.

## 프로젝트 안 TF-IDF 사용처 + BM25 적용 가능성 평가

### 1. `notebooks/EDA.ipynb` (line 5821, 10170)

**현재**: Amazon 리뷰 텍스트에 `TfidfVectorizer()` 적용해 컬럼별 키워드 매트릭스 생성. `tfidf_matrix.toarray()` 로 DataFrame 만들어 *imputed_scale_df* 로 변환 후 *피처 엔지니어링* 사용.

**BM25 적용 시 예상**:
- Amazon 리뷰는 *길이 편차 큼* (1~500 단어) → BM25 의 길이 정규화가 *짧은 리뷰의 키워드 가중치 보정* 에 도움
- 단 *피처 엔지니어링* 용도면 sklearn 호환 안 되는 게 단점 (Pipeline / GridSearchCV 사용 못 함)
- **권고**: 보강 가치 있음 단, sklearn 파이프라인 종속성 확인 후 결정

### 2. `notebooks/amazon_tiktok/05_without_wonyoung_presentation.ipynb` (line 23252)

**현재**: `content_features` 컬럼을 `TfidfVectorizer()` 변환 후 `cosine_similarity(tfidf_matrix, tfidf_matrix[selected_indices])` 로 추천. *검색·추천 본 케이스*.

**BM25 적용 시 예상**:
- **BM25 가 가장 효과적** 인 사용처. 추천 정밀도 직접 영향
- 영상 description 길이 편차 (5~50 단어) 도 정규화 도움
- *cosine similarity 기반* 이라 BM25 score 매트릭스로 바꾸기 쉬움
- **권고**: 1 순위 적용 후보. ER% 추천 정밀도 향상 측정 가능 (정량 비교)

### 3. `notebooks/lemmatized_full_pipeline.ipynb` (line 4462)

**현재**: `# from sklearn.feature_extraction.text import TfidfVectorizer` — *주석 처리됨*. 과거 시도였으나 현재 LDA 토픽 모델로 대체.

**BM25 적용 시 예상**:
- 토픽 모델은 BoW (CountVectorizer) 기반이라 BM25 와 직접 비교 불가
- 단 *키워드 추출 단계* 에서 BM25 사용 가능 (Top-K 키워드 ranking 정밀도 향상)
- **권고**: 우선순위 낮음. LDA 결과 충분히 좋으면 그대로

## 구현 방법

```python
# pip install rank_bm25
from rank_bm25 import BM25Okapi

# 토큰화된 documents 리스트 (각 doc 은 단어 리스트)
tokenized_docs = [doc.split() for doc in documents]

# BM25 인덱스 생성
bm25 = BM25Okapi(tokenized_docs, k1=1.5, b=0.75)

# query 에 대한 score (모든 documents 와 비교)
query = "moisturizing for sensitive skin".split()
scores = bm25.get_scores(query)

# Top-K 추천
import numpy as np
top_k_idx = np.argsort(scores)[::-1][:10]
```

`rank_bm25` 외 대안:
- **gensim BM25** (gensim 4.x 부터 deprecated 주의)
- **Elasticsearch** (검색 엔진 자체에 BM25 내장 — 인프라 구축 부담)
- **직접 구현** (수식 단순해서 numpy 로 100 줄 이내)

## 적용 시 예상 효과

| 영역 | 효과 추정 | 측정 방법 |
|---|---|---|
| 추천 정밀도 (사용처 2) | ER% 평균 +5~15% (가설) | 1,540 부트스트랩 검증 (ver.4 와 동일 방식) — TF-IDF vs BM25 양쪽 1,540 조합으로 |
| 키워드 추출 (사용처 1) | 짧은 리뷰의 keyword 가중치 정정 → 토픽 일관성 향상 | LDA topic coherence score |
| 처리 속도 | TF-IDF 대비 약간 느림 (2~3 배), 단 1,000~10,000 문서 규모면 무시 가능 | timeit |

## 본 프로젝트에서 적용 결정 보류 이유

1. **현재 분석 결과로 *충분히 의미 있는 인사이트* 도출**됨 (within-FE selection effect 95% 등)
2. *추천 알고리즘 ver.4* 가 이미 무작위 대비 3.25배 — 현재 baseline 이 좋음
3. BM25 는 *추가 정밀도* 의 영역, *근본 결론* 을 바꾸지 않음

→ **portfolio 1차 완성 우선**, BM25 는 *2차 보강* 으로 미룸. 만약 면접 / 평가에서 *"검색·추천 정밀도 더 높일 방법?"* 질문 받으면 이 doc 보여주며 *기술 옵션 인지 + 실험 설계 가능* 어필.

## 후속 작업 (적용 시 task)

- [ ] `rank_bm25` 의존성 추가 (`pyproject.toml` 의 `[analysis]` extras)
- [ ] 사용처 2 (추천) 에 BM25 변형 노트북 작성 — 기존 TF-IDF 결과와 *나란히 비교*
- [ ] 1,540 조합 부트스트랩으로 ER% 검증 (TF-IDF baseline 과 동일 방식)
- [ ] 결과 표 + 그래프 → portfolio 보강 섹션
- [ ] 사용처 1 (피처 엔지니어링) 은 sklearn 호환 wrapper 작성 후 적용

## 참고 자료

- [BM25 알고리즘이란? — happydhkim.tistory.com](https://happydhkim.tistory.com/entry/BM25-%EC%95%8C%EA%B3%A0%EB%A6%AC%EC%A6%98%EC%9D%B4%EB%9E%80) — 본 doc 의 출발점
- [`rank_bm25` 라이브러리](https://github.com/dorianbrown/rank_bm25)
- Robertson & Zaragoza (2009), *The Probabilistic Relevance Framework: BM25 and Beyond* — 원조 논문
