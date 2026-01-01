"""
Parser Agent - Autonomous Data Extraction Agent
===============================================
An autonomous agent responsible for parsing and structuring 
raw product data into validated models.
"""

import os
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
    - parse_raw_data: Extract structured product data from raw text
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
                    description="Parse raw text input into structured ProductData",
                    input_types=["raw_text", "file_path"],
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
            self.memory.record_decision(
                "Read from file",
                f"File path provided: {context['file_path']}"
            )
            plan.append({
                "action": "read_file",
                "params": {"path": context["file_path"]}
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
        else:
            # Default to standard input file
            self.memory.record_decision(
                "Use default input file",
                "No source specified, using default data/raw_input.txt"
            )
            plan.append({
                "action": "read_file",
                "params": {"path": "data/raw_input.txt"}
            })
            
        # Add parsing step
        plan.append({
            "action": "parse_with_llm",
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
        raw_text = None
        product_data = None
        
        for step in plan:
            action = step["action"]
            params = step["params"]
            
            self.logger.debug(f"Executing step: {action}")
            
            try:
                if action == "read_file":
                    raw_text = self._read_file(params["path"])
                    if not raw_text:
                        self.memory.record_outcome(action, False, "File not found or empty")
                        return False
                    self.memory.record_outcome(action, True, f"Read {len(raw_text)} characters")
                    
                elif action == "use_raw_text":
                    raw_text = params["text"]
                    self.memory.record_outcome(action, True)
                    
                elif action == "parse_with_llm":
                    product_data = self._parse_with_llm(raw_text)
                    if not product_data:
                        self.memory.record_outcome(action, False, "LLM parsing failed")
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
        
    def _read_file(self, file_path: str) -> Optional[str]:
        """Read raw text from a file."""
        if not os.path.exists(file_path):
            self.logger.error(f"Input file not found: {file_path}")
            return None
            
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
            
        self.memory.record_observation({
            "type": "file_read",
            "path": file_path,
            "size": len(raw_text),
            "lines": len(raw_text.split('\n'))
        })
        
        self.logger.info(f"Read {len(raw_text)} characters from {file_path}")
        return raw_text
        
    def _parse_with_llm(self, raw_text: str) -> Optional[ProductData]:
        """Use LLM to parse raw text into structured data."""
        
        self.logger.info("Sending data to LLM for structured extraction")
        
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
            
            self.logger.info(f"✓ Data parsed successfully: {product_data.name}")
            self.logger.debug(f"  - Price: ₹{product_data.price_inr}")
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
            
        self.logger.info("✓ Product data validation passed")
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
                    # Send response back
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
    raw_text = agent._read_file(file_path)
    if not raw_text:
        raise FileNotFoundError(f"Input file not found at: {file_path}")
        
    # Parse
    product_data = agent._parse_with_llm(raw_text)
    if not product_data:
        raise ValueError("Failed to parse product data")
        
    return product_data
