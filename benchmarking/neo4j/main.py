import csv
import time
import statistics
from neo4j import GraphDatabase

class Neo4jBenchmark:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def get_modelcard(self):
        query = """
        MATCH (mc:ModelCard {external_id: $mc_id})
        OPTIONAL MATCH (mc)-[:USED]->(ai:Model)
        OPTIONAL MATCH (mc)-[:BIAS_ANALYSIS]->(ba:BiasAnalysis)
        OPTIONAL MATCH (mc)-[:XAI_ANALYSIS]->(xai:ExplainabilityAnalysis)
        RETURN mc, ai, ba, xai
        """
        
        params = {"mc_id": "3f7b2c82-75fa-4335-a3b8-e1930893a974"}
        latencies = []
        
        # Benchmark runs
        for i in range(1000):
            with self.driver.session() as session:
                start = time.perf_counter()
                result = session.run(query, params)
                # print("--------------------------------")
                # print(result.data())
                # print("--------------------------------")
                result.consume()
                latency = (time.perf_counter() - start)
                latencies.append(latency)
        
        # Write to CSV
        with open('get_modelcard.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            for latency in latencies:
                writer.writerow([latency])

    def get_all_modelcards(self, limit=10000):
        query = """
            MATCH (mc:ModelCard)
            RETURN mc.external_id as mc_id, mc.name as name, mc.version as version, 
            mc.short_description as short_description
            LIMIT $limit
        """

        latencies = []

        for i in range(1000):
            with self.driver.session() as session:
                start = time.perf_counter()
                result = session.run(query, limit=limit)
                # print("--------------------------------")
                # print(result.data())
                # print("--------------------------------")
                result.consume()
                latency = (time.perf_counter() - start)
                latencies.append(latency)
        
        # Write to CSV after all benchmark runs
        with open('list_modelcards.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            for latency in latencies:
                writer.writerow([latency])
                
    def search_modelcards(self, query_str, max_nodes=10):
        cypher_query = """
            CALL db.index.fulltext.queryNodes("mcFullIndex", $prompt) YIELD node, score
            RETURN node.external_id as mc_id, node.name as name, node.version as version, 
                   node.short_description as short_description, score as score
            LIMIT $num_nodes
        """
        latencies = []
        params = {"prompt": query_str, "num_nodes": max_nodes}

        for i in range(1000):
            with self.driver.session() as session:
                start = time.perf_counter()
                result = session.run(cypher_query, params)
                # print("--------------------------------")
                # print(result.data())
                # print("--------------------------------")
                result.consume()
                latency = (time.perf_counter() - start)
                latencies.append(latency)

        with open('search_modelcards.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            for latency in latencies:
                writer.writerow([latency])
    
    def run_benchmark(self):
        return self.run_benchmark_get_modelcard()
    
    def run_benchmark_all_modelcards(self):
        return self.get_all_modelcards()
    
    def run_benchmark_search_modelcards(self):
        return self.search_modelcards("machine learning model")

    def run_benchmark_get_modelcard(self):
        return self.get_modelcard()

benchmark = Neo4jBenchmark("bolt://localhost:7687", "neo4j", "PWD_HERE")
benchmark.run_benchmark_get_modelcard()
benchmark.run_benchmark_all_modelcards()
benchmark.run_benchmark_search_modelcards()
benchmark.close()
