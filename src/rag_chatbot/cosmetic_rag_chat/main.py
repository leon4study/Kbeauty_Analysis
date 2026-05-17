"""
File: src/rag_chatbot/cosmetic_rag_chat/main.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
무엇인가 (What)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OpenAI 기반 GraphRAG 화장품 추천 챗봇의 진입점.
``settings.yaml`` 로 GraphRAG 설정을 로드하고, Gradio UI 를 띄워
사용자의 피부 타입·알러지·성분 조건에 맞는 화장품을 추천한다.

왜 있는가 (Why)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- ``gradio_rag_ch7.py`` (Ollama 변형)의 OpenAI 대응 버전.
  로컬 LLM 없이 API 키만으로 더 높은 정확도를 원하는 사용자를 위한 변형.
- GraphRAG local / global search 두 방법을 런타임에 선택 가능
  (``--method local|global`` 또는 Gradio 드롭다운).

어디에 쓰이는가 (Where)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 사용자가 직접 ``python main.py`` 로 실행 → 브라우저에서 Gradio UI.
- ``src/rag_chatbot/cosmetic_rag_chat/README.md`` 에 실행 방법 문서화.

어떤 상황 (When — 런타임 흐름)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. ``main()`` 호출 → ``_check_env()`` 로 GRAPHRAG_API_KEY 존재 확인
2. ``load_settings()`` → settings.yaml 읽기 + 경로를 REPO_ROOT 기준 절대경로 변환
3. ``setup_llm_and_embedder()`` → OpenAI LLM + embedding 초기화
4. ``gradio_interface()`` → Gradio ChatInterface 빌드 + launch

사용법 (How)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    cd src/rag_chatbot/cosmetic_rag_chat
    python main.py                    # 기본 (local search)
    python main.py --method global    # global search 모드

    GRAPHRAG_API_KEY 환경변수 또는 .env 파일 필요.

관련 파일 (Related)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- src/rag_chatbot/ollama/gradio_rag_ch7.py   ← 로컬 Ollama 변형 (비용 0)
- src/rag_chatbot/cosmetic_rag_chat/settings.yaml ← GraphRAG 설정
- data/model/graphrag_t_2/output/lancedb    ← GraphRAG 인덱싱 결과 (LanceDB)
- src/rag_chatbot/cosmetic_rag_chat/README.md ← 실행 방법 문서
"""

from dotenv import load_dotenv
import os
import yaml
import logging
import tiktoken
import argparse
from enum import Enum
import gradio as gr

# 경로 portability: settings.yaml 안의 경로는 REPO_ROOT 기준 상대경로.
# 호출부에서 REPO_ROOT 와 합쳐 절대경로로 변환해 GraphRAG 에 넘김.
from util.repo_paths import REPO_ROOT


def _resolve(path):
    """settings.yaml 의 경로 값을 REPO_ROOT 기준 절대경로로 변환.

    이미 절대경로면 그대로 반환 (env override 한 경우 등).
    """
    if not path:
        return path
    if os.path.isabs(path):
        return path
    return str(REPO_ROOT / path)

INVALID_METHOD_ERROR = "Invalid method"

# GraphRAG 관련 모듈
from graphrag.query.llm.oai.embedding import OpenAIEmbedding
from graphrag.query.llm.oai.typing import OpenaiApiType
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.cli import run_global_search, run_local_search

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

env_path = os.path.join(os.path.dirname(__file__), "indexing", ".env")

# 환경변수 로드
load_dotenv(env_path)


class SearchType(Enum):
    """검색 타입"""
    LOCAL = "local"
    GLOBAL = "global"

    def __str__(self):
        return self.value


def load_yaml_config(config_path):
    """YAML 설정 파일을 로드하는 함수"""
    if os.path.exists(config_path):
        with open(config_path, "r") as file:
            return yaml.safe_load(file)
    return {}


def load_settings():
    base_dir = os.path.dirname(os.path.abspath(__file__))  # 현재 파일(chatbot.py)의 디렉토리
    yaml_path = os.getenv("GRAPHRAG_CONFIG", os.path.join(base_dir, "indexing", "settings.yaml"))
    #print("yaml_path:", yaml_path)

    """ YAML과 .env에서 설정을 로드하는 함수"""
    config = load_yaml_config(yaml_path)
    #print("config:", config)

    if not config:  # 설정이 비어 있으면 경고
        print("⚠️ WARNING: settings.yaml 파일이 비어 있거나, 올바르게 로드되지 않았습니다.")

    # config_path 는 yaml 파일 자체의 위치 (이미 절대경로). data_path/root_path 는
    # yaml 안에 REPO_ROOT 기준 상대경로로 적혀있어 _resolve() 로 절대경로 변환.
    return {
        "config_path": _resolve(os.getenv("CONFIG_PATH", config.get("config_path", yaml_path))),
        "data_path": _resolve(os.getenv("DATA_PATH", config.get("data_path"))),
        "root_path": _resolve(os.getenv("ROOT_PATH", config.get("root_path", "."))),
        "method": os.getenv("METHOD", config.get("method", "local")),
        "community_level": int(os.getenv("COMMUNITY_LEVEL", config.get("community_level", 2))),
        "response_type": os.getenv("RESPONSE_TYPE", config.get("response_type", "Multiple Paragraphs")),
        "llm_model": os.getenv("LLM_MODEL", config.get("llm_model")),
        "embedding_model": os.getenv("EMBEDDINGS_MODEL", config.get("embedding_model")),
        "token_limit": int(os.getenv("TOKEN_LIMIT", config.get("token_limit", 4096))),
        "api_key": os.getenv("GRAPHRAG_API_KEY", config.get("api_key")),
        "api_base": os.getenv("LLM_API_BASE", config.get("api_base")),
        "embeddings_api_base": os.getenv("EMBEDDINGS_API_BASE", config.get("embeddings_api_base")),
        "api_type": os.getenv("API_TYPE", config.get("api_type", "openai")),
    }


def setup_llm_and_embedder(settings):
    """✅ LLM과 임베딩 모델 설정"""
    try:
        logger.info("Setting up LLM and embedder")
        llm = ChatOpenAI(
            api_key=settings["api_key"],
            api_base=f"{settings['api_base']}/v1",
            model=settings["llm_model"],
            api_type=OpenaiApiType[settings["api_type"].capitalize()],
            max_retries=20,
        )

        token_encoder = tiktoken.get_encoding("cl100k_base")

        text_embedder = OpenAIEmbedding(
            api_key=settings["api_key"],
            api_base=f"{settings['embeddings_api_base']}/v1",
            api_type=OpenaiApiType[settings["api_type"].capitalize()],
            model=settings["embedding_model"],
            deployment_name=settings["embedding_model"],
            max_retries=20,
        )

        logger.info("LLM and embedder setup complete")
        return llm, token_encoder, text_embedder
    except Exception as e:
        logger.error(f"Error setting up LLM and embedder: {str(e)}")
        raise Exception(f"Failed to set up LLM and embedder: {str(e)}")


def run_search(method, query, settings):
    """✅ 검색 실행 함수"""
    if method == SearchType.LOCAL:
        search_result = run_local_search(
            settings["config_path"],
            settings["data_path"],
            settings["root_path"],
            settings["community_level"],
            settings["response_type"],
            query,
        )
        return search_result
    elif method == SearchType.GLOBAL:
        search_result = run_global_search(
            settings["config_path"],
            settings["data_path"],
            settings["root_path"],
            settings["community_level"],
            settings["response_type"],
            query,
        )
        return search_result
    else:
        raise ValueError("Invalid method")


def gradio_query(input_text, settings):
    """Gradio용 쿼리 실행 함수"""
    try:
        method = settings["method"]
        result = run_search(SearchType[method.upper()], input_text, settings)
        return result
    except Exception as e:
        return f"Error: {str(e)}"


def gradio_interface(settings):
    """Gradio 인터페이스 수정"""
    with gr.Blocks() as demo:
        # 헤더 및 설명 추가
        gr.Markdown("# 화장품 성분 검색기")
        gr.Markdown("**화장품 성분에 대해 궁금한 내용을 입력하면, 관련 정보를 제공합니다.**")

        # 입력 텍스트박스 및 출력 텍스트박스 추가
        with gr.Row():
            query_input = gr.Textbox(label="질문을 입력하세요", placeholder="예: 화장품 성분에 대해 설명해줄래?", lines=2)
            query_button = gr.Button("검색 실행")

        with gr.Row():
            result_output = gr.Textbox(label="검색 결과", placeholder="결과가 여기에 표시됩니다.", lines=10, interactive=False)

        # 버튼 클릭 시 쿼리 실행
        query_button.click(fn=lambda x: gradio_query(x, settings), inputs=query_input, outputs=result_output)

    return demo


def _check_env() -> None:
    """첫 실행자 친화적 환경 체크 — 필수 항목 미충족 시 명확한 안내로 raise."""
    # 1. OpenAI API key 확인
    api_key = os.getenv("GRAPHRAG_API_KEY")
    placeholder_keys = {"your-graphrag-api-key", "your-llm-api-key", "sk-...", "dummy", ""}
    if not api_key or api_key in placeholder_keys:
        raise EnvironmentError(
            f"\n\n❌ OpenAI API key 가 설정되지 않았습니다 (GRAPHRAG_API_KEY).\n\n"
            f"설정 방법:\n"
            f"   1. https://platform.openai.com/api-keys 에서 key 발급\n"
            f"   2. .env 파일에 추가: GRAPHRAG_API_KEY=sk-...\n"
            f"   3. 또는 환경변수: export GRAPHRAG_API_KEY=sk-...\n\n"
            f"자세한 안내: src/rag_chatbot/cosmetic_rag_chat/README.md\n"
        )

    # 2. settings.yaml 존재 확인
    base_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.getenv("GRAPHRAG_CONFIG", os.path.join(base_dir, "indexing", "settings.yaml"))
    if not os.path.exists(yaml_path):
        raise FileNotFoundError(
            f"\n\n❌ GraphRAG settings.yaml 을 찾을 수 없습니다:\n"
            f"   {yaml_path}\n\n"
            f"기본 설정 파일이 indexing/settings.yaml 에 있어야 합니다.\n"
            f"또는 GRAPHRAG_CONFIG 환경변수로 다른 경로 지정.\n"
        )


def main():
    """메인 실행 함수"""
    _check_env()
    settings = load_settings()

    # method를 설정 파일에 반영
    #settings["method"] = args.method.value
    #logger.info(f"Loaded settings: {settings}")
    # Gradio 인터페이스 실행
    gradio_interface(settings).launch()



parser = argparse.ArgumentParser(description="GraphRAG CLI")
parser.add_argument(
    "--method",
    help="검색 방법 (local/global)",
    type=SearchType,
    choices=list(SearchType),
    default="local",
)
args = parser.parse_args()


if __name__ == "__main__":
    main()