# fake_data_gen 통합 + utils 추출

`src/fake_data_gen/` (top-level src) 와 `src/project_code/fake_data_gen/` (project_code 안) 두 곳에 분산돼있던 것을 한 폴더로 통합 + 코드 중복 추출.

## 배경 / 의도

K-beauty 분석에 필요한 합성 customer 데이터 (랜덤 미국 주소, 인구 비율 분포 등) 를 생성하는 도구들. 두 위치에 분산:

```
src/fake_data_gen/
└── address.ipynb                    (1 file — 깨진 scratch 였음)

src/project_code/fake_data_gen/
├── add_ageGroup_Gender_by_brand.ipynb    (브랜드별 연령/성별 추가)
└── address/                              (랜덤 주소 도구 모음)
    ├── crawl_random_address.py          (selenium 으로 postcodebase.com 크롤링)
    └── address_ratio.ipynb              (주별 인구 비율 + 주소 파서)
```

또한 `crawl_random_address.py` 와 `address_ratio.ipynb` 가 **같은 함수 + 같은 상수를 따로** 가지고 있었음.

## 발견된 코드 중복

### `addr_to_df()` — postcodebase 형식 주소 문자열 → DataFrame
- 같은 정규식 파서가 **두 파일에 동일** 정의
- 형식: `"445 S ARDMORE AVE LOS ANGELES CA 90020-3265 USA"` → `{detailed_address, city, state, zipcode}`

### 미국 주별 인구 비율
- `crawl_random_address.py`: `states_population` (list of `[code, count]`, 50 entries)
- `address_ratio.ipynb`: `states_population_percentage` (dict `{code: pct}`) + 별도 계산
- → **같은 정보 두 표현** (list vs dict). 한쪽 수정하면 다른 쪽 stale.

### 깨진 scratch — `src/fake_data_gen/address.ipynb`
- 9 cells, 전체 흐름:
  - cell 1: `os.chdir("/Users/jun/GitStudy/Data_4/Data/project5/address")` (stale)
  - cell 2: read `random_address_LA.csv` — **출력엔 IN state 주소 표시** (LA 파일 이름인데 IN 주소!)
  - cell 4: `from util import slack`
  - cell 5: `send_msg("haha")` → **NameError** (import 한 건 module, 호출은 함수명)
  - cell 6: `import pltfont` — 알 수 없는 라이브러리
- 작동하지 않는 sketch. 폐기 결정.

## 처리

### Phase 1 — 새 공유 모듈 `address_utils.py` 작성

`src/fake_data_gen/address/address_utils.py`:

| Public symbol | 역할 |
|--------------|------|
| `STATE_POPULATION_PCT: dict[str, float]` | 50 주별 인구 비율 (출처: 정부 추계 근사치) |
| `addr_to_df(address_block: str) -> pd.DataFrame` | 줄바꿈 구분 주소 텍스트 → DataFrame. 매칭 실패 라인은 조용히 누락 (입력 노이즈 robust) |
| `compute_state_quotas(total_count: int) -> list[tuple[str, int]]` | 전체 합성 주소 개수 → 주별 quota (`math.ceil` 로 과소표집 방지) |

### Phase 2 — 파일 통합 + 리팩터

```
src/fake_data_gen/
├── __init__.py                              (NEW)
├── add_ageGroup_Gender_by_brand.ipynb       (이동 + REPO_ROOT 기반 경로)
└── address/
    ├── __init__.py                          (NEW)
    ├── address_utils.py                     (NEW — 공유 모듈)
    ├── crawl_random_address.py              (refactor — utils 사용 + function-ize + REPO_ROOT)
    └── address_ratio.ipynb                  (단순화 — utils import + 데모만)
```

#### `crawl_random_address.py` 리팩터
- 원본 150줄 monolithic → 함수 4개:
  - `_click_copy_button(driver)`, `_click_regen_button(driver)` (저수준 헬퍼)
  - `crawl_state(driver, quota)` — 한 주에 대해 quota 만큼 수집
  - `main()` — 모든 주 순회 + 누적 csv 저장
- 중복된 `addr_to_df`, `states_population` 제거 → `from address_utils import addr_to_df, compute_state_quotas`
- stale `Data_4` 경로 → `from util.repo_paths import DATA; ADDRESS_DIR = DATA / "address"`
- `if __name__ == "__main__":` guard 추가
- 모든 함수에 한국어 docstring (캡차 회복 의도, postcodebase API 가정 등)

#### `address_ratio.ipynb` 단순화
원본 8 cells (200줄짜리 하드코딩 sample address + 중복 함수) → 6 cells:
- import (`STATE_POPULATION_PCT`, `addr_to_df`, `compute_state_quotas`)
- TOTAL_COUNT = 12797
- `quotas = compute_state_quotas(TOTAL_COUNT)` 결과
- 작은 sample 4줄로 `addr_to_df` 동작 데모

#### `add_ageGroup_Gender_by_brand.ipynb` 정리
- stale `Data_4/Data/project5/...` 경로 → `from util.repo_paths import DATA`
- 하드코딩된 csv 절대 경로 → `DATA / "brands" / "items" / "..."` 구조

### Phase 3 — `src/project_code/fake_data_gen/` 폴더 삭제
이동 후 비어있는 옛 폴더 정리. `src/project_code/fake_data_gen/` 가 사라짐.

### Phase 4 — `src/fake_data_gen/address.ipynb` (깨진 scratch) 폐기
복구 가치 0. git history 에 남으니 충분.

## canonical 위치

```
src/fake_data_gen/
├── __init__.py
├── add_ageGroup_Gender_by_brand.ipynb       (브랜드별 연령/성별 추가)
└── address/
    ├── __init__.py
    ├── address_utils.py                     (공유 모듈)
    ├── crawl_random_address.py              (function-ize + utils 사용)
    └── address_ratio.ipynb                  (utils import + 데모)
```

## 학습 포인트

1. **같은 디렉터리 이름이 두 곳에 있으면 의도 의심**: `fake_data_gen` 이 두 위치에 — 하나는 정리 후 잊혀진 잔재, 하나가 진짜. 항상 비교 우선.
2. **list vs dict 같은 표현 차이도 동일 정보 중복**: 한 표현 (dict) 만 canonical 로 두고, 다른 (list) 가 필요하면 변환 함수로.
3. **깨진 scratch 는 빨리 폐기**: NameError 나는 셀, 데이터-라벨 불일치 (LA 파일에 IN 주소) 같은 건 지금 도움 안 됨 + 미래에 헷갈림.
4. **`__init__.py` 는 패키지 인식의 신호**: 빈 파일이라도 `pip install -e .` + `setuptools.packages.find` 가 인식하려면 필요.
5. **상수도 함수처럼 추출 가치**: `STATE_POPULATION_PCT` 같이 비자명한 데이터 (50개 주 비율) 는 한 곳에서 정의 + 모듈명으로 의미 전달 (`from address_utils import STATE_POPULATION_PCT`).
6. **`math.ceil` 의 의도 명시 docstring**: "왜 round 가 아니라 ceil?" — 답: 과소표집 방지. 이런 작은 결정도 docstring 으로 남기면 미래의 reader 에게 가치.

## 관련 commits

- `60798a2` — refactor: dissolve src/project_code; consolidate fake_data_gen with shared utils