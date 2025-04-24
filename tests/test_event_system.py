import unittest
from attorney_general.events.event_system import EventSystem
import asyncio

class TestEventSystem(unittest.TestCase):
    """
    اختبارات وحدة لنظام الأحداث
    """
    
    def setUp(self):
        """
        إعداد بيئة الاختبار
        """
        self.event_system = EventSystem()
    
    def test_publish_event(self):
        """
        اختبار نشر حدث
        """
        # إنشاء حلقة أحداث غير متزامنة
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # نشر حدث
        event_id = loop.run_until_complete(self.event_system.publish(
            "test_event",
            {"message": "رسالة اختبار"},
            "test_source"
        ))
        
        # التحقق من نجاح النشر
        self.assertIsNotNone(event_id)
        
        # إغلاق حلقة الأحداث
        loop.close()
    
    def test_subscribe_and_publish(self):
        """
        اختبار الاشتراك ونشر الأحداث
        """
        # إنشاء حلقة أحداث غير متزامنة
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # إنشاء متغير لتتبع استدعاء المشترك
        callback_called = False
        callback_event = None
        
        # إنشاء دالة استدعاء غير متزامنة
        async def callback(event):
            nonlocal callback_called, callback_event
            callback_called = True
            callback_event = event
        
        # الاشتراك في الحدث
        subscription_id = self.event_system.subscribe("test_event", callback)
        
        # التحقق من نجاح الاشتراك
        self.assertIsNotNone(subscription_id)
        
        # نشر حدث
        event_id = loop.run_until_complete(self.event_system.publish(
            "test_event",
            {"message": "رسالة اختبار"},
            "test_source"
        ))
        
        # التحقق من نجاح النشر
        self.assertIsNotNone(event_id)
        
        # التحقق من استدعاء المشترك
        self.assertTrue(callback_called)
        self.assertIsNotNone(callback_event)
        self.assertEqual(callback_event["id"], event_id)
        self.assertEqual(callback_event["type"], "test_event")
        self.assertEqual(callback_event["data"]["message"], "رسالة اختبار")
        self.assertEqual(callback_event["source"], "test_source")
        
        # إغلاق حلقة الأحداث
        loop.close()
    
    def test_unsubscribe(self):
        """
        اختبار إلغاء الاشتراك
        """
        # إنشاء دالة استدعاء غير متزامنة
        async def callback(event):
            pass
        
        # الاشتراك في الحدث
        subscription_id = self.event_system.subscribe("test_event", callback)
        
        # التحقق من نجاح الاشتراك
        self.assertIsNotNone(subscription_id)
        
        # إلغاء الاشتراك
        result = self.event_system.unsubscribe("test_event", subscription_id)
        
        # التحقق من نجاح إلغاء الاشتراك
        self.assertTrue(result)
    
    def test_get_event_history(self):
        """
        اختبار الحصول على تاريخ الأحداث
        """
        # إنشاء حلقة أحداث غير متزامنة
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # نشر أحداث
        loop.run_until_complete(self.event_system.publish(
            "test_event",
            {"message": "رسالة 1"},
            "test_source"
        ))
        loop.run_until_complete(self.event_system.publish(
            "test_event",
            {"message": "رسالة 2"},
            "test_source"
        ))
        
        # الحصول على تاريخ الأحداث
        history = self.event_system.get_event_history("test_event")
        
        # التحقق من صحة التاريخ
        self.assertIsNotNone(history)
        self.assertIn("test_event", history)
        self.assertEqual(len(history["test_event"]), 2)
        
        # إغلاق حلقة الأحداث
        loop.close()
    
    def test_get_event_types(self):
        """
        اختبار الحصول على أنواع الأحداث
        """
        # إنشاء حلقة أحداث غير متزامنة
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # نشر أحداث من أنواع مختلفة
        loop.run_until_complete(self.event_system.publish(
            "test_event_1",
            {"message": "رسالة 1"},
            "test_source"
        ))
        loop.run_until_complete(self.event_system.publish(
            "test_event_2",
            {"message": "رسالة 2"},
            "test_source"
        ))
        
        # الحصول على أنواع الأحداث
        event_types = self.event_system.get_event_types()
        
        # التحقق من صحة الأنواع
        self.assertIsNotNone(event_types)
        self.assertIn("test_event_1", event_types)
        self.assertIn("test_event_2", event_types)
        
        # إغلاق حلقة الأحداث
        loop.close()
    
    def test_get_subscriber_count(self):
        """
        اختبار الحصول على عدد المشتركين
        """
        # إنشاء دوال استدعاء غير متزامنة
        async def callback1(event):
            pass
        
        async def callback2(event):
            pass
        
        # الاشتراك في الأحداث
        self.event_system.subscribe("test_event", callback1)
        self.event_system.subscribe("test_event", callback2)
        
        # الحصول على عدد المشتركين
        counts = self.event_system.get_subscriber_count("test_event")
        
        # التحقق من صحة العدد
        self.assertIsNotNone(counts)
        self.assertIn("test_event", counts)
        self.assertEqual(counts["test_event"], 2)
    
    def test_clear_event_history(self):
        """
        اختبار مسح تاريخ الأحداث
        """
        # إنشاء حلقة أحداث غير متزامنة
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # نشر أحداث
        loop.run_until_complete(self.event_system.publish(
            "test_event",
            {"message": "رسالة 1"},
            "test_source"
        ))
        
        # مسح تاريخ الأحداث
        result = self.event_system.clear_event_history("test_event")
        
        # التحقق من نجاح المسح
        self.assertTrue(result)
        
        # الحصول على تاريخ الأحداث
        history = self.event_system.get_event_history("test_event")
        
        # التحقق من صحة التاريخ
        self.assertIsNotNone(history)
        self.assertIn("test_event", history)
        self.assertEqual(len(history["test_event"]), 0)
        
        # إغلاق حلقة الأحداث
        loop.close()
    
    def test_export_import_event_history(self):
        """
        اختبار تصدير واستيراد تاريخ الأحداث
        """
        # إنشاء حلقة أحداث غير متزامنة
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # نشر أحداث
        loop.run_until_complete(self.event_system.publish(
            "test_event",
            {"message": "رسالة 1"},
            "test_source"
        ))
        
        # تصدير تاريخ الأحداث
        export_data = self.event_system.export_event_history()
        
        # مسح تاريخ الأحداث
        self.event_system.clear_event_history()
        
        # التحقق من المسح
        history = self.event_system.get_event_history("test_event")
        self.assertIsNotNone(history)
        self.assertEqual(len(history.get("test_event", [])), 0)
        
        # استيراد تاريخ الأحداث
        result = self.event_system.import_event_history(export_data)
        
        # التحقق من نجاح الاستيراد
        self.assertTrue(result)
        
        # الحصول على تاريخ الأحداث
        history = self.event_system.get_event_history("test_event")
        
        # التحقق من صحة التاريخ
        self.assertIsNotNone(history)
        self.assertIn("test_event", history)
        self.assertEqual(len(history["test_event"]), 1)
        
        # إغلاق حلقة الأحداث
        loop.close()

if __name__ == "__main__":
    unittest.main()
