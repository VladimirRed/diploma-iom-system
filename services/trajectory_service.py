from sqlalchemy.orm import Session
from datetime import date
from typing import List, Dict
from database.models import (
    Diagnostic, DiagnosticResult, Exercise, 
    EducationalPlan, PlanItem, PlanStatus, Student
)

class TrajectoryService:
    def __init__(self, db: Session):
        self.db = db

    def analyze_diagnostic(self, student_id: int, threshold: float = 3.0) -> Dict:
        """
        АЛГОРИТМ 1: Выявление дефицитов.
        Находит навыки, где балл ниже порогового (threshold).
        Возвращает: {skill_id: score}
        """
        # Берем последнюю диагностику
        last_diag = self.db.query(Diagnostic)\
            .filter(Diagnostic.student_id == student_id)\
            .order_by(Diagnostic.date.desc())\
            .first()

        if not last_diag:
            return None

        # Фильтруем результаты: ищем слабые зоны
        weak_skills = {}
        for res in last_diag.results:
            if res.score < threshold:
                weak_skills[res.skill_id] = res.score
        
        return weak_skills

    def get_recommendations(self, student_id: int, weak_skills_ids: List[int]) -> List[Exercise]:
        """
        АЛГОРИТМ: Подбор с учетом РЕЙТИНГА и БЕЗОПАСНОСТИ.
        """
        if not weak_skills_ids:
            return []

        # 1. Получаем данные ребенка, чтобы узнать его болезни
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return []
            
        # Превращаем строку из БД ("Астма,Эпилепсия") в множество Python {"Астма", "Эпилепсия"}
        student_contraindications = set(student.medical_tags.split(",")) if student.medical_tags else set()

        # 2. Запрос всех подходящих упражнений
        candidates = self.db.query(Exercise)\
            .filter(Exercise.skill_id.in_(weak_skills_ids))\
            .order_by(Exercise.effectiveness_score.desc())\
            .all()
        
        safe_recommendations = []
        
        # 3. ФИЛЬТРАЦИЯ (Safety Filter)
        for ex in candidates:
            # Получаем противопоказания упражнения
            ex_contraindications = set(ex.contraindications.split(",")) if ex.contraindications else set()
            
            # Проверяем пересечение множеств (есть ли общие элементы)
            # Если пересечение НЕ пустое -> значит есть конфликт -> упражнение ОПАСНО
            intersection = student_contraindications.intersection(ex_contraindications)
            
            # Удаляем пустые строки из пересечения (бывают из-за split)
            intersection.discard("") 

            if intersection:
                # Упражнение опасно! Пропускаем его.
                # Можно логировать: print(f"Упражнение {ex.title} исключено из-за {intersection}")
                continue
            else:
                safe_recommendations.append(ex)

        return safe_recommendations

    def create_educational_plan(self, student_id: int, creator_id: int, 
                              goal: str, start_date: date, end_date: date, 
                              exercises: List[Exercise]) -> EducationalPlan:
        """
        Сохранение плана с ЖЕСТКОЙ АВТО-АРХИВАЦИЕЙ.
        Гарантирует, что у ученика будет только 1 активный план.
        """
        # 1. Находим ВСЕ планы (даже если их случайно стало несколько) и архивируем
        old_plans = self.db.query(EducationalPlan).filter(
            EducationalPlan.student_id == student_id,
            EducationalPlan.status == PlanStatus.ACTIVE
        ).all()
        
        for plan in old_plans:
            plan.status = PlanStatus.ARCHIVED
        
        # Применяем изменения (архивацию)
        self.db.commit()

        # 2. Создаем новый план
        new_plan = EducationalPlan(
            student_id=student_id,
            creator_id=creator_id,
            status=PlanStatus.ACTIVE, # Только этот будет активным
            goal_description=goal,
            start_date=start_date,
            end_date=end_date
        )
        self.db.add(new_plan)
        self.db.commit()
        self.db.refresh(new_plan)

        # 3. Привязываем упражнения
        plan_items = []
        for index, ex in enumerate(exercises):
            item = PlanItem(
                plan_id=new_plan.id,
                exercise_id=ex.id,
                frequency="2 раза в неделю",
                target_score=5,
                order_index=index + 1
            )
            plan_items.append(item)

        self.db.add_all(plan_items)
        self.db.commit()
        
        return new_plan