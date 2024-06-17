from neo4j import GraphDatabase
import time


uri = "bolt://localhost:7689"
username = "neo4j"
password = "rootroot"

queries_location = "/Users/swithana/git/ai-model-cards/llm/evaluation/queries_bucketed.txt"


driver = GraphDatabase.driver(uri, auth=(username, password))

def execute_query(driver, query):
    with driver.session() as session:
        result = session.run(query)
        return result

def measure_query_time(driver, query, num_runs=10):
    total_time = 0.0

    for _ in range(num_runs):
        start_time = time.time()
        execute_query(driver, query)
        end_time = time.time()

        query_time = end_time - start_time
        total_time += query_time

    average_time = total_time / num_runs
    return average_time

def get_queries_from_file(filename, query_indices):
    with open(filename, 'r') as file:
        queries = file.readlines()

    selected_queries = [queries[i].strip() for i in query_indices]
    return selected_queries


if __name__ == "__main__":
    basic_lookup = [0, 1, 2, 8, 9, 12]
    similarity = [14, 15]
    deployment = [3, 4, 5, 6, 7, 10, 11, 13, 16, 17, 18, 19]
    aggregated = [8, 9]
    query_indices = deployment
    queries = get_queries_from_file(queries_location, query_indices)

    total_time = 0
    for index, query in enumerate(queries):
        print(query)
        avg_time = measure_query_time(driver, query)
        query_time = avg_time
        total_time += query_time
        print(f"Average query execution time for query {query_indices[index] + 1} over 10 runs: {avg_time:.4f} seconds")

    print(f"Average query execution time: {total_time/len(queries):.4f} seconds")

    driver.close()