import logging
import os
from gremlin_python.driver import client, serializer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KnowledgeGraphManager:
    def __init__(self, endpoint, key, database_name, graph_name):
        # Format the endpoint for Gremlin
        self.endpoint = endpoint.replace("https://", "wss://").replace(".documents.azure.com:443/", ".gremlin.cosmos.azure.com:443/")
        self.key = key
        self.client = client.Client(
            self.endpoint,
            'g',
            username=f"/dbs/{database_name}/colls/{graph_name}",
            password=self.key,
            message_serializer=serializer.GraphSONSerializersV2d0()
        )

    def initialize_graph(self):
        """Initialize the graph with core vertex types for the DBE Expert System."""
        logger.info("Initializing Knowledge Graph structure...")

        queries = [
            "g.addV('ExpertSystem').property('id', 'dbe_root').property('name', 'DBE AI Expert System')",
            "g.addV('Category').property('id', 'policy').property('name', 'Educational Policy')",
            "g.addV('Category').property('id', 'infrastructure').property('name', 'School Infrastructure')",
            "g.V('dbe_root').addE('manages').to(g.V('policy'))",
            "g.V('dbe_root').addE('manages').to(g.V('infrastructure'))"
        ]

        for q in queries:
            try:
                result = self.client.submit(q).all().result()
                logger.debug("Executed graph query: %s -> %s", q, result)
            except Exception as e:
                logger.warning("Error executing graph query '%s': %s", q, e)

    def add_document_node(self, doc_id, doc_name, category_id):
        """Link a document to a category in the graph."""
        if not self.validate_schema('vertex', 'Document'):
            raise ValueError("Schema validation failed for vertex label 'Document'")

        query = f"g.addV('Document').property('id', '{doc_id}').property('name', '{doc_name}')"
        self.client.submit(query).all().result()

        link_query = f"g.V('{category_id}').addE('contains').to(g.V('{doc_id}'))"
        self.client.submit(link_query).all().result()
        logger.info("Added document %s to category %s", doc_name, category_id)

    def validate_schema(self, element_type, label, properties=None):
        """Verify if a label and its properties are part of the allowed schema."""
        schema = self.get_schema_definition()

        if element_type == 'vertex':
            if label not in schema['vertices']:
                logger.error("Invalid vertex label: %s", label)
                return False
        elif element_type == 'edge':
            if label not in schema['edges']:
                logger.error("Invalid edge label: %s", label)
                return False
        else:
            logger.error("Invalid schema element type: %s", element_type)
            return False

        if properties:
            allowed_props = schema['properties'].get(label, [])
            for prop in properties:
                if prop not in allowed_props:
                    logger.warning("Property '%s' is not in the defined schema for '%s'", prop, label)

        return True

    def get_schema_definition(self):
        """Returns the current graph schema definition including allowed properties."""
        return {
            "vertices": ["ExpertSystem", "Category", "Document", "Agent"],
            "edges": ["manages", "contains", "references", "triggers"],
            "properties": {
                "ExpertSystem": ["id", "name", "version"],
                "Category": ["id", "name", "description"],
                "Document": ["id", "name", "source", "category"],
                "Agent": ["id", "name", "type"]
            }
        }

if __name__ == "__main__":
    ENDPOINT = os.getenv("COSMOS_GREMLIN_ENDPOINT")
    KEY = os.getenv("COSMOS_GREMLIN_KEY")

    if ENDPOINT and KEY:
        manager = KnowledgeGraphManager(ENDPOINT, KEY, "KnowledgeDB", "ExpertGraph")
        manager.initialize_graph()
    else:
        logger.warning("COSMOS_GREMLIN_ENDPOINT or COSMOS_GREMLIN_KEY not set.")
