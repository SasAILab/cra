from dataclasses import dataclass
from typing import Generic, TypeVar, Union, List, Dict, Any, Optional, cast
import html
import os
import networkx as nx
from neo4j import GraphDatabase, AsyncGraphDatabase
from neo4j.exceptions import Neo4jError
T = TypeVar("T")
from langchain_community.graphs import Neo4jGraph
from pycra import settings
from pycra.utils.logger import cckg_logger as logger

class GraphStore:
    """
    Wrapper for Neo4j Graph Database.
    Enhanced with additional methods for contract graph operations.
    """
    
    def __init__(self):
        if not settings or not settings.graph_store.neo4j:
            logger.warning("Graph store configuration missing or disabled.")
            self.graph = None
            return

        neo4j_config = settings.graph_store.neo4j
        try:
            self.graph = Neo4jGraph(
                url=neo4j_config.uri,
                username=neo4j_config.username,
                password=neo4j_config.password
            )
            logger.info("Connected to Neo4j Graph Database.")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.graph = None

    def query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query.
        """
        if not self.graph:
            logger.warning("Graph store not initialized, returning empty result.")
            return []
            
        return self.graph.query(query, params=params)

    def refresh_schema(self):
        if self.graph:
            self.graph.refresh_schema()
    
    def get_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a node by its ID.
        
        Args:
            node_id: ID of the node to retrieve
            
        Returns:
            Node data if found, None otherwise
        """
        query = f"MATCH (n {{ id: '{node_id}' }}) RETURN n"
        results = self.query(query)
        if results:
            return results[0]["n"]
        return None
    
    def get_relationships_by_node(self, node_id: str) -> List[Dict[str, Any]]:
        """
        Get all relationships for a specific node.
        
        Args:
            node_id: ID of the node to get relationships for
            
        Returns:
            List of relationships
        """
        query = f"MATCH (n {{ id: '{node_id}' }})-[r]-(m) RETURN r, m"
        return self.query(query)
    
    def get_nodes_by_type(self, node_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get nodes by their type.
        
        Args:
            node_type: Type of nodes to retrieve
            limit: Maximum number of nodes to return
            
        Returns:
            List of nodes
        """
        query = f"MATCH (n:{node_type}) RETURN n LIMIT {limit}"
        results = self.query(query)
        return [result["n"] for result in results]
    
    def get_relationships_by_type(self, relationship_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get relationships by their type.
        
        Args:
            relationship_type: Type of relationships to retrieve
            limit: Maximum number of relationships to return
            
        Returns:
            List of relationships
        """
        query = f"MATCH ()-[r:{relationship_type}]->() RETURN r LIMIT {limit}"
        results = self.query(query)
        return [result["r"] for result in results]
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get graph statistics.
        
        Returns:
            Dictionary containing graph statistics
        """
        stats = {
            "node_count": 0,
            "relationship_count": 0,
            "node_types": {},
            "relationship_types": {}
        }
        
        # Get total node count
        node_count_query = "MATCH (n) RETURN count(n) AS count"
        node_count_result = self.query(node_count_query)
        if node_count_result:
            stats["node_count"] = node_count_result[0]["count"]
        
        # Get total relationship count
        rel_count_query = "MATCH ()-[r]->() RETURN count(r) AS count"
        rel_count_result = self.query(rel_count_query)
        if rel_count_result:
            stats["relationship_count"] = rel_count_result[0]["count"]
        
        # Get node types and counts
        node_types_query = "MATCH (n) RETURN labels(n) AS labels, count(n) AS count"
        node_types_result = self.query(node_types_query)
        for result in node_types_result:
            for label in result["labels"]:
                stats["node_types"][label] = result["count"]
        
        # Get relationship types and counts
        rel_types_query = "MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS count"
        rel_types_result = self.query(rel_types_query)
        for result in rel_types_result:
            stats["relationship_types"][result["type"]] = result["count"]
        
        return stats
    
    def clear_graph(self, graph_id: str) -> bool:
        """
        Clear all nodes and relationships for a specific graph.
        
        Args:
            graph_id: ID of the graph to clear
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete relationships first
            rel_query = f"MATCH ()-[r {{ graph_id: '{graph_id}' }}]->() DELETE r"
            self.query(rel_query)
            
            # Delete nodes
            node_query = f"MATCH (n {{ graph_id: '{graph_id}' }}) DELETE n"
            self.query(node_query)
            
            # Delete metadata node
            meta_query = f"MATCH (m:GraphMetadata {{ graph_id: '{graph_id}' }}) DELETE m"
            self.query(meta_query)
            
            logger.info(f"Cleared graph {graph_id} successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to clear graph {graph_id}: {e}")
            return False
    
    def clear_all_graphs(self) -> bool:
        """
        Clear all graphs from the database.
        Use with caution!
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete all relationships
            self.query("MATCH ()-[r]->() DELETE r")
            
            # Delete all nodes
            self.query("MATCH (n) DELETE n")
            
            logger.info("Cleared all graphs successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to clear all graphs: {e}")
            return False
    
    def execute_batch(self, queries: List[str]) -> List[List[Dict[str, Any]]]:
        """
        Execute multiple queries in a batch.
        
        Args:
            queries: List of Cypher queries to execute
            
        Returns:
            List of results for each query
        """
        results = []
        for query in queries:
            results.append(self.query(query))
        return results
    
    def get_shortest_path(self, source_id: str, target_id: str, max_depth: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        Get the shortest path between two nodes.
        
        Args:
            source_id: ID of the source node
            target_id: ID of the target node
            max_depth: Maximum depth to search
            
        Returns:
            List of nodes and relationships in the shortest path, or None if no path found
        """
        query = f"MATCH p=shortestPath((a {{ id: '{source_id}' }})-[*1..{max_depth}]-(b {{ id: '{target_id}' }})) RETURN p"
        results = self.query(query)
        
        if results:
            return results[0]["p"]
        return None


@dataclass
class StorageNameSpace:
    working_dir: str = None
    namespace: str = None

    async def index_done_callback(self):
        """commit the storage operations after indexing"""

    async def query_done_callback(self):
        """commit the storage operations after querying"""


@dataclass
class BaseListStorage(Generic[T], StorageNameSpace):
    async def all_items(self) -> list[T]:
        raise NotImplementedError

    async def get_by_index(self, index: int) -> Union[T, None]:
        raise NotImplementedError

    async def append(self, data: T):
        raise NotImplementedError

    async def upsert(self, data: list[T]):
        raise NotImplementedError

    async def drop(self):
        raise NotImplementedError


@dataclass
class BaseKVStorage(Generic[T], StorageNameSpace):
    async def all_keys(self) -> list[str]:
        raise NotImplementedError

    async def get_by_id(self, id: str) -> Union[T, None]:
        raise NotImplementedError

    async def get_by_ids(
        self, ids: list[str], fields: Union[set[str], None] = None
    ) -> list[Union[T, None]]:
        raise NotImplementedError

    async def filter_keys(self, data: list[str]) -> set[str]:
        """return un-exist keys"""
        raise NotImplementedError

    async def upsert(self, data: dict[str, T]):
        raise NotImplementedError

    async def drop(self):
        raise NotImplementedError


@dataclass
class BaseGraphStorage(StorageNameSpace):
    async def has_node(self, node_id: str) -> bool:
        raise NotImplementedError

    async def has_edge(self, source_node_id: str, target_node_id: str) -> bool:
        raise NotImplementedError

    async def node_degree(self, node_id: str) -> int:
        raise NotImplementedError

    async def edge_degree(self, src_id: str, tgt_id: str) -> int:
        raise NotImplementedError

    async def get_node(self, node_id: str) -> Union[dict, None]:
        raise NotImplementedError

    async def update_node(self, node_id: str, node_data: dict[str, str]):
        raise NotImplementedError

    async def get_all_nodes(self) -> Union[list[tuple[str, dict]], None]:
        raise NotImplementedError

    async def get_edge(
        self, source_node_id: str, target_node_id: str
    ) -> Union[dict, None]:
        raise NotImplementedError

    async def update_edge(
        self, source_node_id: str, target_node_id: str, edge_data: dict[str, str]
    ):
        raise NotImplementedError

    async def get_all_edges(self) -> Union[list[tuple[str, str, dict]], None]:
        raise NotImplementedError

    async def get_node_edges(
        self, source_node_id: str
    ) -> Union[list[tuple[str, str]], None]:
        raise NotImplementedError

    async def upsert_node(self, node_id: str, node_data: dict[str, str]):
        raise NotImplementedError

    async def upsert_edge(
        self, source_node_id: str, target_node_id: str, edge_data: dict[str, str]
    ):
        raise NotImplementedError

    async def delete_node(self, node_id: str):
        raise NotImplementedError


@dataclass
class NetworkXStorage(BaseGraphStorage):
    @staticmethod
    def load_nx_graph(file_name) -> Optional[nx.Graph]:
        if os.path.exists(file_name):
            return nx.read_graphml(file_name)
        return None

    @staticmethod
    def write_nx_graph(graph: nx.Graph, file_name):
        logger.info(
            "Writing graph with %d nodes, %d edges",
            graph.number_of_nodes(),
            graph.number_of_edges(),
        )
        nx.write_graphml(graph, file_name)

    @staticmethod
    def stable_largest_connected_component(graph: nx.Graph) -> nx.Graph:
        """Refer to https://github.com/microsoft/graphrag/index/graph/utils/stable_lcc.py
        Return the largest connected component of the graph, with nodes and edges sorted in a stable way.
        """
        from graspologic.utils import largest_connected_component

        graph = graph.copy()
        graph = cast(nx.Graph, largest_connected_component(graph))
        node_mapping = {
            node: html.unescape(node.upper().strip()) for node in graph.nodes()
        }  # type: ignore
        graph = nx.relabel_nodes(graph, node_mapping)
        return NetworkXStorage._stabilize_graph(graph)

    @staticmethod
    def _stabilize_graph(graph: nx.Graph) -> nx.Graph:
        """Refer to https://github.com/microsoft/graphrag/index/graph/utils/stable_lcc.py
        Ensure an undirected graph with the same relationships will always be read the same way.
        通过对节点和边进行排序来实现
        """
        fixed_graph = nx.DiGraph() if graph.is_directed() else nx.Graph()

        sorted_nodes = graph.nodes(data=True)
        sorted_nodes = sorted(sorted_nodes, key=lambda x: x[0])

        fixed_graph.add_nodes_from(sorted_nodes)
        edges = list(graph.edges(data=True))

        if not graph.is_directed():

            def _sort_source_target(edge):
                source, target, edge_data = edge
                if source > target:
                    source, target = target, source
                return source, target, edge_data

            edges = [_sort_source_target(edge) for edge in edges]

        def _get_edge_key(source: Any, target: Any) -> str:
            return f"{source} -> {target}"

        edges = sorted(edges, key=lambda x: _get_edge_key(x[0], x[1]))

        fixed_graph.add_edges_from(edges)
        return fixed_graph

    def __post_init__(self):
        """
        如果图文件存在，则加载图文件，否则创建一个新的空图
        """
        self._graphml_xml_file = os.path.join(
            self.working_dir, f"{self.namespace}.graphml"
        )
        preloaded_graph = NetworkXStorage.load_nx_graph(self._graphml_xml_file)
        if preloaded_graph is not None:
            logger.info(
                "Loaded graph from %s with %d nodes, %d edges",
                self._graphml_xml_file,
                preloaded_graph.number_of_nodes(),
                preloaded_graph.number_of_edges(),
            )
        self._graph = preloaded_graph or nx.Graph()

    async def index_done_callback(self):
        NetworkXStorage.write_nx_graph(self._graph, self._graphml_xml_file)

    async def has_node(self, node_id: str) -> bool:
        return self._graph.has_node(node_id)

    async def has_edge(self, source_node_id: str, target_node_id: str) -> bool:
        return self._graph.has_edge(source_node_id, target_node_id)

    async def get_node(self, node_id: str) -> Union[dict, None]:
        return self._graph.nodes.get(node_id)

    async def get_all_nodes(self) -> Union[list[tuple[str, dict]], None]:
        return list(self._graph.nodes(data=True))

    async def node_degree(self, node_id: str) -> int:
        return self._graph.degree(node_id)

    async def edge_degree(self, src_id: str, tgt_id: str) -> int:
        return self._graph.degree(src_id) + self._graph.degree(tgt_id)

    async def get_edge(
        self, source_node_id: str, target_node_id: str
    ) -> Union[dict, None]:
        return self._graph.edges.get((source_node_id, target_node_id))

    async def get_all_edges(self) -> Union[list[tuple[str, str, dict]], None]:
        return list(self._graph.edges(data=True))

    async def get_node_edges(
        self, source_node_id: str
    ) -> Union[list[tuple[str, str]], None]:
        if self._graph.has_node(source_node_id):
            return list(self._graph.edges(source_node_id, data=True))
        return None

    async def get_graph(self) -> nx.Graph:
        return self._graph

    async def upsert_node(self, node_id: str, node_data: dict[str, str]):
        self._graph.add_node(node_id, **node_data)

    async def update_node(self, node_id: str, node_data: dict[str, str]):
        if self._graph.has_node(node_id):
            self._graph.nodes[node_id].update(node_data)
        else:
            logger.warning("Node %s not found in the graph for update.", node_id)

    async def upsert_edge(
        self, source_node_id: str, target_node_id: str, edge_data: dict[str, str]
    ):
        self._graph.add_edge(source_node_id, target_node_id, **edge_data)

    async def update_edge(
        self, source_node_id: str, target_node_id: str, edge_data: dict[str, str]
    ):
        if self._graph.has_edge(source_node_id, target_node_id):
            self._graph.edges[(source_node_id, target_node_id)].update(edge_data)
        else:
            logger.warning(
                "Edge %s -> %s not found in the graph for update.",
                source_node_id,
                target_node_id,
            )

    async def delete_node(self, node_id: str):
        """
        Delete a node from the graph based on the specified node_id.

        :param node_id: The node_id to delete
        """
        if self._graph.has_node(node_id):
            self._graph.remove_node(node_id)
            logger.info("Node %s deleted from the graph.", node_id)
        else:
            logger.warning("Node %s not found in the graph for deletion.", node_id)

    async def clear(self):
        """
        Clear the graph by removing all nodes and edges.
        """
        self._graph.clear()
        logger.info("Graph %s cleared.", self.namespace)


class Neo4jImporter:
    def __init__(self, uri: str, user: str, password: str, batch_size: int = 1000):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        self.batch_size = batch_size

    async def close(self):
        await self.driver.close()

    async def import_nx_graph(self, graph: nx.Graph, node_label: str = "Node", edge_label: str = "REL"):
        """导入NetworkX图到Neo4j"""
        await self._import_nodes_batch(graph, node_label)
        await self._import_edges_batch(graph, node_label, edge_label)

    async def _import_nodes_batch(self, graph: nx.Graph, node_label: str):
        """批量导入节点"""
        nodes = list(graph.nodes(data=True))

        for i in range(0, len(nodes), self.batch_size):
            batch = nodes[i:i + self.batch_size]
            query = f"""
            UNWIND $batch AS node
            MERGE (n:{node_label} {{id: node.id}})
            SET n += node.props
            """

            params = {
                "batch": [
                    {"id": node_id, "props": props or {}}
                    for node_id, props in batch
                ]
            }

            await self._execute_query(query, params)
            print(f"导入节点进度: {min(i + self.batch_size, len(nodes))}/{len(nodes)}")

    async def _execute_query(self, query: str, params: Dict[str, Any]):
        """执行Cypher查询"""
        async with self.driver.session() as session:
            try:
                await session.run(query, **params)
            except Neo4jError as e:
                print(f"Neo4j错误: {e}")
                raise

    async def clear_database(self):
        """清空数据库（可选）"""
        query = "MATCH (n) DETACH DELETE n"
        async with self.driver.session() as session:
            await session.run(query)
        print("数据库已清空")

    async def _import_edges_batch(self, graph: nx.Graph, node_label: str, edge_label: str):
        """批量导入关系"""
        edges = list(graph.edges(data=True))

        for i in range(0, len(edges), self.batch_size):
            batch = edges[i:i + self.batch_size]
            query = f"""
            UNWIND $batch AS edge
            MATCH (a:{node_label} {{id: edge.u}})
            MATCH (b:{node_label} {{id: edge.v}})
            MERGE (a)-[r:{edge_label}]->(b)
            SET r += edge.props
            """

            params = {
                "batch": [
                    {"u": u, "v": v, "props": data or {}}
                    for u, v, data in batch
                ]
            }

            await self._execute_query(query, params)
            print(f"导入边进度: {min(i + self.batch_size, len(edges))}/{len(edges)}")

    async def create_constraints(self, node_label: str = "Node"):
        """创建约束和索引（提升性能）"""
        queries = [
            f"CREATE CONSTRAINT {node_label.lower()}_id IF NOT EXISTS FOR (n:{node_label}) REQUIRE n.id IS UNIQUE",
            f"CREATE INDEX {node_label.lower()}_id_index IF NOT EXISTS FOR (n:{node_label}) ON (n.id)"
        ]

        async with self.driver.session() as session:
            for query in queries:
                try:
                    await session.run(query)
                except Neo4jError as e:
                    print(f"创建约束/索引时出错: {e}")

neo4j_importer = Neo4jImporter(
    uri=settings.graph_store.neo4j.uri,
    user=settings.graph_store.neo4j.username,
    password=settings.graph_store.neo4j.password
)