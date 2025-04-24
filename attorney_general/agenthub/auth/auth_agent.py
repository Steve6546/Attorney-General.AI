"""
وكيل المصادقة (Auth Agent) لنظام Attorney-General.AI
مسؤول عن المصادقة والتفويض
"""

import logging
import json
import asyncio
import os
import jwt
import hashlib
import time
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime, timedelta

from attorney_general.agenthub.base_agent import BaseAgent

logger = logging.getLogger("auth_agent")

class AuthAgent(BaseAgent):
    """
    وكيل المصادقة
    مسؤول عن المصادقة والتفويض
    """
    
    def __init__(self, secret_key: str = None):
        """
        تهيئة وكيل المصادقة
        
        Args:
            secret_key: المفتاح السري للتشفير
        """
        super().__init__(agent_id="auth", name="Auth Agent")
        
        # إضافة القدرات
        self.capabilities = ["authentication", "authorization", "user_management"]
        self.supports_streaming = False
        
        # إعداد المفتاح السري
        self.secret_key = secret_key or self._get_default_secret_key()
        
        # إعداد مخزن المستخدمين (في الإنتاج، سيكون هذا قاعدة بيانات)
        self.users = {}
        
        # إعداد مخزن الرموز
        self.tokens = {}
        
        logger.info("تم تهيئة وكيل المصادقة")
    
    async def process(self, payload: Any, model: str = "gpt-4", 
                    options: Dict = None) -> AsyncGenerator[Dict, None]:
        """
        معالجة الطلب
        
        Args:
            payload: بيانات الطلب (أمر المصادقة)
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
            if command == "login":
                # تسجيل الدخول
                result = await self._login(payload_data)
                yield {"result": result, "command": command}
            
            elif command == "register":
                # تسجيل مستخدم جديد
                result = await self._register(payload_data)
                yield {"result": result, "command": command}
            
            elif command == "verify":
                # التحقق من الرمز
                result = await self._verify_token(payload_data)
                yield {"result": result, "command": command}
            
            elif command == "logout":
                # تسجيل الخروج
                result = await self._logout(payload_data)
                yield {"result": result, "command": command}
            
            elif command == "refresh":
                # تحديث الرمز
                result = await self._refresh_token(payload_data)
                yield {"result": result, "command": command}
            
            else:
                logger.error(f"أمر غير معروف: {command}")
                yield {"error": f"أمر غير معروف: {command}"}
        
        except Exception as e:
            logger.error(f"خطأ في معالجة أمر المصادقة: {e}")
            yield {"error": f"خطأ في معالجة أمر المصادقة: {e}"}
    
    async def _login(self, payload: Dict) -> Dict:
        """
        تسجيل الدخول
        
        Args:
            payload: بيانات الطلب
            
        Returns:
            نتيجة العملية
        """
        # الحصول على اسم المستخدم وكلمة المرور
        username = payload.get("username", "")
        password = payload.get("password", "")
        
        if not username or not password:
            return {"error": "اسم المستخدم أو كلمة المرور غير محددة"}
        
        # التحقق من وجود المستخدم
        if username not in self.users:
            return {"error": "اسم المستخدم أو كلمة المرور غير صحيحة"}
        
        # التحقق من كلمة المرور
        hashed_password = self._hash_password(password)
        if self.users[username]["password"] != hashed_password:
            return {"error": "اسم المستخدم أو كلمة المرور غير صحيحة"}
        
        # إنشاء الرمز
        token = self._generate_token(username)
        
        # تخزين الرمز
        self.tokens[token] = {
            "username": username,
            "created_at": time.time(),
            "expires_at": time.time() + 3600  # ساعة واحدة
        }
        
        return {
            "token": token,
            "username": username,
            "expires_in": 3600
        }
    
    async def _register(self, payload: Dict) -> Dict:
        """
        تسجيل مستخدم جديد
        
        Args:
            payload: بيانات الطلب
            
        Returns:
            نتيجة العملية
        """
        # الحصول على اسم المستخدم وكلمة المرور
        username = payload.get("username", "")
        password = payload.get("password", "")
        email = payload.get("email", "")
        
        if not username or not password:
            return {"error": "اسم المستخدم أو كلمة المرور غير محددة"}
        
        # التحقق من عدم وجود المستخدم
        if username in self.users:
            return {"error": "اسم المستخدم موجود مسبقاً"}
        
        # تشفير كلمة المرور
        hashed_password = self._hash_password(password)
        
        # إنشاء المستخدم
        self.users[username] = {
            "username": username,
            "password": hashed_password,
            "email": email,
            "created_at": time.time(),
            "role": "user"
        }
        
        return {
            "success": True,
            "username": username
        }
    
    async def _verify_token(self, payload: Dict) -> Dict:
        """
        التحقق من الرمز
        
        Args:
            payload: بيانات الطلب
            
        Returns:
            نتيجة العملية
        """
        # الحصول على الرمز
        token = payload.get("token", "")
        
        if not token:
            return {"error": "الرمز غير محدد"}
        
        # التحقق من وجود الرمز
        if token not in self.tokens:
            return {"error": "الرمز غير صالح"}
        
        # التحقق من صلاحية الرمز
        token_info = self.tokens[token]
        if token_info["expires_at"] < time.time():
            # إزالة الرمز منتهي الصلاحية
            del self.tokens[token]
            return {"error": "الرمز منتهي الصلاحية"}
        
        # الحصول على معلومات المستخدم
        username = token_info["username"]
        user_info = self.users.get(username, {})
        
        return {
            "valid": True,
            "username": username,
            "role": user_info.get("role", "user"),
            "expires_at": token_info["expires_at"]
        }
    
    async def _logout(self, payload: Dict) -> Dict:
        """
        تسجيل الخروج
        
        Args:
            payload: بيانات الطلب
            
        Returns:
            نتيجة العملية
        """
        # الحصول على الرمز
        token = payload.get("token", "")
        
        if not token:
            return {"error": "الرمز غير محدد"}
        
        # التحقق من وجود الرمز
        if token not in self.tokens:
            return {"success": True}  # الرمز غير موجود أصلاً
        
        # إزالة الرمز
        del self.tokens[token]
        
        return {"success": True}
    
    async def _refresh_token(self, payload: Dict) -> Dict:
        """
        تحديث الرمز
        
        Args:
            payload: بيانات الطلب
            
        Returns:
            نتيجة العملية
        """
        # الحصول على الرمز
        token = payload.get("token", "")
        
        if not token:
            return {"error": "الرمز غير محدد"}
        
        # التحقق من وجود الرمز
        if token not in self.tokens:
            return {"error": "الرمز غير صالح"}
        
        # التحقق من صلاحية الرمز
        token_info = self.tokens[token]
        if token_info["expires_at"] < time.time():
            # إزالة الرمز منتهي الصلاحية
            del self.tokens[token]
            return {"error": "الرمز منتهي الصلاحية"}
        
        # إنشاء رمز جديد
        username = token_info["username"]
        new_token = self._generate_token(username)
        
        # تخزين الرمز الجديد
        self.tokens[new_token] = {
            "username": username,
            "created_at": time.time(),
            "expires_at": time.time() + 3600  # ساعة واحدة
        }
        
        # إزالة الرمز القديم
        del self.tokens[token]
        
        return {
            "token": new_token,
            "username": username,
            "expires_in": 3600
        }
    
    def _hash_password(self, password: str) -> str:
        """
        تشفير كلمة المرور
        
        Args:
            password: كلمة المرور
            
        Returns:
            كلمة المرور المشفرة
        """
        return hashlib.sha256((password + self.secret_key).encode()).hexdigest()
    
    def _generate_token(self, username: str) -> str:
        """
        إنشاء رمز
        
        Args:
            username: اسم المستخدم
            
        Returns:
            الرمز
        """
        payload = {
            "sub": username,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def _get_default_secret_key(self) -> str:
        """
        الحصول على المفتاح السري الافتراضي
        
        Returns:
            المفتاح السري الافتراضي
        """
        import os
        return os.environ.get("AUTH_SECRET_KEY", "default_secret_key_for_development")
