"""
Database CRUD operations for the fraud detection system.
"""

import sys
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime, date
import json

# Add the parent directory to Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from .models import Vendor, Event, EventImage, ImageHash, FraudAnalysis
from .database import get_db


class VendorOperations:
    """CRUD operations for Vendor model."""
    
    @staticmethod
    def create_vendor(db: Session, name: str, status: str = "active") -> Vendor:
        """Create a new vendor."""
        vendor = Vendor(name=name, status=status)
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        return vendor
    
    @staticmethod
    def get_vendor_by_id(db: Session, vendor_id: int) -> Optional[Vendor]:
        """Get vendor by ID."""
        return db.query(Vendor).filter(Vendor.id == vendor_id).first()
    
    @staticmethod
    def get_vendor_by_name(db: Session, name: str) -> Optional[Vendor]:
        """Get vendor by name."""
        return db.query(Vendor).filter(Vendor.name == name).first()
    
    @staticmethod
    def get_all_vendors(db: Session, active_only: bool = True) -> List[Vendor]:
        """Get all vendors."""
        query = db.query(Vendor)
        if active_only:
            query = query.filter(Vendor.status == "active")
        return query.order_by(Vendor.name).all()
    
    @staticmethod
    def update_vendor_status(db: Session, vendor_id: int, status: str) -> Optional[Vendor]:
        """Update vendor status."""
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if vendor:
            vendor.status = status
            db.commit()
            db.refresh(vendor)
        return vendor
    
    @staticmethod
    def delete_vendor(db: Session, vendor_id: int) -> bool:
        """Delete vendor (soft delete by setting status to inactive)."""
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if vendor:
            vendor.status = "inactive"
            db.commit()
            return True
        return False


class EventOperations:
    """CRUD operations for Event model."""
    
    @staticmethod
    def create_event(db: Session, vendor_id: int, name: str, event_date: date, notes: str = None) -> Event:
        """Create a new event."""
        event = Event(
            vendor_id=vendor_id,
            name=name,
            event_date=event_date,
            notes=notes
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    
    @staticmethod
    def get_event_by_id(db: Session, event_id: int) -> Optional[Event]:
        """Get event by ID."""
        return db.query(Event).filter(Event.id == event_id).first()
    
    @staticmethod
    def get_events_by_vendor(db: Session, vendor_id: int) -> List[Event]:
        """Get all events for a vendor."""
        return db.query(Event).filter(Event.vendor_id == vendor_id).order_by(desc(Event.submission_date)).all()
    
    @staticmethod
    def get_all_events(db: Session) -> List[Event]:
        """Get all events."""
        return db.query(Event).order_by(desc(Event.submission_date)).all()
    
    @staticmethod
    def update_event_status(db: Session, event_id: int, status: str) -> Optional[Event]:
        """Update event status."""
        event = db.query(Event).filter(Event.id == event_id).first()
        if event:
            event.status = status
            db.commit()
            db.refresh(event)
        return event


class EventImageOperations:
    """CRUD operations for EventImage model."""
    
    @staticmethod
    def create_event_image(db: Session, event_id: int, filename: str, file_path: str, file_size: int) -> EventImage:
        """Create a new event image."""
        event_image = EventImage(
            event_id=event_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size
        )
        db.add(event_image)
        db.commit()
        db.refresh(event_image)
        return event_image
    
    @staticmethod
    def get_image_by_id(db: Session, image_id: int) -> Optional[EventImage]:
        """Get image by ID."""
        return db.query(EventImage).filter(EventImage.id == image_id).first()
    
    @staticmethod
    def get_images_by_event(db: Session, event_id: int) -> List[EventImage]:
        """Get all images for an event."""
        return db.query(EventImage).filter(EventImage.event_id == event_id).all()
    
    @staticmethod
    def get_all_images(db: Session) -> List[EventImage]:
        """Get all images."""
        return db.query(EventImage).order_by(desc(EventImage.upload_timestamp)).all()
    
    @staticmethod
    def get_images_for_analysis(db: Session, exclude_event_id: int = None) -> List[EventImage]:
        """Get images for fraud analysis (optionally excluding specific event)."""
        query = db.query(EventImage)
        if exclude_event_id:
            query = query.filter(EventImage.event_id != exclude_event_id)
        return query.all()


class ImageHashOperations:
    """CRUD operations for ImageHash model."""
    
    @staticmethod
    def create_image_hash(db: Session, image_id: int, phash: str, ahash: str, dhash: str, 
                         whash: str, crop_resistant_hash: str = None, file_hash: str = None) -> ImageHash:
        """Create image hash record."""
        image_hash = ImageHash(
            image_id=image_id,
            phash=phash,
            ahash=ahash,
            dhash=dhash,
            whash=whash,
            crop_resistant_hash=crop_resistant_hash,
            file_hash=file_hash
        )
        db.add(image_hash)
        db.commit()
        db.refresh(image_hash)
        return image_hash
    
    @staticmethod
    def get_hash_by_image_id(db: Session, image_id: int) -> Optional[ImageHash]:
        """Get hash by image ID."""
        return db.query(ImageHash).filter(ImageHash.image_id == image_id).first()
    
    @staticmethod
    def get_all_hashes(db: Session) -> List[ImageHash]:
        """Get all image hashes."""
        return db.query(ImageHash).all()


class FraudAnalysisOperations:
    """CRUD operations for FraudAnalysis model."""
    
    @staticmethod
    def create_fraud_analysis(db: Session, new_image_id: int, comparison_image_id: int,
                            similarity_score: float, fraud_score: int, verdict: str,
                            analysis_details: dict) -> FraudAnalysis:
        """Create fraud analysis record."""
        analysis = FraudAnalysis(
            new_image_id=new_image_id,
            comparison_image_id=comparison_image_id,
            similarity_score=similarity_score,
            fraud_score=fraud_score,
            verdict=verdict,
            analysis_details=json.dumps(analysis_details)
        )
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis
    
    @staticmethod
    def get_analyses_by_image(db: Session, image_id: int) -> List[FraudAnalysis]:
        """Get all analyses for an image."""
        return db.query(FraudAnalysis).filter(
            or_(
                FraudAnalysis.new_image_id == image_id,
                FraudAnalysis.comparison_image_id == image_id
            )
        ).order_by(desc(FraudAnalysis.analyzed_at)).all()
    
    @staticmethod
    def get_high_risk_analyses(db: Session) -> List[FraudAnalysis]:
        """Get high-risk fraud analyses."""
        return db.query(FraudAnalysis).filter(
            FraudAnalysis.verdict.in_(["HIGH_RISK_FRAUD", "LIKELY_FRAUD"])
        ).order_by(desc(FraudAnalysis.fraud_score)).all()
    
    @staticmethod
    def get_analyses_by_event(db: Session, event_id: int) -> List[FraudAnalysis]:
        """Get all analyses for images in an event."""
        return db.query(FraudAnalysis).join(
            EventImage, FraudAnalysis.new_image_id == EventImage.id
        ).filter(EventImage.event_id == event_id).all()


# Convenience functions for easy access
def create_vendor(name: str, status: str = "active") -> Vendor:
    """Create a vendor with automatic session management."""
    with next(get_db()) as db:
        return VendorOperations.create_vendor(db, name, status)

def get_all_vendors(active_only: bool = True) -> List[Vendor]:
    """Get all vendors with automatic session management."""
    with next(get_db()) as db:
        return VendorOperations.get_all_vendors(db, active_only)