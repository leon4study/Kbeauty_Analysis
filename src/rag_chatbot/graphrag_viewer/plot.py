"""GraphRAG 인덱싱 결과(parquet) 를 networkx 그래프로 시각화.

`graphrag_viewer/graphRAG_gradio.py` (standalone 시각화 앱) 와
`cosmetic_rag_chat/final_graphrag_LLM.py` (챗봇 통합) 양쪽이 거의 같은 시각화
로직을 따로 갖고 있던 걸 한 모듈로 모은다. 새 시각화 도구가 필요하면 여기서
``plot_graph()`` 를 import 해서 쓰면 됨.

Public API:
    - parquet_to_graph: 단일 parquet → (DiGraph, DataFrame)
    - render_graph_image: DiGraph → PIL Image
    - plot_graph: 여러 parquet → 이미지 리스트 (Gradio gallery 직접 출력 가능)
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Iterable, Union

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from PIL import Image


# Parquet 안에 노드 사이 추가 link 정보를 담을 수 있는 컬럼 이름들.
# id 기반 노드 그래프인 경우 이 컬럼들 (값이 list)을 추가 edge로 흡수.
_LINK_COLUMNS = ("text_unit_ids", "entity_ids", "relationship_ids")


def parquet_to_graph(parquet_file: Union[str, Path]) -> tuple[nx.DiGraph, pd.DataFrame]:
    """단일 parquet 파일을 읽어 networkx ``DiGraph`` + 원본 DataFrame 반환.

    GraphRAG 출력은 두 패턴이 가능:

    1. ``source/target`` 컬럼 있음 → 관계(edge) 데이터. 각 row를 edge로.
    2. ``id`` 컬럼 있음 → 엔티티(node) 데이터. id를 node로 등록하고,
       link 컬럼 (``text_unit_ids`` 등) 값이 list면 그 안의 id로 edge 추가.

    Args:
        parquet_file: parquet 파일 경로 (또는 file-like object).

    Returns:
        ``(graph, df)``. df는 추가 분석/저장용으로 callers가 필요시 사용.

    Raises:
        ValueError: 위 두 패턴 어느 것도 못 맞을 때 (스키마 미지원).
    """
    df = pd.read_parquet(parquet_file)
    G: nx.DiGraph = nx.DiGraph()

    if "source" in df.columns and "target" in df.columns:
        for _, row in df.iterrows():
            G.add_edge(row["source"], row["target"])
    elif "id" in df.columns:
        G.add_nodes_from(df["id"])
        # 노드 사이 link 정보 컬럼이 있으면 흡수
        for col in _LINK_COLUMNS:
            if col not in df.columns:
                continue
            for _, row in df.iterrows():
                value = row[col]
                if isinstance(value, list):
                    for link in value:
                        G.add_edge(row["id"], link)
    else:
        raise ValueError(
            "parquet 스키마 미지원 — 'source/target' 또는 'id' 컬럼이 필요합니다."
        )

    return G, df


def render_graph_image(G: nx.DiGraph) -> Image.Image:
    """networkx ``DiGraph`` 를 spring layout으로 그려 PIL Image 반환.

    Gradio gallery / notebook 등에 바로 표시 가능. Figure는 즉시 close해
    matplotlib 메모리 누수 방지.
    """
    pos = nx.spring_layout(G, seed=42)
    fig, ax = plt.subplots(figsize=(10, 6))
    nx.draw(
        G, pos,
        with_labels=True, node_color="skyblue", edge_color="gray",
        node_size=500, font_size=8, ax=ax,
    )
    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf)


def plot_graph(parquet_files: Iterable) -> list:
    """여러 parquet 파일을 한꺼번에 시각화.

    Gradio Files 컴포넌트 (``.name`` 속성 가진 객체) 와 일반 경로 문자열 둘 다 받음.
    파일 한 개라도 스키마가 틀리면 그 파일만 ⚠️ 문자열로 결과 리스트에 들어감
    (Gradio Gallery는 image / 문자열 mixed 출력을 지원).

    Args:
        parquet_files: parquet 경로 또는 Gradio file 객체의 iterable.

    Returns:
        각 입력에 대응하는 PIL Image 또는 ⚠️ 에러 메시지의 리스트.
    """
    out: list = []
    for f in parquet_files:
        path = f.name if hasattr(f, "name") else f
        try:
            G, _ = parquet_to_graph(path)
            out.append(render_graph_image(G))
        except ValueError as e:
            out.append(f"⚠️ {path}: {e}")
    return out