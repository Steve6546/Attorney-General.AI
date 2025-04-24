"""
نظام الاختبار (Test System) لنظام Attorney-General.AI
يوفر آليات لاختبار مكونات النظام والتحقق من صحة عملها
"""

import logging
import json
import os
import time
import unittest
import sys
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

logger = logging.getLogger("test_system")

class TestSystem:
    """
    نظام الاختبار
    يوفر آليات لاختبار مكونات النظام والتحقق من صحة عملها
    """
    
    def __init__(self, tests_dir: str = None):
        """
        تهيئة نظام الاختبار
        
        Args:
            tests_dir: مسار مجلد الاختبارات
        """
        # إعداد مسار مجلد الاختبارات
        self.tests_dir = tests_dir or self._get_default_tests_dir()
        
        # إنشاء المجلد إذا لم يكن موجوداً
        os.makedirs(self.tests_dir, exist_ok=True)
        
        # إعداد قاموس نتائج الاختبارات
        self.test_results = {}
        
        logger.info("تم تهيئة نظام الاختبار")
    
    def run_all_tests(self) -> Dict:
        """
        تشغيل جميع الاختبارات
        
        Returns:
            نتائج الاختبارات
        """
        # الحصول على قائمة ملفات الاختبار
        test_files = self._discover_test_files()
        
        # تشغيل كل ملف اختبار
        results = {}
        
        for test_file in test_files:
            # الحصول على اسم الاختبار
            test_name = os.path.splitext(os.path.basename(test_file))[0]
            
            # تشغيل الاختبار
            result = self.run_test_file(test_file)
            
            # إضافة النتيجة إلى النتائج
            results[test_name] = result
        
        # تحديث نتائج الاختبارات
        self.test_results = results
        
        # حساب الإحصائيات
        stats = self._calculate_test_stats(results)
        
        logger.info(f"تم تشغيل {stats['total']} اختبار: {stats['passed']} ناجح، {stats['failed']} فاشل، {stats['errors']} أخطاء")
        
        return {
            "results": results,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    
    def run_test_file(self, test_file: str) -> Dict:
        """
        تشغيل ملف اختبار
        
        Args:
            test_file: مسار ملف الاختبار
            
        Returns:
            نتيجة الاختبار
        """
        # التحقق من وجود الملف
        if not os.path.exists(test_file):
            logger.warning(f"ملف الاختبار {test_file} غير موجود")
            return {
                "status": "error",
                "message": f"ملف الاختبار غير موجود: {test_file}",
                "details": None
            }
        
        try:
            # تحميل الاختبارات من الملف
            loader = unittest.TestLoader()
            
            # إضافة مسار الملف إلى مسارات النظام
            sys.path.insert(0, os.path.dirname(test_file))
            
            # تحميل الاختبارات
            tests = loader.discover(os.path.dirname(test_file), pattern=os.path.basename(test_file))
            
            # إزالة المسار من مسارات النظام
            sys.path.pop(0)
            
            # تشغيل الاختبارات
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(tests)
            
            # تحليل النتائج
            test_result = {
                "status": "passed" if result.wasSuccessful() else "failed",
                "message": f"تم تشغيل {result.testsRun} اختبار",
                "details": {
                    "tests_run": result.testsRun,
                    "errors": len(result.errors),
                    "failures": len(result.failures),
                    "skipped": len(result.skipped),
                    "error_details": [
                        {
                            "test": str(test),
                            "error": error
                        }
                        for test, error in result.errors
                    ],
                    "failure_details": [
                        {
                            "test": str(test),
                            "failure": failure
                        }
                        for test, failure in result.failures
                    ]
                }
            }
            
            logger.info(f"تم تشغيل اختبار {test_file}: {test_result['status']}")
            return test_result
        
        except Exception as e:
            logger.error(f"خطأ في تشغيل اختبار {test_file}: {e}")
            return {
                "status": "error",
                "message": f"خطأ في تشغيل الاختبار: {str(e)}",
                "details": {
                    "exception": str(e),
                    "exception_type": type(e).__name__
                }
            }
    
    def run_test_class(self, test_class: Any) -> Dict:
        """
        تشغيل فئة اختبار
        
        Args:
            test_class: فئة الاختبار
            
        Returns:
            نتيجة الاختبار
        """
        try:
            # تحميل الاختبارات من الفئة
            loader = unittest.TestLoader()
            tests = loader.loadTestsFromTestCase(test_class)
            
            # تشغيل الاختبارات
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(tests)
            
            # تحليل النتائج
            test_result = {
                "status": "passed" if result.wasSuccessful() else "failed",
                "message": f"تم تشغيل {result.testsRun} اختبار",
                "details": {
                    "tests_run": result.testsRun,
                    "errors": len(result.errors),
                    "failures": len(result.failures),
                    "skipped": len(result.skipped),
                    "error_details": [
                        {
                            "test": str(test),
                            "error": error
                        }
                        for test, error in result.errors
                    ],
                    "failure_details": [
                        {
                            "test": str(test),
                            "failure": failure
                        }
                        for test, failure in result.failures
                    ]
                }
            }
            
            logger.info(f"تم تشغيل اختبار {test_class.__name__}: {test_result['status']}")
            return test_result
        
        except Exception as e:
            logger.error(f"خطأ في تشغيل اختبار {test_class.__name__}: {e}")
            return {
                "status": "error",
                "message": f"خطأ في تشغيل الاختبار: {str(e)}",
                "details": {
                    "exception": str(e),
                    "exception_type": type(e).__name__
                }
            }
    
    def run_test_method(self, test_class: Any, method_name: str) -> Dict:
        """
        تشغيل طريقة اختبار
        
        Args:
            test_class: فئة الاختبار
            method_name: اسم الطريقة
            
        Returns:
            نتيجة الاختبار
        """
        try:
            # تحميل الاختبار من الطريقة
            loader = unittest.TestLoader()
            tests = loader.loadTestsFromName(method_name, test_class)
            
            # تشغيل الاختبار
            runner = unittest.TextTestRunner(verbosity=2)
            result = runner.run(tests)
            
            # تحليل النتائج
            test_result = {
                "status": "passed" if result.wasSuccessful() else "failed",
                "message": f"تم تشغيل اختبار {method_name}",
                "details": {
                    "tests_run": result.testsRun,
                    "errors": len(result.errors),
                    "failures": len(result.failures),
                    "skipped": len(result.skipped),
                    "error_details": [
                        {
                            "test": str(test),
                            "error": error
                        }
                        for test, error in result.errors
                    ],
                    "failure_details": [
                        {
                            "test": str(test),
                            "failure": failure
                        }
                        for test, failure in result.failures
                    ]
                }
            }
            
            logger.info(f"تم تشغيل اختبار {test_class.__name__}.{method_name}: {test_result['status']}")
            return test_result
        
        except Exception as e:
            logger.error(f"خطأ في تشغيل اختبار {test_class.__name__}.{method_name}: {e}")
            return {
                "status": "error",
                "message": f"خطأ في تشغيل الاختبار: {str(e)}",
                "details": {
                    "exception": str(e),
                    "exception_type": type(e).__name__
                }
            }
    
    def get_test_results(self) -> Dict:
        """
        الحصول على نتائج الاختبارات
        
        Returns:
            نتائج الاختبارات
        """
        return self.test_results
    
    def generate_test_report(self, format: str = "json") -> str:
        """
        إنشاء تقرير اختبار
        
        Args:
            format: تنسيق التقرير (json، html)
            
        Returns:
            تقرير الاختبار
        """
        # التحقق من وجود نتائج اختبارات
        if not self.test_results:
            logger.warning("لا توجد نتائج اختبارات")
            return ""
        
        # حساب الإحصائيات
        stats = self._calculate_test_stats(self.test_results)
        
        # إنشاء التقرير
        report_data = {
            "results": self.test_results,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
        if format == "json":
            # إنشاء تقرير JSON
            return json.dumps(report_data, ensure_ascii=False, indent=2)
        
        elif format == "html":
            # إنشاء تقرير HTML
            html = f"""
            <!DOCTYPE html>
            <html dir="rtl">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>تقرير الاختبار</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; direction: rtl; }}
                    h1 {{ color: #333; }}
                    .summary {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
                    .test {{ margin-bottom: 10px; padding: 10px; border-radius: 5px; }}
                    .passed {{ background-color: #dff0d8; }}
                    .failed {{ background-color: #f2dede; }}
                    .error {{ background-color: #fcf8e3; }}
                    .details {{ margin-top: 10px; }}
                </style>
            </head>
            <body>
                <h1>تقرير الاختبار</h1>
                <div class="summary">
                    <h2>ملخص</h2>
                    <p>تم تشغيل {stats['total']} اختبار: {stats['passed']} ناجح، {stats['failed']} فاشل، {stats['errors']} أخطاء</p>
                    <p>نسبة النجاح: {stats['success_rate']}%</p>
                    <p>التاريخ: {report_data['timestamp']}</p>
                </div>
                <h2>النتائج</h2>
            """
            
            # إضافة نتائج كل اختبار
            for test_name, result in self.test_results.items():
                status = result["status"]
                message = result["message"]
                details = result.get("details", {})
                
                html += f"""
                <div class="test {status}">
                    <h3>{test_name}</h3>
                    <p>الحالة: {status}</p>
                    <p>{message}</p>
                """
                
                if details:
                    html += f"""
                    <div class="details">
                        <p>عدد الاختبارات: {details.get('tests_run', 0)}</p>
                        <p>الأخطاء: {details.get('errors', 0)}</p>
                        <p>الفشل: {details.get('failures', 0)}</p>
                        <p>المتخطى: {details.get('skipped', 0)}</p>
                    """
                    
                    # إضافة تفاصيل الأخطاء
                    if details.get('error_details'):
                        html += "<h4>تفاصيل الأخطاء</h4><ul>"
                        for error in details['error_details']:
                            html += f"<li>{error['test']}: {error['error']}</li>"
                        html += "</ul>"
                    
                    # إضافة تفاصيل الفشل
                    if details.get('failure_details'):
                        html += "<h4>تفاصيل الفشل</h4><ul>"
                        for failure in details['failure_details']:
                            html += f"<li>{failure['test']}: {failure['failure']}</li>"
                        html += "</ul>"
                    
                    html += "</div>"
                
                html += "</div>"
            
            html += """
            </body>
            </html>
            """
            
            return html
        
        else:
            logger.warning(f"تنسيق التقرير غير مدعوم: {format}")
            return ""
    
    def save_test_report(self, file_path: str, format: str = "json") -> bool:
        """
        حفظ تقرير اختبار
        
        Args:
            file_path: مسار الملف
            format: تنسيق التقرير (json، html)
            
        Returns:
            نجاح العملية
        """
        # إنشاء التقرير
        report = self.generate_test_report(format)
        
        if not report:
            logger.warning("لا يمكن إنشاء تقرير")
            return False
        
        try:
            # إنشاء المجلد إذا لم يكن موجوداً
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # كتابة التقرير إلى الملف
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report)
            
            logger.info(f"تم حفظ تقرير الاختبار إلى {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"خطأ في حفظ تقرير الاختبار: {e}")
            return False
    
    def create_test_file(self, test_name: str, test_class_name: str, test_methods: List[str] = None) -> str:
        """
        إنشاء ملف اختبار
        
        Args:
            test_name: اسم الاختبار
            test_class_name: اسم فئة الاختبار
            test_methods: قائمة طرق الاختبار
            
        Returns:
            مسار ملف الاختبار
        """
        if test_methods is None:
            test_methods = ["test_example"]
        
        # إنشاء مسار الملف
        file_path = os.path.join(self.tests_dir, f"test_{test_name}.py")
        
        # إنشاء محتوى الملف
        content = f"""
import unittest

class {test_class_name}(unittest.TestCase):
    """
        
        # إضافة طرق الاختبار
        for method in test_methods:
            content += f"""
    def {method}(self):
        # TODO: تنفيذ اختبار
        self.assertTrue(True)
            """
        
        content += """

if __name__ == "__main__":
    unittest.main()
        """
        
        try:
            # إنشاء المجلد إذا لم يكن موجوداً
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # كتابة المحتوى إلى الملف
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.info(f"تم إنشاء ملف اختبار: {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"خطأ في إنشاء ملف اختبار: {e}")
            return ""
    
    def _discover_test_files(self) -> List[str]:
        """
        اكتشاف ملفات الاختبار
        
        Returns:
            قائمة مسارات ملفات الاختبار
        """
        # التحقق من وجود المجلد
        if not os.path.exists(self.tests_dir):
            logger.warning(f"مجلد الاختبارات {self.tests_dir} غير موجود")
            return []
        
        # البحث عن ملفات الاختبار
        test_files = []
        
        for root, _, files in os.walk(self.tests_dir):
            for file in files:
                if file.startswith("test_") and file.endswith(".py"):
                    test_files.append(os.path.join(root, file))
        
        return test_files
    
    def _calculate_test_stats(self, results: Dict) -> Dict:
        """
        حساب إحصائيات الاختبار
        
        Args:
            results: نتائج الاختبار
            
        Returns:
            إحصائيات الاختبار
        """
        # حساب عدد الاختبارات
        total = len(results)
        
        # حساب عدد الاختبارات الناجحة والفاشلة والأخطاء
        passed = 0
        failed = 0
        errors = 0
        
        for result in results.values():
            status = result["status"]
            
            if status == "passed":
                passed += 1
            elif status == "failed":
                failed += 1
            elif status == "error":
                errors += 1
        
        # حساب نسبة النجاح
        success_rate = (passed / total * 100) if total > 0 else 0
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "success_rate": round(success_rate, 2)
        }
    
    def _get_default_tests_dir(self) -> str:
        """
        الحصول على مسار مجلد الاختبارات الافتراضي
        
        Returns:
            مسار مجلد الاختبارات الافتراضي
        """
        import os
        
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests")
