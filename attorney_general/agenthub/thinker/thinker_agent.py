"""
وكيل التفكير (Thinker Agent) لنظام Attorney-General.AI
مسؤول عن التفكير والاستدلال والتخطيط
"""

import logging
import json
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator

import aiohttp
import openai

from attorney_general.agenthub.base_agent import BaseAgent

logger = logging.getLogger("thinker_agent")

class ThinkerAgent(BaseAgent):
    """
    وكيل التفكير
    مسؤول عن التفكير والاستدلال والتخطيط
    """
    
    def __init__(self, api_key: str = None):
        """
        تهيئة وكيل التفكير
        
        Args:
            api_key: مفتاح API لخدمة الذكاء الاصطناعي
        """
        super().__init__(agent_id="thinker", name="Thinker Agent")
        
        # إضافة القدرات
        self.capabilities = ["thinking", "reasoning", "planning", "analysis"]
        self.supports_streaming = True
        
        # إعداد مفتاح API
        self.api_key = api_key or self._get_api_key_from_env()
        
        # إعداد العميل
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
        
        logger.info("تم تهيئة وكيل التفكير")
    
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
        if options is None:
            options = {}
        
        # تسجيل الطلب
        self._log_request(payload, model, options)
        
        # الحصول على معرف المحادثة
        conversation_id = self._get_conversation_id(options)
        
        # التحقق من نوع البيانات
        if not isinstance(payload, str):
            try:
                payload = json.dumps(payload)
            except Exception as e:
                logger.error(f"خطأ في تحويل البيانات إلى نص: {e}")
                yield {"error": f"خطأ في تحويل البيانات إلى نص: {e}"}
                return
        
        # إعداد سياق المحادثة
        context = options.get("context", [])
        
        # إعداد رسائل المحادثة
        messages = []
        
        # إضافة السياق إلى الرسائل
        for message in context:
            messages.append({
                "role": message.get("role", "user"),
                "content": message.get("content", "")
            })
        
        # إضافة الرسالة الحالية
        messages.append({
            "role": "user",
            "content": payload
        })
        
        try:
            # التحقق من خيار التدفق
            stream = options.get("stream", True)
            
            if stream:
                # استدعاء النموذج مع التدفق
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=True,
                    temperature=options.get("temperature", 0.7),
                    max_tokens=options.get("max_tokens", 4000)
                )
                
                # معالجة الاستجابة المتدفقة
                full_content = ""
                
                async for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content_chunk = chunk.choices[0].delta.content
                        full_content += content_chunk
                        
                        # إرجاع الجزء
                        chunk_response = {
                            "content": content_chunk,
                            "full_content": full_content,
                            "finished": False
                        }
                        
                        self._log_response(chunk_response)
                        yield chunk_response
                
                # إرجاع الاستجابة النهائية
                final_response = {
                    "content": full_content,
                    "finished": True
                }
                
                self._log_response(final_response)
                yield final_response
            else:
                # استدعاء النموذج بدون تدفق
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=False,
                    temperature=options.get("temperature", 0.7),
                    max_tokens=options.get("max_tokens", 4000)
                )
                
                # إرجاع الاستجابة
                content = response.choices[0].message.content
                
                response_data = {
                    "content": content,
                    "finished": True
                }
                
                self._log_response(response_data)
                yield response_data
        
        except Exception as e:
            logger.error(f"خطأ في استدعاء النموذج: {e}")
            yield {"error": f"خطأ في استدعاء النموذج: {e}"}
    
    def _get_api_key_from_env(self) -> str:
        """
        الحصول على مفتاح API من متغيرات البيئة
        
        Returns:
            مفتاح API
        """
        import os
        return os.environ.get("OPENAI_API_KEY", "default_key_for_development")
