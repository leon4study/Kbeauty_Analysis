# Git 브랜치 정리 — 백업 브랜치 안전하게 삭제하기

옛 백업 브랜치 (e.g. `backup/pre-tiktok-pwd-scrub`) 가 *진짜로 버려도 되는 상태* 인지 확인하는 방법. 로컬 git 명령어 두 가지로 검증 가능.

## 핵심 질문

**"백업본에 적혀있는데 본책엔 없는 내용이 있나?"**

- 본책 = `main` 브랜치 (현재 살아있는 작업)
- 백업본 = `backup/...` 브랜치 (옛 시점 저장)

답이 *"없다"* 면 백업 ⊆ main → 백업 = main 의 옛 일부 → **버려도 OK** (본책에 다 있으니까).

답이 *"있다"* 면 백업 ⊄ main → 백업에 *고유한 작업* 존재 → 버리면 그 부분 사라짐 → **검토 필요**.

## 명령어 1 — 차집합 보기

```
git log main..backup/pre-tiktok-pwd-scrub --oneline
```

핵심: 점 두 개 `..` = **빼기 연산**.

- `main..backup` 의 의미: "backup 에 있는데 main 에는 *없는* commit"
- 수학의 차집합 (B − A) 와 같음

결과 해석:
| 출력 | 의미 | 다음 행동 |
|---|---|---|
| 빈 출력 | 백업의 모든 commit 이 main 에 있음 | 안전 삭제 |
| commit 줄 보임 | 백업에만 있는 작업 존재 | 그 commit 보고 살릴지 결정 |

## 명령어 2 — 꼭대기 commit 검사

```
git branch --contains <백업의 꼭대기 commit hash>
```

예: `git branch --contains d75a049`

의미: "이 commit 이 어느 브랜치들에 들어있나?" 확인.

결과 해석:
| 결과 | 의미 | 다음 행동 |
|---|---|---|
| `main` 도 결과에 있음 | 꼭대기가 main 에도 있음 → 백업 chain 전체가 main 에 흡수됨 | 안전 삭제 |
| `backup/...` 만 있음 | 꼭대기가 main 에 안 들어감 | 살릴지 검토 |

## 왜 두 명령어 다 같은 답?

git 의 commit 은 **체인 구조** — 각 commit 이 *바로 이전 commit* 을 가리키며 줄줄이 이어짐.

```
A ← B ← C ← D ← E   (← 화살표는 "이전" 가리킴)
```

만약 꼭대기 `E` 가 main 에 있으면, 그 *아래 chain 전체* (D, C, B, A) 도 main 안에 있음 (또는 main 의 chain 일부). 그래서 *꼭대기 1 개만 검사* 해도 *전체* 검증됨.

명령어 1 은 chain 의 차집합을 *하나하나 list*, 명령어 2 는 *꼭대기 1 개로 한 방에*. 결국 같은 결론.

## 실제 케이스 (2026-05-07)

backup 브랜치 `backup/pre-tiktok-pwd-scrub` 의 꼭대기 = `d75a049 chore(tiktok): drop obsolete titoker_name → tiktoker_name rename cells`

검증:

```
git log main..backup/pre-tiktok-pwd-scrub --oneline
```

→ 빈 출력이면 main 에 다 흡수됨 → 안전 삭제 가능:

```
git branch -D backup/pre-tiktok-pwd-scrub
```

`-D` (대문자) 쓰는 이유: 백업 브랜치는 보통 *main 에 직접 merge 안 된 채* 별도 chain 으로 따라가므로 `-d` (소문자, safe delete) 는 fail. 의도적 백업이라 *force delete* 필요.

## 일반적 정리 패턴

```
# 1. 백업 브랜치 list 확인
git branch | grep backup

# 2. 각 백업의 꼭대기 commit 확인
git log <백업브랜치이름> --oneline -3

# 3. main 에 다 흡수됐는지 검증
git log main..<백업브랜치이름> --oneline

# 4. 빈 출력이면 force delete
git branch -D <백업브랜치이름>
```

## 함정 — `git push origin --delete` 는 *원격* 만 지움

로컬 백업과 *원격 백업* 은 별개:

```
git branch -D backup/foo                    # 로컬 삭제
git push origin --delete backup/foo         # 원격 삭제
```

`origin/backup/foo` 같은 *원격 추적 ref* 는 위 push 후 자동 갱신. 단 `git fetch --prune origin` 으로 명시적 sync 도 가능.

## 관련

- `git log A..B` 의 점 두 개 = 차집합
- `git log A...B` (점 세 개) = 대칭 차집합 (서로 다른 commit 양쪽 다)
- 둘 헷갈리지 말 것. 백업 검증은 *점 두 개* 가 정답
