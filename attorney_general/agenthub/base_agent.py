"""
الوكيل الأساسي (Base Agent) لنظام Attorney-General.AI
يوفر الوظائف الأساسية المشتركة بين جميع الوكلاء
"""

import logging
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncGenerator

logger = logging.getLogger("base_agent")

class BaseAgent(ABC):
    """
    الوكيل الأساسي
    فئة مجردة توفر الوظائف الأساسية المشتركة بين جميع الوكلاء
    """
    
    def __init__(self, agent_id: str, name: str):
        """
        تهيئة الوكيل الأساسي
        
        Args:
            agent_id: معرف الوكيل
            name: اسم الوكيل
        """
        self.agent_id = agent_id
        self.name = name
        self.capabilities = []
        self.supports_streaming = False
        logger.info(f"تم تهيئة الوكيل الأساسي: {name} ({agent_id})")
    
    @abstractmethod
    async def process(self, payload: Any, model: str = "gpt-4", 
                    options: Dict = None) -> AsyncGenerator[Dict, None]:
        """
        معالجة الطلب
        
        Args:
            payload: بيانات الطلب
            model: نموذج الذكاء الاصطناعي المستخدم
            options: خيارات إضافية
            
        Yields:
            استجابات الوكيل
        """
        pass
    
    async def initialize(self) -> bool:
        """
        تهيئة الوكيل
        
        Returns:
            نجاح العملية
        """
        logger.info(f"تهيئة الوكيل: {self.name}")
        return True
    
    async def shutdown(self) -> bool:
        """
        إيقاف الوكيل
        
        Returns:
            نجاح العملية
        """
        logger.info(f"إيقاف الوكيل: {self.name}")
        return True
    
    def get_info(self) -> Dict:
        """
        الحصول على معلومات الوكيل
        
        Returns:
            معلومات الوكيل
        """
        return {
            "id": self.agent_id,
            "name": self.name,
            "capabilities": self.capabilities,
            "supports_streaming": self.supports_streaming
        }
    
    def add_capability(self, capability: str) -> bool:
        """
        إضافة قدرة للوكيل
        
        Args:
            capability: القدرة المراد إضافتها
            
        Returns:
            نجاح العملية
        """
        if capability in self.capabilities:
            logger.warning(f"القدرة {capability} موجودة مسبقاً للوكيل {self.name}")
            return False
        
        self.capabilities.append(capability)
        logger.info(f"تم إضافة القدرة {capability} للوكيل {self.name}")
        return True
    
    def has_capability(self, capability: str) -> bool:
        """
        التحقق مما إذا كان الوكيل يملك قدرة معينة
        
        Args:
            capability: القدرة المراد التحقق منها
            
        Returns:
            ما إذا كان الوكيل يملك القدرة
        """
        return capability in self.capabilities
    
    def _log_request(self, payload: Any, model: str, options: Dict) -> None:
        """
        تسجيل الطلب
        
        Args:
            payload: بيانات الطلب
            model: نموذج الذكاء الاصطناعي المستخدم
            options: خيارات إضافية
        """
        logger.info(f"طلب جديد للوكيل {self.name} باستخدام النموذج {model}")
        
        if isinstance(payload, str) and len(payload) > 100:
            logger.debug(f"البيانات: {payload[:100]}...")
        else:
            logger.debug(f"البيانات: {payload}")
        
        logger.debug(f"الخيارات: {options}")
    
    def _log_response(self, response: Dict) -> None:
        """
        تسجيل الاستجابة
        
        Args:
            response: استجابة الوكيل
        """
        if "content" in response and isinstance(response["content"], str) and len(response["content"]) > 100:
            logger.debug(f"الاستجابة: {response['content'][:100]}...")
        else:
            logger.debug(f"الاستجابة: {response}")
    
    def _get_conversation_id(self, options: Dict) -> str:
        """
        الحصول على معرف المحادثة
        
        Args:
            options: خيارات الطلب
            
        Returns:
            معرف المحادثة
        """
        from datetime import datetime
        
        return options.get("conversation_id", f"conv-{int(datetime.now().timestamp())}")
