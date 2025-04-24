"""
نظام تكثيف الذاكرة (Memory Condenser) لنظام Attorney-General.AI
يقوم بتكثيف وتلخيص محتويات الذاكرة
"""

import logging
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

import openai

logger = logging.getLogger("memory_condenser")

class MemoryCondenser:
    """
    نظام تكثيف الذاكرة
    يقوم بتكثيف وتلخيص محتويات الذاكرة
    """
    
    def __init__(self, api_key: str = None):
        """
        تهيئة نظام تكثيف الذاكرة
        
        Args:
            api_key: مفتاح API لخدمة الذكاء الاصطناعي
        """
        # إعداد مفتاح API
        self.api_key = api_key or self._get_api_key_from_env()
        
        # إعداد العميل
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
        
        logger.info("تم تهيئة نظام تكثيف الذاكرة")
    
    async def condense_memory(self, memory_items: List[Dict], max_tokens: int = 2000) -> Dict:
        """
        تكثيف عناصر الذاكرة
        
        Args:
            memory_items: عناصر الذاكرة
            max_tokens: الحد الأقصى لعدد الرموز
            
        Returns:
            الذاكرة المكثفة
        """
        if not memory_items:
            return {
                "summary": "",
                "key_points": [],
                "last_updated": datetime.now().isoformat()
            }
        
        # استخراج المحتوى من عناصر الذاكرة
        memory_content = []
        
        for item in memory_items:
            if "content" in item and item["content"]:
                if isinstance(item["content"], str):
                    memory_content.append(item["content"])
                elif isinstance(item["content"], dict) and "content" in item["content"]:
                    memory_content.append(item["content"]["content"])
        
        # دمج المحتوى
        combined_content = "\n\n".join(memory_content)
        
        # إذا كان المحتوى فارغاً
        if not combined_content.strip():
            return {
                "summary": "",
                "key_points": [],
                "last_updated": datetime.now().isoformat()
            }
        
        try:
            # إنشاء ملخص
            summary = await self._generate_summary(combined_content, max_tokens)
            
            # استخراج النقاط الرئيسية
            key_points = await self._extract_key_points(combined_content, max_tokens)
            
            return {
                "summary": summary,
                "key_points": key_points,
                "last_updated": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"خطأ في تكثيف الذاكرة: {e}")
            
            # إرجاع ذاكرة مكثفة فارغة في حالة الخطأ
            return {
                "summary": "",
                "key_points": [],
                "last_updated": datetime.now().isoformat(),
                "error": str(e)
            }
    
    async def _generate_summary(self, content: str, max_tokens: int) -> str:
        """
        إنشاء ملخص للمحتوى
        
        Args:
            content: المحتوى
            max_tokens: الحد الأقصى لعدد الرموز
            
        Returns:
            الملخص
        """
        # إعداد رسائل المحادثة
        messages = [
            {
                "role": "system",
                "content": "أنت مساعد مفيد متخصص في تلخيص المحادثات. قم بتلخيص المحتوى التالي بشكل موجز ودقيق."
            },
            {
                "role": "user",
                "content": f"قم بتلخيص المحتوى التالي في فقرة واحدة موجزة:\n\n{content}"
            }
        ]
        
        # استدعاء النموذج
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=max_tokens // 2,
            temperature=0.3
        )
        
        # استخراج الملخص
        summary = response.choices[0].message.content.strip()
        
        return summary
    
    async def _extract_key_points(self, content: str, max_tokens: int) -> List[str]:
        """
        استخراج النقاط الرئيسية من المحتوى
        
        Args:
            content: المحتوى
            max_tokens: الحد الأقصى لعدد الرموز
            
        Returns:
            النقاط الرئيسية
        """
        # إعداد رسائل المحادثة
        messages = [
            {
                "role": "system",
                "content": "أنت مساعد مفيد متخصص في استخراج النقاط الرئيسية من المحادثات. قم باستخراج النقاط الرئيسية من المحتوى التالي."
            },
            {
                "role": "user",
                "content": f"استخرج 3-5 نقاط رئيسية من المحتوى التالي. قدم كل نقطة في جملة واحدة موجزة:\n\n{content}"
            }
        ]
        
        # استدعاء النموذج
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=max_tokens // 2,
            temperature=0.3
        )
        
        # استخراج النقاط الرئيسية
        key_points_text = response.choices[0].message.content.strip()
        
        # تحويل النص إلى قائمة
        key_points = []
        
        for line in key_points_text.split("\n"):
            # إزالة الترقيم والمسافات الزائدة
            clean_line = line.strip()
            if clean_line:
                # إزالة الترقيم في بداية السطر (مثل "1. " أو "- ")
                if clean_line[0].isdigit() and len(clean_line) > 2 and clean_line[1:3] in [". ", "- "]:
                    clean_line = clean_line[3:].strip()
                elif clean_line[0] == "-" and len(clean_line) > 2:
                    clean_line = clean_line[1:].strip()
                
                key_points.append(clean_line)
        
        return key_points
    
    def _get_api_key_from_env(self) -> str:
        """
        الحصول على مفتاح API من متغيرات البيئة
        
        Returns:
            مفتاح API
        """
        import os
        return os.environ.get("OPENAI_API_KEY", "default_key_for_development")
