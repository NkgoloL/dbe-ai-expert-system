import os
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, BaseSettings
from typing import List, Optional
import uvicorn

from src.models.expert_model import AzureMLExpertModel, BaselinePolicyModel
from src.optimization.feedback_loop import FeedbackLoopManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AppSettings(BaseSettings):
    AZURE_ML_ENDPOINT: Optional[str] = None
    AZURE_ML_KEY: Optional[str] = None
    AZURE_SUBSCRIPTION_ID: Optional[str] = None
    AZURE_RESOURCE_GROUP: Optional[str] = None
    AZURE_ML_WORKSPACE: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = AppSettings()

app = FastAPI(title="DBE AI Agent Orchestration Service")

class QueryRequest(BaseModel):
    query: str
    user_id: Optional[str] = "anonymous"

class AgentResponse(BaseModel):
    response: str
    sources: List[str]
    confidence: float

class FeedbackPayload(BaseModel):
    query: str
    response: str
    rating: int

def get_expert_model():
    if settings.AZURE_ML_ENDPOINT and settings.AZURE_ML_KEY:
        return AzureMLExpertModel(settings.AZURE_ML_ENDPOINT, settings.AZURE_ML_KEY)
    return BaselinePolicyModel()

expert_model = get_expert_model()

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

async def retrieve_context(query: str) -> str:
    return f"Retrieved context for query: {query}"

@app.post("/ask", response_model=AgentResponse)
async def ask_agent(request: QueryRequest):
    try:
        context = await retrieve_context(request.query)
        expert_advice = await expert_model.predict(request.query, context)
        reasoning_result = perform_reasoning(request.query, expert_advice)

        sources = ["Internal Knowledge Base"]
        if isinstance(expert_model, AzureMLExpertModel):
            sources.append("Azure ML Endpoint")
        else:
            sources.append("Baseline Policy Model")

        return AgentResponse(
            response=reasoning_result,
            sources=sources,
            confidence=0.98
        )
    except Exception as e:
        logger.exception("Error processing ask request")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def receive_feedback(payload: FeedbackPayload):
    manager = FeedbackLoopManager(
        settings.AZURE_SUBSCRIPTION_ID or "",
        settings.AZURE_RESOURCE_GROUP or "",
        settings.AZURE_ML_WORKSPACE or ""
    )
    manager.process_feedback(payload.query, payload.response, payload.rating)
    return {"status": "feedback received"}

def perform_reasoning(query: str, context: str) -> str:
    return (
        f"Based on the retrieved context '{context}', the system synthesizes the answer to '{query}' "
        "through expert policy reasoning and source alignment."
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
