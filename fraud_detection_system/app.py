"""
Main Streamlit application for Vendor Event Fraud Detection System.
"""

import streamlit as st
from datetime import date, datetime
import sys
import os

# Add the system path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from database.database import init_database, get_db
from database.operations import VendorOperations, EventOperations, EventImageOperations
from utils.config import Config
from utils.file_handler import StreamlitFileHandler
from fraud_engine.batch_processor import DatabaseHashProcessor, process_new_image
from fraud_engine.analyzer import FraudAnalyzer


def init_app():
    """Initialize the application and database."""
    st.set_page_config(
        page_title=Config.STREAMLIT_TITLE,
        page_icon=Config.STREAMLIT_ICON,
        layout="wide"
    )
    
    # Initialize database on first run
    if 'db_initialized' not in st.session_state:
        try:
            init_database()
            st.session_state.db_initialized = True
            st.success("✅ Database initialized successfully!")
        except Exception as e:
            st.error(f"❌ Database initialization failed: {e}")
            return False
    
    return True


def vendor_management_page():
    """Vendor selection and management page."""
    st.header("🏢 Vendor Management")
    
    # Get database session
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Display current vendors
        vendors = VendorOperations.get_all_vendors(db)
        
        if vendors:
            st.subheader("📋 Current Vendors")
            vendor_names = [f"{v.name} (ID: {v.id})" for v in vendors]
            
            # Vendor selection
            selected_vendor_display = st.selectbox(
                "Select Vendor:",
                [""] + vendor_names,
                key="vendor_selector"
            )
            
            if selected_vendor_display:
                # Extract vendor ID from display string
                vendor_id = int(selected_vendor_display.split("ID: ")[1].split(")")[0])
                selected_vendor = VendorOperations.get_vendor_by_id(db, vendor_id)
                
                if selected_vendor:
                    st.session_state.selected_vendor_id = vendor_id
                    st.session_state.selected_vendor_name = selected_vendor.name
                    
                    st.success(f"✅ Selected vendor: **{selected_vendor.name}**")
                    
                    # Show vendor events
                    events = EventOperations.get_events_by_vendor(db, vendor_id)
                    
                    if events:
                        st.subheader(f"📅 Events for {selected_vendor.name}")
                        
                        for event in events[:5]:  # Show recent 5 events
                            # Get fraud analysis results for this event
                            from database.operations import FraudAnalysisOperations
                            event_analyses = FraudAnalysisOperations.get_analyses_by_event(db, event.id)
                            
                            # Determine status color and icon
                            status_color = "🟢"
                            if event.status == "flagged":
                                status_color = "🚨"
                            elif event.status == "reviewed":
                                status_color = "⚠️"
                            elif event.status == "analyzed":
                                status_color = "✅"
                            
                            # Count analysis results
                            high_risk_count = len([a for a in event_analyses if a.fraud_score >= 80])
                            moderate_risk_count = len([a for a in event_analyses if 60 <= a.fraud_score < 80])
                            
                            risk_text = ""
                            if high_risk_count > 0:
                                risk_text = f"🚨 {high_risk_count} high-risk"
                            elif moderate_risk_count > 0:
                                risk_text = f"⚠️ {moderate_risk_count} moderate-risk"
                            elif event_analyses:
                                risk_text = f"✅ {len(event_analyses)} clean"
                            else:
                                risk_text = "📊 No analysis"
                            
                            with st.expander(f"{status_color} {event.name} - {event.event_date} ({risk_text})"):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write(f"**Status:** {event.status}")
                                    st.write(f"**Submitted:** {event.submission_date.strftime('%Y-%m-%d %H:%M')}")
                                    if event.notes:
                                        st.write(f"**Notes:** {event.notes}")
                                
                                with col2:
                                    # Show images for this event
                                    images = EventImageOperations.get_images_by_event(db, event.id)
                                    if images:
                                        st.write(f"**Images:** {len(images)} uploaded")
                                        
                                        # Show analysis summary
                                        if event_analyses:
                                            st.write(f"**Analysis Results:** {len(event_analyses)} comparisons")
                                            if high_risk_count > 0:
                                                st.error(f"🚨 {high_risk_count} HIGH RISK matches")
                                            if moderate_risk_count > 0:
                                                st.warning(f"⚠️ {moderate_risk_count} MODERATE RISK matches")
                                        else:
                                            st.write("**Analysis:** No suspicious matches found")
                                
                                # Show detailed analysis results if any
                                if event_analyses:
                                    st.subheader("🔍 Fraud Analysis Details")
                                    
                                    for analysis in event_analyses[:3]:  # Show top 3 matches
                                        severity = "🚨 HIGH" if analysis.fraud_score >= 80 else "⚠️ MODERATE" if analysis.fraud_score >= 60 else "🟡 LOW"
                                        
                                        with st.container():
                                            st.write(f"**{severity} RISK** - Score: {analysis.fraud_score}/100")
                                            
                                            # Get comparison image details
                                            comp_image = EventImageOperations.get_image_by_id(db, analysis.comparison_image_id)
                                            if comp_image:
                                                st.write(f"• Similar to: `{comp_image.filename}` from event `{comp_image.event.name}`")
                                                st.write(f"• Similarity: {analysis.similarity_score:.1f}%")
                                                st.write(f"• Verdict: {analysis.verdict}")
                                            
                                            # Show analysis details if available
                                            if analysis.analysis_details:
                                                try:
                                                    import json
                                                    details = json.loads(analysis.analysis_details)
                                                    if 'analysis_flags' in details and details['analysis_flags']:
                                                        with st.expander("🔍 Technical Details"):
                                                            for flag in details['analysis_flags'][:3]:  # Show first 3 flags
                                                                st.write(f"• {flag}")
                                                except:
                                                    pass
                                            
                                            st.markdown("---")
                    else:
                        st.info(f"No events found for {selected_vendor.name}")
        
        else:
            st.warning("⚠️ No vendors found. Create a vendor first.")
        
        # Add new vendor section
        st.subheader("➕ Add New Vendor")
        
        with st.form("add_vendor_form"):
            new_vendor_name = st.text_input("Vendor Name:")
            submitted = st.form_submit_button("Create Vendor")
            
            if submitted and new_vendor_name:
                try:
                    # Check if vendor exists
                    existing = VendorOperations.get_vendor_by_name(db, new_vendor_name)
                    if existing:
                        st.error(f"❌ Vendor '{new_vendor_name}' already exists!")
                    else:
                        vendor = VendorOperations.create_vendor(db, new_vendor_name)
                        st.success(f"✅ Created vendor: {vendor.name}")
                        st.rerun()  # Refresh the page
                except Exception as e:
                    st.error(f"❌ Error creating vendor: {e}")
    
    finally:
        db.close()


def event_submission_page():
    """Event submission page."""
    st.header("📋 Submit New Event")
    
    # Check if vendor is selected
    if 'selected_vendor_id' not in st.session_state:
        st.warning("⚠️ Please select a vendor first from the Vendor Management page.")
        return
    
    vendor_name = st.session_state.get('selected_vendor_name', 'Unknown')
    st.info(f"🏢 Submitting event for: **{vendor_name}**")
    
    # Event submission form
    with st.form("event_submission_form"):
        st.subheader("📝 Event Details")
        
        event_name = st.text_input("Event Name:", placeholder="e.g., Summer Music Festival 2024")
        event_date = st.date_input("Event Date:", value=date.today())
        event_notes = st.text_area("Notes (Optional):", placeholder="Additional event details...")
        
        st.subheader("📷 Upload Images")
        uploaded_files = st.file_uploader(
            "Choose images:",
            type=['jpg', 'jpeg', 'png', 'bmp', 'tiff'],
            accept_multiple_files=True,
            help="Upload multiple images from the event"
        )
        
        submitted = st.form_submit_button("🚀 Submit Event", type="primary")
        
        if submitted:
            if not event_name:
                st.error("❌ Please provide an event name.")
                return
                
            if not uploaded_files:
                st.error("❌ Please upload at least one image.")
                return
            
            # Process the submission
            process_event_submission(
                st.session_state.selected_vendor_id,
                event_name,
                event_date,
                event_notes,
                uploaded_files
            )


def process_event_submission(vendor_id: int, event_name: str, event_date: date, 
                           event_notes: str, uploaded_files):
    """Process the event submission with images."""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Create the event
        status_text.text("Creating event...")
        progress_bar.progress(10)
        
        event = EventOperations.create_event(
            db, vendor_id, event_name, event_date, event_notes
        )
        
        # Process uploaded images
        status_text.text("Processing uploaded images...")
        progress_bar.progress(30)
        
        file_handler = StreamlitFileHandler()
        upload_results = file_handler.process_multiple_uploads(uploaded_files)
        
        successful_uploads = 0
        total_files = len(upload_results)
        
        # Save images to database and calculate hashes
        for i, result in enumerate(upload_results):
            progress = 30 + (40 * (i + 1) / total_files)
            progress_bar.progress(int(progress))
            
            if result['status'] == 'success':
                # Create database record
                image_record = EventImageOperations.create_event_image(
                    db,
                    event.id,
                    result['original_name'],
                    result['file_path'],
                    result['file_size']
                )
                
                # Calculate and store hashes
                try:
                    process_new_image(image_record.id, result['file_path'])
                    status_text.text(f"Processed: {result['original_name']}")
                except Exception as e:
                    st.warning(f"⚠️ Hash calculation failed for {result['original_name']}: {e}")
                
                successful_uploads += 1
            else:
                st.error(f"❌ Failed to upload {result['original_name']}: {result['error']}")
        
        # Start fraud analysis
        if successful_uploads > 0:
            status_text.text("Running fraud analysis...")
            progress_bar.progress(75)
            
            # Initialize fraud analyzer
            analyzer = FraudAnalyzer()
            
            try:
                # Run fraud analysis for the entire event
                analysis_results = analyzer.analyze_new_event_submission(event.id, db)
                
                # Update event status based on analysis
                if analysis_results:
                    # Check for high-risk results
                    high_risk_count = sum(1 for r in analysis_results if r.fraud_score >= 80)
                    moderate_risk_count = sum(1 for r in analysis_results if 60 <= r.fraud_score < 80)
                    
                    if high_risk_count > 0:
                        EventOperations.update_event_status(db, event.id, "flagged")
                        st.error(f"🚨 **HIGH RISK DETECTED!** {high_risk_count} image(s) flagged for potential fraud.")
                    elif moderate_risk_count > 0:
                        EventOperations.update_event_status(db, event.id, "reviewed")
                        st.warning(f"⚠️ **MODERATE RISK:** {moderate_risk_count} image(s) require manual review.")
                    else:
                        EventOperations.update_event_status(db, event.id, "analyzed")
                        st.success("✅ No fraud indicators detected.")
                else:
                    EventOperations.update_event_status(db, event.id, "analyzed")
                    st.info("ℹ️ No historical images to compare against.")
                    
            except Exception as e:
                st.warning(f"⚠️ Fraud analysis encountered an error: {e}")
                EventOperations.update_event_status(db, event.id, "submitted")
            
        progress_bar.progress(100)
        status_text.text("Event submission completed!")
        
        # Show summary
        st.success(f"✅ **Event '{event_name}' submitted successfully!**")
        st.info(f"📊 **Summary:** {successful_uploads}/{total_files} images uploaded successfully")
        
        if successful_uploads < total_files:
            st.warning(f"⚠️ {total_files - successful_uploads} files failed to upload")
    
    except Exception as e:
        st.error(f"❌ Error processing event submission: {e}")
    
    finally:
        db.close()


def analysis_results_page():
    """Display fraud analysis results."""
    st.header("🔍 Fraud Analysis Results")
    
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        from database.operations import FraudAnalysisOperations
        
        # Get all analyses
        all_analyses = []
        try:
            # Get analyses with different risk levels
            high_risk = [a for a in FraudAnalysisOperations.get_high_risk_analyses(db) if a.fraud_score >= 80]
            moderate_risk = [a for a in FraudAnalysisOperations.get_high_risk_analyses(db) if 60 <= a.fraud_score < 80]
            
            all_analyses = high_risk + moderate_risk
        except Exception as e:
            st.error(f"Error loading analyses: {e}")
            all_analyses = []
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Analyses", len(all_analyses))
        
        with col2:
            high_risk_count = len([a for a in all_analyses if a.fraud_score >= 80])
            st.metric("High Risk", high_risk_count, delta=None if high_risk_count == 0 else f"+{high_risk_count}")
        
        with col3:
            moderate_risk_count = len([a for a in all_analyses if 60 <= a.fraud_score < 80])
            st.metric("Moderate Risk", moderate_risk_count)
        
        with col4:
            if all_analyses:
                avg_score = sum(a.fraud_score for a in all_analyses) / len(all_analyses)
                st.metric("Avg Risk Score", f"{avg_score:.1f}")
            else:
                st.metric("Avg Risk Score", "N/A")
        
        if all_analyses:
            st.markdown("---")
            
            # Filter controls
            st.subheader("🎛️ Filter Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Risk level filter
                risk_filter = st.selectbox(
                    "Risk Level",
                    ["All", "High Risk (80+)", "Moderate Risk (60-79)"],
                    index=0
                )
            
            with col2:
                # Vendor filter
                vendors = VendorOperations.get_all_vendors(db)
                vendor_names = ["All Vendors"] + [v.name for v in vendors]
                vendor_filter = st.selectbox("Vendor", vendor_names, index=0)
            
            # Apply filters
            filtered_analyses = all_analyses
            
            if risk_filter == "High Risk (80+)":
                filtered_analyses = [a for a in filtered_analyses if a.fraud_score >= 80]
            elif risk_filter == "Moderate Risk (60-79)":
                filtered_analyses = [a for a in filtered_analyses if 60 <= a.fraud_score < 80]
            
            if vendor_filter != "All Vendors":
                filtered_analyses = [a for a in filtered_analyses if a.new_image.event.vendor.name == vendor_filter]
            
            st.markdown("---")
            
            # Results display
            if filtered_analyses:
                st.subheader(f"📊 Analysis Results ({len(filtered_analyses)} matches)")
                
                # Sort by fraud score (highest first)
                filtered_analyses.sort(key=lambda x: x.fraud_score, reverse=True)
                
                for i, analysis in enumerate(filtered_analyses[:20]):  # Show top 20
                    # Determine severity styling
                    if analysis.fraud_score >= 80:
                        severity_color = "🚨"
                        severity_text = "HIGH RISK"
                        bg_color = "#ffebee"  # Light red
                    elif analysis.fraud_score >= 60:
                        severity_color = "⚠️"
                        severity_text = "MODERATE RISK"
                        bg_color = "#fff8e1"  # Light orange
                    else:
                        severity_color = "🟡"
                        severity_text = "LOW RISK"
                        bg_color = "#f3f4f6"  # Light gray
                    
                    with st.container():
                        # Create styled container
                        st.markdown(f"""
                        <div style="background-color: {bg_color}; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;">
                        """, unsafe_allow_html=True)
                        
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.write(f"**{severity_color} {severity_text}**")
                            st.write(f"**Score:** {analysis.fraud_score}/100")
                            st.write(f"**Similarity:** {analysis.similarity_score:.1f}%")
                            st.write(f"**Verdict:** {analysis.verdict}")
                        
                        with col2:
                            st.write("**Image Comparison:**")
                            new_image = analysis.new_image
                            comp_image = analysis.comparison_image
                            
                            st.write(f"🆕 `{new_image.filename}`")
                            st.write(f"   └ Event: {new_image.event.name}")
                            st.write(f"   └ Vendor: {new_image.event.vendor.name}")
                            
                            st.write(f"🔍 `{comp_image.filename}`")
                            st.write(f"   └ Event: {comp_image.event.name}")
                            st.write(f"   └ Vendor: {comp_image.event.vendor.name}")
                        
                        with col3:
                            st.write(f"**Analyzed:**")
                            st.write(f"{analysis.analyzed_at.strftime('%Y-%m-%d')}")
                            st.write(f"{analysis.analyzed_at.strftime('%H:%M:%S')}")
                        
                        # Show technical details
                        if analysis.analysis_details:
                            try:
                                import json
                                details = json.loads(analysis.analysis_details)
                                
                                if details.get('analysis_flags'):
                                    with st.expander(f"🔍 Technical Details ({len(details['analysis_flags'])} flags)"):
                                        for flag in details['analysis_flags']:
                                            st.write(f"• {flag}")
                                        
                                        # Show similarity breakdown if available
                                        if 'visual_similarities' in details:
                                            st.write("**Similarity Breakdown:**")
                                            sims = details['visual_similarities']
                                            for algo, score in sims.items():
                                                st.write(f"  - {algo}: {score:.1f}%")
                            except:
                                pass
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                if len(filtered_analyses) > 20:
                    st.info(f"Showing top 20 results out of {len(filtered_analyses)} total matches.")
            
            else:
                st.info("No results found matching the current filters.")
        
        else:
            st.success("✅ No fraud detections found - all submissions appear clean!")
    
    finally:
        db.close()


def main():
    """Main application function."""
    
    if not init_app():
        return
    
    st.title("🕵️ Vendor Event Fraud Detection System")
    st.markdown("---")
    
    # Navigation
    tab1, tab2, tab3 = st.tabs(["🏢 Vendor Management", "📋 Submit Event", "🔍 Analysis Results"])
    
    with tab1:
        vendor_management_page()
    
    with tab2:
        event_submission_page()
    
    with tab3:
        analysis_results_page()
    
    # Sidebar with system info
    with st.sidebar:
        st.header("ℹ️ System Info")
        
        # Storage stats
        from utils.file_handler import FileHandler
        stats = FileHandler.get_storage_stats()
        
        st.metric("📁 Total Files", stats['total_files'])
        st.metric("💾 Storage Used", f"{stats['total_size_mb']:.1f} MB")
        
        # Database stats
        db_gen = get_db()
        db = next(db_gen)
        try:
            vendor_count = len(VendorOperations.get_all_vendors(db))
            event_count = len(EventOperations.get_all_events(db))
            
            st.metric("🏢 Vendors", vendor_count)
            st.metric("📅 Events", event_count)
        finally:
            db.close()


if __name__ == "__main__":
    main()