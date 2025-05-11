import streamlit as st
import pandas as pd
import os
import io
import sys
import json
from datetime import datetime

# Add the parent directory to the path to import from the app root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import check_role_access, generate_id

# Page configuration
st.set_page_config(
    page_title="File Management - Circuit Breakers",
    page_icon="📁",
    layout="wide"
)

# Check if user is authenticated
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("Please login to access this page.")
    st.stop()

# Page title
st.title("File Management")
st.write("Upload, manage, and process files for the Circuit Breakers team")

# Define the uploads directory
UPLOADS_DIR = "breaker/data/uploads"  # Modified line
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

# Create subdirectories for different file types
EXCEL_DIR = os.path.join(UPLOADS_DIR, "excel")
DOCS_DIR = os.path.join(UPLOADS_DIR, "documents")
IMAGES_DIR = os.path.join(UPLOADS_DIR, "images")
MISC_DIR = os.path.join(UPLOADS_DIR, "misc")

for directory in [EXCEL_DIR, DOCS_DIR, IMAGES_DIR, MISC_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Function to load file metadata
def load_file_metadata():
    metadata_file = os.path.join(UPLOADS_DIR, "file_metadata.json") # Modified line
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

# Function to save file metadata
def save_file_metadata(metadata):
    metadata_file = os.path.join(UPLOADS_DIR, "file_metadata.json") # Modified line
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=4)

# Function to determine the file type and appropriate directory
def get_file_type_and_dir(filename):
    extension = os.path.splitext(filename)[1].lower()
    
    # Excel files
    if extension in ['.xlsx', '.xls', '.xlsm', '.csv']:
        return "Excel/CSV", EXCEL_DIR
    
    # Document files
    elif extension in ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.md']:
        return "Document", DOCS_DIR
    
    # Image files
    elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']:
        return "Image", IMAGES_DIR
    
    # Miscellaneous files
    else:
        return "Other", MISC_DIR

# Create tabs for different file operations
tab1, tab2, tab3 = st.tabs(["Upload Files", "View & Manage Files", "Excel Viewer"])

with tab1:
    st.header("Upload New Files")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose files to upload", 
        accept_multiple_files=True,
        type=None  # Accept all file types
    )
    
    if uploaded_files:
        # Metadata for tracking uploads
        file_metadata = load_file_metadata()
        
        success_count = 0
        
        for idx, uploaded_file in enumerate(uploaded_files): # Added enumerate
            try:
                # Get file type and destination directory
                file_type, dest_dir = get_file_type_and_dir(uploaded_file.name)
                
                # Generate a unique filename to avoid overwrites
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                base_name, extension = os.path.splitext(uploaded_file.name)
                unique_filename = f"{base_name}_{timestamp}{extension}"
                file_path = os.path.join(dest_dir, unique_filename)
                
                # Save the file
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Add to metadata
                if file_type not in file_metadata:
                    file_metadata[file_type] = []
                
                file_metadata[file_type].append({
                    "id": generate_id(),
                    "original_name": uploaded_file.name,
                    "stored_name": unique_filename,
                    "file_path": file_path,
                    "file_type": file_type,
                    "size_kb": round(uploaded_file.size / 1024, 2),
                    "upload_date": datetime.now().isoformat(),
                    "uploaded_by": st.session_state.user
                })
                
                success_count += 1
                
            except Exception as e:
                st.error(f"Error uploading {uploaded_file.name}: {str(e)}")
        
        # Save updated metadata
        save_file_metadata(file_metadata)
        
        if success_count > 0:
            st.success(f"Successfully uploaded {success_count} file(s)!")

with tab2:
    st.header("View & Manage Files")
    
    # Load file metadata
    file_metadata = load_file_metadata()
    
    if not file_metadata:
        st.info("No files have been uploaded yet. Use the 'Upload Files' tab to upload files.")
    else:
        # Create expandable sections for each file type
        for file_type, files in file_metadata.items():
            if files:
                with st.expander(f"{file_type} Files ({len(files)})", expanded=True):
                    # Create a table of files
                    file_data = []
                    for file in files:
                        # Convert upload date to a more readable format
                        upload_date = datetime.fromisoformat(file['upload_date'])
                        formatted_date = upload_date.strftime("%Y-%m-%d %H:%M:%S")
                        
                        file_data.append({
                            "Filename": file['original_name'],
                            "Size (KB)": file['size_kb'],
                            "Uploaded By": file['uploaded_by'],
                            "Upload Date": formatted_date,
                            "Path": file['file_path'],
                            "ID": file['id']
                        })
                    
                    if file_data:
                        df = pd.DataFrame(file_data)
                        
                        # Display the dataframe with a download button for each file
                        for i, row in df.iterrows():
                            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                            
                            with col1:
                                st.write(f"**{row['Filename']}**")
                                st.write(f"Size: {row['Size (KB)']} KB | Uploaded: {row['Upload Date']} | By: {row['Uploaded By']}")
                            
                            with col2:
                                # Only show preview for certain file types
                                if file_type == "Excel/CSV":
                                    # Make the key unique by including the file ID
                                    if st.button(f"Preview", key=f"preview_{row['ID']}"):
                                        st.session_state.selected_excel = row['Path']
                                        st.session_state.active_tab = "Excel Viewer"
                                        st.rerun()
                            
                            with col3:
                                # Create a download button
                                if os.path.exists(row['Path']):
                                    with open(row['Path'], 'rb') as file:
                                        st.download_button(
                                            label="Download",
                                            data=file,
                                            file_name=row['Filename'],
                                            key=f"download_{row['ID']}"
                                        )
                            
                            with col4:
                                # Delete button
                                if check_role_access(['admin', 'lead']):
                                    if st.button("Delete", key=f"delete_{row['ID']}"):
                                        # Get the file_type and file index to delete
                                        file_id_to_delete = row['ID']
                                        file_to_delete = next((file for file in file_metadata[file_type] if file['id'] == file_id_to_delete), None)
                                        
                                        if file_to_delete:
                                            # Remove the file from the filesystem
                                            if os.path.exists(file_to_delete['file_path']):
                                                os.remove(file_to_delete['file_path'])
                                            
                                            # Remove from metadata
                                            file_metadata[file_type] = [f for f in file_metadata[file_type] if f['id'] != file_id_to_delete]
                                            save_file_metadata(file_metadata)
                                            
                                            st.success(f"Deleted file: {file_to_delete['original_name']}")
                                            st.rerun()
                            
                            st.markdown("---")


with tab3:
    st.header("Excel File Viewer")
    
    # Initialize session state for selected Excel file
    if 'selected_excel' not in st.session_state:
        st.session_state.selected_excel = None
    
    # Show Excel file selector
    file_metadata = load_file_metadata()
    excel_files = []
    
    if "Excel/CSV" in file_metadata:
        excel_files = file_metadata["Excel/CSV"]
    
    if not excel_files:
        st.info("No Excel or CSV files have been uploaded yet.")
    else:
        # Create a selectbox with all available Excel files
        excel_options = [f"{file['original_name']} (Uploaded: {datetime.fromisoformat(file['upload_date']).strftime('%Y-%m-%d')})" for file in excel_files]
        excel_option_to_file = {option: file for option, file in zip(excel_options, excel_files)}
        
        selected_option = st.selectbox(
            "Select an Excel/CSV file to view:",
            options=[""] + excel_options,
            key="excel_file_selector" # Added a key here
        )
        
        if selected_option:
            selected_file = excel_option_to_file[selected_option]
            file_path = selected_file['file_path']
            
            if os.path.exists(file_path):
                # Determine if it's an Excel or CSV file
                _, extension = os.path.splitext(file_path)
                
                try:
                    if extension.lower() in ['.xlsx', '.xls', '.xlsm']:
                        # Read the Excel file with pandas
                        excel_file = pd.ExcelFile(file_path)
                        sheet_names = excel_file.sheet_names
                        
                        # Allow user to select a sheet
                        selected_sheet = st.selectbox("Select a sheet:", sheet_names, key=f"sheet_selector_{selected_file['id']}") # Added key
                        
                        # Read the selected sheet
                        df = pd.read_excel(file_path, sheet_name=selected_sheet)
                        
                    elif extension.lower() == '.csv':
                        # Read the CSV file with pandas
                        df = pd.read_csv(file_path)
                    else:
                        st.error(f"Unsupported file extension: {extension}")
                        st.stop()
                    
                    # Display file info
                    st.write(f"**File:** {selected_file['original_name']}")
                    st.write(f"**Shape:** {df.shape[0]} rows, {df.shape[1]} columns")
                    
                    # Show dataframe
                    st.dataframe(df)
                    
                    # Add some data analysis options
                    with st.expander("Data Analysis Options"):
                        # Show data types
                        st.write("**Data Types:**")
                        st.write(df.dtypes)
                        
                        # Summary statistics for numeric columns
                        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                        if numeric_cols:
                            st.write("**Summary Statistics:**")
                            st.write(df[numeric_cols].describe())
                        
                        # Download as CSV option
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download as CSV",
                            data=csv,
                            file_name=f"{os.path.splitext(selected_file['original_name'])[0]}_processed.csv",
                            mime="text/csv",
                            key=f"download_csv_{selected_file['id']}" # Added key
                        )
                
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
            else:
                st.error(f"File not found: {file_path}")

# Footer
st.caption("Circuit Breakers Team Hub - File Management")

