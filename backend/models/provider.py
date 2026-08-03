from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database.database import Base

class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    bio = Column(String, nullable=True)
    business_name = Column(String, nullable=True)
    category = Column(String, nullable=False)  # e.g., Plumbing, Cleaning, IT
    hourly_rate = Column(Float, nullable=False, default=0.0)
    rating = Column(Float, default=0.0)
    is_verified = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="provider")
    services = relationship("Service", back_populates="provider", cascade="all, delete-orphan")
