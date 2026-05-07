"""Standard repo / data paths for Kbeauty Analysis.

Resolves all paths from the repo root (marked by .git), so they work
regardless of where the repo is cloned or which subdirectory is the CWD.

Notebook usage:

    import sys
    from pathlib import Path
    REPO_ROOT = next(p for p in [Path.cwd().resolve()] + list(Path.cwd().resolve().parents)
                     if (p / ".git").is_dir())
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from util.repo_paths import DATA, AMAZON, TIKTOK
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
