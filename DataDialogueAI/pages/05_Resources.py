import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime, timedelta
import base64
from io import BytesIO

# Add the parent directory to the path to import from the app root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import load_resources, save_resources, check_role_access, generate_id

# Page configuration
st.set_page_config(
    page_title="Resources - Circuit Breakers",
    page_icon="📚",
    layout="wide"
)

# Check if user is authenticated
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("Please login to access this page.")
    st.stop()

# Page title
st.title("Resources & Documents")
st.write("Centralized storage for team files, documentation, and reference materials")

# Define resource categories
RESOURCE_CATEGORIES = ["Competition", "Engineering", "Design", "Electrical", "Administrative", "Outreach", "Safety", "Training", "Other"]
FILE_TYPES = ["PDF", "DOC", "DOCX", "XLS", "XLSX", "PPT", "PPTX", "TXT", "CSV", "ZIP", "Other"]

# Initialize session state for resource form
if 'show_resource_form' not in st.session_state:
    st.session_state.show_resource_form = False
if 'editing_resource' not in st.session_state:
    st.session_state.editing_resource = None
if 'resource_search' not in st.session_state:
    st.session_state.resource_search = ""

# Load resources
resources = load_resources()

# Function to toggle resource form visibility
def toggle_resource_form():
    st.session_state.show_resource_form = not st.session_state.show_resource_form
    st.session_state.editing_resource = None

# Function to edit an existing resource
def edit_resource(resource_id):
    st.session_state.editing_resource = resource_id
    st.session_state.show_resource_form = True

# Function to delete a resource
def delete_resource(resource_id):
    global resources
    resources = [resource for resource in resources if resource['id'] != resource_id]
    save_resources(resources)
    st.success("Resource deleted successfully!")
    st.rerun()

# Create top action buttons
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("Add New Resource 📄"):
        toggle_resource_form()

with col3:
    st.session_state.resource_search = st.text_input("Search resources...", value=st.session_state.resource_search)

# Create tabs
tab1, tab2 = st.tabs(["Resource Library", "Recent Uploads"])

with tab1:
    # Filter resources based on search term
    filtered_resources = resources
    if st.session_state.resource_search:
        search_term = st.session_state.resource_search.lower()
        filtered_resources = [
            resource for resource in resources 
            if (search_term in resource.get("title", "").lower() or 
                search_term in resource.get("description", "").lower() or 
                search_term in resource.get("category", "").lower() or
                search_term in resource.get("tags", []))
        ]
    
    # Add filtering options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_category = st.multiselect("Filter by Category", ["All"] + RESOURCE_CATEGORIES, default=["All"])
    
    with col2:
        filter_type = st.multiselect("Filter by File Type", ["All"] + FILE_TYPES, default=["All"])
    
    with col3:
        sort_options = ["Newest First", "Oldest First", "Title (A-Z)", "Category"]
        sort_by = st.selectbox("Sort by", sort_options)
    
    # Apply filters
    # Category filter
    if not ("All" in filter_category or len(filter_category) == 0):
        filtered_resources = [resource for resource in filtered_resources if resource.get("category", "Other") in filter_category]
    
    # File type filter
    if not ("All" in filter_type or len(filter_type) == 0):
        filtered_resources = [resource for resource in filtered_resources if resource.get("file_type", "Other") in filter_type]
    
    # Apply sorting
    if sort_by == "Newest First":
        filtered_resources.sort(key=lambda x: datetime.fromisoformat(x.get("upload_date")), reverse=True)
    elif sort_by == "Oldest First":
        filtered_resources.sort(key=lambda x: datetime.fromisoformat(x.get("upload_date")))
    elif sort_by == "Title (A-Z)":
        filtered_resources.sort(key=lambda x: x.get("title", "").lower())
    elif sort_by == "Category":
        filtered_resources.sort(key=lambda x: x.get("category", "Other"))
    
    # Display resources in a grid layout
    if filtered_resources:
        # Create a dataframe for display
        resource_data = []
        for resource in filtered_resources:
            upload_date = datetime.fromisoformat(resource.get("upload_date"))
            formatted_date = upload_date.strftime("%m/%d/%Y")
            
            resource_data.append({
                "ID": resource["id"],
                "Title": resource["title"],
                "Category": resource.get("category", "Other"),
                "File Type": resource.get("file_type", "Other"),
                "Uploaded By": resource.get("uploaded_by", "Unknown"),
                "Upload Date": formatted_date,
                "File Size": resource.get("file_size", "Unknown")
            })
        
        # Display in a grid
        num_cols = 3
        num_resources = len(filtered_resources)
        
        for i in range(0, num_resources, num_cols):
            cols = st.columns(num_cols)
            for j in range(num_cols):
                idx = i + j
                if idx < num_resources:
                    resource = filtered_resources[idx]
                    with cols[j]:
                        # Determine icon based on file type
                        file_type = resource.get("file_type", "Other")
                        icon = "📄"  # Default
                        if file_type == "PDF":
                            icon = "📕"
                        elif file_type in ["DOC", "DOCX"]:
                            icon = "📘"
                        elif file_type in ["XLS", "XLSX", "CSV"]:
                            icon = "📊"
                        elif file_type in ["PPT", "PPTX"]:
                            icon = "📑"
                        elif file_type == "ZIP":
                            icon = "🗜️"
                        
                        # Create card
                        with st.container():
                            st.markdown(
                                f"""
                                <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; height: 150px; overflow: hidden;">
                                    <h3 style="margin-top: 0;">{icon} {resource.get('title')}</h3>
                                    <p style="font-size: 0.8em; color: gray;">
                                        Category: {resource.get('category', 'Other')}<br/>
                                        Type: {resource.get('file_type', 'Other')}<br/>
                                        Size: {resource.get('file_size', 'Unknown')}<br/>
                                        Uploaded: {datetime.fromisoformat(resource.get('upload_date')).strftime('%m/%d/%Y')}
                                    </p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            
                            # Add view/download button
                            if st.button("View Details", key=f"view_{resource['id']}"):
                                st.session_state.selected_resource = resource["id"]
                                st.rerun()
        
        # Display full details if a resource is selected
        if 'selected_resource' in st.session_state:
            selected = next((r for r in resources if r["id"] == st.session_state.selected_resource), None)
            
            if selected:
                st.markdown("---")
                st.subheader(f"{selected.get('title')}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Category:** {selected.get('category', 'Other')}")
                    st.markdown(f"**File Type:** {selected.get('file_type', 'Other')}")
                    st.markdown(f"**File Size:** {selected.get('file_size', 'Unknown')}")
                    
                with col2:
                    st.markdown(f"**Uploaded By:** {selected.get('uploaded_by', 'Unknown')}")
                    upload_date = datetime.fromisoformat(selected.get('upload_date'))
                    st.markdown(f"**Upload Date:** {upload_date.strftime('%m/%d/%Y')}")
                    
                    # Add tags if available
                    if selected.get('tags'):
                        tags = ', '.join(selected.get('tags', []))
                        st.markdown(f"**Tags:** {tags}")
                
                st.markdown("### Description")
                st.markdown(selected.get('description', 'No description provided.'))
                
                # Add actions
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # This would typically download the file in a real application
                    st.button("Download File")
                
                # Only show edit/delete if admin/lead or the uploader
                if st.session_state.role in ['admin', 'lead'] or selected.get('uploaded_by') == st.session_state.user:
                    with col2:
                        if st.button("Edit Resource"):
                            edit_resource(selected["id"])
                    
                    with col3:
                        if st.button("Delete Resource"):
                            delete_resource(selected["id"])
                
                # Close detail view
                if st.button("Close"):
                    del st.session_state.selected_resource
                    st.rerun()
    else:
        st.info("No resources found matching your filters. Try adjusting your search criteria or upload new resources.")

with tab2:
    st.subheader("Recent Uploads")
    
    # Get recent uploads (last 30 days)
    now = datetime.now()
    recent_resources = [
        resource for resource in resources 
        if datetime.fromisoformat(resource.get("upload_date")) > (now - timedelta(days=30))
    ]
    
    # Sort by upload date (newest first)
    recent_resources.sort(key=lambda x: datetime.fromisoformat(x.get("upload_date")), reverse=True)
    
    if recent_resources:
        # Create a table for recent uploads
        recent_data = []
        
        for resource in recent_resources:
            upload_date = datetime.fromisoformat(resource.get("upload_date"))
            days_ago = (now - upload_date).days
            
            if days_ago == 0:
                time_str = "Today"
            elif days_ago == 1:
                time_str = "Yesterday"
            else:
                time_str = f"{days_ago} days ago"
            
            recent_data.append({
                "Title": resource["title"],
                "Category": resource.get("category", "Other"),
                "File Type": resource.get("file_type", "Other"),
                "Uploaded By": resource.get("uploaded_by", "Unknown"),
                "When": time_str,
                "ID": resource["id"]
            })
        
        # Create DataFrame
        recent_df = pd.DataFrame(recent_data)
        
        # Display as table
        st.dataframe(recent_df.drop(columns=["ID"]), use_container_width=True)
        
        # Option to view details
        selected_recent = st.selectbox(
            "Select a resource to view details", 
            recent_df["ID"].tolist(),
            format_func=lambda x: next((r["title"] for r in recent_resources if r["id"] == x), x)
        )
        
        if st.button("View Selected Resource"):
            st.session_state.selected_resource = selected_recent
            st.rerun()
    else:
        st.info("No resources have been uploaded in the last 30 days.")

# Resource upload/edit form
if st.session_state.show_resource_form:
    st.markdown("---")
    
    # Determine if we're editing or creating a new resource
    editing = st.session_state.editing_resource is not None
    
    if editing:
        resource_to_edit = next((resource for resource in resources if resource["id"] == st.session_state.editing_resource), None)
        st.subheader(f"Edit Resource: {resource_to_edit['title']}")
    else:
        st.subheader("Add New Resource")
    
    # Create form
    with st.form("resource_form"):
        # Pre-fill values if editing
        if editing:
            title_value = resource_to_edit["title"]
            description_value = resource_to_edit.get("description", "")
            category_index = RESOURCE_CATEGORIES.index(resource_to_edit.get("category")) if resource_to_edit.get("category") in RESOURCE_CATEGORIES else -1
            file_type_index = FILE_TYPES.index(resource_to_edit.get("file_type")) if resource_to_edit.get("file_type") in FILE_TYPES else -1
            file_size_value = resource_to_edit.get("file_size", "")
            tags_value = ", ".join(resource_to_edit.get("tags", []))
        else:
            title_value = ""
            description_value = ""
            category_index = -1  # No default category
            file_type_index = -1  # No default file type
            file_size_value = ""
            tags_value = ""
        
        # Form fields
        resource_title = st.text_input("Resource Title*", value=title_value)
        resource_description = st.text_area("Description", value=description_value, height=100)
        
        col1, col2 = st.columns(2)
        
        with col1:
            resource_category = st.selectbox("Category", RESOURCE_CATEGORIES, index=category_index if category_index >= 0 else 0)
            resource_tags = st.text_input("Tags (comma separated)", value=tags_value, help="Example: rules, engine, safety")
        
        with col2:
            resource_file_type = st.selectbox("File Type", FILE_TYPES, index=file_type_index if file_type_index >= 0 else 0)
            resource_file_size = st.text_input("File Size", value=file_size_value, help="Example: 2.5 MB")
        
        # File upload (in a real app this would actually upload a file)
        if not editing:
            uploaded_file = st.file_uploader("Upload File", type=["pdf", "doc", "docx", "xls", "xlsx", "csv", "ppt", "pptx", "txt", "zip"])
        
        # Submit buttons
        col1, col2 = st.columns(2)
        
        with col1:
            submit_button = st.form_submit_button("Save Resource")
        
        with col2:
            cancel_button = st.form_submit_button("Cancel")
        
        if cancel_button:
            st.session_state.show_resource_form = False
            st.session_state.editing_resource = None
            st.rerun()
        
        if submit_button:
            # Validate required fields
            if not resource_title:
                st.error("Resource title is required!")
            # In a real app, we'd also validate that a file is uploaded if creating a new resource
            else:
                # Process tags
                tags_list = [tag.strip() for tag in resource_tags.split(",") if tag.strip()]
                
                if editing:
                    # Update existing resource
                    for resource in resources:
                        if resource["id"] == st.session_state.editing_resource:
                            resource["title"] = resource_title
                            resource["description"] = resource_description
                            resource["category"] = resource_category
                            resource["file_type"] = resource_file_type
                            resource["file_size"] = resource_file_size
                            resource["tags"] = tags_list
                            break
                    
                    success_message = "Resource updated successfully!"
                else:
                    # Create new resource
                    # In a real app, we'd get file size and type from the uploaded file
                    file_size = resource_file_size or "1.2 MB"  # Placeholder
                    file_type = resource_file_type
                    
                    new_resource = {
                        "id": generate_id(),
                        "title": resource_title,
                        "description": resource_description,
                        "category": resource_category,
                        "uploaded_by": st.session_state.user,
                        "upload_date": datetime.now().isoformat(),
                        "file_type": file_type,
                        "file_size": file_size,
                        "tags": tags_list
                    }
                    
                    resources.append(new_resource)
                    success_message = "Resource uploaded successfully!"
                
                # Save resources to file
                save_resources(resources)
                
                # Reset form
                st.session_state.show_resource_form = False
                st.session_state.editing_resource = None
                
                st.success(success_message)
                st.rerun()

# At the bottom, show popular resource categories
st.markdown("---")
st.subheader("Resource Categories")

# Count resources by category
category_counts = {}
for category in RESOURCE_CATEGORIES:
    category_counts[category] = len([r for r in resources if r.get("category") == category])

# Display categories in a grid
num_cols = 3
cols = st.columns(num_cols)

for i, (category, count) in enumerate(category_counts.items()):
    with cols[i % num_cols]:
        st.markdown(
            f"""
            <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-bottom: 10px; text-align: center;">
                <h4>{category}</h4>
                <p>{count} resources</p>
            </div>
            """,
            unsafe_allow_html=True
        )

st.caption("Circuit Breakers Team Hub - Resources & Documents")
