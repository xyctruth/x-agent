from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Request, status

from x_agent.agent.nl2sql_agent import Nl2SqlGenerationError
from x_agent.api.v1.schemas import (
    GeneratedSqlResponse,
    Nl2SqlGenerateRequest,
    Nl2SqlGenerateResponse,
    SqlKnowledgeItemResponse,
    SqlRetrievalPlanStepResponse,
    SqlValidationResponse,
)
from x_agent.application.llm import LLMProviderError
from x_agent.application.nl2sql import GenerateSqlCommand, Nl2SqlService

router = APIRouter(prefix="/api/v1/nl2sql", tags=["nl2sql"])


def get_nl2sql_service(request: Request) -> Nl2SqlService:
    return cast(Nl2SqlService, request.app.state.nl2sql_service)


@router.post("/generate")
async def generate_sql(
    request: Nl2SqlGenerateRequest,
    service: Annotated[Nl2SqlService, Depends(get_nl2sql_service)],
) -> Nl2SqlGenerateResponse:
    try:
        result = service.generate(
            GenerateSqlCommand(
                question=request.question,
                metadata=request.metadata,
            ),
        )
    except (LLMProviderError, Nl2SqlGenerationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="NL2SQL generation failed",
        ) from exc

    return Nl2SqlGenerateResponse(
        question=result.question,
        retrieval_plan=tuple(
            SqlRetrievalPlanStepResponse(
                query=step.query,
                knowledge_types=step.knowledge_types,
                reason=step.reason,
            )
            for step in result.retrieval_plan
        ),
        retrieved_context=tuple(
            SqlKnowledgeItemResponse(
                id=item.id,
                type=item.type,
                name=item.name,
                content=item.content,
                metadata=item.metadata,
            )
            for item in result.retrieved_context
        ),
        generated_sql=GeneratedSqlResponse(
            sql=result.generated_sql.sql,
            explanation=result.generated_sql.explanation,
            assumptions=result.generated_sql.assumptions,
        ),
        validation=SqlValidationResponse(
            is_valid=result.validation.is_valid,
            errors=result.validation.errors,
            warnings=result.validation.warnings,
            referenced_tables=result.validation.referenced_tables,
        ),
    )
