"""
File: src/util/repo_paths.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
무엇인가 (What)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
프로젝트 전체에서 사용하는 경로 상수를 한 곳에서 관리하는 모듈.
``BRONZE_AMAZON``, ``SILVER_TIKTOK`` 같이 medallion 계층 × 도메인 조합 경로를
전부 여기서 정의한다.

왜 있는가 (Why)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 노트북 14 개 + 스크립트 10 개가 같은 데이터 경로를 반복 하드코딩하면
  폴더 이름이 바뀔 때 전수 수정이 필요하다.
- ``__file__`` 기준 앵커링으로 CWD 와 무관하게 동작 — 노트북을 어느 서브폴더
  에서 열어도 import 한 번으로 올바른 절대경로를 얻는다.

어디에 쓰이는가 (Where)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- ``src/util/data_io.py`` — SILVER_TIKTOK 로 tiktok silver 읽기
- ``src/pipelines/build_silver_tiktok.py`` — BRONZE_TIKTOK, SILVER_TIKTOK
- ``src/rag_chatbot/cosmetic_rag_chat/main.py`` — REPO_ROOT (settings.yaml 경로 해석)
- ``notebooks/amazon/01~03`` — BRONZE_AMAZON, SILVER_AMAZON
- ``notebooks/tiktok/`` 각 노트북 — BRONZE_TIKTOK, SILVER_TIKTOK

사용법 (How — 노트북에서 import)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    import sys
    from pathlib import Path
    REPO_ROOT = next(p for p in [Path.cwd().resolve()] + list(Path.cwd().resolve().parents)
                     if (p / ".git").is_dir())
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from util.repo_paths import BRONZE_AMAZON, SILVER_AMAZON

경로 계층 (medallion)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    data/
      bronze/amazon/   raw 수집 CSV (변경 X, 재생성 불가한 것 포함)
      bronze/tiktok/
      silver/amazon/   전처리 완료 bridge (01_amazon_preprocessing 가 생성)
      silver/tiktok/   historical artifact (tiktok_videos_silver.csv)
      gold/            분석 최종 산출물 (미완성)
      archive/         재현 불가 artifact 보존
      amazon/          legacy — 점진적으로 bronze 로 이동 중
      tiktok/          legacy

관련 파일 (Related)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- src/util/data_io.py          ← SILVER_TIKTOK 사용
- src/pipelines/               ← BRONZE_*/SILVER_* 사용
- docs/refactor/16_silver_artifact_origin.md ← silver 단계 설계 결정 기록
"""
from pathlib import Path


def find_repo_root() -> Path:
    """Walk up from this file's location until a .git directory is found.

    Anchored on __file__ so imports work regardless of CWD.
    """
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / ".git").is_dir():
            return parent
    raise RuntimeError(f".git not found above {p}")


REPO_ROOT = find_repo_root()

# Code dirs
SRC = REPO_ROOT / "src"
NOTEBOOKS = REPO_ROOT / "notebooks"

# Data top-level
DATA = REPO_ROOT / "data"

# Data subdirs (legacy — 마이그레이션 진행 중, 점진적으로 BRONZE/SILVER/GOLD 로 이동)
AMAZON = DATA / "amazon"
TIKTOK = DATA / "tiktok"
MODEL = DATA / "model"
RESULTS = DATA / "results"
ARCHIVE = DATA / "archive"
REFERENCES = DATA / "References"

# Medallion architecture (bronze: raw 수집 / silver: 정제 / gold: 분석 input)
BRONZE = DATA / "bronze"
SILVER = DATA / "silver"
GOLD = DATA / "gold"

# 도메인별 경로 (medallion × source)
BRONZE_AMAZON = BRONZE / "amazon"
BRONZE_TIKTOK = BRONZE / "tiktok"
SILVER_AMAZON = SILVER / "amazon"
SILVER_TIKTOK = SILVER / "tiktok"
GOLD_AMAZON = GOLD / "amazon"
GOLD_TIKTOK = GOLD / "tiktok"

# Frequently-used Autogluon model paths
AUTOGLUON_DIR = TIKTOK / "AutogluonModels"
AUTOGLUON_FINAL_DL = AUTOGLUON_DIR / "ag_tiktok_final_dl"
AUTOGLUON_FINAL_DL_V2 = AUTOGLUON_DIR / "ag_tiktok_final_dl_v2"
