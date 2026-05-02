# Refactor history

이 디렉터리는 Kbeauty Analysis repo 의 **정리/리팩터링 결정**을 토픽별로 기록한 문서다.

코드를 읽는 것만으로는 "왜 이런 형태가 됐는지" 보이지 않는다. 특히 폐기된 변종들 — 어떤 시도였고, 무엇을 배웠고, 왜 채택 안 했는지 — 는 git log 만으로는 부족하다. 이 문서들은 그 맥락을 남긴다 (포트폴리오 측면에서도 "결정의 흐름" 이 코드보다 더 가치 있다).

각 .md 는 다음 표준 섹션을 가진다:

1. **배경 / 의도** — 무엇을 하려고 했나
2. **시도된 변종** — 표 형태로 비교
3. **최종 채택 + 이유** — 왜 이걸로 결정
4. **canonical 위치 + 학습 노트 보존 위치**
5. **학습 포인트** — 이 시도/결정에서 배운 것
6. **관련 commits**

## 정리 토픽 인덱스

| 파일 | 토픽 | commits |
|------|------|---------|
| [01_data_layout.md](01_data_layout.md) | `data/project5/*` 8.2GB → `data/{amazon, tiktok, model, archive,...}` 평면화 | `e88f614` |
| [02_path_portability.md](02_path_portability.md) | 하드코딩 경로 → `REPO_ROOT` 패턴, `pyproject.toml` 도입 | `e88f614` |
| [03_env_consolidation.md](03_env_consolidation.md) | 28개 흩어진 `.env` → 루트 1개 + prefix 컨벤션 | `7b169c3` |
| [04_secrets_scrub.md](04_secrets_scrub.md) | Neo4j 키 + TikTok 비밀번호 git history rewrite | (filter-repo, force-push) |
| [05_util_extraction.md](05_util_extraction.md) | `slack`, `repo_paths`, `data_io`, `address_utils`, `plot` 모듈 추출 | 여러 commit |
| [06_mysql_client.md](06_mysql_client.md) | `mysql1` ↔ `mysql2_developed` 변종 → 새 `mysql.py` (bulk + retry) | `43e21f5` |
| [07_tiktok_crawler.md](07_tiktok_crawler.md) | 모놀리식 script → 6 함수, env 분리, typo 정정 | `0af6cd3`, `d75a049` |
| [08_chatbot_v1_v2.md](08_chatbot_v1_v2.md) | `0209/` v1 → `cosmetic_rag_chat/` v2 진화 + plot 모듈 추출 | `2d248cd` |
| [09_ollama_rag_variants.md](09_ollama_rag_variants.md) | gradio_rag_ch1~ch8 + LangChain 변종 정리 | `3a99a56` |
| [10_fake_data_gen.md](10_fake_data_gen.md) | 중복 코드 → `address_utils`, project_code 흡수 | `60798a2` |
| [11_project_code_dissolution.md](11_project_code_dissolution.md) | `src/project_code/` 해체, lemmatized 노트북 승격 | `60798a2` |

## 정리 원칙 (이 repo에 적용된 것)

1. **사용처 0개 + 후계 있음 → 학습 자료로 ~/GitStudy/utils/ 로 이동** (이 repo는 깔끔하게)
2. **사용처 0개 + 후계 없음 + git 보존 충분 → 폐기**
3. **변종 폐기 시에도 의도/차이는 이 docs/refactor/ 에 표로 남김**
4. **함수화는 진짜 중복 (3+ 곳)일 때만** — 한 줄짜리 wrapping은 하지 않음
5. **코드 변경 동반된 모든 함수에 docstring 필수** (한국어, "왜" 우선)
6. **포터블 경로**: 절대 경로 → `REPO_ROOT` (`pyproject.toml` + `pip install -e .` 기반)