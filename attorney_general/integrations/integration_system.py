"""
نظام التكاملات (Integration System) لنظام Attorney-General.AI
يوفر واجهة موحدة للتكامل مع الخدمات الخارجية
"""

import logging
import json
import os
import requests
import time
from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime
import uuid

logger = logging.getLogger("integration_system")

class IntegrationSystem:
    """
    نظام التكاملات
    يوفر واجهة موحدة للتكامل مع الخدمات الخارجية
    """
    
    def __init__(self, config_path: str = None):
        """
        تهيئة نظام التكاملات
        
        Args:
            config_path: مسار ملف الإعدادات
        """
        # إعداد مسار ملف الإعدادات
        self.config_path = config_path or self._get_default_config_path()
        
        # إعداد قاموس التكاملات
        self.integrations = {}
        
        # إعداد قاموس الإعدادات
        self.config = self._load_config()
        
        # تسجيل التكاملات المدمجة
        self._register_built_in_integrations()
        
        logger.info("تم تهيئة نظام التكاملات")
    
    def register_integration(self, integration_id: str, integration_handler: Callable) -> bool:
        """
        تسجيل تكامل
        
        Args:
            integration_id: معرف التكامل
            integration_handler: معالج التكامل
            
        Returns:
            نجاح العملية
        """
        # التحقق من عدم وجود تكامل بنفس المعرف
        if integration_id in self.integrations:
            logger.warning(f"تكامل بالمعرف {integration_id} موجود مسبقاً")
            return False
        
        # تسجيل التكامل
        self.integrations[integration_id] = integration_handler
        
        logger.info(f"تم تسجيل التكامل: {integration_id}")
        return True
    
    def unregister_integration(self, integration_id: str) -> bool:
        """
        إلغاء تسجيل تكامل
        
        Args:
            integration_id: معرف التكامل
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود التكامل
        if integration_id not in self.integrations:
            logger.warning(f"التكامل {integration_id} غير موجود")
            return False
        
        # إلغاء تسجيل التكامل
        del self.integrations[integration_id]
        
        logger.info(f"تم إلغاء تسجيل التكامل: {integration_id}")
        return True
    
    def get_integration(self, integration_id: str) -> Optional[Callable]:
        """
        الحصول على تكامل
        
        Args:
            integration_id: معرف التكامل
            
        Returns:
            معالج التكامل أو None إذا لم يكن موجوداً
        """
        return self.integrations.get(integration_id)
    
    def get_all_integrations(self) -> Dict[str, Callable]:
        """
        الحصول على جميع التكاملات
        
        Returns:
            قاموس التكاملات
        """
        return self.integrations
    
    def get_integration_config(self, integration_id: str) -> Optional[Dict]:
        """
        الحصول على إعدادات التكامل
        
        Args:
            integration_id: معرف التكامل
            
        Returns:
            إعدادات التكامل أو None إذا لم تكن موجودة
        """
        return self.config.get(integration_id)
    
    def set_integration_config(self, integration_id: str, config: Dict) -> bool:
        """
        تعيين إعدادات التكامل
        
        Args:
            integration_id: معرف التكامل
            config: الإعدادات
            
        Returns:
            نجاح العملية
        """
        # تحديث الإعدادات
        self.config[integration_id] = config
        
        # حفظ الإعدادات
        self._save_config()
        
        logger.info(f"تم تعيين إعدادات التكامل: {integration_id}")
        return True
    
    def call_integration(self, integration_id: str, method: str, **kwargs) -> Any:
        """
        استدعاء تكامل
        
        Args:
            integration_id: معرف التكامل
            method: الطريقة
            **kwargs: المعاملات
            
        Returns:
            نتيجة الاستدعاء
        """
        # الحصول على التكامل
        integration = self.get_integration(integration_id)
        
        if integration is None:
            logger.warning(f"التكامل {integration_id} غير موجود")
            return None
        
        # الحصول على إعدادات التكامل
        config = self.get_integration_config(integration_id) or {}
        
        # استدعاء التكامل
        try:
            return integration(method, config, **kwargs)
        except Exception as e:
            logger.error(f"خطأ في استدعاء التكامل {integration_id}: {e}")
            return None
    
    def _register_built_in_integrations(self) -> None:
        """
        تسجيل التكاملات المدمجة
        """
        # تسجيل تكامل HTTP
        self.register_integration("http", self._http_integration_handler)
        
        # تسجيل تكامل البريد الإلكتروني
        self.register_integration("email", self._email_integration_handler)
        
        # تسجيل تكامل قاعدة البيانات
        self.register_integration("database", self._database_integration_handler)
        
        # تسجيل تكامل الإشعارات
        self.register_integration("notification", self._notification_integration_handler)
        
        # تسجيل تكامل الملفات
        self.register_integration("file", self._file_integration_handler)
    
    def _http_integration_handler(self, method: str, config: Dict, **kwargs) -> Any:
        """
        معالج تكامل HTTP
        
        Args:
            method: الطريقة
            config: الإعدادات
            **kwargs: المعاملات
            
        Returns:
            نتيجة الاستدعاء
        """
        # التحقق من الطريقة
        if method not in ["get", "post", "put", "delete", "patch"]:
            logger.warning(f"طريقة HTTP غير صالحة: {method}")
            return None
        
        # الحصول على المعاملات
        url = kwargs.get("url")
        headers = kwargs.get("headers", {})
        params = kwargs.get("params", {})
        data = kwargs.get("data")
        json_data = kwargs.get("json")
        timeout = kwargs.get("timeout", 30)
        
        # التحقق من وجود عنوان URL
        if not url:
            logger.warning("عنوان URL مطلوب")
            return None
        
        # إضافة الرأسيات من الإعدادات
        if "headers" in config:
            headers.update(config["headers"])
        
        # إضافة المعاملات من الإعدادات
        if "params" in config:
            params.update(config["params"])
        
        # إنشاء الطلب
        try:
            # استدعاء الطريقة المناسبة
            if method == "get":
                response = requests.get(url, headers=headers, params=params, timeout=timeout)
            elif method == "post":
                response = requests.post(url, headers=headers, params=params, data=data, json=json_data, timeout=timeout)
            elif method == "put":
                response = requests.put(url, headers=headers, params=params, data=data, json=json_data, timeout=timeout)
            elif method == "delete":
                response = requests.delete(url, headers=headers, params=params, timeout=timeout)
            elif method == "patch":
                response = requests.patch(url, headers=headers, params=params, data=data, json=json_data, timeout=timeout)
            
            # التحقق من نجاح الطلب
            response.raise_for_status()
            
            # محاولة تحليل الاستجابة كـ JSON
            try:
                return response.json()
            except:
                return response.text
        
        except requests.exceptions.RequestException as e:
            logger.error(f"خطأ في طلب HTTP: {e}")
            return None
    
    def _email_integration_handler(self, method: str, config: Dict, **kwargs) -> Any:
        """
        معالج تكامل البريد الإلكتروني
        
        Args:
            method: الطريقة
            config: الإعدادات
            **kwargs: المعاملات
            
        Returns:
            نتيجة الاستدعاء
        """
        # التحقق من الطريقة
        if method not in ["send"]:
            logger.warning(f"طريقة البريد الإلكتروني غير صالحة: {method}")
            return None
        
        # التحقق من وجود إعدادات SMTP
        if "smtp_server" not in config:
            logger.warning("إعدادات SMTP مطلوبة")
            return None
        
        # الحصول على المعاملات
        to = kwargs.get("to")
        subject = kwargs.get("subject", "")
        body = kwargs.get("body", "")
        html = kwargs.get("html", False)
        attachments = kwargs.get("attachments", [])
        
        # التحقق من وجود عنوان البريد الإلكتروني للمستلم
        if not to:
            logger.warning("عنوان البريد الإلكتروني للمستلم مطلوب")
            return None
        
        # إرسال البريد الإلكتروني
        try:
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.mime.application import MIMEApplication
            
            # إنشاء رسالة
            msg = MIMEMultipart()
            msg["From"] = config.get("from", "noreply@example.com")
            msg["To"] = to
            msg["Subject"] = subject
            
            # إضافة النص
            if html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))
            
            # إضافة المرفقات
            for attachment in attachments:
                with open(attachment, "rb") as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(attachment))
                
                part["Content-Disposition"] = f'attachment; filename="{os.path.basename(attachment)}"'
                msg.attach(part)
            
            # إنشاء اتصال SMTP
            server = smtplib.SMTP(config["smtp_server"], config.get("smtp_port", 587))
            server.starttls()
            
            # تسجيل الدخول
            if "smtp_username" in config and "smtp_password" in config:
                server.login(config["smtp_username"], config["smtp_password"])
            
            # إرسال البريد الإلكتروني
            server.send_message(msg)
            server.quit()
            
            return True
        
        except Exception as e:
            logger.error(f"خطأ في إرسال البريد الإلكتروني: {e}")
            return None
    
    def _database_integration_handler(self, method: str, config: Dict, **kwargs) -> Any:
        """
        معالج تكامل قاعدة البيانات
        
        Args:
            method: الطريقة
            config: الإعدادات
            **kwargs: المعاملات
            
        Returns:
            نتيجة الاستدعاء
        """
        # التحقق من الطريقة
        if method not in ["query", "execute"]:
            logger.warning(f"طريقة قاعدة البيانات غير صالحة: {method}")
            return None
        
        # التحقق من وجود إعدادات قاعدة البيانات
        if "type" not in config:
            logger.warning("نوع قاعدة البيانات مطلوب")
            return None
        
        # الحصول على المعاملات
        query = kwargs.get("query")
        params = kwargs.get("params", [])
        
        # التحقق من وجود الاستعلام
        if not query:
            logger.warning("الاستعلام مطلوب")
            return None
        
        # تنفيذ الاستعلام
        try:
            # التعامل مع أنواع قواعد البيانات المختلفة
            if config["type"] == "sqlite":
                import sqlite3
                
                # إنشاء اتصال
                conn = sqlite3.connect(config.get("database", ":memory:"))
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # تنفيذ الاستعلام
                cursor.execute(query, params)
                
                # الحصول على النتائج
                if method == "query":
                    rows = cursor.fetchall()
                    result = [dict(row) for row in rows]
                else:
                    conn.commit()
                    result = {"rowcount": cursor.rowcount, "lastrowid": cursor.lastrowid}
                
                # إغلاق الاتصال
                conn.close()
                
                return result
            
            elif config["type"] == "mysql":
                import pymysql
                
                # إنشاء اتصال
                conn = pymysql.connect(
                    host=config.get("host", "localhost"),
                    user=config.get("user", "root"),
                    password=config.get("password", ""),
                    database=config.get("database", ""),
                    charset=config.get("charset", "utf8mb4"),
                    cursorclass=pymysql.cursors.DictCursor
                )
                
                # تنفيذ الاستعلام
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    
                    # الحصول على النتائج
                    if method == "query":
                        result = cursor.fetchall()
                    else:
                        conn.commit()
                        result = {"rowcount": cursor.rowcount, "lastrowid": cursor.lastrowid}
                
                # إغلاق الاتصال
                conn.close()
                
                return result
            
            elif config["type"] == "postgresql":
                import psycopg2
                import psycopg2.extras
                
                # إنشاء اتصال
                conn = psycopg2.connect(
                    host=config.get("host", "localhost"),
                    user=config.get("user", "postgres"),
                    password=config.get("password", ""),
                    dbname=config.get("database", "postgres")
                )
                
                # تنفيذ الاستعلام
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute(query, params)
                    
                    # الحصول على النتائج
                    if method == "query":
                        rows = cursor.fetchall()
                        result = [dict(row) for row in rows]
                    else:
                        conn.commit()
                        result = {"rowcount": cursor.rowcount}
                
                # إغلاق الاتصال
                conn.close()
                
                return result
            
            else:
                logger.warning(f"نوع قاعدة البيانات غير مدعوم: {config['type']}")
                return None
        
        except Exception as e:
            logger.error(f"خطأ في تنفيذ استعلام قاعدة البيانات: {e}")
            return None
    
    def _notification_integration_handler(self, method: str, config: Dict, **kwargs) -> Any:
        """
        معالج تكامل الإشعارات
        
        Args:
            method: الطريقة
            config: الإعدادات
            **kwargs: المعاملات
            
        Returns:
            نتيجة الاستدعاء
        """
        # التحقق من الطريقة
        if method not in ["send"]:
            logger.warning(f"طريقة الإشعارات غير صالحة: {method}")
            return None
        
        # الحصول على المعاملات
        channel = kwargs.get("channel", "default")
        title = kwargs.get("title", "")
        message = kwargs.get("message", "")
        data = kwargs.get("data", {})
        
        # التحقق من وجود الرسالة
        if not message:
            logger.warning("الرسالة مطلوبة")
            return None
        
        # إرسال الإشعار
        try:
            # التعامل مع قنوات الإشعارات المختلفة
            if channel == "console":
                # إشعار وحدة التحكم
                print(f"[{title}] {message}")
                return True
            
            elif channel == "webhook":
                # إشعار Webhook
                if "webhook_url" not in config:
                    logger.warning("عنوان URL للـ Webhook مطلوب")
                    return None
                
                # إرسال الإشعار
                response = requests.post(
                    config["webhook_url"],
                    json={
                        "title": title,
                        "message": message,
                        "data": data,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                
                # التحقق من نجاح الطلب
                response.raise_for_status()
                
                return True
            
            elif channel == "file":
                # إشعار ملف
                if "log_file" not in config:
                    logger.warning("مسار ملف السجل مطلوب")
                    return None
                
                # إنشاء المجلد إذا لم يكن موجوداً
                os.makedirs(os.path.dirname(config["log_file"]), exist_ok=True)
                
                # كتابة الإشعار إلى الملف
                with open(config["log_file"], "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now().isoformat()}] [{title}] {message}\n")
                
                return True
            
            else:
                logger.warning(f"قناة الإشعارات غير مدعومة: {channel}")
                return None
        
        except Exception as e:
            logger.error(f"خطأ في إرسال الإشعار: {e}")
            return None
    
    def _file_integration_handler(self, method: str, config: Dict, **kwargs) -> Any:
        """
        معالج تكامل الملفات
        
        Args:
            method: الطريقة
            config: الإعدادات
            **kwargs: المعاملات
            
        Returns:
            نتيجة الاستدعاء
        """
        # التحقق من الطريقة
        if method not in ["read", "write", "delete", "list"]:
            logger.warning(f"طريقة الملفات غير صالحة: {method}")
            return None
        
        # الحصول على المعاملات
        path = kwargs.get("path")
        content = kwargs.get("content")
        
        # التحقق من وجود المسار
        if not path and method != "list":
            logger.warning("المسار مطلوب")
            return None
        
        # تنفيذ العملية
        try:
            # التعامل مع أنواع التخزين المختلفة
            if config.get("type", "local") == "local":
                # تخزين محلي
                base_path = config.get("base_path", "")
                
                if base_path:
                    full_path = os.path.join(base_path, path) if path else base_path
                else:
                    full_path = path
                
                # تنفيذ العملية المطلوبة
                if method == "read":
                    # قراءة الملف
                    with open(full_path, "r", encoding="utf-8") as f:
                        return f.read()
                
                elif method == "write":
                    # التحقق من وجود المحتوى
                    if content is None:
                        logger.warning("المحتوى مطلوب")
                        return None
                    
                    # إنشاء المجلد إذا لم يكن موجوداً
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    
                    # كتابة الملف
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    
                    return True
                
                elif method == "delete":
                    # حذف الملف
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        return True
                    else:
                        logger.warning(f"الملف غير موجود: {full_path}")
                        return False
                
                elif method == "list":
                    # قائمة الملفات
                    if os.path.isdir(full_path):
                        return os.listdir(full_path)
                    else:
                        logger.warning(f"المجلد غير موجود: {full_path}")
                        return []
            
            elif config.get("type") == "s3":
                # تخزين S3
                try:
                    import boto3
                    
                    # التحقق من وجود إعدادات S3
                    if "bucket" not in config:
                        logger.warning("اسم الـ bucket مطلوب")
                        return None
                    
                    # إنشاء عميل S3
                    s3 = boto3.client(
                        "s3",
                        aws_access_key_id=config.get("access_key"),
                        aws_secret_access_key=config.get("secret_key"),
                        region_name=config.get("region")
                    )
                    
                    # تنفيذ العملية المطلوبة
                    if method == "read":
                        # قراءة الملف
                        response = s3.get_object(Bucket=config["bucket"], Key=path)
                        return response["Body"].read().decode("utf-8")
                    
                    elif method == "write":
                        # التحقق من وجود المحتوى
                        if content is None:
                            logger.warning("المحتوى مطلوب")
                            return None
                        
                        # كتابة الملف
                        s3.put_object(
                            Bucket=config["bucket"],
                            Key=path,
                            Body=content.encode("utf-8")
                        )
                        
                        return True
                    
                    elif method == "delete":
                        # حذف الملف
                        s3.delete_object(Bucket=config["bucket"], Key=path)
                        return True
                    
                    elif method == "list":
                        # قائمة الملفات
                        prefix = path + "/" if path else ""
                        response = s3.list_objects_v2(Bucket=config["bucket"], Prefix=prefix)
                        
                        if "Contents" in response:
                            return [obj["Key"] for obj in response["Contents"]]
                        else:
                            return []
                
                except ImportError:
                    logger.error("مكتبة boto3 غير مثبتة")
                    return None
                
                except Exception as e:
                    logger.error(f"خطأ في عملية S3: {e}")
                    return None
            
            else:
                logger.warning(f"نوع تخزين الملفات غير مدعوم: {config.get('type')}")
                return None
        
        except Exception as e:
            logger.error(f"خطأ في عملية الملفات: {e}")
            return None
    
    def _load_config(self) -> Dict:
        """
        تحميل الإعدادات
        
        Returns:
            الإعدادات
        """
        # التحقق من وجود ملف الإعدادات
        if os.path.exists(self.config_path):
            try:
                # قراءة الإعدادات من الملف
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"خطأ في قراءة ملف الإعدادات: {e}")
        
        # إرجاع إعدادات افتراضية
        return {}
    
    def _save_config(self) -> None:
        """
        حفظ الإعدادات
        """
        try:
            # إنشاء المجلد إذا لم يكن موجوداً
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # كتابة الإعدادات إلى الملف
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            logger.info("تم حفظ إعدادات التكاملات")
        
        except Exception as e:
            logger.error(f"خطأ في حفظ ملف الإعدادات: {e}")
    
    def _get_default_config_path(self) -> str:
        """
        الحصول على مسار ملف الإعدادات الافتراضي
        
        Returns:
            مسار ملف الإعدادات الافتراضي
        """
        import os
        
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "integrations.json")
