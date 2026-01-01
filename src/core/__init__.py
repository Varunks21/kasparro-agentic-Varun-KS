"""
Core Multi-Agent Framework
==========================
Provides the foundational components for building autonomous, 
coordinated multi-agent systems.
"""

from .base_agent import BaseAgent, AgentCapability, AgentState
from .messages import Message, MessageType, MessageBus
from .blackboard import Blackboard
from .orchestrator import Orchestrator, Task, TaskStatus

__all__ = [
    'BaseAgent',
    'AgentCapability', 
    'AgentState',
    'Message',
    'MessageType',
    'MessageBus',
    'Blackboard',
    'Orchestrator',
    'Task',
    'TaskStatus'
]
