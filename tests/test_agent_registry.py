import unittest
from attorney_general.controller.agent_registry import AgentRegistry

class TestAgentRegistry(unittest.TestCase):
    """
    اختبارات وحدة لنظام تسجيل الوكلاء
    """
    
    def setUp(self):
        """
        إعداد بيئة الاختبار
        """
        self.agent_registry = AgentRegistry()
    
    def test_register_agent(self):
        """
        اختبار تسجيل وكيل
        """
        # تسجيل وكيل
        agent_id = "test_agent"
        agent_info = {
            "name": "وكيل اختبار",
            "type": "test",
            "capabilities": ["capability1", "capability2"],
            "endpoint": "http://localhost:8000/test_agent"
        }
        
        result = self.agent_registry.register_agent(agent_id, agent_info)
        
        # التحقق من نجاح التسجيل
        self.assertTrue(result)
        
        # التحقق من وجود الوكيل
        agent = self.agent_registry.get_agent(agent_id)
        self.assertIsNotNone(agent)
        self.assertEqual(agent["name"], "وكيل اختبار")
        self.assertEqual(agent["type"], "test")
        self.assertListEqual(agent["capabilities"], ["capability1", "capability2"])
        self.assertEqual(agent["endpoint"], "http://localhost:8000/test_agent")
    
    def test_unregister_agent(self):
        """
        اختبار إلغاء تسجيل وكيل
        """
        # تسجيل وكيل
        agent_id = "test_agent"
        agent_info = {
            "name": "وكيل اختبار",
            "type": "test",
            "capabilities": ["capability1", "capability2"],
            "endpoint": "http://localhost:8000/test_agent"
        }
        
        self.agent_registry.register_agent(agent_id, agent_info)
        
        # إلغاء تسجيل الوكيل
        result = self.agent_registry.unregister_agent(agent_id)
        
        # التحقق من نجاح إلغاء التسجيل
        self.assertTrue(result)
        
        # التحقق من عدم وجود الوكيل
        agent = self.agent_registry.get_agent(agent_id)
        self.assertIsNone(agent)
    
    def test_get_agent(self):
        """
        اختبار الحصول على وكيل
        """
        # تسجيل وكيل
        agent_id = "test_agent"
        agent_info = {
            "name": "وكيل اختبار",
            "type": "test",
            "capabilities": ["capability1", "capability2"],
            "endpoint": "http://localhost:8000/test_agent"
        }
        
        self.agent_registry.register_agent(agent_id, agent_info)
        
        # الحصول على الوكيل
        agent = self.agent_registry.get_agent(agent_id)
        
        # التحقق من صحة الوكيل
        self.assertIsNotNone(agent)
        self.assertEqual(agent["name"], "وكيل اختبار")
        self.assertEqual(agent["type"], "test")
        self.assertListEqual(agent["capabilities"], ["capability1", "capability2"])
        self.assertEqual(agent["endpoint"], "http://localhost:8000/test_agent")
    
    def test_get_all_agents(self):
        """
        اختبار الحصول على جميع الوكلاء
        """
        # تسجيل وكلاء
        self.agent_registry.register_agent("agent1", {
            "name": "وكيل 1",
            "type": "test",
            "capabilities": ["capability1"],
            "endpoint": "http://localhost:8000/agent1"
        })
        self.agent_registry.register_agent("agent2", {
            "name": "وكيل 2",
            "type": "test",
            "capabilities": ["capability2"],
            "endpoint": "http://localhost:8000/agent2"
        })
        
        # الحصول على جميع الوكلاء
        agents = self.agent_registry.get_all_agents()
        
        # التحقق من صحة الوكلاء
        self.assertIsNotNone(agents)
        self.assertEqual(len(agents), 2)
        self.assertIn("agent1", agents)
        self.assertIn("agent2", agents)
    
    def test_get_agents_by_type(self):
        """
        اختبار الحصول على الوكلاء حسب النوع
        """
        # تسجيل وكلاء
        self.agent_registry.register_agent("agent1", {
            "name": "وكيل 1",
            "type": "type1",
            "capabilities": ["capability1"],
            "endpoint": "http://localhost:8000/agent1"
        })
        self.agent_registry.register_agent("agent2", {
            "name": "وكيل 2",
            "type": "type2",
            "capabilities": ["capability2"],
            "endpoint": "http://localhost:8000/agent2"
        })
        self.agent_registry.register_agent("agent3", {
            "name": "وكيل 3",
            "type": "type1",
            "capabilities": ["capability3"],
            "endpoint": "http://localhost:8000/agent3"
        })
        
        # الحصول على الوكلاء حسب النوع
        agents = self.agent_registry.get_agents_by_type("type1")
        
        # التحقق من صحة الوكلاء
        self.assertIsNotNone(agents)
        self.assertEqual(len(agents), 2)
        self.assertIn("agent1", agents)
        self.assertIn("agent3", agents)
    
    def test_get_agents_by_capability(self):
        """
        اختبار الحصول على الوكلاء حسب القدرة
        """
        # تسجيل وكلاء
        self.agent_registry.register_agent("agent1", {
            "name": "وكيل 1",
            "type": "test",
            "capabilities": ["capability1", "capability3"],
            "endpoint": "http://localhost:8000/agent1"
        })
        self.agent_registry.register_agent("agent2", {
            "name": "وكيل 2",
            "type": "test",
            "capabilities": ["capability2"],
            "endpoint": "http://localhost:8000/agent2"
        })
        self.agent_registry.register_agent("agent3", {
            "name": "وكيل 3",
            "type": "test",
            "capabilities": ["capability1", "capability2"],
            "endpoint": "http://localhost:8000/agent3"
        })
        
        # الحصول على الوكلاء حسب القدرة
        agents = self.agent_registry.get_agents_by_capability("capability1")
        
        # التحقق من صحة الوكلاء
        self.assertIsNotNone(agents)
        self.assertEqual(len(agents), 2)
        self.assertIn("agent1", agents)
        self.assertIn("agent3", agents)
    
    def test_update_agent(self):
        """
        اختبار تحديث وكيل
        """
        # تسجيل وكيل
        agent_id = "test_agent"
        agent_info = {
            "name": "وكيل اختبار",
            "type": "test",
            "capabilities": ["capability1", "capability2"],
            "endpoint": "http://localhost:8000/test_agent"
        }
        
        self.agent_registry.register_agent(agent_id, agent_info)
        
        # تحديث الوكيل
        updated_info = {
            "name": "وكيل اختبار محدث",
            "type": "test_updated",
            "capabilities": ["capability1", "capability2", "capability3"],
            "endpoint": "http://localhost:8000/test_agent_updated"
        }
        
        result = self.agent_registry.update_agent(agent_id, updated_info)
        
        # التحقق من نجاح التحديث
        self.assertTrue(result)
        
        # التحقق من صحة الوكيل المحدث
        agent = self.agent_registry.get_agent(agent_id)
        self.assertIsNotNone(agent)
        self.assertEqual(agent["name"], "وكيل اختبار محدث")
        self.assertEqual(agent["type"], "test_updated")
        self.assertListEqual(agent["capabilities"], ["capability1", "capability2", "capability3"])
        self.assertEqual(agent["endpoint"], "http://localhost:8000/test_agent_updated")
    
    def test_agent_exists(self):
        """
        اختبار التحقق من وجود وكيل
        """
        # تسجيل وكيل
        agent_id = "test_agent"
        agent_info = {
            "name": "وكيل اختبار",
            "type": "test",
            "capabilities": ["capability1", "capability2"],
            "endpoint": "http://localhost:8000/test_agent"
        }
        
        self.agent_registry.register_agent(agent_id, agent_info)
        
        # التحقق من وجود الوكيل
        exists = self.agent_registry.agent_exists(agent_id)
        
        # التحقق من صحة النتيجة
        self.assertTrue(exists)
        
        # التحقق من عدم وجود وكيل غير مسجل
        exists = self.agent_registry.agent_exists("non_existent_agent")
        
        # التحقق من صحة النتيجة
        self.assertFalse(exists)
    
    def test_clear_registry(self):
        """
        اختبار مسح سجل الوكلاء
        """
        # تسجيل وكلاء
        self.agent_registry.register_agent("agent1", {
            "name": "وكيل 1",
            "type": "test",
            "capabilities": ["capability1"],
            "endpoint": "http://localhost:8000/agent1"
        })
        self.agent_registry.register_agent("agent2", {
            "name": "وكيل 2",
            "type": "test",
            "capabilities": ["capability2"],
            "endpoint": "http://localhost:8000/agent2"
        })
        
        # مسح السجل
        self.agent_registry.clear_registry()
        
        # التحقق من مسح السجل
        agents = self.agent_registry.get_all_agents()
        self.assertEqual(len(agents), 0)

if __name__ == "__main__":
    unittest.main()
