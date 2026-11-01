
from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from database import Base


class DriverDB(Base):
    __tablename__ = "drivers"

    driver_id = Column(String, primary_key=True, index=True)
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

