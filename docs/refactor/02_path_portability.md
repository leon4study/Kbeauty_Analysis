# 경로 portability — REPO_ROOT 패턴 + pyproject 패키지화

repo 안 코드/노트북이 가지고 있던 **하드코딩된 절대 경로** (`/Users/jun/GitStudy/...`) 를 자기 위치 기반 자동 해석으로 바꿔서 **clone/fork 한 다른 사람이 그대로 실행 가능**하게 만든 작업.

## 배경 / 의도

11개 노트북 + 다수 .py 가 다음 같은 패턴을 가지고 있었음:
```python
DATA_PATH = "/Users/jun/GitStudy/Data_4/Data/project/project5/amazon"
os.chdir(DATA_PATH)
```
- `/Users/jun/...` → 다른 사용자에겐 절대 안 통함
- `Data_4/...` → 옛 경로 (현재 repo 위치 아님)
- `os.chdir` → 잡 도중에 CWD 가 바뀌면 다른 셀의 상대 경로도 깨짐

clone/fork 한 사람이 그대로 실행할 수 있어야 portfolio 가치 있음.

## 두 단계로 진행

### 1단계 — REPO_ROOT 자동 검색 패턴 (인라인)

각 셀에 4-5 줄 bootstrap 추가:
```python
from pathlib import Path
REPO_ROOT = next(p for p in [Path.cwd().resolve()] + list(Path.cwd().resolve().parents)
                 if (p / ".git").is_dir())
DATA_PATH = str(REPO_ROOT / "data" / "amazon")
```
원리: CWD 부터 위로 올라가며 `.git` 폴더 만나면 그 위치가 repo root.

장점: 의존성 0, 어떤 환경에서도 동작.
단점: 셀마다 5줄 boilerplate.

### 2단계 — `pyproject.toml` + `pip install -e .` 로 패키지화

`pyproject.toml` 추가:
```toml
[project]
name = "kbeauty-analysis"
[tool.setuptools.packages.find]
where = ["src"]
```

→ `pip install -e .` 한 번 실행하면 `src/util/`, `src/rag_chatbot/` 등이 패키지로 인식됨.

이후 노트북/스크립트에서 한 줄 import 로 해결:
```python
from util.repo_paths import DATA, AMAZON, TIKTOK, AUTOGLUON_FINAL_DL
```

## `repo_paths.py` 설계 결정

`__file__` 기반 검색 (CWD 무관):
```python
def find_repo_root() -> Path:
    p = Path(__file__).resolve()  # ← 이 모듈 파일의 위치
    for parent in p.parents:
        if (parent / ".git").is_dir():
            return parent
    raise RuntimeError(...)

REPO_ROOT = find_repo_root()
DATA = REPO_ROOT / "data"
AMAZON = DATA / "amazon"
TIKTOK = DATA / "tiktok"
# ... 등
```

이유: 만약 `Path.cwd()` 기반이면, 외부 (예: `/tmp`) 에서 `from util.repo_paths import ...` 한 순간 `.git` 찾기 실패. `__file__` 은 모듈 위치 (= 항상 repo 안) 라 안전.

## Jupyter 의 한계

노트북은 `__file__` 이 없음 (CWD 기반). 환경별 차이:

| 환경 | 노트북 자기 경로 가져오는 법 | 신뢰도 |
|------|------------------------|-------|
| VSCode | `__vsc_ipynb_file__` (전역 자동 주입) | VSCode 전용 |
| Classic Jupyter | `ipynbname` 패키지 설치 필요 | 외부 의존 |
| JupyterLab | JS injection 트릭 | 브래틀 |
| Colab | `google.colab.drive` API | Colab 전용 |

→ **표준 X**. 가장 robust 한 건 **CWD 에서 `.git` 까지 위로 올라가는 패턴** (Jupyter 가 repo 안에서 시작된다는 가정만 필요).

## 변경 영향 범위

11개 노트북:
- `EDA.ipynb`, `amazon_tiktok_analysis*.ipynb` (5종), `lemmatized_full_pipeline.ipynb`, `tiktok_marketing_modeling*.ipynb` (2종), `tiktok_statistic_analysis.ipynb`, `temp.ipynb`

각 노트북에서:
- 절대 경로 ("/Users/jun/...") → `REPO_ROOT` 기반 또는 `DATA / "subpath"`
- `model_path = "..."` → `AUTOGLUON_FINAL_DL` 같은 상수
- 경로 박힌 셀에 `import` 한 줄로 단축

## canonical 위치

```
src/util/repo_paths.py    (REPO_ROOT, DATA, AMAZON, TIKTOK, MODEL, ARCHIVE, ... 상수들)
pyproject.toml             (`pip install -e .` 가능하게)
src/util/__init__.py       (패키지 인식용)
```

## 학습 포인트

1. **`Path(__file__)` vs `Path.cwd()`**: 둘 다 anchor 후보. 모듈에선 `__file__` 이 안전, 노트북에선 안전한 `__file__` 이 없으니 cwd-walk-up.
2. **`pyproject.toml` 의 `where = ["src"]`**: src layout 표준. 패키지 로직과 설정/문서를 명확히 분리.
3. **`pip install -e .` 의 부수효과**: editable install 이 `*.egg-info` 폴더 만듦 → `.gitignore` 에 추가 필요.
4. **Bootstrap boilerplate trade-off**: 셀마다 5줄 vs 한 줄 import. 후자는 setup 단계 (`pip install -e .`) 가 추가되지만, 한 번만 하면 모든 노트북이 깔끔.
5. **Path constants 의 가치**: `DATA / "amazon"` vs `f"{REPO_ROOT}/data/amazon"` — 전자는 IDE 자동완성 + typo 방지 + 의도 명확.

## 관련 commits

- `e88f614` — refactor: flatten data/ layout, extract util modules, portable paths