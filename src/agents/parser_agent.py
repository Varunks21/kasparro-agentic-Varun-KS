"""
Parser Agent - Autonomous Data Extraction Agent
===============================================
An autonomous agent responsible for parsing and structuring 
raw product data into validated models.
"""

import os
import json
from typing import Any, Dict, List, Optional

from src.core.base_agent import BaseAgent, AgentCapability, AgentGoal, AgentState
from src.core.messages import Message, MessageType
from src.models.internal import ProductData
from src.utils.llm_client import get_structured_data
from src.utils.logger import get_agent_logger

logger = get_agent_logger("ParserAgent")


class ParserAgent(BaseAgent):
    """
    Autonomous agent for parsing raw product data.
    
    Capabilities:
    - parse_raw_data: Extract structured product data from JSON or text input
    - validate_data: Validate extracted data against schema
    
    The ParserAgent operates autonomously, receiving goals from
    the orchestrator and making decisions about how to achieve them.
    """
    
    def __init__(self):
        super().__init__(
            agent_id="parser_agent",
            name="Parser Agent",
            description="Autonomous agent for parsing and structuring raw product data",
            capabilities=[
                AgentCapability(
                    name="parse_raw_data",
                    description="Parse JSON or text input into structured ProductData",
                    input_types=["json_file", "text_file", "raw_text"],
                    output_types=["ProductData"]
                ),
                AgentCapability(
                    name="validate_data",
                    description="Validate data against schema requirements",
                    input_types=["ProductData"],
                    output_types=["ValidationResult"]
                )
            ]
        )
        
    def plan(self, goal: AgentGoal) -> Optional[List[Dict[str, Any]]]:
        """
        Create a plan to achieve the parsing goal.
        
        The agent analyzes the goal and determines the best
        approach to parse the data.
        """
        self.logger.info(f"Planning for goal: {goal.description}")
        
        # Analyze what we're being asked to do
        context = goal.context
        plan = []
        
        # Decision: Determine the source of data
        if "file_path" in context:
            file_path = context["file_path"]
            self.memory.record_decision(
                "Read from file",
                f"File path provided: {file_path}"
            )
            plan.append({
                "action": "read_file",
                "params": {"path": file_path}
            })
        elif "raw_text" in context:
            self.memory.record_decision(
                "Use provided text",
                "Raw text provided directly in context"
            )
            plan.append({
                "action": "use_raw_text",
                "params": {"text": context["raw_text"]}
            })
        elif "json_data" in context:
            self.memory.record_decision(
                "Use provided JSON",
                "JSON data provided directly in context"
            )
            plan.append({
                "action": "use_json_data",
                "params": {"data": context["json_data"]}
            })
        else:
            # Default to standard JSON input file
            self.memory.record_decision(
                "Use default input file",
                "No source specified, using default data/raw_input.json"
            )
            plan.append({
                "action": "read_file",
                "params": {"path": "data/raw_input.json"}
            })
            
        # Add parsing step
        plan.append({
            "action": "parse_data",
            "params": {}
        })
        
        # Add validation step
        plan.append({
            "action": "validate_output",
            "params": {}
        })
        
        # Add publication step (share results)
        plan.append({
            "action": "publish_results",
            "params": {"goal_id": goal.id}
        })
        
        self.logger.info(f"Plan created with {len(plan)} steps")
        return plan
        
    def execute(self, plan: List[Dict[str, Any]], goal: AgentGoal) -> bool:
        """
        Execute the parsing plan.
        
        The agent carries out each step, adapting if needed.
        """
        input_data = None  # Can be JSON dict or raw text
        is_json = False
        product_data = None
        
        for step in plan:
            action = step["action"]
            params = step["params"]
            
            self.logger.debug(f"Executing step: {action}")
            
            try:
                if action == "read_file":
                    input_data, is_json = self._read_file(params["path"])
                    if input_data is None:
                        self.memory.record_outcome(action, False, "File not found or empty")
                        return False
                    file_type = "JSON" if is_json else "text"
                    self.memory.record_outcome(action, True, f"Read {file_type} data")
                    
                elif action == "use_raw_text":
                    input_data = params["text"]
                    is_json = False
                    self.memory.record_outcome(action, True)
                    
                elif action == "use_json_data":
                    input_data = params["data"]
                    is_json = True
                    self.memory.record_outcome(action, True)
                    
                elif action == "parse_data":
                    if is_json:
                        product_data = self._parse_json(input_data)
                    else:
                        product_data = self._parse_with_llm(input_data)
                        
                    if not product_data:
                        self.memory.record_outcome(action, False, "Parsing failed")
                        return False
                    self.memory.record_outcome(action, True, f"Parsed: {product_data.name}")
                    
                elif action == "validate_output":
                    is_valid = self._validate_product_data(product_data)
                    if not is_valid:
                        self.memory.record_outcome(action, False, "Validation failed")
                        return False
                    self.memory.record_outcome(action, True)
                    
                elif action == "publish_results":
                    self._publish_results(product_data, params.get("goal_id"))
                    self.memory.record_outcome(action, True)
                    
            except Exception as e:
                self.logger.error(f"Step '{action}' failed: {e}")
                self.memory.record_outcome(action, False, str(e))
                return False
                
        return True
        
    def _read_file(self, file_path: str) -> tuple[Optional[Any], bool]:
        """
        Read data from a file (JSON or text).
        
        Returns:
            tuple: (data, is_json) - data and whether it's JSON
        """
        if not os.path.exists(file_path):
            self.logger.error(f"Input file not found: {file_path}")
            return None, False
            
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Check if it's a JSON file
        is_json = file_path.endswith('.json')
        
        if is_json:
            try:
                data = json.loads(content)
                self.memory.record_observation({
                    "type": "json_file_read",
                    "path": file_path,
                    "keys": list(data.keys()) if isinstance(data, dict) else "array"
                })
                self.logger.info(f"Read JSON file: {file_path}")
                return data, True
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in {file_path}: {e}")
                return None, False
        else:
            self.memory.record_observation({
                "type": "text_file_read",
                "path": file_path,
                "size": len(content),
                "lines": len(content.split('\n'))
            })
            self.logger.info(f"Read text file: {file_path} ({len(content)} characters)")
            return content, False
            
    def _parse_json(self, json_data: Dict[str, Any]) -> Optional[ProductData]:
        """
        Parse JSON data directly into ProductData.
        
        This is more reliable than LLM parsing for structured input.
        """
        self.logger.info("Parsing JSON data directly")
        
        try:
            # Map JSON keys to ProductData fields
            product_data = ProductData(
                name=json_data.get("product_name", ""),
                concentration=json_data.get("concentration"),
                skin_type=json_data.get("skin_type", []),
                key_ingredients=json_data.get("key_ingredients", []),
                benefits=json_data.get("benefits", []),
                usage_instructions=json_data.get("how_to_use", ""),
                side_effects=json_data.get("side_effects"),
                price_inr=float(json_data.get("price_inr", 0))
            )
            
            self.logger.info(f"Parsed JSON successfully: {product_data.name}")
            self.logger.debug(f"  - Price: Rs.{product_data.price_inr}")
            self.logger.debug(f"  - Ingredients: {len(product_data.key_ingredients)} items")
            self.logger.debug(f"  - Benefits: {len(product_data.benefits)} items")
            
            return product_data
            
        except Exception as e:
            self.logger.error(f"Failed to parse JSON: {e}")
            return None
        
    def _parse_with_llm(self, raw_text: str) -> Optional[ProductData]:
        """Use LLM to parse raw text into structured data."""
        
        self.logger.info("Sending text data to LLM for structured extraction")
        
        prompt = f"""
        You are an expert Data Parsing Agent.
        Your job is to extract product details from the raw text provided below.
        
        Rules:
        - Extract exact values where possible.
        - If a value is missing, use reasonable context or leave as null (do not hallucinate).
        - Convert price to a float number (remove currency symbols).
        - 'skin_type' should be a list of strings.
        - 'usage_instructions' should capture the full 'How to Use' text.
        
        Raw Text:
        {raw_text}
        """
        
        try:
            product_data = get_structured_data(prompt, ProductData)
            
            self.logger.info(f"Data parsed successfully: {product_data.name}")
            self.logger.debug(f"  - Price: Rs.{product_data.price_inr}")
            self.logger.debug(f"  - Ingredients: {len(product_data.key_ingredients)} items")
            self.logger.debug(f"  - Benefits: {len(product_data.benefits)} items")
            
            return product_data
            
        except Exception as e:
            self.logger.error(f"Failed to parse data: {e}")
            return None
            
    def _validate_product_data(self, product_data: ProductData) -> bool:
        """Validate the extracted product data."""
        
        # Check required fields
        if not product_data.name:
            self.logger.warning("Validation: Missing product name")
            return False
            
        if not product_data.key_ingredients:
            self.logger.warning("Validation: No ingredients found")
            return False
            
        if product_data.price_inr <= 0:
            self.logger.warning("Validation: Invalid price")
            return False
            
        self.logger.info("Product data validation passed")
        return True
        
    def _publish_results(self, product_data: ProductData, goal_id: str) -> None:
        """Publish parsed results to the blackboard."""
        
        # Post the main product data
        self.post_to_blackboard(
            "product_data",
            product_data,
            tags={"parsed", "product", "source"}
        )
        
        # Also post as the goal result
        self.post_to_blackboard(
            f"result_{goal_id}",
            product_data,
            tags={"result"}
        )
        
        self.logger.info(f"Published product data to blackboard")
        
    def on_message(self, message: Message) -> None:
        """Handle custom messages."""
        self.logger.debug(f"Received message type: {message.type}")
        
    def on_task_request(
        self,
        task_name: str,
        params: Dict[str, Any],
        message: Message
    ) -> None:
        """
        Handle task requests from other agents.
        
        Enables other agents to request parsing services.
        """
        if task_name == "parse_text":
            raw_text = params.get("text")
            if raw_text:
                product_data = self._parse_with_llm(raw_text)
                if product_data:
                    self.send_message(
                        MessageType.DATA_RESPONSE,
                        message.sender,
                        {
                            "task": task_name,
                            "result": product_data.model_dump(),
                            "success": True
                        }
                    )
                    return
                    
        elif task_name == "parse_json":
            json_data = params.get("data")
            if json_data:
                product_data = self._parse_json(json_data)
                if product_data:
                    self.send_message(
                        MessageType.DATA_RESPONSE,
                        message.sender,
                        {
                            "task": task_name,
                            "result": product_data.model_dump(),
                            "success": True
                        }
                    )
                    return
                    
        # Send failure response
        self.send_message(
            MessageType.TASK_FAILED,
            message.sender,
            {
                "task": task_name,
                "reason": "Failed to execute task"
            }
        )


# Backwards compatibility function
def parse_raw_data(file_path: str) -> ProductData:
    """
    Legacy function for backwards compatibility.
    Creates a temporary agent to parse data.
    """
    agent = ParserAgent()
    
    # Read file
    input_data, is_json = agent._read_file(file_path)
    if input_data is None:
        raise FileNotFoundError(f"Input file not found at: {file_path}")
    
    # Parse based on file type
    if is_json:
        product_data = agent._parse_json(input_data)
    else:
        product_data = agent._parse_with_llm(input_data)
        
    if not product_data:
        raise ValueError("Failed to parse product data")
        
    return product_data
