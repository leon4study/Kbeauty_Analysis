# silver/tiktok/ 가 historical artifact 인 이유 — 외부 경로 의존 + raw 4 csv 분실

K-Beauty TikTok 분석의 *silver 단계 final csv 두 개* (`tiktok_videos_silver.csv` + `tiktokers_silver.csv`) 가 *재현 불가능한 historical artifact* 인 이유 영구 기록.

## 배경

분석 노트북 17 개가 같은 csv 두 파일에 `to_csv` 하고 있어 *생성자 책임 불분명* 상태. 정리 위해 *canonical generator* (한 노트북이 raw 부터 처리해 silver 만드는 책임) 식별 시도.

후보 노트북: `tiktok_EDA.ipynb` 가 *유일하게 raw csv 부터 처리* 해서 canonical 로 지목됨.

## 발견된 문제 — raw 4 csv 외부 경로 의존

`tiktok_EDA.ipynb` 의 cell 2 가 raw 4 csv 를 읽는 경로:

```python
clean_beauty_df = pd.read_csv('C:/Users/user/Desktop/databootcamp/tiktok_test/tiktok_post_clean_beauty_0124.csv')
glow_skin_df = pd.read_csv('C:/Users/user/Desktop/databootcamp/tiktok_test/tiktok_post_glow_skin_0123.csv')
kbeauty_skin_care_df = pd.read_csv('C:/Users/user/Desktop/databootcamp/tiktok_test/tiktok_post_kbeauty_skin_care_0124.csv')
korean_skincare_df = pd.read_csv('C:/Users/user/Desktop/databootcamp/tiktok_test/tiktok_post_korean_skincare_0124.csv')
```

→ **이 노트북 작성자의 로컬 Windows 컴퓨터 경로**. repo 안이 아님.

## raw 4 csv 검증 결과 — 100% reproduce 불가

repo 전체 + `~/GitStudy/Data_4` 까지 검색 (140 csv 중 컬럼 형태 + hashtag 매칭 모두 시도):

| raw 4 (작성 당시 이름) | 현재 후보 | 매칭도 |
|---|---|---|
| `tiktok_post_clean_beauty_0124.csv` | `data/tiktok/tiktok_post_k_beauty_0124.csv` (`#cleanbeauty` hashtag, 250 rows) | 중간 |
| `tiktok_post_glow_skin_0123.csv` | **없음** | 0 |
| `tiktok_post_kbeauty_skin_care_0124.csv` | `data/tiktok/tiktok_post_k_beauty_0121.csv` (100 rows, 전처리됨) | 낮음 |
| `tiktok_post_korean_skincare_0124.csv` | **없음** | 0 |

→ **4 중 0~2 partial 매칭**, glow_skin / korean_skincare 는 *진짜 사라짐*.

## canonical generator 부재의 의미

`tiktok_EDA` 가 *유일한 raw → final 변환 노트북* 이었지만 *입력 missing* 으로 cell 2~36 *영원히 dead*. 즉 **재현 가능한 canonical generator 가 어디에도 없음**.

→ 17 to_csv 호출의 정체:
- 1 개 (`tiktok_EDA` cell 36) : 진짜 변환 = **dead** (입력 없음)
- 나머지 16 개: 이미 만들어진 final csv 를 *읽고 → 같은 컬럼 select → 다시 쓰기* (**circular read-write loop**)

= *실제 생성 코드가 어디에도 없는 상태에서 17 노트북이 같은 파일을 덮어쓰기만 반복*

## 결정 — silver = historical artifact

**옵션 A2-α 선택**:
1. raw → final 변환부 (`tiktok_EDA` cell 0~36) **완전 삭제**. 코드 너무 평범 (concat + dedup + hash_tag 추출 6 줄 함수) 해서 보존 가치 없음. 미래에 새 raw 들어와도 새로 짜는 게 더 빠름
2. silver 의 final csv 두 개는 **재현 불가능한 historical artifact** 로 명시. 변환 결과만 보존
3. 17 to_csv 호출 모두 제거. silver 가 *single source of truth*. 모든 분석 노트북은 *read-only* 로 silver 만 읽기
4. 후반부 EDA 코드 (`tiktok_EDA` cell 37~) 는 *입력 경로만 silver 로* 바꿔서 살림

## 영향

| 변경 | 효과 |
|---|---|
| `tiktok_EDA.ipynb`: 98 cell → 49 cell | dead 코드 (cell 0~36) 삭제, EDA 본 가치만 남음 |
| `tiktoker_EDA.ipynb`: portable path | DATA_PATH (외부 경로) → BRONZE_TIKTOK / SILVER_TIKTOK |
| `tiktoker_recommend.ipynb`: portable path | TIKTOK 변수 → SILVER_TIKTOK + BRONZE_TIKTOK 분리 |
| 9 secondary 노트북: 17 to_csv 제거 | read-write loop 종료. silver = single source |
| `src/util/data_io.py`: `load_keyword_dfs()` | TIKTOK / `tiktok_post_final_df.csv` → SILVER_TIKTOK / `tiktok_videos_silver.csv` |
| 옛 final csv 2 개 삭제 | `data/tiktok/tiktok_post_final_df.csv`, `tiktoker_final_df_0127.csv` (silver 에 동일 내용 보존) |
| orphan 6 → archive/orphan_outputs/ | 어떤 노트북도 read 안 하는 산물들 분리 |

## 미래에 신규 raw 들어오면

새 `src/pipelines/build_silver_tiktok.py` 모듈로 작성:
- 새 raw csv 들 (검색어별) 읽기
- concat + dedup
- hash_tag 추출 (`info` 컬럼 → `hash_tag` 컬럼)
- 9 컬럼 select: `[search_term, vedio_order, tiktoker_name, upload_date, like_cnt, comment_cnt, save_cnt, info, hash_tag]`
- silver 에 저장

→ 노트북 안에 변환 코드 두지 말고 *Python 모듈로* (재실행 명확 + 테스트 가능). 이건 *현재 task 외*, 미래 신규 raw 들어왔을 때 별도 작업.

## 학습 포인트

1. **canonical generator 라고 지목된 노트북도 *외부 환경 의존* 일 수 있음** — 실제 reproduce 가능한지 *입력 경로* 까지 추적 필수
2. **17 to_csv 호출이 모두 동일 transform 이라도 *진짜 생성 코드 없으면* read-write loop**. 리팩터 시점에 *진짜 generator 부재* 자체가 발견될 수 있음
3. **dead code 보존 vs 삭제** — 코드가 *너무 평범* 하면 보존 가치 없음. 미래에 새로 짜는 게 더 깨끗. `concat + dedup` 같은 기본 패턴은 *historical 가치 0*
4. **silver 단계도 *재현 가능 vs historical artifact* 구분 필요** — medallion 아키텍처가 항상 재현 가능 의미하지 않음. 어떤 단계는 *과거 결과의 영구 보존* 일 수 있음

## 관련

- [`14_kpremium_number_history.md`](14_kpremium_number_history.md) — within-FE selection effect 95% 발견의 데이터 흐름
- [`src/util/data_io.py`](../../src/util/data_io.py) — `load_keyword_dfs()` 가 silver 가리킴
- [`src/util/repo_paths.py`](../../src/util/repo_paths.py) — `BRONZE_TIKTOK`, `SILVER_TIKTOK` 상수 정의
