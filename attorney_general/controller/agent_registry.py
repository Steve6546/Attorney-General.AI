"""
نظام تسجيل الوكلاء (Agent Registry) لنظام Attorney-General.AI
يدير تسجيل وإلغاء تسجيل الوكلاء وتتبع حالتهم
"""

import logging
import time
from typing import Dict, List, Optional, Any

logger = logging.getLogger("agent_registry")

class AgentRegistry:
    """
    نظام تسجيل الوكلاء
    يدير قائمة الوكلاء المتاحين وقدراتهم وحالتهم
    """
    
    def __init__(self):
        """تهيئة سجل الوكلاء"""
        self._agents = {}  # قاموس لتخزين معلومات الوكلاء
        self._agent_activity = {}  # قاموس لتتبع نشاط الوكلاء
        self._capability_index = {}  # فهرس للبحث عن الوكلاء حسب القدرات
        logger.info("تم تهيئة سجل الوكلاء")
    
    def register_agent(self, agent_id: str, name: str, url: str, 
                      capabilities: List[str] = None, supports_streaming: bool = False) -> bool:
        """
        تسجيل وكيل جديد في النظام
        
        Args:
            agent_id: معرف الوكيل الفريد
            name: اسم الوكيل
            url: عنوان URL للوكيل
            capabilities: قائمة قدرات الوكيل
            supports_streaming: ما إذا كان الوكيل يدعم الاستجابة المتدفقة
            
        Returns:
            نجاح العملية
        """
        if capabilities is None:
            capabilities = []
            
        # التحقق من عدم وجود الوكيل مسبقاً
        if agent_id in self._agents:
            logger.warning(f"الوكيل {agent_id} مسجل مسبقاً")
            return False
        
        # تسجيل الوكيل
        self._agents[agent_id] = {
            "id": agent_id,
            "name": name,
            "url": url,
            "capabilities": capabilities,
            "supports_streaming": supports_streaming,
            "status": "active",
            "registered_at": self._get_timestamp()
        }
        
        # تحديث فهرس القدرات
        for capability in capabilities:
            if capability not in self._capability_index:
                self._capability_index[capability] = []
            self._capability_index[capability].append(agent_id)
        
        # تسجيل وقت النشاط الأخير
        self._agent_activity[agent_id] = time.time()
        
        logger.info(f"تم تسجيل الوكيل: {agent_id} ({name})")
        return True
    
    def unregister_agent(self, agent_id: str) -> bool:
        """
        إلغاء تسجيل وكيل من النظام
        
        Args:
            agent_id: معرف الوكيل
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود الوكيل
        if agent_id not in self._agents:
            logger.warning(f"الوكيل {agent_id} غير مسجل")
            return False
        
        # إزالة الوكيل من فهرس القدرات
        for capability in self._agents[agent_id]["capabilities"]:
            if capability in self._capability_index and agent_id in self._capability_index[capability]:
                self._capability_index[capability].remove(agent_id)
                
                # إزالة القدرة من الفهرس إذا لم تعد مستخدمة
                if not self._capability_index[capability]:
                    del self._capability_index[capability]
        
        # إزالة الوكيل من سجل النشاط
        if agent_id in self._agent_activity:
            del self._agent_activity[agent_id]
        
        # إزالة الوكيل من السجل
        agent_name = self._agents[agent_id]["name"]
        del self._agents[agent_id]
        
        logger.info(f"تم إلغاء تسجيل الوكيل: {agent_id} ({agent_name})")
        return True
    
    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """
        الحصول على معلومات وكيل محدد
        
        Args:
            agent_id: معرف الوكيل
            
        Returns:
            معلومات الوكيل أو None إذا لم يكن موجوداً
        """
        return self._agents.get(agent_id)
    
    def get_all_agents(self) -> Dict:
        """
        الحصول على قائمة جميع الوكلاء المسجلين
        
        Returns:
            قاموس الوكلاء المسجلين
        """
        return self._agents
    
    def update_agent_status(self, agent_id: str, status: str) -> bool:
        """
        تحديث حالة وكيل
        
        Args:
            agent_id: معرف الوكيل
            status: الحالة الجديدة ('active', 'inactive', 'error')
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود الوكيل
        if agent_id not in self._agents:
            logger.warning(f"الوكيل {agent_id} غير مسجل")
            return False
        
        # التحقق من صحة الحالة
        valid_statuses = ['active', 'inactive', 'error']
        if status not in valid_statuses:
            logger.warning(f"حالة غير صالحة: {status}")
            return False
        
        # تحديث الحالة
        self._agents[agent_id]["status"] = status
        logger.info(f"تم تحديث حالة الوكيل {agent_id} إلى: {status}")
        return True
    
    def update_agent_activity(self, agent_id: str) -> bool:
        """
        تحديث وقت النشاط الأخير للوكيل
        
        Args:
            agent_id: معرف الوكيل
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود الوكيل
        if agent_id not in self._agents:
            logger.warning(f"الوكيل {agent_id} غير مسجل")
            return False
        
        # تحديث وقت النشاط
        self._agent_activity[agent_id] = time.time()
        return True
    
    def find_agents_by_capability(self, capability: str) -> List[str]:
        """
        البحث عن الوكلاء بناءً على القدرات
        
        Args:
            capability: القدرة المطلوبة
            
        Returns:
            قائمة معرفات الوكلاء التي تملك القدرة المطلوبة
        """
        return self._capability_index.get(capability, [])
    
    def find_best_agent_for_task(self, required_capabilities: List[str]) -> Optional[str]:
        """
        البحث عن أفضل وكيل لمهمة معينة بناءً على القدرات المطلوبة
        
        Args:
            required_capabilities: قائمة القدرات المطلوبة
            
        Returns:
            معرف أفضل وكيل أو None إذا لم يتم العثور على وكيل مناسب
        """
        if not required_capabilities:
            return None
        
        # حساب درجة التطابق لكل وكيل
        agent_scores = {}
        
        for capability in required_capabilities:
            for agent_id in self.find_agents_by_capability(capability):
                if agent_id not in agent_scores:
                    agent_scores[agent_id] = 0
                agent_scores[agent_id] += 1
        
        # اختيار الوكيل ذو أعلى درجة
        if not agent_scores:
            return None
        
        best_agent = max(agent_scores.items(), key=lambda x: x[1])[0]
        return best_agent
    
    def get_inactive_agents(self, inactive_threshold_seconds: int = 3600) -> List[str]:
        """
        الحصول على قائمة الوكلاء غير النشطين
        
        Args:
            inactive_threshold_seconds: عتبة عدم النشاط بالثواني
            
        Returns:
            قائمة معرفات الوكلاء غير النشطين
        """
        current_time = time.time()
        inactive_agents = []
        
        for agent_id, last_activity in self._agent_activity.items():
            if current_time - last_activity > inactive_threshold_seconds:
                inactive_agents.append(agent_id)
        
        return inactive_agents
    
    def _get_timestamp(self) -> str:
        """الحصول على الطابع الزمني الحالي"""
        from datetime import datetime
        return datetime.now().isoformat()
