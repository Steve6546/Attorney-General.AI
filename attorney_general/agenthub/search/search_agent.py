"""
وكيل البحث (Search Agent) لنظام Attorney-General.AI
مسؤول عن البحث واسترجاع المعلومات
"""

import logging
import json
import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
import re
import aiohttp

from attorney_general.agenthub.base_agent import BaseAgent

logger = logging.getLogger("search_agent")

class SearchAgent(BaseAgent):
    """
    وكيل البحث
    مسؤول عن البحث واسترجاع المعلومات
    """
    
    def __init__(self, search_api_key: str = None):
        """
        تهيئة وكيل البحث
        
        Args:
            search_api_key: مفتاح API لخدمة البحث
        """
        super().__init__(agent_id="search", name="Search Agent")
        
        # إضافة القدرات
        self.capabilities = ["search", "information_retrieval", "web_search", "fact_checking"]
        self.supports_streaming = True
        
        # إعداد مفتاح API
        self.search_api_key = search_api_key or self._get_api_key_from_env()
        
        # إعداد عناوين API
        self.search_endpoint = "https://api.search.com/v1/search"
        
        logger.info("تم تهيئة وكيل البحث")
    
    async def process(self, payload: Any, model: str = "gpt-4", 
                    options: Dict = None) -> AsyncGenerator[Dict, None]:
        """
        معالجة الطلب
        
        Args:
            payload: بيانات الطلب (استعلام البحث)
            model: نموذج الذكاء الاصطناعي المستخدم (غير مستخدم في هذا الوكيل)
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
        
        # استخراج استعلام البحث
        search_query = self._extract_search_query(payload)
        
        if not search_query:
            logger.error("لم يتم العثور على استعلام بحث صالح")
            yield {"error": "لم يتم العثور على استعلام بحث صالح"}
            return
        
        try:
            # إجراء البحث
            search_results = await self._perform_search(search_query, options)
            
            # التحقق من خيار التدفق
            stream = options.get("stream", True)
            
            if stream:
                # إرسال النتائج بشكل متدفق
                for i, result in enumerate(search_results):
                    # إرجاع النتيجة
                    result_response = {
                        "content": json.dumps(result),
                        "type": "search_result",
                        "index": i,
                        "total": len(search_results),
                        "finished": False
                    }
                    
                    self._log_response(result_response)
                    yield result_response
                    
                    # انتظار قصير بين النتائج
                    await asyncio.sleep(0.1)
                
                # إرجاع الاستجابة النهائية
                final_response = {
                    "content": json.dumps(search_results),
                    "type": "search_results",
                    "total": len(search_results),
                    "finished": True
                }
                
                self._log_response(final_response)
                yield final_response
            else:
                # إرجاع جميع النتائج دفعة واحدة
                response_data = {
                    "content": json.dumps(search_results),
                    "type": "search_results",
                    "total": len(search_results),
                    "finished": True
                }
                
                self._log_response(response_data)
                yield response_data
        
        except Exception as e:
            logger.error(f"خطأ في إجراء البحث: {e}")
            yield {"error": f"خطأ في إجراء البحث: {e}"}
    
    def _extract_search_query(self, text: str) -> str:
        """
        استخراج استعلام البحث من النص
        
        Args:
            text: النص المراد استخراج استعلام البحث منه
            
        Returns:
            استعلام البحث
        """
        # البحث عن أنماط استعلام البحث
        patterns = [
            r"ابحث عن\s+(.+)",
            r"بحث\s+(.+)",
            r"search for\s+(.+)",
            r"search\s+(.+)",
            r"find\s+(.+)",
            r"lookup\s+(.+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # إذا لم يتم العثور على نمط، استخدم النص كاملاً
        return text.strip()
    
    async def _perform_search(self, query: str, options: Dict) -> List[Dict]:
        """
        إجراء البحث
        
        Args:
            query: استعلام البحث
            options: خيارات إضافية
            
        Returns:
            نتائج البحث
        """
        # في بيئة الإنتاج، هذا سيستخدم API بحث حقيقي
        # لأغراض التطوير، نستخدم نتائج وهمية
        
        # محاكاة استدعاء API
        await asyncio.sleep(1)
        
        # إنشاء نتائج وهمية
        results = [
            {
                "title": f"نتيجة بحث 1 لـ '{query}'",
                "url": "https://example.com/result1",
                "snippet": f"هذه هي نتيجة البحث الأولى لاستعلام '{query}'. تحتوي على معلومات مفيدة حول الموضوع."
            },
            {
                "title": f"نتيجة بحث 2 لـ '{query}'",
                "url": "https://example.com/result2",
                "snippet": f"هذه هي نتيجة البحث الثانية لاستعلام '{query}'. تحتوي على معلومات إضافية حول الموضوع."
            },
            {
                "title": f"نتيجة بحث 3 لـ '{query}'",
                "url": "https://example.com/result3",
                "snippet": f"هذه هي نتيجة البحث الثالثة لاستعلام '{query}'. تحتوي على معلومات متخصصة حول الموضوع."
            }
        ]
        
        return results
    
    async def _call_search_api(self, query: str, options: Dict) -> Dict:
        """
        استدعاء API البحث
        
        Args:
            query: استعلام البحث
            options: خيارات إضافية
            
        Returns:
            استجابة API البحث
        """
        # إعداد معلمات البحث
        params = {
            "q": query,
            "limit": options.get("limit", 10),
            "offset": options.get("offset", 0)
        }
        
        # إضافة معلمات إضافية
        if "filters" in options:
            params["filters"] = json.dumps(options["filters"])
        
        # إعداد الرؤوس
        headers = {
            "Authorization": f"Bearer {self.search_api_key}",
            "Content-Type": "application/json"
        }
        
        # استدعاء API
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.search_endpoint,
                params=params,
                headers=headers
            ) as response:
                return await response.json()
    
    def _get_api_key_from_env(self) -> str:
        """
        الحصول على مفتاح API من متغيرات البيئة
        
        Returns:
            مفتاح API
        """
        import os
        return os.environ.get("SEARCH_API_KEY", "default_key_for_development")
