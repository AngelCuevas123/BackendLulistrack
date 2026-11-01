from sqlalchemy import Column, String, Float, Integer
from database import Base

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

class DriverDB(Base):
    __tablename__ = "drivers"

    driver_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    vehicle = Column(String, nullable=False)
    completed_deliveries = Column(Integer, default=0)
    average_time = Column(String, nullable=False)
    