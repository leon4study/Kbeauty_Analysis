from dotenv import load_dotenv
import os
import yaml
import logging
import tiktoken
import argparse  # argparse 모듈 추가
from enum import Enum
import gradio as gr

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

    return {
        "config_path": yaml_path,
        "data_path": os.getenv("DATA_PATH", config.get("data_path")),
        "root_path": os.getenv("ROOT_PATH", config.get("root_path", ".")),
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


def main():
    """메인 실행 함수"""
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