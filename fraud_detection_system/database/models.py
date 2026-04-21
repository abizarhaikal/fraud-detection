"""
Database models for the fraud detection system.
"""

from sqlalchemy import Column, Integer, String, DateTime, Date, Text, Float, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Vendor(Base):
    """Vendor model for storing vendor information."""
    __tablename__ = 'vendors'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='active')  # active/inactive
    
    # Relationships
    events = relationship("Event", back_populates="vendor", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Vendor(id={self.id}, name='{self.name}', status='{self.status}')>"


class Event(Base):
    """Event model for storing event information."""
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    vendor_id = Column(Integer, ForeignKey('vendors.id'), nullable=False)
    name = Column(String(255), nullable=False)
    event_date = Column(Date, nullable=False)
    submission_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default='submitted')  # submitted/analyzed/flagged
    notes = Column(Text)
    
    # Relationships
    vendor = relationship("Vendor", back_populates="events")
    images = relationship("EventImage", back_populates="event", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Event(id={self.id}, name='{self.name}', vendor_id={self.vendor_id}, status='{self.status}')>"


class EventImage(Base):
    """Event image model for storing image information."""
    __tablename__ = 'event_images'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    filename = Column(String(255), nullable=False)  # Original filename
    file_path = Column(String(500), nullable=False)  # Unique storage path
    file_size = Column(Integer)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    event = relationship("Event", back_populates="images")
    hashes = relationship("ImageHash", back_populates="image", cascade="all, delete-orphan")
    new_image_analyses = relationship("FraudAnalysis", 
                                    foreign_keys="FraudAnalysis.new_image_id",
                                    back_populates="new_image", 
                                    cascade="all, delete-orphan")
    comparison_image_analyses = relationship("FraudAnalysis", 
                                           foreign_keys="FraudAnalysis.comparison_image_id",
                                           back_populates="comparison_image")
    
    def __repr__(self):
        return f"<EventImage(id={self.id}, filename='{self.filename}', event_id={self.event_id})>"


class ImageHash(Base):
    """Image hash model for storing calculated hashes."""
    __tablename__ = 'image_hashes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    image_id = Column(Integer, ForeignKey('event_images.id'), nullable=False)
    phash = Column(String(64))
    ahash = Column(String(64))
    dhash = Column(String(64))
    whash = Column(String(64))
    crop_resistant_hash = Column(String(128))
    file_hash = Column(String(32))  # MD5 hash
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    image = relationship("EventImage", back_populates="hashes")
    
    def __repr__(self):
        return f"<ImageHash(id={self.id}, image_id={self.image_id}, calculated_at='{self.calculated_at}')>"


class FraudAnalysis(Base):
    """Fraud analysis model for storing analysis results."""
    __tablename__ = 'fraud_analyses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    new_image_id = Column(Integer, ForeignKey('event_images.id'), nullable=False)
    comparison_image_id = Column(Integer, ForeignKey('event_images.id'), nullable=False)
    similarity_score = Column(Float)
    fraud_score = Column(Integer)
    verdict = Column(String(50))  # HIGH_RISK_FRAUD, LIKELY_FRAUD, etc.
    analysis_details = Column(Text)  # JSON string with detailed results
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    new_image = relationship("EventImage", 
                           foreign_keys=[new_image_id],
                           back_populates="new_image_analyses")
    comparison_image = relationship("EventImage", 
                                  foreign_keys=[comparison_image_id],
                                  back_populates="comparison_image_analyses")
    
    def __repr__(self):
        return f"<FraudAnalysis(id={self.id}, verdict='{self.verdict}', fraud_score={self.fraud_score})>"