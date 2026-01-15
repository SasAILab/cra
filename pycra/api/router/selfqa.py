from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from pycra.api.models.common import ContractGraphRequest
from pycra.utils.logger import selfqa_logger as logger
from pycra.core.knowledge_graph import KgBuilder
from pycra.api.core.dependencies import get_kgBuilder_async, get_factory
from pycra.api.models.knowledge_graph import BuildReturnModel
from pycra.api.models.selfqa import SelfQaRequest, SelfQaSubgrapnResponse
from pycra.core.agents.selfqa.sub_graph import SubGraphBuilder
selfqa_router = APIRouter(prefix="/selfqa", tags=["SELF-QA"])  # current contract knowledge graph


@selfqa_router.post("/build", response_model=BuildReturnModel, tags=["SELF-QA"],
                  summary="Build a contract graph for current contract")
async def build_selfqa(request: ContractGraphRequest,
                               kg_builder: KgBuilder = Depends(get_kgBuilder_async), ) -> BuildReturnModel:
    try:
        logger.info(f"build contract graph: id={request.contract_id}")
        # Extract entities and relationships
        nodes, edges, namespaces = await kg_builder.build_graph(
            md_content=request.contract_text,
            contract_id=request.contract_id
        )
        # Prepare response
        response = BuildReturnModel(
            status="success",
            nodes=nodes,
            edges=edges,
            graph_namespace=namespaces
        )

        logger.info(f"{request.contract_id} successfully built contract graph")
        return response

    except Exception as e:
        logger.error(f"Failed to build contract graph: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build contract graph: {str(e)}"
        )


@selfqa_router.post("/subgraph", response_model=SelfQaSubgrapnResponse, tags=["SELF-QA"])
async def test_selfqa_subgraph(request: SelfQaRequest) -> SelfQaSubgrapnResponse:
    try:
        builder = SubGraphBuilder()
        subgraph_count = 0
        total_nodes = 0
        total_edges = 0
        subgraph_summaries = []
        async for df in builder(request.namespace):
            subgraph_count += 1
            nodes = df["nodes"].iloc[0]
            edges = df["edges"].iloc[0]

            node_count = len(nodes)
            edge_count = len(edges)
            total_nodes += node_count
            total_edges += edge_count
            subgraph_summaries.append({
                "subgraph_id": subgraph_count,
                "node_count": node_count,
                "edge_count": edge_count,
                "nodes_sample": [node[0] for node in nodes] if nodes else [],
                "edges_sample": [f"{edge[0]}-{edge[1]}" for edge in edges] if edges else []
            })

            logger.info(f"获得第 {subgraph_count} 个子图数据，节点数: {node_count}, 边数: {edge_count}")

        return SelfQaSubgrapnResponse(
            success=True,
            message=f"成功生成 {subgraph_count} 个子图",
            total_subgraphs=subgraph_count,
            total_nodes=total_nodes,
            total_edges=total_edges,
            avg_nodes_per_subgraph=total_nodes / subgraph_count if subgraph_count > 0 else 0,
            avg_edges_per_subgraph=total_edges / subgraph_count if subgraph_count > 0 else 0,
            subgraph_summaries=subgraph_summaries
        )
    except Exception as e:
        logger.error(f"Failed to build contract graph: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build contract graph: {str(e)}"
        )