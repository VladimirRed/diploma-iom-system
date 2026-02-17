from sqlalchemy.orm import Session
from database.models import Student
from datetime import date
from typing import List, Optional

class StudentService:
    def __init__(self, db: Session):
        self.db = db

    def create_student(self, full_name: str, birth_date: date, diagnosis_code: str, parent_contact: str, medical_tags: list = None) -> Student:
        """Создание новой карточки ученика с медицинскими тегами"""
        
        # Превращаем список ["Астма", "Эпилепсия"] в строку "Астма,Эпилепсия" для БД
        tags_str = ",".join(medical_tags) if medical_tags else ""
        
        new_student = Student(
            full_name=full_name,
            birth_date=birth_date,
            diagnosis_code=diagnosis_code,
            parent_contact=parent_contact,
            enrollment_date=date.today(),
            active=True,
            medical_tags=tags_str # Сохраняем строку
        )
        self.db.add(new_student)
        self.db.commit()
        self.db.refresh(new_student)
        return new_student
    

    def update_student(self, student_id: int, full_name: str, birth_date, diagnosis: str, parent: str, medical_tags: list):
        """Обновление данных ученика"""
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if student:
            student.full_name = full_name
            student.birth_date = birth_date
            student.diagnosis_code = diagnosis
            student.parent_contact = parent
            # Превращаем список обратно в строку
            student.medical_tags = ",".join(medical_tags) if medical_tags else ""
            
            self.db.commit()
            self.db.refresh(student)
            return student
        return None
    

    def delete_student(self, student_id: int):
        """Удаление ученика и всех связанных с ним данных"""
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if student:
            # SQLAlchemy автоматически удалит каскадные данные (диагностики, планы),
            # если в моделях настроено cascade="all, delete-orphan".
            # Если нет, удалит только ученика (или выдаст ошибку, если есть связи).
            # Для диплома пока просто удаляем объект.
            self.db.delete(student)
            self.db.commit()
            return True
        return False


    def get_all_students(self, active_only: bool = True) -> List[Student]:
        """Получение списка всех учеников"""
        query = self.db.query(Student)
        if active_only:
            query = query.filter(Student.active == True)
        return query.all()

    def get_student_by_id(self, student_id: int) -> Optional[Student]:
        """Поиск ученика по ID"""
        return self.db.query(Student).filter(Student.id == student_id).first()

    def get_total_count(self) -> int:
        """Статистика: всего активных учеников"""
        return self.db.query(Student).filter(Student.active == True).count()