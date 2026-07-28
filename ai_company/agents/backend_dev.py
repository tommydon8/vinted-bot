"""BackendDeveloperAgent — genera un backend FastAPI + SQLAlchemy funzionante.

Il backend generato espone sempre il catalogo (Item), e in piu':
  - anagrafica Clienti, se preferences.enable_customer_accounts
  - Ordini (con relative righe OrderItem), se preferences.enable_online_orders

La terminologia (nomi di entita' esposti nelle risposte/URL "friendly")
segue le etichette definite dal profilo di business scelto dall'utente.
"""

from __future__ import annotations

from pathlib import Path

from ai_company.agents.base import BaseAgent
from ai_company.models import ArchitectureSpec, Preferences, RequirementsSpec

DATABASE_PY = '''"""Configurazione del database SQLite via SQLAlchemy."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./data/app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''


def _models_py(enable_orders: bool, enable_customers: bool) -> str:
    parts = ['''"""Modelli ORM SQLAlchemy."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String, default="")
    price = Column(Float, nullable=False, default=0.0)
    category = Column(String, default="")
    available = Column(Boolean, default=True)
''']

    if enable_customers:
        parts.append('''

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, default="")
    phone = Column(String, default="")
''')

    if enable_orders:
        parts.append('''

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)
    status = Column(String, default="ricevuto")
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    quantity = Column(Integer, default=1)

    order = relationship("Order", back_populates="items")
''')

    return "".join(parts)


def _schemas_py(enable_orders: bool, enable_customers: bool) -> str:
    parts = ['''"""Schemi Pydantic per validazione request/response."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ItemBase(BaseModel):
    name: str
    description: str = ""
    price: float = 0.0
    category: str = ""
    available: bool = True


class ItemCreate(ItemBase):
    pass


class ItemOut(ItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
''']

    if enable_customers:
        parts.append('''

class CustomerBase(BaseModel):
    name: str
    email: str = ""
    phone: str = ""


class CustomerCreate(CustomerBase):
    pass


class CustomerOut(CustomerBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
''')

    if enable_orders:
        parts.append('''

class OrderItemCreate(BaseModel):
    item_id: int
    quantity: int = 1


class OrderItemOut(OrderItemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class OrderCreate(BaseModel):
    customer_name: str
    items: list[OrderItemCreate]


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_name: str
    status: str
    created_at: datetime
    items: list[OrderItemOut] = []
''')

    return "".join(parts)


def _crud_py(enable_orders: bool, enable_customers: bool) -> str:
    parts = ['''"""Funzioni di accesso ai dati (CRUD)."""

from sqlalchemy.orm import Session

from app import models, schemas


def list_items(db: Session) -> list[models.Item]:
    return db.query(models.Item).all()


def create_item(db: Session, item: schemas.ItemCreate) -> models.Item:
    db_item = models.Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def get_item(db: Session, item_id: int) -> models.Item | None:
    return db.query(models.Item).filter(models.Item.id == item_id).first()


def delete_item(db: Session, item_id: int) -> bool:
    db_item = get_item(db, item_id)
    if not db_item:
        return False
    db.delete(db_item)
    db.commit()
    return True
''']

    if enable_customers:
        parts.append('''

def list_customers(db: Session) -> list[models.Customer]:
    return db.query(models.Customer).all()


def create_customer(db: Session, customer: schemas.CustomerCreate) -> models.Customer:
    db_customer = models.Customer(**customer.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer
''')

    if enable_orders:
        parts.append('''

def list_orders(db: Session) -> list[models.Order]:
    return db.query(models.Order).all()


def create_order(db: Session, order: schemas.OrderCreate) -> models.Order:
    db_order = models.Order(customer_name=order.customer_name)
    db.add(db_order)
    db.flush()
    for line in order.items:
        db.add(models.OrderItem(order_id=db_order.id, item_id=line.item_id, quantity=line.quantity))
    db.commit()
    db.refresh(db_order)
    return db_order


def update_order_status(db: Session, order_id: int, status: str) -> models.Order | None:
    db_order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not db_order:
        return None
    db_order.status = status
    db.commit()
    db.refresh(db_order)
    return db_order
''')

    return "".join(parts)


def _main_py(preferences: Preferences, requirements: RequirementsSpec) -> str:
    labels = requirements.entity_labels
    enable_orders = preferences.enable_online_orders
    enable_customers = preferences.enable_customer_accounts

    imports = ["from fastapi import FastAPI, HTTPException, Depends, Request"]
    imports.append("from fastapi.staticfiles import StaticFiles")
    imports.append("from fastapi.templating import Jinja2Templates")
    imports.append("from sqlalchemy.orm import Session")
    imports.append("")
    imports.append("from app import crud, models, schemas")
    imports.append("from app.database import Base, engine, get_db")

    body = f'''
Base.metadata.create_all(bind=engine)

app = FastAPI(title="{preferences.business_name}")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

BUSINESS_NAME = "{preferences.business_name}"
ITEM_LABEL = "{labels['item']}"
ITEM_LABEL_PLURAL = "{labels['item_plural']}"


@app.get("/health")
def health():
    return {{"status": "ok", "business": BUSINESS_NAME}}


@app.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    items = crud.list_items(db)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={{
            "business_name": BUSINESS_NAME,
            "item_label": ITEM_LABEL,
            "item_label_plural": ITEM_LABEL_PLURAL,
            "items": items,
        }},
    )


@app.get("/api/items", response_model=list[schemas.ItemOut])
def api_list_items(db: Session = Depends(get_db)):
    return crud.list_items(db)


@app.post("/api/items", response_model=schemas.ItemOut, status_code=201)
def api_create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db, item)


@app.get("/api/items/{{item_id}}", response_model=schemas.ItemOut)
def api_get_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="{labels['item']} non trovato")
    return db_item


@app.delete("/api/items/{{item_id}}", status_code=204)
def api_delete_item(item_id: int, db: Session = Depends(get_db)):
    if not crud.delete_item(db, item_id):
        raise HTTPException(status_code=404, detail="{labels['item']} non trovato")
'''

    if enable_customers:
        body += f'''

@app.get("/api/customers", response_model=list[schemas.CustomerOut])
def api_list_customers(db: Session = Depends(get_db)):
    return crud.list_customers(db)


@app.post("/api/customers", response_model=schemas.CustomerOut, status_code=201)
def api_create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    return crud.create_customer(db, customer)
'''

    if enable_orders:
        body += f'''

@app.get("/api/orders", response_model=list[schemas.OrderOut])
def api_list_orders(db: Session = Depends(get_db)):
    return crud.list_orders(db)


@app.post("/api/orders", response_model=schemas.OrderOut, status_code=201)
def api_create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    for line in order.items:
        if not crud.get_item(db, line.item_id):
            raise HTTPException(status_code=400, detail=f"{labels['item']} {{line.item_id}} inesistente")
    return crud.create_order(db, order)


@app.patch("/api/orders/{{order_id}}/status", response_model=schemas.OrderOut)
def api_update_order_status(order_id: int, status: str, db: Session = Depends(get_db)):
    db_order = crud.update_order_status(db, order_id, status)
    if not db_order:
        raise HTTPException(status_code=404, detail="{labels['order']} non trovato")
    return db_order
'''

    return "\n".join(imports) + "\n" + body


class BackendDeveloperAgent(BaseAgent):
    name = "Backend Developer Agent"
    role = "Genera il backend FastAPI + SQLAlchemy"

    def build(
        self,
        project_dir: Path,
        preferences: Preferences,
        requirements: RequirementsSpec,
        architecture: ArchitectureSpec,
    ) -> list[str]:
        enable_orders = preferences.enable_online_orders
        enable_customers = preferences.enable_customer_accounts

        written: list[str] = []
        app_dir = project_dir / "app"

        files = {
            app_dir / "__init__.py": "",
            app_dir / "database.py": DATABASE_PY,
            app_dir / "models.py": _models_py(enable_orders, enable_customers),
            app_dir / "schemas.py": _schemas_py(enable_orders, enable_customers),
            app_dir / "crud.py": _crud_py(enable_orders, enable_customers),
            app_dir / "main.py": _main_py(preferences, requirements),
        }
        for path, content in files.items():
            self._write(path, content)
            written.append(str(path.relative_to(project_dir)))

        (project_dir / "data").mkdir(parents=True, exist_ok=True)
        (project_dir / "data" / ".gitkeep").touch()

        return written
