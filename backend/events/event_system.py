"""
Attorney-General.AI - Event System

This module implements the event system for the Attorney-General.AI backend.
It provides functionality for publishing and subscribing to events.
"""

import logging
from typing import Dict, Any, List, Callable, Optional
import asyncio
import uuid

logger = logging.getLogger(__name__)

class EventSystem:
    """Event system for publishing and subscribing to events."""
    
    def __init__(self):
        """Initialize the event system."""
        self.subscribers = {}
        self.event_history = {}
    
    async def publish(self, event_type: str, data: Dict[str, Any]) -> str:
        """
        Publish an event to all subscribers.
        
        Args:
            event_type: The type of event
            data: The event data
            
        Returns:
            str: The event ID
        """
        event_id = str(uuid.uuid4())
        
        # Create event object
        event = {
            "id": event_id,
            "type": event_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Store event in history
        if event_type not in self.event_history:
            self.event_history[event_type] = []
        self.event_history[event_type].append(event)
        
        # Limit history size
        max_history = 100
        if len(self.event_history[event_type]) > max_history:
            self.event_history[event_type] = self.event_history[event_type][-max_history:]
        
        # Notify subscribers
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    await callback(event)
                except Exception as e:
                    logger.error(f"Error in event subscriber callback: {str(e)}")
        
        return event_id
    
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: The type of event to subscribe to
            callback: The callback function to call when the event is published
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable) -> bool:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: The type of event to unsubscribe from
            callback: The callback function to remove
            
        Returns:
            bool: True if the callback was removed, False otherwise
        """
        if event_type in self.subscribers and callback in self.subscribers[event_type]:
            self.subscribers[event_type].remove(callback)
            return True
        
        return False
    
    def get_event_history(self, event_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the event history.
        
        Args:
            event_type: Optional event type to filter by
            limit: Maximum number of events to return
            
        Returns:
            List[Dict[str, Any]]: The event history
        """
        if event_type:
            if event_type in self.event_history:
                return self.event_history[event_type][-limit:]
            return []
        
        # Combine all event types
        all_events = []
        for events in self.event_history.values():
            all_events.extend(events)
        
        # Sort by timestamp
        all_events.sort(key=lambda e: e["timestamp"])
        
        return all_events[-limit:]

# Create a global event system instance
event_system = EventSystem()
