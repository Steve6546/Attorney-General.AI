"""
نظام توجيه الطلبات (Router) لنظام Attorney-General.AI
يوجه الطلبات إلى الوكلاء المناسبين ويدير الاستجابات
"""

import logging
import json
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime

import aiohttp

from attorney_general.controller.agent_registry import AgentRegistry
from attorney_general.controller.state_manager import StateManager
from attorney_general.events.event_stream import EventStream
from attorney_general.memory.memory_store import MemoryStore
from attorney_general.security.validator import SecurityValidator

logger = logging.getLogger("router")

class Router:
    """
    نظام توجيه الطلبات
    يوجه الطلبات إلى الوكلاء المناسبين ويدير الاستجابات
    """
    
    def __init__(self, agent_registry: AgentRegistry, event_stream: EventStream,
                state_manager: StateManager, memory_store: MemoryStore,
                security_validator: SecurityValidator):
        """
        تهيئة نظام التوجيه
        
        Args:
            agent_registry: سجل الوكلاء
            event_stream: نظام تدفق الأحداث
            state_manager: مدير الحالة
            memory_store: مخزن الذاكرة
            security_validator: محقق الأمان
        """
        self.agent_registry = agent_registry
        self.event_stream = event_stream
        self.state_manager = state_manager
        self.memory_store = memory_store
        self.security_validator = security_validator
        logger.info("تم تهيئة نظام توجيه الطلبات")
    
    async def route_to_agent(self, agent: str, payload: Any, model: str = "gpt-4", 
                           options: Dict = None) -> AsyncGenerator[Dict, None]:
        """
        توجيه الطلب إلى الوكيل المناسب
        
        Args:
            agent: اسم الوكيل
            payload: بيانات الطلب
            model: نموذج الذكاء الاصطناعي المستخدم
            options: خيارات إضافية
            
        Yields:
            استجابات الوكيل
        """
        if options is None:
            options = {}
        
        # التحقق من أمان الطلب
        security_check = self.security_validator.validate_request({
            "agent": agent,
            "payload": payload,
            "model": model,
            "options": options
        })
        
        if not security_check["safe"]:
            logger.error(f"طلب غير آمن: {json.dumps(security_check['violations'])}")
            yield {"error": f"طلب غير آمن: {', '.join(security_check['violations'])}"}
            
            # نشر حدث أمني
            self.event_stream.publish(
                event_type="security_violation",
                data={
                    "request": {
                        "agent": agent,
                        "model": model,
                        "options": options
                    },
                    "violations": security_check["violations"],
                    "details": security_check["details"]
                },
                source="router"
            )
            
            return
        
        try:
            # إنشاء معرف محادثة إذا لم يكن موجوداً
            conversation_id = options.get("conversation_id", f"conv-{int(datetime.now().timestamp())}")
            
            # إنشاء أو تحديث حالة المحادثة
            conversation = self.state_manager.get_conversation(conversation_id)
            if not conversation:
                conversation = self.state_manager.create_conversation(conversation_id, {
                    "model": model,
                    "started_at": datetime.now().isoformat(),
                    "user_info": options.get("user_info", {})
                })
            else:
                self.state_manager.update_conversation(conversation_id, {
                    "metadata": {
                        "last_activity": datetime.now().isoformat()
                    }
                })
            
            # إضافة الطلب إلى سجل الرسائل
            self.state_manager.add_message(conversation_id, {
                "role": "user",
                "content": payload,
                "timestamp": datetime.now().isoformat()
            })
            
            # إضافة الطلب إلى الذاكرة قصيرة المدى
            memory = self.memory_store.get_memory(conversation_id)
            if not memory:
                memory = self.memory_store.create_memory(conversation_id)
            
            self.memory_store.add_to_short_term_memory(conversation_id, {
                "type": "request",
                "content": payload,
                "timestamp": datetime.now().isoformat()
            })
            
            # نشر حدث بدء الطلب
            self.event_stream.publish(
                event_type="request_started",
                data={
                    "conversation_id": conversation_id,
                    "agent": agent,
                    "model": model,
                    "timestamp": datetime.now().isoformat()
                },
                source="router"
            )
            
            logger.info(f"توجيه الطلب إلى {agent} (المحادثة: {conversation_id})")
            
            # البحث عن الوكيل في السجل
            agent_info = self.agent_registry.get_agent(agent)
            
            if not agent_info:
                # إذا لم يكن الوكيل مسجلاً، نحاول استخدام التعريف القديم
                async for response in self._route_legacy_agent(agent, payload, model, options, conversation_id):
                    yield response
                return
            
            # تحديث الوكيل النشط في المحادثة
            self.state_manager.update_conversation(conversation_id, {
                "active_agent": agent
            })
            
            # تحديث نشاط الوكيل
            self.agent_registry.update_agent_activity(agent)
            
            # استدعاء الوكيل مع خيار التدفق إذا كان يدعمه
            supports_streaming = agent_info.get("supports_streaming", False)
            
            try:
                async with aiohttp.ClientSession() as session:
                    request_data = {
                        "payload": payload,
                        "model": model,
                        "options": options,
                        "stream": supports_streaming,
                        "conversation_id": conversation_id
                    }
                    
                    headers = {
                        "Authorization": f"Bearer {self._get_api_key()}",
                        "Content-Type": "application/json"
                    }
                    
                    async with session.post(
                        f"{agent_info['url']}/process",
                        json=request_data,
                        headers=headers
                    ) as response:
                        if supports_streaming:
                            # معالجة الاستجابة المتدفقة
                            async for line in response.content:
                                try:
                                    line = line.decode('utf-8').strip()
                                    if not line:
                                        continue
                                    
                                    data = json.loads(line)
                                    
                                    # إضافة الاستجابة إلى الذاكرة
                                    if "content" in data:
                                        self.memory_store.add_to_short_term_memory(conversation_id, {
                                            "type": "response_chunk",
                                            "content": data["content"],
                                            "timestamp": datetime.now().isoformat()
                                        })
                                    
                                    # نشر حدث استجابة جزئية
                                    self.event_stream.publish(
                                        event_type="response_chunk",
                                        data={
                                            "conversation_id": conversation_id,
                                            "agent": agent,
                                            "data": data,
                                            "timestamp": datetime.now().isoformat()
                                        },
                                        source="router"
                                    )
                                    
                                    yield data
                                except json.JSONDecodeError as e:
                                    logger.error(f"خطأ في تحليل البيانات المتدفقة: {e}")
                        else:
                            # معالجة الاستجابة العادية
                            data = await response.json()
                            
                            # إضافة الاستجابة إلى سجل الرسائل
                            self.state_manager.add_message(conversation_id, {
                                "role": "assistant",
                                "content": data.get("content", data),
                                "timestamp": datetime.now().isoformat()
                            })
                            
                            # إضافة الاستجابة إلى الذاكرة
                            self.memory_store.add_to_short_term_memory(conversation_id, {
                                "type": "response",
                                "content": data.get("content", data),
                                "timestamp": datetime.now().isoformat()
                            })
                            
                            # نشر حدث استجابة كاملة
                            self.event_stream.publish(
                                event_type="response_complete",
                                data={
                                    "conversation_id": conversation_id,
                                    "agent": agent,
                                    "data": data,
                                    "timestamp": datetime.now().isoformat()
                                },
                                source="router"
                            )
                            
                            yield data
                
                # تحديث حالة المحادثة بعد الانتهاء
                self.state_manager.update_conversation(conversation_id, {
                    "metadata": {
                        "last_response": datetime.now().isoformat()
                    },
                    "active_agent": None
                })
                
            except Exception as error:
                logger.error(f"خطأ في استدعاء الوكيل {agent}: {error}")
                
                # نشر حدث خطأ
                self.event_stream.publish(
                    event_type="agent_error",
                    data={
                        "conversation_id": conversation_id,
                        "agent": agent,
                        "error": str(error),
                        "timestamp": datetime.now().isoformat()
                    },
                    source="router"
                )
                
                yield {"error": f"حدث خطأ أثناء معالجة الطلب: {error}"}
        
        except Exception as error:
            logger.error(f"خطأ في توجيه الطلب: {error}")
            yield {"error": f"حدث خطأ أثناء معالجة الطلب: {error}"}
    
    async def _route_legacy_agent(self, agent: str, payload: Any, model: str,
                                options: Dict, conversation_id: str) -> AsyncGenerator[Dict, None]:
        """
        توجيه الطلب إلى الوكيل باستخدام النظام القديم
        للحفاظ على التوافق مع الإصدارات السابقة
        
        Args:
            agent: اسم الوكيل
            payload: بيانات الطلب
            model: نموذج الذكاء الاصطناعي المستخدم
            options: خيارات إضافية
            conversation_id: معرف المحادثة
            
        Yields:
            استجابات الوكيل
        """
        # تعريف عناوين الوكلاء القديمة
        AGENT_URLS = {
            "ThinkerAgent": "http://thinker:3001",
            "SearchAgent": "http://search:3002",
            "FileAgent": "http://file:5002",
            "AuthAgent": "http://auth:3003",
            "NotifyAgent": "http://notify:3004"
        }
        
        if not agent or agent not in AGENT_URLS:
            yield {"error": f"الوكيل غير معروف: {agent}"}
            return
        
        try:
            logger.info(f"توجيه الطلب إلى {agent} باستخدام النظام القديم")
            
            # نشر حدث استخدام النظام القديم
            self.event_stream.publish(
                event_type="legacy_system_used",
                data={
                    "conversation_id": conversation_id,
                    "agent": agent,
                    "timestamp": datetime.now().isoformat()
                },
                source="router"
            )
            
            # إذا كان الوكيل يدعم الاستجابة المتدفقة
            supports_streaming = agent in ["ThinkerAgent", "SearchAgent"]
            
            async with aiohttp.ClientSession() as session:
                request_data = {
                    "payload": payload,
                    "model": model,
                    "options": options
                }
                
                if supports_streaming:
                    request_data["stream"] = True
                
                headers = {
                    "Authorization": f"Bearer {self._get_api_key()}",
                    "Content-Type": "application/json"
                }
                
                async with session.post(
                    f"{AGENT_URLS[agent]}/process",
                    json=request_data,
                    headers=headers
                ) as response:
                    if supports_streaming:
                        # معالجة الاستجابة المتدفقة
                        async for line in response.content:
                            try:
                                line = line.decode('utf-8').strip()
                                if not line:
                                    continue
                                
                                data = json.loads(line)
                                
                                # إضافة الاستجابة إلى الذاكرة
                                if "content" in data:
                                    self.memory_store.add_to_short_term_memory(conversation_id, {
                                        "type": "legacy_response_chunk",
                                        "content": data["content"],
                                        "timestamp": datetime.now().isoformat()
                                    })
                                
                                yield data
                            except json.JSONDecodeError as e:
                                logger.error(f"خطأ في تحليل البيانات المتدفقة: {e}")
                    else:
                        # معالجة الاستجابة العادية
                        data = await response.json()
                        
                        # إضافة الاستجابة إلى الذاكرة
                        self.memory_store.add_to_short_term_memory(conversation_id, {
                            "type": "legacy_response",
                            "content": data,
                            "timestamp": datetime.now().isoformat()
                        })
                        
                        yield data
        
        except Exception as error:
            logger.error(f"خطأ في توجيه الطلب إلى {agent} باستخدام النظام القديم: {error}")
            yield {"error": f"حدث خطأ أثناء معالجة الطلب: {error}"}
    
    def _get_api_key(self) -> str:
        """الحصول على مفتاح API"""
        import os
        return os.environ.get("OPENROUTER_API_KEY", "default_key_for_development")
