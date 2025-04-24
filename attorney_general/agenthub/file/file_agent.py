"""
وكيل الملفات (File Agent) لنظام Attorney-General.AI
مسؤول عن إدارة الملفات ومعالجة المستندات
"""

import logging
import json
import asyncio
import os
import base64
from typing import Dict, List, Optional, Any, AsyncGenerator
import mimetypes

from attorney_general.agenthub.base_agent import BaseAgent

logger = logging.getLogger("file_agent")

class FileAgent(BaseAgent):
    """
    وكيل الملفات
    مسؤول عن إدارة الملفات ومعالجة المستندات
    """
    
    def __init__(self, storage_path: str = None):
        """
        تهيئة وكيل الملفات
        
        Args:
            storage_path: مسار التخزين الافتراضي
        """
        super().__init__(agent_id="file", name="File Agent")
        
        # إضافة القدرات
        self.capabilities = ["file_management", "document_processing", "file_conversion", "file_storage"]
        self.supports_streaming = False
        
        # إعداد مسار التخزين
        self.storage_path = storage_path or self._get_default_storage_path()
        
        # التأكد من وجود مجلد التخزين
        os.makedirs(self.storage_path, exist_ok=True)
        
        logger.info(f"تم تهيئة وكيل الملفات مع مسار تخزين: {self.storage_path}")
    
    async def process(self, payload: Any, model: str = "gpt-4", 
                    options: Dict = None) -> AsyncGenerator[Dict, None]:
        """
        معالجة الطلب
        
        Args:
            payload: بيانات الطلب (أمر الملف)
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
        if isinstance(payload, str):
            try:
                # محاولة تحليل البيانات كـ JSON
                payload_data = json.loads(payload)
            except json.JSONDecodeError:
                # إذا لم يكن JSON، استخدم النص كأمر
                payload_data = {"command": payload}
        elif isinstance(payload, dict):
            payload_data = payload
        else:
            logger.error("نوع بيانات غير مدعوم")
            yield {"error": "نوع بيانات غير مدعوم"}
            return
        
        # استخراج الأمر
        command = payload_data.get("command", "").lower()
        
        try:
            # معالجة الأمر
            if command == "list":
                # قائمة الملفات
                result = await self._list_files(payload_data)
                yield {"result": result, "command": command}
            
            elif command == "read":
                # قراءة ملف
                result = await self._read_file(payload_data)
                yield {"result": result, "command": command}
            
            elif command == "write":
                # كتابة ملف
                result = await self._write_file(payload_data)
                yield {"result": result, "command": command}
            
            elif command == "delete":
                # حذف ملف
                result = await self._delete_file(payload_data)
                yield {"result": result, "command": command}
            
            elif command == "info":
                # معلومات الملف
                result = await self._get_file_info(payload_data)
                yield {"result": result, "command": command}
            
            elif command == "convert":
                # تحويل الملف
                result = await self._convert_file(payload_data)
                yield {"result": result, "command": command}
            
            else:
                logger.error(f"أمر غير معروف: {command}")
                yield {"error": f"أمر غير معروف: {command}"}
        
        except Exception as e:
            logger.error(f"خطأ في معالجة أمر الملف: {e}")
            yield {"error": f"خطأ في معالجة أمر الملف: {e}"}
    
    async def _list_files(self, payload: Dict) -> Dict:
        """
        قائمة الملفات
        
        Args:
            payload: بيانات الطلب
            
        Returns:
            نتيجة العملية
        """
        # الحصول على المسار
        path = payload.get("path", "")
        full_path = os.path.join(self.storage_path, path)
        
        # التحقق من وجود المسار
        if not os.path.exists(full_path):
            return {"error": f"المسار غير موجود: {path}"}
        
        # التحقق من أن المسار هو مجلد
        if not os.path.isdir(full_path):
            return {"error": f"المسار ليس مجلداً: {path}"}
        
        # الحصول على قائمة الملفات
        files = []
        
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            item_type = "directory" if os.path.isdir(item_path) else "file"
            item_size = os.path.getsize(item_path) if os.path.isfile(item_path) else 0
            
            files.append({
                "name": item,
                "type": item_type,
                "size": item_size,
                "path": os.path.join(path, item)
            })
        
        return {"files": files, "path": path}
    
    async def _read_file(self, payload: Dict) -> Dict:
        """
        قراءة ملف
        
        Args:
            payload: بيانات الطلب
            
        Returns:
            نتيجة العملية
        """
        # الحصول على المسار
        path = payload.get("path", "")
        if not path:
            return {"error": "المسار غير محدد"}
        
        full_path = os.path.join(self.storage_path, path)
        
        # التحقق من وجود الملف
        if not os.path.exists(full_path):
            return {"error": f"الملف غير موجود: {path}"}
        
        # التحقق من أن المسار هو ملف
        if not os.path.isfile(full_path):
            return {"error": f"المسار ليس ملفاً: {path}"}
        
        try:
            # تحديد نوع الملف
            mime_type, _ = mimetypes.guess_type(full_path)
            
            # قراءة الملف
            if mime_type and mime_type.startswith("text/"):
                # قراءة ملف نصي
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                return {"content": content, "path": path, "mime_type": mime_type}
            else:
                # قراءة ملف ثنائي
                with open(full_path, "rb") as f:
                    content = base64.b64encode(f.read()).decode("utf-8")
                
                return {"content": content, "path": path, "mime_type": mime_type, "encoding": "base64"}
        
        except Exception as e:
            return {"error": f"خطأ في قراءة الملف: {e}"}
    
    async def _write_file(self, payload: Dict) -> Dict:
        """
        كتابة ملف
        
        Args:
            payload: بيانات الطلب
            
        Returns:
            نتيجة العملية
        """
        # الحصول على المسار
        path = payload.get("path", "")
        if not path:
            return {"error": "المسار غير محدد"}
        
        # الحصول على المحتوى
        content = payload.get("content", "")
        if content is None:
            return {"error": "المحتوى غير محدد"}
        
        # الحصول على الترميز
        encoding = payload.get("encoding", "text")
        
        full_path = os.path.join(self.storage_path, path)
        
        # التأكد من وجود المجلد
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        try:
            if encoding == "base64":
                # كتابة ملف ثنائي
                binary_content = base64.b64decode(content)
                with open(full_path, "wb") as f:
                    f.write(binary_content)
            else:
                # كتابة ملف نصي
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
            
            return {"success": True, "path": path}
        
        except Exception as e:
            return {"error": f"خطأ في كتابة الملف: {e}"}
    
    async def _delete_file(self, payload: Dict) -> Dict:
        """
        حذف ملف
        
        Args:
            payload: بيانات الطلب
            
        Returns:
            نتيجة العملية
        """
        # الحصول على المسار
        path = payload.get("path", "")
        if not path:
            return {"error": "المسار غير محدد"}
        
        full_path = os.path.join(self.storage_path, path)
        
        # التحقق من وجود الملف
        if not os.path.exists(full_path):
            return {"error": f"الملف غير موجود: {path}"}
        
        try:
            if os.path.isfile(full_path):
                # حذف ملف
                os.remove(full_path)
            elif os.path.isdir(full_path):
                # حذف مجلد
                recursive = payload.get("recursive", False)
                
                if recursive:
                    import shutil
                    shutil.rmtree(full_path)
                else:
                    os.rmdir(full_path)
            
            return {"success": True, "path": path}
        
        except Exception as e:
            return {"error": f"خطأ في حذف الملف: {e}"}
    
    async def _get_file_info(self, payload: Dict) -> Dict:
        """
        معلومات الملف
        
        Args:
            payload: بيانات الطلب
            
        Returns:
            نتيجة العملية
        """
        # الحصول على المسار
        path = payload.get("path", "")
        if not path:
            return {"error": "المسار غير محدد"}
        
        full_path = os.path.join(self.storage_path, path)
        
        # التحقق من وجود الملف
        if not os.path.exists(full_path):
            return {"error": f"الملف غير موجود: {path}"}
        
        try:
            # الحصول على معلومات الملف
            stat_info = os.stat(full_path)
            
            # تحديد نوع الملف
            mime_type, _ = mimetypes.guess_type(full_path)
            
            # إنشاء معلومات الملف
            file_info = {
                "path": path,
                "size": stat_info.st_size,
                "created": stat_info.st_ctime,
                "modified": stat_info.st_mtime,
                "accessed": stat_info.st_atime,
                "is_file": os.path.isfile(full_path),
                "is_dir": os.path.isdir(full_path),
                "mime_type": mime_type
            }
            
            return {"info": file_info}
        
        except Exception as e:
            return {"error": f"خطأ في الحصول على معلومات الملف: {e}"}
    
    async def _convert_file(self, payload: Dict) -> Dict:
        """
        تحويل الملف
        
        Args:
            payload: بيانات الطلب
            
        Returns:
            نتيجة العملية
        """
        # الحصول على المسار
        path = payload.get("path", "")
        if not path:
            return {"error": "المسار غير محدد"}
        
        # الحصول على التنسيق المطلوب
        target_format = payload.get("format", "")
        if not target_format:
            return {"error": "التنسيق المطلوب غير محدد"}
        
        full_path = os.path.join(self.storage_path, path)
        
        # التحقق من وجود الملف
        if not os.path.exists(full_path):
            return {"error": f"الملف غير موجود: {path}"}
        
        # التحقق من أن المسار هو ملف
        if not os.path.isfile(full_path):
            return {"error": f"المسار ليس ملفاً: {path}"}
        
        # في الإصدار الحالي، نحاكي عملية التحويل
        # في الإصدار النهائي، يمكن استخدام مكتبات متخصصة مثل Pandoc أو Pillow
        
        # إنشاء مسار الملف الجديد
        base_name = os.path.splitext(path)[0]
        new_path = f"{base_name}.{target_format}"
        full_new_path = os.path.join(self.storage_path, new_path)
        
        try:
            # محاكاة عملية التحويل
            with open(full_path, "rb") as f:
                content = f.read()
            
            with open(full_new_path, "wb") as f:
                f.write(content)
            
            return {
                "success": True,
                "original_path": path,
                "new_path": new_path,
                "format": target_format
            }
        
        except Exception as e:
            return {"error": f"خطأ في تحويل الملف: {e}"}
    
    def _get_default_storage_path(self) -> str:
        """
        الحصول على مسار التخزين الافتراضي
        
        Returns:
            مسار التخزين الافتراضي
        """
        return os.path.join(os.path.expanduser("~"), "attorney_general_files")
