"""
نظام الأحداث (Event System) لنظام Attorney-General.AI
يدير تدفق الأحداث والإشعارات بين مكونات النظام
"""

import logging
import json
import asyncio
import time
from typing import Dict, List, Optional, Any, Callable, Awaitable
from datetime import datetime
import uuid

logger = logging.getLogger("event_system")

class EventSystem:
    """
    نظام الأحداث
    يدير تدفق الأحداث والإشعارات بين مكونات النظام
    """
    
    def __init__(self):
        """
        تهيئة نظام الأحداث
        """
        self._subscribers = {}  # قاموس للمشتركين
        self._event_history = {}  # قاموس لتاريخ الأحداث
        self._max_history_per_type = 100  # الحد الأقصى لعدد الأحداث المحفوظة لكل نوع
        
        logger.info("تم تهيئة نظام الأحداث")
    
    async def publish(self, event_type: str, event_data: Dict, source: str = None) -> str:
        """
        نشر حدث
        
        Args:
            event_type: نوع الحدث
            event_data: بيانات الحدث
            source: مصدر الحدث
            
        Returns:
            معرف الحدث
        """
        # إنشاء معرف للحدث
        event_id = str(uuid.uuid4())
        
        # إنشاء الحدث
        event = {
            "id": event_id,
            "type": event_type,
            "data": event_data,
            "source": source,
            "timestamp": datetime.now().isoformat()
        }
        
        # إضافة الحدث إلى التاريخ
        if event_type not in self._event_history:
            self._event_history[event_type] = []
        
        self._event_history[event_type].append(event)
        
        # التحقق من حجم التاريخ
        if len(self._event_history[event_type]) > self._max_history_per_type:
            # إزالة الأحداث القديمة
            self._event_history[event_type] = self._event_history[event_type][-self._max_history_per_type:]
        
        # إرسال الحدث إلى المشتركين
        await self._notify_subscribers(event_type, event)
        
        logger.debug(f"تم نشر حدث من النوع {event_type} بالمعرف {event_id}")
        return event_id
    
    def subscribe(self, event_type: str, callback: Callable[[Dict], Awaitable[None]]) -> str:
        """
        الاشتراك في نوع حدث
        
        Args:
            event_type: نوع الحدث
            callback: دالة الاستدعاء
            
        Returns:
            معرف الاشتراك
        """
        # إنشاء معرف للاشتراك
        subscription_id = str(uuid.uuid4())
        
        # إضافة المشترك
        if event_type not in self._subscribers:
            self._subscribers[event_type] = {}
        
        self._subscribers[event_type][subscription_id] = callback
        
        logger.debug(f"تم الاشتراك في أحداث من النوع {event_type} بالمعرف {subscription_id}")
        return subscription_id
    
    def unsubscribe(self, event_type: str, subscription_id: str) -> bool:
        """
        إلغاء الاشتراك في نوع حدث
        
        Args:
            event_type: نوع الحدث
            subscription_id: معرف الاشتراك
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود نوع الحدث
        if event_type not in self._subscribers:
            logger.warning(f"لا يوجد مشتركون في أحداث من النوع {event_type}")
            return False
        
        # التحقق من وجود الاشتراك
        if subscription_id not in self._subscribers[event_type]:
            logger.warning(f"الاشتراك {subscription_id} غير موجود في أحداث من النوع {event_type}")
            return False
        
        # إزالة الاشتراك
        del self._subscribers[event_type][subscription_id]
        
        # إذا لم يعد هناك مشتركون في نوع الحدث، إزالة نوع الحدث
        if not self._subscribers[event_type]:
            del self._subscribers[event_type]
        
        logger.debug(f"تم إلغاء الاشتراك {subscription_id} في أحداث من النوع {event_type}")
        return True
    
    def get_event_history(self, event_type: str = None, limit: int = None) -> Dict[str, List[Dict]]:
        """
        الحصول على تاريخ الأحداث
        
        Args:
            event_type: نوع الحدث (اختياري)
            limit: الحد الأقصى لعدد الأحداث (اختياري)
            
        Returns:
            تاريخ الأحداث
        """
        if event_type:
            # الحصول على تاريخ نوع حدث محدد
            if event_type not in self._event_history:
                return {event_type: []}
            
            events = self._event_history[event_type]
            
            # تطبيق الحد
            if limit:
                events = events[-limit:]
            
            return {event_type: events}
        else:
            # الحصول على تاريخ جميع أنواع الأحداث
            history = {}
            
            for event_type, events in self._event_history.items():
                # تطبيق الحد
                if limit:
                    history[event_type] = events[-limit:]
                else:
                    history[event_type] = events
            
            return history
    
    def get_event_types(self) -> List[str]:
        """
        الحصول على أنواع الأحداث المتاحة
        
        Returns:
            أنواع الأحداث
        """
        return list(self._event_history.keys())
    
    def get_subscriber_count(self, event_type: str = None) -> Dict[str, int]:
        """
        الحصول على عدد المشتركين
        
        Args:
            event_type: نوع الحدث (اختياري)
            
        Returns:
            عدد المشتركين
        """
        if event_type:
            # الحصول على عدد المشتركين في نوع حدث محدد
            if event_type not in self._subscribers:
                return {event_type: 0}
            
            return {event_type: len(self._subscribers[event_type])}
        else:
            # الحصول على عدد المشتركين في جميع أنواع الأحداث
            counts = {}
            
            for event_type, subscribers in self._subscribers.items():
                counts[event_type] = len(subscribers)
            
            return counts
    
    def clear_event_history(self, event_type: str = None) -> bool:
        """
        مسح تاريخ الأحداث
        
        Args:
            event_type: نوع الحدث (اختياري)
            
        Returns:
            نجاح العملية
        """
        if event_type:
            # مسح تاريخ نوع حدث محدد
            if event_type not in self._event_history:
                logger.warning(f"لا يوجد تاريخ لأحداث من النوع {event_type}")
                return False
            
            self._event_history[event_type] = []
            logger.info(f"تم مسح تاريخ الأحداث من النوع {event_type}")
        else:
            # مسح تاريخ جميع أنواع الأحداث
            self._event_history = {}
            logger.info("تم مسح تاريخ جميع الأحداث")
        
        return True
    
    async def _notify_subscribers(self, event_type: str, event: Dict) -> None:
        """
        إشعار المشتركين بحدث
        
        Args:
            event_type: نوع الحدث
            event: الحدث
        """
        # التحقق من وجود مشتركين في نوع الحدث
        if event_type not in self._subscribers:
            return
        
        # إشعار المشتركين
        for subscription_id, callback in self._subscribers[event_type].items():
            try:
                await callback(event)
            except Exception as e:
                logger.error(f"خطأ في استدعاء المشترك {subscription_id} للحدث {event['id']}: {e}")
    
    def export_event_history(self, event_type: str = None) -> Dict:
        """
        تصدير تاريخ الأحداث
        
        Args:
            event_type: نوع الحدث (اختياري)
            
        Returns:
            تاريخ الأحداث
        """
        history = self.get_event_history(event_type)
        
        return {
            "event_history": history,
            "exported_at": datetime.now().isoformat()
        }
    
    def import_event_history(self, history_data: Dict) -> bool:
        """
        استيراد تاريخ الأحداث
        
        Args:
            history_data: بيانات تاريخ الأحداث
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود تاريخ الأحداث
        if "event_history" not in history_data:
            logger.error("بيانات تاريخ الأحداث غير صالحة")
            return False
        
        # استيراد تاريخ الأحداث
        for event_type, events in history_data["event_history"].items():
            self._event_history[event_type] = events
        
        logger.info("تم استيراد تاريخ الأحداث")
        return True
