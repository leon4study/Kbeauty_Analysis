# Experiments Playbook

변종 (실험 분기, progressive iteration, 가설 검증 변형) 을 어떻게 정리할지 정한 표준.

> **핵심 원칙**: 폴더가 1순위. 폴더를 열었을 때 한 눈에 의도가 보여야 함. git history/branch/tag 는 보조용.

---

## 1. 폴더 표준 구조

도메인 (rag_chatbot/ollama, notebooks/tiktok, data/model 등) 마다 동일:

```
<domain>/
├── README.md                ← 진입점 (필수). 의도 + 변종 카탈로그 + 진화 흐름
├── (canonical 파일들)        ← main 으로 채택된 것
└── experiments/             ← 곁가지 분기 (선택, 영양가 있을 때만)
    ├── <variant1>
    └── <variant2>
```

- **README.md 가 진입점**: 도메인 폴더 열자마자 의도 + 변종 차이 1줄씩 보여야 함. 미래의 본인이 30초 만에 파악 가능해야 함.
- **`experiments/` 서브폴더는 선택**: 변종 코드 자체가 영양가 있을 때만. README 한 단락으로 충분하면 만들지 않음.

---

## 2. 통폐합 패턴 (영양가 있게 묶기)

변종을 단순 보존하지 말고, 가능하면 통합해서 영양가↑.

| 패턴 | 케이스 | 방법 |
|---|---|---|
| **A. 단일 파일 + 주석 진화** | progressive iteration (ch1→ch7, calculator add/sub/...) | main 파일 1개에 `# v1: 기본, v2: X 추가, v3: Y 도입` 주석으로 변경점 누적 |
| **B. 파라미터화** | 가설 검증 변종 (apple+banana vs apple+orange, with/without ngram) | 1개 파일 + 파라미터 (`EXCLUDE_NAMES = []`, `USE_NGRAM = False`) 로 케이스 흡수 |
| **C. README 카탈로그** | 거대한 ipynb (50M+) 또는 통합 위험한 변종 | 같이 두고 README 표 1개로 차이 1줄씩. 코드 안 건드림 |

### 어떤 패턴을 언제?
- **`.py` 변종, 대부분 같음, 100줄 이내** → A 또는 B
- **`.ipynb` 변종, 50M+, 출력 셀 손상 위험** → C
- **별개 stack/방법론 변종** (LangChain vs LlamaIndex 같은) → C, 별도 파일 유지 + README 에 차이 표시
- **폐기된 변종 복원 가치 있나?** README 1단락이 변종 코드 6개보다 영양가↑ 인 경우가 많음. `git show <commit>:<path>` 명령어 README 에 적어두면 누구든 꺼낼 수 있음.

---

## 3. 분류 결정 트리

변종 발견 시 5초 결정:

| 질문 (Yes 면 분류) | 분류 |
|---|---|
| K-beauty 도메인 무관, 학습 sketch (LlamaIndex tutorial 등) ? | `~/GitStudy/utils/legacy_*` (외부 보존) |
| 같은 도메인 progressive iteration ? | 통폐합 A 또는 README 카탈로그 |
| 가설 검증 분기 (`_without_X`, `_v2`, `_ngram_added`) ? | 통폐합 B 또는 README 카탈로그 (C) |
| 중간 산출물 (cache, pickle, parquet 출력) ? | 폐기 + `.gitignore` |
| 빈 placeholder, 임시 copy, 단순 백업 ? | 폐기 |
| 별개 stack 시도 (LangChain vs LlamaIndex) ? | 별도 파일 유지 + README 에 차이 |

---

## 4. README per domain 템플릿

도메인 폴더 README.md 의 표준 섹션:

```markdown
# <domain name>

## 의도
한 단락. 이 도메인이 무엇을 하려는지, 왜 만들었는지.

## canonical 파일
- `<file>` — 무엇을 함, 왜 이게 main 인지

## 변종 카탈로그
| 변종 | 가설/차이 | 처분 |
|---|---|---|
| `<name>` | 무엇을 다르게 시도, 무엇을 검증 | main 채택 / experiments/ 보존 / 폐기 (git show 복원 가능) |

## 진화 흐름 (선택)
v1 (기본) → v2 (X 추가) → v3 (Y 도입, main)

## 관련 docs
- [docs/refactor/09_X.md](../../docs/refactor/09_X.md) — 자세한 정리 기록
```

---

## 5. 실용 명령어

### ipynb 변종 비교 (50M 노트북도 30초)
```bash
# markdown header + 변수 할당만 추출해서 diff
jupyter nbconvert --to script --stdout A.ipynb | grep -E "^# ###|^[a-z_]+ =" > /tmp/A.summary
jupyter nbconvert --to script --stdout B.ipynb | grep -E "^# ###|^[a-z_]+ =" > /tmp/B.summary
diff /tmp/A.summary /tmp/B.summary
```

### 폐기된 변종 복원 (git show)
```bash
# commit 직전 (또는 직후) 의 파일 꺼내기
git show <commit>^:<path/to/file> > <new/path>

# 예: ch1 복원
git show 3a99a56^:src/rag_chatbot/ollama/gradio_rag_ch1.py > /tmp/ch1.py
```

### nbdime / jupytext (선택)
```bash
pip install nbdime jupytext
nbdime diff A.ipynb B.ipynb       # ipynb 전용 diff
jupytext --to py A.ipynb           # ipynb → .py 동기화 (git diff 가능)
```

---

## 6. 외부 보존 (`~/GitStudy/utils/legacy_*`) 기준

**도메인 무관한 학습 흔적만** 외부로:
- ✅ 외부: `legacy_crawlers/` (selenium 학습), `db_patterns/` (mysql 학습), `legacy_rag/llamaindex_ollama_demo.py` (LlamaIndex tutorial)
- ❌ 외부 X (프로젝트 안에): K-beauty 도메인 흔적 (ollama 챗봇 변종, graphrag 실험 분기, tiktok 분석 변종)

이미 외부에 있는 K-beauty 도메인 흔적은 시간 날 때 프로젝트 안 `experiments/` 또는 README 로 통폐합.

---

## 7. 실제 적용 사례

| 도메인 | 변종 | 적용 패턴 |
|---|---|---|
| `src/rag_chatbot/ollama/` | ch1~ch8, OllamaLLM v1/v2, LangChain 변종 | C + git show 안내 (README + [09_ollama_rag_variants](09_ollama_rag_variants.md)) |
| `notebooks/tiktok/tiktoker_recommend.ipynb` | ver.1/v2/v3 (한 노트북 안) | A 그 자체 (이미 통합됨) + [12_tiktok_recommendation_evolution](12_tiktok_recommendation_evolution.md) |
| `notebooks/amazon_tiktok/` | _ngram_added, _1228, _without_wonyoung, _copy | C (50M ipynb, 통합 위험. README 카탈로그) |
| `notebooks/tiktok/tiktok_marketing_modeling*.ipynb` | v1/v2 | C (같이 두고 README) |

---

## 관련 docs

- [README.md](README.md) — refactor docs 전체 인덱스
- [09_ollama_rag_variants.md](09_ollama_rag_variants.md) — ollama 변종 정리 (이 PLAYBOOK 패턴 C 의 첫 사례)
- [12_tiktok_recommendation_evolution.md](12_tiktok_recommendation_evolution.md) — tiktoker_recommend ver.1/v2/v3 진화 (패턴 A)
