import os
import logging
from neo4j import GraphDatabase
from typing import Dict, Optional, Any, List

# Environment variables
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PWD = os.getenv("NEO4J_PWD", "password")

# Initialize Neo4j driver
try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PWD))
    logging.info("Successfully connected to the Neo4j database.")
except Exception as e:
    logging.error(f"Error connecting to the Neo4j database: {str(e)}")
    raise

def get_base_model_card(session, model_card_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the base model card from the knowledge graph."""
    query = 'MATCH (mc:ModelCard {external_id: $mc_id}) RETURN mc'
    result = session.run(query, mc_id=model_card_id)
    record = result.single()
    
    if not record:
        return None
        
    model_card = dict(record['mc'])
    
    # Remove embedding if present
    if 'embedding' in model_card:
        del model_card['embedding']
    
    return model_card

def get_ai_model(session, model_card_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the AI model associated with the model card."""
    ai_query = 'MATCH (ai:Model {model_id: $ai_model_id}) RETURN ai'
    ai_result = session.run(ai_query, ai_model_id=f"{model_card_id}-model")
    ai_record = ai_result.single()
    
    if ai_record:
        return dict(ai_record['ai'])
    return None

def get_bias_analysis(session, model_card_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve bias analysis for the model card."""
    bias_query = 'MATCH (ba:`Bias Analysis` {external_id: $bias_id}) RETURN ba'
    bias_result = session.run(bias_query, bias_id=f"{model_card_id}-bias")
    bias_record = bias_result.single()
    
    if bias_record:
        return dict(bias_record['ba'])
    return None

def get_xai_analysis(session, model_card_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve explainability analysis for the model card."""
    xai_query = 'MATCH (xai:`Explainability Analysis` {external_id: $xai_id}) RETURN xai'
    xai_result = session.run(xai_query, xai_id=f"{model_card_id}-xai")
    xai_record = xai_result.single()
    
    if xai_record:
        return dict(xai_record['xai'])
    return None

def convert_datetime_to_string(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert datetime objects to strings in the given dictionary."""
    if 'start_time' in data and data['start_time']:
        data['start_time'] = str(data['start_time'])
    if 'end_time' in data and data['end_time']:
        data['end_time'] = str(data['end_time'])
    return data

def serialize_datetime_objects(obj):
    """Recursively convert Neo4j DateTime objects to strings in any data structure."""
    from neo4j.time import DateTime
    
    if isinstance(obj, DateTime):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: serialize_datetime_objects(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime_objects(item) for item in obj]
    else:
        return obj

def get_deployments(session, model_card_id: str) -> List[Dict[str, Any]]:
    """Retrieve deployment information for the model card."""
    deployment_query = """
        MATCH (mc:ModelCard {external_id: $mc_id})-[:aiModel]->(m:Model)-[:hasDeployment]->(d:Deployment)
        OPTIONAL MATCH (d)-[:deployedIn]->(ed:Device)
        OPTIONAL MATCH (d)-[:deploymentInfo]->(exp:Experiment)
        OPTIONAL MATCH (exp)-[:submittedBy]->(u:User)
        RETURN d, ed, exp, u
        ORDER BY d.start_time DESC
    """
    deployment_result = session.run(deployment_query, mc_id=model_card_id)
    deployments = []
    
    for record in deployment_result:
        deployment_info = dict(record['d']) if record['d'] else {}
        device_info = dict(record['ed']) if record['ed'] else {}
        experiment_info = dict(record['exp']) if record['exp'] else {}
        user_info = dict(record['u']) if record['u'] else {}
        
        # Convert datetime objects to strings
        deployment_info = convert_datetime_to_string(deployment_info)
        
        deployment_data = {
            "deployment": deployment_info,
            "device": device_info,
            "experiment": experiment_info,
            "user": user_info
        }
        deployments.append(deployment_data)
    
    return deployments

def get_model_card(model_card_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a complete model card from the knowledge graph.
    
    Args:
        model_card_id: The external ID of the model card to retrieve
        
    Returns:
        A dictionary containing the complete model card data, or None if not found
    """
    try:
        with driver.session() as session:
            # Get base model card
            model_card = get_base_model_card(session, model_card_id)
            if not model_card:
                return None
            
            # Get AI model
            ai_model = get_ai_model(session, model_card_id)
            if ai_model:
                model_card["ai_model"] = ai_model
            
            # Get bias analysis
            bias_analysis = get_bias_analysis(session, model_card_id)
            if bias_analysis:
                model_card["bias_analysis"] = bias_analysis
            
            # Get XAI analysis
            xai_analysis = get_xai_analysis(session, model_card_id)
            if xai_analysis:
                model_card["xai_analysis"] = xai_analysis
            
            # Get deployment information
            deployments = get_deployments(session, model_card_id)
            if deployments:
                model_card["deployments"] = deployments
            
            # Serialize all DateTime objects to strings for JSON compatibility
            model_card = serialize_datetime_objects(model_card)            
            return model_card
            
    except Exception as e:
        logging.error(f"Error retrieving model card {model_card_id}: {str(e)}")
        return None

def search_model_cards(query: str) -> List[Dict[str, Any]]:
    """
    Search the knowledge graph using full-text search.
    
    Args:
        query: Search query string
        
    Returns:
        List of matching model cards
    """
    try:
        with driver.session() as session:
            search_query = """        
                CALL db.index.fulltext.queryNodes("mcFullIndex", $prompt) YIELD node, score
                RETURN node.external_id as mc_id, node.name as name, node.version as version, 
                node.short_description as short_description, score as score
                LIMIT 10
            """
            result = session.run(search_query, prompt=query)
            records = list(result)
            
            return [
                {
                    "mc_id": r["mc_id"],
                    "name": r["name"],
                    "version": r["version"],
                    "short_description": r["short_description"],
                    "score": r["score"]
                }
                for r in records
            ]
            
    except Exception as e:
        logging.error(f"Error searching with query '{query}': {str(e)}")
        return []

def close_driver():
    """Close the Neo4j driver connection."""
    driver.close()
