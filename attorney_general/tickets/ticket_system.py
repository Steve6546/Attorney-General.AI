"""
نظام التذاكر (Ticket System) لنظام Attorney-General.AI
يدير تذاكر المهام والطلبات بين مكونات النظام
"""

import logging
import json
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import uuid

logger = logging.getLogger("ticket_system")

class TicketSystem:
    """
    نظام التذاكر
    يدير تذاكر المهام والطلبات بين مكونات النظام
    """
    
    def __init__(self, event_system=None):
        """
        تهيئة نظام التذاكر
        
        Args:
            event_system: نظام الأحداث (اختياري)
        """
        # إعداد قاموس التذاكر
        self.tickets = {}
        
        # إعداد نظام الأحداث
        self.event_system = event_system
        
        logger.info("تم تهيئة نظام التذاكر")
    
    def create_ticket(self, ticket_type: str, data: Dict, priority: str = "normal", assignee: str = None) -> str:
        """
        إنشاء تذكرة جديدة
        
        Args:
            ticket_type: نوع التذكرة
            data: بيانات التذكرة
            priority: أولوية التذكرة (منخفضة، عادية، عالية، حرجة)
            assignee: المسؤول عن التذكرة
            
        Returns:
            معرف التذكرة
        """
        # إنشاء معرف للتذكرة
        ticket_id = str(uuid.uuid4())
        
        # التحقق من صحة الأولوية
        if priority not in ["low", "normal", "high", "critical"]:
            priority = "normal"
        
        # إنشاء التذكرة
        ticket = {
            "id": ticket_id,
            "type": ticket_type,
            "data": data,
            "priority": priority,
            "assignee": assignee,
            "status": "open",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "history": [
                {
                    "action": "create",
                    "timestamp": datetime.now().isoformat(),
                    "details": f"تم إنشاء التذكرة من النوع {ticket_type}"
                }
            ]
        }
        
        # إضافة التذكرة إلى القاموس
        self.tickets[ticket_id] = ticket
        
        # نشر حدث إنشاء التذكرة
        self._publish_event("ticket_created", {
            "ticket_id": ticket_id,
            "ticket_type": ticket_type,
            "priority": priority,
            "assignee": assignee
        })
        
        logger.info(f"تم إنشاء التذكرة: {ticket_id} من النوع {ticket_type}")
        return ticket_id
    
    def get_ticket(self, ticket_id: str) -> Optional[Dict]:
        """
        الحصول على تذكرة
        
        Args:
            ticket_id: معرف التذكرة
            
        Returns:
            التذكرة أو None إذا لم تكن موجودة
        """
        return self.tickets.get(ticket_id)
    
    def update_ticket(self, ticket_id: str, updates: Dict, action: str = "update") -> bool:
        """
        تحديث تذكرة
        
        Args:
            ticket_id: معرف التذكرة
            updates: التحديثات
            action: إجراء التحديث
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود التذكرة
        if ticket_id not in self.tickets:
            logger.warning(f"التذكرة {ticket_id} غير موجودة")
            return False
        
        # الحصول على التذكرة
        ticket = self.tickets[ticket_id]
        
        # تحديث البيانات
        for key, value in updates.items():
            if key in ["id", "created_at", "history"]:
                # تجاهل الحقول التي لا يمكن تحديثها
                continue
            
            if key == "data" and isinstance(value, dict) and isinstance(ticket["data"], dict):
                # دمج بيانات التذكرة
                ticket["data"].update(value)
            else:
                # تحديث الحقل
                ticket[key] = value
        
        # تحديث وقت التحديث
        ticket["updated_at"] = datetime.now().isoformat()
        
        # إضافة سجل إلى التاريخ
        ticket["history"].append({
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "details": f"تم تحديث التذكرة: {', '.join(updates.keys())}"
        })
        
        # نشر حدث تحديث التذكرة
        self._publish_event("ticket_updated", {
            "ticket_id": ticket_id,
            "updates": updates,
            "action": action
        })
        
        logger.info(f"تم تحديث التذكرة: {ticket_id}")
        return True
    
    def assign_ticket(self, ticket_id: str, assignee: str) -> bool:
        """
        تعيين مسؤول عن تذكرة
        
        Args:
            ticket_id: معرف التذكرة
            assignee: المسؤول عن التذكرة
            
        Returns:
            نجاح العملية
        """
        return self.update_ticket(
            ticket_id,
            {"assignee": assignee},
            "assign"
        )
    
    def change_ticket_status(self, ticket_id: str, status: str, comment: str = None) -> bool:
        """
        تغيير حالة تذكرة
        
        Args:
            ticket_id: معرف التذكرة
            status: الحالة الجديدة
            comment: تعليق (اختياري)
            
        Returns:
            نجاح العملية
        """
        # التحقق من صحة الحالة
        if status not in ["open", "in_progress", "pending", "resolved", "closed", "rejected"]:
            logger.warning(f"حالة التذكرة غير صالحة: {status}")
            return False
        
        # تحديث التذكرة
        updates = {"status": status}
        
        if comment:
            # إضافة تعليق إلى بيانات التذكرة
            updates["data"] = {"comment": comment}
        
        return self.update_ticket(
            ticket_id,
            updates,
            f"change_status_to_{status}"
        )
    
    def add_comment(self, ticket_id: str, comment: str, author: str = None) -> bool:
        """
        إضافة تعليق إلى تذكرة
        
        Args:
            ticket_id: معرف التذكرة
            comment: التعليق
            author: كاتب التعليق (اختياري)
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود التذكرة
        if ticket_id not in self.tickets:
            logger.warning(f"التذكرة {ticket_id} غير موجودة")
            return False
        
        # الحصول على التذكرة
        ticket = self.tickets[ticket_id]
        
        # إنشاء التعليق
        comment_data = {
            "text": comment,
            "author": author,
            "timestamp": datetime.now().isoformat()
        }
        
        # إضافة التعليق إلى بيانات التذكرة
        if "comments" not in ticket["data"]:
            ticket["data"]["comments"] = []
        
        ticket["data"]["comments"].append(comment_data)
        
        # تحديث وقت التحديث
        ticket["updated_at"] = datetime.now().isoformat()
        
        # إضافة سجل إلى التاريخ
        ticket["history"].append({
            "action": "add_comment",
            "timestamp": datetime.now().isoformat(),
            "details": f"تم إضافة تعليق بواسطة {author or 'مجهول'}"
        })
        
        # نشر حدث إضافة تعليق
        self._publish_event("ticket_comment_added", {
            "ticket_id": ticket_id,
            "comment": comment_data
        })
        
        logger.info(f"تم إضافة تعليق إلى التذكرة: {ticket_id}")
        return True
    
    def close_ticket(self, ticket_id: str, resolution: str = None) -> bool:
        """
        إغلاق تذكرة
        
        Args:
            ticket_id: معرف التذكرة
            resolution: الحل (اختياري)
            
        Returns:
            نجاح العملية
        """
        # تحديث التذكرة
        updates = {"status": "closed"}
        
        if resolution:
            # إضافة الحل إلى بيانات التذكرة
            updates["data"] = {"resolution": resolution}
        
        return self.update_ticket(
            ticket_id,
            updates,
            "close"
        )
    
    def reopen_ticket(self, ticket_id: str, reason: str = None) -> bool:
        """
        إعادة فتح تذكرة
        
        Args:
            ticket_id: معرف التذكرة
            reason: سبب إعادة الفتح (اختياري)
            
        Returns:
            نجاح العملية
        """
        # تحديث التذكرة
        updates = {"status": "open"}
        
        if reason:
            # إضافة سبب إعادة الفتح إلى بيانات التذكرة
            updates["data"] = {"reopen_reason": reason}
        
        return self.update_ticket(
            ticket_id,
            updates,
            "reopen"
        )
    
    def delete_ticket(self, ticket_id: str) -> bool:
        """
        حذف تذكرة
        
        Args:
            ticket_id: معرف التذكرة
            
        Returns:
            نجاح العملية
        """
        # التحقق من وجود التذكرة
        if ticket_id not in self.tickets:
            logger.warning(f"التذكرة {ticket_id} غير موجودة")
            return False
        
        # نشر حدث حذف التذكرة
        self._publish_event("ticket_deleted", {
            "ticket_id": ticket_id
        })
        
        # حذف التذكرة
        del self.tickets[ticket_id]
        
        logger.info(f"تم حذف التذكرة: {ticket_id}")
        return True
    
    def search_tickets(self, filters: Dict = None, sort_by: str = "created_at", sort_order: str = "desc", limit: int = None, offset: int = 0) -> List[Dict]:
        """
        البحث عن تذاكر
        
        Args:
            filters: مرشحات البحث (اختياري)
            sort_by: حقل الترتيب (اختياري)
            sort_order: ترتيب الفرز (اختياري)
            limit: الحد الأقصى لعدد النتائج (اختياري)
            offset: إزاحة النتائج (اختياري)
            
        Returns:
            قائمة التذاكر
        """
        if filters is None:
            filters = {}
        
        # تصفية التذاكر
        filtered_tickets = []
        
        for ticket in self.tickets.values():
            # التحقق من تطابق المرشحات
            match = True
            
            for key, value in filters.items():
                if key == "data":
                    # البحث في بيانات التذكرة
                    if isinstance(value, dict):
                        for data_key, data_value in value.items():
                            if data_key not in ticket["data"] or ticket["data"][data_key] != data_value:
                                match = False
                                break
                elif key not in ticket or ticket[key] != value:
                    match = False
                    break
            
            if match:
                filtered_tickets.append(ticket)
        
        # ترتيب التذاكر
        if sort_by in ["created_at", "updated_at", "priority"]:
            reverse = sort_order.lower() == "desc"
            
            filtered_tickets.sort(
                key=lambda t: t[sort_by],
                reverse=reverse
            )
        
        # تطبيق الإزاحة والحد
        if offset > 0:
            filtered_tickets = filtered_tickets[offset:]
        
        if limit is not None:
            filtered_tickets = filtered_tickets[:limit]
        
        return filtered_tickets
    
    def get_ticket_history(self, ticket_id: str) -> Optional[List[Dict]]:
        """
        الحصول على تاريخ تذكرة
        
        Args:
            ticket_id: معرف التذكرة
            
        Returns:
            تاريخ التذكرة أو None إذا لم تكن موجودة
        """
        # التحقق من وجود التذكرة
        if ticket_id not in self.tickets:
            logger.warning(f"التذكرة {ticket_id} غير موجودة")
            return None
        
        # الحصول على التذكرة
        ticket = self.tickets[ticket_id]
        
        return ticket["history"]
    
    def get_ticket_comments(self, ticket_id: str) -> Optional[List[Dict]]:
        """
        الحصول على تعليقات تذكرة
        
        Args:
            ticket_id: معرف التذكرة
            
        Returns:
            تعليقات التذكرة أو None إذا لم تكن موجودة
        """
        # التحقق من وجود التذكرة
        if ticket_id not in self.tickets:
            logger.warning(f"التذكرة {ticket_id} غير موجودة")
            return None
        
        # الحصول على التذكرة
        ticket = self.tickets[ticket_id]
        
        # الحصول على التعليقات
        return ticket["data"].get("comments", [])
    
    def get_tickets_by_status(self, status: str) -> List[Dict]:
        """
        الحصول على التذاكر حسب الحالة
        
        Args:
            status: الحالة
            
        Returns:
            قائمة التذاكر
        """
        return self.search_tickets({"status": status})
    
    def get_tickets_by_assignee(self, assignee: str) -> List[Dict]:
        """
        الحصول على التذاكر حسب المسؤول
        
        Args:
            assignee: المسؤول
            
        Returns:
            قائمة التذاكر
        """
        return self.search_tickets({"assignee": assignee})
    
    def get_tickets_by_type(self, ticket_type: str) -> List[Dict]:
        """
        الحصول على التذاكر حسب النوع
        
        Args:
            ticket_type: نوع التذكرة
            
        Returns:
            قائمة التذاكر
        """
        return self.search_tickets({"type": ticket_type})
    
    def get_tickets_by_priority(self, priority: str) -> List[Dict]:
        """
        الحصول على التذاكر حسب الأولوية
        
        Args:
            priority: الأولوية
            
        Returns:
            قائمة التذاكر
        """
        return self.search_tickets({"priority": priority})
    
    def export_tickets(self, ticket_ids: List[str] = None) -> Dict:
        """
        تصدير التذاكر
        
        Args:
            ticket_ids: قائمة معرفات التذاكر (اختياري)
            
        Returns:
            بيانات التذاكر
        """
        # تحديد التذاكر المراد تصديرها
        if ticket_ids is None:
            # تصدير جميع التذاكر
            export_data = {
                "tickets": list(self.tickets.values()),
                "exported_at": datetime.now().isoformat()
            }
        else:
            # تصدير التذاكر المحددة
            export_data = {
                "tickets": [
                    self.tickets[ticket_id]
                    for ticket_id in ticket_ids
                    if ticket_id in self.tickets
                ],
                "exported_at": datetime.now().isoformat()
            }
        
        return export_data
    
    def import_tickets(self, import_data: Dict) -> int:
        """
        استيراد التذاكر
        
        Args:
            import_data: بيانات التذاكر
            
        Returns:
            عدد التذاكر المستوردة
        """
        # التحقق من صحة البيانات
        if "tickets" not in import_data or not isinstance(import_data["tickets"], list):
            logger.warning("بيانات التذاكر غير صالحة")
            return 0
        
        # استيراد التذاكر
        imported_count = 0
        
        for ticket in import_data["tickets"]:
            # التحقق من وجود المعرف
            if "id" not in ticket:
                continue
            
            # إضافة التذكرة إلى القاموس
            self.tickets[ticket["id"]] = ticket
            imported_count += 1
        
        logger.info(f"تم استيراد {imported_count} تذكرة")
        return imported_count
    
    def _publish_event(self, event_type: str, event_data: Dict) -> None:
        """
        نشر حدث
        
        Args:
            event_type: نوع الحدث
            event_data: بيانات الحدث
        """
        if self.event_system:
            try:
                # نشر الحدث باستخدام نظام الأحداث
                self.event_system.publish(event_type, event_data, "ticket_system")
            except Exception as e:
                logger.error(f"خطأ في نشر الحدث {event_type}: {e}")
