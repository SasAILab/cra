from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from pycra.api.models.common import ContractGraphRequest
from pycra.utils import setup_logger
from pycra.core.knowledge_graph import KgBuilder
from pycra.api.core.dependencies import get_kgBuilder_async, get_factory
from pycra.api.models.knowledge_graph import BuildReturnModel
from pycra.api.models.selfqa import SelfQaRequest, SelfQaSubgrapnResponse
from pycra.core.agents.selfqa.sub_graph import SubGraphBuilder

logger = setup_logger(name="pycra-api-selfqa")
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
        factory = await get_factory()
        llm_pycra = factory.llm_pycra
        builder = SubGraphBuilder(llm_pycra=llm_pycra)
        result_generator  = builder(request.namespace)
        for df in result_generator:
            print(f"获得一个子图数据 {df}")
        return SelfQaSubgrapnResponse(
            answer = "1"
        )
    except Exception as e:
        logger.error(f"Failed to build contract graph: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build contract graph: {str(e)}"
        )

