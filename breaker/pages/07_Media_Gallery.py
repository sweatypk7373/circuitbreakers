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
from util import load_media, save_media, check_role_access, generate_id

# Page configuration
st.set_page_config(
    page_title="Media Gallery - Circuit Breakers",
    page_icon="📸",
    layout="wide"
)

# Check if user is authenticated
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("Please login to access this page.")
    st.stop()

# Page title
st.title("Media Gallery")
st.write("Archive of team photos, videos, and media assets")

# Define media categories
MEDIA_CATEGORIES = ["Team Photos", "Build Process", "Competition", "Testing", "Design", "Outreach", "Promotional",
                    "Other"]
MEDIA_TYPES = ["Photo", "Video", "Document", "Presentation", "Other"]

# Initialize session state for media form
if 'show_media_form' not in st.session_state:
    st.session_state.show_media_form = False
if 'editing_media' not in st.session_state:
    st.session_state.editing_media = None
if 'media_search' not in st.session_state:
    st.session_state.media_search = ""
if 'selected_media' not in st.session_state:
    st.session_state.selected_media = None

# Load media items
media_items = load_media()


# Function to toggle media form visibility
def toggle_media_form():
    st.session_state.show_media_form = not st.session_state.show_media_form
    st.session_state.editing_media = None


# Function to edit an existing media item
def edit_media(media_id):
    st.session_state.editing_media = media_id
    st.session_state.show_media_form = True


# Function to delete a media item
def delete_media(media_id):
    global media_items

    # Find the media item first to get file path
    media_to_delete = next((item for item in media_items if item['id'] == media_id), None)

    if media_to_delete:
        # Delete the actual file if it exists
        file_path = media_to_delete.get('file_path')
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                st.info(f"File {os.path.basename(file_path)} deleted from disk.")
            except Exception as e:
                st.warning(f"Could not delete file from disk: {str(e)}")

    # Remove from the list
    media_items = [item for item in media_items if item['id'] != media_id]
    save_media(media_items)

    # Reset selected media if we're deleting it
    if st.session_state.selected_media == media_id:
        st.session_state.selected_media = None

    st.success("Media item deleted successfully!")
    st.rerun()


# Create top action buttons
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("Add New Media 📷"):
        toggle_media_form()

with col3:
    st.session_state.media_search = st.text_input("Search media...", value=st.session_state.media_search)

# Create tabs
tab1, tab2, tab3 = st.tabs(["Gallery View", "List View", "Albums"])

with tab1:
    # Filter media based on search term
    filtered_media = media_items
    if st.session_state.media_search:
        search_term = st.session_state.media_search.lower()
        filtered_media = [
            item for item in media_items
            if (search_term in item.get("title", "").lower() or
                search_term in item.get("description", "").lower() or
                search_term in item.get("category", "").lower() or
                any(search_term in tag.lower() for tag in item.get("tags", [])))
        ]

    # Add filtering options
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        filter_category = st.multiselect("Filter by Category", ["All"] + MEDIA_CATEGORIES, default=["All"])

    with filter_col2:
        filter_type = st.multiselect("Filter by Media Type", ["All"] + MEDIA_TYPES, default=["All"])

    with filter_col3:
        sort_options = ["Newest First", "Oldest First", "Title (A-Z)", "Category"]
        sort_by = st.selectbox("Sort by", sort_options)

    # Apply filters
    # Category filter
    if not ("All" in filter_category or len(filter_category) == 0):
        filtered_media = [item for item in filtered_media if item.get("category", "Other") in filter_category]

    # Media type filter
    if not ("All" in filter_type or len(filter_type) == 0):
        filtered_media = [item for item in filtered_media if item.get("media_type", "Other") in filter_type]

    # Apply sorting
    if sort_by == "Newest First":
        filtered_media.sort(key=lambda x: datetime.fromisoformat(x.get("upload_date")), reverse=True)
    elif sort_by == "Oldest First":
        filtered_media.sort(key=lambda x: datetime.fromisoformat(x.get("upload_date")))
    elif sort_by == "Title (A-Z)":
        filtered_media.sort(key=lambda x: x.get("title", "").lower())
    elif sort_by == "Category":
        filtered_media.sort(key=lambda x: x.get("category", "Other"))

    # Display media in a grid layout
    if filtered_media:
        # Create a grid of media items
        num_cols = 3
        num_items = len(filtered_media)

        for i in range(0, num_items, num_cols):
            cols = st.columns(num_cols)
            for j in range(num_cols):
                idx = i + j
                if idx < num_items:
                    item = filtered_media[idx]
                    with cols[j]:
                        # Determine icon based on media type
                        media_type = item.get("media_type", "Photo")
                        icon = "📷"  # Default photo icon
                        if media_type == "Video":
                            icon = "🎬"
                        elif media_type == "Document":
                            icon = "📄"
                        elif media_type == "Presentation":
                            icon = "📊"

                        # Create media card
                        with st.container():
                            # Check if we have a file and it exists
                            file_path = item.get("file_path")
                            has_image = False

                            # Display card header
                            st.markdown(f"#### {icon} {item.get('title')}")

                            # Display actual image if it's a photo and file exists
                            if file_path and os.path.exists(file_path):
                                file_ext = os.path.splitext(file_path)[1].lower()
                                if media_type == "Photo" or file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                                    try:
                                        st.image(file_path, use_column_width=True)
                                        has_image = True
                                    except:
                                        has_image = False

                            # If no image could be displayed, show the icon
                            if not has_image:
                                st.markdown(
                                    f"""
                                    <div style="background-color: #f0f0f0; height: 150px; display: flex; align-items: center; justify-content: center; margin: 10px 0;">
                                        <span style="font-size: 48px;">{icon}</span>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )

                            # Display media info
                            st.markdown(f"{item.get('category', 'Uncategorized')} | {media_type}")

                            # Add button to view details
                            if st.button("View Details", key=f"view_{item['id']}"):
                                st.session_state.selected_media = item["id"]
                                st.rerun()

        # Display full details if an item is selected
        if st.session_state.selected_media:
            selected_item = next((item for item in filtered_media if item["id"] == st.session_state.selected_media),
                                 None)

            if selected_item:
                st.markdown("---")
                st.subheader(f"{selected_item.get('title')}")

                col1, col2 = st.columns(2)

                with col1:
                    # Display the actual media if possible
                    media_type = selected_item.get("media_type", "Photo")
                    file_path = selected_item.get("file_path")

                    # Check if we have a file and it exists
                    if file_path and os.path.exists(file_path):
                        file_ext = os.path.splitext(file_path)[1].lower()

                        # For images, display the actual image
                        if media_type == "Photo" or file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                            try:
                                st.image(file_path, caption=selected_item.get('title'), use_column_width=True)
                            except Exception as e:
                                st.error(f"Error displaying image: {str(e)}")
                                st.markdown(f"📷 **Photo:** {os.path.basename(file_path)}")

                        # For videos, offer a download link
                        elif media_type == "Video" or file_ext in ['.mp4', '.mov', '.avi']:
                            st.markdown(f"🎬 **Video file:** {os.path.basename(file_path)}")
                            st.info("Videos need to be downloaded to view. Use the Download button below.")

                        # For PDFs, display info
                        elif file_ext == '.pdf':
                            st.markdown(f"📕 **PDF file:** {os.path.basename(file_path)}")
                            st.info("PDF files need to be downloaded to view. Use the Download button below.")

                        # For other files, just show icon
                        else:
                            icon = "📄"  # Default document icon
                            if media_type == "Presentation" or file_ext in ['.ppt', '.pptx']:
                                icon = "📊"

                            st.markdown(
                                f"""
                                <div style="background-color: #f0f0f0; padding: 20px; text-align: center; border-radius: 5px;">
                                    <span style="font-size: 48px;">{icon}</span>
                                    <p>{os.path.basename(file_path)}</p>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                    else:
                        # No file or file doesn't exist, show placeholder
                        icon = "📷"  # Default photo icon
                        if media_type == "Video":
                            icon = "🎬"
                        elif media_type == "Document":
                            icon = "📄"
                        elif media_type == "Presentation":
                            icon = "📊"

                        st.markdown(
                            f"""
                            <div style="background-color: #f0f0f0; height: 300px; display: flex; align-items: center; justify-content: center; margin: 10px 0;">
                                <span style="font-size: 96px;">{icon}</span>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                with col2:
                    st.markdown(f"**Category:** {selected_item.get('category', 'Other')}")
                    st.markdown(f"**Media Type:** {selected_item.get('media_type', 'Photo')}")
                    st.markdown(f"**Uploaded By:** {selected_item.get('uploaded_by', 'Unknown')}")
                    upload_date = datetime.fromisoformat(selected_item.get('upload_date'))
                    st.markdown(f"**Upload Date:** {upload_date.strftime('%m/%d/%Y')}")

                    # Add tags if available
                    if selected_item.get('tags'):
                        tags = ', '.join(selected_item.get('tags', []))
                        st.markdown(f"**Tags:** {tags}")

                    st.markdown("### Description")
                    st.markdown(selected_item.get('description', 'No description provided.'))

                    # Add actions
                    action_col1, action_col2, action_col3 = st.columns(3)

                    with action_col1:
                        # Provide download button if file exists
                        if selected_item.get('file_path') and os.path.exists(selected_item.get('file_path')):
                            with open(selected_item.get('file_path'), 'rb') as file:
                                st.download_button(
                                    label="Download Media",
                                    data=file,
                                    file_name=os.path.basename(selected_item.get('file_path')),
                                    mime="application/octet-stream"
                                )
                        else:
                            st.button("Download Media (Not Available)")

                    # Only show edit/delete if admin/lead or the uploader
                    if st.session_state.role in ['admin', 'lead'] or selected_item.get(
                            'uploaded_by') == st.session_state.user:
                        with action_col2:
                            if st.button("Edit Media"):
                                edit_media(selected_item["id"])

                        with action_col3:
                            if st.button("Delete Media"):
                                delete_media(selected_item["id"])

                # Close detail view
                if st.button("Close"):
                    st.session_state.selected_media = None
                    st.rerun()
    else:
        st.info("No media items found matching your filters. Try adjusting your search criteria or upload new media.")

with tab2:
    # List view for media items
    st.subheader("Media List View")

    # Create the DataFrame for display
    if media_items:
        media_data = []
        for item in media_items:
            upload_date = datetime.fromisoformat(item.get("upload_date"))
            formatted_date = upload_date.strftime("%m/%d/%Y")

            media_data.append({
                "ID": item["id"],
                "Title": item["title"],
                "Category": item.get("category", "Other"),
                "Type": item.get("media_type", "Photo"),
                "Uploaded By": item.get("uploaded_by", "Unknown"),
                "Upload Date": formatted_date
            })

        media_df = pd.DataFrame(media_data)

        # Display as a table
        st.dataframe(media_df.drop(columns=["ID"]), use_container_width=True)

        # Option to view details
        selected_item_id = st.selectbox(
            "Select an item to view details",
            media_df["ID"].tolist(),
            format_func=lambda x: next((item["title"] for item in media_items if item["id"] == x), x)
        )

        if st.button("View Selected Media"):
            st.session_state.selected_media = selected_item_id
            st.rerun()
    else:
        st.info("No media items available. Add some using the 'Add New Media' button.")

with tab3:
    # Albums view (grouped by category)
    st.subheader("Media Albums")

    # Group media by category
    albums = {}
    for category in MEDIA_CATEGORIES:
        items = [item for item in media_items if item.get("category") == category]
        if items:
            albums[category] = items

    if albums:
        # Display album cards
        album_cols = st.columns(3)

        for i, (category, items) in enumerate(albums.items()):
            with album_cols[i % 3]:
                st.markdown(
                    f"""
                    <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin-bottom: 10px; text-align: center;">
                        <h3>{category}</h3>
                        <p>{len(items)} items</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.button(f"View Album", key=f"album_{category}"):
                    st.session_state.selected_album = category
                    st.rerun()

        # Display selected album
        if 'selected_album' in st.session_state:
            category = st.session_state.selected_album
            album_items = albums.get(category, [])

            st.markdown("---")
            st.subheader(f"Album: {category}")

            # Back button
            if st.button("← Back to Albums"):
                del st.session_state.selected_album
                st.rerun()

            # Display items in the album
            if album_items:
                # Create a grid of media items
                num_cols = 3
                num_items = len(album_items)

                for i in range(0, num_items, num_cols):
                    cols = st.columns(num_cols)
                    for j in range(num_cols):
                        idx = i + j
                        if idx < num_items:
                            item = album_items[idx]
                            with cols[j]:
                                # Determine icon based on media type
                                media_type = item.get("media_type", "Photo")
                                icon = "📷"  # Default photo icon
                                if media_type == "Video":
                                    icon = "🎬"
                                elif media_type == "Document":
                                    icon = "📄"
                                elif media_type == "Presentation":
                                    icon = "📊"

                                # Create media card
                                with st.container():
                                    # Check if we have a file and it exists
                                    file_path = item.get("file_path")
                                    has_image = False

                                    # Display card header
                                    st.markdown(f"#### {icon} {item.get('title')}")

                                    # Display actual image if it's a photo and file exists
                                    if file_path and os.path.exists(file_path):
                                        file_ext = os.path.splitext(file_path)[1].lower()
                                        if media_type == "Photo" or file_ext in ['.jpg', '.jpeg', '.png', '.gif']:
                                            try:
                                                st.image(file_path, use_columm_width=True)
                                                has_image = True
                                            except:
                                                has_image = False

                                    # If no image could be displayed, show the icon
                                    if not has_image:
                                        st.markdown(
                                            f"""
                                            <div style="background-color: #f0f0f0; height: 150px; display: flex; align-items: center; justify-content: center; margin: 10px 0;">
                                                <span style="font-size: 48px;">{icon}</span>
                                            </div>
                                            """,
                                            unsafe_allow_html=True
                                        )

                                    # Display media info
                                    st.markdown(f"{media_type}")

                                    # Add button to view details
                                    if st.button("View Details", key=f"album_view_{item['id']}"):
                                        st.session_state.selected_media = item["id"]
                                        st.rerun()
            else:
                st.info(f"No media items in the {category} album.")
    else:
        st.info("No media albums available. Add media items using the 'Add New Media' button.")

# Media upload/edit form
if st.session_state.show_media_form:
    st.markdown("---")

    # Determine if we're editing or creating a new media item
    editing = st.session_state.editing_media is not None
    media_to_edit = None

    if editing:
        media_to_edit = next((item for item in media_items if item["id"] == st.session_state.editing_media), None)
        if media_to_edit:
            st.subheader(f"Edit Media: {media_to_edit['title']}")
        else:
            st.error("Media item not found!")
            st.session_state.editing_media = None
            st.session_state.show_media_form = False
            st.rerun()
    else:
        st.subheader("Add New Media")

    # Create form
    with st.form("media_form"):
        # Pre-fill values if editing and media_to_edit exists
        if editing and media_to_edit:
            title_value = media_to_edit["title"]
            description_value = media_to_edit.get("description", "")
            category_index = MEDIA_CATEGORIES.index(media_to_edit.get("category")) if media_to_edit.get(
                "category") in MEDIA_CATEGORIES else -1
            media_type_index = MEDIA_TYPES.index(media_to_edit.get("media_type")) if media_to_edit.get(
                "media_type") in MEDIA_TYPES else -1
            tags_value = ", ".join(media_to_edit.get("tags", []))
        else:
            title_value = ""
            description_value = ""
            category_index = -1  # No default category
            media_type_index = 0  # Default to Photo
            tags_value = ""

        # Form fields
        media_title = st.text_input("Media Title*", value=title_value)
        media_description = st.text_area("Description", value=description_value, height=100)

        col1, col2 = st.columns(2)

        with col1:
            media_category = st.selectbox("Category", MEDIA_CATEGORIES,
                                          index=category_index if category_index >= 0 else 0)
            media_tags = st.text_input("Tags (comma separated)", value=tags_value,
                                       help="Example: competition, team, awards")

        with col2:
            media_type = st.selectbox("Media Type", MEDIA_TYPES, index=media_type_index if media_type_index >= 0 else 0)

        # File upload with proper state handling
        if not editing:
            uploaded_file = st.file_uploader("Upload Media", type=["jpg", "jpeg", "png", "mp4", "pdf", "ppt", "pptx"])
            if uploaded_file:
                st.session_state.uploaded_file = uploaded_file

        # Submit buttons
        col1, col2 = st.columns(2)

        with col1:
            submit_button = st.form_submit_button("Save Media")

        with col2:
            cancel_button = st.form_submit_button("Cancel")

        if cancel_button:
            st.session_state.show_media_form = False
            st.session_state.editing_media = None
            # Clear the uploaded file from session state
            if 'uploaded_file' in st.session_state:
                del st.session_state.uploaded_file
            st.rerun()

        if submit_button:
            # Validate required fields
            if not media_title:
                st.error("Media title is required!")
            # In a real app, we'd also validate that a file is uploaded if creating a new media item
            else:
                # Process tags
                tags_list = [tag.strip() for tag in media_tags.split(",") if tag.strip()]

                # Initialize success message variable
                success_message = ""

                if editing:
                    # Update existing media item
                    for item in media_items:
                        if item["id"] == st.session_state.editing_media:
                            item["title"] = media_title
                            item["description"] = media_description
                            item["category"] = media_category
                            item["media_type"] = media_type
                            item["tags"] = tags_list
                            break

                    success_message = "Media item updated successfully!"
                else:
                    # Get the uploaded file if it exists
                    uploaded_file = st.session_state.get('uploaded_file', None)

                    # Validate that a file is uploaded for new media
                    if uploaded_file is None:
                        st.error("Please upload a media file!")
                    else:
                        # Setup media uploads directory
                        MEDIA_DIR = "data/media_uploads"
                        if not os.path.exists(MEDIA_DIR):
                            os.makedirs(MEDIA_DIR)

                        # Generate a unique ID
                        media_id = generate_id()

                        # Process the uploaded file
                        file_path = None

                        # Get file extension and determine file type if needed
                        file_ext = os.path.splitext(uploaded_file.name)[1].lower()

                        # Create a unique filename to avoid overwrites
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        unique_filename = f"{media_id}_{timestamp}{file_ext}"
                        file_path = os.path.join(MEDIA_DIR, unique_filename)

                        # Save the uploaded file to disk
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        # Create the new media entry
                        new_media = {
                            "id": media_id,
                            "title": media_title,
                            "description": media_description,
                            "category": media_category,
                            "uploaded_by": st.session_state.user,
                            "upload_date": datetime.now().isoformat(),
                            "media_type": media_type,
                            "tags": tags_list,
                            "file_path": file_path
                        }

                        media_items.append(new_media)
                        success_message = "Media uploaded successfully!"

                # Save media items to file
                save_media(media_items)

                # Reset form
                st.session_state.show_media_form = False
                st.session_state.editing_media = None

                # Clear the uploaded file from session state if it exists
                if 'uploaded_file' in st.session_state:
                    del st.session_state.uploaded_file

                st.success(success_message)
                st.rerun()

# At the bottom, show media stats
st.markdown("---")
st.subheader("Media Statistics")

# Count media by type and category
if media_items:
    col1, col2, col3 = st.columns(3)

    with col1:
        # Count by media type
        type_counts = {}
        for media_type in MEDIA_TYPES:
            type_counts[media_type] = len([item for item in media_items if item.get("media_type") == media_type])

        st.markdown("### Media by Type")

        # Create a simple bar chart using markdown
        for media_type, count in type_counts.items():
            if count > 0:
                # Calculate percentage width (max 100%)
                max_count = max(type_counts.values())
                width_pct = int((count / max_count) * 100)

                st.markdown(
                    f"""
                    <div style="margin-bottom: 5px;">
                        <span style="display: inline-block; width: 100px;">{media_type}</span>
                        <div style="display: inline-block; width: {width_pct}%; background-color: #00B4D8; height: 20px;"></div>
                        <span style="margin-left: 5px;">{count}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    with col2:
        # Total media count
        total_items = len(media_items)

        # Recent uploads (last 30 days)
        now = datetime.now()
        recent_count = len([
            item for item in media_items
            if datetime.fromisoformat(item.get("upload_date")) > (now - timedelta(days=30))
        ])

        # Calculate percentage
        recent_pct = int((recent_count / total_items) * 100) if total_items > 0 else 0

        st.markdown("### Media Overview")
        st.markdown(f"**Total Media Items:** {total_items}")
        st.markdown(f"**Recently Added:** {recent_count} ({recent_pct}% in last 30 days)")

        # Top contributors
        contributors = {}
        for item in media_items:
            uploader = item.get("uploaded_by", "Unknown")
            if uploader in contributors:
                contributors[uploader] += 1
            else:
                contributors[uploader] = 1

        # Sort by count
        top_contributors = sorted(contributors.items(), key=lambda x: x[1], reverse=True)[:3]

        st.markdown("### Top Contributors")
        for contributor, count in top_contributors:
            st.markdown(f"- **{contributor}:** {count} items")

    with col3:
        # Media by category
        category_counts = {}
        for category in MEDIA_CATEGORIES:
            category_counts[category] = len([item for item in media_items if item.get("category") == category])

        # Filter out categories with 0 items
        category_counts = {k: v for k, v in category_counts.items() if v > 0}

        st.markdown("### Categories")
        for category, count in category_counts.items():
            st.markdown(f"- **{category}:** {count} items")

        # Export button
        if st.button("Export Media Inventory"):
            # Create DataFrame for export
            export_data = []
            for item in media_items:
                upload_date = datetime.fromisoformat(item.get("upload_date"))
                formatted_date = upload_date.strftime("%Y-%m-%d")

                export_data.append({
                    "Title": item.get("title", ""),
                    "Category": item.get("category", ""),
                    "Type": item.get("media_type", ""),
                    "Uploaded By": item.get("uploaded_by", ""),
                    "Date": formatted_date,
                    "Description": item.get("description", "").replace("\n", " "),
                    "Tags": ", ".join(item.get("tags", []))
                })

            export_df = pd.DataFrame(export_data)

            # Create download link
            csv = export_df.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="media_inventory.csv">Download CSV file</a>'
            st.markdown(href, unsafe_allow_html=True)
else:
    st.info("No media items available for statistics.")

st.caption("Circuit Breakers Team Hub - Media Gallery")
