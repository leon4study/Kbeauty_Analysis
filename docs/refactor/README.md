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
| [12_tiktok_recommendation_evolution.md](12_tiktok_recommendation_evolution.md) | tiktoker 추천 알고리즘 ver.1/v2/v3 + 회귀분석 진화 + 정량화 (Top-10 = 2.32× random) | (이번 정리) |
| [13_amazon_tiktok_brand_matching.md](13_amazon_tiktok_brand_matching.md) | Amazon × TikTok 5 브랜드 매칭 — 가설 반박: TikTok 활발도 ↔ Amazon 인기도 = 음의 상관 (신생 vs established 양극화) | (이번 정리) |
| [14_kpremium_number_history.md](14_kpremium_number_history.md) | K-Premium 수치 변천 (8.43 → 4.76 ~ 5.10) 영구 기록 + within-FE 95% selection effect 발견 | (이번 정리) |
| [15_ollama_graphrag_compatibility.md](15_ollama_graphrag_compatibility.md) | Ollama × GraphRAG 호환성 — entity extraction / 임베딩 차원 / JSON mode 3 issue + 운영 옵션 A/B/C | `1e236b1` |
| [16_silver_artifact_origin.md](16_silver_artifact_origin.md) | silver 단계 설계 결정 + historical artifact 보존 이유 (raw 재현 불가) | `6bc440f` |
| [17_2026_05_session_cleanup.md](17_2026_05_session_cleanup.md) | 2026-05 medallion 마무리 + data legacy + bronze 네이밍 + team_folder + 온보딩 (PR #5~#14 종합) | (이번 정리) |
| [18_vectorization_and_constants.md](18_vectorization_and_constants.md) | H1+H2 — 노트북 for-loop 벡터화 (util 추출) + main.py 상수 정리. `np.select` / `explode` / dict-lookup 패턴 학습 노트 | `3fa1972` |
| [EXPERIMENTS_PLAYBOOK.md](EXPERIMENTS_PLAYBOOK.md) | **변종 정리 표준 — 폴더 우선, 통폐합 패턴, 결정 트리** | (이번 정리) |

## 정리 원칙 (이 repo에 적용된 것)

> **변종 정리 표준은 [EXPERIMENTS_PLAYBOOK.md](EXPERIMENTS_PLAYBOOK.md) 참고** — 폴더 우선, 통폐합 패턴 A/B/C, 결정 트리, 실용 명령어.

1. **도메인 무관한 학습 sketch → `~/GitStudy/utils/legacy_*`** (외부 보존). 도메인 흔적은 프로젝트 안에 둠
2. **변종은 통폐합 우선** (단일 파일 + 주석 진화 / 파라미터화 / README 카탈로그). 단순 보존보다 영양가↑
3. **변종 폐기 시에도 의도/차이는 이 docs/refactor/ 또는 도메인 README 에 표로 남김**
4. **폴더가 1순위 진입점** — 도메인 폴더 열자마자 README 로 의도 파악 가능해야 함. git history/branch 는 보조
5. **함수화는 진짜 중복 (3+ 곳)일 때만** — 한 줄짜리 wrapping은 하지 않음
6. **코드 변경 동반된 모든 함수에 docstring 필수** (한국어, "왜" 우선)
7. **포터블 경로**: 절대 경로 → `REPO_ROOT` (`pyproject.toml` + `pip install -e .` 기반)