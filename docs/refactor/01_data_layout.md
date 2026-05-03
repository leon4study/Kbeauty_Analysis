# Data 레이아웃 평면화

`data/` 8.2GB 가 `data/project5/...` 라는 한 단계 아래에 다 묶여있던 것을 의미 단위로 평면화 + 무거운 archive 분리.

## 배경 / 의도

`data/project5/` 라는 prefix 가 모든 데이터에 붙어있었음. 이 repo 자체가 project5 결과물이라 **prefix 가 의미 없는 noise**. 또한 `final/` (3.8GB), `ppt/` (1.4GB), `dashboard/` (1.3GB, mp4) 같은 거대한 아카이브가 활성 데이터 (`amazon/`, `tiktok/`, `model/`) 와 섞여있어서 어디가 "쓰는 데이터" 고 어디가 "정리 안 한 산출물" 인지 분간이 어려웠음.

## 변경 전 / 후

| 변경 전 (8.2GB, project5/ 안에 다 박힘) | 변경 후 (의미 단위 평면화) |
|----------------------------------------|--------------------------|
| `data/amazon/` (빈 폴더!) | (삭제) |
| `data/tiktok/` (AutogluonModels, dashboards) | `data/tiktok/` (아래 + project5 자료 흡수) |
| `data/project5/amazon/` (51MB, 브랜드 csv) | `data/amazon/` |
| `data/project5/tiktok/` (9.7MB) | (위 `data/tiktok/` 와 병합 — 이름 충돌 0건 확인) |
| `data/project5/model/` (76MB, graphrag) | `data/model/` |
| `data/project5/results/` | `data/results/` |
| `data/project5/{address, brands, References}/` | `data/{address, brands, References}/` |
| `data/project5/final/` (3.8GB, 제출본 zip) | `data/archive/final/` |
| `data/project5/ppt/` (1.4GB) | `data/archive/ppt/` |
| `data/project5/dashboard/` (1.3GB mp4) | `data/archive/dashboard/` |
| `data/project5/gdrive/` (955MB 백업) | `data/archive/gdrive/` |
| `data/project5/{중간발표, 제출용}/` | `data/archive/{중간발표, 제출용}/` |
| `data/project5/` 루트 jpg/pdf/screenshot/zip | `data/archive/` 직접 |

## 중복 / 충돌 검사

병합 전에 확인:
- `data/amazon/` (top-level) vs `data/project5/amazon/` — top-level 은 **빈 폴더** → 단순 승격
- `data/tiktok/` vs `data/project5/tiktok/` — 파일/폴더 이름 **충돌 0건** → 안전 병합

## 처리 방식 / 학습 포인트

`zsh` 의 함정:
- `shopt -s dotglob` (bash) ≠ zsh — zsh 에선 `setopt dotglob` 또는 `*` 대신 `*(D)` 같은 다른 syntax. 잘못 쓰면 hidden 파일 (`.DS_Store` 등) 이 안 옮겨짐 → 빈 폴더가 archive 로 잘못 들어감 (실제 발생, 추가 정리 필요했음).

코드 영향:
- 노트북 + .py 의 모든 `data/project5/amazon` → `data/amazon` 일괄 변경 (정규식 치환 + 검증).
- 절대 경로는 portable path (`REPO_ROOT` 기반) 로도 함께 마이그레이션 ([02_path_portability.md](02_path_portability.md) 참고).

## canonical 위치

```
data/
├── amazon/             (브랜드별 items/reviews csv)
├── tiktok/             (AutogluonModels, dashboards, 키워드 csv 등)
├── model/              (GraphRAG 출력 폴더들)
├── address/            (랜덤 주소 csv)
├── brands/, References/, results/
└── archive/            (final, ppt, dashboard 비디오, gdrive 백업, 중간발표, 제출용 등 7.5GB)
```

## 학습 포인트

1. **무의미한 prefix 는 제거**: 모든 자식이 같은 prefix 를 갖는다면 그 prefix 는 정보 없음. 그냥 한 단계 위로 끌어올림.
2. **활성 vs 아카이브 분리**: 무거운 산출물/제출본을 별도 디렉터리로 빼면 활성 데이터의 시각적 노이즈가 크게 줄어듦. `data/archive/` 는 전체 8.2GB 중 7.5GB 차지 — 무거운 거 한 곳에 모아두고 나중에 외부 storage 로 옮길 결정도 쉬워짐.
3. **zsh vs bash 셸 차이**: `shopt` 는 bash 전용. cross-shell 스크립트는 python 으로 짜는 게 안전 (실제로 이번 세션에선 python 으로 검증 + 후처리).
4. **데이터 이동은 코드 경로 변경과 짝**: data 만 옮기고 코드를 안 고치면 침묵 실패 (`FileNotFoundError`). 두 가지를 같이 해야 함.

## 관련 commits

- `e88f614` — refactor: flatten data/ layout, extract util modules, portable paths