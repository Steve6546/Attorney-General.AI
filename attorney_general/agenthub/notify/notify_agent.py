"""
وكيل الإشعارات (Notify Agent) لنظام Attorney-General.AI
مسؤول عن إرسال الإشعارات والتنبيهات
"""

import logging
import json
import asyncio
import time
from typing import Dict, List, Optional, Any, AsyncGenerator
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from attorney_general.agenthub.base_agent import BaseAgent

logger = logging.getLogger("notify_agent")

class NotifyAgent(BaseAgent):
    """
    وكيل الإشعارات
    مسؤول عن إرسال الإشعارات والتنبيهات
    """
    
    def __init__(self, smtp_config: Dict = None):
        """
        تهيئة وكيل الإشعارات
        
        Args:
            smtp_config: إعدادات SMTP لإرسال البريد الإلكتروني
        """
        super().__init__(agent_id="notify", name="Notification Agent")
        
        # إضافة القدرات
        self.capabilities = ["notifications", "alerts", "email", "sms"]
        self.supports_streaming = False
        
        # إعداد تكوين SMTP
        self.smtp_config = smtp_config or self._get_default_smtp_config()
        
        # إعداد سجل الإشعارات
        self.notification_history = []
        
        logger.info("تم تهيئة وكيل الإشعارات")
    
    async def process(self, payload: Any, model: str = "gpt-4", 
                    options: Dict = None) -> AsyncGenerator[Dict, None]:
        """
        معالجة الطلب
        
        Args:
            payload: بيانات الطلب (أمر الإشعار)
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
                payload_data = {"command": "send", "message": payload}
        elif isinstance(payload, dict):
            payload_data = payload
        else:
            logger.error("نوع بيانات غير مدعوم")
            yield {"error": "نوع بيانات غير مدعوم"}
            return
        
        # استخراج الأمر
        command = payload_data.get("command", "send").lower()
        
        try:
            # معالجة الأمر
            if command == "send":
                # إرسال إشعار
                result = await self._send_notification(payload_data)
                yield {"result": result, "command": command}
            
            elif command == "email":
                # إرسال بريد إلكتروني
                result = await self._send_email(payload_data)
                yield {"result": result, "command": command}
            
            elif command == "sms":
                # إرسال رسالة نصية
                result = await self._send_sms(payload_data)
                yield {"result": result, "command": command}
            
            elif command == "history":
                # الحصول على سجل الإشعارات
                result = await self._get_notification_history(payload_data)
                yield {"result": result, "command": command}
            
            else:
                logger.error(f"أمر غير معروف: {command}")
                yield {"error": f"أمر غير معروف: {command}"}
        
        except Exception as e:
            logger.error(f"خطأ في معالجة أمر الإشعار: {e}")
            yield {"error": f"خطأ في معالجة أمر الإشعار: {e}"}
    
    async def _send_notification(self, payload: Dict) -> Dict:
        """
        إرسال إشعار
        
        Args:
            payload: بيانات الطلب
            
        Returns:
            نتيجة العملية
        """
        # الحصول على الرسالة
        message = payload.get("message", "")
        if not message:
            return {"error": "الرسالة غير محددة"}
        
        # الحصول على المستلم
        recipient = payload.get("recipient", "")
        
        # الحصول على نوع الإشعار
        notification_type = payload.get("type", "info")
        
        # الحصول على الأولوية
        priority = payload.get("priority", "normal")
        
        # إنشاء الإشعار
        notification = {
            "message": message,
            "recipient": recipient,
            "type": notification_type,
            "priority": priority,
            "timestamp": time.time(),
            "status": "sent"
        }
        
        # إضافة الإشعار إلى السجل
        self.notification_history.append(notification)
        
        # في الإصدار النهائي، يمكن إرسال الإشعار عبر قنوات مختلفة
        # مثل WebSockets أو Firebase Cloud Messaging
        
        logger.info(f"تم إرسال إشعار إلى {recipient}: {message}")
        
        return {
            "success": True,
            "notification_id": len(self.notification_history) - 1,
            "timestamp": notification["timestamp"]
        }
    
    async def _send_email(self, payload: Dict) -> Dict:
        """
        إرسال بريد إلكتروني
        
        Args:
            payload: بيانات الطلب
            
        Returns:
            نتيجة العملية
        """
        # الحصول على المستلم
        to_email = payload.get("to", "")
        if not to_email:
            return {"error": "عنوان البريد الإلكتروني للمستلم غير محدد"}
        
        # الحصول على الموضوع
        subject = payload.get("subject", "إشعار من Attorney-General.AI")
        
        # الحصول على الرسالة
        message = payload.get("message", "")
        if not message:
            return {"error": "الرسالة غير محددة"}
        
        # الحصول على نوع المحتوى
        content_type = payload.get("content_type", "text")
        
        try:
            # إنشاء رسالة البريد الإلكتروني
            email_message = MIMEMultipart()
            email_message["From"] = self.smtp_config["from_email"]
            email_message["To"] = to_email
            email_message["Subject"] = subject
            
            # إضافة الرسالة
            if content_type == "html":
                email_message.attach(MIMEText(message, "html"))
            else:
                email_message.attach(MIMEText(message, "plain"))
            
            # في بيئة التطوير، نحاكي إرسال البريد الإلكتروني
            if self.smtp_config["host"] == "localhost":
                logger.info(f"محاكاة إرسال بريد إلكتروني إلى {to_email}: {subject}")
                
                # إضافة البريد الإلكتروني إلى السجل
                email_notification = {
                    "message": message,
                    "recipient": to_email,
                    "type": "email",
                    "priority": "normal",
                    "timestamp": time.time(),
                    "status": "sent",
                    "subject": subject
                }
                
                self.notification_history.append(email_notification)
                
                return {
                    "success": True,
                    "notification_id": len(self.notification_history) - 1,
                    "timestamp": email_notification["timestamp"]
                }
            
            # في بيئة الإنتاج، نرسل البريد الإلكتروني فعلياً
            with smtplib.SMTP(self.smtp_config["host"], self.smtp_config["port"]) as server:
                if self.smtp_config["use_tls"]:
                    server.starttls()
                
                if self.smtp_config["username"] and self.smtp_config["password"]:
                    server.login(self.smtp_config["username"], self.smtp_config["password"])
                
                server.send_message(email_message)
            
            # إضافة البريد الإلكتروني إلى السجل
            email_notification = {
                "message": message,
                "recipient": to_email,
                "type": "email",
                "priority": "normal",
                "timestamp": time.time(),
                "status": "sent",
                "subject": subject
            }
            
            self.notification_history.append(email_notification)
            
            logger.info(f"تم إرسال بريد إلكتروني إلى {to_email}: {subject}")
            
            return {
                "success": True,
                "notification_id": len(self.notification_history) - 1,
                "timestamp": email_notification["timestamp"]
            }
        
        except Exception as e:
            logger.error(f"خطأ في إرسال البريد الإلكتروني: {e}")
            return {"error": f"خطأ في إرسال البريد الإلكتروني: {e}"}
    
    async def _send_sms(self, payload: Dict) -> Dict:
        """
        إرسال رسالة نصية
        
        Args:
            payload: بيانات الطلب
            
        Returns:
            نتيجة العملية
        """
        # الحصول على رقم الهاتف
        phone_number = payload.get("to", "")
        if not phone_number:
            return {"error": "رقم الهاتف غير محدد"}
        
        # الحصول على الرسالة
        message = payload.get("message", "")
        if not message:
            return {"error": "الرسالة غير محددة"}
        
        # في الإصدار الحالي، نحاكي إرسال الرسالة النصية
        # في الإصدار النهائي، يمكن استخدام خدمة مثل Twilio أو AWS SNS
        
        # إضافة الرسالة النصية إلى السجل
        sms_notification = {
            "message": message,
            "recipient": phone_number,
            "type": "sms",
            "priority": "high",
            "timestamp": time.time(),
            "status": "sent"
        }
        
        self.notification_history.append(sms_notification)
        
        logger.info(f"تم إرسال رسالة نصية إلى {phone_number}: {message}")
        
        return {
            "success": True,
            "notification_id": len(self.notification_history) - 1,
            "timestamp": sms_notification["timestamp"]
        }
    
    async def _get_notification_history(self, payload: Dict) -> Dict:
        """
        الحصول على سجل الإشعارات
        
        Args:
            payload: بيانات الطلب
            
        Returns:
            نتيجة العملية
        """
        # الحصول على المستلم
        recipient = payload.get("recipient", "")
        
        # الحصول على نوع الإشعار
        notification_type = payload.get("type", "")
        
        # الحصول على الحد
        limit = payload.get("limit", 10)
        
        # تصفية الإشعارات
        filtered_notifications = self.notification_history
        
        if recipient:
            filtered_notifications = [
                n for n in filtered_notifications
                if n.get("recipient") == recipient
            ]
        
        if notification_type:
            filtered_notifications = [
                n for n in filtered_notifications
                if n.get("type") == notification_type
            ]
        
        # ترتيب الإشعارات حسب الطابع الزمني (الأحدث أولاً)
        sorted_notifications = sorted(
            filtered_notifications,
            key=lambda n: n.get("timestamp", 0),
            reverse=True
        )
        
        # تطبيق الحد
        limited_notifications = sorted_notifications[:limit]
        
        return {
            "notifications": limited_notifications,
            "total": len(filtered_notifications),
            "returned": len(limited_notifications)
        }
    
    def _get_default_smtp_config(self) -> Dict:
        """
        الحصول على إعدادات SMTP الافتراضية
        
        Returns:
            إعدادات SMTP الافتراضية
        """
        import os
        
        return {
            "host": os.environ.get("SMTP_HOST", "localhost"),
            "port": int(os.environ.get("SMTP_PORT", "25")),
            "username": os.environ.get("SMTP_USERNAME", ""),
            "password": os.environ.get("SMTP_PASSWORD", ""),
            "from_email": os.environ.get("SMTP_FROM_EMAIL", "noreply@attorney-general.ai"),
            "use_tls": os.environ.get("SMTP_USE_TLS", "false").lower() == "true"
        }
