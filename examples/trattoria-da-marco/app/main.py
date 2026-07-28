from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Trattoria da Marco")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

BUSINESS_NAME = "Trattoria da Marco"
ITEM_LABEL = "Piatto"
ITEM_LABEL_PLURAL = "Menù"


@app.get("/health")
def health():
    return {"status": "ok", "business": BUSINESS_NAME}


@app.get("/")
def index(request: Request, db: Session = Depends(get_db)):
    items = crud.list_items(db)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "business_name": BUSINESS_NAME,
            "item_label": ITEM_LABEL,
            "item_label_plural": ITEM_LABEL_PLURAL,
            "items": items,
        },
    )


@app.get("/api/items", response_model=list[schemas.ItemOut])
def api_list_items(db: Session = Depends(get_db)):
    return crud.list_items(db)


@app.post("/api/items", response_model=schemas.ItemOut, status_code=201)
def api_create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
    return crud.create_item(db, item)


@app.get("/api/items/{item_id}", response_model=schemas.ItemOut)
def api_get_item(item_id: int, db: Session = Depends(get_db)):
    db_item = crud.get_item(db, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Piatto non trovato")
    return db_item


@app.delete("/api/items/{item_id}", status_code=204)
def api_delete_item(item_id: int, db: Session = Depends(get_db)):
    if not crud.delete_item(db, item_id):
        raise HTTPException(status_code=404, detail="Piatto non trovato")


@app.get("/api/customers", response_model=list[schemas.CustomerOut])
def api_list_customers(db: Session = Depends(get_db)):
    return crud.list_customers(db)


@app.post("/api/customers", response_model=schemas.CustomerOut, status_code=201)
def api_create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    return crud.create_customer(db, customer)


@app.get("/api/orders", response_model=list[schemas.OrderOut])
def api_list_orders(db: Session = Depends(get_db)):
    return crud.list_orders(db)


@app.post("/api/orders", response_model=schemas.OrderOut, status_code=201)
def api_create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    for line in order.items:
        if not crud.get_item(db, line.item_id):
            raise HTTPException(status_code=400, detail=f"Piatto {line.item_id} inesistente")
    return crud.create_order(db, order)


@app.patch("/api/orders/{order_id}/status", response_model=schemas.OrderOut)
def api_update_order_status(order_id: int, status: str, db: Session = Depends(get_db)):
    db_order = crud.update_order_status(db, order_id, status)
    if not db_order:
        raise HTTPException(status_code=404, detail="Comanda non trovato")
    return db_order
