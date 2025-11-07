import os
import logging
from neo4j import AsyncGraphDatabase
from typing import Dict, Optional, Any, List

# Environment variables
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PWD = os.getenv("NEO4J_PWD", "password")

# Initialize Neo4j async driver
try:
    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PWD))
    logging.info("Successfully connected to the Neo4j database.")
except Exception as e:
    logging.error(f"Error connecting to the Neo4j database: {str(e)}")
    raise

async def get_base_model_card(session, model_card_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the base model card from the knowledge graph."""
    query = 'MATCH (mc:ModelCard {external_id: $mc_id}) RETURN mc'
    result = await session.run(query, mc_id=model_card_id)
    record = await result.single()

    if not record:
        return None

    model_card = dict(record['mc'])

    # Remove embedding if present
    if 'embedding' in model_card:
        del model_card['embedding']

    return model_card

async def get_ai_model(session, model_card_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve the AI model associated with the model card."""
    ai_query = 'MATCH (ai:Model {model_id: $ai_model_id}) RETURN ai'
    ai_result = await session.run(ai_query, ai_model_id=f"{model_card_id}-model")
    ai_record = await ai_result.single()

    if ai_record:
        return dict(ai_record['ai'])
    return None

async def get_bias_analysis(session, model_card_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve bias analysis for the model card."""
    bias_query = 'MATCH (ba:`Bias Analysis` {external_id: $bias_id}) RETURN ba'
    bias_result = await session.run(bias_query, bias_id=f"{model_card_id}-bias")
    bias_record = await bias_result.single()

    if bias_record:
        return dict(bias_record['ba'])
    return None

async def get_xai_analysis(session, model_card_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve explainability analysis for the model card."""
    xai_query = 'MATCH (xai:`Explainability Analysis` {external_id: $xai_id}) RETURN xai'
    xai_result = await session.run(xai_query, xai_id=f"{model_card_id}-xai")
    xai_record = await xai_result.single()

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

async def get_deployments(session, model_card_id: str) -> List[Dict[str, Any]]:
    """Retrieve deployment information for the model card."""
    deployment_query = """
        MATCH (mc:ModelCard {external_id: $mc_id})-[:aiModel]->(m:Model)-[:hasDeployment]->(d:Deployment)
        OPTIONAL MATCH (d)-[:deployedIn]->(ed:Device)
        OPTIONAL MATCH (d)-[:deploymentInfo]->(exp:Experiment)
        OPTIONAL MATCH (exp)-[:submittedBy]->(u:User)
        RETURN d, ed, exp, u
        ORDER BY d.start_time DESC
    """
    deployment_result = await session.run(deployment_query, mc_id=model_card_id)
    deployments = []

    async for record in deployment_result:
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

async def get_model_card(model_card_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a complete model card from the knowledge graph.

    Args:
        model_card_id: The external ID of the model card to retrieve

    Returns:
        A dictionary containing the complete model card data, or None if not found
    """
    try:
        async with driver.session() as session:
            # Get base model card
            model_card = await get_base_model_card(session, model_card_id)
            if not model_card:
                return None

            # Get AI model
            ai_model = await get_ai_model(session, model_card_id)
            if ai_model:
                model_card["ai_model"] = ai_model

            # Get bias analysis
            bias_analysis = await get_bias_analysis(session, model_card_id)
            if bias_analysis:
                model_card["bias_analysis"] = bias_analysis

            # Get XAI analysis
            xai_analysis = await get_xai_analysis(session, model_card_id)
            if xai_analysis:
                model_card["xai_analysis"] = xai_analysis

            # Get deployment information
            deployments = await get_deployments(session, model_card_id)
            if deployments:
                model_card["deployments"] = deployments

            # Serialize all DateTime objects to strings for JSON compatibility
            model_card = serialize_datetime_objects(model_card)
            return model_card

    except Exception as e:
        logging.error(f"Error retrieving model card {model_card_id}: {str(e)}")
        return None

async def search_model_cards(query: str) -> List[Dict[str, Any]]:
    """
    Search the knowledge graph using full-text search.

    Args:
        query: Search query string

    Returns:
        List of matching model cards
    """
    try:
        async with driver.session() as session:
            search_query = """
                CALL db.index.fulltext.queryNodes("mcFullIndex", $prompt) YIELD node, score
                RETURN node.external_id as mc_id, node.name as name, node.version as version,
                node.short_description as short_description, score as score
                LIMIT 10
            """
            result = await session.run(search_query, prompt=query)
            records = []
            async for record in result:
                records.append(record)

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

async def close_driver():
    """Close the Neo4j driver connection."""
    await driver.close()

# VALID_LINK_CONSTRAINTS mapping
VALID_LINK_CONSTRAINTS = {
    'ModelCard': ['Datasheet', 'ModelRequirements', 'BiasAnalysis', 'ExplainabilityAnalysis', 'Model'],
    'Model': ['Deployment', 'Experiment'],
    'Server': ['Deployment'],
    'Deployment': ['Experiment', 'Device'],
    'Experiment': ['RawImage', 'User', 'Device', 'Model'],
    'Datasheet': ['ModelCard'],
    'ModelRequirements': ['ModelCard'],
    'BiasAnalysis': ['ModelCard'],
    'ExplainabilityAnalysis': ['ModelCard'],
    'User': ['Experiment'],
    'RawImage': ['Experiment'],
    'Device': ['Deployment', 'Experiment']
}

# Mapping from (source_label, target_label) to relationship type
RELATIONSHIP_TYPE_MAP = {
    ('ModelCard', 'Model'): 'USED',
    ('ModelCard', 'Datasheet'): 'TRAINED_ON',
    ('ModelCard', 'ModelRequirements'): 'REQUIREMENTS',
    ('ModelCard', 'BiasAnalysis'): 'BIAS_ANALYSIS',
    ('ModelCard', 'ExplainabilityAnalysis'): 'XAI_ANALYSIS',
    ('Model', 'Deployment'): 'hasDeployment',
    ('Model', 'Experiment'): 'used',
    ('Server', 'Deployment'): 'hosts',
    ('Deployment', 'Experiment'): 'deploymentInfo',
    ('Deployment', 'Device'): 'deployedIn',
    ('Experiment', 'RawImage'): 'processes',
    ('Experiment', 'User'): 'submittedBy',
    ('Experiment', 'Device'): 'executedOn',
    ('Experiment', 'Model'): 'uses',
    ('User', 'Experiment'): 'submits',
    ('RawImage', 'Experiment'): 'processedBy',
    ('Device', 'Deployment'): 'hosts',
    ('Device', 'Experiment'): 'executes',
}

def normalize_label(label: str) -> str:
    """Normalize node label to match constraint keys."""
    # Remove spaces and handle common variations
    label = label.replace(' ', '')
    # Handle specific cases
    if label == 'ModelCard':
        return 'ModelCard'
    elif label == 'DataSheet' or label == 'Datasheet':
        return 'Datasheet'
    elif label == 'BiasAnalysis' or label == 'Bias Analysis':
        return 'BiasAnalysis'
    elif label == 'ExplainabilityAnalysis' or label == 'Explainability Analysis':
        return 'ExplainabilityAnalysis'
    elif label == 'ModelRequirements' or label == 'Model Requirements':
        return 'ModelRequirements'
    elif label == 'RawImage' or label == 'Raw Image':
        return 'RawImage'
    return label

def get_relationship_type(source_label: str, target_label: str) -> Optional[str]:
    """
    Determine the relationship type between two node labels based on constraints.
    
    Args:
        source_label: Label of the source node
        target_label: Label of the target node
        
    Returns:
        Relationship type name, or None if no valid relationship exists
    """
    # Normalize labels
    source_norm = normalize_label(source_label)
    target_norm = normalize_label(target_label)
    
    # Check if relationship is valid according to constraints
    if source_norm not in VALID_LINK_CONSTRAINTS:
        return None
    
    if target_norm not in VALID_LINK_CONSTRAINTS[source_norm]:
        return None
    
    # Get relationship type from map
    rel_type = RELATIONSHIP_TYPE_MAP.get((source_norm, target_norm))
    if rel_type:
        return rel_type
    
    # Default: use uppercase version of target label if no specific mapping
    return target_norm.upper()

async def create_edge(source_node_id: str, target_node_id: str) -> Dict[str, Any]:
    """
    Create an edge between two nodes in the Neo4j graph.
    
    Args:
        source_node_id: Neo4j elementId of the source node
        target_node_id: Neo4j elementId of the target node
        
    Returns:
        Dictionary with success status and relationship type, or error information
    """
    try:
        async with driver.session() as session:
            # First, get the labels of both nodes
            query = """
            MATCH (a), (b)
            WHERE elementId(a) = $source_id AND elementId(b) = $target_id
            RETURN labels(a) as source_labels, labels(b) as target_labels
            """
            result = await session.run(query, source_id=source_node_id, target_id=target_node_id)
            record = await result.single()
            
            if not record:
                return {
                    "success": False,
                    "error": "One or both nodes not found"
                }
            
            source_labels = record["source_labels"]
            target_labels = record["target_labels"]
            
            if not source_labels or not target_labels:
                return {
                    "success": False,
                    "error": "Nodes have no labels"
                }
            
            # Use the first label (nodes typically have one primary label)
            source_label = source_labels[0]
            target_label = target_labels[0]
            
            # Determine relationship type
            relationship_type = get_relationship_type(source_label, target_label)
            
            if not relationship_type:
                return {
                    "success": False,
                    "error": f"No valid relationship type between {source_label} and {target_label}",
                    "source_label": source_label,
                    "target_label": target_label
                }
            
            # Check if edge already exists
            check_query = f"""
            MATCH (a), (b)
            WHERE elementId(a) = $source_id AND elementId(b) = $target_id
            MATCH (a)-[r:{relationship_type}]->(b)
            RETURN r
            LIMIT 1
            """
            check_result = await session.run(check_query, source_id=source_node_id, target_id=target_node_id)
            existing = await check_result.single()
            
            if existing:
                return {
                    "success": True,
                    "message": "Edge already exists",
                    "relationship_type": relationship_type,
                    "source_node_id": source_node_id,
                    "target_node_id": target_node_id
                }
            
            # Create the edge
            create_query = f"""
            MATCH (a), (b)
            WHERE elementId(a) = $source_id AND elementId(b) = $target_id
            CREATE (a)-[r:{relationship_type}]->(b)
            RETURN r, type(r) as rel_type
            """
            create_result = await session.run(create_query, source_id=source_node_id, target_id=target_node_id)
            created = await create_result.single()
            
            if created:
                return {
                    "success": True,
                    "message": "Edge created successfully",
                    "relationship_type": relationship_type,
                    "source_node_id": source_node_id,
                    "target_node_id": target_node_id,
                    "source_label": source_label,
                    "target_label": target_label
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create edge"
                }
                
    except Exception as e:
        logging.error(f"Error creating edge: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
