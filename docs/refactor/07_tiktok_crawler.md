# TikTok 크롤러 정리

`src/tiktok_crawler/tiktok_crawling.py` — 200여 줄의 모놀리식 top-level 스크립트 (보안 이슈 + typo + stale path 동반) 를 함수화 + env 분리 + history scrub.

## 배경 / 의도

원본 (`tiktok_crawling.py`, 206 lines) 의 문제점 7가지:

1. **🚨 이메일 + 비밀번호 평문 하드코딩** (line 48, 52) — git Initial commit 부터 노출
2. **stale `Data_4` 경로**: `os.chdir("/Users/jun/GitStudy/Data_4/Data/project5/tiktok")`
3. **typo**: 파일명 `titoker_crawling.ipynb` (`tiktoker` 가 아니라 `titoker`)
4. **typo**: 출력 컬럼명 `'titoker_name'` — 이미 raw csv 3개에 박혀있고, 6+ 노트북이 `df.rename(...)` 로 정정 중
5. **함수화 X**: 전체가 top-level script (로그인 → 검색 → 수집 → 저장이 한 흐름으로 늘어짐)
6. **dead imports**: `urlopen`, `Alert` 등
7. **`wait = wait = WebDriverWait(driver, 5)`** 중복 할당 (line 30)

## 처리

### Phase A — 사용자 직접: TikTok 비밀번호 변경
시크릿이 history 에 있으니 코드 수정 전 비밀번호 reset 우선.

### Phase B — 코드 리팩터 (함수화 + env + path)

원본 200줄 top-level → **6 함수**:

| 함수 | 역할 |
|------|------|
| `setup_driver()` | Chrome WebDriver 초기화 (implicit wait 포함) |
| `login_tiktok(driver, email, password)` | 헤더 로그인 → 이메일/비번 입력 → 클릭 → 캡차 대기 sleep |
| `search_videos(driver, keyword)` | 검색 → "동영상" 탭 → 첫 영상 클릭 + 캡차 수동 대기 |
| `collect_video_metadata(driver, n_videos=250)` | 좋아요/댓글/저장수/이름/날짜/설명 수집, 다음 영상 ARROW_DOWN |
| `save_to_csv(data, output_path)` | DataFrame 저장 (utf-8-sig) |
| `main(keyword, n_videos=250)` | 진입점 — env 검증 + 흐름 조립 |

기타 변경:
- 자격증명 → `.env` 의 `TIKTOK_EMAIL`, `TIKTOK_PASSWORD` ([03_env_consolidation.md](03_env_consolidation.md) 참고)
- stale path → `from util.repo_paths import TIKTOK`
- 컬럼명 typo: `'titoker_name'` → `'tiktoker_name'`
- 파일명 typo: `git mv titoker_crawling.ipynb tiktoker_crawling.ipynb`
- dead imports 제거 (`urlopen`, `Alert`)
- `wait = wait = ...` 정리
- 모든 함수에 한국어 docstring (스택, 가정, 캡차 처리 의도)
- env 미설정 시 `RuntimeError` 로 fail-fast

### Phase C — 데이터 컬럼 정정 + 노트북 청소

raw csv 3개의 `titoker_name` 컬럼 정정 (pandas rename 후 저장):
- `data/tiktok/clean_beauty.csv`
- `data/tiktok/tiktok_post_k_beauty_0121.csv`
- `data/tiktok/tiktok_post_k_beauty_0124.csv`

8개 노트북에서 obsolete 가 된 rename 호출 + 관련 markdown 셀 삭제:
```python
clean_beauty_df.rename(columns={'titoker_name': 'tiktoker_name'}, inplace=True)
```
이미 데이터가 정정됐으니 더 이상 no-op 으로 남길 필요 없음 → 한 묶음으로 제거.

### Phase D — git history scrub
`#project5` 비밀번호 텍스트를 모든 commit 에서 `REDACTED_OLD_TIKTOK_PWD` 로 치환:
- `git filter-repo --replace-text /tmp/secrets_expressions.txt --force`
- 자세한 절차: [04_secrets_scrub.md](04_secrets_scrub.md)

## canonical 위치

```
src/tiktok_crawler/
├── tiktok_crawling.py           (6 함수 + 한국어 docstring + env-driven)
└── tiktoker_crawling.ipynb      (rename: titoker → tiktoker)

.env                             (TIKTOK_EMAIL, TIKTOK_PASSWORD)
.env.example                     (TIKTOK_* 섹션 + placeholder)

data/tiktok/                     (raw csv 3개 컬럼명 정정됨)
```

## 학습 포인트

1. **하드코딩된 시크릿 발견 시 순서**: revoke (계정 비번 변경) → 코드 수정 → history scrub. 코드 먼저 고치고 revoke 깜빡하면 의미 없음.
2. **typo 정정의 파급 범위**: 컬럼명 하나 바꾸려면 (a) 데이터 파일, (b) 그걸 만들어내는 코드, (c) 그걸 사용하는 모든 노트북 — 셋 다 같이 정리해야 클린.
3. **데이터 정정 vs 노트북 rename 호출**: 두 옵션 — (a) 데이터는 그대로, 노트북에서 rename 으로 흡수 (idempotent), (b) 데이터 자체를 정정 + 노트북에서 rename 호출 제거. 후자가 더 깔끔.
4. **함수화 의도 분류**: setup / login / search / collect / save / main 처럼 **단계별로 자르는 게 자연** — 미래의 자기 자신이 한 단계만 디버깅할 때 쉬움.
5. **캡차/사람 인증 자동화는 별개 문제**: 코드 안에 `time.sleep(15)` 같은 게 있는 건 "사람이 옆에서 풀어줘야 함" 신호. 이런 건 docstring 에 명시.
6. **`if __name__ == "__main__":` guard**: 모듈을 import 만 해도 Gradio 가 launch 되거나 크롤러가 바로 실행되면 testing 어려움. main() 분리 + guard.

## 관련 commits

- `0af6cd3` — refactor(tiktok_crawler): extract functions, env-ize creds, fix typo + stale path
- `d75a049` — chore(tiktok): drop obsolete titoker_name → tiktoker_name rename cells