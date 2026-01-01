"""
Dynamic Orchestrator for Multi-Agent Coordination
================================================
Provides intelligent coordination of autonomous agents,
managing task distribution, dependency resolution, and workflow execution.
"""

from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Type
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import logging

from .base_agent import BaseAgent, AgentCapability, AgentGoal, AgentState
from .messages import Message, MessageBus, MessageType
from .blackboard import Blackboard

logger = logging.getLogger("kasparro.orchestrator")


class TaskStatus(Enum):
    """Status of a task in the orchestrator."""
    
    PENDING = auto()        # Waiting to be assigned
    ASSIGNED = auto()       # Assigned to an agent
    IN_PROGRESS = auto()    # Being executed
    COMPLETED = auto()      # Successfully completed
    FAILED = auto()         # Failed execution
    BLOCKED = auto()        # Waiting on dependencies


class Task(BaseModel):
    """A task to be executed by an agent."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    required_capability: str
    priority: int = Field(default=5, ge=1, le=10)
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)  # Task IDs
    context: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Any] = None
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = False


class WorkflowDefinition(BaseModel):
    """Defines a workflow as a set of tasks with dependencies."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    tasks: List[Task]
    
    
class AgentRegistry:
    """
    Registry of available agents and their capabilities.
    
    Enables dynamic agent discovery and capability-based routing.
    """
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._capability_index: Dict[str, Set[str]] = {}  # capability -> agent_ids
        
    def register(self, agent: BaseAgent) -> None:
        """Register an agent with the registry."""
        self._agents[agent.agent_id] = agent
        
        # Index capabilities
        for capability in agent.capabilities:
            if capability.name not in self._capability_index:
                self._capability_index[capability.name] = set()
            self._capability_index[capability.name].add(agent.agent_id)
            
        logger.info(f"Registered agent: {agent.name} ({agent.agent_id})")
        
    def unregister(self, agent_id: str) -> None:
        """Unregister an agent from the registry."""
        if agent_id in self._agents:
            agent = self._agents[agent_id]
            
            # Remove from capability index
            for capability in agent.capabilities:
                if capability.name in self._capability_index:
                    self._capability_index[capability.name].discard(agent_id)
                    
            del self._agents[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")
            
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID."""
        return self._agents.get(agent_id)
        
    def find_agents_by_capability(self, capability: str) -> List[BaseAgent]:
        """Find all agents with a specific capability."""
        agent_ids = self._capability_index.get(capability, set())
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]
        
    def find_best_agent_for_task(self, task: Task) -> Optional[BaseAgent]:
        """
        Find the best available agent for a task.
        
        Selection criteria:
        1. Has required capability
        2. Currently in IDLE state
        3. Lowest current workload
        """
        candidates = self.find_agents_by_capability(task.required_capability)
        
        # Filter to idle agents
        idle_agents = [a for a in candidates if a.state == AgentState.IDLE]
        
        if not idle_agents:
            # Fall back to any agent with capability
            return candidates[0] if candidates else None
            
        # Return first idle agent (could add more sophisticated selection)
        return idle_agents[0]
        
    def get_all_agents(self) -> List[BaseAgent]:
        """Get all registered agents."""
        return list(self._agents.values())
        
    def get_capabilities(self) -> List[str]:
        """Get all available capabilities across agents."""
        return list(self._capability_index.keys())


class Orchestrator:
    """
    Dynamic orchestrator for multi-agent coordination.
    
    The orchestrator is responsible for:
    1. Managing the agent lifecycle
    2. Dynamic task assignment based on capabilities
    3. Dependency resolution and task ordering
    4. Monitoring agent progress and handling failures
    5. Coordinating inter-agent collaboration
    
    Unlike hardcoded sequential pipelines, the orchestrator
    enables true dynamic coordination of autonomous agents.
    """
    
    def __init__(self):
        self.agent_id = "orchestrator"
        self.registry = AgentRegistry()
        self.message_bus = MessageBus()
        self.blackboard = Blackboard()
        
        # Task management
        self._task_queue: List[Task] = []
        self._active_tasks: Dict[str, Task] = {}
        self._completed_tasks: Dict[str, Task] = {}
        
        # Workflow tracking
        self._current_workflow: Optional[WorkflowDefinition] = None
        self._workflow_complete_callback: Optional[callable] = None
        
        # Subscribe to messages
        self.message_bus.subscribe(self.agent_id, self._handle_message)
        self.message_bus.subscribe_broadcast(self._handle_broadcast)
        
        logger.info("Orchestrator initialized")
        
    def register_agent(self, agent: BaseAgent) -> None:
        """
        Register an agent with the orchestrator.
        
        The agent is connected to the message bus and blackboard,
        enabling it to participate in the multi-agent system.
        """
        self.registry.register(agent)
        agent.connect(self.message_bus, self.blackboard)
        
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the orchestrator."""
        agent = self.registry.get_agent(agent_id)
        if agent:
            agent.disconnect()
            self.registry.unregister(agent_id)
            
    def _handle_message(self, message: Message) -> None:
        """Handle messages directed to the orchestrator."""
        if message.type == MessageType.GOAL_COMPLETE:
            self._handle_goal_complete(message)
        elif message.type == MessageType.TASK_FAILED:
            self._handle_task_failed(message)
        elif message.type == MessageType.STATUS_UPDATE:
            self._handle_status_update(message)
            
    def _handle_broadcast(self, message: Message) -> None:
        """Handle broadcast messages."""
        if message.type == MessageType.NEED_ASSISTANCE:
            self._handle_assistance_request(message)
            
    def _handle_goal_complete(self, message: Message) -> None:
        """Handle goal completion reports from agents."""
        goal_id = message.content.get("goal_id")
        success = message.content.get("success", False)
        agent_id = message.content.get("agent_id")
        
        logger.info(f"Goal {goal_id} completed by {agent_id}: {'Success' if success else 'Failed'}")
        
        # Find and update the task
        if goal_id in self._active_tasks:
            task = self._active_tasks[goal_id]
            task.completed_at = datetime.now()
            
            if success:
                task.status = TaskStatus.COMPLETED
                # Get result from blackboard if available
                task.result = self.blackboard.get(f"result_{goal_id}")
            else:
                task.status = TaskStatus.FAILED
                
            # Move to completed
            self._completed_tasks[goal_id] = task
            del self._active_tasks[goal_id]
            
            # Check for dependent tasks that can now run
            self._process_unblocked_tasks()
            
            # Check if workflow is complete
            self._check_workflow_completion()
            
    def _handle_task_failed(self, message: Message) -> None:
        """Handle task failure reports."""
        task_id = message.content.get("task_id")
        reason = message.content.get("reason", "Unknown")
        
        logger.error(f"Task {task_id} failed: {reason}")
        
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            self._completed_tasks[task_id] = task
            del self._active_tasks[task_id]
            
    def _handle_status_update(self, message: Message) -> None:
        """Handle status updates from agents."""
        agent_id = message.content.get("agent_id")
        status = message.content.get("status")
        logger.debug(f"Agent {agent_id} status: {status}")
        
    def _handle_assistance_request(self, message: Message) -> None:
        """
        Handle assistance requests from agents.
        
        The orchestrator finds an appropriate agent to help
        and coordinates the collaboration.
        """
        requesting_agent = message.content.get("requesting_agent")
        task_desc = message.content.get("task")
        required_capability = message.content.get("required_capability")
        
        logger.info(f"Agent {requesting_agent} needs help with: {task_desc}")
        
        # Find an agent that can help
        helpers = self.registry.find_agents_by_capability(required_capability)
        helpers = [h for h in helpers if h.agent_id != requesting_agent]
        
        if helpers:
            helper = helpers[0]
            # Send task request to helper
            self.message_bus.publish(Message(
                type=MessageType.TASK_REQUEST,
                sender=self.agent_id,
                recipient=helper.agent_id,
                content={
                    "task": task_desc,
                    "params": message.content,
                    "requested_by": requesting_agent
                }
            ))
            logger.info(f"Delegated assistance to {helper.name}")
        else:
            logger.warning(f"No agent available with capability: {required_capability}")
            
    def submit_task(self, task: Task) -> str:
        """
        Submit a single task for execution.
        
        Args:
            task: The task to execute
            
        Returns:
            The task ID
        """
        self._task_queue.append(task)
        logger.info(f"Task submitted: {task.name} (requires: {task.required_capability})")
        
        # Try to assign immediately
        self._assign_pending_tasks()
        
        return task.id
        
    def submit_workflow(
        self, 
        workflow: WorkflowDefinition,
        on_complete: Optional[callable] = None
    ) -> str:
        """
        Submit a workflow for execution.
        
        The orchestrator will:
        1. Analyze task dependencies
        2. Dynamically assign tasks to capable agents
        3. Coordinate execution respecting dependencies
        4. Report completion when all tasks are done
        
        Args:
            workflow: The workflow definition
            on_complete: Optional callback when workflow completes
            
        Returns:
            The workflow ID
        """
        self._current_workflow = workflow
        self._workflow_complete_callback = on_complete
        
        logger.info(f"Workflow submitted: {workflow.name}")
        logger.info(f"  - Tasks: {len(workflow.tasks)}")
        
        # Add all tasks to queue
        for task in workflow.tasks:
            self._task_queue.append(task)
            
        # Assign tasks that have no dependencies
        self._assign_pending_tasks()
        
        return workflow.id
        
    def _assign_pending_tasks(self) -> None:
        """
        Assign pending tasks to available agents.
        
        This is where dynamic task assignment happens based on:
        - Agent capabilities
        - Agent availability
        - Task dependencies
        """
        tasks_to_remove = []
        
        # Create a copy to iterate over
        queue_snapshot = list(self._task_queue)
        
        for task in queue_snapshot:
            # Skip if already removed
            if task not in self._task_queue:
                continue
                
            # Check if dependencies are met
            if not self._dependencies_met(task):
                task.status = TaskStatus.BLOCKED
                continue
                
            # Find a suitable agent
            agent = self.registry.find_best_agent_for_task(task)
            
            if agent:
                # Assign task
                task.status = TaskStatus.ASSIGNED
                task.assigned_agent = agent.agent_id
                task.started_at = datetime.now()
                
                self._active_tasks[task.id] = task
                tasks_to_remove.append(task)
                
                # Create goal for agent
                goal = AgentGoal(
                    id=task.id,
                    description=task.description,
                    priority=task.priority,
                    context=task.context
                )
                
                # Send goal assignment
                self.message_bus.publish(Message(
                    type=MessageType.GOAL_ASSIGNED,
                    sender=self.agent_id,
                    recipient=agent.agent_id,
                    content={"goal": goal.model_dump()},
                    priority=task.priority
                ))
                
                logger.info(f"Assigned task '{task.name}' to {agent.name}")
            else:
                logger.warning(f"No agent available for task: {task.name}")
                
        # Remove assigned tasks from queue (safely)
        for task in tasks_to_remove:
            if task in self._task_queue:
                self._task_queue.remove(task)
            
    def _dependencies_met(self, task: Task) -> bool:
        """Check if all task dependencies are completed."""
        for dep_id in task.dependencies:
            if dep_id not in self._completed_tasks:
                return False
            if self._completed_tasks[dep_id].status != TaskStatus.COMPLETED:
                return False
        return True
        
    def _process_unblocked_tasks(self) -> None:
        """Process tasks that were blocked but may now be ready."""
        for task in self._task_queue:
            if task.status == TaskStatus.BLOCKED:
                if self._dependencies_met(task):
                    task.status = TaskStatus.PENDING
                    
        self._assign_pending_tasks()
        
    def _check_workflow_completion(self) -> None:
        """Check if the current workflow is complete."""
        if not self._current_workflow:
            return
            
        # Check if all workflow tasks are completed
        workflow_task_ids = {t.id for t in self._current_workflow.tasks}
        completed_ids = set(self._completed_tasks.keys())
        
        if workflow_task_ids.issubset(completed_ids):
            # Check for any failures
            failed = [
                self._completed_tasks[tid] 
                for tid in workflow_task_ids 
                if self._completed_tasks[tid].status == TaskStatus.FAILED
            ]
            
            if failed:
                logger.warning(f"Workflow completed with {len(failed)} failed tasks")
            else:
                logger.info(f"Workflow '{self._current_workflow.name}' completed successfully!")
                
            # Execute callback if provided
            if self._workflow_complete_callback:
                self._workflow_complete_callback(
                    self._current_workflow,
                    failed=failed
                )
                
            self._current_workflow = None
            self._workflow_complete_callback = None
            
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get the status of a task."""
        if task_id in self._active_tasks:
            return self._active_tasks[task_id].status
        if task_id in self._completed_tasks:
            return self._completed_tasks[task_id].status
        for task in self._task_queue:
            if task.id == task_id:
                return task.status
        return None
        
    def get_result(self, task_id: str) -> Optional[Any]:
        """Get the result of a completed task."""
        if task_id in self._completed_tasks:
            return self._completed_tasks[task_id].result
        return self.blackboard.get(f"result_{task_id}")
        
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        return {
            "registered_agents": len(self.registry.get_all_agents()),
            "available_capabilities": self.registry.get_capabilities(),
            "pending_tasks": len(self._task_queue),
            "active_tasks": len(self._active_tasks),
            "completed_tasks": len(self._completed_tasks),
            "agents": [
                {
                    "id": a.agent_id,
                    "name": a.name,
                    "state": a.state.name,
                    "capabilities": a.get_capability_names()
                }
                for a in self.registry.get_all_agents()
            ]
        }
