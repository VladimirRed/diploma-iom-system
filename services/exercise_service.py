from sqlalchemy.orm import Session
from database.models import Exercise, SkillCategory
from typing import List

class ExerciseService:
    def __init__(self, db: Session):
        self.db = db

    def create_exercise(self, title, description, skill_id, difficulty, materials, duration, score):
        """Добавление новой методики в базу"""
        new_ex = Exercise(
            title=title,
            description=description,
            skill_id=skill_id,
            difficulty_level=difficulty,
            materials=materials,
            duration_minutes=duration,
            effectiveness_score=score # Педагог сам ставит начальный рейтинг
        )
        self.db.add(new_ex)
        self.db.commit()
        return new_ex
    

    def update_exercise(self, ex_id: int, title, description, skill_id, difficulty, materials, duration, score, contraindications_list):
        """Обновление методики"""
        ex = self.db.query(Exercise).filter(Exercise.id == ex_id).first()
        if ex:
            ex.title = title
            ex.description = description
            ex.skill_id = skill_id
            ex.difficulty_level = difficulty
            ex.materials = materials
            ex.duration_minutes = duration
            ex.effectiveness_score = score
            # Список тегов -> строка
            ex.contraindications = ",".join(contraindications_list) if contraindications_list else ""
            
            self.db.commit()
            self.db.refresh(ex)
            return ex
        return None
    

    def get_all_exercises(self) -> List[Exercise]:
        """Получить все, отсортированные по рейтингу (лучшие сверху)"""
        return self.db.query(Exercise).order_by(Exercise.effectiveness_score.desc()).all()

    def delete_exercise(self, exercise_id: int):
        """Удаление методики"""
        ex = self.db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if ex:
            self.db.delete(ex)
            self.db.commit()

    def get_all_skills(self):
        """Список навыков для выпадающего списка"""
        return self.db.query(SkillCategory).filter(SkillCategory.parent_id.isnot(None)).all()