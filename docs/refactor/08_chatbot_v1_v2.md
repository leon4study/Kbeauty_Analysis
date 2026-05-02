# RAG 챗봇 v1 / v2 진화 정리

`src/rag_chatbot/0209/` (v1, 날짜 폴더) 와 `src/rag_chatbot/cosmetic_rag_chat/` (v2, 의미 있는 이름) — 같은 챗봇의 두 단계가 별도 폴더로 남아있던 것을 v2 단일로 정리 + 시각화 코드 추출.

## 배경 / 의도

K-beauty 화장품 성분 RAG 챗봇 (OpenAI cloud + MS GraphRAG 스택, Gradio UI) 을 두 단계로 진화시킨 흔적:

| 폴더 | 의미 | 메인 진입 |
|------|------|----------|
| `0209/` | 2월 9일 작업한 시점 (날짜 폴더) | `chatbot.py` |
| `cosmetic_rag_chat/` | "화장품 RAG 챗봇" (의미 있는 이름) | `main.py` |

둘이 거의 같은 일을 하면서 양쪽 다 `indexing/`, `lancedb/`, `openaitest_0206/` 를 가지고 있었음.

## 변종 분석

### `0209/` 안의 chatbot 변종 4개

| 파일 | lines | 차이 |
|------|------:|------|
| `chatbot.py` | 172 | "옛 v1" — 단순 `gr.Interface()` UI |
| `chatbot_ver2.py` | 214 | chatbot.py 와 **기능 100% 동일**, black 포매터 적용본만 (멀티라인 들여쓰기 등) |
| `old_ver_chatbot.py` | 172 | chatbot.py 와 **byte-identical** (diff 0줄) — 단순 백업본 |
| `chatbot.ipynb` | 6 cells | 짧은 sketch (import 몇 개 + 셀 몇 개), 본격 챗봇 코드 아님 |

### `0209/` vs `cosmetic_rag_chat/` 비교

| 비교 항목 | 0209 | cosmetic_rag_chat | 결론 |
|---------|------|-------------------|------|
| 메인 코드 | `chatbot.py` (172줄) | `main.py` (172줄, UI 다름) | 33줄 diff — UI 진화 |
| **Gradio UI** | `gr.Interface()` 단순 텍스트 박스 | `gr.Blocks()` + 헤더 + 마크다운 + 버튼 분리 | v2 명백히 발전 |
| 디버그 로그 | `print("result in gradio_query:", result)` | (제거) | v2 가 정리된 상태 |
| `indexing/settings.yaml` | base path: `Data_4/Data/project/project5/...` | `Data_4/Data/project5/...` | 둘 다 stale, 다른 위치 |
| `lancedb/` | 18MB, version 1~10 (10번 인덱싱 누적) | 3.6MB, version 1~2 (깨끗한 재인덱싱) | 같은 데이터 580 rows, cosmetic 이 12분 더 늦은 깨끗한 버전 |
| `openaitest_0206/` | 35MB | 35MB | **diff 0건 — 100% 동일** |
| 추가 파일 | (없음) | `final_graphrag_LLM.py` (NetworkX 그래프 시각화 + 챗봇 통합) | v2 만 가짐 |

### 시각화 코드 중복

`cosmetic_rag_chat/final_graphrag_LLM.py` 의 `apply_parquet_files()` 와 `graphrag_viewer/graphRAG_gradio.py` 의 `plot_graph()` — **거의 같은 로직** (Parquet 로드 → networkx DiGraph → matplotlib spring layout → BytesIO/PIL Image) 을 따로 가지고 있었음. 약간씩 진화하면서 갈라짐:

| 기능 | `graphRAG_gradio.py` (graphrag_viewer/) | `apply_parquet_files()` (final_graphrag_LLM.py) |
|------|-----------|-------------|
| Parquet 로드 + 그래프 생성 | ✓ | ✓ (동일) |
| `link_columns` 추가 처리 (`text_unit_ids`, `entity_ids`, `relationship_ids`) | ✓ (richer) | ❌ |
| `graph_data` 글로벌 저장 (검색 연동) | ❌ | ✓ |
| Standalone `iface.launch()` | ✓ | ❌ (챗봇 통합) |

## 처리

### v1 → v2 통합 (0209 통째 폐기)

v2 (`cosmetic_rag_chat`) 가 canonical. v1 (`0209`) 의 모든 파일이:
- (a) **후계 있음** (`main.py` 가 `chatbot.py` 발전형)
- (b) **byte-identical 중복** (`old_ver_chatbot.py`)
- (c) **포맷만 다름** (`chatbot_ver2.py`)
- (d) **재생성 가능** (lancedb)
- (e) **완전 동일 사본** (openaitest_0206)

→ 0209 폐기 안전. 단, **v1 챗봇 코드 자체는 학습 가치 있음** (UI 진화 비교 가능) — `chatbot.py` 만 `~/GitStudy/utils/legacy_rag/chatbot_v1.py` 로 보존.

### 시각화 코드 DRY (`plot.py` 추출)

새 모듈 `src/rag_chatbot/graphrag_viewer/plot.py`:

```python
parquet_to_graph(parquet_file)  -> (DiGraph, DataFrame)
render_graph_image(G)            -> PIL.Image
plot_graph(parquet_files)        -> list[Image | str]
```

`link_columns` 풍부한 처리 (graphrag_viewer 의 옛 plot_graph 가 가진 부분) + `plt.close(fig)` 메모리 누수 방지 (둘 다 없던 것) 포함.

호출부:
- `graphRAG_gradio.py`: 65줄 → **24줄** (plot_graph import + Gradio launch 만)
- `final_graphrag_LLM.py`: `apply_parquet_files()` 인라인 코드 → `parquet_to_graph` + `render_graph_image` 호출. `pandas`, `networkx`, `matplotlib`, `PIL`, `BytesIO` import 5개 제거됨

## canonical 위치

```
src/rag_chatbot/
├── __init__.py
├── cosmetic_rag_chat/
│   ├── __init__.py
│   ├── main.py                       (v2 메인 — gr.Blocks UI)
│   ├── final_graphrag_LLM.py         (시각화 + 챗봇 통합, plot.py 사용)
│   └── (indexing/, lancedb/ 등)
└── graphrag_viewer/
    ├── __init__.py
    ├── plot.py                       (parquet_to_graph, render_graph_image, plot_graph)
    └── graphRAG_gradio.py            (24줄, plot_graph import + Gradio Interface)
```

## 학습 노트 보존 위치

```
~/GitStudy/utils/legacy_rag/
└── chatbot_v1.py                     (옛 0209/chatbot.py)
```

## 학습 포인트

1. **날짜 폴더 vs 의미 폴더**: `0209/` 같은 날짜 폴더는 작업 시점 표시는 되지만 **무엇을 하는지** 안 보임. 작업 안정화되면 의미 있는 이름 (cosmetic_rag_chat) 으로 마이그레이션.
2. **byte-identical 중복은 명백 폐기**: diff 0줄이면 의심할 여지 없음.
3. **포매터-only 차이도 폐기**: 같은 로직, 다른 들여쓰기 — 실용적 가치 0. 하나만 남김.
4. **lancedb 같은 binary store 비교**: schema + row count + version timestamp 로 "같은 데이터의 다른 인덱싱 단계인지" 판별 가능. `lance.dataset(...).schema`, `.count_rows()`, `.versions()`.
5. **시각화 코드 같은 게 두 곳 → 즉시 추출 후보**: 두 코드 미세하게 갈라지면 한 쪽은 버그 픽스, 다른 쪽은 그대로 남는 식으로 어긋나기 시작. 일찍 추출.
6. **추출 시 더 풍부한 기능 + bug fix 합치기**: `link_columns` (graphrag_viewer 만 가진 것) + `plt.close()` (둘 다 없던 메모리 누수 방지) — 추출이 단순 복사가 아니라 quality 향상 기회.

## 관련 commits

- `2d248cd` — refactor(rag_chatbot): drop 0209 v1, extract shared graph plot module