# util 모듈 추출 + 정리

여러 곳에 흩어져있던 헬퍼들을 `src/util/` 단일 패키지로 모으고, 코드 곳곳의 명백한 중복을 함수로 추출.

## 배경 / 의도

리팩터 시작 시점:
```
util/                              (top-level, 4 파일)
├── faker.ipynb                    (3줄짜리 Faker 라이브러리 테스트)
├── kaggle_link_to.py              (kagglehub 다운로드 헬퍼, 사용처 0)
├── print_tree.py                  (디렉터리 트리 출력, 사용처 0)
└── slack1.py                      (Slack webhook 알림)
```

문제:
- 위치가 src/ 밖. import 일관성 없음.
- 이름 어색 (slack1 — "1" 의미 불명)
- 사용처 검사 시 `import slack1` 패턴이 7곳 (crawler 등) 인데, src/util/ 로 옮긴 뒤로 모두 깨진 채로 있었음 (실행 안 해서 모름)

## 처리

### 1단계 — `util/` → `src/util/` 이동 + 정리
- `slack1.py` → `slack.py` (이름 정리, "1" 제거 + docstring 추가)
- 사용처 7곳의 `from slack1 import send_msg` → `from util.slack import send_msg`
- `__init__.py` 추가 (패키지화)

### 2단계 — dead code 분류 + 학습 자료 보존 위치로
| 파일 | 사용처 | 처분 |
|------|--------|------|
| `faker.ipynb` | 0건 | `~/GitStudy/utils/` 로 보존 (다른 프로젝트에서도 쓸지) |
| `kaggle_link_to.py` | 0건 | `~/GitStudy/utils/` |
| `print_tree.py` | 0건 | `~/GitStudy/utils/` |

### 3단계 — 새 모듈 추출 (DRY)

3개의 명백한 중복을 모듈로:

#### `repo_paths.py` (REPO_ROOT 자동 검색 + DATA 상수)
- 위치: `src/util/repo_paths.py`
- 노트북 11개 + 다수 .py 가 같은 4-5줄 boilerplate 가지고 있던 것 추출
- 자세한 설계: [02_path_portability.md](02_path_portability.md)

#### `data_io.py` (`load_keyword_dfs`)
- 위치: `src/util/data_io.py`
- 5개 노트북에 동일한 패턴 박혀있었음:
  ```python
  keyword_df = pd.read_csv('tiktok_post_final_df.csv')
  clean_beauty_df      = keyword_df[keyword_df['search_term'] == 'clean_beauty'].copy()
  glow_skin_df         = keyword_df[keyword_df['search_term'] == 'glow skin'].copy()
  kbeauty_skin_care_df = keyword_df[keyword_df['search_term'] == 'kbeauty skin care'].copy()
  korean_skincare_df   = keyword_df[keyword_df['search_term'] == 'korean skincare'].copy()
  ```
- → `load_keyword_dfs() -> dict[str, DataFrame]` 한 함수
- 호출부: `kw = load_keyword_dfs(); clean_beauty_df = kw["clean_beauty"]; ...`

**추출 안 한 것** (지나친 wrapping):
- `load_tiktoker_df()` — 단순 `pd.read_csv(TIKTOK / "tiktoker_final_df_0127.csv")` 한 줄. wrapping 가치 < boilerplate
- `load_amazon_brand(brand, kind)` — 비슷한 이유. 인라인 호출로 충분

#### 추출 원칙: "3+ 곳 중복 + 비자명한 변환" 만 함수로
- 단순 한 줄 wrapping (이름만 바꾸기) 은 noise 만 늘림
- 진짜 중복 ( 5+5+5 = 15 줄 → 1 함수) 만 가치 있음

### 4단계 — 다른 추출들 (모듈별)

| 모듈 | 추출된 함수 | 추출 이유 |
|------|------------|-----------|
| `src/fake_data_gen/address/address_utils.py` | `addr_to_df`, `STATE_POPULATION_PCT`, `compute_state_quotas` | crawler 와 ratio 노트북에 동일 코드 박혀있던 것 ([10_fake_data_gen.md](10_fake_data_gen.md)) |
| `src/rag_chatbot/graphrag_viewer/plot.py` | `parquet_to_graph`, `render_graph_image`, `plot_graph` | standalone viewer 와 챗봇이 같은 시각화 로직 따로 가지고 있던 것 ([08_chatbot_v1_v2.md](08_chatbot_v1_v2.md)) |

## canonical 위치

```
src/util/
├── __init__.py
├── repo_paths.py       (REPO_ROOT + DATA 상수, find_repo_root)
├── data_io.py          (load_keyword_dfs, AMAZON_BRANDS)
└── slack.py            (send_msg, find_dotenv 사용)
```

## 학습 노트 보존 위치

```
~/GitStudy/utils/
├── faker.ipynb                 (Faker 라이브러리 테스트 sketch)
├── kaggle_link_to.py           (kagglehub 다운로드 helper)
├── print_tree.py               (디렉터리 트리 출력)
├── db_patterns/                (mysql 학습 흔적, 별개 — 06 참고)
├── legacy_crawlers/            (옛 selenium 시도들 — 11 참고)
├── legacy_notebooks/           (옛 sketch 노트북들 — 11 참고)
└── legacy_rag/                 (rag 진화 흔적 — 09 참고)
```

## 학습 포인트

1. **이름의 무게**: `slack1.py` 의 "1" 같은 의미 없는 suffix 는 미래의 자기 자신을 헷갈리게 함. 처음부터 의미 있는 이름.
2. **dead code 의 두 가지 처분**: (a) git history 만 남기고 폐기, (b) 학습 가치 있으면 외부 보존. 사용자 패턴은 (b) — 다른 프로젝트에서 reference 할 만한 건 보존.
3. **"3+ 곳 중복" 룰**: 한 곳만 있으면 인라인, 두 곳이면 추출 고려, 세 곳 이상이면 추출. 그 미만은 wrapping noise 만 늘어남.
4. **함수 시그니처 = API 결정**: `load_keyword_dfs()` 가 dict 반환 vs tuple unpacking — dict 가 확장성 좋음 (key 추가 가능). 처음부터 잘 짜야 호출부 일괄 변경 안 해도 됨.
5. **"왜 이 함수 추출 했는지" docstring**: 단순 호출부에서 안 보이는 결정 (예: "raw 4 파일은 분실, final_df 에서 split") 은 docstring 으로 남김.

## 관련 commits

- (slack rename) `7b169c3` — refactor: consolidate util/graphRAG, scrub lancedb tracking, prefix env vars
- (repo_paths + data_io 추출) `e88f614` — refactor: flatten data/ layout, extract util modules, portable paths
- (address_utils, plot 추출) `60798a2`, `2d248cd`