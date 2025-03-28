import streamlit as st
from process_data import process_data_pipeline, batch_validate_emails
import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="No-Show Appointment Data Processor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with updated colors and hover fixes
st.markdown("""
    <style>
    /* Global styles */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 20px;
        font-family: 'Segoe UI', sans-serif;
    }
    
    /* Title */
    h1 {
        color: #1a3c34;
        font-size: 2.5em;
        font-weight: 700;
        text-align: center;
        margin-bottom: 20px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Subtitle */
    .stMarkdown p {
        color: #4a5e6d;
        font-size: 1.1em;
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* Sidebar */
    .sidebar .sidebar-content {
        background-color: #1F1D1D;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        padding: 20px;
        margin: 10px;
    }
    .sidebar h2 {
        color: #ffffff;
        font-size: 1.5em;
        font-weight: 600;
    }
    .sidebar p {
        color: #d1d5db;
        font-size: 1em;
        line-height: 1.5;
    }
    
    /* File uploader card */
    .stFileUploader {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 2px dashed #e2e8f0;
        transition: all 0.3s ease;
    }
    .stFileUploader:hover {
        border-color: #50699c;
        box-shadow: 0 6px 18px rgba(0,0,0,0.1);
    }
    
    /* Process Data Button */
    .stButton>button {
        background: linear-gradient(90deg, #50699c 0%, #3e557d 100%);
        color: white !important;  /* Force white font */
        border: none;
        border-radius: 25px;
        padding: 12px 30px;
        font-size: 1.1em;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 10px rgba(80, 105, 156, 0.3);
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #3e557d 0%, #50699c 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(80, 105, 156, 0.4);
        color: white !important;  /* Keep font white on hover */
    }
    
    /* Spinner (Loading Animation) */
    .stSpinner > div > div {
        border-color: #50699c transparent #50699c transparent !important;
        border-width: 4px;
        animation: spin 1s linear infinite;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Progress bar */
    .stProgress .st-bo {
        background: linear-gradient(90deg, #50699c 0%, #3e557d 100%);
        border-radius: 10px;
    }
    
    /* Status messages */
    .stAlert {
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* Columns */
    .stColumn {
        padding: 10px;
    }
    
    /* Download Results Button */
    .stDownloadButton>button {
        background: linear-gradient(90deg, #50699c 0%, #3e557d 100%);
        color: white !important;  /* Force white font */
        border-radius: 25px;
        padding: 10px 25px;
        font-size: 1em;
        transition: all 0.3s ease;
        box-shadow: 0 4px 10px rgba(80, 105, 156, 0.3);
    }
    .stDownloadButton>button:hover {
        background: linear-gradient(90deg, #3e557d 0%, #50699c 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(80, 105, 156, 0.4);
        color: white !important;  /* Keep font white on hover */
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar with logo at the top
with st.sidebar:
    st.image("evenflow_ai_logo.jpeg", use_container_width=True)  # Adjust path as needed
    st.header("Instructions")
    st.write("""
    1. Upload the four required Excel files below.
    2. Click 'Process Data' to analyze and generate target lists.
    3. Download the results once processing is complete.
    """)
    st.subheader("Status")
    status_placeholder = st.empty()

# Main content
st.title("No-Show Appointment Data Processor")
st.write("Daily Target List for 'No Show' Outbound Campaign.")

# File uploaders with modern layout
col1, col2 = st.columns(2)
with col1:
    no_shows_file = st.file_uploader("No Shows File", type=["xlsx"], help="Upload the list of no-shows.")
    planned_next_file = st.file_uploader("Planned Next File", type=["xlsx"], help="Upload planned appointments for the next 10 days.")
with col2:
    prior_appointments_file = st.file_uploader("Prior Appointments File", type=["xlsx"], help="Upload prior 10 days appointments.")
    prior_repairs_file = st.file_uploader("Prior Repairs File", type=["xlsx"], help="Upload prior 10 days repair orders.")

# Process button
if st.button("Process Data"):
    if all([no_shows_file, planned_next_file, prior_appointments_file, prior_repairs_file]):
        status_placeholder.info("Processing started...")
        
        # Read uploaded files into DataFrames
        with st.spinner("Reading files..."):
            no_shows_df = pd.read_excel(no_shows_file)
            planned_next_df = pd.read_excel(planned_next_file)
            prior_appointments_df = pd.read_excel(prior_appointments_file)
            prior_repairs_df = pd.read_excel(prior_repairs_file)
        
        # Progress bar for email validation
        progress_bar = st.progress(0)
        def update_progress(current, total):
            progress = min(int((current / total) * 100), 100)
            progress_bar.progress(progress)
            status_placeholder.info(f"Validating emails: {current}/{total}")

        # Wrap batch_validate_emails for progress tracking
        original_batch_validate = batch_validate_emails
        def wrapped_batch_validate(emails, progress_callback=None):
            callback = progress_callback if progress_callback else update_progress
            return original_batch_validate(emails, callback)
        import process_data
        process_data.batch_validate_emails = wrapped_batch_validate
        
        # Process data
        try:
            output_buffer, output_filename = process_data_pipeline(no_shows_df, planned_next_df, prior_appointments_df, prior_repairs_df)
            status_placeholder.success("Processing complete! Download your results below.")
            
            # Download button (file is only saved when downloaded)
            st.download_button(
                label="Download Results",
                data=output_buffer,
                file_name=output_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            status_placeholder.error(f"Error: {str(e)}")
            logger.error(f"Pipeline error: {e}")
    else:
        status_placeholder.error("Please upload all four files before processing.")

# Footer
st.markdown("""
    <style>
    .footer {
        text-align: center;
        padding: 10px;
        background-color: #f5f7fa;
        border-top: 1px solid #e2e8f0;
        font-size: 0.9em;
        color: #6b7280;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="footer">
        A EvenFlow AI Tool - All rights reserved 2025
    </div>
""", unsafe_allow_html=True)