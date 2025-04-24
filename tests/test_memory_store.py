import unittest
from attorney_general.memory.memory_store import MemoryStore

class TestMemoryStore(unittest.TestCase):
    """
    اختبارات وحدة لنظام الذاكرة
    """
    
    def setUp(self):
        """
        إعداد بيئة الاختبار
        """
        self.memory_store = MemoryStore()
    
    def test_add_to_short_term_memory(self):
        """
        اختبار إضافة عنصر إلى الذاكرة قصيرة المدى
        """
        # إضافة عنصر إلى الذاكرة
        memory_id = self.memory_store.add_to_short_term_memory({
            "type": "message",
            "content": "رسالة اختبار"
        })
        
        # التحقق من إضافة العنصر
        self.assertIsNotNone(memory_id)
        
        # استرجاع العنصر
        memory_item = self.memory_store.get_memory_item(memory_id)
        
        # التحقق من صحة العنصر
        self.assertIsNotNone(memory_item)
        self.assertEqual(memory_item["type"], "message")
        self.assertEqual(memory_item["content"], "رسالة اختبار")
    
    def test_add_to_long_term_memory(self):
        """
        اختبار إضافة عنصر إلى الذاكرة طويلة المدى
        """
        # إضافة عنصر إلى الذاكرة
        memory_id = self.memory_store.add_to_long_term_memory({
            "type": "fact",
            "content": "حقيقة اختبار"
        })
        
        # التحقق من إضافة العنصر
        self.assertIsNotNone(memory_id)
        
        # استرجاع العنصر
        memory_item = self.memory_store.get_memory_item(memory_id)
        
        # التحقق من صحة العنصر
        self.assertIsNotNone(memory_item)
        self.assertEqual(memory_item["type"], "fact")
        self.assertEqual(memory_item["content"], "حقيقة اختبار")
    
    def test_get_short_term_memory(self):
        """
        اختبار استرجاع الذاكرة قصيرة المدى
        """
        # إضافة عناصر إلى الذاكرة
        self.memory_store.add_to_short_term_memory({
            "type": "message",
            "content": "رسالة 1"
        })
        self.memory_store.add_to_short_term_memory({
            "type": "message",
            "content": "رسالة 2"
        })
        
        # استرجاع الذاكرة
        memory = self.memory_store.get_short_term_memory()
        
        # التحقق من صحة الذاكرة
        self.assertIsNotNone(memory)
        self.assertGreaterEqual(len(memory), 2)
    
    def test_get_long_term_memory(self):
        """
        اختبار استرجاع الذاكرة طويلة المدى
        """
        # إضافة عناصر إلى الذاكرة
        self.memory_store.add_to_long_term_memory({
            "type": "fact",
            "content": "حقيقة 1"
        })
        self.memory_store.add_to_long_term_memory({
            "type": "fact",
            "content": "حقيقة 2"
        })
        
        # استرجاع الذاكرة
        memory = self.memory_store.get_long_term_memory()
        
        # التحقق من صحة الذاكرة
        self.assertIsNotNone(memory)
        self.assertGreaterEqual(len(memory), 2)
    
    def test_search_memory(self):
        """
        اختبار البحث في الذاكرة
        """
        # إضافة عناصر إلى الذاكرة
        self.memory_store.add_to_short_term_memory({
            "type": "message",
            "content": "رسالة اختبار"
        })
        self.memory_store.add_to_long_term_memory({
            "type": "fact",
            "content": "حقيقة اختبار"
        })
        
        # البحث في الذاكرة
        results = self.memory_store.search_memory("اختبار")
        
        # التحقق من صحة النتائج
        self.assertIsNotNone(results)
        self.assertGreaterEqual(len(results), 2)
    
    def test_delete_memory_item(self):
        """
        اختبار حذف عنصر من الذاكرة
        """
        # إضافة عنصر إلى الذاكرة
        memory_id = self.memory_store.add_to_short_term_memory({
            "type": "message",
            "content": "رسالة للحذف"
        })
        
        # التحقق من إضافة العنصر
        self.assertIsNotNone(memory_id)
        
        # حذف العنصر
        result = self.memory_store.delete_memory_item(memory_id)
        
        # التحقق من نجاح الحذف
        self.assertTrue(result)
        
        # محاولة استرجاع العنصر
        memory_item = self.memory_store.get_memory_item(memory_id)
        
        # التحقق من عدم وجود العنصر
        self.assertIsNone(memory_item)
    
    def test_clear_short_term_memory(self):
        """
        اختبار مسح الذاكرة قصيرة المدى
        """
        # إضافة عناصر إلى الذاكرة
        self.memory_store.add_to_short_term_memory({
            "type": "message",
            "content": "رسالة 1"
        })
        self.memory_store.add_to_short_term_memory({
            "type": "message",
            "content": "رسالة 2"
        })
        
        # مسح الذاكرة
        self.memory_store.clear_short_term_memory()
        
        # استرجاع الذاكرة
        memory = self.memory_store.get_short_term_memory()
        
        # التحقق من صحة الذاكرة
        self.assertEqual(len(memory), 0)
    
    def test_add_to_condensed_memory(self):
        """
        اختبار إضافة عنصر إلى الذاكرة المكثفة
        """
        # إضافة عنصر إلى الذاكرة
        memory_id = self.memory_store.add_to_condensed_memory({
            "type": "summary",
            "content": "ملخص اختبار"
        })
        
        # التحقق من إضافة العنصر
        self.assertIsNotNone(memory_id)
        
        # استرجاع العنصر
        memory_item = self.memory_store.get_memory_item(memory_id)
        
        # التحقق من صحة العنصر
        self.assertIsNotNone(memory_item)
        self.assertEqual(memory_item["type"], "summary")
        self.assertEqual(memory_item["content"], "ملخص اختبار")
    
    def test_get_condensed_memory(self):
        """
        اختبار استرجاع الذاكرة المكثفة
        """
        # إضافة عناصر إلى الذاكرة
        self.memory_store.add_to_condensed_memory({
            "type": "summary",
            "content": "ملخص 1"
        })
        self.memory_store.add_to_condensed_memory({
            "type": "summary",
            "content": "ملخص 2"
        })
        
        # استرجاع الذاكرة
        memory = self.memory_store.get_condensed_memory()
        
        # التحقق من صحة الذاكرة
        self.assertIsNotNone(memory)
        self.assertGreaterEqual(len(memory), 2)

if __name__ == "__main__":
    unittest.main()
