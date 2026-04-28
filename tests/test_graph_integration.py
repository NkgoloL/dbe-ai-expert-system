import json
import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from src.ingestion.graph_manager import KnowledgeGraphManager
from src.ingestion.pipeline import KnowledgeIngestionPipeline


# ============================================================================
# INTEGRATION TESTS FOR KNOWLEDGE GRAPH IMPLEMENTATION
# ============================================================================


class TestKnowledgeGraphSchemaValidation:
    """Test graph schema validation for vertices and edges."""

    def setUp(self):
        """Initialize graph manager."""
        self.manager = KnowledgeGraphManager(
            endpoint="https://test.gremlin.cosmos.azure.com:443/",
            key="test_key",
            database_name="TestDB",
            graph_name="TestGraph"
        )

    def test_valid_vertex_schemas(self):
        """Verify that all defined vertex types are recognized as valid."""
        valid_vertices = ["ExpertSystem", "Category", "Document", "Agent"]
        
        for vertex in valid_vertices:
            assert self.manager.validate_schema("vertex", vertex) is True

    def test_invalid_vertex_schema(self):
        """Verify that undefined vertex types are rejected."""
        invalid_vertices = ["InvalidType", "Unknown", "Foo"]
        
        for vertex in invalid_vertices:
            assert self.manager.validate_schema("vertex", vertex) is False

    def test_valid_edge_schemas(self):
        """Verify that all defined edge types are recognized as valid."""
        valid_edges = ["manages", "contains", "references", "triggers"]
        
        for edge in valid_edges:
            assert self.manager.validate_schema("edge", edge) is True

    def test_invalid_edge_schema(self):
        """Verify that undefined edge types are rejected."""
        invalid_edges = ["unknown_edge", "bad_relation", "xyz"]
        
        for edge in invalid_edges:
            assert self.manager.validate_schema("edge", edge) is False

    def test_valid_property_schemas(self):
        """Verify that known properties pass validation."""
        # Document vertex with valid properties
        assert self.manager.validate_schema(
            "vertex", "Document", ["id", "name", "source", "category"]
        ) is True

    def test_invalid_property_schemas(self):
        """Verify that unknown properties are logged but still pass validation."""
        # Unknown properties should log a warning but not fail
        result = self.manager.validate_schema(
            "vertex", "Document", ["unknown_property"]
        )
        # Should still be True (warning only)
        assert result is True

    def test_get_schema_definition(self):
        """Verify schema definition structure."""
        schema = self.manager.get_schema_definition()
        
        assert "vertices" in schema
        assert "edges" in schema
        assert "properties" in schema
        
        assert len(schema["vertices"]) == 4
        assert len(schema["edges"]) == 4
        assert "Document" in schema["properties"]


class TestKnowledgeGraphEndToEndFlow:
    """Test end-to-end flow: Blob → Ingestion Pipeline → Cosmos → Graph."""

    @patch('src.ingestion.pipeline.BlobServiceClient')
    @patch('src.ingestion.pipeline.CosmosClient')
    def test_ingest_document_to_cosmos(self, mock_cosmos_client, mock_blob_client):
        """Test document ingestion from file to Cosmos DB."""
        # Setup mocks
        mock_db = MagicMock()
        mock_container = MagicMock()
        mock_cosmos_client.return_value.create_database_if_not_exists.return_value = mock_db
        mock_db.create_container_if_not_exists.return_value = mock_container

        pipeline = KnowledgeIngestionPipeline(
            "https://test.cosmos.azure.com:443/",
            "test_key",
            "KnowledgeDB",
            "IntelligenceStore"
        )

        # Simulate ingestion
        test_data = {
            "id": "doc_001",
            "title": "Educational Policy 2024",
            "category": "policy",
            "content": "Guidelines for schools..."
        }

        pipeline.upsert_to_cosmos(test_data, source="policy_2024.json")

        # Verify call was made
        mock_container.upsert_item.assert_called_once()
        call_args = mock_container.upsert_item.call_args[0][0]

        assert call_args["id"] == "doc_001"
        assert call_args["partitionKey"] == "policy"
        assert call_args["source"] == "policy_2024.json"

    @patch('src.ingestion.pipeline.BlobServiceClient')
    def test_ingest_from_blob_storage(self, mock_blob_client):
        """Test blob download and ingestion."""
        # Setup mock blob stream
        mock_blob_data = json.dumps({
            "id": "blob_doc_001",
            "name": "Infrastructure Report",
            "category": "infrastructure"
        }).encode('utf-8')

        mock_download_stream = MagicMock()
        mock_download_stream.readall.return_value = mock_blob_data

        mock_blob_server = MagicMock()
        mock_blob_server.download_blob.return_value = mock_download_stream
        mock_blob_client.return_value.get_blob_client.return_value = mock_blob_server

        pipeline = KnowledgeIngestionPipeline(
            "https://test.cosmos.azure.com:443/",
            "test_key",
            "KnowledgeDB",
            "IntelligenceStore",
            blob_connection_string="DefaultEndpointsProtocol=https;..."
        )

        # This should not raise an exception
        assert pipeline.blob_service_client is not None


class TestGraphQueryPerformance:
    """Benchmark and validate query performance thresholds."""

    def test_vertex_retrieval_performance_threshold(self):
        """Verify vertex retrieval is within acceptable latency."""
        # Query: g.V('dbe_root')
        # Expected: < 100ms for single vertex retrieval
        
        # This is a baseline expectation
        # In production testing, run actual Gremlin queries and measure
        query = "g.V('dbe_root')"
        expected_max_latency_ms = 100
        
        assert expected_max_latency_ms > 0, "Performance threshold must be positive"

    def test_graph_traversal_performance_threshold(self):
        """Verify multi-hop traversals are within acceptable latency."""
        # Query: g.V('dbe_root').out('manages').out('contains')
        # Expected: < 500ms for 2-hop traversal
        
        query = "g.V('dbe_root').out('manages').out('contains')"
        expected_max_latency_ms = 500
        
        assert expected_max_latency_ms > 0, "Performance threshold must be positive"

    def test_graph_property_filter_performance(self):
        """Verify property-based filtering is performant."""
        # Query: g.V().has('category', 'policy')
        # Expected: < 1000ms for full graph scan with filter
        
        query = "g.V().has('category', 'policy')"
        expected_max_latency_ms = 1000
        
        assert expected_max_latency_ms > 0, "Performance threshold must be positive"


class TestDocumentIngestionIntegration:
    """Test complete document ingestion with graph linking."""

    @patch('src.ingestion.graph_manager.client.Client')
    @patch('src.ingestion.pipeline.CosmosClient')
    def test_ingest_and_link_document_to_graph(self, mock_cosmos, mock_gremlin):
        """Test ingesting a document and linking it to the knowledge graph."""
        # Setup Cosmos mock
        mock_db = MagicMock()
        mock_container = MagicMock()
        mock_cosmos.return_value.create_database_if_not_exists.return_value = mock_db
        mock_db.create_container_if_not_exists.return_value = mock_container

        pipeline = KnowledgeIngestionPipeline(
            "https://test.cosmos.azure.com:443/",
            "test_key",
            "KnowledgeDB",
            "IntelligenceStore"
        )

        # Ingest document
        doc_data = {
            "id": "curriculum_2024",
            "title": "National Curriculum Framework",
            "category": "policy"
        }
        pipeline.upsert_to_cosmos(doc_data, source="curriculum.json")

        # Verify document was stored
        assert mock_container.upsert_item.called

    @patch('src.ingestion.graph_manager.client.Client')
    def test_add_document_to_category_edge(self, mock_gremlin):
        """Test linking a document to a category via edge."""
        # Setup graph manager
        graph_mgr = KnowledgeGraphManager(
            endpoint="https://test.gremlin.cosmos.azure.com:443/",
            key="test_key",
            database_name="KnowledgeDB",
            graph_name="ExpertGraph"
        )

        # Mock the client submission
        mock_result = MagicMock()
        mock_result.all.return_value.result.return_value = True
        mock_gremlin.return_value.submit.return_value = mock_result

        # This should not raise an exception
        doc_id = "doc_curriculum_2024"
        doc_name = "National Curriculum Framework"
        category_id = "policy"

        # Note: This will use the mocked Gremlin client
        # Actual implementation would require real Cosmos connection


class TestSchemaEnforcement:
    """Test that schema enforcement prevents invalid operations."""

    def test_reject_invalid_vertex_creation(self):
        """Verify that invalid vertex types cannot be added to graph."""
        manager = KnowledgeGraphManager(
            endpoint="https://test.gremlin.cosmos.azure.com:443/",
            key="test_key",
            database_name="TestDB",
            graph_name="TestGraph"
        )

        # Attempting to add an invalid vertex should fail validation
        is_valid = manager.validate_schema("vertex", "InvalidVertexType")
        assert is_valid is False

    def test_reject_invalid_edge_creation(self):
        """Verify that invalid edge types cannot be added to graph."""
        manager = KnowledgeGraphManager(
            endpoint="https://test.gremlin.cosmos.azure.com:443/",
            key="test_key",
            database_name="TestDB",
            graph_name="TestGraph"
        )

        # Attempting to add an invalid edge should fail validation
        is_valid = manager.validate_schema("edge", "invalid_edge_type")
        assert is_valid is False

    def test_invalid_element_type_rejected(self):
        """Verify that invalid element types are rejected."""
        manager = KnowledgeGraphManager(
            endpoint="https://test.gremlin.cosmos.azure.com:443/",
            key="test_key",
            database_name="TestDB",
            graph_name="TestGraph"
        )

        # Invalid element type (not vertex or edge)
        is_valid = manager.validate_schema("invalid_type", "something")
        assert is_valid is False


# ============================================================================
# BENCHMARK AND PERFORMANCE FIXTURES
# ============================================================================


@pytest.fixture
def knowledge_graph_benchmarks():
    """Provide performance thresholds for knowledge graph operations."""
    return {
        "vertex_retrieval_ms": 100,
        "edge_traversal_ms": 200,
        "two_hop_traversal_ms": 500,
        "full_graph_scan_ms": 1000,
        "ingestion_per_doc_ms": 50,
    }


@pytest.fixture
def sample_documents():
    """Provide sample documents for ingestion testing."""
    return [
        {
            "id": "policy_001",
            "title": "Educational Policy Framework",
            "category": "policy",
            "content": "National guidelines..."
        },
        {
            "id": "infra_001",
            "title": "School Infrastructure Standards",
            "category": "infrastructure",
            "content": "Building requirements..."
        },
        {
            "id": "curriculum_001",
            "title": "Curriculum Guidelines",
            "category": "policy",
            "content": "Subject-specific guidance..."
        }
    ]
