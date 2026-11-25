from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth import verificar_administrador
from database import get_db
from models import InventoryProductDB
from schemas import (
    InventoryProductCreate,
    InventoryProductResponse,
    InventoryProductUpdate
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/products", response_model=List[InventoryProductResponse])
def get_products(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    usuario: dict = Depends(verificar_administrador)
):
    query = db.query(InventoryProductDB)

    if not include_inactive:
        query = query.filter(InventoryProductDB.is_active.is_(True))

    return query.order_by(InventoryProductDB.name.asc()).all()


@router.post(
    "/products",
    response_model=InventoryProductResponse,
    status_code=201
)
def create_product(
    product: InventoryProductCreate,
    db: Session = Depends(get_db),
    usuario: dict = Depends(verificar_administrador)
):
    new_product = InventoryProductDB(
        id=f"prd-{uuid4().hex[:10]}",
        sku=product.sku.strip().upper(),
        name=product.name.strip(),
        description=(product.description or "").strip() or None,
        unit=product.unit.strip(),
        stock_quantity=product.stock_quantity,
        min_stock=product.min_stock,
        unit_price=product.unit_price,
        is_active=True
    )

    try:
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe un producto con ese código SKU"
        )

    return new_product


@router.patch(
    "/products/{product_id}",
    response_model=InventoryProductResponse
)
def update_product(
    product_id: str,
    changes: InventoryProductUpdate,
    db: Session = Depends(get_db),
    usuario: dict = Depends(verificar_administrador)
):
    product = db.query(InventoryProductDB).filter(
        InventoryProductDB.id == product_id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    values = changes.dict(exclude_unset=True)

    if "sku" in values and values["sku"] is not None:
        values["sku"] = values["sku"].strip().upper()
    if "name" in values and values["name"] is not None:
        values["name"] = values["name"].strip()
    if "description" in values and values["description"] is not None:
        values["description"] = values["description"].strip() or None
    if "unit" in values and values["unit"] is not None:
        values["unit"] = values["unit"].strip()

    for field, value in values.items():
        setattr(product, field, value)

    try:
        db.commit()
        db.refresh(product)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Ya existe un producto con ese código SKU"
        )

    return product


@router.delete("/products/{product_id}", status_code=204)
def deactivate_product(
    product_id: str,
    db: Session = Depends(get_db),
    usuario: dict = Depends(verificar_administrador)
):
    product = db.query(InventoryProductDB).filter(
        InventoryProductDB.id == product_id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    product.is_active = False
    db.commit()
    return None
