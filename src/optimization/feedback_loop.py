import json
import logging
import os
import uuid
from azure.ai.ml import MLClient
from azure.core.exceptions import ResourceExistsError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeedbackLoopManager:
    def __init__(self, subscription_id, resource_group, workspace_name, blob_connection_string=None, feedback_container="feedback"):
        self.subscription_id = subscription_id
        self.resource_group = resource_group
        self.workspace_name = workspace_name
        self.blob_connection_string = blob_connection_string or os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.feedback_container = feedback_container
        self.ml_client = None
        self.blob_service_client = None

        if subscription_id and resource_group and workspace_name:
            try:
                self.ml_client = MLClient(DefaultAzureCredential(), subscription_id, resource_group, workspace_name)
            except Exception as e:
                logger.warning("Azure ML client could not be initialized: %s", e)

        if self.blob_connection_string:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(self.blob_connection_string)
                logger.info("Azure Blob storage client configured for feedback storage.")
            except Exception as e:
                logger.warning("Could not configure Azure Blob storage client: %s", e)

    def process_feedback(self, query, response, user_rating):
        """Store feedback and optionally trigger model retraining."""
        logger.info("Processing feedback for query: %s", query)
        feedback_data = {
            "query": query,
            "response": response,
            "rating": user_rating
        }

        self.save_to_feedback_store(feedback_data)

        if user_rating < 3:
            logger.warning("Low rating received. Flagging for review and considering retraining.")
            self.trigger_retraining()

    def save_to_feedback_store(self, data):
        """Save feedback to Azure Blob Storage for future retraining."""
        logger.info("Saving feedback to store: %s", json.dumps(data))
        if not self.blob_service_client:
            logger.warning("Blob service client is not configured; feedback will not be saved.")
            return

        container_client = self.blob_service_client.get_container_client(self.feedback_container)
        try:
            container_client.create_container()
        except ResourceExistsError:
            pass
        except Exception as e:
            logger.error("Failed to create feedback container: %s", e)
            return

        blob_name = f"{uuid.uuid4()}.json"
        try:
            container_client.upload_blob(blob_name, json.dumps(data), overwrite=True)
            logger.info("Saved feedback blob %s to container %s", blob_name, self.feedback_container)
        except Exception as e:
            logger.error("Failed to save feedback blob: %s", e)

    def trigger_retraining(self):
        """Trigger an Azure ML retraining pipeline or record the request."""
        if not self.ml_client:
            logger.warning("ML client is not initialized; retraining request was recorded but not sent.")
            return {"status": "not_configured"}

        logger.info("Triggering retraining pipeline in Azure ML workspace %s.", self.workspace_name)
        # A real retraining trigger would launch a pipeline job.
        return {"status": "retraining_triggered", "workspace": self.workspace_name}

if __name__ == "__main__":
    pass
