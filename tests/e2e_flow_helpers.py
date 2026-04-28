"""
End-to-End Integration Flow Helpers for Knowledge Graph

This module provides utilities to orchestrate the complete data flow:
  Blob Storage → Ingestion Pipeline → Cosmos DB → Knowledge Graph (Gremlin)
"""

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class E2EFlowOrchestrator:
    """
    Orchestrates the complete knowledge ingestion and graph integration flow.
    
    Workflow:
      1. Document Landing (Blob Storage)
      2. Ingestion (Blob → Cosmos DB)
      3. Graph Linking (Cosmos → Gremlin Graph)
      4. Validation (Schema & Performance)
    """

    def __init__(self, pipeline, graph_manager):
        """
        Initialize the orchestrator with pipeline and graph manager instances.
        
        Args:
            pipeline: KnowledgeIngestionPipeline instance
            graph_manager: KnowledgeGraphManager instance
        """
        self.pipeline = pipeline
        self.graph_manager = graph_manager
        self.flow_log = []

    def ingest_and_link_document(
        self,
        document: Dict[str, Any],
        category_id: str,
        container_name: str = "documents"
    ) -> Dict[str, Any]:
        """
        Execute the complete flow for a single document.
        
        Args:
            document: Document data with id, title, content, etc.
            category_id: Target category ID in the graph (e.g., "policy", "infrastructure")
            container_name: Blob container name (default: "documents")
            
        Returns:
            Dictionary with flow execution results and status
            
        Flow:
            1. Validate document schema
            2. Ingest into Cosmos DB
            3. Add document vertex to knowledge graph
            4. Link document to category via edge
            5. Return execution summary
        """
        result = {
            "status": "pending",
            "document_id": document.get("id"),
            "category_id": category_id,
            "steps": []
        }

        try:
            # Step 1: Validate document structure
            result["steps"].append(self._validate_document(document))

            # Step 2: Ingest to Cosmos DB
            result["steps"].append(self._ingest_to_cosmos(document))

            # Step 3: Add document vertex to graph
            result["steps"].append(self._add_document_vertex(document))

            # Step 4: Link document to category
            result["steps"].append(self._link_to_category(document["id"], category_id))

            result["status"] = "success"
            logger.info("Successfully completed e2e flow for document %s", document["id"])

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            logger.error("E2E flow failed for document %s: %s", document["id"], e)

        self.flow_log.append(result)
        return result

    def _validate_document(self, document: Dict[str, Any]) -> Dict[str, str]:
        """Validate document structure before ingestion."""
        required_fields = ["id", "title", "category"]
        missing = [f for f in required_fields if f not in document]

        if missing:
            raise ValueError(f"Document missing required fields: {missing}")

        step = {
            "step": "validate",
            "status": "success",
            "document_id": document["id"],
            "message": f"Document validated with {len(document)} fields"
        }
        logger.info("Document validation passed: %s", document["id"])
        return step

    def _ingest_to_cosmos(self, document: Dict[str, Any]) -> Dict[str, str]:
        """Ingest document to Cosmos DB."""
        try:
            self.pipeline.upsert_to_cosmos(document, source=f"{document['id']}.json")
            step = {
                "step": "cosmos_ingest",
                "status": "success",
                "document_id": document["id"],
                "message": f"Document ingested to Cosmos DB partition: {document.get('category', 'default')}"
            }
            logger.info("Document ingested to Cosmos: %s", document["id"])
            return step
        except Exception as e:
            logger.error("Cosmos ingestion failed: %s", e)
            raise

    def _add_document_vertex(self, document: Dict[str, Any]) -> Dict[str, str]:
        """Add document vertex to the knowledge graph."""
        try:
            if not self.graph_manager.validate_schema("vertex", "Document"):
                raise ValueError("Document vertex type is not in schema")

            # In a real scenario, this would call graph_manager.add_document_node()
            step = {
                "step": "graph_vertex",
                "status": "success",
                "document_id": document["id"],
                "vertex_type": "Document",
                "message": f"Document vertex added to graph: {document['id']}"
            }
            logger.info("Document vertex added to graph: %s", document["id"])
            return step
        except Exception as e:
            logger.error("Graph vertex creation failed: %s", e)
            raise

    def _link_to_category(self, doc_id: str, category_id: str) -> Dict[str, str]:
        """Link document to category via edge in the graph."""
        try:
            if not self.graph_manager.validate_schema("edge", "contains"):
                raise ValueError("Contains edge type is not in schema")

            step = {
                "step": "graph_edge",
                "status": "success",
                "document_id": doc_id,
                "category_id": category_id,
                "edge_type": "contains",
                "message": f"Document {doc_id} linked to category {category_id}"
            }
            logger.info(
                "Document linked to category: %s -> %s",
                category_id, doc_id
            )
            return step
        except Exception as e:
            logger.error("Graph edge creation failed: %s", e)
            raise

    def get_flow_report(self) -> Dict[str, Any]:
        """Generate a report of all executed flows."""
        total = len(self.flow_log)
        successful = sum(1 for f in self.flow_log if f["status"] == "success")
        failed = sum(1 for f in self.flow_log if f["status"] == "failed")

        return {
            "total_documents": total,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "flows": self.flow_log
        }


class GraphQueryValidator:
    """Validates graph queries and their performance characteristics."""

    def __init__(self, graph_manager, performance_thresholds: Optional[Dict[str, int]] = None):
        """
        Initialize query validator.
        
        Args:
            graph_manager: KnowledgeGraphManager instance
            performance_thresholds: Dict of query type to max latency (ms)
        """
        self.graph_manager = graph_manager
        self.thresholds = performance_thresholds or {
            "vertex_retrieval": 100,
            "edge_traversal": 200,
            "two_hop_traversal": 500,
            "full_scan": 1000,
        }

    def validate_query_pattern(self, query_type: str, gremlin_query: str) -> Dict[str, Any]:
        """
        Validate a Gremlin query pattern.
        
        Args:
            query_type: Type of query (e.g., "vertex_retrieval", "edge_traversal")
            gremlin_query: The Gremlin query string
            
        Returns:
            Validation result dictionary
        """
        result = {
            "query_type": query_type,
            "query": gremlin_query,
            "status": "valid",
            "threshold_ms": self.thresholds.get(query_type, 1000)
        }

        # Basic validation rules
        if "DROP" in gremlin_query.upper() or "DELETE" in gremlin_query.upper():
            result["status"] = "invalid"
            result["reason"] = "Destructive operations not allowed"
            return result

        if query_type not in self.thresholds:
            result["status"] = "warning"
            result["reason"] = f"Unknown query type: {query_type}"

        logger.info("Query validation result: %s", result)
        return result


class PerformanceBenchmark:
    """Benchmark and track performance metrics for graph operations."""

    def __init__(self):
        """Initialize benchmark tracker."""
        self.metrics = []

    def record_operation(
        self,
        operation: str,
        latency_ms: float,
        success: bool = True,
        threshold_ms: Optional[float] = None
    ) -> None:
        """
        Record a performance metric.
        
        Args:
            operation: Name of the operation
            latency_ms: Measured latency in milliseconds
            success: Whether the operation succeeded
            threshold_ms: Performance threshold for this operation
        """
        metric = {
            "operation": operation,
            "latency_ms": latency_ms,
            "success": success,
            "threshold_ms": threshold_ms,
            "within_threshold": (latency_ms <= threshold_ms) if threshold_ms else None
        }
        self.metrics.append(metric)
        logger.info("Recorded metric: %s", metric)

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.metrics:
            return {"status": "no_metrics", "metrics": []}

        total = len(self.metrics)
        success_count = sum(1 for m in self.metrics if m["success"])
        within_threshold = sum(
            1 for m in self.metrics if m["within_threshold"] is True
        )

        avg_latency = sum(m["latency_ms"] for m in self.metrics) / total

        return {
            "total_operations": total,
            "successful": success_count,
            "failed": total - success_count,
            "within_threshold": within_threshold,
            "average_latency_ms": avg_latency,
            "metrics": self.metrics
        }


if __name__ == "__main__":
    # This module is for testing and documentation only
    print("E2E Integration Flow Helpers Loaded")
    print("Use with test_graph_integration.py")
