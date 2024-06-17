from parser.json_mc_parser import parse_json_mc
from neo4j_ingester import MCIngester

def main():
    uri = "bolt://localhost:7689"
    user = "neo4j"
    password = "rootroot"

    # uri = "bolt+s://a3433c07.databases.neo4j.io:7687"
    # user = "neo4j"
    # password = "FI3rVpZwsEmekGGX4HJkWV6aOpe_pSvkj7CvciN2DY4"

    mc_ingester = MCIngester(uri, user, password)

    datasheet = parse_json_mc("../examples/datasheets/uci_adult_datasheet.json")

    mc_ingester.add_datasheet(datasheet)

if __name__ == "__main__":
    main()