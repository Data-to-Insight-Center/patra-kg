.PHONY: kg down

# Check Neo4j health
check-neo4j-server:
	@while ! docker exec neo4j_server cypher-shell -u neo4j -p PWD_HERE "RETURN 1" > /dev/null 2>&1; do \
		echo "neo4j-server starting..."; \
		sleep 5; \
	done

# Bring up services
kg:
	docker-compose -f patra_kg/docker-compose.yml up -d

	# Check if neo4j-server has started and then add constraints
	$(MAKE) check-neo4j-server
	docker cp patra_kg/constraints.cypher neo4j_server:/constraints.cypher
	docker exec -it neo4j_server cypher-shell -u neo4j -p PWD_HERE -f /constraints.cypher

	export NEO4J_URI=bolt://neo4j:7687
	export NEO4J_USER=neo4j
	export NEO4J_PWD=PWD_HERE

# Bring down services
down:
	docker-compose -f patra_kg/docker-compose.yml down