"""
نظام الأمان (Security System) لنظام Attorney-General.AI
يوفر آليات التحقق من الأمان وتحليل المخاطر
"""

import logging
import json
import re
import hashlib
import base64
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger("security_system")

class SecuritySystem:
    """
    نظام الأمان
    يوفر آليات التحقق من الأمان وتحليل المخاطر
    """
    
    def __init__(self, security_config: Dict = None):
        """
        تهيئة نظام الأمان
        
        Args:
            security_config: إعدادات الأمان
        """
        # إعداد تكوين الأمان
        self.security_config = security_config or self._get_default_security_config()
        
        # إعداد سجل الأحداث الأمنية
        self.security_events = []
        
        # إعداد قائمة القواعد
        self.rules = self._initialize_security_rules()
        
        logger.info("تم تهيئة نظام الأمان")
    
    def analyze_input(self, input_data: Any, context: Dict = None) -> Dict:
        """
        تحليل المدخلات للتحقق من الأمان
        
        Args:
            input_data: البيانات المدخلة
            context: سياق التحليل
            
        Returns:
            نتائج التحليل
        """
        if context is None:
            context = {}
        
        # تحويل البيانات إلى نص
        input_text = self._convert_to_text(input_data)
        
        # تطبيق قواعد الأمان
        issues = []
        
        for rule in self.rules:
            if rule["enabled"]:
                rule_result = self._apply_rule(rule, input_text, context)
                if rule_result["triggered"]:
                    issues.append({
                        "rule_id": rule["id"],
                        "rule_name": rule["name"],
                        "severity": rule["severity"],
                        "description": rule["description"],
                        "matches": rule_result["matches"]
                    })
        
        # تحديد مستوى الخطورة الإجمالي
        severity_level = self._calculate_severity(issues)
        
        # إنشاء نتائج التحليل
        analysis_result = {
            "is_safe": severity_level == "safe",
            "severity_level": severity_level,
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        }
        
        # تسجيل الحدث الأمني
        self._log_security_event("input_analysis", {
            "result": analysis_result,
            "context": context
        })
        
        return analysis_result
    
    def analyze_output(self, output_data: Any, context: Dict = None) -> Dict:
        """
        تحليل المخرجات للتحقق من الأمان
        
        Args:
            output_data: البيانات المخرجة
            context: سياق التحليل
            
        Returns:
            نتائج التحليل
        """
        if context is None:
            context = {}
        
        # تحويل البيانات إلى نص
        output_text = self._convert_to_text(output_data)
        
        # تطبيق قواعد الأمان
        issues = []
        
        for rule in self.rules:
            if rule["enabled"] and rule.get("check_output", True):
                rule_result = self._apply_rule(rule, output_text, context)
                if rule_result["triggered"]:
                    issues.append({
                        "rule_id": rule["id"],
                        "rule_name": rule["name"],
                        "severity": rule["severity"],
                        "description": rule["description"],
                        "matches": rule_result["matches"]
                    })
        
        # تحديد مستوى الخطورة الإجمالي
        severity_level = self._calculate_severity(issues)
        
        # إنشاء نتائج التحليل
        analysis_result = {
            "is_safe": severity_level == "safe",
            "severity_level": severity_level,
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        }
        
        # تسجيل الحدث الأمني
        self._log_security_event("output_analysis", {
            "result": analysis_result,
            "context": context
        })
        
        return analysis_result
    
    def sanitize_input(self, input_data: Any, context: Dict = None) -> Tuple[Any, Dict]:
        """
        تنظيف المدخلات من المحتوى الضار
        
        Args:
            input_data: البيانات المدخلة
            context: سياق التنظيف
            
        Returns:
            البيانات المنظفة ونتائج التنظيف
        """
        if context is None:
            context = {}
        
        # تحليل المدخلات
        analysis_result = self.analyze_input(input_data, context)
        
        # إذا كانت المدخلات آمنة، إرجاعها كما هي
        if analysis_result["is_safe"]:
            return input_data, {
                "sanitized": False,
                "original_analysis": analysis_result
            }
        
        # تحويل البيانات إلى نص
        input_text = self._convert_to_text(input_data)
        sanitized_text = input_text
        
        # تنظيف المحتوى الضار
        for issue in analysis_result["issues"]:
            for match in issue["matches"]:
                # استبدال المحتوى الضار
                sanitized_text = sanitized_text.replace(match, "[REDACTED]")
        
        # تحويل النص المنظف إلى نوع البيانات الأصلي
        sanitized_data = self._convert_from_text(sanitized_text, input_data)
        
        # تسجيل الحدث الأمني
        self._log_security_event("input_sanitization", {
            "original_analysis": analysis_result,
            "context": context
        })
        
        return sanitized_data, {
            "sanitized": True,
            "original_analysis": analysis_result
        }
    
    def validate_request(self, request_data: Dict, context: Dict = None) -> Dict:
        """
        التحقق من صحة الطلب
        
        Args:
            request_data: بيانات الطلب
            context: سياق التحقق
            
        Returns:
            نتائج التحقق
        """
        if context is None:
            context = {}
        
        # التحقق من وجود البيانات المطلوبة
        required_fields = context.get("required_fields", [])
        missing_fields = []
        
        for field in required_fields:
            if field not in request_data:
                missing_fields.append(field)
        
        # التحقق من صحة البيانات
        validation_errors = []
        
        for field, value in request_data.items():
            # التحقق من نوع البيانات
            expected_type = context.get(f"{field}_type")
            if expected_type and not self._validate_type(value, expected_type):
                validation_errors.append({
                    "field": field,
                    "error": f"نوع البيانات غير صحيح. المتوقع: {expected_type}"
                })
            
            # التحقق من الحد الأدنى والأقصى
            if isinstance(value, (int, float)):
                min_value = context.get(f"{field}_min")
                max_value = context.get(f"{field}_max")
                
                if min_value is not None and value < min_value:
                    validation_errors.append({
                        "field": field,
                        "error": f"القيمة أقل من الحد الأدنى. الحد الأدنى: {min_value}"
                    })
                
                if max_value is not None and value > max_value:
                    validation_errors.append({
                        "field": field,
                        "error": f"القيمة أكبر من الحد الأقصى. الحد الأقصى: {max_value}"
                    })
            
            # التحقق من طول النص
            if isinstance(value, str):
                min_length = context.get(f"{field}_min_length")
                max_length = context.get(f"{field}_max_length")
                
                if min_length is not None and len(value) < min_length:
                    validation_errors.append({
                        "field": field,
                        "error": f"النص أقصر من الحد الأدنى. الحد الأدنى: {min_length}"
                    })
                
                if max_length is not None and len(value) > max_length:
                    validation_errors.append({
                        "field": field,
                        "error": f"النص أطول من الحد الأقصى. الحد الأقصى: {max_length}"
                    })
                
                # التحقق من النمط
                pattern = context.get(f"{field}_pattern")
                if pattern and not re.match(pattern, value):
                    validation_errors.append({
                        "field": field,
                        "error": f"النص لا يتطابق مع النمط المطلوب"
                    })
        
        # إنشاء نتائج التحقق
        validation_result = {
            "is_valid": len(missing_fields) == 0 and len(validation_errors) == 0,
            "missing_fields": missing_fields,
            "validation_errors": validation_errors,
            "timestamp": datetime.now().isoformat()
        }
        
        # تسجيل الحدث الأمني
        self._log_security_event("request_validation", {
            "result": validation_result,
            "context": context
        })
        
        return validation_result
    
    def generate_hash(self, data: Any, algorithm: str = "sha256") -> str:
        """
        إنشاء قيمة تجزئة للبيانات
        
        Args:
            data: البيانات
            algorithm: خوارزمية التجزئة
            
        Returns:
            قيمة التجزئة
        """
        # تحويل البيانات إلى نص
        data_text = self._convert_to_text(data)
        
        # إنشاء قيمة التجزئة
        if algorithm == "md5":
            hash_value = hashlib.md5(data_text.encode()).hexdigest()
        elif algorithm == "sha1":
            hash_value = hashlib.sha1(data_text.encode()).hexdigest()
        elif algorithm == "sha256":
            hash_value = hashlib.sha256(data_text.encode()).hexdigest()
        elif algorithm == "sha512":
            hash_value = hashlib.sha512(data_text.encode()).hexdigest()
        else:
            raise ValueError(f"خوارزمية التجزئة غير مدعومة: {algorithm}")
        
        return hash_value
    
    def encrypt_data(self, data: str, key: str = None) -> str:
        """
        تشفير البيانات
        
        Args:
            data: البيانات
            key: مفتاح التشفير
            
        Returns:
            البيانات المشفرة
        """
        # استخدام المفتاح الافتراضي إذا لم يتم تحديد مفتاح
        if key is None:
            key = self.security_config["encryption_key"]
        
        # في الإصدار الحالي، نستخدم تشفير بسيط
        # في الإصدار النهائي، يمكن استخدام مكتبات تشفير متقدمة
        
        # تشفير البيانات باستخدام XOR
        encrypted_bytes = bytearray()
        key_bytes = key.encode()
        data_bytes = data.encode()
        
        for i in range(len(data_bytes)):
            key_byte = key_bytes[i % len(key_bytes)]
            encrypted_bytes.append(data_bytes[i] ^ key_byte)
        
        # تحويل البيانات المشفرة إلى نص
        encrypted_data = base64.b64encode(encrypted_bytes).decode()
        
        return encrypted_data
    
    def decrypt_data(self, encrypted_data: str, key: str = None) -> str:
        """
        فك تشفير البيانات
        
        Args:
            encrypted_data: البيانات المشفرة
            key: مفتاح التشفير
            
        Returns:
            البيانات الأصلية
        """
        # استخدام المفتاح الافتراضي إذا لم يتم تحديد مفتاح
        if key is None:
            key = self.security_config["encryption_key"]
        
        # فك تشفير البيانات
        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
            decrypted_bytes = bytearray()
            key_bytes = key.encode()
            
            for i in range(len(encrypted_bytes)):
                key_byte = key_bytes[i % len(key_bytes)]
                decrypted_bytes.append(encrypted_bytes[i] ^ key_byte)
            
            # تحويل البيانات المفكوكة إلى نص
            decrypted_data = decrypted_bytes.decode()
            
            return decrypted_data
        
        except Exception as e:
            logger.error(f"خطأ في فك تشفير البيانات: {e}")
            return ""
    
    def get_security_events(self, event_type: str = None, limit: int = None) -> List[Dict]:
        """
        الحصول على الأحداث الأمنية
        
        Args:
            event_type: نوع الحدث (اختياري)
            limit: الحد الأقصى لعدد الأحداث (اختياري)
            
        Returns:
            الأحداث الأمنية
        """
        # تصفية الأحداث حسب النوع
        filtered_events = self.security_events
        
        if event_type:
            filtered_events = [
                event for event in filtered_events
                if event["type"] == event_type
            ]
        
        # ترتيب الأحداث حسب الطابع الزمني (الأحدث أولاً)
        sorted_events = sorted(
            filtered_events,
            key=lambda event: event["timestamp"],
            reverse=True
        )
        
        # تطبيق الحد
        if limit:
            sorted_events = sorted_events[:limit]
        
        return sorted_events
    
    def add_security_rule(self, rule: Dict) -> bool:
        """
        إضافة قاعدة أمان جديدة
        
        Args:
            rule: قاعدة الأمان
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود المعلومات المطلوبة
        required_fields = ["id", "name", "description", "pattern", "severity"]
        
        for field in required_fields:
            if field not in rule:
                logger.error(f"حقل مطلوب مفقود في قاعدة الأمان: {field}")
                return False
        
        # التحقق من عدم وجود قاعدة بنفس المعرف
        for existing_rule in self.rules:
            if existing_rule["id"] == rule["id"]:
                logger.error(f"قاعدة أمان بالمعرف {rule['id']} موجودة مسبقاً")
                return False
        
        # إضافة القاعدة
        self.rules.append(rule)
        
        logger.info(f"تم إضافة قاعدة أمان جديدة: {rule['name']} ({rule['id']})")
        return True
    
    def update_security_rule(self, rule_id: str, updates: Dict) -> bool:
        """
        تحديث قاعدة أمان
        
        Args:
            rule_id: معرف القاعدة
            updates: التحديثات
            
        Returns:
            نجاح العملية
        """
        # البحث عن القاعدة
        for i, rule in enumerate(self.rules):
            if rule["id"] == rule_id:
                # تحديث القاعدة
                self.rules[i].update(updates)
                
                logger.info(f"تم تحديث قاعدة الأمان: {rule['name']} ({rule['id']})")
                return True
        
        logger.error(f"قاعدة أمان بالمعرف {rule_id} غير موجودة")
        return False
    
    def delete_security_rule(self, rule_id: str) -> bool:
        """
        حذف قاعدة أمان
        
        Args:
            rule_id: معرف القاعدة
            
        Returns:
            نجاح العملية
        """
        # البحث عن القاعدة
        for i, rule in enumerate(self.rules):
            if rule["id"] == rule_id:
                # حذف القاعدة
                del self.rules[i]
                
                logger.info(f"تم حذف قاعدة الأمان: {rule['name']} ({rule['id']})")
                return True
        
        logger.error(f"قاعدة أمان بالمعرف {rule_id} غير موجودة")
        return False
    
    def _initialize_security_rules(self) -> List[Dict]:
        """
        تهيئة قواعد الأمان
        
        Returns:
            قواعد الأمان
        """
        return [
            {
                "id": "sql_injection",
                "name": "SQL Injection",
                "description": "محاولة حقن SQL",
                "pattern": r"(\b(select|insert|update|delete|drop|alter|create|exec)\b.*\b(from|into|table|database|values)\b)|('--)|(\b(union|join)\b.*\bselect\b)",
                "severity": "high",
                "enabled": True,
                "check_output": False
            },
            {
                "id": "xss",
                "name": "Cross-Site Scripting (XSS)",
                "description": "محاولة هجوم XSS",
                "pattern": r"<script.*?>|javascript:|onerror=|onclick=|onload=|eval\(|document\.cookie",
                "severity": "high",
                "enabled": True,
                "check_output": True
            },
            {
                "id": "path_traversal",
                "name": "Path Traversal",
                "description": "محاولة اختراق المسار",
                "pattern": r"\.\.\/|\.\.\\|~\/|~\\|\/etc\/|\/var\/|\/bin\/|C:\\Windows\\|C:\\Program Files\\",
                "severity": "high",
                "enabled": True,
                "check_output": False
            },
            {
                "id": "command_injection",
                "name": "Command Injection",
                "description": "محاولة حقن أوامر",
                "pattern": r";\s*(\w+\s*\|\s*\w+|\w+\s*>\s*\w+|\w+\s*>>\s*\w+)|`.*?`|\$\(.*?\)|\|.*?;",
                "severity": "high",
                "enabled": True,
                "check_output": False
            },
            {
                "id": "sensitive_data",
                "name": "Sensitive Data",
                "description": "بيانات حساسة",
                "pattern": r"password|passwd|pwd|secret|api[_\-\s]?key|access[_\-\s]?token|auth[_\-\s]?token|credentials",
                "severity": "medium",
                "enabled": True,
                "check_output": True
            }
        ]
    
    def _apply_rule(self, rule: Dict, text: str, context: Dict) -> Dict:
        """
        تطبيق قاعدة أمان
        
        Args:
            rule: قاعدة الأمان
            text: النص
            context: السياق
            
        Returns:
            نتيجة تطبيق القاعدة
        """
        # البحث عن تطابقات
        pattern = rule["pattern"]
        matches = re.findall(pattern, text, re.IGNORECASE)
        
        # تحويل المطابقات إلى قائمة نصية
        text_matches = []
        
        if matches:
            if isinstance(matches[0], tuple):
                # إذا كانت المطابقات عبارة عن مجموعات
                for match_tuple in matches:
                    for match in match_tuple:
                        if match:
                            text_matches.append(match)
            else:
                # إذا كانت المطابقات عبارة عن نصوص
                text_matches = matches
        
        # إزالة المطابقات المكررة
        unique_matches = list(set(text_matches))
        
        return {
            "triggered": len(unique_matches) > 0,
            "matches": unique_matches
        }
    
    def _calculate_severity(self, issues: List[Dict]) -> str:
        """
        حساب مستوى الخطورة الإجمالي
        
        Args:
            issues: المشكلات
            
        Returns:
            مستوى الخطورة
        """
        if not issues:
            return "safe"
        
        # حساب عدد المشكلات لكل مستوى خطورة
        severity_counts = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "critical": 0
        }
        
        for issue in issues:
            severity = issue["severity"].lower()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # تحديد مستوى الخطورة الإجمالي
        if severity_counts["critical"] > 0:
            return "critical"
        elif severity_counts["high"] > 0:
            return "high"
        elif severity_counts["medium"] > 0:
            return "medium"
        elif severity_counts["low"] > 0:
            return "low"
        else:
            return "safe"
    
    def _convert_to_text(self, data: Any) -> str:
        """
        تحويل البيانات إلى نص
        
        Args:
            data: البيانات
            
        Returns:
            النص
        """
        if isinstance(data, str):
            return data
        elif isinstance(data, (dict, list)):
            return json.dumps(data)
        else:
            return str(data)
    
    def _convert_from_text(self, text: str, original_data: Any) -> Any:
        """
        تحويل النص إلى نوع البيانات الأصلي
        
        Args:
            text: النص
            original_data: البيانات الأصلية
            
        Returns:
            البيانات المحولة
        """
        if isinstance(original_data, str):
            return text
        elif isinstance(original_data, dict):
            try:
                return json.loads(text)
            except:
                return {}
        elif isinstance(original_data, list):
            try:
                return json.loads(text)
            except:
                return []
        else:
            return text
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """
        التحقق من نوع البيانات
        
        Args:
            value: القيمة
            expected_type: النوع المتوقع
            
        Returns:
            صحة النوع
        """
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "number":
            return isinstance(value, (int, float))
        elif expected_type == "integer":
            return isinstance(value, int)
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "object":
            return isinstance(value, dict)
        else:
            return True
    
    def _log_security_event(self, event_type: str, event_data: Dict) -> None:
        """
        تسجيل حدث أمني
        
        Args:
            event_type: نوع الحدث
            event_data: بيانات الحدث
        """
        # إنشاء الحدث
        event = {
            "type": event_type,
            "data": event_data,
            "timestamp": datetime.now().isoformat()
        }
        
        # إضافة الحدث إلى السجل
        self.security_events.append(event)
        
        # التحقق من حجم السجل
        max_events = self.security_config["max_security_events"]
        if len(self.security_events) > max_events:
            # إزالة الأحداث القديمة
            self.security_events = self.security_events[-max_events:]
    
    def _get_default_security_config(self) -> Dict:
        """
        الحصول على إعدادات الأمان الافتراضية
        
        Returns:
            إعدادات الأمان الافتراضية
        """
        import os
        
        return {
            "encryption_key": os.environ.get("SECURITY_ENCRYPTION_KEY", "default_encryption_key_for_development"),
            "max_security_events": 1000
        }
