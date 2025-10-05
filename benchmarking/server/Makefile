.PHONY: up constraints down logs health

NEO4J_CONTAINER=patra-backend-neo4j
NEO4J_USER=neo4j
NEO4J_PWD?=password
CONSTRAINTS_FILE=constraints.cypher

up:
	docker-compose up -d
	$(MAKE) constraints

constraints:
	@echo "Waiting for Neo4j to become healthy..."
	@until [ "`docker inspect -f '{{.State.Health.Status}}' $(NEO4J_CONTAINER) 2>/dev/null`" = "healthy" ]; do \
		echo "neo4j is starting..."; \
		sleep 5; \
	done
	@echo "Applying constraints from $(CONSTRAINTS_FILE)"
	docker cp $(CONSTRAINTS_FILE) $(NEO4J_CONTAINER):/constraints.cypher
	docker exec $(NEO4J_CONTAINER) cypher-shell -u $(NEO4J_USER) -p $(NEO4J_PWD) -f /constraints.cypher

health:
	docker inspect -f '{{.State.Health.Status}}' $(NEO4J_CONTAINER)

logs:
	docker-compose logs -f

down:
	docker-compose down -v

