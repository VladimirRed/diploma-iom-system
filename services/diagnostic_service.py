from sqlalchemy.orm import Session
from sqlalchemy import func
from database.models import Diagnostic, DiagnosticResult, SkillCategory, DiagnosticType
from datetime import date
from typing import List, Dict

class DiagnosticService:
    def __init__(self, db: Session):
        self.db = db

    def get_assessment_skills(self) -> List[SkillCategory]:
        """
        Получает список навыков, которые нужно оценить.
        Берем только те категории, у которых есть parent_id (то есть это конкретные навыки, а не общие сферы).
        """
        return self.db.query(SkillCategory).filter(SkillCategory.parent_id.isnot(None)).all()

    def save_diagnostic(self, student_id: int, teacher_id: int, d_type: str, scores: Dict[int, int], summary: str = ""):
        """
        Сохранение результатов диагностики.
        scores: словарь {skill_id: оценка}
        """
        # 1. Создаем запись о самой диагностике
        new_diagnostic = Diagnostic(
            student_id=student_id,
            teacher_id=teacher_id, # В реальной системе брать из сессии, пока заглушка
            date=date.today(),
            type=DiagnosticType(d_type),
            summary=summary
        )
        self.db.add(new_diagnostic)
        self.db.commit()
        self.db.refresh(new_diagnostic)

        # 2. Сохраняем результаты по каждому навыку
        results = []
        for skill_id, score in scores.items():
            result = DiagnosticResult(
                diagnostic_id=new_diagnostic.id,
                skill_id=skill_id,
                score=float(score),
                comment="" 
            )
            results.append(result)
        
        self.db.add_all(results)
        self.db.commit()
        return new_diagnostic

    def get_latest_diagnostic(self, student_id: int):
        """Получить последнюю диагностику ребенка для построения графика"""
        return self.db.query(Diagnostic)\
            .filter(Diagnostic.student_id == student_id)\
            .order_by(Diagnostic.date.desc())\
            .first()
    
    def get_all_diagnostics(self, student_id: int) -> List[Diagnostic]:
        """
        Получает ВСЕ диагностики ученика, отсортированные по дате.
        Нужно для построения сравнительного графика.
        """
        return self.db.query(Diagnostic)\
            .filter(Diagnostic.student_id == student_id)\
            .order_by(Diagnostic.date.asc())\
            .all()