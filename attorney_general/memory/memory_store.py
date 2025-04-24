"""
نظام الذاكرة (Memory Store) لنظام Attorney-General.AI
يدير ذاكرة المحادثات والسياق
"""

import logging
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger("memory_store")

class MemoryStore:
    """
    نظام الذاكرة
    يدير ذاكرة المحادثات والسياق
    """
    
    def __init__(self, max_short_term_items: int = 100, max_long_term_items: int = 1000):
        """
        تهيئة نظام الذاكرة
        
        Args:
            max_short_term_items: الحد الأقصى لعدد العناصر في الذاكرة قصيرة المدى
            max_long_term_items: الحد الأقصى لعدد العناصر في الذاكرة طويلة المدى
        """
        self._short_term_memory = {}  # قاموس للذاكرة قصيرة المدى
        self._long_term_memory = {}  # قاموس للذاكرة طويلة المدى
        self._condensed_memory = {}  # قاموس للذاكرة المكثفة
        
        self._max_short_term_items = max_short_term_items
        self._max_long_term_items = max_long_term_items
        
        logger.info("تم تهيئة نظام الذاكرة")
    
    def create_memory(self, conversation_id: str) -> Dict:
        """
        إنشاء ذاكرة جديدة لمحادثة
        
        Args:
            conversation_id: معرف المحادثة
            
        Returns:
            معلومات الذاكرة
        """
        # التحقق من عدم وجود الذاكرة مسبقاً
        if conversation_id in self._short_term_memory:
            logger.warning(f"الذاكرة للمحادثة {conversation_id} موجودة مسبقاً")
            return self.get_memory(conversation_id)
        
        # إنشاء الذاكرة
        self._short_term_memory[conversation_id] = []
        self._long_term_memory[conversation_id] = []
        self._condensed_memory[conversation_id] = {
            "summary": "",
            "key_points": [],
            "last_updated": datetime.now().isoformat()
        }
        
        logger.info(f"تم إنشاء ذاكرة جديدة للمحادثة: {conversation_id}")
        
        return {
            "conversation_id": conversation_id,
            "short_term": [],
            "long_term": [],
            "condensed": self._condensed_memory[conversation_id]
        }
    
    def get_memory(self, conversation_id: str) -> Optional[Dict]:
        """
        الحصول على ذاكرة محادثة
        
        Args:
            conversation_id: معرف المحادثة
            
        Returns:
            معلومات الذاكرة أو None إذا لم تكن موجودة
        """
        # التحقق من وجود الذاكرة
        if conversation_id not in self._short_term_memory:
            logger.warning(f"الذاكرة للمحادثة {conversation_id} غير موجودة")
            return None
        
        return {
            "conversation_id": conversation_id,
            "short_term": self._short_term_memory[conversation_id],
            "long_term": self._long_term_memory[conversation_id],
            "condensed": self._condensed_memory[conversation_id]
        }
    
    def add_to_short_term_memory(self, conversation_id: str, item: Dict) -> bool:
        """
        إضافة عنصر إلى الذاكرة قصيرة المدى
        
        Args:
            conversation_id: معرف المحادثة
            item: العنصر المراد إضافته
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود الذاكرة
        if conversation_id not in self._short_term_memory:
            logger.warning(f"الذاكرة للمحادثة {conversation_id} غير موجودة")
            return False
        
        # إضافة العنصر
        self._short_term_memory[conversation_id].append(item)
        
        # التحقق من حجم الذاكرة
        if len(self._short_term_memory[conversation_id]) > self._max_short_term_items:
            # نقل العناصر القديمة إلى الذاكرة طويلة المدى
            oldest_item = self._short_term_memory[conversation_id].pop(0)
            self._long_term_memory[conversation_id].append(oldest_item)
            
            # التحقق من حجم الذاكرة طويلة المدى
            if len(self._long_term_memory[conversation_id]) > self._max_long_term_items:
                # إزالة العناصر القديمة
                self._long_term_memory[conversation_id] = self._long_term_memory[conversation_id][-self._max_long_term_items:]
        
        logger.debug(f"تم إضافة عنصر إلى الذاكرة قصيرة المدى للمحادثة: {conversation_id}")
        return True
    
    def add_to_long_term_memory(self, conversation_id: str, item: Dict) -> bool:
        """
        إضافة عنصر إلى الذاكرة طويلة المدى
        
        Args:
            conversation_id: معرف المحادثة
            item: العنصر المراد إضافته
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود الذاكرة
        if conversation_id not in self._long_term_memory:
            logger.warning(f"الذاكرة للمحادثة {conversation_id} غير موجودة")
            return False
        
        # إضافة العنصر
        self._long_term_memory[conversation_id].append(item)
        
        # التحقق من حجم الذاكرة
        if len(self._long_term_memory[conversation_id]) > self._max_long_term_items:
            # إزالة العناصر القديمة
            self._long_term_memory[conversation_id] = self._long_term_memory[conversation_id][-self._max_long_term_items:]
        
        logger.debug(f"تم إضافة عنصر إلى الذاكرة طويلة المدى للمحادثة: {conversation_id}")
        return True
    
    def update_condensed_memory(self, conversation_id: str, summary: str = None, key_points: List[str] = None) -> bool:
        """
        تحديث الذاكرة المكثفة
        
        Args:
            conversation_id: معرف المحادثة
            summary: ملخص المحادثة
            key_points: النقاط الرئيسية
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود الذاكرة
        if conversation_id not in self._condensed_memory:
            logger.warning(f"الذاكرة للمحادثة {conversation_id} غير موجودة")
            return False
        
        # تحديث الذاكرة المكثفة
        if summary is not None:
            self._condensed_memory[conversation_id]["summary"] = summary
        
        if key_points is not None:
            self._condensed_memory[conversation_id]["key_points"] = key_points
        
        # تحديث وقت التحديث
        self._condensed_memory[conversation_id]["last_updated"] = datetime.now().isoformat()
        
        logger.info(f"تم تحديث الذاكرة المكثفة للمحادثة: {conversation_id}")
        return True
    
    def get_short_term_memory(self, conversation_id: str, limit: int = None) -> Optional[List[Dict]]:
        """
        الحصول على الذاكرة قصيرة المدى
        
        Args:
            conversation_id: معرف المحادثة
            limit: الحد الأقصى لعدد العناصر
            
        Returns:
            الذاكرة قصيرة المدى أو None إذا لم تكن موجودة
        """
        # التحقق من وجود الذاكرة
        if conversation_id not in self._short_term_memory:
            logger.warning(f"الذاكرة للمحادثة {conversation_id} غير موجودة")
            return None
        
        # الحصول على الذاكرة
        memory = self._short_term_memory[conversation_id]
        
        # تطبيق الحد
        if limit is not None:
            memory = memory[-limit:]
        
        return memory
    
    def get_long_term_memory(self, conversation_id: str, limit: int = None) -> Optional[List[Dict]]:
        """
        الحصول على الذاكرة طويلة المدى
        
        Args:
            conversation_id: معرف المحادثة
            limit: الحد الأقصى لعدد العناصر
            
        Returns:
            الذاكرة طويلة المدى أو None إذا لم تكن موجودة
        """
        # التحقق من وجود الذاكرة
        if conversation_id not in self._long_term_memory:
            logger.warning(f"الذاكرة للمحادثة {conversation_id} غير موجودة")
            return None
        
        # الحصول على الذاكرة
        memory = self._long_term_memory[conversation_id]
        
        # تطبيق الحد
        if limit is not None:
            memory = memory[-limit:]
        
        return memory
    
    def get_condensed_memory(self, conversation_id: str) -> Optional[Dict]:
        """
        الحصول على الذاكرة المكثفة
        
        Args:
            conversation_id: معرف المحادثة
            
        Returns:
            الذاكرة المكثفة أو None إذا لم تكن موجودة
        """
        # التحقق من وجود الذاكرة
        if conversation_id not in self._condensed_memory:
            logger.warning(f"الذاكرة للمحادثة {conversation_id} غير موجودة")
            return None
        
        return self._condensed_memory[conversation_id]
    
    def clear_memory(self, conversation_id: str) -> bool:
        """
        مسح ذاكرة محادثة
        
        Args:
            conversation_id: معرف المحادثة
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود الذاكرة
        if conversation_id not in self._short_term_memory:
            logger.warning(f"الذاكرة للمحادثة {conversation_id} غير موجودة")
            return False
        
        # مسح الذاكرة
        self._short_term_memory[conversation_id] = []
        self._long_term_memory[conversation_id] = []
        self._condensed_memory[conversation_id] = {
            "summary": "",
            "key_points": [],
            "last_updated": datetime.now().isoformat()
        }
        
        logger.info(f"تم مسح ذاكرة المحادثة: {conversation_id}")
        return True
    
    def delete_memory(self, conversation_id: str) -> bool:
        """
        حذف ذاكرة محادثة
        
        Args:
            conversation_id: معرف المحادثة
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود الذاكرة
        if conversation_id not in self._short_term_memory:
            logger.warning(f"الذاكرة للمحادثة {conversation_id} غير موجودة")
            return False
        
        # حذف الذاكرة
        del self._short_term_memory[conversation_id]
        del self._long_term_memory[conversation_id]
        del self._condensed_memory[conversation_id]
        
        logger.info(f"تم حذف ذاكرة المحادثة: {conversation_id}")
        return True
    
    def search_memory(self, conversation_id: str, query: str) -> Optional[List[Dict]]:
        """
        البحث في ذاكرة محادثة
        
        Args:
            conversation_id: معرف المحادثة
            query: استعلام البحث
            
        Returns:
            نتائج البحث أو None إذا لم تكن الذاكرة موجودة
        """
        # التحقق من وجود الذاكرة
        if conversation_id not in self._short_term_memory:
            logger.warning(f"الذاكرة للمحادثة {conversation_id} غير موجودة")
            return None
        
        # البحث في الذاكرة قصيرة المدى
        short_term_results = []
        for item in self._short_term_memory[conversation_id]:
            if "content" in item and isinstance(item["content"], str) and query.lower() in item["content"].lower():
                short_term_results.append(item)
        
        # البحث في الذاكرة طويلة المدى
        long_term_results = []
        for item in self._long_term_memory[conversation_id]:
            if "content" in item and isinstance(item["content"], str) and query.lower() in item["content"].lower():
                long_term_results.append(item)
        
        # دمج النتائج
        results = short_term_results + long_term_results
        
        return results
    
    def export_memory(self, conversation_id: str) -> Optional[Dict]:
        """
        تصدير ذاكرة محادثة
        
        Args:
            conversation_id: معرف المحادثة
            
        Returns:
            ذاكرة المحادثة أو None إذا لم تكن موجودة
        """
        # التحقق من وجود الذاكرة
        if conversation_id not in self._short_term_memory:
            logger.warning(f"الذاكرة للمحادثة {conversation_id} غير موجودة")
            return None
        
        return {
            "conversation_id": conversation_id,
            "short_term": self._short_term_memory[conversation_id],
            "long_term": self._long_term_memory[conversation_id],
            "condensed": self._condensed_memory[conversation_id],
            "exported_at": datetime.now().isoformat()
        }
    
    def import_memory(self, memory_data: Dict) -> bool:
        """
        استيراد ذاكرة محادثة
        
        Args:
            memory_data: بيانات الذاكرة
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود معرف المحادثة
        if "conversation_id" not in memory_data:
            logger.error("بيانات الذاكرة لا تحتوي على معرف المحادثة")
            return False
        
        conversation_id = memory_data["conversation_id"]
        
        # استيراد الذاكرة
        self._short_term_memory[conversation_id] = memory_data.get("short_term", [])
        self._long_term_memory[conversation_id] = memory_data.get("long_term", [])
        self._condensed_memory[conversation_id] = memory_data.get("condensed", {
            "summary": "",
            "key_points": [],
            "last_updated": datetime.now().isoformat()
        })
        
        logger.info(f"تم استيراد ذاكرة المحادثة: {conversation_id}")
        return True
