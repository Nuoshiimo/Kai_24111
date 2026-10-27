import secrets
import string
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

engine = create_engine("sqlite:///./links.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

class Link(Base):
    __tablename__ = "links"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(unique=True, index=True)
    url: Mapped[str]

Base.metadata.create_all(engine)

def get_db():
    with SessionLocal() as db:
        yield db

class LinkIn(BaseModel):
    url: HttpUrl

class LinkOut(BaseModel):
    id: int
    url: str
    short_url: str

def to_out(link: Link, request: Request) -> LinkOut:
    return LinkOut(id=link.id, url=link.url, short_url=f"{request.base_url}{link.code}")

app = FastAPI(title="Сокращатель ссылок")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/docs")

@app.post("/links", response_model=LinkOut, status_code=201, summary="Создать короткую ссылку")
def create_link(data: LinkIn, request: Request, db: Session = Depends(get_db)):
    chars = string.ascii_letters + string.digits
    link = Link(code="".join(secrets.choice(chars) for _ in range(6)), url=str(data.url))
    db.add(link)
    db.commit()
    return to_out(link, request)

@app.get("/links", response_model=list[LinkOut], summary="Показать все ссылки")
def list_links(request: Request, db: Session = Depends(get_db)):
    return [to_out(link, request) for link in db.scalars(select(Link))]

@app.delete("/links/{link_id}", status_code=204, summary="Удалить ссылку по id")
def delete_link(link_id: int, db: Session = Depends(get_db)):
    link = db.get(Link, link_id)
    if not link:
        raise HTTPException(404, "Ссылка не найдена")
    db.delete(link)
    db.commit()

@app.get("/{code}", include_in_schema=False)
def follow(code: str, db: Session = Depends(get_db)):
    link = db.scalar(select(Link).where(Link.code == code))
    if not link:
        raise HTTPException(404, "Ссылка не найдена")
    return RedirectResponse(link.url)