.PHONY: up down

# Check Neo4j health
check-neo4j-server:
	@while ! docker exec patra_neo4j_server cypher-shell -u neo4j -p PWD_HERE "RETURN 1" > /dev/null 2>&1; do \
		echo "neo4j-server starting..."; \
		sleep 5; \
	done

# Bring up services
up:
	docker-compose up -d

	$(MAKE) check-neo4j-server
	docker cp server/kg_config/constraints.cypher patra_neo4j_server:/constraints.cypher
	docker exec -it patra_neo4j_server cypher-shell -u neo4j -p PWD_HERE -f /constraints.cypher

# Bring down services
down:
	docker-compose down
