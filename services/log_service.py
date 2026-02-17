from sqlalchemy.orm import Session
from datetime import date
from typing import List, Dict
from database.models import (
    EducationalPlan, PlanItem, ProgressLog, 
    LogStatus, PlanStatus
)

class LogService:
    def __init__(self, db: Session):
        self.db = db

    def get_active_plan(self, student_id: int) -> EducationalPlan:
        """Находит текущий активный план ребенка (самый свежий)"""
        return self.db.query(EducationalPlan)\
            .filter(EducationalPlan.student_id == student_id)\
            .filter(EducationalPlan.status == PlanStatus.ACTIVE)\
            .order_by(EducationalPlan.created_at.desc())\
            .first()

    def get_logs_for_date(self, plan_id: int, log_date: date) -> Dict[int, ProgressLog]:
        """
        Возвращает словарь {plan_item_id: ProgressLog} за конкретную дату.
        Это нужно, чтобы отобразить в интерфейсе уже введенные данные.
        """
        logs = self.db.query(ProgressLog)\
            .join(PlanItem)\
            .filter(PlanItem.plan_id == plan_id)\
            .filter(ProgressLog.date == log_date)\
            .all()
        
        return {log.plan_item_id: log for log in logs}
    
    def get_all_logs_for_plan(self, plan_id: int):
        """
        Получает историю выполнения для отчета.
        Сортируем по дате (сначала новые).
        """
        return self.db.query(ProgressLog)\
            .join(PlanItem)\
            .filter(PlanItem.plan_id == plan_id)\
            .order_by(ProgressLog.date.desc())\
            .all()

    def save_daily_log(self, item_id: int, log_date: date, status: str, score: int, notes: str):
        """
        Сохраняет или обновляет запись в дневнике.
        """
        # 1. Проверяем, есть ли уже запись за этот день для этого упражнения
        existing_log = self.db.query(ProgressLog)\
            .filter(ProgressLog.plan_item_id == item_id)\
            .filter(ProgressLog.date == log_date)\
            .first()

        if existing_log:
            # Обновляем существующую
            existing_log.status = LogStatus(status)
            existing_log.performance_score = score
            existing_log.teacher_notes = notes
        else:
            # Создаем новую
            new_log = ProgressLog(
                plan_item_id=item_id,
                date=log_date,
                status=LogStatus(status),
                performance_score=score,
                teacher_notes=notes
            )
            self.db.add(new_log)
        
        self.db.commit()