import uuid
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from sqlalchemy.sql import func
from app.database import Base

class Feature(Base):
    __tablename__ = "features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_id = Column(String, index=True, nullable=False, unique=True)
    feature_type = Column(String, index=True, nullable=False) # building, road, field, parcel
    source = Column(String, index=True, nullable=False) # overture, osm, manual
    
    # Using EPSG:4326 for storage
    geometry = Column(Geometry('GEOMETRY', srid=4326), nullable=False)
    geometry_version = Column(Integer, default=1, nullable=False)
    
    properties = Column(JSON, default=dict)
    
    confidence_score = Column(Float, nullable=True)
    validation_status = Column(String, default="UNKNOWN")
    review_status = Column(String, default="DRAFT")
    approval_status = Column(String, default="PENDING")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
