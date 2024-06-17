from parser.json_mc_parser import parse_json_mc
from neo4j_ingester import MCIngester

def main():
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "rootroot"

    mc_ingester = MCIngester(uri, user, password)

    # model_card = parse_json_mc("../examples/model_cards/foundational_uci.json")
    model_card = parse_json_mc("../examples/model_cards/uci_cnn_mc.json")
    mc_ingester.add_mc(model_card)


if __name__ == "__main__":
    main()