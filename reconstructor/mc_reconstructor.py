from ingester.database import GraphDB
import time
import csv
import os
from datetime import datetime
from typing import Dict, Optional, Any, List, Tuple
import logging


class MCReconstructor:
    """
    Re-constructs model cards from the Knowledge Graph.
    
    This class provides functionality to retrieve and reconstruct complete model cards
    from a Neo4j knowledge graph, including associated AI models, bias analysis,
    and explainability analysis.
    """

    def __init__(self, uri: str, user: str, password: str, 
                 csv_output_file: str = "reconstruct_timings.csv") -> None:
        """
        Initialize the MCReconstructor with Neo4j connection parameters.
        
        Args:
            uri: Neo4j database URI
            user: Database username
            password: Database password
            csv_output_file: Path to CSV file for timing data
        """
        self.csv_output_file = csv_output_file

        try:
            self.db = GraphDB(uri, user, password)
            logging.info("Successfully connected to the Neo4j database.")
        except Exception as e:
            logging.error(f"Error connecting to the Neo4j database: {str(e)}")
            raise
        
        self._initialize_csv()

    def reconstruct(self, model_card_id: str) -> Optional[Dict[str, Any]]:
        """
        Reconstruct a complete model card from the knowledge graph.
        
        Args:
            model_card_id: The external ID of the model card to reconstruct
            
        Returns:
            A dictionary containing the complete model card data, or None if not found
        """
        base_mc, time_base = self._retrieve_base_model_card(model_card_id)
        if base_mc is None:
            return None

        self._clean_model_card(base_mc)
        time_ai = self._attach_ai_model(base_mc, model_card_id)
        time_bias = self._attach_bias_analysis(base_mc, model_card_id)
        time_xai = self._attach_xai_analysis(base_mc, model_card_id)

        total_time = time_base + time_ai + time_bias + time_xai
        self._write_timing_to_csv(model_card_id, time_base, time_ai, time_bias, time_xai, total_time)
        
        logging.debug(f"Reconstruct time: {total_time:.2f}ms "
                     f"[base:{time_base:.2f} ai:{time_ai:.2f} bias:{time_bias:.2f} xai:{time_xai:.2f}]")

        return base_mc
    
    def _initialize_csv(self) -> None:
        """Initialize the CSV file with headers if it doesn't exist."""
        try:
            csv_dir = os.path.dirname(self.csv_output_file)
            if csv_dir and not os.path.exists(csv_dir):
                os.makedirs(csv_dir, exist_ok=True)
            
            if not os.path.exists(self.csv_output_file):
                with open(self.csv_output_file, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([
                        'timestamp', 'model_card_id', 'base_query_ms',
                        'ai_model_query_ms', 'bias_analysis_query_ms',
                        'xai_analysis_query_ms', 'total_ms'
                    ])
        except (PermissionError, OSError) as e:
            logging.warning(f"Cannot initialize CSV file {self.csv_output_file}: {e}")
            self.csv_output_file = None
    
    def _write_timing_to_csv(self, model_card_id: str, time_base: float, time_ai: float,
                             time_bias: float, time_xai: float, total_time: float) -> None:
        """
        Write timing data to CSV file.
        
        Args:
            model_card_id: The model card ID
            time_base: Base query execution time in ms
            time_ai: AI model query execution time in ms
            time_bias: Bias analysis query execution time in ms
            time_xai: XAI analysis query execution time in ms
            total_time: Total execution time in ms
        """
        self._write_csv_row(self.csv_output_file, [
            datetime.now().isoformat(),
            model_card_id,
            time_base, time_ai, time_bias, time_xai, total_time
        ])
    
    def _write_csv_row(self, csv_file: str, values: List[Any]) -> None:
        """Write a row to CSV file with float formatting."""
        if csv_file is None:
            return
            
        try:
            with open(csv_file, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                formatted_values = [f"{v:.2f}" if isinstance(v, float) else v for v in values]
                writer.writerow(formatted_values)
        except (PermissionError, OSError) as e:
            logging.warning(f"Cannot write to CSV file {csv_file}: {e}")

    def _query_and_time(self, query: str, result_key: str, metadata: Dict[str, str], 
                        log_message: str) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Execute a timed query and return result with execution time.
        
        Args:
            query: Cypher query to execute
            result_key: Key to extract from query result
            metadata: Query parameters
            log_message: Debug log message for timing
            
        Returns:
            Tuple of (result_dict, execution_time_ms)
        """
        start_time = time.perf_counter()
        result = self.get_result_dict(query, result_key, metadata)
        elapsed_time = (time.perf_counter() - start_time) * 1000
        logging.debug(f"{log_message}: {elapsed_time:.2f} ms")
        return result, elapsed_time

    def _retrieve_base_model_card(self, model_card_id: str) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Retrieve the base model card from the knowledge graph.
        
        Args:
            model_card_id: The external ID of the model card
            
        Returns:
            Tuple of (model_card_dict, execution_time_ms)
        """
        query = 'MATCH (mc:ModelCard {external_id: $mc_id}) RETURN mc'
        base_mc, elapsed_time = self._query_and_time(
            query, "mc", {"mc_id": model_card_id}, "Base model card query"
        )

        if base_mc is None:
            logging.warning(f"Model card '{model_card_id}' not found in knowledge graph")
        
        return base_mc, elapsed_time

    def _clean_model_card(self, model_card: Dict[str, Any]) -> None:
        """
        Remove unnecessary data from the model card (e.g., embeddings).
        
        Args:
            model_card: The model card dictionary to clean
        """
        if 'embedding' in model_card:
            del model_card["embedding"]

    def _attach_ai_model(self, model_card: Dict[str, Any], model_card_id: str) -> float:
        """
        Retrieve and attach AI model information to the model card.
        
        Args:
            model_card: The model card dictionary to update
            model_card_id: The model card ID for constructing the AI model ID
            
        Returns:
            Execution time in milliseconds
        """
        query = 'MATCH (ai:Model {model_id: $ai_model_id}) RETURN ai'
        ai_model, elapsed_time = self._query_and_time(
            query, "ai", {"ai_model_id": f"{model_card_id}-model"}, "AI model query"
        )
        model_card["ai_model"] = ai_model
        return elapsed_time

    def _attach_bias_analysis(self, model_card: Dict[str, Any], model_card_id: str) -> float:
        """
        Retrieve and attach bias analysis information to the model card if available.
        
        Args:
            model_card: The model card dictionary to update
            model_card_id: The model card ID for constructing the bias analysis ID
            
        Returns:
            Execution time in milliseconds
        """
        query = 'MATCH (ba:BiasAnalysis {external_id: $bias_id}) RETURN ba'
        bias_analysis, elapsed_time = self._query_and_time(
            query, "ba", {"bias_id": f"{model_card_id}-bias"}, "Bias analysis query"
        )
        if bias_analysis is not None:
            model_card["bias_analysis"] = bias_analysis
        return elapsed_time

    def _attach_xai_analysis(self, model_card: Dict[str, Any], model_card_id: str) -> float:
        """
        Retrieve and attach explainability analysis information to the model card if available.
        
        Args:
            model_card: The model card dictionary to update
            model_card_id: The model card ID for constructing the XAI analysis ID
            
        Returns:
            Execution time in milliseconds
        """
        query = 'MATCH (xai:ExplainabilityAnalysis {external_id: $xai_id}) RETURN xai'
        xai_analysis, elapsed_time = self._query_and_time(
            query, "xai", {"xai_id": f"{model_card_id}-xai"}, "Explainability analysis query"
        )
        if xai_analysis is not None:
            model_card["xai_analysis"] = xai_analysis
        return elapsed_time

    def get_result_dict(self, query: str, result_type: str, metadata: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Execute a Cypher query and extract the result as a dictionary."""
        response = self.db.get_result_query(query, metadata)
        if response is None:
            return None

        node = response[result_type]
        if node is None:
            return None

        return {key: node[key] for key in node.keys()}

    def search_kg(self, query: str) -> List[Dict[str, Any]]:
        """Search the knowledge graph using full-text search."""
        results = self.db.full_text_search(query)
        return [
            {
                "mc_id": r["mc_id"],
                "name": r["name"],
                "version": r["version"],
                "short_description": r["short_description"],
                "score": r["score"]
            }
            for r in results
        ]

    def get_all_mcs(self) -> List[Dict[str, Any]]:
        """Retrieve all model cards from the knowledge graph."""
        model_cards = self.db.get_all_modelcards()
        return [
            {
                "mc_id": r["mc_id"],
                "name": r["name"],
                "version": r["version"],
                "short_description": r["short_description"]
            }
            for r in model_cards
        ]

    def get_model_location(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the download location for a specific model."""
        model_info = self.db.get_model_location(model_id)
        if model_info is None:
            logging.warning(f"Model location not found for model ID: {model_id}")
            return None
            
        return {
            "model_id": model_info["model_id"],
            "name": model_info["name"],
            "version": model_info["version"],
            "download_url": model_info["download_url"]
        }

    def get_deployments(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve deployment information for a specific model."""
        deployment_info = self.db.get_deployments(model_id)
        if deployment_info is None:
            logging.warning(f"No deployments found for model ID: {model_id}")
            return None
        return deployment_info

    def set_model_location(self, model_id: str, location: str) -> None:
        """Update the download location for a specific model."""
        self.db.set_model_location(model_id, location)
        logging.info(f"Updated model location for {model_id}")


    def get_link_headers(self, model_card: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate HTTP Link and Content-Length headers based on model card data.
        
        Creates HTTP Link headers for related resources like author, input data,
        model location, and inference labels based on the model card content.

        Args:
            model_card: The model card data dictionary
            
        Returns:
            A dictionary containing 'Link' and 'Content-Length' headers
        """
        links = []

        # Extract basic model card information
        model_card_id: str = model_card.get('external_id')
        author: str = model_card.get('author')
        input_data_url: str = model_card.get('input_data')

        # Extract AI model information
        ai_model_dict: Dict[str, Any] = model_card.get('ai_model', {})
        model_location_url: Optional[str] = ai_model_dict.get('location')
        inference_labels_url: Optional[str] = ai_model_dict.get('inference_labels')

        # Build citation link
        if model_card_id:
            links.append(f'<{model_card_id}>; rel="cite-as"')

        # Build author link
        if author and isinstance(author, str):
            if author.startswith(('http://', 'https://')):
                links.append(f'<{author}>; rel="author"')
            else:
                links.append(f'<http://tapis.com/{author}>; rel="author"')

        # Build input data link
        if (input_data_url and isinstance(input_data_url, str) and 
            input_data_url.startswith(('http://', 'https://'))):
            links.append(f'<{input_data_url}>; rel="item"; title="input_data"')

        # Build model location link
        if (model_location_url and isinstance(model_location_url, str) and 
            model_location_url.startswith(('http://', 'https://'))):
            links.append(f'<{model_location_url}>; rel="item"; title="model_location"')

        # Build inference labels link
        if (inference_labels_url and isinstance(inference_labels_url, str) and 
            inference_labels_url.startswith(('http://', 'https://'))):
            links.append(f'<{inference_labels_url}>; rel="item"; title="inference_labels"')

        # Assemble headers
        headers = {}
        if links:
            headers['Link'] = ", ".join(links)

        # Set Content-Length for empty body response
        headers['Content-Length'] = '0'

        return headers
