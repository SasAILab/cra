from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from pycra.api.models.common import ContractGraphRequest
from pycra.utils.logger import cckg_logger as logger
from pycra.core.knowledge_graph import KgBuilder
from pycra.api.core.dependencies import get_kgBuilder_async
from pycra.api.models.knowledge_graph import BuildReturnModel
cckg_router = APIRouter(prefix="/cckg", tags=["CCKG"]) # current contract knowledge graph

@cckg_router.post("/build", response_model=BuildReturnModel, tags=["CCKG"], summary="Build a contract graph for current contract")
async def build_contract_graph(request: ContractGraphRequest, kg_builder: KgBuilder = Depends(get_kgBuilder_async),) -> BuildReturnModel:
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
