"""GraphRAG 인덱싱 결과 (parquet) 를 업로드해서 네트워크 그래프로 시각화하는
standalone Gradio 앱.

실제 그래프 생성/렌더 로직은 ``plot.py`` 의 ``plot_graph`` 함수에 위임 — 같은
함수를 ``cosmetic_rag_chat/final_graphrag_LLM.py`` 의 챗봇에서도 재사용한다.

CLI 실행:
    python -m rag_chatbot.graphrag_viewer.graphRAG_gradio
"""
import gradio as gr

from rag_chatbot.graphrag_viewer.plot import plot_graph


# Gradio UI — 단순 파일 업로드 → 갤러리 시각화.
# fn(plot_graph)는 input list를 받아 PIL.Image 리스트를 반환하므로 Gallery에 바로 연결.
iface = gr.Interface(
    fn=plot_graph,
    inputs=gr.Files(label="Parquet 파일 업로드"),
    outputs=gr.Gallery(label="네트워크 그래프"),
)


if __name__ == "__main__":
    iface.launch()