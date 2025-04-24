"""
نظام التخزين (Storage System) لنظام Attorney-General.AI
يوفر واجهة موحدة للتخزين والاسترجاع
"""

import logging
import json
import os
import shutil
import sqlite3
from typing import Dict, List, Optional, Any, Union, BinaryIO
from datetime import datetime
import uuid

logger = logging.getLogger("storage_system")

class StorageSystem:
    """
    نظام التخزين
    يوفر واجهة موحدة للتخزين والاسترجاع
    """
    
    def __init__(self, storage_config: Dict = None):
        """
        تهيئة نظام التخزين
        
        Args:
            storage_config: إعدادات التخزين
        """
        # إعداد تكوين التخزين
        self.storage_config = storage_config or self._get_default_storage_config()
        
        # إعداد مسارات التخزين
        self.base_path = self.storage_config["base_path"]
        self.conversations_path = os.path.join(self.base_path, "conversations")
        self.files_path = os.path.join(self.base_path, "files")
        self.cache_path = os.path.join(self.base_path, "cache")
        
        # إنشاء المجلدات إذا لم تكن موجودة
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(self.conversations_path, exist_ok=True)
        os.makedirs(self.files_path, exist_ok=True)
        os.makedirs(self.cache_path, exist_ok=True)
        
        # إعداد قاعدة البيانات
        self.db_path = os.path.join(self.base_path, "storage.db")
        self._initialize_database()
        
        logger.info("تم تهيئة نظام التخزين")
    
    def store_conversation(self, conversation_id: str, conversation_data: Dict) -> bool:
        """
        تخزين محادثة
        
        Args:
            conversation_id: معرف المحادثة
            conversation_data: بيانات المحادثة
            
        Returns:
            نجاح العملية
        """
        # إنشاء مسار الملف
        file_path = os.path.join(self.conversations_path, f"{conversation_id}.json")
        
        try:
            # إضافة معلومات التخزين
            conversation_data["_storage_info"] = {
                "stored_at": datetime.now().isoformat(),
                "conversation_id": conversation_id
            }
            
            # كتابة البيانات إلى الملف
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
            
            # تحديث قاعدة البيانات
            self._update_conversation_metadata(conversation_id, conversation_data)
            
            logger.info(f"تم تخزين المحادثة: {conversation_id}")
            return True
        
        except Exception as e:
            logger.error(f"خطأ في تخزين المحادثة {conversation_id}: {e}")
            return False
    
    def retrieve_conversation(self, conversation_id: str) -> Optional[Dict]:
        """
        استرجاع محادثة
        
        Args:
            conversation_id: معرف المحادثة
            
        Returns:
            بيانات المحادثة أو None إذا لم تكن موجودة
        """
        # إنشاء مسار الملف
        file_path = os.path.join(self.conversations_path, f"{conversation_id}.json")
        
        # التحقق من وجود الملف
        if not os.path.exists(file_path):
            logger.warning(f"المحادثة {conversation_id} غير موجودة")
            return None
        
        try:
            # قراءة البيانات من الملف
            with open(file_path, "r", encoding="utf-8") as f:
                conversation_data = json.load(f)
            
            logger.info(f"تم استرجاع المحادثة: {conversation_id}")
            return conversation_data
        
        except Exception as e:
            logger.error(f"خطأ في استرجاع المحادثة {conversation_id}: {e}")
            return None
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        حذف محادثة
        
        Args:
            conversation_id: معرف المحادثة
            
        Returns:
            نجاح العملية
        """
        # إنشاء مسار الملف
        file_path = os.path.join(self.conversations_path, f"{conversation_id}.json")
        
        # التحقق من وجود الملف
        if not os.path.exists(file_path):
            logger.warning(f"المحادثة {conversation_id} غير موجودة")
            return False
        
        try:
            # حذف الملف
            os.remove(file_path)
            
            # حذف البيانات الوصفية من قاعدة البيانات
            self._delete_conversation_metadata(conversation_id)
            
            logger.info(f"تم حذف المحادثة: {conversation_id}")
            return True
        
        except Exception as e:
            logger.error(f"خطأ في حذف المحادثة {conversation_id}: {e}")
            return False
    
    def list_conversations(self, filters: Dict = None, limit: int = None, offset: int = 0) -> List[Dict]:
        """
        قائمة المحادثات
        
        Args:
            filters: مرشحات البحث (اختياري)
            limit: الحد الأقصى لعدد النتائج (اختياري)
            offset: إزاحة النتائج (اختياري)
            
        Returns:
            قائمة المحادثات
        """
        if filters is None:
            filters = {}
        
        try:
            # إنشاء استعلام SQL
            query = "SELECT * FROM conversations"
            params = []
            
            # إضافة المرشحات
            if filters:
                conditions = []
                
                if "user_id" in filters:
                    conditions.append("user_id = ?")
                    params.append(filters["user_id"])
                
                if "start_date" in filters:
                    conditions.append("created_at >= ?")
                    params.append(filters["start_date"])
                
                if "end_date" in filters:
                    conditions.append("created_at <= ?")
                    params.append(filters["end_date"])
                
                if "title" in filters:
                    conditions.append("title LIKE ?")
                    params.append(f"%{filters['title']}%")
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            # إضافة الترتيب
            query += " ORDER BY created_at DESC"
            
            # إضافة الحد والإزاحة
            if limit is not None:
                query += f" LIMIT {limit}"
            
            if offset > 0:
                query += f" OFFSET {offset}"
            
            # تنفيذ الاستعلام
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # تحويل النتائج إلى قائمة
            conversations = []
            
            for row in rows:
                conversation = dict(row)
                conversations.append(conversation)
            
            conn.close()
            
            logger.info(f"تم استرجاع {len(conversations)} محادثة")
            return conversations
        
        except Exception as e:
            logger.error(f"خطأ في استرجاع قائمة المحادثات: {e}")
            return []
    
    def store_file(self, file_data: Union[str, bytes], file_name: str = None, file_type: str = None) -> Optional[str]:
        """
        تخزين ملف
        
        Args:
            file_data: بيانات الملف
            file_name: اسم الملف (اختياري)
            file_type: نوع الملف (اختياري)
            
        Returns:
            معرف الملف أو None في حالة الفشل
        """
        # إنشاء معرف للملف
        file_id = str(uuid.uuid4())
        
        # إنشاء اسم الملف إذا لم يتم تحديده
        if file_name is None:
            file_name = f"{file_id}"
        
        # إنشاء مسار الملف
        file_path = os.path.join(self.files_path, file_id)
        
        try:
            # كتابة البيانات إلى الملف
            if isinstance(file_data, str):
                # إذا كانت البيانات نصية
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_data)
            else:
                # إذا كانت البيانات ثنائية
                with open(file_path, "wb") as f:
                    f.write(file_data)
            
            # تحديث قاعدة البيانات
            self._update_file_metadata(file_id, file_name, file_type)
            
            logger.info(f"تم تخزين الملف: {file_name} ({file_id})")
            return file_id
        
        except Exception as e:
            logger.error(f"خطأ في تخزين الملف {file_name}: {e}")
            return None
    
    def retrieve_file(self, file_id: str, as_binary: bool = False) -> Optional[Union[str, bytes]]:
        """
        استرجاع ملف
        
        Args:
            file_id: معرف الملف
            as_binary: ما إذا كان يجب إرجاع البيانات كبيانات ثنائية
            
        Returns:
            بيانات الملف أو None إذا لم يكن موجوداً
        """
        # إنشاء مسار الملف
        file_path = os.path.join(self.files_path, file_id)
        
        # التحقق من وجود الملف
        if not os.path.exists(file_path):
            logger.warning(f"الملف {file_id} غير موجود")
            return None
        
        try:
            # قراءة البيانات من الملف
            if as_binary:
                # قراءة البيانات كبيانات ثنائية
                with open(file_path, "rb") as f:
                    file_data = f.read()
            else:
                # قراءة البيانات كنص
                with open(file_path, "r", encoding="utf-8") as f:
                    file_data = f.read()
            
            logger.info(f"تم استرجاع الملف: {file_id}")
            return file_data
        
        except Exception as e:
            logger.error(f"خطأ في استرجاع الملف {file_id}: {e}")
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """
        حذف ملف
        
        Args:
            file_id: معرف الملف
            
        Returns:
            نجاح العملية
        """
        # إنشاء مسار الملف
        file_path = os.path.join(self.files_path, file_id)
        
        # التحقق من وجود الملف
        if not os.path.exists(file_path):
            logger.warning(f"الملف {file_id} غير موجود")
            return False
        
        try:
            # حذف الملف
            os.remove(file_path)
            
            # حذف البيانات الوصفية من قاعدة البيانات
            self._delete_file_metadata(file_id)
            
            logger.info(f"تم حذف الملف: {file_id}")
            return True
        
        except Exception as e:
            logger.error(f"خطأ في حذف الملف {file_id}: {e}")
            return False
    
    def list_files(self, filters: Dict = None, limit: int = None, offset: int = 0) -> List[Dict]:
        """
        قائمة الملفات
        
        Args:
            filters: مرشحات البحث (اختياري)
            limit: الحد الأقصى لعدد النتائج (اختياري)
            offset: إزاحة النتائج (اختياري)
            
        Returns:
            قائمة الملفات
        """
        if filters is None:
            filters = {}
        
        try:
            # إنشاء استعلام SQL
            query = "SELECT * FROM files"
            params = []
            
            # إضافة المرشحات
            if filters:
                conditions = []
                
                if "file_type" in filters:
                    conditions.append("file_type = ?")
                    params.append(filters["file_type"])
                
                if "file_name" in filters:
                    conditions.append("file_name LIKE ?")
                    params.append(f"%{filters['file_name']}%")
                
                if "start_date" in filters:
                    conditions.append("created_at >= ?")
                    params.append(filters["start_date"])
                
                if "end_date" in filters:
                    conditions.append("created_at <= ?")
                    params.append(filters["end_date"])
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            # إضافة الترتيب
            query += " ORDER BY created_at DESC"
            
            # إضافة الحد والإزاحة
            if limit is not None:
                query += f" LIMIT {limit}"
            
            if offset > 0:
                query += f" OFFSET {offset}"
            
            # تنفيذ الاستعلام
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # تحويل النتائج إلى قائمة
            files = []
            
            for row in rows:
                file = dict(row)
                files.append(file)
            
            conn.close()
            
            logger.info(f"تم استرجاع {len(files)} ملف")
            return files
        
        except Exception as e:
            logger.error(f"خطأ في استرجاع قائمة الملفات: {e}")
            return []
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict]:
        """
        الحصول على البيانات الوصفية للملف
        
        Args:
            file_id: معرف الملف
            
        Returns:
            البيانات الوصفية للملف أو None إذا لم يكن موجوداً
        """
        try:
            # إنشاء استعلام SQL
            query = "SELECT * FROM files WHERE file_id = ?"
            
            # تنفيذ الاستعلام
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(query, (file_id,))
            row = cursor.fetchone()
            
            conn.close()
            
            if row:
                return dict(row)
            else:
                logger.warning(f"البيانات الوصفية للملف {file_id} غير موجودة")
                return None
        
        except Exception as e:
            logger.error(f"خطأ في استرجاع البيانات الوصفية للملف {file_id}: {e}")
            return None
    
    def store_cache(self, cache_key: str, cache_data: Any, ttl: int = 3600) -> bool:
        """
        تخزين بيانات في ذاكرة التخزين المؤقت
        
        Args:
            cache_key: مفتاح التخزين المؤقت
            cache_data: البيانات
            ttl: مدة الصلاحية بالثواني
            
        Returns:
            نجاح العملية
        """
        # إنشاء مسار الملف
        file_path = os.path.join(self.cache_path, cache_key)
        
        try:
            # تحويل البيانات إلى JSON
            if not isinstance(cache_data, (str, bytes)):
                cache_data = json.dumps(cache_data, ensure_ascii=False)
            
            # كتابة البيانات إلى الملف
            if isinstance(cache_data, str):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(cache_data)
            else:
                with open(file_path, "wb") as f:
                    f.write(cache_data)
            
            # تحديث قاعدة البيانات
            self._update_cache_metadata(cache_key, ttl)
            
            logger.debug(f"تم تخزين البيانات في ذاكرة التخزين المؤقت: {cache_key}")
            return True
        
        except Exception as e:
            logger.error(f"خطأ في تخزين البيانات في ذاكرة التخزين المؤقت {cache_key}: {e}")
            return False
    
    def retrieve_cache(self, cache_key: str, as_json: bool = True) -> Optional[Any]:
        """
        استرجاع بيانات من ذاكرة التخزين المؤقت
        
        Args:
            cache_key: مفتاح التخزين المؤقت
            as_json: ما إذا كان يجب تحليل البيانات كـ JSON
            
        Returns:
            البيانات أو None إذا لم تكن موجودة أو منتهية الصلاحية
        """
        # إنشاء مسار الملف
        file_path = os.path.join(self.cache_path, cache_key)
        
        # التحقق من وجود الملف
        if not os.path.exists(file_path):
            logger.debug(f"البيانات في ذاكرة التخزين المؤقت {cache_key} غير موجودة")
            return None
        
        try:
            # التحقق من صلاحية البيانات
            if not self._is_cache_valid(cache_key):
                # حذف البيانات منتهية الصلاحية
                self.delete_cache(cache_key)
                logger.debug(f"البيانات في ذاكرة التخزين المؤقت {cache_key} منتهية الصلاحية")
                return None
            
            # قراءة البيانات من الملف
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    cache_data = f.read()
                
                # تحليل البيانات كـ JSON إذا كان مطلوباً
                if as_json:
                    try:
                        cache_data = json.loads(cache_data)
                    except:
                        pass
            except:
                # إذا فشلت القراءة كنص، قراءة البيانات كبيانات ثنائية
                with open(file_path, "rb") as f:
                    cache_data = f.read()
            
            logger.debug(f"تم استرجاع البيانات من ذاكرة التخزين المؤقت: {cache_key}")
            return cache_data
        
        except Exception as e:
            logger.error(f"خطأ في استرجاع البيانات من ذاكرة التخزين المؤقت {cache_key}: {e}")
            return None
    
    def delete_cache(self, cache_key: str) -> bool:
        """
        حذف بيانات من ذاكرة التخزين المؤقت
        
        Args:
            cache_key: مفتاح التخزين المؤقت
            
        Returns:
            نجاح العملية
        """
        # إنشاء مسار الملف
        file_path = os.path.join(self.cache_path, cache_key)
        
        # التحقق من وجود الملف
        if not os.path.exists(file_path):
            logger.debug(f"البيانات في ذاكرة التخزين المؤقت {cache_key} غير موجودة")
            return False
        
        try:
            # حذف الملف
            os.remove(file_path)
            
            # حذف البيانات الوصفية من قاعدة البيانات
            self._delete_cache_metadata(cache_key)
            
            logger.debug(f"تم حذف البيانات من ذاكرة التخزين المؤقت: {cache_key}")
            return True
        
        except Exception as e:
            logger.error(f"خطأ في حذف البيانات من ذاكرة التخزين المؤقت {cache_key}: {e}")
            return False
    
    def clear_cache(self) -> bool:
        """
        مسح ذاكرة التخزين المؤقت
        
        Returns:
            نجاح العملية
        """
        try:
            # حذف جميع الملفات في مجلد التخزين المؤقت
            for file_name in os.listdir(self.cache_path):
                file_path = os.path.join(self.cache_path, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            
            # حذف جميع البيانات الوصفية من قاعدة البيانات
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM cache")
            
            conn.commit()
            conn.close()
            
            logger.info("تم مسح ذاكرة التخزين المؤقت")
            return True
        
        except Exception as e:
            logger.error(f"خطأ في مسح ذاكرة التخزين المؤقت: {e}")
            return False
    
    def cleanup_expired_cache(self) -> int:
        """
        تنظيف ذاكرة التخزين المؤقت منتهية الصلاحية
        
        Returns:
            عدد العناصر التي تم حذفها
        """
        try:
            # الحصول على قائمة مفاتيح التخزين المؤقت منتهية الصلاحية
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT cache_key FROM cache WHERE expires_at <= ?", (datetime.now().timestamp(),))
            rows = cursor.fetchall()
            
            conn.close()
            
            # حذف العناصر منتهية الصلاحية
            deleted_count = 0
            
            for row in rows:
                cache_key = row[0]
                if self.delete_cache(cache_key):
                    deleted_count += 1
            
            logger.info(f"تم حذف {deleted_count} عنصر منتهي الصلاحية من ذاكرة التخزين المؤقت")
            return deleted_count
        
        except Exception as e:
            logger.error(f"خطأ في تنظيف ذاكرة التخزين المؤقت منتهية الصلاحية: {e}")
            return 0
    
    def _initialize_database(self) -> None:
        """
        تهيئة قاعدة البيانات
        """
        try:
            # إنشاء اتصال بقاعدة البيانات
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # إنشاء جدول المحادثات
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    title TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    message_count INTEGER,
                    metadata TEXT
                )
            """)
            
            # إنشاء جدول الملفات
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    file_id TEXT PRIMARY KEY,
                    file_name TEXT,
                    file_type TEXT,
                    file_size INTEGER,
                    created_at TEXT,
                    updated_at TEXT,
                    metadata TEXT
                )
            """)
            
            # إنشاء جدول التخزين المؤقت
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    cache_key TEXT PRIMARY KEY,
                    created_at REAL,
                    expires_at REAL
                )
            """)
            
            # حفظ التغييرات
            conn.commit()
            conn.close()
            
            logger.info("تم تهيئة قاعدة البيانات")
        
        except Exception as e:
            logger.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
    
    def _update_conversation_metadata(self, conversation_id: str, conversation_data: Dict) -> None:
        """
        تحديث البيانات الوصفية للمحادثة
        
        Args:
            conversation_id: معرف المحادثة
            conversation_data: بيانات المحادثة
        """
        try:
            # استخراج البيانات الوصفية
            user_id = conversation_data.get("user_id", "")
            title = conversation_data.get("title", "")
            created_at = conversation_data.get("created_at", datetime.now().isoformat())
            updated_at = datetime.now().isoformat()
            message_count = len(conversation_data.get("messages", []))
            
            # تحويل البيانات الوصفية الإضافية إلى JSON
            metadata = {}
            
            for key, value in conversation_data.items():
                if key not in ["user_id", "title", "created_at", "messages", "_storage_info"]:
                    metadata[key] = value
            
            metadata_json = json.dumps(metadata, ensure_ascii=False)
            
            # إنشاء اتصال بقاعدة البيانات
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # التحقق من وجود المحادثة
            cursor.execute("SELECT 1 FROM conversations WHERE conversation_id = ?", (conversation_id,))
            exists = cursor.fetchone() is not None
            
            if exists:
                # تحديث البيانات الوصفية
                cursor.execute("""
                    UPDATE conversations
                    SET user_id = ?, title = ?, updated_at = ?, message_count = ?, metadata = ?
                    WHERE conversation_id = ?
                """, (user_id, title, updated_at, message_count, metadata_json, conversation_id))
            else:
                # إضافة البيانات الوصفية
                cursor.execute("""
                    INSERT INTO conversations (conversation_id, user_id, title, created_at, updated_at, message_count, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (conversation_id, user_id, title, created_at, updated_at, message_count, metadata_json))
            
            # حفظ التغييرات
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"خطأ في تحديث البيانات الوصفية للمحادثة {conversation_id}: {e}")
    
    def _delete_conversation_metadata(self, conversation_id: str) -> None:
        """
        حذف البيانات الوصفية للمحادثة
        
        Args:
            conversation_id: معرف المحادثة
        """
        try:
            # إنشاء اتصال بقاعدة البيانات
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # حذف البيانات الوصفية
            cursor.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))
            
            # حفظ التغييرات
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"خطأ في حذف البيانات الوصفية للمحادثة {conversation_id}: {e}")
    
    def _update_file_metadata(self, file_id: str, file_name: str, file_type: str) -> None:
        """
        تحديث البيانات الوصفية للملف
        
        Args:
            file_id: معرف الملف
            file_name: اسم الملف
            file_type: نوع الملف
        """
        try:
            # الحصول على حجم الملف
            file_path = os.path.join(self.files_path, file_id)
            file_size = os.path.getsize(file_path)
            
            # إنشاء اتصال بقاعدة البيانات
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # التحقق من وجود الملف
            cursor.execute("SELECT 1 FROM files WHERE file_id = ?", (file_id,))
            exists = cursor.fetchone() is not None
            
            # الحصول على الوقت الحالي
            now = datetime.now().isoformat()
            
            if exists:
                # تحديث البيانات الوصفية
                cursor.execute("""
                    UPDATE files
                    SET file_name = ?, file_type = ?, file_size = ?, updated_at = ?
                    WHERE file_id = ?
                """, (file_name, file_type, file_size, now, file_id))
            else:
                # إضافة البيانات الوصفية
                cursor.execute("""
                    INSERT INTO files (file_id, file_name, file_type, file_size, created_at, updated_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (file_id, file_name, file_type, file_size, now, now, "{}"))
            
            # حفظ التغييرات
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"خطأ في تحديث البيانات الوصفية للملف {file_id}: {e}")
    
    def _delete_file_metadata(self, file_id: str) -> None:
        """
        حذف البيانات الوصفية للملف
        
        Args:
            file_id: معرف الملف
        """
        try:
            # إنشاء اتصال بقاعدة البيانات
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # حذف البيانات الوصفية
            cursor.execute("DELETE FROM files WHERE file_id = ?", (file_id,))
            
            # حفظ التغييرات
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"خطأ في حذف البيانات الوصفية للملف {file_id}: {e}")
    
    def _update_cache_metadata(self, cache_key: str, ttl: int) -> None:
        """
        تحديث البيانات الوصفية للتخزين المؤقت
        
        Args:
            cache_key: مفتاح التخزين المؤقت
            ttl: مدة الصلاحية بالثواني
        """
        try:
            # إنشاء اتصال بقاعدة البيانات
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # الحصول على الوقت الحالي
            now = datetime.now().timestamp()
            expires_at = now + ttl
            
            # التحقق من وجود المفتاح
            cursor.execute("SELECT 1 FROM cache WHERE cache_key = ?", (cache_key,))
            exists = cursor.fetchone() is not None
            
            if exists:
                # تحديث البيانات الوصفية
                cursor.execute("""
                    UPDATE cache
                    SET created_at = ?, expires_at = ?
                    WHERE cache_key = ?
                """, (now, expires_at, cache_key))
            else:
                # إضافة البيانات الوصفية
                cursor.execute("""
                    INSERT INTO cache (cache_key, created_at, expires_at)
                    VALUES (?, ?, ?)
                """, (cache_key, now, expires_at))
            
            # حفظ التغييرات
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"خطأ في تحديث البيانات الوصفية للتخزين المؤقت {cache_key}: {e}")
    
    def _delete_cache_metadata(self, cache_key: str) -> None:
        """
        حذف البيانات الوصفية للتخزين المؤقت
        
        Args:
            cache_key: مفتاح التخزين المؤقت
        """
        try:
            # إنشاء اتصال بقاعدة البيانات
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # حذف البيانات الوصفية
            cursor.execute("DELETE FROM cache WHERE cache_key = ?", (cache_key,))
            
            # حفظ التغييرات
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"خطأ في حذف البيانات الوصفية للتخزين المؤقت {cache_key}: {e}")
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """
        التحقق من صلاحية التخزين المؤقت
        
        Args:
            cache_key: مفتاح التخزين المؤقت
            
        Returns:
            ما إذا كان التخزين المؤقت صالحاً
        """
        try:
            # إنشاء اتصال بقاعدة البيانات
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # التحقق من صلاحية التخزين المؤقت
            cursor.execute("""
                SELECT 1 FROM cache
                WHERE cache_key = ? AND expires_at > ?
            """, (cache_key, datetime.now().timestamp()))
            
            is_valid = cursor.fetchone() is not None
            
            conn.close()
            
            return is_valid
        
        except Exception as e:
            logger.error(f"خطأ في التحقق من صلاحية التخزين المؤقت {cache_key}: {e}")
            return False
    
    def _get_default_storage_config(self) -> Dict:
        """
        الحصول على إعدادات التخزين الافتراضية
        
        Returns:
            إعدادات التخزين الافتراضية
        """
        import os
        
        return {
            "base_path": os.path.join(os.path.expanduser("~"), "attorney_general_storage")
        }
