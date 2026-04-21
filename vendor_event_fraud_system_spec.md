# 🏗️ Vendor Event Fraud Detection System - Spec-Driven Development Plan

## 📋 Project Overview

**Goal**: Build a comprehensive vendor event management system with fraud detection capabilities using image similarity analysis, featuring a user-friendly interface and persistent data storage.

## 🎯 Core Requirements Analysis

### Business Logic
- **Vendors**: Multiple vendors can submit events (dynamically selectable in UI)
- **Events**: Each event has name, date, vendor association, and multiple images
- **Fraud Detection**: Compare new event images against historical events to detect reuse
- **Pre-calculation**: Hash/analyze historical images for fast comparison
- **Workflow**: Simple vendor selection → event list → event submission → fraud analysis

### Technical Requirements
- **Database**: SQLite for persistence with ORM
- **File Storage**: Local file system for images (vendor-agnostic organization)
- **UI**: Streamlit (more suitable for data apps than EasyGUI)
- **Image Analysis**: Leverage existing fraud detection algorithms
- **Performance**: Pre-calculated hashes for fast comparisons

## 📊 System Architecture Specification

### 1. Data Model Design

```python
# Database Schema
class Vendor:
    - id: Integer (Primary Key)
    - name: String (Unique)
    - created_at: DateTime
    - status: String (active/inactive)

class Event:
    - id: Integer (Primary Key)
    - vendor_id: Integer (Foreign Key)
    - name: String
    - event_date: Date
    - submission_date: DateTime
    - status: String (submitted/analyzed/flagged)
    - notes: Text

class EventImage:
    - id: Integer (Primary Key)
    - event_id: Integer (Foreign Key)
    - filename: String
    - file_path: String
    - file_size: Integer
    - upload_timestamp: DateTime
    
class ImageHash:
    - id: Integer (Primary Key)
    - image_id: Integer (Foreign Key)
    - phash: String
    - ahash: String  
    - dhash: String
    - whash: String
    - crop_resistant_hash: String
    - file_hash: String (MD5)
    - calculated_at: DateTime

class FraudAnalysis:
    - id: Integer (Primary Key)
    - new_image_id: Integer (Foreign Key)
    - comparison_image_id: Integer (Foreign Key)
    - similarity_score: Float
    - fraud_score: Integer
    - verdict: String
    - analysis_details: JSON
    - analyzed_at: DateTime
```

### 2. Application Structure

```
fraud_detection_system/
├── app.py                 # Main Streamlit application
├── database/
│   ├── __init__.py
│   ├── models.py         # SQLAlchemy models
│   ├── database.py       # Database connection and setup
│   └── operations.py     # Database CRUD operations
├── fraud_engine/
│   ├── __init__.py
│   ├── hash_calculator.py    # Image hash calculations
│   ├── comparator.py        # Image comparison logic
│   └── analyzer.py          # Fraud analysis engine
├── ui/
│   ├── __init__.py
│   ├── vendor_management.py # Vendor selection/creation
│   ├── event_management.py  # Event listing/creation
│   └── analysis_results.py  # Results display
├── utils/
│   ├── __init__.py
│   ├── file_handler.py      # File operations
│   └── config.py           # Configuration settings
├── storage/
│   ├── uploads/            # All uploaded images (vendor-agnostic)
│   └── database.db         # SQLite database
└── requirements.txt
```

### 3. Revised Storage Strategy (Vendor-Agnostic)

**Why This Approach**:
- UI dynamically loads vendor data from database
- No hardcoded vendor directories
- Images stored by unique IDs, vendor association via database
- Easy vendor switching in UI without file system changes

```
storage/
├── uploads/
│   ├── img_001.jpg         # Images stored with unique IDs
│   ├── img_002.jpg         # Database tracks vendor/event association
│   ├── img_003.jpg
│   └── ...
└── database.db
```

**Database-Driven Vendor Management**:
```python
# UI Flow
1. Load all vendors from database into dropdown
2. User selects vendor -> query events for that vendor
3. User creates new event -> images uploaded with unique names
4. Database stores vendor_id -> event_id -> image_id relationships
5. Fraud analysis queries all historical images regardless of vendor
```

## 🚀 Development Phases

### Phase 1: Foundation Setup (Priority 1)
**Goal**: Database setup, basic models, and file structure

**Tasks**:
1. Create project structure
2. Set up SQLAlchemy models
3. Create database initialization scripts
4. Basic file handling utilities (vendor-agnostic)
5. Configuration management

**Deliverables**:
- Database schema created
- Basic CRUD operations
- File upload/storage system (unique ID based)

### Phase 2: Core Engine Integration (Priority 1)
**Goal**: Integrate existing fraud detection algorithms

**Tasks**:
1. Refactor existing fraud detection code into modular components
2. Create hash calculation service
3. Build image comparison engine
4. Implement batch processing for historical data
5. Create analysis result storage

**Deliverables**:
- Hash calculation module
- Image comparison service
- Database integration for analysis results

### Phase 3: Basic UI Development (Priority 2)
**Goal**: Streamlit interface for vendor and event management

**Tasks**:
1. Dynamic vendor selection/creation interface
2. Event listing and details view (filtered by selected vendor)
3. New event submission form
4. Image upload functionality (generates unique IDs)
5. Basic navigation structure

**Deliverables**:
- Working Streamlit app
- Dynamic vendor management interface
- Event submission workflow

### Phase 4: Advanced Analysis Interface (Priority 2)
**Goal**: Fraud analysis results and visualization

**Tasks**:
1. Real-time fraud analysis during submission
2. Analysis results display with visualizations
3. Historical comparison views (across all vendors)
4. Fraud score interpretation
5. Action recommendations

**Deliverables**:
- Analysis results dashboard
- Visual comparison tools
- Fraud scoring interface

### Phase 5: Performance Optimization (Priority 3)
**Goal**: Optimize for production use

**Tasks**:
1. Implement background hash calculation
2. Add caching for frequent operations  
3. Batch processing improvements
4. Database indexing optimization
5. Error handling and logging

**Deliverables**:
- Performance optimizations
- Robust error handling
- Logging system

## 🛠️ Technical Implementation Details

### Database Technology Stack
- **ORM**: SQLAlchemy (excellent Python ORM with good SQLite support)
- **Database**: SQLite (perfect for POC, easy deployment)
- **Migrations**: Alembic (SQLAlchemy migrations)

### UI Technology Choice: Streamlit
**Why Streamlit over EasyGUI**:
- Better for data-driven applications
- Built-in support for file uploads
- Easy visualization integration
- Web-based (accessible remotely)
- Better styling options
- Active community and development

### Dynamic Vendor Management Strategy

```python
# Streamlit UI Flow
def main():
    st.title("Vendor Event Fraud Detection System")
    
    # Dynamic vendor selection
    vendors = get_all_vendors()  # Query database
    selected_vendor = st.selectbox("Select Vendor", vendors)
    
    if selected_vendor:
        # Load events for selected vendor
        events = get_events_by_vendor(selected_vendor.id)
        
        # Event management interface
        display_events(events)
        
        # New event submission
        if st.button("Submit New Event"):
            show_event_submission_form(selected_vendor.id)

def show_event_submission_form(vendor_id):
    # Form for new event
    event_name = st.text_input("Event Name")
    event_date = st.date_input("Event Date")
    
    # File upload with unique ID generation
    uploaded_files = st.file_uploader("Upload Images", accept_multiple_files=True)
    
    if uploaded_files and st.button("Submit Event"):
        # Process submission
        event_id = create_event(vendor_id, event_name, event_date)
        
        for file in uploaded_files:
            # Generate unique filename
            unique_id = generate_unique_id()
            file_path = save_uploaded_file(file, unique_id)
            
            # Store in database with relationships
            image_id = create_event_image(event_id, file.name, file_path)
            
            # Calculate and store hashes
            calculate_and_store_hashes(image_id, file_path)
            
            # Run fraud analysis against historical images
            run_fraud_analysis(image_id)
```

### Image Analysis Integration
- Leverage existing algorithms from `fraud_detection.py`
- Pre-calculate hashes for all historical images
- Store analysis results for audit trails
- Implement incremental analysis for new submissions
- Cross-vendor comparison (detect if vendor A reuses vendor B's images)

## 📋 Detailed Task Breakdown

### Phase 1 Tasks (Week 1)

1. **Project Setup** (Day 1)
   - Create directory structure
   - Set up virtual environment
   - Install dependencies (SQLAlchemy, Streamlit, existing deps)

2. **Database Models** (Day 1-2)
   - Define SQLAlchemy models
   - Create database initialization
   - Set up basic CRUD operations

3. **File Handling** (Day 2)
   - Image upload utilities with unique ID generation
   - Vendor-agnostic file organization system
   - Path management

4. **Configuration** (Day 2)
   - Database connection settings
   - File path configurations
   - Streamlit app settings

### Phase 2 Tasks (Week 1-2)

5. **Hash Calculation Service** (Day 3)
   - Extract hash logic from existing code
   - Create batch hash calculator
   - Database integration for hash storage

6. **Comparison Engine** (Day 3-4)
   - Modularize fraud detection algorithms
   - Create comparison service
   - Optimize for database queries

7. **Analysis Engine** (Day 4-5)
   - Integrate fraud scoring
   - Result storage and retrieval
   - Historical analysis capabilities

### Phase 3 Tasks (Week 2)

8. **Dynamic Streamlit App** (Day 5-6)
   - App structure and navigation
   - Dynamic vendor selection interface
   - Event management pages with filtering

9. **Event Submission** (Day 6-7)
   - Form creation
   - Image upload integration with unique ID generation
   - Real-time validation

## 🎲 Risk Mitigation

### Technical Risks
- **Image processing performance**: Use background processing
- **Database scalability**: SQLite limitations for concurrent users
- **File storage growth**: Implement cleanup strategies
- **Vendor switching complexity**: Ensure proper database queries and UI state management

### Development Risks
- **Scope creep**: Stick to POC requirements
- **Integration complexity**: Thoroughly test existing code integration
- **UI/UX complexity**: Keep Streamlit interface simple and functional

## 📈 Success Metrics

### Phase 1 Success Criteria
- [ ] Database created and models working
- [ ] Basic CRUD operations functional
- [ ] File upload/storage working with unique IDs

### Phase 2 Success Criteria  
- [ ] Hash calculation for all image types
- [ ] Fraud detection engine integrated
- [ ] Historical data processing complete

### Phase 3 Success Criteria
- [ ] Working Streamlit application
- [ ] Dynamic vendor and event management functional
- [ ] New event submission working with proper file handling

### Final POC Success Criteria
- [ ] Complete vendor-event workflow
- [ ] Real-time fraud analysis
- [ ] Historical comparison capabilities (cross-vendor)
- [ ] Intuitive user interface with smooth vendor switching

## 🚀 Next Steps

**Ready to start implementation with**:
1. **Phase 1**: Create project structure and database models
2. **Dynamic vendor management**: Database-driven approach, no hardcoded vendor directories
3. **Vendor-agnostic file storage**: Unique ID-based image storage with database relationships
4. **Cross-vendor fraud detection**: Analyze new images against all historical images regardless of vendor

This approach provides maximum flexibility for POC testing while maintaining clean separation of concerns between UI state management and data persistence.