from sqlalchemy import Column, Integer, String
from database import Base

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String)
    phone = Column(String)

    service = Column(String)

    date = Column(String)
    time = Column(String)

    status = Column(String)
