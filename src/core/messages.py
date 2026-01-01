"""
Message Protocol for Inter-Agent Communication
==============================================
Defines the message types and communication bus for agent collaboration.
"""

from enum import Enum, auto
from typing import Any, Dict, Optional, List, Callable
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class MessageType(Enum):
    """Types of messages that agents can exchange."""
    
    # Task-related messages
    TASK_REQUEST = auto()       # Request an agent to perform a task
    TASK_COMPLETE = auto()      # Notify that a task is complete
    TASK_FAILED = auto()        # Notify that a task failed
    
    # Collaboration messages
    DATA_REQUEST = auto()       # Request data from another agent
    DATA_RESPONSE = auto()      # Respond with requested data
    
    # Coordination messages
    CAPABILITY_QUERY = auto()   # Query agent capabilities
    CAPABILITY_RESPONSE = auto() # Respond with capabilities
    
    # Status messages
    STATUS_UPDATE = auto()      # Update on agent status
    HEARTBEAT = auto()          # Keep-alive signal
    
    # Orchestrator messages
    GOAL_ASSIGNED = auto()      # Orchestrator assigns a goal
    GOAL_COMPLETE = auto()      # Agent reports goal completion
    NEED_ASSISTANCE = auto()    # Agent requests help from others


class Message(BaseModel):
    """
    A message exchanged between agents in the multi-agent system.
    
    Messages are the primary means of communication and coordination
    between autonomous agents.
    """
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: MessageType
    sender: str                          # Agent ID of sender
    recipient: Optional[str] = None      # Agent ID of recipient (None = broadcast)
    content: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    correlation_id: Optional[str] = None # Links related messages
    priority: int = Field(default=5, ge=1, le=10)  # 1=highest, 10=lowest
    
    class Config:
        use_enum_values = False
        
    def reply(self, type: MessageType, content: Dict[str, Any]) -> 'Message':
        """Create a reply message to this message."""
        return Message(
            type=type,
            sender=self.recipient or "unknown",
            recipient=self.sender,
            content=content,
            correlation_id=self.id,
            priority=self.priority
        )


class MessageBus:
    """
    Central message bus for agent communication.
    
    Provides publish-subscribe pattern for agent messaging,
    enabling decoupled communication between agents.
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Message], None]]] = {}
        self._broadcast_subscribers: List[Callable[[Message], None]] = []
        self._message_history: List[Message] = []
        self._max_history = 1000
        
    def subscribe(self, agent_id: str, handler: Callable[[Message], None]) -> None:
        """
        Subscribe an agent to receive directed messages.
        
        Args:
            agent_id: Unique identifier for the agent
            handler: Callback function to handle incoming messages
        """
        if agent_id not in self._subscribers:
            self._subscribers[agent_id] = []
        self._subscribers[agent_id].append(handler)
        
    def subscribe_broadcast(self, handler: Callable[[Message], None]) -> None:
        """
        Subscribe to all broadcast messages.
        
        Args:
            handler: Callback function to handle broadcast messages
        """
        self._broadcast_subscribers.append(handler)
        
    def unsubscribe(self, agent_id: str) -> None:
        """
        Unsubscribe an agent from the message bus.
        
        Args:
            agent_id: Unique identifier for the agent
        """
        if agent_id in self._subscribers:
            del self._subscribers[agent_id]
            
    def publish(self, message: Message) -> None:
        """
        Publish a message to the appropriate recipient(s).
        
        Args:
            message: The message to publish
        """
        # Store in history
        self._message_history.append(message)
        if len(self._message_history) > self._max_history:
            self._message_history = self._message_history[-self._max_history:]
        
        if message.recipient is None:
            # Broadcast message
            for handler in self._broadcast_subscribers:
                handler(message)
            # Also send to all subscribed agents
            for handlers in self._subscribers.values():
                for handler in handlers:
                    handler(message)
        else:
            # Directed message
            if message.recipient in self._subscribers:
                for handler in self._subscribers[message.recipient]:
                    handler(message)
                    
    def get_history(self, 
                    sender: Optional[str] = None,
                    recipient: Optional[str] = None,
                    message_type: Optional[MessageType] = None,
                    limit: int = 100) -> List[Message]:
        """
        Retrieve message history with optional filtering.
        
        Args:
            sender: Filter by sender agent ID
            recipient: Filter by recipient agent ID
            message_type: Filter by message type
            limit: Maximum number of messages to return
            
        Returns:
            List of matching messages
        """
        filtered = self._message_history
        
        if sender:
            filtered = [m for m in filtered if m.sender == sender]
        if recipient:
            filtered = [m for m in filtered if m.recipient == recipient]
        if message_type:
            filtered = [m for m in filtered if m.type == message_type]
            
        return filtered[-limit:]
