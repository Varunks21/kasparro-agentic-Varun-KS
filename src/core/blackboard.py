"""
Shared Blackboard for Agent Collaboration
=========================================
Provides a shared state space where agents can publish and 
consume data, enabling indirect coordination.
"""

from typing import Any, Dict, Optional, List, Set
from pydantic import BaseModel, Field
from datetime import datetime
from threading import Lock
import logging

logger = logging.getLogger("kasparro.blackboard")


class BlackboardEntry(BaseModel):
    """An entry on the shared blackboard."""
    
    key: str
    value: Any
    owner: str                           # Agent that created this entry
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    version: int = 1
    tags: Set[str] = Field(default_factory=set)
    
    class Config:
        arbitrary_types_allowed = True


class Blackboard:
    """
    A shared knowledge space for multi-agent coordination.
    
    The Blackboard pattern allows agents to:
    1. Post intermediate results for other agents to consume
    2. Query for data they need without direct coupling
    3. React to changes in shared state
    
    This enables indirect coordination and emergent collaboration.
    """
    
    def __init__(self):
        self._entries: Dict[str, BlackboardEntry] = {}
        self._watchers: Dict[str, List[callable]] = {}
        self._lock = Lock()
        logger.debug("Blackboard initialized")
        
    def post(self, 
             key: str, 
             value: Any, 
             owner: str,
             tags: Optional[Set[str]] = None) -> None:
        """
        Post or update data on the blackboard.
        
        Args:
            key: Unique identifier for the data
            value: The data to store
            owner: Agent ID posting the data
            tags: Optional tags for categorization
        """
        with self._lock:
            if key in self._entries:
                # Update existing entry
                entry = self._entries[key]
                entry.value = value
                entry.updated_at = datetime.now()
                entry.version += 1
                if tags:
                    entry.tags.update(tags)
                logger.debug(f"Blackboard: Updated '{key}' (v{entry.version}) by {owner}")
            else:
                # Create new entry
                entry = BlackboardEntry(
                    key=key,
                    value=value,
                    owner=owner,
                    tags=tags or set()
                )
                self._entries[key] = entry
                logger.debug(f"Blackboard: Posted '{key}' by {owner}")
            
            # Notify watchers
            self._notify_watchers(key, entry)
            
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve data from the blackboard.
        
        Args:
            key: The key to look up
            
        Returns:
            The stored value, or None if not found
        """
        with self._lock:
            entry = self._entries.get(key)
            return entry.value if entry else None
            
    def get_entry(self, key: str) -> Optional[BlackboardEntry]:
        """
        Retrieve full entry metadata from the blackboard.
        
        Args:
            key: The key to look up
            
        Returns:
            The full BlackboardEntry, or None if not found
        """
        with self._lock:
            return self._entries.get(key)
            
    def query_by_tag(self, tag: str) -> Dict[str, Any]:
        """
        Query all entries with a specific tag.
        
        Args:
            tag: The tag to search for
            
        Returns:
            Dict of key -> value for matching entries
        """
        with self._lock:
            return {
                key: entry.value 
                for key, entry in self._entries.items() 
                if tag in entry.tags
            }
            
    def query_by_owner(self, owner: str) -> Dict[str, Any]:
        """
        Query all entries posted by a specific agent.
        
        Args:
            owner: The agent ID to filter by
            
        Returns:
            Dict of key -> value for matching entries
        """
        with self._lock:
            return {
                key: entry.value 
                for key, entry in self._entries.items() 
                if entry.owner == owner
            }
            
    def exists(self, key: str) -> bool:
        """Check if a key exists on the blackboard."""
        with self._lock:
            return key in self._entries
            
    def keys(self) -> List[str]:
        """Get all keys on the blackboard."""
        with self._lock:
            return list(self._entries.keys())
            
    def watch(self, key: str, callback: callable) -> None:
        """
        Register a callback to be notified when a key changes.
        
        Args:
            key: The key to watch
            callback: Function to call with (key, entry) when changed
        """
        with self._lock:
            if key not in self._watchers:
                self._watchers[key] = []
            self._watchers[key].append(callback)
            logger.debug(f"Blackboard: Watcher registered for '{key}'")
            
    def unwatch(self, key: str, callback: callable) -> None:
        """Remove a watcher callback."""
        with self._lock:
            if key in self._watchers and callback in self._watchers[key]:
                self._watchers[key].remove(callback)
                
    def _notify_watchers(self, key: str, entry: BlackboardEntry) -> None:
        """Notify all watchers of a key change."""
        if key in self._watchers:
            for callback in self._watchers[key]:
                try:
                    callback(key, entry)
                except Exception as e:
                    logger.error(f"Blackboard watcher error: {e}")
                    
    def clear(self) -> None:
        """Clear all entries from the blackboard."""
        with self._lock:
            self._entries.clear()
            logger.debug("Blackboard cleared")
            
    def snapshot(self) -> Dict[str, Any]:
        """Get a snapshot of all current values."""
        with self._lock:
            return {key: entry.value for key, entry in self._entries.items()}
