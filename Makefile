.PHONY: up down

# Bring up services
up:
	docker-compose up -d

	docker cp server/kg_config/constraints.cypher patra_neo4j_server:/constraints.cypher
	docker exec -it patra_neo4j_server cypher-shell -u neo4j -p PWD_HERE -f /constraints.cypher

# Bring down services
down:
	docker-compose down