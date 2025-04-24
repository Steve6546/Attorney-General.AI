"""
نظام تدفق الأحداث (Event Stream) لنظام Attorney-General.AI
يدير تدفق الأحداث بين مكونات النظام
"""

import logging
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum, auto

logger = logging.getLogger("event_stream")

class EventStreamSubscriber(Enum):
    """أنواع المشتركين في نظام الأحداث"""
    CONTROLLER = auto()
    AGENT = auto()
    MEMORY = auto()
    SECURITY = auto()
    STORAGE = auto()
    LOGGER = auto()
    PLUGIN = auto()
    EXTERNAL = auto()

class Event:
    """
    كائن الحدث
    يمثل حدثاً في النظام
    """
    
    def __init__(self, event_type: str, data: Any, source: str, timestamp: str = None):
        """
        تهيئة الحدث
        
        Args:
            event_type: نوع الحدث
            data: بيانات الحدث
            source: مصدر الحدث
            timestamp: الطابع الزمني للحدث
        """
        self.type = event_type
        self.data = data
        self.source = source
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """
        تحويل الحدث إلى قاموس
        
        Returns:
            قاموس يمثل الحدث
        """
        return {
            "type": self.type,
            "data": self.data,
            "source": self.source,
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, event_dict: Dict) -> 'Event':
        """
        إنشاء حدث من قاموس
        
        Args:
            event_dict: قاموس يمثل الحدث
            
        Returns:
            كائن الحدث
        """
        return cls(
            event_type=event_dict["type"],
            data=event_dict["data"],
            source=event_dict["source"],
            timestamp=event_dict.get("timestamp")
        )

class EventStream:
    """
    نظام تدفق الأحداث
    يدير تدفق الأحداث بين مكونات النظام
    """
    
    def __init__(self, max_history: int = 1000):
        """
        تهيئة نظام تدفق الأحداث
        
        Args:
            max_history: الحد الأقصى لعدد الأحداث المخزنة في التاريخ
        """
        self._subscribers = {}  # قاموس المشتركين
        self._history = []  # تاريخ الأحداث
        self._max_history = max_history
        logger.info("تم تهيئة نظام تدفق الأحداث")
    
    def subscribe(self, subscriber: EventStreamSubscriber, callback: Callable[[Event], None],
                 subscriber_id: str, event_types: List[str]) -> bool:
        """
        تسجيل مشترك في نظام الأحداث
        
        Args:
            subscriber: نوع المشترك
            callback: دالة الاستدعاء عند حدوث الحدث
            subscriber_id: معرف المشترك
            event_types: أنواع الأحداث المطلوبة
            
        Returns:
            نجاح العملية
        """
        if not event_types:
            logger.warning(f"لا يمكن تسجيل المشترك {subscriber_id} بدون أنواع أحداث")
            return False
        
        # تسجيل المشترك
        self._subscribers[subscriber_id] = {
            "type": subscriber,
            "callback": callback,
            "event_types": event_types
        }
        
        logger.info(f"تم تسجيل المشترك {subscriber_id} لأنواع الأحداث: {', '.join(event_types)}")
        return True
    
    def unsubscribe(self, subscriber_id: str) -> bool:
        """
        إلغاء تسجيل مشترك من نظام الأحداث
        
        Args:
            subscriber_id: معرف المشترك
            
        Returns:
            نجاح العملية
        """
        if subscriber_id not in self._subscribers:
            logger.warning(f"المشترك {subscriber_id} غير مسجل")
            return False
        
        # إلغاء تسجيل المشترك
        del self._subscribers[subscriber_id]
        
        logger.info(f"تم إلغاء تسجيل المشترك {subscriber_id}")
        return True
    
    def publish(self, event_type: str, data: Any, source: str) -> bool:
        """
        نشر حدث في النظام
        
        Args:
            event_type: نوع الحدث
            data: بيانات الحدث
            source: مصدر الحدث
            
        Returns:
            نجاح العملية
        """
        # إنشاء الحدث
        event = Event(event_type, data, source)
        
        # إضافة الحدث إلى التاريخ
        self._history.append(event)
        
        # التحقق من حجم التاريخ
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        
        # إرسال الحدث إلى المشتركين
        for subscriber_id, subscriber in self._subscribers.items():
            event_types = subscriber["event_types"]
            
            # التحقق مما إذا كان المشترك مهتماً بهذا النوع من الأحداث
            if "*" in event_types or event_type in event_types:
                try:
                    subscriber["callback"](event)
                except Exception as e:
                    logger.error(f"خطأ في معالجة الحدث للمشترك {subscriber_id}: {e}")
        
        logger.debug(f"تم نشر حدث {event_type} من المصدر {source}")
        return True
    
    def get_history(self, limit: int = None, event_types: List[str] = None) -> List[Dict]:
        """
        الحصول على تاريخ الأحداث
        
        Args:
            limit: الحد الأقصى لعدد الأحداث المطلوبة
            event_types: أنواع الأحداث المطلوبة
            
        Returns:
            قائمة الأحداث
        """
        # تحديد الحد الأقصى
        if limit is None or limit > len(self._history):
            limit = len(self._history)
        
        # تصفية الأحداث حسب النوع
        if event_types:
            filtered_events = [
                event.to_dict() for event in self._history
                if event.type in event_types
            ]
        else:
            filtered_events = [event.to_dict() for event in self._history]
        
        # إرجاع الأحداث المحددة
        return filtered_events[-limit:]
    
    def clear_history(self) -> bool:
        """
        مسح تاريخ الأحداث
        
        Returns:
            نجاح العملية
        """
        self._history = []
        logger.info("تم مسح تاريخ الأحداث")
        return True
    
    def get_subscribers(self) -> Dict:
        """
        الحصول على قائمة المشتركين
        
        Returns:
            قاموس المشتركين
        """
        subscribers = {}
        
        for subscriber_id, subscriber in self._subscribers.items():
            subscribers[subscriber_id] = {
                "type": subscriber["type"].name,
                "event_types": subscriber["event_types"]
            }
        
        return subscribers
