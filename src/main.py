"""
Kasparro AI Content Engine - Multi-Agent System
================================================
A true multi-agent system with autonomous agents coordinated
by a dynamic orchestrator.

Architecture:
- Orchestrator: Manages agent lifecycle and task coordination
- ParserAgent: Autonomous data extraction and structuring
- StrategyAgent: Autonomous strategic planning and analysis
- BuilderAgent: Autonomous content assembly

Agents communicate via messages and share data through a blackboard,
enabling dynamic coordination rather than hardcoded sequential flow.
"""

import os
import json
from datetime import datetime

# Core multi-agent framework
from src.core.orchestrator import Orchestrator, Task, WorkflowDefinition, TaskStatus
from src.core.messages import MessageType

# Autonomous agents
from src.agents.parser_agent import ParserAgent
from src.agents.strategy_agent import StrategyAgent
from src.agents.builder_agent import BuilderAgent

# Logging
from src.utils.logger import (
    main_logger,
    log_pipeline_start,
    log_pipeline_complete,
    log_file_saved,
    log_agent_thought
)


def save_json(filename: str, pydantic_obj):
    """Save a Pydantic object to JSON file."""
    path = os.path.join("output", filename)
    os.makedirs("output", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(pydantic_obj.model_dump_json(indent=2))
    log_file_saved(path)


def run_multi_agent_system():
    """
    Run the content generation using a true multi-agent architecture.
    
    This demonstrates:
    1. Agent registration with the orchestrator
    2. Dynamic task assignment based on capabilities
    3. Dependency-aware workflow execution
    4. Inter-agent communication via message bus
    5. Shared state via blackboard
    """
    
    log_pipeline_start()
    main_logger.info("Initializing Multi-Agent System...")
    
    # =========================================
    # 1. Initialize the Orchestrator
    # =========================================
    orchestrator = Orchestrator()
    main_logger.info("Orchestrator initialized")
    
    # =========================================
    # 2. Create and Register Autonomous Agents
    # =========================================
    parser_agent = ParserAgent()
    strategy_agent = StrategyAgent()
    builder_agent = BuilderAgent()
    
    orchestrator.register_agent(parser_agent)
    orchestrator.register_agent(strategy_agent)
    orchestrator.register_agent(builder_agent)
    
    main_logger.info(f"Registered {len(orchestrator.registry.get_all_agents())} agents")
    main_logger.info(f"Available capabilities: {orchestrator.registry.get_capabilities()}")
    
    # =========================================
    # 3. Define the Content Generation Workflow
    # =========================================
    # Tasks are defined with their required capabilities
    # The orchestrator will dynamically assign them to capable agents
    
    parse_task = Task(
        id="task_parse",
        name="Parse Product Data",
        description="Extract and structure product data from raw input",
        required_capability="parse_raw_data",
        priority=1,  # Highest priority - must run first
        context={
            "file_path": "data/raw_input.txt"
        }
    )
    
    competitor_task = Task(
        id="task_competitor",
        name="Generate Competitor",
        description="Create fictional competitor for comparison",
        required_capability="generate_competitor",
        priority=2,
        dependencies=["task_parse"]  # Depends on parsing
    )
    
    faq_task = Task(
        id="task_faqs",
        name="Generate FAQ Questions",
        description="Generate FAQ questions from product data",
        required_capability="generate_faqs",
        priority=2,
        dependencies=["task_parse"]  # Depends on parsing
    )
    
    build_product_task = Task(
        id="task_build_product",
        name="Build Product Page",
        description="Assemble the product page",
        required_capability="build_product_page",
        priority=3,
        dependencies=["task_parse"]  # Only needs product data
    )
    
    build_faq_task = Task(
        id="task_build_faq",
        name="Build FAQ Page",
        description="Assemble the FAQ page with answers",
        required_capability="build_faq_page",
        priority=3,
        dependencies=["task_parse", "task_faqs"]  # Needs product + questions
    )
    
    build_comparison_task = Task(
        id="task_build_comparison",
        name="Build Comparison Page",
        description="Assemble the comparison page",
        required_capability="build_comparison_page",
        priority=3,
        dependencies=["task_parse", "task_competitor"]  # Needs product + competitor
    )
    
    # Create workflow definition
    workflow = WorkflowDefinition(
        id="content_generation_workflow",
        name="Content Generation Pipeline",
        description="Generate product page, FAQ, and comparison content",
        tasks=[
            parse_task,
            competitor_task,
            faq_task,
            build_product_task,
            build_faq_task,
            build_comparison_task
        ]
    )
    
    main_logger.info(f"Workflow defined: {workflow.name}")
    main_logger.info(f"  Tasks: {len(workflow.tasks)}")
    
    # =========================================
    # 4. Execute Workflow with Dynamic Coordination
    # =========================================
    log_agent_thought("Orchestrator", "Starting workflow execution")
    
    # Track completion
    workflow_complete = False
    failed_tasks = []
    
    def on_workflow_complete(wf, failed):
        nonlocal workflow_complete, failed_tasks
        workflow_complete = True
        failed_tasks = failed
        main_logger.info("Workflow completion callback triggered")
    
    # Submit workflow to orchestrator
    orchestrator.submit_workflow(workflow, on_complete=on_workflow_complete)
    
    # The orchestrator handles task assignment and coordination
    # We can monitor progress
    main_logger.info("\n" + "="*60)
    main_logger.info("WORKFLOW EXECUTION STATUS")
    main_logger.info("="*60)
    
    status = orchestrator.get_system_status()
    for agent_info in status["agents"]:
        main_logger.info(f"  Agent: {agent_info['name']}")
        main_logger.info(f"    - State: {agent_info['state']}")
        main_logger.info(f"    - Capabilities: {agent_info['capabilities']}")
    
    # =========================================
    # 5. Retrieve Results and Save Outputs
    # =========================================
    main_logger.info("\n" + "="*60)
    main_logger.info("RETRIEVING RESULTS FROM BLACKBOARD")
    main_logger.info("="*60)
    
    # Get results from the shared blackboard
    blackboard = orchestrator.blackboard
    
    # Product Page
    product_page = blackboard.get("product_page")
    if product_page:
        save_json("product_page.json", product_page)
        main_logger.info("✓ Product page saved")
    else:
        main_logger.warning("Product page not found on blackboard")
        
    # FAQ Page
    faq_page = blackboard.get("faq_page")
    if faq_page:
        save_json("faq.json", faq_page)
        main_logger.info("✓ FAQ page saved")
    else:
        main_logger.warning("FAQ page not found on blackboard")
        
    # Comparison Page
    comparison_page = blackboard.get("comparison_page")
    if comparison_page:
        save_json("comparison_page.json", comparison_page)
        main_logger.info("✓ Comparison page saved")
    else:
        main_logger.warning("Comparison page not found on blackboard")
    
    # =========================================
    # 6. Display Agent Memory (Decision Trail)
    # =========================================
    main_logger.info("\n" + "="*60)
    main_logger.info("AGENT DECISION TRAILS")
    main_logger.info("="*60)
    
    for agent in [parser_agent, strategy_agent, builder_agent]:
        main_logger.info(f"\n{agent.name} Decisions:")
        for decision in agent.memory.decisions[-3:]:  # Last 3 decisions
            main_logger.info(f"  - {decision.get('decision', 'N/A')}")
            main_logger.info(f"      Reasoning: {decision.get('reasoning', 'N/A')}")
    
    # =========================================
    # Complete
    # =========================================
    log_pipeline_complete()
    
    return {
        "success": len(failed_tasks) == 0,
        "product_page": product_page,
        "faq_page": faq_page,
        "comparison_page": comparison_page
    }


def main():
    """
    Main entry point.
    
    Runs the multi-agent content generation system.
    """
    try:
        results = run_multi_agent_system()
        
        if results["success"]:
            main_logger.info("\n✓ All content generated successfully!")
        else:
            main_logger.warning("\n⚠ Some tasks failed during execution")
            
    except Exception as e:
        main_logger.error(f"\n✗ Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()
