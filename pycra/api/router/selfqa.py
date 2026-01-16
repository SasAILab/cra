import json
import os
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from pycra import settings
from pycra.utils.common import normalize_result, serialize_item
from pycra.utils.logger import selfqa_logger as logger
from pycra.api.core.dependencies import get_generatorSerivce_async
from pycra.api.models.selfqa import selfQaResponse
from pycra.api.models.selfqa import SelfQaRequest, SelfQaSubgrapnResponse
from pycra.core.agents.selfqa.sub_graph import SubGraphBuilder
from pycra.core.agents import GenerateService
selfqa_router = APIRouter(prefix="/selfqa", tags=["SELF-QA"])  # current contract knowledge graph


@selfqa_router.post("/build", response_model=selfQaResponse, tags=["SELF-QA"],
                  summary="Build a contract graph for current contract")
async def build_selfqa(request: SelfQaRequest,
                               generatorService: GenerateService = Depends(get_generatorSerivce_async), ) -> selfQaResponse:
    try:
        results = []
        # Extract entities and relationships
        async for result in generatorService.build(namespace=request.namespace):
            for item in normalize_result(result):
                serialized = serialize_item(item)
                if isinstance(serialized, list):
                    results.extend(serialized)
                else:
                    results.append(serialized)
        logger.info(f"results : {results}")
        save_dir = f"{settings.kg.working_dir}/selfqa_data/{request.namespace}"
        os.makedirs(save_dir, exist_ok=True)
        save_path = f"{save_dir}/{settings.agents.selfqa.method}.json"
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        logger.info(f"self qa data saved to {save_path}")
        logger.info(f"{request.namespace} successfully generate self qa data")
        response = selfQaResponse(
            status = "success",
            data = results
        )
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