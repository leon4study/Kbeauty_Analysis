# 18 — H1+H2 리팩터링: for-loop 벡터화 + Selenium 상수 정리

PR #16 (`9fdf99b`) 의 종합 기록. 두 가지 안전 + ROI 큰 리팩터링을 한 번에 진행:
H1 = 노트북 for-loop → 벡터화, H2 = `main.py` 의 산재 상수 → 상단 명명 상수.

## 배경 / 의도

Explore agent 리포트 (이전 세션) 에서 5 개 리팩터링 기회 발견. 그 중 안전하고
가시적 효과 큰 두 개 (H1, H2) 부터 진행. *진짜 중복 (5+ 위치)* 만 추출 — 사용자
feedback memory ("3 비슷한 라인 < premature abstraction") 준수.

## H1 — for-loop → 벡터화

### 발견된 패턴

3 노트북 (`01_tiktok_eda`, `02_tiktoker_eda`, `07_tiktok_statistic_analysis`) 에
동일한 5 개 함수가 *각자 정의됨*:

- `process_follower` / `process_view` / `process_like` / `process_comment` /
  `process_save` (K/M 단위 파싱, 본질은 동일)
- `preprocess_date` (mixed format 날짜 정규화)
- `new_hash_tag_process` (hashtag/mention 추출)
- `min_ad_cost_range` (인플루언서 사이즈 버켓 + 광고비)
- `upload_y_m` (datetime → "YYYY-MM" 문자열)

모두 `for i in range(len(df)): df.loc[i, col] = ...` 패턴.

### 왜 비효율적

`df.loc[i, col] = value` 는 row 마다:
1. row label lookup (O(log n) ~ O(n))
2. column label lookup
3. dtype 추론 → 필요 시 cast
4. internal index 확장

1.6k rows 노트북에서 *수 초 소요* (체감). 같은 작업 벡터화 시 < 0.1초.

### 적용 패턴

| 옛 패턴 | 벡터화 |
|---|---|
| `for i in range(len(df)): df.loc[i, col] = scalar` | `df[col] = scalar` (broadcast) |
| `for i: df.loc[i, col] = i+1` | `df[col] = np.arange(1, len(df)+1)` |
| `for i: if K in s: ...; elif M in s: ...` | `np.select(condlist, choicelist, default)` |
| `for i: list.append(parsed_x)` (then sum) | `df[col].str.split(',').explode()` |
| `for i: df.loc[i, 'y_m'] = date[:7]` | `df['col'].dt.strftime('%Y-%m')` |
| `for i: if x >= 1M: 'mega'; elif >= 500K: 'mekro'...` | `np.select` with tiered conditions |

### 신설 모듈: `src/util/tiktok_metrics.py`

5 단위 함수로 통합 — 1 모듈, 300 LOC, 모든 함수 thorough docstring 포함:

```python
parse_metric_with_unit(series)         # K/M/B 단위 → 숫자
parse_relative_date(series, today=...) # mixed-format date 정규화
extract_hashtags_and_mentions(series)  # 정규식 #/@ 추출
bucket_influencer_size(df, ...)        # follower → mega/mekro/middle/micro/nano
format_year_month(series)              # datetime → "YYYY-MM"
```

5 process_X 함수가 하나의 `parse_metric_with_unit` 으로 — 입력 컬럼만 바뀜.
도메인 본질은 동일.

### 핵심 아이디어: `np.select` 패턴

if/elif 체인 + for-loop 의 자연스러운 벡터화:

```python
multiplier = np.select(
    condlist=[s.str.endswith(unit) for unit in _UNIT_MULTIPLIER],
    choicelist=list(_UNIT_MULTIPLIER.values()),
    default=1,
)
```

- `condlist`: bool Series 리스트 (각 row 가 어떤 조건 매칭하는지)
- `choicelist`: 매칭 시 사용할 값 (condlist 와 같은 길이)
- `default`: 아무것도 매칭 안 하면 사용할 값
- 첫 번째 매칭 조건이 우선 (Python if/elif 와 동일 의미)

순회 코드 → 컴파일된 NumPy 호출 1 회로 단축.

### 측정 효과

| 노트북 | 옛 for-loop | 남은 (의도적) | 제거 |
|---|---|---|---|
| 01_tiktok_eda | 5 | 1 (tag 집계) | 4 |
| 02_tiktoker_eda | 7 | 0 | 7 |
| 07_tiktok_statistic_analysis | 11 | 2 (tag 집계) | 9 |

총 21 → 3 (남은 3 개는 tag-count 집계 — outer loop 의도 보존, 안쪽 중복 제거만).

## H2 — main.py 상수 정리

### 발견된 패턴

`src/amazon_review_crawler/main.py` 에 wait/sleep/uniform 값 15+ 위치 산재:

```python
wait = WebDriverWait(driver, 3)         # line 74
time.sleep(0.2)                          # line 184
random.uniform(0.05, 0.15)               # line 174, 277, 280
random.uniform(0.7, 1)                   # line 581, 786
time.sleep(2)                            # line 556, 885
# ... 등
```

브랜드별 CSS selector 도 5-way if/elif 로 분기 + check_DrJart 에서 별도 하드코딩.

### 왜 비효율적

- 튜닝 시 grep 으로 일일이 찾아야 함
- anti-bot 회피 / 안정성 조정 어려움
- 새 브랜드 추가 시 if/elif 추가 + check_DrJart 도 별도 수정 = 2 곳 손봐야 함

### 적용

파일 상단에 명명 상수 6 개 + 브랜드 dict 1 개:

```python
WAIT_TIMEOUT_SEC        = 3
SHORT_JITTER_RANGE      = (0.05, 0.15)
PAGE_LOAD_JITTER_RANGE  = (0.7, 1.0)
SCROLL_PAUSE_SEC        = 0.2
HEAVY_PAGE_LOAD_SEC     = 2
NEXT_PAGE_LOAD_SEC      = 1.5

BRAND_FILTER_IDS: dict[str, str] = {
    "COSRX":            "241477",
    "Beauty of Joseon": "591445",
    "Dr. Jart+":        "452045",
    "PURITO":           "312482",
    "I'm from":         "654399",
}
```

각 상수에 *왜 이 값* 주석 (anti-bot 회피, DOM 렌더링 여유 등).

### 브랜드 selector 단순화

옛:
```python
if brand == "COSRX":
    element_locator = (By.CSS_SELECTOR, "#p_123\\/241477 > span > a > span")
elif brand == "Beauty of Joseon":
    element_locator = (By.CSS_SELECTOR, "#p_123\\/591445 > span > a > span")
elif brand == "Dr. Jart+":
    ...
```

신규:
```python
brand_id = BRAND_FILTER_IDS.get(brand)
if brand_id is None:
    raise KeyError(f"등록 안 된 브랜드: {brand!r}")
element_locator = (By.CSS_SELECTOR,
    f"{BRAND_FILTER_CSS_PREFIX}{brand_id}{BRAND_FILTER_CSS_SUFFIX}")
```

5-way if/elif 분기 → dict lookup 으로 단축. 새 브랜드 추가 = dict 한 줄 등록.
`check_DrJart` 도 같은 dict 참조 → 이중 하드코딩 제거.

## 적용 자료구조 / 알고리즘

### 1. `np.select` (벡터 conditional)

if/elif 체인의 벡터 버전. `condlist` 와 `choicelist` 가 짝.
순회 코드를 컴파일된 NumPy 한 줄로 변환.

**사용처**: K/M 단위 분기, 인플루언서 사이즈 버켓, age bucket 등.

### 2. `pd.Series.str.split().explode()` (1-to-many 펴기)

리스트 컬럼 → row 펼치기. SQL 의 ``UNNEST`` 와 동일.
옛 `for i: sum(lists, [])` 패턴의 직접 대체.

**사용처**: hashtag 문자열 ("a,b,c") → row 단위 ("a", "b", "c").

### 3. `dict[str, str]` lookup (분기 대체)

if/elif 체인의 가장 간단한 대체. 새 항목 추가 = dict 한 줄.
이중 하드코딩 (같은 값을 여러 곳에 작성) 방지.

**사용처**: 브랜드 → CSS ID, search_term → keyword 등.

### 4. `pd.Series.dt.strftime()` (datetime → 문자열)

`.astype(str).str[:7]` 처럼 *문자열 조작* 우회 — datetime 객체에 직접
포맷 지정. 더 안전 (dtype 보존) + 빠름.

### 5. 가드 + 명명 상수 패턴

```python
WAIT_TIMEOUT_SEC = 3  # 왜 3초인지 주석
wait = WebDriverWait(driver, WAIT_TIMEOUT_SEC)
```

매직 넘버 제거 + 의도 명시. 튜닝 시 한 곳만 수정.

## 학습 포인트

1. **`df.loc[i, col]=` 는 hot loop 의 함정** — 인덱싱 cost 가 크고 dtype 추론
   매번 발생. 작은 데이터셋에선 안 보이지만 1k+ rows 부터 체감.

2. **5 함수가 동일 패턴이면 1 함수로 통합** — 입력 컬럼이 다르다고 별도 함수
   만들지 말기. `parse_metric_with_unit(series)` 가 5 process_X 전체 대체.

3. **`np.select` 가 if/elif 의 벡터 형제** — 익숙해지면 거의 모든 row 단위
   분기에 적용 가능.

4. **상수는 *왜* 주석과 함께** — `WAIT_TIMEOUT_SEC = 3` 만으로는 의미 불명.
   "DOM 렌더링 + script 실행 여유" 같은 *왜* 가 있어야 한 달 후 튜닝 시 안전.

5. **behavior 보존 우선** — `ad_cost = follower * 20000` 이 단위적으로 의심
   스러워도 옛 분석 결과와 일관성 위해 보존. 정정은 별도 PR 로 (refactor 와 별개).

## 관련 commits

```
3fa1972 refactor(H1+H2): 노트북 for-loop 벡터화 + main.py 상수 정리 (#16)
```

## 관련 docs

- [`17_2026_05_session_cleanup.md`](17_2026_05_session_cleanup.md) — 직전 세션 정리 종합 (data legacy, bronze naming 등)
- [`02_path_portability.md`](02_path_portability.md) — REPO_ROOT 패턴 (벡터화 함수가 동일 사용)
- [`EXPERIMENTS_PLAYBOOK.md`](EXPERIMENTS_PLAYBOOK.md) — 변종 정리 표준
