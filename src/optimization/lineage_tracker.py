import logging
from azure.ai.ml import MLClient
from azure.identity import DefaultAzureCredential

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LineageTracker:
    def __init__(self, subscription_id, resource_group, workspace_name):
        self.ml_client = None
        try:
            self.ml_client = MLClient(DefaultAzureCredential(), subscription_id, resource_group, workspace_name)
        except Exception as e:
            logger.warning("Azure ML client could not be initialized for lineage tracking: %s", e)

    def track_model_version(self, model_name, version, dataset_id):
        """Track which dataset was used to train a specific model version."""
        logger.info("Tracking lineage for %s v%s", model_name, version)
        if not self.ml_client:
            logger.warning("Lineage tracker is not configured. Skipping model version tagging.")
            return

        try:
            model = self.ml_client.models.get(name=model_name, version=version)
            tags = getattr(model, "tags", {}) or {}
            tags["trained_on_dataset"] = dataset_id
            model.tags = tags
            self.ml_client.models.create_or_update(model)
            logger.info("Model %s:%s successfully linked to dataset %s", model_name, version, dataset_id)
        except Exception as e:
            logger.error("Could not update model lineage for %s:%s: %s", model_name, version, e)

    def log_inference_event(self, model_version, query_id):
        """Log an inference event for auditing and lineage."""
        logger.info("Logging inference event: model=%s, query=%s", model_version, query_id)
        # Extend this method to push custom telemetry to Azure Monitor or event storage.
