import json
import logging
from abc import ABC, abstractmethod
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExpertModel(ABC):
    @abstractmethod
    async def predict(self, query, context):
        pass

class AzureMLExpertModel(ExpertModel):
    def __init__(self, endpoint_url, api_key):
        self.endpoint_url = endpoint_url
        self.api_key = api_key

    async def predict(self, query, context):
        """Call an Azure ML Online Endpoint asynchronously."""
        if not self.endpoint_url:
            return f"Simulated Insight: Focus on {query[:30]} in context of {context[:30]}."

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "input_data": {
                "columns": ["query", "context"],
                "data": [[query, context]]
            }
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(self.endpoint_url, json=payload, headers=headers)
                response.raise_for_status()
                parsed = response.json()

                if isinstance(parsed, dict) and "result" in parsed:
                    return parsed["result"]
                if isinstance(parsed, list) and parsed:
                    return parsed[0]
                return json.dumps(parsed)
        except Exception as e:
            logger.error("Error calling Azure ML endpoint: %s", e)
            return f"Error: Could not reach expert model. {str(e)}"

class BaselinePolicyModel(ExpertModel):
    async def predict(self, query, context):
        """A simple baseline model that uses heuristics."""
        logger.info("Using Baseline Policy Model")
        query_lower = query.lower()

        if "infrastructure" in query_lower:
            return "Infrastructure Recommendation: Ensure all schools have broadband connectivity."
        elif "policy" in query_lower:
            return "Policy Recommendation: Align with the latest 2024 Educational Standards."
        else:
            return "General Recommendation: Refer to the DBE Master Plan."
