# [←](../README.md) RAG · LLM · 평가 벤치마크 — 알아둘 지식 정리

> **목적**: K-Beauty GraphRAG 챗봇 프로젝트를 면접에서 설명할 때 *배경 지식*으로 깔려 있어야 하는 RAG·LLM·평가 개념을 정리. 회사 제품·데이터 내용은 제외하고, *기술 일반 지식*만 담음. 프로젝트에서 실제 쓴 도구(GraphRAG / LightRAG / OpenAI / Groq / Gemini / RAGAS)에 닻을 내려서, 개념 → "내 프로젝트에선 이렇게 썼다" 로 연결되게 구성.
>
> **연결 문서**: 평가 metric 정의는 [`rag_evaluation_framework.md`](rag_evaluation_framework.md), 실측 결과는 [`rag_evaluation_results.md`](rag_evaluation_results.md), GraphRAG↔LightRAG 비교는 [`lightrag_comparison_design.md`](lightrag_comparison_design.md).

---

## 1. RAG — 왜, 무엇

### 1.1 RAG 가 푸는 문제

LLM 단독은 세 가지 한계가 있다.

- **지식 컷오프**: 학습 시점 이후 정보를 모름.
- **할루시네이션**: 모르는 걸 그럴듯하게 지어냄.
- **출처 부재**: 답의 근거를 댈 수 없음 (검증 불가).

RAG(Retrieval-Augmented Generation)는 *질문 시점에* 외부 지식에서 관련 문서를 **검색(retrieve)** 해 프롬프트에 끼워 넣고, 그 context 위에서 LLM 이 **생성(generate)** 하게 한다. 모델 파라미터를 안 건드리고(파인튜닝 X) 지식을 갈아끼울 수 있고, 근거 문서를 같이 보여줄 수 있다.

> 한 줄 정의: **"검색으로 찾은 근거를 프롬프트에 넣어 LLM 이 그 근거 위에서 답하게 하는 구조."**

### 1.2 Naive RAG 파이프라인 (가장 기본형)

```
[인덱싱 단계 — 1회]
문서 → 청킹(chunking) → 임베딩(embedding) → 벡터 DB 저장

[질의 단계 — 매 질문]
질문 → 질문 임베딩 → 벡터 유사도 검색(top-K) → context 조립
     → 프롬프트(질문+context) → LLM → 답변
```

각 단계의 핵심 의사결정:

| 단계 | 결정할 것 | 트레이드오프 |
|---|---|---|
| **청킹** | chunk 크기, overlap | 작으면 정밀하지만 맥락 끊김 / 크면 맥락 보존하지만 노이즈·비용↑ |
| **임베딩** | 어떤 임베딩 모델 | 차원·언어·도메인 적합도 vs 비용·속도 |
| **벡터 DB** | 어디에 저장·검색 | 로컬(in-process) vs 서버형, 인덱스 종류(HNSW 등) |
| **검색** | top-K, 유사도 척도 | K 크면 recall↑ 하지만 noise·토큰↑ |
| **생성** | 어떤 LLM, temperature | 정확도·비용·latency |

### 1.3 RAG 의 진화 단계 (용어로 알아두기)

- **Naive RAG**: 위 기본형. 검색→붙여넣기→생성.
- **Advanced RAG**: 검색 전후를 보강. *pre-retrieval*(쿼리 재작성query rewriting, HyDE, 쿼리 확장) + *post-retrieval*(reranking, context 압축).
- **Modular RAG**: 검색·생성·라우팅·메모리를 모듈로 분리해 조립. (예: 질문 유형별로 다른 retriever 라우팅)
- **GraphRAG**: 문서를 *지식 그래프(entity + relation)* 로 구조화해 검색. → §3.

---

## 2. RAG 구성요소 깊게 보기

### 2.1 임베딩(Embedding)

텍스트를 의미를 담은 고정 길이 벡터로 변환. 의미가 비슷하면 벡터 거리가 가깝다.

- **유사도 척도**: 코사인 유사도(cosine similarity)가 가장 흔함. 내적(dot product), 유클리드 거리도 사용.
- **차원(dimension)**: 768, 1024, 1536 등. 클수록 표현력↑ 하지만 저장·계산 비용↑.
- 본 프로젝트에서 쓴 임베딩:
  - `text-embedding-3-small` (OpenAI, GraphRAG 변형) — 1536 dim, 유료 API.
  - `bge-m3` (BAAI, LightRAG 로컬 변형) — 1024 dim, 다국어·로컬 실행 가능, 비용 0.
  - `text-embedding-004` (Google, Gemini 변형).
- **알아둘 포인트**: 인덱싱과 질의에서 *같은 임베딩 모델*을 써야 한다. 다르면 벡터 공간이 안 맞아 검색이 망가짐.

### 2.2 청킹(Chunking)

긴 문서를 검색 단위로 자르는 것. 전략:

- **고정 크기**(N 토큰 + overlap): 단순, 가장 흔함.
- **문장/문단 단위**: 의미 경계 보존.
- **재귀적(recursive)**: 문단→문장→단어 순으로 큰 단위부터 자르다 크기 맞추기.
- **의미 기반(semantic chunking)**: 임베딩 유사도가 급변하는 지점에서 자름.

핵심 긴장: **chunk 가 작으면** 검색 정밀도는 오르지만 답에 필요한 맥락이 잘려 나감. **크면** 맥락은 살지만 관련 없는 내용까지 끌려와 노이즈·토큰 비용 증가.

### 2.3 벡터 DB / 인덱스

대량 벡터에서 최근접 이웃을 빠르게 찾는 저장소. 정확히 다 비교하면(brute-force) 느리므로 **ANN(Approximate Nearest Neighbor)** 인덱스를 씀.

- **인덱스 알고리즘**: HNSW(그래프 기반, 가장 보편), IVF(클러스터 기반), PQ(양자화로 압축).
- **저장 형태**:
  - 서버형: Pinecone, Weaviate, Qdrant, Milvus.
  - 임베디드/로컬: **LanceDB**(본 프로젝트 사용), Chroma, FAISS, nano-vectordb(LightRAG 내장).
- 본 프로젝트: GraphRAG 변형은 **LanceDB + Parquet**, LightRAG 변형은 **JSON + nano-vectordb(in-process)**.

### 2.4 검색 방식 — Dense vs Sparse vs Hybrid

| 방식 | 원리 | 강점 | 약점 |
|---|---|---|---|
| **Sparse (어휘 기반)** | 단어 일치도. TF-IDF, **BM25** | 정확한 키워드·고유명사·희귀어에 강함 | 동의어·의역 못 잡음 |
| **Dense (의미 기반)** | 임베딩 벡터 유사도 | 의미·문맥·동의어 포착 | 정확한 키워드·숫자·코드엔 약할 수 있음 |
| **Hybrid** | 둘을 가중 합산(예: RRF) | 양쪽 장점 | 튜닝·구현 복잡 |

- **BM25**: TF-IDF 를 개선한 어휘 검색의 사실상 표준. 문서 길이 정규화 + 단어 빈도 포화(saturation)를 반영. → 본 프로젝트에는 [`bm25_for_tfidf_consideration.md`](bm25_for_tfidf_consideration.md) 에 TF-IDF→BM25 보강 검토 기록.
- **RRF(Reciprocal Rank Fusion)**: 여러 검색 결과의 순위를 `1/(k+rank)` 로 합쳐 융합하는 hybrid 표준 기법.

### 2.5 Reranking (재순위화)

1차 검색(빠르고 recall 위주)으로 후보 수십 개를 뽑은 뒤, **cross-encoder reranker** 가 질문-문서 쌍을 직접 보며 정밀 재채점해 top-K 로 좁힘.

- **Bi-encoder**(임베딩 검색): 질문·문서를 따로 인코딩 → 빠름, 미리 계산 가능.
- **Cross-encoder**(reranker): 질문+문서를 같이 인코딩 → 정확하지만 느림 (미리 계산 불가).
- 패턴: bi-encoder 로 넓게 건진 뒤 cross-encoder 로 좁게 거른다. (예: Cohere Rerank, bge-reranker)

### 2.6 검색 보강 기법 (용어)

- **Query rewriting / expansion**: 모호한 질문을 검색 친화적으로 재작성하거나 동의어 추가.
- **HyDE(Hypothetical Document Embeddings)**: 질문에 대한 *가상의 답*을 LLM 이 먼저 생성 → 그 가상 답을 임베딩해 검색. 질문보다 답이 문서와 더 닮았다는 직관.
- **Context 압축**: 검색된 chunk 에서 질문과 무관한 문장을 쳐내 토큰 절약.

---

## 3. GraphRAG vs LightRAG — 그래프 기반 RAG

### 3.1 왜 그래프 RAG 인가

벡터 검색은 *국소적*이다 — 질문과 비슷한 chunk 만 모은다. "여러 문서에 흩어진 정보를 종합해야 하는" 질문(예: "전체에서 가장 자주 언급된 관계는?")엔 약하다. **GraphRAG** 는 문서에서 *엔티티(entity)와 관계(relation)*를 추출해 **지식 그래프**를 만들고, 그래프 구조 + 커뮤니티 요약으로 *전역적(global)* 질문에 답한다.

### 3.2 인덱싱 파이프라인 차이

| 항목 | Microsoft **GraphRAG** | HKUDS **LightRAG** |
|---|---|---|
| 인덱싱 단계 | Documents → Text Units → Entities → Relations → **Communities → Community Summaries** (5+단계) | Documents → Chunks → Entities → Relations (3단계) |
| Entity 추출 프롬프트 | strict, 다단계 gleaning(반복 추출) | 단순, 단일 패스 |
| 권장 LLM 크기 | 큰 모델(GPT-3.5+/70B+) 전제 | 작은 모델 친화(공식 32B+, 실측은 9B 도 동작) |
| 저장 | Parquet + LanceDB | JSON + nano-vectordb |
| 쿼리 모드 | local / global / drift | naive / local / global / hybrid |

### 3.3 쿼리 모드 (개념)

- **local search**: 특정 엔티티 주변(이웃 노드 + 관련 chunk)을 모아 답함 → "이 제품 성분은?" 류 구체적 질문.
- **global search**: 커뮤니티 요약들을 map-reduce 로 종합 → "전체 트렌드는?" 류 광역 질문.
- **hybrid**(LightRAG): 엔티티 그래프 + chunk 를 결합. **naive**: 그래프 우회한 단순 벡터 RAG.

### 3.4 "community" 와 map-reduce 요약

GraphRAG 는 그래프를 **커뮤니티(밀집 연결된 노드 군집, Leiden 알고리즘)** 로 나누고 각 커뮤니티를 LLM 이 요약해 둔다. global 질문이 오면 커뮤니티 요약들에 각각 답하게 한 뒤(map) 그 부분답들을 합친다(reduce). → 이 *사전 요약 단계*가 GraphRAG 의 강점이자 비용·인덱싱 시간의 주범. LightRAG 엔 이 단계가 없어 가볍다.

> **면접 한 줄**: "벡터 RAG 는 비슷한 조각을 모으는 국소 검색이라 전역 종합 질문에 약합니다. GraphRAG 는 엔티티·관계를 그래프로 구조화하고 커뮤니티 요약을 미리 만들어 광역 질문에 답하는 구조이고, 그만큼 인덱싱이 무겁습니다. 그래서 가벼운 LightRAG 와 같은 입력으로 비교 실험했습니다."

---

## 4. LLM 운영에서 알아둘 개념

### 4.1 토큰 · 컨텍스트 윈도우

- **토큰**: LLM 이 텍스트를 쪼개는 단위(영어 ≈ 0.75단어, 한국어는 글자당 토큰 더 많이 먹음). 비용·길이 제한이 토큰 기준.
- **컨텍스트 윈도우**: 한 번에 입력+출력으로 넣을 수 있는 최대 토큰. RAG 에서 검색 context 가 이 한도를 압박 → "넣을 수 있는 chunk 수"의 상한.

### 4.2 디코딩 파라미터

- **temperature**: 0 에 가까울수록 결정적(같은 입력→같은 출력 경향), 높을수록 다양·창의적. *RAG·평가는 보통 temperature=0* (재현성). 본 프로젝트 GraphRAG 도 `temperature=0`.
- **top-p / top-k**: 샘플링 후보 제한. **max_tokens**: 출력 길이 상한.

### 4.3 Provider 와 rate limit — *단위가 다르다*

면접에서 "무료 tier 로 어떻게 운영했나" 질문에 직결되는 실무 지식.

| Provider | 한도 단위 | 의미 | 실무 함의 |
|---|---|---|---|
| **Groq** | TPM (분당 토큰) | 분당 처리 토큰 총량 + **단일 request 토큰 상한** | 단일 요청이 한도 초과면 *영구 fail* (재시도·직렬화로도 못 우회) |
| **Gemini** | RPM (분당 요청) | 분당 요청 수 | 직렬화·딜레이로 우회 가능. Tier 1(카드 등록) 시 한도 급증 |
| **OpenAI** | RPM + TPM 둘 다 | — | 유료라 한도 넉넉 |

> **본 프로젝트 실측 인사이트** (→ [`rag_evaluation_results.md`](rag_evaluation_results.md)): "시간당 한도(TPM/RPM)는 직렬화·캐시로 우회되지만, **단일 request 크기 한도**는 우회 불가." LightRAG 의 엔티티 추출 프롬프트(~13k 토큰)가 Groq 무료 12k TPM(=단일 request 상한)을 넘겨 인덱싱이 막혔다. → "long-prompt RAG 엔 단일 request 한도가 큰 provider 가 맞다"는 결론.

### 4.4 비용 구조

- **인덱싱 비용**(1회) vs **질의 비용**(매번) 분리해서 봐야 함. GraphRAG 는 커뮤니티 요약 때문에 인덱싱 비용이 큼.
- **임베딩 비용 ≪ 생성 비용**. 임베딩은 싸고, LLM 생성 토큰이 비용 대부분.
- 로컬(Ollama + bge-m3)은 비용 0 이지만 *느림*(인덱싱 수 시간, 질의 수십 초) — 프라이버시·오프라인 niche.

### 4.5 양자화(Quantization) — 로컬 LLM

가중치를 FP16 → INT8/INT4 로 줄여 메모리·속도를 버는 기법. 4-bit 양자화면 7B 모델을 일반 노트북에서 돌릴 수 있음(약간의 품질 손실). 본 프로젝트 Ollama 변형(gemma2 9B, qwen2.5)이 로컬 양자화 모델.

### 4.6 파인튜닝 vs RAG (자주 나오는 비교)

| | RAG | 파인튜닝 |
|---|---|---|
| 바꾸는 것 | 외부 지식(프롬프트) | 모델 가중치 |
| 적합 | 최신·변동 지식, 출처 필요 | 말투·형식·도메인 스타일 학습 |
| 비용/갱신 | 문서만 갈면 됨(싸고 빠름) | 재학습 필요(비쌈) |
| 할루시네이션 | 근거로 억제 | 직접 억제 안 됨 |

→ 실무에선 둘을 **병행**(RAG 로 지식 + 파인튜닝/프롬프트로 형식)하기도. 본 프로젝트는 파인튜닝 없이 순수 RAG.

---

## 5. 평가 (1) — RAG 평가

RAG 는 **검색(retrieval)** 과 **생성(generation)** 을 *분리해서* 평가해야 한다. 한쪽만 보면 실패 원인을 못 짚는다.

### 5.1 검색 품질 metric

| Metric | 정의 | 직관 |
|---|---|---|
| **Recall@K** | 정답 문서가 top-K 안에 든 비율 | "필요한 걸 건졌나" |
| **Precision@K** | top-K 중 진짜 관련 비율 | "건진 게 깨끗한가" |
| **MRR** (Mean Reciprocal Rank) | 첫 정답의 순위 역수 평균(1/rank) | "정답이 위에 오는가" (1위면 1.0, 5위면 0.2) |
| **nDCG** | 순위별 가중 + 이상순위 정규화 | "관련도 높은 게 위에 정렬됐나" |

본 프로젝트는 골든 질문에서 `expected_entity` 매칭으로 Recall@K·MRR 측정, 도메인 metric(브랜드 recall 등)도 별도 정의.

### 5.2 생성 품질 metric — RAGAS

**RAGAS** 는 RAG 평가 표준 프레임워크. 핵심은 **LLM-as-judge**(LLM 이 채점자) 라 정답 라벨 없이도 일부 측정 가능.

| Metric | 측정 | 정답(ground truth) 필요? |
|---|---|---|
| **Faithfulness** | 답이 검색 context 에 근거하는가 (할루시네이션 역지표) | X |
| **Answer Relevancy** | 답이 질문에 적절한가 | X |
| **Context Precision** | 쓴 context 중 관련 비율 | X |
| **Context Recall** | 정답에 필요한 context 가 빠지지 않았나 | **O** |

> 4축으로 외우기: **답↔context**(faithfulness), **답↔질문**(relevancy), **context↔질문**(context precision), **context↔정답**(context recall).

### 5.3 LLM-as-judge 의 함정 (면접 가산점 포인트)

- **Self-preference bias**: judge LLM 이 *자기 family* 답을 후하게 줌. → judge 는 평가 대상과 *다른 family* 로. (본 프로젝트: 대상이 OpenAI/Groq 면 judge 는 Gemini)
- **Position bias**: A/B 비교 시 앞에 놓인 답을 선호.
- **Verbosity bias**: 길고 장황한 답에 점수를 더 줌.
- **샘플 수 한계**: 질문 10개는 통계적으로 약함. *큰 차이(latency 10배, faithfulness 0.5 vs 0.9)만* 신뢰, 미세 차이로 결론 X.
- **측정 한계 사례**: 본 프로젝트에서 faithfulness 가 두 변형 다 0 으로 나온 건 진짜 0 이 아니라 *context 추출 경로가 변형마다 달라* judge 가 근거를 못 본 measurement issue. → 메트릭이 0/이상값이면 "측정이 깨진 건 아닌가"부터 의심.

### 5.4 운영 metric (정확도 못지않게 중요)

무료 tier 운영에선 정확도만큼 중요: **Latency p50/p95**(p95 = worst case 체감, cold start 영향), **Cost per query**, **Failure rate**(rate limit/JSON 파싱/timeout), **Indexing time/cost**, **Reproducibility**(같은 질문 N회 → 임베딩 코사인 분산).

---

## 6. 평가 (2) — LLM 일반 벤치마크

> RAG 평가와 별개로, "LLM 자체가 얼마나 똑똑한가"를 재는 표준 벤치마크들. 면접에서 "모델을 어떤 기준으로 골랐나" 류 질문에 배경 지식.

### 6.1 능력별 대표 벤치마크

| 영역 | 벤치마크 | 무엇을 재나 |
|---|---|---|
| **종합 지식·추론** | **MMLU** (Massive Multitask Language Understanding) | 57개 과목 객관식. 모델 종합 지능의 사실상 표준 |
| | MMLU-Pro | MMLU 강화판(보기 10개, 더 어려움) |
| | GPQA | 대학원 수준 과학(검색해도 어려운 문제) |
| **상식 추론** | HellaSwag, WinoGrande, ARC | 문장 완성·상식·과학 추론 |
| **수학** | **GSM8K**(초등 단어 문제), **MATH**(경시대회 수준) | 다단계 수리 추론 |
| **코딩** | **HumanEval**, MBPP | 함수 생성 후 실제 테스트 통과율(pass@k) |
| | SWE-bench | 실제 GitHub 이슈 해결(에이전트 능력) |
| **지시 따르기** | IFEval | 형식·제약 지시 준수 |
| **장문 이해** | LongBench, "Needle in a Haystack" | 긴 컨텍스트에서 특정 정보 회수 |
| **다국어** | MMMLU, KMMLU(한국어) | 언어별 능력 |
| **환각·진실성** | TruthfulQA | 흔한 오개념에 안 속는가 |

### 6.2 벤치마크 vs 사람 선호 — 두 패러다임

- **정적 벤치마크**(MMLU 등): 정답이 정해진 객관식·테스트. 재현 가능하지만 *데이터 오염(contamination)* 위험(모델이 학습 때 시험문제를 봤을 수 있음).
- **사람 선호 기반**:
  - **Chatbot Arena (LMArena)**: 사람이 두 모델 답을 블라인드 비교 투표 → **Elo 레이팅**. 실사용 만족도에 가장 가깝다고 평가받음.
  - **MT-Bench**: 멀티턴 대화를 GPT-4 가 채점(LLM-as-judge).

### 6.3 벤치마크 읽을 때 주의

- **데이터 오염**: 공개 벤치마크는 학습 데이터에 섞였을 수 있음 → 점수 과대.
- **pass@k 표기**: 코딩 벤치마크는 k번 시도 중 1번 성공이면 인정(pass@1 이 가장 엄격).
- **shot 수**: 0-shot / 5-shot(예시 몇 개 줬는지)에 따라 점수 달라짐 → 비교 시 조건 통일 필수.
- **벤치마크 ≠ 내 태스크**: 종합 점수 높은 모델이 *내 도메인(예: 한국어 화장품 추천)*에서 최고란 보장 없음. → 그래서 **도메인 골든셋으로 직접 평가**하는 게 본 프로젝트의 핵심 논리.

### 6.4 (참고) RAG 전용 벤치마크

데이터셋 단위로도 RAG 를 잴 수 있음: **RGB**, **CRUD-RAG**, **MultiHop-RAG**(다중 문서 종합), **RAGTruth**(할루시네이션 라벨), 검색 평가용 **BEIR**(다양한 검색 태스크 모음)·**MTEB**(임베딩 모델 리더보드). → 임베딩 모델 고를 때 **MTEB 리더보드**가 실무 참고점.

---

## 7. 면접 대비 — 자주 나오는 질문 + 한 줄 답

| 질문 | 한 줄 답 |
|---|---|
| RAG 가 왜 필요? | 파인튜닝 없이 최신·외부 지식을 주입하고, 근거로 할루시네이션을 억제하며 출처를 댈 수 있어서. |
| GraphRAG 와 일반 벡터 RAG 차이? | 벡터 RAG 는 비슷한 조각을 모으는 국소 검색, GraphRAG 는 엔티티·관계를 그래프로 구조화 + 커뮤니티 요약으로 전역 종합 질문에 강함. |
| 왜 LightRAG 도 비교했나? | GraphRAG 는 인덱싱이 무겁고 큰 LLM 전제. 가벼운 LightRAG 가 작은/무료 모델로도 되는지를 같은 입력으로 검증하려고. |
| RAG 를 어떻게 평가했나? | 검색(Recall@K·MRR)과 생성(RAGAS: faithfulness·relevancy·context precision/recall)을 분리 + 운영(latency·cost·failure) + 도메인 metric, 골든 10질문으로. |
| LLM-as-judge 의 위험은? | self-preference·position·verbosity bias. judge 를 평가 대상과 다른 family 로 두고, 샘플 적으니 큰 차이만 신뢰. |
| 무료 tier 로 어떻게 운영? | provider별 한도 단위가 다름(Groq=TPM·단일 request 상한, Gemini=RPM). 단일 request 한도는 우회 불가라 long-prompt RAG 엔 한도 큰 provider, Gemini Tier 1 등록이 실질 진입점. |
| temperature 0 인 이유? | 평가·RAG 는 재현성이 중요해서 결정적 출력으로 둠. |
| 임베딩 모델 어떻게 고르나? | 언어·도메인 적합도(다국어면 bge-m3 류), 차원·비용·로컬 가능 여부. 객관 참고는 MTEB 리더보드. |
| 벤치마크 점수 높은 모델이 항상 최선? | 아니다. 데이터 오염·태스크 불일치 때문에 도메인 골든셋으로 직접 재야 한다. |

---

## 8. 용어 빠른 사전

- **RAG**: Retrieval-Augmented Generation. 검색+생성.
- **Chunk / Chunking**: 검색 단위로 문서를 자른 조각 / 자르는 작업.
- **Embedding**: 텍스트→의미 벡터.
- **ANN**: Approximate Nearest Neighbor. 근사 최근접 검색(HNSW/IVF/PQ).
- **BM25**: 어휘(sparse) 검색 표준. TF-IDF 개선판.
- **Dense / Sparse / Hybrid retrieval**: 의미 / 어휘 / 결합 검색.
- **RRF**: Reciprocal Rank Fusion. hybrid 결과 융합.
- **Reranker (cross-encoder)**: 후보를 질문과 직접 대조해 재순위.
- **HyDE**: 가상 답을 만들어 그걸로 검색.
- **Entity / Relation**: 그래프 노드 / 노드 간 관계.
- **Community summary**: 그래프 군집 요약(GraphRAG 전역 검색의 핵심).
- **TPM / RPM**: 분당 토큰 / 분당 요청 한도.
- **Faithfulness / Answer relevancy / Context precision·recall**: RAGAS 4 metric.
- **MRR / Recall@K / nDCG**: 검색 순위 품질.
- **LLM-as-judge**: LLM 으로 채점.
- **MMLU / GSM8K / HumanEval / Chatbot Arena(Elo)**: 대표 LLM 벤치마크.
- **MTEB / BEIR**: 임베딩·검색 벤치마크 리더보드.
- **Quantization**: 가중치 비트 축소(INT8/INT4)로 로컬 실행.

---

## 관련 docs

- [`rag_evaluation_framework.md`](rag_evaluation_framework.md) — 본 프로젝트 5차원 평가 metric 정의(이 문서 §5 의 실제 적용판)
- [`rag_evaluation_results.md`](rag_evaluation_results.md) — GraphRAG vs LightRAG 실측 결과 + 무료 한도 인사이트(§4.3 근거)
- [`lightrag_comparison_design.md`](lightrag_comparison_design.md) — GraphRAG↔LightRAG 아키텍처 비교 설계(§3 근거)
- [`bm25_for_tfidf_consideration.md`](bm25_for_tfidf_consideration.md) — TF-IDF→BM25 보강 검토(§2.4)
- [`setup_lightrag_env.md`](setup_lightrag_env.md) — LightRAG 로컬 venv 환경
