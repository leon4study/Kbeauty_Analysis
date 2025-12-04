import gradio as gr
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image



# 그래프 그리기 함수
def plot_graph(parquet_files):
    all_graphs = []
    
    for parquet_file in parquet_files:
        # Parquet 데이터 로드
        df = pd.read_parquet(parquet_file)

        # 네트워크 그래프 생성
        G = nx.DiGraph()

        # 관계 데이터가 있는 경우 (source, target 기반)
        if "source" in df.columns and "target" in df.columns:
            for _, row in df.iterrows():
                G.add_edge(row["source"], row["target"])

        # 관계 데이터가 없지만 ID 기반 노드 추가 가능
        elif "id" in df.columns:
            G.add_nodes_from(df["id"])
            # 연결 가능한 컬럼이 있는 경우, 연결 시도
            link_columns = ["text_unit_ids", "entity_ids", "relationship_ids"]
            for col in link_columns:
                if col in df.columns:
                    for _, row in df.iterrows():
                        if isinstance(row[col], list):  # 리스트 형태인지 확인
                            for link in row[col]:
                                G.add_edge(row["id"], link)

        else:
            all_graphs.append(f"⚠️ {parquet_file.name}에 'source' 또는 'id' 컬럼이 없습니다.")
            continue  # 다음 파일로 이동

        # 그래프 레이아웃 설정
        pos = nx.spring_layout(G, seed=42)

        # 그래프 그리기
        fig, ax = plt.subplots(figsize=(10, 6))
        nx.draw(G, pos, with_labels=True, node_color="skyblue", edge_color="gray", node_size=500, font_size=8, ax=ax)
        
        # 그래프를 이미지로 변환
        buf = BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        img = Image.open(buf)  # BytesIO 객체를 PIL.Image로 변환
        all_graphs.append(img)  # 이미지 리스트에 추가
    
    return all_graphs

# Gradio UI
iface = gr.Interface(
    fn=plot_graph, 
    inputs=gr.Files(label="Parquet 파일 업로드"),  # 여러 파일 업로드
    outputs=gr.Gallery(label="네트워크 그래프")  # 여러 이미지를 한 번에 출력
)

# 앱 실행
iface.launch()