"""
Base Agent Framework for Autonomous Agents
==========================================
Provides the foundational class for creating autonomous agents 
with goal-driven behavior, state management, and communication capabilities.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING
from pydantic import BaseModel, Field
from datetime import datetime
import logging

if TYPE_CHECKING:
    from .messages import Message, MessageBus, MessageType
    from .blackboard import Blackboard

logger = logging.getLogger("kasparro.agent")


class AgentState(Enum):
    """Possible states for an autonomous agent."""
    
    IDLE = auto()           # Ready to accept tasks
    THINKING = auto()       # Processing/planning
    EXECUTING = auto()      # Actively working on a task
    WAITING = auto()        # Waiting for external input/collaboration
    COMPLETED = auto()      # Task completed successfully
    FAILED = auto()         # Task failed
    SUSPENDED = auto()      # Temporarily paused


class AgentCapability(BaseModel):
    """Describes a capability that an agent possesses."""
    
    name: str
    description: str
    input_types: List[str] = Field(default_factory=list)
    output_types: List[str] = Field(default_factory=list)
    
    
class AgentGoal(BaseModel):
    """A goal assigned to an agent."""
    
    id: str
    description: str
    priority: int = 5
    deadline: Optional[datetime] = None
    dependencies: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    

class AgentMemory(BaseModel):
    """
    Agent's internal memory/state that persists across actions.
    
    This enables agents to learn from past interactions and 
    maintain context throughout their operation.
    """
    
    observations: List[Dict[str, Any]] = Field(default_factory=list)
    decisions: List[Dict[str, Any]] = Field(default_factory=list)
    outcomes: List[Dict[str, Any]] = Field(default_factory=list)
    
    def record_observation(self, observation: Dict[str, Any]) -> None:
        """Record an observation about the environment/task."""
        self.observations.append({
            **observation,
            "timestamp": datetime.now().isoformat()
        })
        
    def record_decision(self, decision: str, reasoning: str) -> None:
        """Record a decision made by the agent."""
        self.decisions.append({
            "decision": decision,
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat()
        })
        
    def record_outcome(self, action: str, success: bool, result: Any = None) -> None:
        """Record the outcome of an action."""
        self.outcomes.append({
            "action": action,
            "success": success,
            "result": str(result)[:500] if result else None,
            "timestamp": datetime.now().isoformat()
        })


class BaseAgent(ABC):
    """
    Abstract base class for autonomous agents.
    
    An agent is an autonomous entity that:
    1. Has its own identity and capabilities
    2. Maintains internal state and memory
    3. Can receive and pursue goals
    4. Communicates with other agents via messages
    5. Makes autonomous decisions based on its knowledge
    
    Subclasses must implement the abstract methods to define
    agent-specific behavior.
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str,
        capabilities: Optional[List[AgentCapability]] = None
    ):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.capabilities = capabilities or []
        
        # Agent state
        self._state = AgentState.IDLE
        self._current_goal: Optional[AgentGoal] = None
        self._goal_queue: List[AgentGoal] = []
        
        # Memory and learning
        self.memory = AgentMemory()
        
        # Communication
        self._message_bus: Optional['MessageBus'] = None
        self._blackboard: Optional['Blackboard'] = None
        self._inbox: List['Message'] = []
        
        # Logging
        self.logger = logging.getLogger(f"kasparro.{agent_id}")
        self.logger.debug(f"Agent '{name}' initialized with capabilities: {[c.name for c in self.capabilities]}")
        
    @property
    def state(self) -> AgentState:
        """Current state of the agent."""
        return self._state
        
    @state.setter
    def state(self, new_state: AgentState) -> None:
        """Update agent state with logging."""
        old_state = self._state
        self._state = new_state
        self.logger.debug(f"State transition: {old_state.name} -> {new_state.name}")
        
    def connect(self, message_bus: 'MessageBus', blackboard: 'Blackboard') -> None:
        """
        Connect the agent to the multi-agent system.
        
        Args:
            message_bus: The shared message bus for communication
            blackboard: The shared blackboard for data exchange
        """
        self._message_bus = message_bus
        self._blackboard = blackboard
        
        # Subscribe to directed messages
        message_bus.subscribe(self.agent_id, self._handle_message)
        self.logger.info(f"Agent '{self.name}' connected to multi-agent system")
        
    def disconnect(self) -> None:
        """Disconnect from the multi-agent system."""
        if self._message_bus:
            self._message_bus.unsubscribe(self.agent_id)
        self._message_bus = None
        self._blackboard = None
        self.logger.info(f"Agent '{self.name}' disconnected")
        
    def _handle_message(self, message: 'Message') -> None:
        """
        Internal message handler. Routes messages to appropriate handlers.
        """
        from .messages import MessageType
        
        self._inbox.append(message)
        self.logger.debug(f"Received message: {message.type.name} from {message.sender}")
        
        # Route based on message type
        if message.type == MessageType.GOAL_ASSIGNED:
            self._handle_goal_assignment(message)
        elif message.type == MessageType.DATA_REQUEST:
            self._handle_data_request(message)
        elif message.type == MessageType.TASK_REQUEST:
            self._handle_task_request(message)
        elif message.type == MessageType.CAPABILITY_QUERY:
            self._handle_capability_query(message)
        else:
            self.on_message(message)
            
    def _handle_goal_assignment(self, message: 'Message') -> None:
        """Handle a goal assignment from the orchestrator."""
        goal_data = message.content.get("goal")
        if goal_data:
            goal = AgentGoal(**goal_data)
            self.assign_goal(goal)
            
    def _handle_data_request(self, message: 'Message') -> None:
        """Handle a data request from another agent."""
        from .messages import MessageType
        
        requested_data = message.content.get("data_key")
        if requested_data and self._blackboard:
            data = self._blackboard.get(requested_data)
            self.send_message(
                MessageType.DATA_RESPONSE,
                message.sender,
                {"data_key": requested_data, "data": data}
            )
            
    def _handle_task_request(self, message: 'Message') -> None:
        """Handle a task request from another agent."""
        task_name = message.content.get("task")
        task_params = message.content.get("params", {})
        
        # Record the request
        self.memory.record_observation({
            "type": "task_request",
            "from": message.sender,
            "task": task_name,
            "params": task_params
        })
        
        # Delegate to subclass implementation
        self.on_task_request(task_name, task_params, message)
        
    def _handle_capability_query(self, message: 'Message') -> None:
        """Respond to capability queries."""
        from .messages import MessageType
        
        self.send_message(
            MessageType.CAPABILITY_RESPONSE,
            message.sender,
            {
                "agent_id": self.agent_id,
                "capabilities": [c.model_dump() for c in self.capabilities]
            }
        )
        
    def send_message(
        self,
        msg_type: 'MessageType',
        recipient: Optional[str],
        content: Dict[str, Any],
        priority: int = 5
    ) -> None:
        """
        Send a message to another agent or broadcast.
        
        Args:
            msg_type: Type of message to send
            recipient: Agent ID to send to (None for broadcast)
            content: Message content
            priority: Message priority (1-10)
        """
        from .messages import Message
        
        if not self._message_bus:
            self.logger.warning("Cannot send message: not connected to message bus")
            return
            
        message = Message(
            type=msg_type,
            sender=self.agent_id,
            recipient=recipient,
            content=content,
            priority=priority
        )
        self._message_bus.publish(message)
        self.logger.debug(f"Sent {msg_type.name} to {recipient or 'broadcast'}")
        
    def post_to_blackboard(
        self,
        key: str,
        value: Any,
        tags: Optional[Set[str]] = None
    ) -> None:
        """
        Post data to the shared blackboard.
        
        Args:
            key: Key to store data under
            value: Data to store
            tags: Optional tags for categorization
        """
        if not self._blackboard:
            self.logger.warning("Cannot post: not connected to blackboard")
            return
            
        self._blackboard.post(key, value, self.agent_id, tags)
        self.logger.debug(f"Posted '{key}' to blackboard")
        
    def read_from_blackboard(self, key: str) -> Optional[Any]:
        """
        Read data from the shared blackboard.
        
        Args:
            key: Key to read
            
        Returns:
            The stored value, or None if not found
        """
        if not self._blackboard:
            return None
        return self._blackboard.get(key)
        
    def assign_goal(self, goal: AgentGoal) -> None:
        """
        Assign a goal to this agent.
        
        The agent will autonomously work towards achieving this goal.
        
        Args:
            goal: The goal to achieve
        """
        self._goal_queue.append(goal)
        self.logger.info(f"Goal assigned: {goal.description}")
        
        # If idle, start working on the goal
        if self.state == AgentState.IDLE:
            self._process_next_goal()
            
    def _process_next_goal(self) -> None:
        """Process the next goal in the queue."""
        if not self._goal_queue:
            self.state = AgentState.IDLE
            return
            
        # Sort by priority (lower number = higher priority)
        self._goal_queue.sort(key=lambda g: g.priority)
        self._current_goal = self._goal_queue.pop(0)
        
        self.logger.info(f"Processing goal: {self._current_goal.description}")
        self.state = AgentState.THINKING
        
        # Autonomous planning
        plan = self.plan(self._current_goal)
        
        if plan:
            self.memory.record_decision(
                f"Execute plan for: {self._current_goal.description}",
                f"Generated {len(plan)} steps"
            )
            self.state = AgentState.EXECUTING
            success = self.execute(plan, self._current_goal)
            
            if success:
                self.state = AgentState.COMPLETED
                self._report_goal_complete(self._current_goal)
            else:
                self.state = AgentState.FAILED
                self._report_goal_failed(self._current_goal)
        else:
            self.state = AgentState.FAILED
            self._report_goal_failed(self._current_goal, "Failed to create plan")
            
        # Process next goal
        self._current_goal = None
        self._process_next_goal()
        
    def _report_goal_complete(self, goal: AgentGoal) -> None:
        """Report goal completion to the orchestrator."""
        from .messages import MessageType
        
        self.memory.record_outcome(goal.description, success=True)
        self.send_message(
            MessageType.GOAL_COMPLETE,
            "orchestrator",
            {
                "goal_id": goal.id,
                "agent_id": self.agent_id,
                "success": True
            }
        )
        
    def _report_goal_failed(self, goal: AgentGoal, reason: str = "Execution failed") -> None:
        """Report goal failure to the orchestrator."""
        from .messages import MessageType
        
        self.memory.record_outcome(goal.description, success=False, result=reason)
        self.send_message(
            MessageType.GOAL_COMPLETE,
            "orchestrator",
            {
                "goal_id": goal.id,
                "agent_id": self.agent_id,
                "success": False,
                "reason": reason
            }
        )
        
    def request_assistance(self, task: str, required_capability: str) -> None:
        """
        Request assistance from other agents.
        
        Args:
            task: Description of what help is needed
            required_capability: The capability needed
        """
        from .messages import MessageType
        
        self.state = AgentState.WAITING
        self.send_message(
            MessageType.NEED_ASSISTANCE,
            None,  # Broadcast
            {
                "requesting_agent": self.agent_id,
                "task": task,
                "required_capability": required_capability
            }
        )
        self.logger.info(f"Requested assistance for: {task}")
        
    def get_capability_names(self) -> List[str]:
        """Get list of capability names this agent has."""
        return [cap.name for cap in self.capabilities]
        
    def has_capability(self, capability_name: str) -> bool:
        """Check if this agent has a specific capability."""
        return capability_name in self.get_capability_names()
        
    # =====================================================
    # Abstract methods - Must be implemented by subclasses
    # =====================================================
    
    @abstractmethod
    def plan(self, goal: AgentGoal) -> Optional[List[Dict[str, Any]]]:
        """
        Create a plan to achieve the given goal.
        
        This is where the agent's autonomous decision-making happens.
        The agent analyzes the goal and creates a sequence of steps.
        
        Args:
            goal: The goal to plan for
            
        Returns:
            A list of action steps, or None if planning fails
        """
        pass
        
    @abstractmethod
    def execute(self, plan: List[Dict[str, Any]], goal: AgentGoal) -> bool:
        """
        Execute a plan to achieve a goal.
        
        The agent carries out the planned steps, adapting as needed.
        
        Args:
            plan: The plan to execute
            goal: The goal being pursued
            
        Returns:
            True if execution succeeded, False otherwise
        """
        pass
        
    @abstractmethod
    def on_message(self, message: 'Message') -> None:
        """
        Handle a custom message not covered by default handlers.
        
        Subclasses implement this to handle domain-specific messages.
        
        Args:
            message: The received message
        """
        pass
        
    @abstractmethod
    def on_task_request(
        self,
        task_name: str,
        params: Dict[str, Any],
        message: 'Message'
    ) -> None:
        """
        Handle a task request from another agent.
        
        This enables agent collaboration through task delegation.
        
        Args:
            task_name: Name of the requested task
            params: Task parameters
            message: The original request message
        """
        pass
