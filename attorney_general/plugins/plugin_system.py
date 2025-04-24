"""
نظام الإضافات (Plugin System) لنظام Attorney-General.AI
يوفر آلية لتوسيع وظائف النظام من خلال الإضافات
"""

import logging
import json
import os
import importlib.util
import inspect
from typing import Dict, List, Optional, Any, Callable, Type
from datetime import datetime

logger = logging.getLogger("plugin_system")

class PluginSystem:
    """
    نظام الإضافات
    يوفر آلية لتوسيع وظائف النظام من خلال الإضافات
    """
    
    def __init__(self, plugins_dir: str = None):
        """
        تهيئة نظام الإضافات
        
        Args:
            plugins_dir: مسار مجلد الإضافات
        """
        # إعداد مسار مجلد الإضافات
        self.plugins_dir = plugins_dir or self._get_default_plugins_dir()
        
        # إنشاء المجلد إذا لم يكن موجوداً
        os.makedirs(self.plugins_dir, exist_ok=True)
        
        # إعداد قاموس الإضافات
        self.plugins = {}
        
        # إعداد قاموس الإضافات المعطلة
        self.disabled_plugins = {}
        
        # تحميل الإضافات
        self._load_plugins()
        
        logger.info("تم تهيئة نظام الإضافات")
    
    def get_plugin(self, plugin_id: str) -> Optional[Any]:
        """
        الحصول على إضافة
        
        Args:
            plugin_id: معرف الإضافة
            
        Returns:
            الإضافة أو None إذا لم تكن موجودة
        """
        return self.plugins.get(plugin_id)
    
    def get_all_plugins(self) -> Dict[str, Any]:
        """
        الحصول على جميع الإضافات
        
        Returns:
            قاموس الإضافات
        """
        return self.plugins
    
    def get_plugin_info(self, plugin_id: str) -> Optional[Dict]:
        """
        الحصول على معلومات الإضافة
        
        Args:
            plugin_id: معرف الإضافة
            
        Returns:
            معلومات الإضافة أو None إذا لم تكن موجودة
        """
        plugin = self.get_plugin(plugin_id)
        
        if plugin is None:
            return None
        
        # الحصول على معلومات الإضافة
        info = {
            "id": plugin_id,
            "name": getattr(plugin, "name", plugin_id),
            "description": getattr(plugin, "description", ""),
            "version": getattr(plugin, "version", "1.0.0"),
            "author": getattr(plugin, "author", ""),
            "enabled": True
        }
        
        return info
    
    def get_all_plugin_info(self, include_disabled: bool = False) -> List[Dict]:
        """
        الحصول على معلومات جميع الإضافات
        
        Args:
            include_disabled: ما إذا كان يجب تضمين الإضافات المعطلة
            
        Returns:
            قائمة معلومات الإضافات
        """
        # الحصول على معلومات الإضافات المفعلة
        plugin_info = []
        
        for plugin_id, plugin in self.plugins.items():
            info = self.get_plugin_info(plugin_id)
            if info:
                plugin_info.append(info)
        
        # إضافة معلومات الإضافات المعطلة إذا كان مطلوباً
        if include_disabled:
            for plugin_id, plugin_path in self.disabled_plugins.items():
                plugin_info.append({
                    "id": plugin_id,
                    "name": plugin_id,
                    "description": "إضافة معطلة",
                    "version": "unknown",
                    "author": "unknown",
                    "enabled": False,
                    "path": plugin_path
                })
        
        return plugin_info
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """
        تفعيل إضافة
        
        Args:
            plugin_id: معرف الإضافة
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود الإضافة في قائمة الإضافات المعطلة
        if plugin_id not in self.disabled_plugins:
            logger.warning(f"الإضافة {plugin_id} غير موجودة في قائمة الإضافات المعطلة")
            return False
        
        # الحصول على مسار الإضافة
        plugin_path = self.disabled_plugins[plugin_id]
        
        # تحميل الإضافة
        plugin = self._load_plugin_from_path(plugin_path)
        
        if plugin is None:
            logger.error(f"فشل في تحميل الإضافة {plugin_id} من المسار {plugin_path}")
            return False
        
        # إضافة الإضافة إلى قاموس الإضافات
        self.plugins[plugin_id] = plugin
        
        # إزالة الإضافة من قاموس الإضافات المعطلة
        del self.disabled_plugins[plugin_id]
        
        logger.info(f"تم تفعيل الإضافة: {plugin_id}")
        return True
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """
        تعطيل إضافة
        
        Args:
            plugin_id: معرف الإضافة
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود الإضافة
        if plugin_id not in self.plugins:
            logger.warning(f"الإضافة {plugin_id} غير موجودة")
            return False
        
        # الحصول على مسار الإضافة
        plugin = self.plugins[plugin_id]
        plugin_path = getattr(plugin, "__file__", "")
        
        # إضافة الإضافة إلى قاموس الإضافات المعطلة
        self.disabled_plugins[plugin_id] = plugin_path
        
        # إزالة الإضافة من قاموس الإضافات
        del self.plugins[plugin_id]
        
        logger.info(f"تم تعطيل الإضافة: {plugin_id}")
        return True
    
    def reload_plugin(self, plugin_id: str) -> bool:
        """
        إعادة تحميل إضافة
        
        Args:
            plugin_id: معرف الإضافة
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود الإضافة
        if plugin_id not in self.plugins:
            logger.warning(f"الإضافة {plugin_id} غير موجودة")
            return False
        
        # الحصول على مسار الإضافة
        plugin = self.plugins[plugin_id]
        plugin_path = getattr(plugin, "__file__", "")
        
        if not plugin_path:
            logger.error(f"لا يمكن تحديد مسار الإضافة {plugin_id}")
            return False
        
        # إزالة الإضافة من قاموس الإضافات
        del self.plugins[plugin_id]
        
        # تحميل الإضافة
        plugin = self._load_plugin_from_path(plugin_path)
        
        if plugin is None:
            logger.error(f"فشل في إعادة تحميل الإضافة {plugin_id} من المسار {plugin_path}")
            return False
        
        # إضافة الإضافة إلى قاموس الإضافات
        self.plugins[plugin_id] = plugin
        
        logger.info(f"تم إعادة تحميل الإضافة: {plugin_id}")
        return True
    
    def reload_all_plugins(self) -> bool:
        """
        إعادة تحميل جميع الإضافات
        
        Returns:
            نجاح العملية
        """
        # الحصول على قائمة معرفات الإضافات
        plugin_ids = list(self.plugins.keys())
        
        # إعادة تحميل كل إضافة
        success = True
        
        for plugin_id in plugin_ids:
            if not self.reload_plugin(plugin_id):
                success = False
        
        return success
    
    def install_plugin(self, plugin_path: str) -> Optional[str]:
        """
        تثبيت إضافة
        
        Args:
            plugin_path: مسار الإضافة
            
        Returns:
            معرف الإضافة أو None في حالة الفشل
        """
        # التحقق من وجود الملف
        if not os.path.exists(plugin_path):
            logger.error(f"ملف الإضافة {plugin_path} غير موجود")
            return None
        
        # الحصول على اسم الملف
        file_name = os.path.basename(plugin_path)
        
        # نسخ الملف إلى مجلد الإضافات
        target_path = os.path.join(self.plugins_dir, file_name)
        
        try:
            import shutil
            shutil.copy2(plugin_path, target_path)
        except Exception as e:
            logger.error(f"خطأ في نسخ ملف الإضافة: {e}")
            return None
        
        # تحميل الإضافة
        plugin = self._load_plugin_from_path(target_path)
        
        if plugin is None:
            logger.error(f"فشل في تحميل الإضافة من المسار {target_path}")
            return None
        
        # الحصول على معرف الإضافة
        plugin_id = getattr(plugin, "id", os.path.splitext(file_name)[0])
        
        # إضافة الإضافة إلى قاموس الإضافات
        self.plugins[plugin_id] = plugin
        
        logger.info(f"تم تثبيت الإضافة: {plugin_id}")
        return plugin_id
    
    def uninstall_plugin(self, plugin_id: str) -> bool:
        """
        إلغاء تثبيت إضافة
        
        Args:
            plugin_id: معرف الإضافة
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود الإضافة
        plugin = None
        plugin_path = ""
        
        if plugin_id in self.plugins:
            plugin = self.plugins[plugin_id]
            plugin_path = getattr(plugin, "__file__", "")
            
            # إزالة الإضافة من قاموس الإضافات
            del self.plugins[plugin_id]
        elif plugin_id in self.disabled_plugins:
            plugin_path = self.disabled_plugins[plugin_id]
            
            # إزالة الإضافة من قاموس الإضافات المعطلة
            del self.disabled_plugins[plugin_id]
        else:
            logger.warning(f"الإضافة {plugin_id} غير موجودة")
            return False
        
        # التحقق من وجود مسار الإضافة
        if not plugin_path:
            logger.error(f"لا يمكن تحديد مسار الإضافة {plugin_id}")
            return False
        
        # التحقق من أن الملف موجود في مجلد الإضافات
        if not plugin_path.startswith(self.plugins_dir):
            logger.warning(f"الإضافة {plugin_id} ليست في مجلد الإضافات")
            return False
        
        # حذف ملف الإضافة
        try:
            os.remove(plugin_path)
        except Exception as e:
            logger.error(f"خطأ في حذف ملف الإضافة: {e}")
            return False
        
        logger.info(f"تم إلغاء تثبيت الإضافة: {plugin_id}")
        return True
    
    def call_plugin_method(self, plugin_id: str, method_name: str, *args, **kwargs) -> Any:
        """
        استدعاء طريقة في إضافة
        
        Args:
            plugin_id: معرف الإضافة
            method_name: اسم الطريقة
            *args: المعاملات الموضعية
            **kwargs: المعاملات المسماة
            
        Returns:
            نتيجة استدعاء الطريقة
        """
        # الحصول على الإضافة
        plugin = self.get_plugin(plugin_id)
        
        if plugin is None:
            logger.warning(f"الإضافة {plugin_id} غير موجودة")
            return None
        
        # التحقق من وجود الطريقة
        if not hasattr(plugin, method_name):
            logger.warning(f"الطريقة {method_name} غير موجودة في الإضافة {plugin_id}")
            return None
        
        # الحصول على الطريقة
        method = getattr(plugin, method_name)
        
        # التحقق من أن الطريقة قابلة للاستدعاء
        if not callable(method):
            logger.warning(f"الخاصية {method_name} في الإضافة {plugin_id} ليست طريقة")
            return None
        
        # استدعاء الطريقة
        try:
            return method(*args, **kwargs)
        except Exception as e:
            logger.error(f"خطأ في استدعاء الطريقة {method_name} في الإضافة {plugin_id}: {e}")
            return None
    
    def get_plugin_methods(self, plugin_id: str) -> List[str]:
        """
        الحصول على قائمة طرق الإضافة
        
        Args:
            plugin_id: معرف الإضافة
            
        Returns:
            قائمة أسماء الطرق
        """
        # الحصول على الإضافة
        plugin = self.get_plugin(plugin_id)
        
        if plugin is None:
            logger.warning(f"الإضافة {plugin_id} غير موجودة")
            return []
        
        # الحصول على قائمة الطرق
        methods = []
        
        for name, member in inspect.getmembers(plugin, inspect.ismethod):
            # تجاهل الطرق الخاصة
            if not name.startswith("_"):
                methods.append(name)
        
        return methods
    
    def _load_plugins(self) -> None:
        """
        تحميل الإضافات من مجلد الإضافات
        """
        # التحقق من وجود المجلد
        if not os.path.exists(self.plugins_dir):
            logger.warning(f"مجلد الإضافات {self.plugins_dir} غير موجود")
            return
        
        # الحصول على قائمة ملفات Python في المجلد
        plugin_files = []
        
        for file_name in os.listdir(self.plugins_dir):
            if file_name.endswith(".py"):
                plugin_files.append(os.path.join(self.plugins_dir, file_name))
        
        # تحميل كل إضافة
        for plugin_path in plugin_files:
            plugin = self._load_plugin_from_path(plugin_path)
            
            if plugin is not None:
                # الحصول على معرف الإضافة
                plugin_id = getattr(plugin, "id", os.path.splitext(os.path.basename(plugin_path))[0])
                
                # إضافة الإضافة إلى قاموس الإضافات
                self.plugins[plugin_id] = plugin
                
                logger.info(f"تم تحميل الإضافة: {plugin_id}")
    
    def _load_plugin_from_path(self, plugin_path: str) -> Optional[Any]:
        """
        تحميل إضافة من مسار
        
        Args:
            plugin_path: مسار الإضافة
            
        Returns:
            الإضافة أو None في حالة الفشل
        """
        try:
            # الحصول على اسم الوحدة
            module_name = os.path.splitext(os.path.basename(plugin_path))[0]
            
            # تحميل المواصفات
            spec = importlib.util.spec_from_file_location(module_name, plugin_path)
            
            if spec is None:
                logger.error(f"فشل في تحميل مواصفات الإضافة من المسار {plugin_path}")
                return None
            
            # تحميل الوحدة
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # التحقق من وجود فئة الإضافة
            plugin_class = None
            
            for name, member in inspect.getmembers(module, inspect.isclass):
                # البحث عن فئة تنتهي بـ "Plugin"
                if name.endswith("Plugin"):
                    plugin_class = member
                    break
            
            if plugin_class is None:
                logger.warning(f"لم يتم العثور على فئة إضافة في الوحدة {module_name}")
                return module
            
            # إنشاء كائن من فئة الإضافة
            plugin = plugin_class()
            
            # إضافة مسار الملف إلى الكائن
            setattr(plugin, "__file__", plugin_path)
            
            return plugin
        
        except Exception as e:
            logger.error(f"خطأ في تحميل الإضافة من المسار {plugin_path}: {e}")
            return None
    
    def _get_default_plugins_dir(self) -> str:
        """
        الحصول على مسار مجلد الإضافات الافتراضي
        
        Returns:
            مسار مجلد الإضافات الافتراضي
        """
        import os
        
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins")
