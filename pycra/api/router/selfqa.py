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
        results, results_multihop, results_cot = await generatorService.build(namespace=request.namespace)
        save_dir = f"{settings.kg.working_dir}/selfqa_data/{request.namespace}"
        os.makedirs(save_dir, exist_ok=True)
        save_path_aggregated = f"{save_dir}/aggregated.json"
        save_path_multihop = f"{save_dir}/multi_hop.json"
        save_path_cot = f"{save_dir}/cot.json"
        with open(save_path_aggregated, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        with open(save_path_multihop, 'w', encoding='utf-8') as f:
            json.dump(results_multihop, f, ensure_ascii=False, indent=2)
        with open(save_path_cot, 'w', encoding='utf-8') as f:
            json.dump(results_cot, f, ensure_ascii=False, indent=2)
        logger.info(f"{request.namespace} successfully generate self qa data")
        response = selfQaResponse(
            status = "success",
            aggregated = results,
            multi_hop = results_multihop,
            cot = results_cot
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
        batches, batches_leiden = await builder(request.namespace)

        return SelfQaSubgrapnResponse(
            status = "success",
            batches = batches,
            batches_leiden = batches_leiden
        )
    except Exception as e:
        logger.error(f"Failed to build contract graph: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build contract graph: {str(e)}"
        )