"""Funzioni di accesso ai dati (CRUD)."""

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


def list_customers(db: Session) -> list[models.Customer]:
    return db.query(models.Customer).all()


def create_customer(db: Session, customer: schemas.CustomerCreate) -> models.Customer:
    db_customer = models.Customer(**customer.model_dump())
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer


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
