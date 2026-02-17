import enum
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, Text, Float, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base

# --- Перечисления (Enums) для жесткого ограничения выбора ---

class UserRole(enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    PARENT = "parent"

class DiagnosticType(enum.Enum):
    PRIMARY = "primary"         # Первичная
    INTERMEDIATE = "intermediate" # Промежуточная
    FINAL = "final"             # Итоговая

class PlanStatus(enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class LogStatus(enum.Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

# --- Модели Таблиц ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.TEACHER)
    specialization = Column(String, nullable=True) # Например: Логопед

    # Связи
    diagnostics = relationship("Diagnostic", back_populates="teacher")
    created_plans = relationship("EducationalPlan", back_populates="creator")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    diagnosis_code = Column(String, nullable=True)
    parent_contact = Column(String, nullable=True)
    enrollment_date = Column(Date, default=func.now())
    active = Column(Boolean, default=True)
    
    # НОВОЕ ПОЛЕ: Список болезней через запятую (напр: "Астма,Эпилепсия")
    medical_tags = Column(String, nullable=True, default="") 

    # Связи
    diagnostics = relationship("Diagnostic", back_populates="student")
    plans = relationship("EducationalPlan", back_populates="student")


class SkillCategory(Base):
    __tablename__ = "skills_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    # Самоссылающаяся связь (Сфера -> Навык)
    parent_id = Column(Integer, ForeignKey("skills_categories.id"), nullable=True)
    
    children = relationship("SkillCategory", backref="parent", remote_side=[id])
    exercises = relationship("Exercise", back_populates="skill")
    diagnostic_results = relationship("DiagnosticResult", back_populates="skill")


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    skill_id = Column(Integer, ForeignKey("skills_categories.id"))
    difficulty_level = Column(Integer) # 1-5
    materials = Column(String, nullable=True)
    duration_minutes = Column(Integer, default=15)
    contraindications = Column(Text, nullable=True)

    # НОВОЕ ПОЛЕ: Рейтинг эффективности (0.0 - 10.0)
    effectiveness_score = Column(Float, default=5.0)

    # Связи
    skill = relationship("SkillCategory", back_populates="exercises")
    plan_items = relationship("PlanItem", back_populates="exercise")


class Diagnostic(Base):
    __tablename__ = "diagnostics"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    teacher_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, default=func.now())
    type = Column(Enum(DiagnosticType), default=DiagnosticType.PRIMARY)
    summary = Column(Text, nullable=True)

    # Связи
    student = relationship("Student", back_populates="diagnostics")
    teacher = relationship("User", back_populates="diagnostics")
    results = relationship("DiagnosticResult", back_populates="diagnostic", cascade="all, delete-orphan")


class DiagnosticResult(Base):
    __tablename__ = "diagnostic_results"

    id = Column(Integer, primary_key=True, index=True)
    diagnostic_id = Column(Integer, ForeignKey("diagnostics.id"))
    skill_id = Column(Integer, ForeignKey("skills_categories.id"))
    score = Column(Float, nullable=False) # 0.0 - 5.0 (можно дробные)
    comment = Column(Text, nullable=True)

    # Связи
    diagnostic = relationship("Diagnostic", back_populates="results")
    skill = relationship("SkillCategory", back_populates="diagnostic_results")


class EducationalPlan(Base):
    __tablename__ = "educational_plans"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    creator_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(Enum(PlanStatus), default=PlanStatus.DRAFT)
    goal_description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    # Связи
    student = relationship("Student", back_populates="plans")
    creator = relationship("User", back_populates="created_plans")
    items = relationship("PlanItem", back_populates="plan", cascade="all, delete-orphan")


class PlanItem(Base):
    __tablename__ = "plan_items"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("educational_plans.id"))
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    frequency = Column(String, nullable=True) # "2 раза в неделю"
    target_score = Column(Integer, nullable=True)
    order_index = Column(Integer, default=0) # Порядок выполнения

    # Связи
    plan = relationship("EducationalPlan", back_populates="items")
    exercise = relationship("Exercise", back_populates="plan_items")
    logs = relationship("ProgressLog", back_populates="item", cascade="all, delete-orphan")


class ProgressLog(Base):
    __tablename__ = "progress_log"

    id = Column(Integer, primary_key=True, index=True)
    plan_item_id = Column(Integer, ForeignKey("plan_items.id"))
    date = Column(Date, default=func.now())
    status = Column(Enum(LogStatus), default=LogStatus.COMPLETED)
    performance_score = Column(Integer, nullable=True) # 1-5
    teacher_notes = Column(Text, nullable=True)

    # Связи
    item = relationship("PlanItem", back_populates="logs")