from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

engine = create_engine("sqlite:///./todo.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    done: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

Base.metadata.create_all(engine)

def get_db():
    with SessionLocal() as db:
        yield db

def get_task(task_id: int, db: Session = Depends(get_db)) -> Task:
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(404, "Задача не найдена")
    return task

class TaskIn(BaseModel):
    title: str
    description: str = ""

class TaskOut(TaskIn):
    id: int
    done: bool
    created_at: datetime
    model_config = {"from_attributes": True}

app = FastAPI(title="ToDo List")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")

@app.post("/tasks", response_model=TaskOut, status_code=201, summary="Добавить задачу")
def create_task(data: TaskIn, db: Session = Depends(get_db)):
    task = Task(title=data.title, description=data.description)
    db.add(task)
    db.commit()
    return task

@app.get("/tasks", response_model=list[TaskOut], summary="Показать все задачи")
def list_tasks(db: Session = Depends(get_db)):
    return db.scalars(select(Task).order_by(Task.id)).all()

@app.patch("/tasks/{task_id}/done", response_model=TaskOut, summary="Отметить задачу выполненной")
def mark_done(task: Task = Depends(get_task), db: Session = Depends(get_db)):
    task.done = True
    db.commit()
    return task

@app.delete("/tasks/{task_id}", status_code=204, summary="Удалить задачу")
def delete_task(task: Task = Depends(get_task), db: Session = Depends(get_db)):
    db.delete(task)
    db.commit()