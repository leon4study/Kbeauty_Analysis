# LightRAG + Ollama smoke test (Plan E - 단계 0)

LightRAG 가 *작은 Ollama 모델 (gemma2 등) 로 실제 동작하는지* 검증하는 최소 ping.

## 왜 필요한가

- LightRAG = GraphRAG 의 lighter 대안. 작은 LLM 친화적이라고 *알려짐*
- 옛 GraphRAG + Ollama 시도 ([`docs/refactor/15`](../../docs/refactor/15_ollama_graphrag_compatibility.md))
  는 entity extraction 단계 fail
- 이번엔 *진짜 끝까지 가는지* 작은 sample 로 빠르게 검증
- **결과 따라**: 동작 OK → E1 design + E2 본격 구현. fail → 원인 기록 + 대안 검토

LightRAG 공식 README 권장은 32B+ 모델인데, 우리는 *gemma2 (9B) 도 되는지* 가 핵심
관심사.

## 사전 준비

### 1. LightRAG 설치

```bash
pip install lightrag-hku
```

### 2. Ollama + 모델

```bash
# Ollama 데몬 (이미 떠있으면 skip)
ollama serve

# 모델 다운로드 (별도 터미널)
ollama pull gemma2              # LLM (~5GB)
ollama pull bge-m3              # embedding (~1.2GB, 1024 dim)

# 데몬 확인
curl http://localhost:11434/api/tags
```

## 실행

```bash
cd examples/lightrag_smoke_test
python smoke_test.py
```

### 옵션 — 다른 모델 시도

```bash
# 더 큰 LLM (LightRAG 권장 수준)
python smoke_test.py --llm qwen2.5-coder:7b

# 다른 embedding (차원 다름)
python smoke_test.py --embed nomic-embed-text   # 768 dim 자동 적용
```

## 무엇이 출력되나

4 단계 + 4 query mode = 단계별 ✓/❌ 명확히. 예:

```
[STEP] import lightrag
  ✓ lightrag, lightrag.llm.ollama import OK

[STEP] instantiate LightRAG (llm=gemma2, embed=bge-m3)
  ✓ LightRAG instance 생성 + storage 초기화 OK

[STEP] insert K-Beauty sample
  입력 텍스트: 753 chars
  ✓ insert 완료 (45.2s)

[STEP] query: "건성 피부에 맞는 보습 크림 추천해줘"
  [naive  ] ( 3.1s) 건성 피부엔 COSRX Advanced Snail 92 ...
  [local  ] ( 8.5s) ...
  [global ] (12.3s) ...
  [hybrid ] (15.1s) ...
```

## 결과 공유 (다음 단계 결정용)

실행 후 *stdout 전체* 를 공유 — 어느 단계까지 OK 인지가 다음 결정 기준:

| 결과 | 다음 단계 |
|---|---|
| 모든 단계 ✓ | E1: design doc + 본격 비교 진행 |
| query 일부만 fail | E1: 어느 mode 만 쓸 지 결정 + 부분 진행 |
| insert 단계 fail | E1: 더 큰 모델 (qwen2.5-coder:32b 등) 시도 + 비용 평가 |
| import / instantiate fail | Plan E 폐기 또는 LightRAG 버전 다운그레이드 검토 |

## 알려진 제약

- **gemma2 (9B) 가 LightRAG 권장 미달** — 32B+ 권장. fail 시 모델 키워서 재시도.
- **첫 실행 시 entity extraction 이 오래 걸림** (수 분, 7B 모델 기준). 인내심 필요.
- **embedding 차원 일관성** — 인덱싱과 query 가 같은 임베딩 모델 사용해야. 한 번
  인덱싱한 후 다른 임베딩 모델로 query 시 차원 mismatch error.

## 정리

smoke test 완료 후 storage 폴더 정리:

```bash
rm -rf examples/lightrag_smoke_test/lightrag_storage_smoke/
```

## 관련

- [`../graphrag_input/`](../graphrag_input/) — 같은 도메인 더 큰 sample (E2 인덱싱용)
- [`../../docs/refactor/15_ollama_graphrag_compatibility.md`](../../docs/refactor/15_ollama_graphrag_compatibility.md)
  — 옛 GraphRAG + Ollama 실패 기록 (Plan E 의 배경)
- [`../../docs/rag_evaluation_framework.md`](../../docs/rag_evaluation_framework.md)
  — 본격 비교 시 사용할 metric (E2+)
