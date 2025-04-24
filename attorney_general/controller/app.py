"""
وحدة التحكم الرئيسية (Controller) لنظام Attorney-General.AI
تعمل كنقطة الدخول الرئيسية للتطبيق وتدير تدفق العمل
"""

import logging
import os
from typing import Dict, List, Optional, Union, Any

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

# استيراد المكونات الداخلية
from attorney_general.controller.agent_registry import AgentRegistry
from attorney_general.controller.router import Router
from attorney_general.controller.state_manager import StateManager
from attorney_general.events.event_stream import EventStream, EventStreamSubscriber
from attorney_general.memory.memory_store import MemoryStore
from attorney_general.security.validator import SecurityValidator

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("attorney_general.log")
    ]
)
logger = logging.getLogger("controller")

class Controller:
    """
    وحدة التحكم الرئيسية للنظام
    تدير تدفق العمل وتوزيع المهام بين الوكلاء
    """
    
    def __init__(self):
        """تهيئة وحدة التحكم والمكونات الأساسية"""
        logger.info("بدء تهيئة وحدة التحكم")
        
        # إنشاء مكونات النظام الأساسية
        self.agent_registry = AgentRegistry()
        self.event_stream = EventStream()
        self.state_manager = StateManager()
        self.memory_store = MemoryStore()
        self.security_validator = SecurityValidator()
        self.router = Router(
            agent_registry=self.agent_registry,
            event_stream=self.event_stream,
            state_manager=self.state_manager,
            memory_store=self.memory_store,
            security_validator=self.security_validator
        )
        
        # تسجيل الوكلاء الافتراضيين
        self._register_default_agents()
        
        # تهيئة نظام الأحداث
        self._initialize_event_system()
        
        # تهيئة نظام الذاكرة
        self._initialize_memory_system()
        
        logger.info("اكتملت تهيئة وحدة التحكم")
    
    def _register_default_agents(self):
        """تسجيل الوكلاء الافتراضيين في النظام"""
        logger.info("تسجيل الوكلاء الافتراضيين")
        
        # تسجيل وكيل التفكير
        self.agent_registry.register_agent(
            agent_id="thinker",
            name="Thinker Agent",
            url="http://localhost:3001",
            capabilities=["thinking", "reasoning", "planning"],
            supports_streaming=True
        )
        
        # تسجيل وكيل البحث
        self.agent_registry.register_agent(
            agent_id="search",
            name="Search Agent",
            url="http://localhost:3002",
            capabilities=["search", "information_retrieval"],
            supports_streaming=True
        )
        
        # تسجيل وكيل الملفات
        self.agent_registry.register_agent(
            agent_id="file",
            name="File Agent",
            url="http://localhost:5002",
            capabilities=["file_management", "document_processing"],
            supports_streaming=False
        )
        
        # تسجيل وكيل المصادقة
        self.agent_registry.register_agent(
            agent_id="auth",
            name="Auth Agent",
            url="http://localhost:3003",
            capabilities=["authentication", "authorization"],
            supports_streaming=False
        )
        
        # تسجيل وكيل الإشعارات
        self.agent_registry.register_agent(
            agent_id="notify",
            name="Notification Agent",
            url="http://localhost:3004",
            capabilities=["notifications", "alerts"],
            supports_streaming=False
        )
    
    def _initialize_event_system(self):
        """تهيئة نظام الأحداث"""
        logger.info("تهيئة نظام الأحداث")
        
        # تسجيل مستمع للأحداث للتسجيل
        self.event_stream.subscribe(
            subscriber=EventStreamSubscriber.LOGGER,
            callback=lambda event: logger.debug(f"حدث: {event.type} من المصدر: {event.source}"),
            subscriber_id="event_logger",
            event_types=["*"]  # الاشتراك في جميع أنواع الأحداث
        )
    
    def _initialize_memory_system(self):
        """تهيئة نظام الذاكرة"""
        logger.info("تهيئة نظام الذاكرة")
        
        # تسجيل مستمع لأحداث بدء المحادثات لإنشاء ذاكرة جديدة
        self.event_stream.subscribe(
            subscriber=EventStreamSubscriber.CONTROLLER,
            callback=self._handle_conversation_start,
            subscriber_id="memory_initializer",
            event_types=["request_started"]
        )
    
    def _handle_conversation_start(self, event):
        """معالجة حدث بدء محادثة جديدة"""
        if event.type == "request_started" and event.data.get("conversation_id"):
            conversation_id = event.data["conversation_id"]
            
            # التحقق مما إذا كانت المحادثة موجودة في نظام الذاكرة
            if not self.memory_store.get_memory(conversation_id):
                # إنشاء ذاكرة جديدة
                self.memory_store.create_memory(conversation_id)
                logger.info(f"تم تهيئة نظام الذاكرة للمحادثة: {conversation_id}")
    
    async def process_request(self, agent: str, payload: Any, model: str = "gpt-4", options: Dict = None) -> Any:
        """
        معالجة طلب وتوجيهه إلى الوكيل المناسب
        
        Args:
            agent: اسم الوكيل المطلوب
            payload: بيانات الطلب
            model: نموذج الذكاء الاصطناعي المستخدم
            options: خيارات إضافية
            
        Returns:
            استجابة الوكيل
        """
        if options is None:
            options = {}
            
        # نشر حدث استلام طلب
        self.event_stream.publish(
            event_type="request_received",
            data={
                "agent": agent,
                "timestamp": self._get_timestamp()
            },
            source="controller"
        )
        
        # توجيه الطلب إلى الوكيل المناسب
        return await self.router.route_to_agent(
            agent=agent,
            payload=payload,
            model=model,
            options=options
        )
    
    def _get_timestamp(self) -> str:
        """الحصول على الطابع الزمني الحالي"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_active_conversations(self) -> List[str]:
        """الحصول على قائمة المحادثات النشطة"""
        return self.state_manager.get_active_conversations()
    
    def get_registered_agents(self) -> Dict:
        """الحصول على قائمة الوكلاء المسجلين"""
        return self.agent_registry.get_all_agents()
    
    def get_system_status(self) -> Dict:
        """الحصول على حالة النظام"""
        return {
            "status": "ok",
            "version": "2.0.0",
            "agents": list(self.agent_registry.get_all_agents().keys()),
            "active_conversations": len(self.state_manager.get_active_conversations())
        }

# إنشاء نسخة واحدة من وحدة التحكم للاستخدام في جميع أنحاء التطبيق
controller = Controller()
