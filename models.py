
import uuid

from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    ForeignKey,
    DateTime,
    Text,
    Boolean,
    func
)
from sqlalchemy.orm import relationship
from database import Base


class DriverDB(Base):
    __tablename__ = "drivers"

    driver_id = Column(String, primary_key=True, index=True)

    # Relacion con el usuario de Supabase
    auth_user_id = Column(String(36), unique=True, nullable=True, index=True)

    name = Column(String, nullable=False)
    vehicle = Column(String, nullable=False)
    completed_deliveries = Column(Integer, default=0)
    average_time = Column(String, nullable=False, default="Sin datos")

    # Relacion con los pedidos
    orders = relationship("OrderDB", back_populates="driver")


class OrderDB(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, index=True)
    tracking_number = Column(String, unique=True, index=True)
    client_name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    colony = Column(String, nullable=False)
    estimated_time = Column(String, nullable=False)
    status = Column(String, default="en_transito")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Repartidor asignado
    driver_id = Column(
        String,
        ForeignKey("drivers.driver_id"),
        nullable=True
    )

    # Evidencia de entrega
    photo_path = Column(String, nullable=True)
    signature = Column(Text, nullable=True)
    proof_timestamp = Column(DateTime, nullable=True)

    # Relacion con el repartidor
    driver = relationship("DriverDB", back_populates="orders")
    items = relationship("OrderItemDB", back_populates="order")


class DriverDeviceDB(Base):
    __tablename__ = "driver_devices"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    driver_id = Column(
        String,
        ForeignKey("drivers.driver_id"),
        nullable=False,
        index=True
    )

    firebase_installation_id = Column(
        String,
        nullable=False,
        unique=True,
        index=True
    )

    platform = Column(String(20), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class DriverLocationDB(Base):
    __tablename__ = "driver_locations"

    driver_id = Column(
        String,
        ForeignKey("drivers.driver_id"),
        primary_key=True,
        index=True
    )

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    accuracy = Column(Float, nullable=True)

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class InventoryProductDB(Base):
    __tablename__ = "inventory_products"

    id = Column(String, primary_key=True, index=True)
    sku = Column(String(40), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    unit = Column(String(30), nullable=False, default="pieza")
    stock_quantity = Column(Integer, nullable=False, default=0)
    min_stock = Column(Integer, nullable=False, default=0)
    unit_price = Column(Float, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    order_items = relationship("OrderItemDB", back_populates="product")


class OrderItemDB(Base):
    __tablename__ = "order_items"

    id = Column(String, primary_key=True, index=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False, index=True)
    product_id = Column(String, ForeignKey("inventory_products.id"), nullable=False, index=True)
    product_name = Column(String(120), nullable=False)
    sku = Column(String(40), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    order = relationship("OrderDB", back_populates="items")
    product = relationship("InventoryProductDB", back_populates="order_items")
