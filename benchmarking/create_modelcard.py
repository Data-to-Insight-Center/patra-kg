#!/usr/bin/env python3
"""
Script to create 1 model card with 1 experiment node in Neo4j database
Based on the MegaDetector model card structure provided
"""

import os
import logging
import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from neo4j import GraphDatabase
import uuid

# Environment variables
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://149.165.175.102:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PWD = os.getenv("NEO4J_PWD", "PWD_HERE")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Neo4j driver
try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PWD))
    logger.info("Successfully connected to the Neo4j database.")
except Exception as e:
    logger.error(f"Error connecting to the Neo4j database: {str(e)}")
    raise

# Data templates and variations
EXPERIMENT_STATUSES = [
    "planned", "ongoing", "completed", "cancelled", "failed", "paused"
]

DEPLOYMENT_ENVIRONMENTS = [
    "forest", "savanna", "desert", "urban", "coastal", "mountain", 
    "arctic", "tropical", "suburban", "industrial"
]

DEVICE_TYPES = [
    "camera_trap", "smartphone", "drone", "satellite", "edge_device",
    "iot_sensor", "server", "cloud_instance", "mobile_device", "embedded_system"
]

def generate_random_date(start_date: datetime, end_date: datetime) -> str:
    """Generate a random datetime string between start and end dates."""
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    random_date = start_date + timedelta(days=random_days)
    return random_date.isoformat() + "+00:00"

def create_base_model_card(session) -> Dict[str, Any]:
    """Create the base model card (using the provided MegaDetector data)."""

    # Generate unique ID for this run
    unique_id = str(uuid.uuid4())[:8]

    # Use the provided MegaDetector data as the base model card with unique IDs
    model_card_data = {
        "input_data": "https://github.com/microsoft/CameraTraps/tree/main/data/sample_images",
        "short_description": "Wildlife detection using MegaDetector from Microsoft.",
        "full_description": "MegaDetector is a machine learning model designed to detect animals in images collected from camera traps. It is developed by Microsoft and is widely used in wildlife conservation efforts.",
        "keywords": "wildlife, camera traps, object detection, microsoft, conservation",
        "author": "jstubbs",
        "foundational_model": "None",
        "name": f"MegaDetector for Wildlife Detection {unique_id}",
        "input_type": "images",
        "external_id": f"megadetector-mc-{unique_id}",
        "category": "classification",
        "output_data": "https://github.com/ICICLE-ai/camera_traps/blob/main/models",
        "version": "5a",
    }

    # Create ModelCard node (always create new one)
    model_card_query = """
    CREATE (mc:ModelCard {
        external_id: $external_id,
        name: $name,
        version: $version,
        short_description: $short_description,
        full_description: $full_description,
        keywords: $keywords,
        author: $author,
        foundational_model: $foundational_model,
        input_type: $input_type,
        category: $category,
        input_data: $input_data,
        output_data: $output_data
    })
    """
    
    session.run(model_card_query, **model_card_data)
    logger.info(f"Created ModelCard with external_id: {model_card_data['external_id']}")

    # Create AI Model node with unique ID
    ai_model_data = {
        "owner": "Microsoft AI for Earth",
        "batch_size": 8,
        "input_shape": "(3, 800, 800)",
        "precision": 0.9,
        "model_type": "convolutional neural network",
        "model_structure": "Faster R-CNN",
        "test_accuracy": 0.85,
        "description": "A convolutional neural network model for detecting animals in camera trap images.",
        "model_id": f"megadetector-mc-model-{unique_id}",
        "version": "5a",
        "license": "MIT License",
        "framework": "PyTorch",
        "recall": 0.8,
        "name": f"MegaDetector {unique_id}",
        "backbone": "ResNet-50",
        "location": "https://github.com/ICICLE-ai/camera_traps/raw/main/models/md_v5a.0.0.pt",
        "learning_rate": 0.001
    }

    # Create Model node (always create new one)
    model_query = """
    CREATE (m:Model {
        model_id: $model_id,
        name: $name,
        version: $version,
        owner: $owner,
        batch_size: $batch_size,
        input_shape: $input_shape,
        precision: $precision,
        model_type: $model_type,
        model_structure: $model_structure,
        test_accuracy: $test_accuracy,
        description: $description,
        license: $license,
        framework: $framework,
        recall: $recall,
        backbone: $backbone,
        location: $location,
        learning_rate: $learning_rate
    })
    """

    session.run(model_query, **ai_model_data)
    logger.info(f"Created Model with model_id: {ai_model_data['model_id']}")
    
    # Create relationship between ModelCard and Model
    relationship_query = """
    MATCH (mc:ModelCard {external_id: $external_id})
    MATCH (m:Model {model_id: $model_id})
    CREATE (mc)-[:aiModel]->(m)
    """

    session.run(relationship_query, external_id=model_card_data["external_id"], model_id=ai_model_data["model_id"])
    
    # Create Bias Analysis node with unique ID
    bias_analysis_data = {
        "name": f"megadetector-mc-bias_analysis-{unique_id}",
        "external_id": f"megadetector-mc-bias-{unique_id}",
        "description": "Comprehensive bias analysis for MegaDetector model across different species and environments",
        "methodology": "Statistical parity analysis and equalized odds testing",
        "bias_metrics": "demographic_parity, equal_opportunity, disparate_impact",
        "fairness_score": 0.87,
        "demographic_parity": 0.92,
        "equal_opportunity": 0.85,
        "disparate_impact_ratio": 0.89,
        "analysis_date": datetime.now().isoformat() + "+00:00",
        "analyzed_groups": "species_type, environment_type, lighting_conditions",
        "mitigation_strategies": "Balanced dataset augmentation, threshold adjustment"
    }

    # Create Bias Analysis node (always create new one)
    bias_query = """
    CREATE (ba:`Bias Analysis` {
        external_id: $external_id,
        name: $name,
        description: $description,
        methodology: $methodology,
        bias_metrics: $bias_metrics,
        fairness_score: $fairness_score,
        demographic_parity: $demographic_parity,
        equal_opportunity: $equal_opportunity,
        disparate_impact_ratio: $disparate_impact_ratio,
        analysis_date: datetime($analysis_date),
        analyzed_groups: $analyzed_groups,
        mitigation_strategies: $mitigation_strategies
    })
    """

    session.run(bias_query, **bias_analysis_data)
    logger.info(f"Created Bias Analysis with external_id: {bias_analysis_data['external_id']}")
    
    # Create XAI Analysis node with unique ID
    xai_analysis_data = {
        "name": f"megadetector-mc-xai_analysis-{unique_id}",
        "external_id": f"megadetector-mc-xai-{unique_id}",
        "description": "Explainability analysis using gradient-based attribution methods",
        "methodology": "GradCAM, SHAP values, and feature importance analysis",
        "explanation_type": "visual_attribution, feature_attribution",
        "interpretability_score": 0.78,
        "analysis_date": datetime.now().isoformat() + "+00:00",
        "key_features": "object_boundaries, texture_patterns, environmental_context",
        "visualization_methods": "heatmaps, saliency_maps, attention_maps",
        "confidence_threshold": 0.75,
        "tools_used": "GradCAM, SHAP, LIME"
    }

    # Create XAI Analysis node (always create new one)
    xai_query = """
    CREATE (xai:`Explainability Analysis` {
        external_id: $external_id,
        name: $name,
        description: $description,
        methodology: $methodology,
        explanation_type: $explanation_type,
        interpretability_score: $interpretability_score,
        analysis_date: datetime($analysis_date),
        key_features: $key_features,
        visualization_methods: $visualization_methods,
        confidence_threshold: $confidence_threshold,
        tools_used: $tools_used
    })
    """

    session.run(xai_query, **xai_analysis_data)
    logger.info(f"Created XAI Analysis with external_id: {xai_analysis_data['external_id']}")
    # Create relationship between ModelCard and Bias Analysis
    bias_relationship_query = """
    MATCH (mc:ModelCard {external_id: $external_id})
    MATCH (ba:`Bias Analysis` {external_id: $bias_external_id})
    CREATE (mc)-[:BIAS_ANALYSIS]->(ba)
    """

    session.run(bias_relationship_query,
               external_id=model_card_data["external_id"],
               bias_external_id=bias_analysis_data["external_id"])

    # Create relationship between ModelCard and XAI Analysis
    xai_relationship_query = """
    MATCH (mc:ModelCard {external_id: $external_id})
    MATCH (xai:`Explainability Analysis` {external_id: $xai_external_id})
    CREATE (mc)-[:XAI_ANALYSIS]->(xai)
    """

    session.run(xai_relationship_query,
               external_id=model_card_data["external_id"],
               xai_external_id=xai_analysis_data["external_id"])
    
    return model_card_data, ai_model_data

def create_experiment_nodes(session, ai_model_data: Dict[str, Any], author_username: str, 
                           num_experiments: int = 1000, num_deployments: int = 10000, num_devices: int = 100) -> None:
    """Create experiment nodes with associated deployments/devices and tie each Experiment to the User."""
    
    logger.info(f"Creating {num_devices} devices, {num_experiments} experiments, and {num_deployments} deployments...")
    
    # Step 1: Create 100 devices first (these will be reused)
    device_ids = []
    logger.info(f"Creating {num_devices} devices...")
    for i in range(num_devices):
        device_unique_id = str(uuid.uuid4())[:8]
        device_data = {
            "device_id": f"device_{device_unique_id}",
            "name": f"Wildlife Camera {i}",
            "description": f"{random.choice(DEVICE_TYPES).replace('_', ' ').title()} device for wildlife monitoring",
            "device_type": random.choice(DEVICE_TYPES),
            "weather_resistance": random.choice(["IP67", "IP65", "IP68", "IP54"]),
            "power_consumption": random.randint(3, 15),
            "battery_life": random.randint(24, 72),
            "temperature_range": f"-{random.randint(10, 40)} to {random.randint(40, 80)}°C",
            "location": f"Forest_{random.randint(1, 50)}"
        }
        
        device_query = """
        CREATE (dev:Device {
            device_id: $device_id,
            name: $name,
            description: $description,
            device_type: $device_type,
            weather_resistance: $weather_resistance,
            power_consumption: $power_consumption,
            battery_life: $battery_life,
            temperature_range: $temperature_range,
            location: $location
        })
        """
        session.run(device_query, **device_data)
        device_ids.append(device_data["device_id"])
        
        if (i + 1) % 10 == 0:
            logger.info(f"Created {i + 1} devices...")
    
    # Step 2: Create 1,000 experiments
    experiment_ids = []
    logger.info(f"Creating {num_experiments} experiments...")
    
    # Ensure User exists
    user_query = """
    MERGE (u:User {username: $username})
    ON CREATE SET
        u.email = $email,
        u.full_name = $full_name,
        u.organization = $organization,
        u.role = $role,
        u.created_at = datetime($created_at)
    RETURN u.username as username
    """
    user_data = {
        "username": author_username,
        "email": f"{author_username}@conservation.org",
        "full_name": "Joe Stubbs",
        "organization": "ICICLE AI Institute",
        "role": "Research Scientist",
        "created_at": datetime.now().isoformat() + "+00:00"
    }
    session.run(user_query, user_data)
    
    for i in range(num_experiments):
        exp_unique_id = str(uuid.uuid4())[:8]
        start_date = datetime.now() - timedelta(days=random.randint(30, 365))
        end_date = start_date + timedelta(days=random.randint(1, 30))
        
        experiment_data = {
            "experiment_id": f"exp_{exp_unique_id}",
            "name": f"Wildlife Detection Experiment {i}",
            "description": f"Experiment to test MegaDetector performance in different environments",
            "results": f"Experiment {i} results: accuracy improved by {random.randint(0, 10)}%",
            "status": random.choice(EXPERIMENT_STATUSES),
            "start_date": generate_random_date(start_date, end_date),
            "end_date": generate_random_date(start_date, end_date)
        }
        
        experiment_query = """
        CREATE (exp:Experiment {
            experiment_id: $experiment_id,
            name: $name,
            description: $description,
            results: $results,
            status: $status,
            start_date: datetime($start_date),
            end_date: datetime($end_date)
        })
        """
        session.run(experiment_query, **experiment_data)
        experiment_ids.append(experiment_data["experiment_id"])
        
        # Link experiment to user
        exp_user_rel_query = """
        MATCH (exp:Experiment {experiment_id: $experiment_id})
        MATCH (u:User {username: $username})
        CREATE (exp)-[:submittedBy]->(u)
        """
        session.run(exp_user_rel_query, {"experiment_id": experiment_data["experiment_id"], "username": author_username})
        
        if (i + 1) % 100 == 0:
            logger.info(f"Created {i + 1} experiments...")
    
    # Step 3: Create 10,000 deployments
    # Distribute: 10 deployments per experiment, 100 deployments per device
    deployments_per_experiment = num_deployments // num_experiments  # 10
    logger.info(f"Creating {num_deployments} deployments ({deployments_per_experiment} per experiment)...")
    
    for i in range(num_deployments):
        deployment_unique_id = str(uuid.uuid4())[:8]
        
        # Assign to experiment (round-robin: 10 per experiment)
        experiment_idx = i // deployments_per_experiment
        experiment_id = experiment_ids[experiment_idx % len(experiment_ids)]
        
        # Assign to device (round-robin: 100 per device)
        device_id = device_ids[i % len(device_ids)]
        
        start_date = datetime.now() - timedelta(days=random.randint(30, 365))
        end_date = start_date + timedelta(days=random.randint(1, 30))
        
        deployment_data = {
            "deployment_id": f"deployment_{deployment_unique_id}",
            "name": f"MegaDetector Deployment {i}",
            "deployment_location": f"Location_{random.randint(1, 100)}",
            "deployment_environment": random.choice(DEPLOYMENT_ENVIRONMENTS),
            "requests_served": random.randint(1000, 10000),
            "cpu_consumption_average_percentage": random.randint(10, 50),
            "cpu_consumption_peak_percentage": random.randint(40, 90),
            "gpu_consumption_peak_percentage": random.randint(60, 95),
            "gpu_consumption_average_percentage": random.randint(20, 60),
            "power_consumption_peak_watts": random.randint(5, 20),
            "power_consumption_average_watts": round(random.uniform(2.0, 8.0), 1),
            "mean_latency_ms": random.randint(30, 200),
            "mean_accuracy": round(random.uniform(0.75, 0.99), 2),
            "start_time": generate_random_date(start_date, end_date),
            "end_time": generate_random_date(start_date, end_date),
            "duration_minutes": random.randint(1440, 43200)
        }
        
        deployment_query = """
        CREATE (d:Deployment {
            deployment_id: $deployment_id,
            name: $name,
            deployment_location: $deployment_location,
            deployment_environment: $deployment_environment,
            requests_served: $requests_served,
            cpu_consumption_average_percentage: $cpu_consumption_average_percentage,
            cpu_consumption_peak_percentage: $cpu_consumption_peak_percentage,
            gpu_consumption_peak_percentage: $gpu_consumption_peak_percentage,
            gpu_consumption_average_percentage: $gpu_consumption_average_percentage,
            power_consumption_peak_watts: $power_consumption_peak_watts,
            power_consumption_average_watts: $power_consumption_average_watts,
            mean_latency_ms: $mean_latency_ms,
            mean_accuracy: $mean_accuracy,
            start_time: datetime($start_time),
            end_time: datetime($end_time),
            duration_minutes: $duration_minutes
        })
        """
        session.run(deployment_query, **deployment_data)
        
        # Create relationships: Model -> Deployment -> Device, Deployment -> Experiment
        relationships_query = """
        MATCH (m:Model {model_id: $model_id})
        MATCH (d:Deployment {deployment_id: $deployment_id})
        MATCH (dev:Device {device_id: $device_id})
        MATCH (exp:Experiment {experiment_id: $experiment_id})
        CREATE (m)-[:hasDeployment]->(d)
        CREATE (d)-[:deployedIn]->(dev)
        CREATE (d)-[:deploymentInfo]->(exp)
        """
        
        session.run(relationships_query, 
                   model_id=ai_model_data["model_id"],
                   deployment_id=deployment_data["deployment_id"],
                   device_id=device_id,
                   experiment_id=experiment_id)
        
        if (i + 1) % 1000 == 0:
            logger.info(f"Created {i + 1} deployments...")
    
    logger.info(f"Successfully created {num_devices} devices, {num_experiments} experiments, and {num_deployments} deployments!")

def cleanup_duplicate_modelcards(session) -> None:
    """Remove duplicate ModelCard nodes, keeping only the first one."""
    
    logger.info("Checking for duplicate ModelCard nodes...")
    
    # Find all ModelCard nodes
    find_query = """
    MATCH (mc:ModelCard)
    RETURN mc.external_id as external_id, collect(mc) as cards
    """
    
    result = session.run(find_query)
    records = list(result)
    
    duplicates_found = False
    for record in records:
        external_id = record["external_id"]
        cards = record["cards"]
        
        if len(cards) > 1:
            duplicates_found = True
            logger.info(f"Found {len(cards)} duplicate ModelCard nodes with external_id: {external_id}")
            
            # Keep the first card, delete the rest
            cards_to_delete = cards[1:]  # All except the first one
            
            for card in cards_to_delete:
                # Get the node ID for deletion
                delete_query = """
                MATCH (mc:ModelCard)
                WHERE id(mc) = $node_id
                DETACH DELETE mc
                """
                session.run(delete_query, node_id=card.id)
                logger.info(f"Deleted duplicate ModelCard node with ID: {card.id}")
    
    if not duplicates_found:
        logger.info("No duplicate ModelCard nodes found.")

def verify_database_access(session):
    """Verify database access and permissions."""
    try:
        # Test basic read access
        result = session.run("MATCH (n) RETURN count(n) as node_count LIMIT 1")
        node_count = result.single()["node_count"]
        logger.info(f"Database contains {node_count} nodes")
        
        # Test write access by creating a test node
        test_query = "CREATE (t:TestNode {id: 'test_connection'}) RETURN t.id as test_id"
        result = session.run(test_query)
        test_id = result.single()["test_id"]
        logger.info(f"Write test successful: {test_id}")
        
        # Clean up test node
        session.run("MATCH (t:TestNode {id: 'test_connection'}) DELETE t")
        logger.info("Database access verified successfully")
        
    except Exception as e:
        logger.error(f"Database access verification failed: {str(e)}")
        raise

def create_fulltext_index(session) -> None:
    """Create fulltext index for model cards."""
    try:
        index_query = """
        CREATE FULLTEXT INDEX mcFullIndex IF NOT EXISTS
        FOR (n:ModelCard) ON EACH [n.name, n.short_description, n.full_description, n.keywords]
        """
        session.run(index_query)
        logger.info("Created fulltext index for ModelCard nodes")
    except Exception as e:
        logger.warning(f"Could not create fulltext index: {e}")

def main():
    """Main function to create 1 model card with 1000 experiments, 10000 deployments, and 100 devices."""
    
    logger.info("Starting creation of 1 model card with 1000 experiments, 10000 deployments, and 100 devices...")
    
    try:
        with driver.session() as session:
            # Verify database access first
            verify_database_access(session)
            
            # Clean up any existing duplicate ModelCards
            cleanup_duplicate_modelcards(session)
            
            # Create fulltext index (skip if unauthorized)
            try:
                create_fulltext_index(session)
            except Exception as e:
                logger.warning(f"Skipping fulltext index creation: {e}")
            
            # Create the base model card
            logger.info("Creating base model card...")
            model_card_data, ai_model_data = create_base_model_card(session)
            
            # Create 1000 experiments, 10000 deployments, and 100 devices
            create_experiment_nodes(session, ai_model_data, model_card_data["author"], 
                                  num_experiments=1000, num_deployments=10000, num_devices=100)
            
            logger.info("Successfully created model card with experiments, deployments, and devices!")
            
            # Verify creation
            count_queries = [
                ("ModelCard", "MATCH (mc:ModelCard) RETURN count(mc) as count"),
                ("Model", "MATCH (m:Model) RETURN count(m) as count"),
                ("Deployment", "MATCH (d:Deployment) RETURN count(d) as count"),
                ("Device", "MATCH (dev:Device) RETURN count(dev) as count"),
                ("Experiment", "MATCH (exp:Experiment) RETURN count(exp) as count"),
                ("User", "MATCH (u:User) RETURN count(u) as count")
            ]
            
            for node_type, query in count_queries:
                result = session.run(query)
                count = result.single()["count"]
                logger.info(f"Total {node_type} nodes in database: {count}")
            
    except Exception as e:
        logger.error(f"Error creating model card and experiments: {str(e)}")
        raise
    finally:
        driver.close()
        logger.info("Database connection closed.")

if __name__ == "__main__":
    main()