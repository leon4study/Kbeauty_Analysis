# [←](../README.md) Anna 정렬 평가 강화 전략

> **목적**: (주)애나 LLM/RAG 직무 면접 + 회사가 운영하는 KOLAS / ISO 25023·25024 / NIA AI 데이터 품질관리 가이드라인 v3.5 기반 평가 사업에 정렬된 평가 파이프라인으로 K-Beauty 챗봇 평가 인프라를 강화. 본진 strategy 의 K-Beauty 섹션을 이 repo 컨텍스트로 옮긴 것.
>
> **메인 strategy 문서**: `~/GitStudy/make_portfolio/지원/anna/평가전략_종합.md` — Anna 방법론 요약 + 학술/오픈소스 자료 + ccomantle 트랙 + 면접 활용 카드 포함. 이 문서는 K-Beauty 쪽 실행 카탈로그.

---

## 1. 현 상태 요약 (2026-05-23 실측 기준)

- **2-way 비교 완료**: GraphRAG (OpenAI gpt-4o-mini) vs LightRAG (Gemini Flash Lite, Tier 1)
- 평가 자산: `tests/rag_eval/evaluate.py` + `tests/rag_eval/golden_questions.yaml` (10 케이스) + Gemini judge LM
- 측정 6지표: `product_recall` · `brand_recall` · `forbidden_violations` · `faithfulness` · `answer_relevancy` · `latency`
- 결과: LightRAG = 응답 품질·속도 우세 (relevancy 0.93, brand_recall 58%, p95 6s) / GraphRAG = 안전성 우세 (forbidden_violations 1 vs 11) — 트레이드오프, 단순 승자 X
- 상세: [`rag_evaluation_results.md`](rag_evaluation_results.md), 메서드 정의: [`rag_evaluation_framework.md`](rag_evaluation_framework.md)

---

## 2. Anna 기준 갭 분석

Anna 의 KOLAS 공인 LLM·RAG 평가 사업 흐름 (ISO 25024 + NIA v3.5) 에 정렬해서 보면:

| 항목 | 현재 | Anna 기준 | 갭 | 처리 우선순위 |
|---|---|---|---|---|
| RAGAS `faithfulness` | 둘 다 0 (measurement broken — context 추출 path 차이) | 핵심 환각 측정 지표 | ✗ 깨짐 | **1** |
| `context_precision` / `recall` | 측정 안 함 | 검색 품질 핵심 지표 | ✗ | **1** |
| 통계 유의성 | 단순 평균 비교 | bootstrap CI + paired t-test | ✗ | 2 |
| 한국어 평가셋 | 영어 골든 10케이스 | 한국어 평가 자산 | ✗ | 2 |
| Judge LLM 다축 | Gemini 단일 | inter-judge agreement (Krippendorff α) | ✗ | 2 |
| NIA 비정형 8지표 매핑 | `forbidden_violations` 1개 (안전성 부분) | 8지표 매핑 | △ | 3 |
| 표본 수 | 10 케이스 (통계 약함) | 50-100+ | △ | 3 |
| 도메인 분리 | 5브랜드 한 묶음 | 도메인별 독립 평가 (피부타입·알러지·카테고리) | ✗ | 4 |
| AutoML / grid search | 수동 2-way 비교 | AutoRAG 등 자동 탐색 | ✗ | 5 (선택) |

---

## 3. 우선순위별 실행 계획

### 1순위 — RAGAS 정식 도입 (1-2주, 1 PR)

**목표**: `faithfulness=0` 깨짐 해소 + 검색 품질 지표 신규.

- `tests/rag_eval/evaluate.py` 의 자체 faithfulness 로직을 RAGAS 표준 정의로 교체
- GraphRAG/LightRAG 양쪽 **context 추출 path 통일** — RAGAS 가 요구하는 `contexts: List[str]` 포맷 맞춤
  - GraphRAG: `run_local_search` 의 context_data dict 를 평탄화 대신 정식 list 변환
  - LightRAG: `_run_lightrag` 가 현재 `contexts=[]` 반환 — LightRAG 내부 검색 결과를 wrapper 에서 노출
- 신규 측정: `context_precision`, `context_recall` (`context_recall` 은 ground_truth 필요 — 골든셋에 추가)
- 회귀: `tests/rag_eval/results/` baseline JSON 갱신 (기존 git tracked baseline 그대로 두고 RAGAS 적용 후 비교본 별도 박제)

**관련 자료**:
- RAGAS 논문: https://arxiv.org/abs/2309.15217 (EACL 2024)
- RAGAS repo: https://github.com/explodinggradients/ragas
- ARES 대안 (judge LM 자체 학습 방향): https://arxiv.org/abs/2311.09476

**관련 HANDOFF B 그룹 항목**: "lightrag faithfulness fix" — 이 작업의 1순위 단계와 동일. 본 트랙이 그걸 흡수.

### 2순위 — 한국어 평가셋 추가 + Judge 다축화 (2-3주, 1-2 PR)

**목표**: 한국어 RAG 평가 자산 구축 + judge bias 정량화.

- **Allganize RAG-Evaluation-Dataset-KO** commerce 도메인 **60Q 그대로 차용** (라이선스 MIT)
  - HF: https://huggingface.co/datasets/allganize/RAG-Evaluation-Dataset-KO
  - 9 문서 · 211 페이지 · context_type 4종 (paragraph/table/image/etc)
  - 본인 GraphRAG/LightRAG 점수를 **공개 리더보드** (Claude 3.5 Sonnet 0.847 / GPT-4o 0.783) 와 같은 축에서 비교 가능 — 면접 강력 카드
- K-Beauty 특화 한국어 골든 Q 30개 자체 작성 → 총 100 케이스로 확장 (영어 10 + Allganize 60 + 자체 30)
- Judge LLM 3-way cross-check:
  - Solar (Upstage), HyperCLOVA X (NAVER), Gemini Flash (현재)
  - inter-judge agreement (Krippendorff's α) 측정 → judge bias 정량화
- 한국어 임베딩 모델 검토: KoE5, KURE-v1, BGE-M3-ko (메인 strategy §2.5 참조)

**관련 자료**:
- Allganize 상세 (5도메인 × 60Q = 300Q, 리더보드 상위 5): 본진 strategy §2.3
- KMMLU (한국 고시 기반 35k Q, 번역 없이): https://arxiv.org/abs/2402.11548
- Ko-LongRAG: https://aclanthology.org/2025.findings-emnlp.938/

### 3순위 — 통계 유의성 (1주, 1 PR)

**목표**: 작은 표본에서도 차이의 통계적 유의성·신뢰구간 보고.

- `scipy` 로 bootstrap CI (95%) — RAG-A vs RAG-B 차이의 신뢰구간
- paired t-test (질문별 paired) — 두 변형 차이의 유의성
- `evaluate.py --summarize` 출력에 CI·p-value 컬럼 추가
- 작은 표본 (10-100) 에서도 차이의 크기·신뢰도 함께 보고 가능 → "10케이스라 약하다" 비판 보완

**메서드 참조**: 본인 K-Beauty TikTok 추천 알고리즘 검증의 `docs/methods/psm_within_fe.md` 와 같은 통계 검증 방법론 결.

### 4순위 — NIA 비정형 8지표 매핑 강화 (2-3주, 2-3 PR)

**목표**: NIA AI 데이터 품질관리 가이드라인 v3.5 의 비정형 8지표 중 측정 가능한 항목을 평가 인프라에 흡수.

- **안전성**: 현재 `forbidden_violations` 1개 → 약사법·과대광고·의료기기법 금칙어 확장 + Giskard 도입 검토
- 신규 **편향성**: 응답의 브랜드·가격대·국가 편향 비율 측정 (특정 브랜드만 추천하는지)
- 신규 **다양성**: 추천 다양성 (distinct brand, distinct ingredient, distinct category 수)
- 신규 **프라이버시**: 응답의 PII (개인식별정보) 노출 검사 — `presidio` 또는 정규식
- **내용품질·언어품질**: 응답의 한국어 자연스러움 측정 (LLM judge 또는 별도 한국어 fluency metric)
- 신규 **중복도**: 응답 간 동일·유사 응답 비율 (5회 반복 → embedding similarity)
- **노이즈**: 응답에 의미 없는 텍스트·필러 비율

**산출**: NIA 8지표 중 6-7개 직접 측정 가능 → "회사 비정형 8지표 중 본인 작업이 실측 닿는다" 면접 카드.

**관련 자료**: NIA v3.5 발표: https://www.aitimes.kr/news/articleView.html?idxno=35058

### 5순위 — 표본 확장 + 도메인 분리 (3-4주)

**목표**: 통계적 신뢰도 + 도메인별 강약 진단.

- 골든 케이스 100 → 200 (Allganize 5도메인 전체 300Q + 자체 한국어 K-Beauty 100)
- 도메인 분리 평가 축:
  - 피부타입 (건성/지성/민감/복합/중성)
  - 알러지 (파라벤·알코올·향료)
  - 카테고리 (클렌저/토너/세럼/크림/마스크)
- 도메인별 GraphRAG/LightRAG 강약 표 → 운영 가이드 정량화

### 6순위 (선택) — AutoRAG 도입

**목표**: 수동 2-way → 자동 grid search.

- AutoRAG (Marker-Inc-Korea) repo: https://github.com/Marker-Inc-Korea/AutoRAG (Apache-2.0)
- GraphRAG / LightRAG 를 strategy 노드로 등록
- retriever × generator 조합 자동 탐색 → 자동 최적 조합 리포트
- 단, AutoRAG README 검증 결과 "한국어 특화 기능" 명시는 없음 (multilingual AutoRAG 결). 한국어 평가셋은 별도 트랙 (2순위) 으로 유지

---

## 4. PR 단위 분해 (예상)

| PR 후보 | 범위 | 의존 | 예상 작업량 |
|---|---|---|---|
| `feat/rag_eval/ragas-integration` | 1순위 — RAGAS 도입 + context path 통일 | 없음 | 1-2주 |
| `feat/rag_eval/allganize-commerce-dataset` | 2순위-a — Allganize commerce 60Q 통합 | RAGAS-integration | 1주 |
| `feat/rag_eval/korean-golden-30` | 2순위-b — K-Beauty 한국어 골든 30 자체 작성 | RAGAS-integration | 1-2주 |
| `feat/rag_eval/judge-3way-crosscheck` | 2순위-c — Solar/HCX/Gemini 3-way + Krippendorff α | RAGAS-integration | 1주 |
| `feat/rag_eval/bootstrap-pairedt` | 3순위 — bootstrap CI + paired t-test | 평가셋 확장 후 | 1주 |
| `feat/rag_eval/nia-bias-diversity` | 4순위-a — 편향성·다양성 신규 | RAGAS-integration | 1-2주 |
| `feat/rag_eval/nia-privacy-safety` | 4순위-b — 프라이버시·안전성 강화 (Giskard) | RAGAS-integration | 1-2주 |
| `feat/rag_eval/domain-split` | 5순위 — 도메인 분리 (피부타입·알러지·카테고리) | 표본 확장 후 | 2주 |
| `feat/rag_eval/autorag-strategy` | 6순위 (선택) — AutoRAG 통합 | 위 다수 머지 후 | 2-3주 |

---

## 5. 기존 docs 와의 관계

| 파일 | 관계 |
|---|---|
| [`rag_evaluation_framework.md`](rag_evaluation_framework.md) | 5 차원 평가 프레임워크 정의. 본 문서가 그 정의를 RAGAS 표준 + NIA 8지표로 확장하는 형태 |
| [`rag_evaluation_results.md`](rag_evaluation_results.md) | 2-way 실측 결과 + 알려진 이슈. 본 문서 §2 의 갭 분석이 그 알려진 이슈를 Anna 표준 결로 재구성한 것 |
| [`lightrag_comparison_design.md`](lightrag_comparison_design.md) | LightRAG vs GraphRAG 아키텍처 비교. 본 문서 §3 1순위가 그 평가 framework 의 faithfulness 측정 보강 |
| [`rag_llm_eval_knowledge.md`](rag_llm_eval_knowledge.md) | 평가 일반 지식. 본 문서가 그 지식을 K-Beauty 실행 카탈로그로 옮긴 형태 |
| `~/GitStudy/make_portfolio/지원/anna/평가전략_종합.md` | 메인 strategy. 본 문서는 그 §5 K-Beauty 섹션을 이 repo 결로 확장한 것 |

---

## 6. 면접 활용 (Anna 직격)

본 트랙의 실행 자체가 면접 자산. 진행 정도에 따라:

- **1순위 진행만으로도**: "RAGAS 표준 도입으로 자체 측정 한계를 해소하고 있다" — 정직한 진행 상태로 어필
- **2순위까지**: "Allganize 한국어 RAG 평가셋의 commerce 도메인을 본인 작업에 결합하고 공개 리더보드와 같은 축에서 비교한다" — 회사 한국어 RAG 평가 사업 직격
- **4순위까지**: "회사 NIA 비정형 8지표 중 6-7개가 본인 평가 인프라에 실측 매핑된다" — 회사 평가 서비스 영역에 본인 작업이 닿는다는 정량 증거
- **6순위까지**: "AutoRAG 같은 한국발 도구를 production 통합 검토했다" — 가산점

상세 면접 카드는 메인 strategy `~/GitStudy/make_portfolio/지원/anna/평가전략_종합.md` §7 참조.

---

## 7. 변경 이력

- **2026-06-01 v1**: 메인 strategy §5 의 K-Beauty 섹션을 이 repo 컨텍스트 결로 옮김. HANDOFF B 그룹의 "lightrag faithfulness fix" 항목을 1순위로 흡수. PR 9개 단위로 분해.
