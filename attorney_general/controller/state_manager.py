"""
نظام إدارة الحالة (State Manager) لنظام Attorney-General.AI
يدير حالة المحادثات والسياق والرسائل
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger("state_manager")

class StateManager:
    """
    نظام إدارة الحالة
    يدير حالة المحادثات والسياق والرسائل
    """
    
    def __init__(self):
        """تهيئة مدير الحالة"""
        self._conversations = {}  # قاموس لتخزين المحادثات
        self._messages = {}  # قاموس لتخزين الرسائل
        self._contexts = {}  # قاموس لتخزين السياق
        logger.info("تم تهيئة مدير الحالة")
    
    def create_conversation(self, conversation_id: str, metadata: Dict = None) -> Dict:
        """
        إنشاء محادثة جديدة
        
        Args:
            conversation_id: معرف المحادثة
            metadata: بيانات وصفية للمحادثة
            
        Returns:
            معلومات المحادثة
        """
        if metadata is None:
            metadata = {}
            
        # التحقق من عدم وجود المحادثة مسبقاً
        if conversation_id in self._conversations:
            logger.warning(f"المحادثة {conversation_id} موجودة مسبقاً")
            return self._conversations[conversation_id]
        
        # إنشاء المحادثة
        self._conversations[conversation_id] = {
            "id": conversation_id,
            "state": "active",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "active_agent": None,
            "metadata": metadata
        }
        
        # إنشاء قائمة رسائل فارغة
        self._messages[conversation_id] = []
        
        # إنشاء سياق فارغ
        self._contexts[conversation_id] = {}
        
        logger.info(f"تم إنشاء محادثة جديدة: {conversation_id}")
        return self._conversations[conversation_id]
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        الحصول على معلومات محادثة
        
        Args:
            conversation_id: معرف المحادثة
            
        Returns:
            معلومات المحادثة أو None إذا لم تكن موجودة
        """
        return self._conversations.get(conversation_id)
    
    def update_conversation(self, conversation_id: str, updates: Dict) -> Optional[Dict]:
        """
        تحديث معلومات محادثة
        
        Args:
            conversation_id: معرف المحادثة
            updates: التحديثات المطلوبة
            
        Returns:
            معلومات المحادثة المحدثة أو None إذا لم تكن موجودة
        """
        # التحقق من وجود المحادثة
        if conversation_id not in self._conversations:
            logger.warning(f"المحادثة {conversation_id} غير موجودة")
            return None
        
        # تحديث المحادثة
        conversation = self._conversations[conversation_id]
        
        if "state" in updates:
            conversation["state"] = updates["state"]
        
        if "active_agent" in updates:
            conversation["active_agent"] = updates["active_agent"]
        
        if "metadata" in updates:
            if isinstance(updates["metadata"], dict):
                conversation["metadata"].update(updates["metadata"])
            else:
                conversation["metadata"] = updates["metadata"]
        
        # تحديث وقت التحديث
        conversation["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"تم تحديث المحادثة: {conversation_id}")
        return conversation
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        حذف محادثة
        
        Args:
            conversation_id: معرف المحادثة
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود المحادثة
        if conversation_id not in self._conversations:
            logger.warning(f"المحادثة {conversation_id} غير موجودة")
            return False
        
        # حذف المحادثة
        del self._conversations[conversation_id]
        
        # حذف الرسائل
        if conversation_id in self._messages:
            del self._messages[conversation_id]
        
        # حذف السياق
        if conversation_id in self._contexts:
            del self._contexts[conversation_id]
        
        logger.info(f"تم حذف المحادثة: {conversation_id}")
        return True
    
    def get_active_conversations(self) -> List[str]:
        """
        الحصول على قائمة المحادثات النشطة
        
        Returns:
            قائمة معرفات المحادثات النشطة
        """
        active_conversations = []
        
        for conversation_id, conversation in self._conversations.items():
            if conversation["state"] == "active":
                active_conversations.append(conversation_id)
        
        return active_conversations
    
    def add_message(self, conversation_id: str, message: Dict) -> bool:
        """
        إضافة رسالة إلى محادثة
        
        Args:
            conversation_id: معرف المحادثة
            message: الرسالة
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود المحادثة
        if conversation_id not in self._conversations:
            logger.warning(f"المحادثة {conversation_id} غير موجودة")
            return False
        
        # التحقق من وجود قائمة الرسائل
        if conversation_id not in self._messages:
            self._messages[conversation_id] = []
        
        # إضافة الرسالة
        self._messages[conversation_id].append(message)
        
        # تحديث وقت تحديث المحادثة
        self._conversations[conversation_id]["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"تم إضافة رسالة إلى المحادثة: {conversation_id}")
        return True
    
    def get_messages(self, conversation_id: str, limit: int = 50, offset: int = 0) -> Optional[List[Dict]]:
        """
        الحصول على رسائل محادثة
        
        Args:
            conversation_id: معرف المحادثة
            limit: عدد الرسائل المطلوبة
            offset: بداية الرسائل
            
        Returns:
            قائمة الرسائل أو None إذا لم تكن المحادثة موجودة
        """
        # التحقق من وجود المحادثة
        if conversation_id not in self._conversations:
            logger.warning(f"المحادثة {conversation_id} غير موجودة")
            return None
        
        # التحقق من وجود قائمة الرسائل
        if conversation_id not in self._messages:
            return []
        
        # الحصول على الرسائل
        messages = self._messages[conversation_id]
        
        # تطبيق الحد والإزاحة
        return messages[offset:offset + limit]
    
    def set_context(self, conversation_id: str, context: Dict) -> bool:
        """
        تعيين سياق محادثة
        
        Args:
            conversation_id: معرف المحادثة
            context: السياق
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود المحادثة
        if conversation_id not in self._conversations:
            logger.warning(f"المحادثة {conversation_id} غير موجودة")
            return False
        
        # تعيين السياق
        self._contexts[conversation_id] = context
        
        # تحديث وقت تحديث المحادثة
        self._conversations[conversation_id]["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"تم تعيين سياق المحادثة: {conversation_id}")
        return True
    
    def get_context(self, conversation_id: str) -> Optional[Dict]:
        """
        الحصول على سياق محادثة
        
        Args:
            conversation_id: معرف المحادثة
            
        Returns:
            السياق أو None إذا لم تكن المحادثة موجودة
        """
        # التحقق من وجود المحادثة
        if conversation_id not in self._conversations:
            logger.warning(f"المحادثة {conversation_id} غير موجودة")
            return None
        
        # التحقق من وجود السياق
        if conversation_id not in self._contexts:
            self._contexts[conversation_id] = {}
        
        return self._contexts[conversation_id]
    
    def update_context(self, conversation_id: str, updates: Dict) -> Optional[Dict]:
        """
        تحديث سياق محادثة
        
        Args:
            conversation_id: معرف المحادثة
            updates: التحديثات المطلوبة
            
        Returns:
            السياق المحدث أو None إذا لم تكن المحادثة موجودة
        """
        # التحقق من وجود المحادثة
        if conversation_id not in self._conversations:
            logger.warning(f"المحادثة {conversation_id} غير موجودة")
            return None
        
        # التحقق من وجود السياق
        if conversation_id not in self._contexts:
            self._contexts[conversation_id] = {}
        
        # تحديث السياق
        self._contexts[conversation_id].update(updates)
        
        # تحديث وقت تحديث المحادثة
        self._conversations[conversation_id]["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"تم تحديث سياق المحادثة: {conversation_id}")
        return self._contexts[conversation_id]
    
    def export_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        تصدير محادثة كاملة مع الرسائل والسياق
        
        Args:
            conversation_id: معرف المحادثة
            
        Returns:
            المحادثة الكاملة أو None إذا لم تكن موجودة
        """
        # التحقق من وجود المحادثة
        if conversation_id not in self._conversations:
            logger.warning(f"المحادثة {conversation_id} غير موجودة")
            return None
        
        # تجميع المحادثة
        conversation = self._conversations[conversation_id].copy()
        conversation["messages"] = self._messages.get(conversation_id, [])
        conversation["context"] = self._contexts.get(conversation_id, {})
        
        return conversation
    
    def import_conversation(self, conversation_data: Dict) -> bool:
        """
        استيراد محادثة كاملة
        
        Args:
            conversation_data: بيانات المحادثة
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود معرف المحادثة
        if "id" not in conversation_data:
            logger.error("بيانات المحادثة لا تحتوي على معرف")
            return False
        
        conversation_id = conversation_data["id"]
        
        # استيراد المحادثة
        self._conversations[conversation_id] = {
            "id": conversation_id,
            "state": conversation_data.get("state", "active"),
            "created_at": conversation_data.get("created_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat(),
            "active_agent": conversation_data.get("active_agent"),
            "metadata": conversation_data.get("metadata", {})
        }
        
        # استيراد الرسائل
        self._messages[conversation_id] = conversation_data.get("messages", [])
        
        # استيراد السياق
        self._contexts[conversation_id] = conversation_data.get("context", {})
        
        logger.info(f"تم استيراد المحادثة: {conversation_id}")
        return True
