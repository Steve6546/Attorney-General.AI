import unittest
from attorney_general.security.security_system import SecuritySystem

class TestSecuritySystem(unittest.TestCase):
    """
    اختبارات وحدة لنظام الأمان
    """
    
    def setUp(self):
        """
        إعداد بيئة الاختبار
        """
        self.security_system = SecuritySystem()
    
    def test_validate_request(self):
        """
        اختبار التحقق من صحة الطلب
        """
        # إنشاء طلب صحيح
        valid_request = {
            "action": "get_data",
            "user_id": "test_user",
            "timestamp": 1650000000,
            "data": {
                "resource_id": "test_resource"
            }
        }
        
        # التحقق من صحة الطلب
        result = self.security_system.validate_request(valid_request)
        
        # التحقق من نجاح التحقق
        self.assertTrue(result["valid"])
        self.assertIsNone(result["error"])
    
    def test_validate_invalid_request(self):
        """
        اختبار التحقق من طلب غير صحيح
        """
        # إنشاء طلب غير صحيح (بدون حقل action)
        invalid_request = {
            "user_id": "test_user",
            "timestamp": 1650000000,
            "data": {
                "resource_id": "test_resource"
            }
        }
        
        # التحقق من صحة الطلب
        result = self.security_system.validate_request(invalid_request)
        
        # التحقق من فشل التحقق
        self.assertFalse(result["valid"])
        self.assertIsNotNone(result["error"])
    
    def test_check_permissions(self):
        """
        اختبار التحقق من الصلاحيات
        """
        # إضافة صلاحيات للمستخدم
        self.security_system.add_permission("test_user", "get_data", "test_resource")
        
        # التحقق من الصلاحيات
        has_permission = self.security_system.check_permission("test_user", "get_data", "test_resource")
        
        # التحقق من وجود الصلاحية
        self.assertTrue(has_permission)
    
    def test_check_missing_permissions(self):
        """
        اختبار التحقق من صلاحيات غير موجودة
        """
        # التحقق من صلاحيات غير موجودة
        has_permission = self.security_system.check_permission("test_user", "delete_data", "test_resource")
        
        # التحقق من عدم وجود الصلاحية
        self.assertFalse(has_permission)
    
    def test_add_permission(self):
        """
        اختبار إضافة صلاحية
        """
        # إضافة صلاحية
        result = self.security_system.add_permission("test_user", "update_data", "test_resource")
        
        # التحقق من نجاح الإضافة
        self.assertTrue(result)
        
        # التحقق من وجود الصلاحية
        has_permission = self.security_system.check_permission("test_user", "update_data", "test_resource")
        self.assertTrue(has_permission)
    
    def test_remove_permission(self):
        """
        اختبار إزالة صلاحية
        """
        # إضافة صلاحية
        self.security_system.add_permission("test_user", "delete_data", "test_resource")
        
        # التحقق من وجود الصلاحية
        has_permission = self.security_system.check_permission("test_user", "delete_data", "test_resource")
        self.assertTrue(has_permission)
        
        # إزالة الصلاحية
        result = self.security_system.remove_permission("test_user", "delete_data", "test_resource")
        
        # التحقق من نجاح الإزالة
        self.assertTrue(result)
        
        # التحقق من عدم وجود الصلاحية
        has_permission = self.security_system.check_permission("test_user", "delete_data", "test_resource")
        self.assertFalse(has_permission)
    
    def test_get_user_permissions(self):
        """
        اختبار الحصول على صلاحيات المستخدم
        """
        # إضافة صلاحيات
        self.security_system.add_permission("test_user", "get_data", "resource1")
        self.security_system.add_permission("test_user", "update_data", "resource1")
        self.security_system.add_permission("test_user", "get_data", "resource2")
        
        # الحصول على صلاحيات المستخدم
        permissions = self.security_system.get_user_permissions("test_user")
        
        # التحقق من صحة الصلاحيات
        self.assertIsNotNone(permissions)
        self.assertEqual(len(permissions), 3)
        self.assertIn({"action": "get_data", "resource": "resource1"}, permissions)
        self.assertIn({"action": "update_data", "resource": "resource1"}, permissions)
        self.assertIn({"action": "get_data", "resource": "resource2"}, permissions)
    
    def test_get_resource_permissions(self):
        """
        اختبار الحصول على صلاحيات المورد
        """
        # إضافة صلاحيات
        self.security_system.add_permission("user1", "get_data", "test_resource")
        self.security_system.add_permission("user2", "get_data", "test_resource")
        self.security_system.add_permission("user1", "update_data", "test_resource")
        
        # الحصول على صلاحيات المورد
        permissions = self.security_system.get_resource_permissions("test_resource")
        
        # التحقق من صحة الصلاحيات
        self.assertIsNotNone(permissions)
        self.assertEqual(len(permissions), 3)
        self.assertIn({"user": "user1", "action": "get_data"}, permissions)
        self.assertIn({"user": "user2", "action": "get_data"}, permissions)
        self.assertIn({"user": "user1", "action": "update_data"}, permissions)
    
    def test_add_role(self):
        """
        اختبار إضافة دور
        """
        # إضافة دور
        role_permissions = [
            {"action": "get_data", "resource": "resource1"},
            {"action": "update_data", "resource": "resource1"}
        ]
        
        result = self.security_system.add_role("admin", role_permissions)
        
        # التحقق من نجاح الإضافة
        self.assertTrue(result)
        
        # التحقق من وجود الدور
        role = self.security_system.get_role("admin")
        self.assertIsNotNone(role)
        self.assertEqual(len(role), 2)
        self.assertIn({"action": "get_data", "resource": "resource1"}, role)
        self.assertIn({"action": "update_data", "resource": "resource1"}, role)
    
    def test_assign_role_to_user(self):
        """
        اختبار تعيين دور للمستخدم
        """
        # إضافة دور
        role_permissions = [
            {"action": "get_data", "resource": "resource1"},
            {"action": "update_data", "resource": "resource1"}
        ]
        
        self.security_system.add_role("editor", role_permissions)
        
        # تعيين الدور للمستخدم
        result = self.security_system.assign_role_to_user("test_user", "editor")
        
        # التحقق من نجاح التعيين
        self.assertTrue(result)
        
        # التحقق من وجود صلاحيات الدور للمستخدم
        has_permission = self.security_system.check_permission("test_user", "get_data", "resource1")
        self.assertTrue(has_permission)
        
        has_permission = self.security_system.check_permission("test_user", "update_data", "resource1")
        self.assertTrue(has_permission)
    
    def test_remove_role_from_user(self):
        """
        اختبار إزالة دور من المستخدم
        """
        # إضافة دور
        role_permissions = [
            {"action": "get_data", "resource": "resource1"},
            {"action": "update_data", "resource": "resource1"}
        ]
        
        self.security_system.add_role("viewer", role_permissions)
        
        # تعيين الدور للمستخدم
        self.security_system.assign_role_to_user("test_user", "viewer")
        
        # التحقق من وجود صلاحيات الدور للمستخدم
        has_permission = self.security_system.check_permission("test_user", "get_data", "resource1")
        self.assertTrue(has_permission)
        
        # إزالة الدور من المستخدم
        result = self.security_system.remove_role_from_user("test_user", "viewer")
        
        # التحقق من نجاح الإزالة
        self.assertTrue(result)
        
        # التحقق من عدم وجود صلاحيات الدور للمستخدم
        has_permission = self.security_system.check_permission("test_user", "get_data", "resource1")
        self.assertFalse(has_permission)

if __name__ == "__main__":
    unittest.main()
