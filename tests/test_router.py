import unittest
from attorney_general.controller.router import Router
from unittest.mock import MagicMock, patch

class TestRouter(unittest.TestCase):
    """
    اختبارات وحدة لنظام التوجيه
    """
    
    def setUp(self):
        """
        إعداد بيئة الاختبار
        """
        self.agent_registry = MagicMock()
        self.event_system = MagicMock()
        self.state_manager = MagicMock()
        
        self.router = Router(
            agent_registry=self.agent_registry,
            event_system=self.event_system,
            state_manager=self.state_manager
        )
    
    def test_route_request(self):
        """
        اختبار توجيه الطلب
        """
        # إعداد وكيل وهمي
        mock_agent = {
            "endpoint": "http://localhost:8000/test_agent",
            "capabilities": ["test_capability"]
        }
        self.agent_registry.get_agent.return_value = mock_agent
        self.agent_registry.agent_exists.return_value = True
        
        # إعداد استجابة وهمية
        mock_response = {"status": "success", "data": "test_data"}
        
        # استبدال دالة الاتصال بالوكيل
        with patch.object(self.router, '_call_agent', return_value=mock_response) as mock_call:
            # توجيه الطلب
            request = {
                "action": "test_action",
                "agent_id": "test_agent",
                "data": {"param": "value"}
            }
            
            response = self.router.route_request(request)
            
            # التحقق من استدعاء الوكيل
            mock_call.assert_called_once_with(
                "test_agent",
                "http://localhost:8000/test_agent",
                request
            )
            
            # التحقق من صحة الاستجابة
            self.assertEqual(response, mock_response)
    
    def test_route_request_to_capability(self):
        """
        اختبار توجيه الطلب حسب القدرة
        """
        # إعداد وكلاء وهميين
        mock_agents = {
            "agent1": {
                "endpoint": "http://localhost:8000/agent1",
                "capabilities": ["capability1", "capability2"]
            },
            "agent2": {
                "endpoint": "http://localhost:8000/agent2",
                "capabilities": ["capability2", "capability3"]
            }
        }
        
        # إعداد استجابة وهمية
        mock_response = {"status": "success", "data": "test_data"}
        
        # استبدال دوال وهمية
        self.agent_registry.get_agents_by_capability.return_value = mock_agents
        
        with patch.object(self.router, '_call_agent', return_value=mock_response) as mock_call:
            # توجيه الطلب
            request = {
                "action": "test_action",
                "capability": "capability2",
                "data": {"param": "value"}
            }
            
            response = self.router.route_request_to_capability(request)
            
            # التحقق من استدعاء الوكيل
            mock_call.assert_called_once()
            
            # التحقق من صحة الاستجابة
            self.assertEqual(response, mock_response)
    
    def test_route_request_to_all_agents(self):
        """
        اختبار توجيه الطلب لجميع الوكلاء
        """
        # إعداد وكلاء وهميين
        mock_agents = {
            "agent1": {
                "endpoint": "http://localhost:8000/agent1",
                "capabilities": ["capability1"]
            },
            "agent2": {
                "endpoint": "http://localhost:8000/agent2",
                "capabilities": ["capability2"]
            }
        }
        
        # إعداد استجابات وهمية
        mock_responses = {
            "agent1": {"status": "success", "data": "data1"},
            "agent2": {"status": "success", "data": "data2"}
        }
        
        # استبدال دوال وهمية
        self.agent_registry.get_all_agents.return_value = mock_agents
        
        def mock_call_agent(agent_id, endpoint, request):
            return mock_responses[agent_id]
        
        with patch.object(self.router, '_call_agent', side_effect=mock_call_agent) as mock_call:
            # توجيه الطلب
            request = {
                "action": "test_action",
                "data": {"param": "value"}
            }
            
            responses = self.router.route_request_to_all_agents(request)
            
            # التحقق من استدعاء الوكلاء
            self.assertEqual(mock_call.call_count, 2)
            
            # التحقق من صحة الاستجابات
            self.assertEqual(len(responses), 2)
            self.assertEqual(responses["agent1"], mock_responses["agent1"])
            self.assertEqual(responses["agent2"], mock_responses["agent2"])
    
    def test_route_request_agent_not_found(self):
        """
        اختبار توجيه الطلب لوكيل غير موجود
        """
        # إعداد وكيل وهمي غير موجود
        self.agent_registry.agent_exists.return_value = False
        
        # توجيه الطلب
        request = {
            "action": "test_action",
            "agent_id": "non_existent_agent",
            "data": {"param": "value"}
        }
        
        response = self.router.route_request(request)
        
        # التحقق من صحة الاستجابة
        self.assertEqual(response["status"], "error")
        self.assertIn("agent_not_found", response["error"])
    
    def test_route_request_invalid_request(self):
        """
        اختبار توجيه طلب غير صحيح
        """
        # توجيه طلب بدون حقل action
        request = {
            "agent_id": "test_agent",
            "data": {"param": "value"}
        }
        
        response = self.router.route_request(request)
        
        # التحقق من صحة الاستجابة
        self.assertEqual(response["status"], "error")
        self.assertIn("invalid_request", response["error"])
    
    def test_route_request_to_capability_no_agents(self):
        """
        اختبار توجيه الطلب حسب القدرة بدون وكلاء
        """
        # إعداد وكلاء وهميين فارغين
        self.agent_registry.get_agents_by_capability.return_value = {}
        
        # توجيه الطلب
        request = {
            "action": "test_action",
            "capability": "non_existent_capability",
            "data": {"param": "value"}
        }
        
        response = self.router.route_request_to_capability(request)
        
        # التحقق من صحة الاستجابة
        self.assertEqual(response["status"], "error")
        self.assertIn("no_agents_with_capability", response["error"])
    
    @patch('requests.post')
    def test_call_agent_success(self, mock_post):
        """
        اختبار استدعاء الوكيل بنجاح
        """
        # إعداد استجابة وهمية
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "data": "test_data"}
        mock_post.return_value = mock_response
        
        # استدعاء الوكيل
        request = {
            "action": "test_action",
            "data": {"param": "value"}
        }
        
        response = self.router._call_agent("test_agent", "http://localhost:8000/test_agent", request)
        
        # التحقق من صحة الاستجابة
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["data"], "test_data")
    
    @patch('requests.post')
    def test_call_agent_failure(self, mock_post):
        """
        اختبار فشل استدعاء الوكيل
        """
        # إعداد استثناء وهمي
        mock_post.side_effect = Exception("Connection error")
        
        # استدعاء الوكيل
        request = {
            "action": "test_action",
            "data": {"param": "value"}
        }
        
        response = self.router._call_agent("test_agent", "http://localhost:8000/test_agent", request)
        
        # التحقق من صحة الاستجابة
        self.assertEqual(response["status"], "error")
        self.assertIn("agent_communication_error", response["error"])

if __name__ == "__main__":
    unittest.main()
