import logging
import os

import gradio as gr
import yaml
from dotenv import load_dotenv
from graphrag.query.cli import run_global_search, run_local_search

# 그래프 시각화는 같은 패키지의 graphrag_viewer/plot.py 에 위임 — DRY 위해 추출.
from rag_chatbot.graphrag_viewer.plot import parquet_to_graph, render_graph_image

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 환경 변수 로드
env_path = os.path.join(os.path.dirname(__file__), "indexing", ".env")
load_dotenv(env_path)

# 🔹 전역 변수: 설정 및 데이터 저장
settings = None
graph_data = None
saved_answers = []  # 🔥 검색 결과 저장용 리스트

def load_yaml_config(config_path):
    """YAML 설정 파일을 로드하는 함수"""
    if os.path.exists(config_path):
        with open(config_path, "r") as file:
            return yaml.safe_load(file)
    return {}

def load_settings():
    """설정 로드 함수"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.getenv("GRAPHRAG_CONFIG", os.path.join(base_dir, "indexing", "settings.yaml"))
    config = load_yaml_config(yaml_path)
    
    return {
        "config_path": yaml_path,
        "data_path": os.getenv("DATA_PATH", config.get("data_path")),
        "root_path": os.getenv("ROOT_PATH", config.get("root_path", ".")),
        "method": os.getenv("METHOD", config.get("method", "local")),
        "community_level": int(os.getenv("COMMUNITY_LEVEL", config.get("community_level", 2))),
        "response_type": os.getenv("RESPONSE_TYPE", config.get("response_type", "Multiple Paragraphs")),
    }

def run_search(method, query, settings):
    """✅ 검색 실행 함수"""
    if method == "local":
        return run_local_search(settings["config_path"], settings["data_path"], settings["root_path"], settings["community_level"], settings["response_type"], query)
    elif method == "global":
        return run_global_search(settings["config_path"], settings["data_path"], settings["root_path"], settings["community_level"], settings["response_type"], query)
    else:
        raise ValueError("Invalid method")

def apply_parquet_files(parquet_files):
    """업로드된 parquet 파일들을 그래프로 시각화 + 검색용 데이터로 저장.

    UI에서 "적용하기" 누르면 호출되는 핸들러. 각 parquet에서 (1) 네트워크
    그래프 이미지를 만들어 갤러리에 띄우고 (2) 원본 DataFrame을 ``graph_data``
    글로벌에 누적 — 이후 ``perform_search`` 가 이 데이터를 검색에 활용.

    실제 그래프 생성/렌더링은 ``rag_chatbot.graphrag_viewer.plot`` 에 위임.
    """
    global settings, graph_data
    settings = load_settings()

    if not parquet_files:
        return ["⚠️ Parquet 파일을 먼저 업로드하세요."], "⚠️ Parquet 파일을 먼저 업로드해야 합니다."

    all_graphs: list = []
    graph_data = []  # 검색에서 참조할 DataFrame 누적

    for parquet_file in parquet_files:
        try:
            G, df = parquet_to_graph(parquet_file.name)
        except ValueError as e:
            all_graphs.append(f"⚠️ {parquet_file.name}: {e}")
            continue
        graph_data.append(df)
        all_graphs.append(render_graph_image(G))

    return all_graphs, "✅ 데이터 적용 완료! 이제 질문을 입력하세요."

def perform_search(query):
    """✅ 질문을 바탕으로 검색 수행"""
    global settings, graph_data, saved_answers

    if settings is None or graph_data is None:
        return "⚠️ 먼저 Parquet 파일을 업로드하고 적용하세요."

    # 🔍 RAG 검색 실행
    search_result = run_search(settings["method"], query, settings)

    # 검색 결과 저장
    formatted_result = f"### 🔍 질문: {query}\n\n{search_result}\n---"
    saved_answers.append(formatted_result)  # 저장

    return formatted_result

def get_saved_answers():
    """✅ 저장된 검색 결과 조회"""
    global saved_answers

    if not saved_answers:
        return "📭 저장된 답변이 없습니다."

    return "\n\n".join(saved_answers)

def gradio_interface():
    """✅ Gradio UI"""
    with gr.Blocks() as demo:
        gr.Markdown("# 📌 화장품 성분 검색 및 네트워크 분석")

        with gr.Row():
            parquet_input = gr.Files(label="📂 Parquet 파일 업로드", file_types=[".parquet"])
        apply_button = gr.Button("✅ 적용하기")

        with gr.Row():
            graph_output = gr.Gallery(label="📊 네트워크 그래프", columns=2)

        with gr.Row():
            status_output = gr.Textbox(label="✅ 상태 메시지", interactive=False)

        with gr.Row():
            with gr.Column(scale=1):  # 왼쪽: 질문 입력란과 버튼
                query_input = gr.Textbox(label="🔍 질문을 입력하세요", placeholder="예: 이 성분은 안전한가요?", lines=2)
                search_button = gr.Button("🔎 검색 실행")
                
            with gr.Column(scale=2):  # 오른쪽: 검색 결과
                result_output = gr.Textbox(label="📋 검색 결과")

        with gr.Row():
            save_answer_button = gr.Button("💾 답변 저장하기")  # "답변 저장하기"로 변경
        saved_answers_output = gr.Textbox(label="📂 저장된 검색 결과")

        # 버튼 동작 설정
        apply_button.click(fn=apply_parquet_files, inputs=[parquet_input], outputs=[graph_output, status_output])
        search_button.click(fn=perform_search, inputs=[query_input], outputs=[result_output])
        save_answer_button.click(fn=save_answer, inputs=[result_output], outputs=[saved_answers_output])

    return demo


def save_answer(answer):
    """✅ 답변을 파일로 저장"""
    # 답변을 파일로 저장
    file_path = os.path.join(settings["data_path"], "saved_answer.txt")
    with open(file_path, "a") as file:
        file.write(answer + "\n---\n")

    return f"답변이 '{file_path}'에 저장되었습니다."


def main():
    """✅ 실행"""
    gradio_interface().launch()

if __name__ == "__main__":
    main()
