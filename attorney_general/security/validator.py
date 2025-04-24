"""
نظام الأمان (Security Validator) لنظام Attorney-General.AI
يتحقق من سلامة الطلبات والإجراءات
"""

import logging
import re
from typing import Dict, List, Optional, Any

logger = logging.getLogger("security_validator")

class SecurityValidator:
    """
    نظام التحقق من الأمان
    يتحقق من سلامة الطلبات والإجراءات
    """
    
    def __init__(self):
        """تهيئة محقق الأمان"""
        # قائمة الأنماط المحظورة
        self._blocked_patterns = [
            r"rm\s+-rf\s+/",  # حذف الجذر
            r"sudo\s+rm",  # حذف باستخدام sudo
            r"eval\(",  # استخدام eval
            r"exec\(",  # استخدام exec
            r"system\(",  # استخدام system
            r"subprocess\.call",  # استخدام subprocess.call
            r"os\.system",  # استخدام os.system
            r"__import__\(",  # استخدام __import__
            r"importlib",  # استخدام importlib
        ]
        
        # قائمة عناوين URL المحظورة
        self._blocked_domains = [
            "evil.com",
            "malware.com",
            "phishing.com",
        ]
        
        logger.info("تم تهيئة محقق الأمان")
    
    def validate_request(self, request: Dict) -> Dict:
        """
        التحقق من سلامة الطلب
        
        Args:
            request: الطلب المراد التحقق منه
            
        Returns:
            نتيجة التحقق
        """
        violations = []
        details = {}
        
        # التحقق من وجود الوكيل
        if "agent" not in request:
            violations.append("الوكيل غير محدد")
        
        # التحقق من وجود البيانات
        if "payload" not in request:
            violations.append("البيانات غير محددة")
        
        # التحقق من سلامة النص
        if "payload" in request and isinstance(request["payload"], str):
            text_violations = self._check_text_safety(request["payload"])
            if text_violations:
                violations.extend(text_violations)
                details["text_violations"] = text_violations
        
        # التحقق من سلامة عناوين URL
        if "payload" in request:
            url_violations = self._check_url_safety(request["payload"])
            if url_violations:
                violations.extend(url_violations)
                details["url_violations"] = url_violations
        
        # التحقق من سلامة الخيارات
        if "options" in request and isinstance(request["options"], dict):
            option_violations = self._check_options_safety(request["options"])
            if option_violations:
                violations.extend(option_violations)
                details["option_violations"] = option_violations
        
        # إرجاع نتيجة التحقق
        return {
            "safe": len(violations) == 0,
            "violations": violations,
            "details": details
        }
    
    def _check_text_safety(self, text: str) -> List[str]:
        """
        التحقق من سلامة النص
        
        Args:
            text: النص المراد التحقق منه
            
        Returns:
            قائمة الانتهاكات
        """
        violations = []
        
        # التحقق من الأنماط المحظورة
        for pattern in self._blocked_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append(f"نمط محظور: {pattern}")
        
        return violations
    
    def _check_url_safety(self, payload: Any) -> List[str]:
        """
        التحقق من سلامة عناوين URL
        
        Args:
            payload: البيانات المراد التحقق منها
            
        Returns:
            قائمة الانتهاكات
        """
        violations = []
        
        # استخراج عناوين URL من النص
        if isinstance(payload, str):
            urls = self._extract_urls(payload)
            
            # التحقق من النطاقات المحظورة
            for url in urls:
                for domain in self._blocked_domains:
                    if domain in url.lower():
                        violations.append(f"نطاق محظور: {domain}")
        
        return violations
    
    def _check_options_safety(self, options: Dict) -> List[str]:
        """
        التحقق من سلامة الخيارات
        
        Args:
            options: الخيارات المراد التحقق منها
            
        Returns:
            قائمة الانتهاكات
        """
        violations = []
        
        # التحقق من وجود خيارات غير آمنة
        if "unsafe" in options and options["unsafe"]:
            violations.append("خيار غير آمن: unsafe")
        
        if "bypass_security" in options and options["bypass_security"]:
            violations.append("خيار غير آمن: bypass_security")
        
        return violations
    
    def _extract_urls(self, text: str) -> List[str]:
        """
        استخراج عناوين URL من النص
        
        Args:
            text: النص المراد استخراج عناوين URL منه
            
        Returns:
            قائمة عناوين URL
        """
        # نمط بسيط لاستخراج عناوين URL
        url_pattern = r'https?://[^\s]+'
        return re.findall(url_pattern, text)
    
    def add_blocked_pattern(self, pattern: str) -> bool:
        """
        إضافة نمط محظور
        
        Args:
            pattern: النمط المراد إضافته
            
        Returns:
            نجاح العملية
        """
        if pattern in self._blocked_patterns:
            logger.warning(f"النمط {pattern} محظور مسبقاً")
            return False
        
        self._blocked_patterns.append(pattern)
        logger.info(f"تم إضافة النمط المحظور: {pattern}")
        return True
    
    def add_blocked_domain(self, domain: str) -> bool:
        """
        إضافة نطاق محظور
        
        Args:
            domain: النطاق المراد إضافته
            
        Returns:
            نجاح العملية
        """
        if domain in self._blocked_domains:
            logger.warning(f"النطاق {domain} محظور مسبقاً")
            return False
        
        self._blocked_domains.append(domain)
        logger.info(f"تم إضافة النطاق المحظور: {domain}")
        return True
    
    def get_blocked_patterns(self) -> List[str]:
        """
        الحصول على قائمة الأنماط المحظورة
        
        Returns:
            قائمة الأنماط المحظورة
        """
        return self._blocked_patterns
    
    def get_blocked_domains(self) -> List[str]:
        """
        الحصول على قائمة النطاقات المحظورة
        
        Returns:
            قائمة النطاقات المحظورة
        """
        return self._blocked_domains
