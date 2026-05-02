# 시크릿 git history scrub

git 에 commit 됐던 시크릿 (Neo4j 키, TikTok 비밀번호) 을 history 에서도 제거 + force push 한 작업.

## 배경 / 의도

`.gitignore` 가 처음부터 `.env` 를 잡고 있던 덕에 OpenAI 키 류는 commit 된 적 없었음. 하지만 두 가지는 commit 됐었음:

1. **Neo4j Aura 인스턴스 자격증명** (Initial commit 부터)
   - `src/rag_chatbot/neo4j/key/Neo4j-623aa2e4-Created-2025-02-07.txt`
   - URI + username + password 가 평문으로
   - GitHub public repo 에 노출
2. **TikTok 계정 이메일 + 비밀번호** (Initial commit 부터)
   - `src/tiktok_crawler/tiktok_crawling.py` 에 하드코딩
   - 이메일: `chameleo1022@naver.com`
   - 비밀번호: `#project5`

`.gitignore` 추가만으로는 부족 — **history 에 남으면 누구나 옛 commit 에서 찾아냄**. `git log -p` 한 번이면 끝.

## 두 가지 처리 방식 비교

### A. `git filter-repo --path <file> --invert-paths`
- **파일 통째로** 모든 commit 에서 제거
- 사용 케이스: 파일 자체가 노출 (Neo4j key 파일)

### B. `git filter-repo --replace-text <expressions.txt>`
- **특정 텍스트만** 모든 파일에서 치환 (`secret==>REDACTED`)
- 사용 케이스: 파일 안 한 줄만 시크릿 (TikTok 비밀번호)

## Neo4j 처리 (A 방식)

순서:
1. 사용자가 Neo4j Aura console 에서 인스턴스 password reset (또는 destroy)
2. `git filter-repo --path src/rag_chatbot/neo4j/ --invert-paths --force`
3. backup branch 생성 (`backup/pre-neo4j-removal`)
4. `origin` 자동 제거됨 → `git remote add origin ...` 로 복원
5. `git push --force-with-lease origin refactor/repo-cleanup` + `... main`
6. (옵션) Neo4j 인스턴스 자체를 사용자가 console 에서 destroy

부수 검증:
- 다른 사용처 grep — neo4j 폴더는 학습 sketch 노트북 (5개월간 미수정) 외 의존 0개. 통째 폐기 안전.
- Sandbox 자격증명 2개도 같이 (3일 만료 후 자동 폐기됐을 가능성).

## TikTok 처리 (B 방식)

순서:
1. 사용자가 TikTok 비밀번호 변경 (수동)
2. expressions.txt 작성:
   ```
   #project5==>REDACTED_OLD_TIKTOK_PWD
   ```
3. backup branch (`backup/pre-tiktok-pwd-scrub`)
4. `git filter-repo --replace-text /tmp/secrets_expressions.txt --force`
5. origin 복원 + force push 두 브랜치

이메일 (`chameleo1022@naver.com`) 은 PII 지만 password 만큼 critical 아니라서 **scrub 안 함** (사용자 결정).

## 두 케이스 모두 공통

- **filter-repo 는 모든 ref 동시 rewrite** — backup branch 도 같이 rewrite 됨. "원래 history" 보존하려면 **별도 clone 으로 복사** 필요. backup branch 는 단순 안전망 (잠깐의 실수 대비).
- **force push 의 영향**:
  - main + refactor/repo-cleanup 둘 다 force push 필요 (filter-repo 가 모든 ref rewrite)
  - 다른 사람이 이미 clone 했다면 그 clone 의 history 는 옛 시크릿 보유 → 그래서 **GitHub repo 가 단독 use 인지 먼저 확인** (사용자 답: 단독 ✓)
- **GitHub 의 caching**:
  - force push 직후에도 GitHub 은 옛 commit object 를 일시 보관 (며칠 ~ 몇 주). 옛 SHA 알면 직접 access 가능
  - 정말 시급하면 GitHub support 에 cache purge 요청
  - 시간이 지나면 자동 GC

## 검증 명령어

scrub 후:
```bash
git log --all -S '<scrubbed string>' --oneline
# → 0건 출력이면 성공

git log --all --diff-filter=A --name-only -- '<path>'
# → 더 이상 그 path 가 history 에 안 나타남
```

## 학습 포인트

1. **Path 자체가 시크릿이면 `--path --invert-paths`, 텍스트가 시크릿이면 `--replace-text`** — 도구 선택이 명확.
2. **noseup**: filter-repo 는 origin remote 를 자동 제거 (실수로 push 못 하게). 의도한 push 는 remote 복원 후 명시적 force push.
3. **`--force-with-lease` vs `--force`**: 전자는 remote 가 fetch 한 시점과 같을 때만 push (다른 사람의 push 보호). 단독 repo 면 `--force` 도 안전.
4. **history rewrite 후 `--force-with-lease` 가 "stale info" 에러**: 새 origin 추가 직후엔 remote-tracking ref 가 비어있어서 비교 불가. `git fetch origin` 한 번 → 다시 force-with-lease.
5. **시크릿은 revoke 우선, scrub 다음**: filter-repo 로 history 가 깨끗해져도 GitHub 캐시/forks 가 남아있을 수 있음. **revoke (key reset) 를 먼저** 하면 히스토리에 남아도 무력함.
6. **`.gitignore` 의 한계**: 이미 commit 된 파일은 `.gitignore` 가 막을 수 없음 — 추적 해제는 `git rm --cached` + 그 다음 commit 부터 적용.
7. **PII 처리 정도는 사용자 결정**: 이메일은 비밀번호만큼 결정적이진 않음. 본인 판단.

## 관련 commits

직접 commit 없음 (filter-repo + force push 는 history 를 다시 쓰는 작업이지 새 commit 이 아님). 이 작업의 산물은 **새 SHA 의 모든 commit** — Initial commit 부터 모든 commit 의 SHA 가 바뀜.

전후 비교용 backup branches (force push 후 검증되면 삭제 가능):
- `backup/pre-neo4j-removal`
- `backup/pre-lancedb-scrub` (lancedb 데이터 history 청소 시 만든 것)
- `backup/pre-tiktok-pwd-scrub`