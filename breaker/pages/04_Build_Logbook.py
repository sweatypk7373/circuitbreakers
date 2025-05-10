import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime, timedelta
import base64
from io import BytesIO
from PIL import Image
import plotly.express as px

# Add the parent directory to the path to import from the app root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import load_logs, save_logs, generate_id

# Page configuration
st.set_page_config(
    page_title="Build Logbook - Circuit Breakers",
    page_icon="📔",
    layout="wide"
)

# Check if user is authenticated
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("Please login to access this page.")
    st.stop()

# Page title
st.title("Build Logbook")
st.write("Document build progress, issues, and achievements")

# Define log categories
LOG_CATEGORIES = ["Engineering", "Electrical", "Design", "Testing", "Outreach", "Competition", "Other"]

# Initialize session state for log form
if 'show_log_form' not in st.session_state:
    st.session_state.show_log_form = False
if 'editing_log' not in st.session_state:
    st.session_state.editing_log = None
if 'log_search' not in st.session_state:
    st.session_state.log_search = ""

# Load logs
logs = load_logs()

# Function to toggle log form visibility
def toggle_log_form():
    st.session_state.show_log_form = not st.session_state.show_log_form
    st.session_state.editing_log = None

# Function to edit an existing log
def edit_log(log_id):
    st.session_state.editing_log = log_id
    st.session_state.show_log_form = True

# Function to delete a log
def delete_log(log_id):
    global logs
    logs = [log for log in logs if log['id'] != log_id]
    save_logs(logs)
    st.success("Log entry deleted successfully!")
    st.rerun()

# Create top action buttons
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    if st.button("Add New Log Entry ✏️"):
        toggle_log_form()

with col3:
    st.session_state.log_search = st.text_input("Search logs...", value=st.session_state.log_search)

# Create tabs
tab1, tab2 = st.tabs(["Log Entries", "Analytics"])

with tab1:
    # Filter logs based on search term
    filtered_logs = logs
    if st.session_state.log_search:
        search_term = st.session_state.log_search.lower()
        filtered_logs = [
            log for log in logs 
            if (search_term in log.get("title", "").lower() or 
                search_term in log.get("description", "").lower() or 
                search_term in log.get("author", "").lower() or 
                search_term in log.get("category", "").lower())
        ]
    
    # Add sorting and filtering options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sort_options = ["Newest First", "Oldest First", "Category", "Author"]
        sort_by = st.selectbox("Sort by", sort_options)
    
    with col2:
        filter_category = st.multiselect("Filter by Category", ["All"] + LOG_CATEGORIES, default=["All"])
    
    with col3:
        date_range = st.radio("Date Range", ["All Time", "Past Week", "Past Month", "Custom"], horizontal=True)
        
        if date_range == "Custom":
            custom_col1, custom_col2 = st.columns(2)
            with custom_col1:
                start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
            with custom_col2:
                end_date = st.date_input("End Date", value=datetime.now())
    
    # Apply filters
    # Category filter
    if not ("All" in filter_category or len(filter_category) == 0):
        filtered_logs = [log for log in filtered_logs if log.get("category", "Other") in filter_category]
    
    # Date filter
    now = datetime.now()
    if date_range == "Past Week":
        filtered_logs = [
            log for log in filtered_logs 
            if datetime.fromisoformat(log.get("date")) > (now - timedelta(days=7))
        ]
    elif date_range == "Past Month":
        filtered_logs = [
            log for log in filtered_logs 
            if datetime.fromisoformat(log.get("date")) > (now - timedelta(days=30))
        ]
    elif date_range == "Custom":
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())
        filtered_logs = [
            log for log in filtered_logs 
            if start_datetime <= datetime.fromisoformat(log.get("date")) <= end_datetime
        ]
    
    # Apply sorting
    if sort_by == "Newest First":
        filtered_logs.sort(key=lambda x: datetime.fromisoformat(x.get("date")), reverse=True)
    elif sort_by == "Oldest First":
        filtered_logs.sort(key=lambda x: datetime.fromisoformat(x.get("date")))
    elif sort_by == "Category":
        filtered_logs.sort(key=lambda x: x.get("category", "Other"))
    elif sort_by == "Author":
        filtered_logs.sort(key=lambda x: x.get("author", ""))
    
    # Display logs
    if filtered_logs:
        for log in filtered_logs:
            log_date = datetime.fromisoformat(log.get("date"))
            formatted_date = log_date.strftime("%A, %B %d, %Y %I:%M %p")
            
            with st.expander(f"{log.get('title')} - {formatted_date}"):
                # Display log content
                st.markdown(f"**Category:** {log.get('category', 'Uncategorized')}")
                st.markdown(f"**Author:** {log.get('author', 'Unknown')}")
                st.markdown(f"**Date:** {formatted_date}")
                st.markdown("---")
                st.markdown(log.get("description", "No description provided."))
                
                # If there's an image description, display it
                if log.get("image_description"):
                    st.info(f"Image description: {log.get('image_description')}")
                
                # Show edit/delete buttons for author or admin
                if st.session_state.role in ['admin', 'lead'] or log.get("author") == st.session_state.user:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Edit Entry", key=f"edit_{log['id']}"):
                            edit_log(log["id"])
                    with col2:
                        if st.button("Delete Entry", key=f"delete_{log['id']}"):
                            delete_log(log["id"])
    else:
        st.info("No log entries found. Add some using the 'Add New Log Entry' button.")

# Log entry form (add/edit)
if st.session_state.show_log_form:
    st.markdown("---")
    
    # Determine if we're editing or creating a new log
    editing = st.session_state.editing_log is not None
    
    if editing:
        log_to_edit = next((log for log in logs if log["id"] == st.session_state.editing_log), None)
        st.subheader(f"Edit Log Entry: {log_to_edit['title']}")
    else:
        st.subheader("Add New Log Entry")
    
    # Create form
    with st.form("log_form"):
        # Pre-fill values if editing
        if editing:
            title_value = log_to_edit["title"]
            description_value = log_to_edit.get("description", "")
            category_index = LOG_CATEGORIES.index(log_to_edit.get("category")) if log_to_edit.get("category") in LOG_CATEGORIES else -1
            log_date_value = datetime.fromisoformat(log_to_edit.get("date"))
            image_desc_value = log_to_edit.get("image_description", "")
        else:
            title_value = ""
            description_value = ""
            category_index = -1  # No default category
            log_date_value = datetime.now()
            image_desc_value = ""
        
        # Form fields
        log_title = st.text_input("Log Title*", value=title_value)
        log_category = st.selectbox("Category", LOG_CATEGORIES, index=category_index if category_index >= 0 else 0)
        
        col1, col2 = st.columns(2)
        
        with col1:
            log_date = st.date_input("Date", value=log_date_value.date())
        
        with col2:
            log_time = st.time_input("Time", value=log_date_value.time())
        
        log_description = st.text_area("Description*", value=description_value, height=200)
        
        # Image description field
        st.markdown("### Image Description")
        st.markdown("Describe any images that would accompany this log entry.")
        image_description = st.text_area("Image Description", value=image_desc_value)
        
        # Submit buttons
        col1, col2 = st.columns(2)
        
        with col1:
            submit_button = st.form_submit_button("Save Log Entry")
        
        with col2:
            cancel_button = st.form_submit_button("Cancel")
        
        if cancel_button:
            st.session_state.show_log_form = False
            st.session_state.editing_log = None
            st.rerun()
        
        if submit_button:
            # Validate required fields
            if not log_title or not log_description:
                st.error("Log title and description are required!")
            else:
                # Process form submission
                log_datetime = datetime.combine(log_date, log_time)
                
                if editing:
                    # Update existing log
                    for log in logs:
                        if log["id"] == st.session_state.editing_log:
                            log["title"] = log_title
                            log["description"] = log_description
                            log["category"] = log_category
                            log["date"] = log_datetime.isoformat()
                            log["image_description"] = image_description
                            break
                    
                    success_message = "Log entry updated successfully!"
                else:
                    # Create new log
                    new_log = {
                        "id": generate_id(),
                        "title": log_title,
                        "description": log_description,
                        "category": log_category,
                        "author": st.session_state.user,
                        "date": log_datetime.isoformat(),
                        "image_description": image_description
                    }
                    
                    logs.append(new_log)
                    success_message = "Log entry created successfully!"
                
                # Save logs to file
                save_logs(logs)
                
                # Reset form
                st.session_state.show_log_form = False
                st.session_state.editing_log = None
                
                st.success(success_message)
                st.rerun()

with tab2:
    st.subheader("Build Log Analytics")
    
    if logs:
        # Calculate log statistics
        total_logs = len(logs)
        
        # Get date range of logs
        log_dates = [datetime.fromisoformat(log.get("date")) for log in logs]
        earliest_date = min(log_dates)
        latest_date = max(log_dates)
        date_range = (latest_date - earliest_date).days + 1
        
        # Calculate logs per category
        category_counts = {}
        for category in LOG_CATEGORIES:
            category_counts[category] = len([log for log in logs if log.get("category") == category])
        
        # Calculate logs by author
        author_counts = {}
        for log in logs:
            author = log.get("author", "Unknown")
            if author in author_counts:
                author_counts[author] += 1
            else:
                author_counts[author] = 1
        
        # Calculate logs over time
        logs_by_date = {}
        for log in logs:
            log_date = datetime.fromisoformat(log.get("date")).date()
            date_str = log_date.isoformat()
            if date_str in logs_by_date:
                logs_by_date[date_str] += 1
            else:
                logs_by_date[date_str] = 1
        
        # Create metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Log Entries", total_logs)
        
        with col2:
            logs_last_week = len([log for log in logs if datetime.fromisoformat(log.get("date")) > (datetime.now() - timedelta(days=7))])
            st.metric("Entries Last 7 Days", logs_last_week)
        
        with col3:
            if date_range > 0:
                avg_logs_per_week = round((total_logs / date_range) * 7, 1)
            else:
                avg_logs_per_week = total_logs
            st.metric("Avg. Entries Per Week", avg_logs_per_week)
        
        with col4:
            most_common_category = max(category_counts.items(), key=lambda x: x[1])[0]
            st.metric("Most Active Category", most_common_category)
        
        # Create visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            # Category distribution
            st.subheader("Log Distribution by Category")
            
            category_data = pd.DataFrame({
                "Category": list(category_counts.keys()),
                "Count": list(category_counts.values())
            })
            
            fig = px.pie(
                category_data,
                values="Count",
                names="Category",
                title="Log Distribution by Category",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Author distribution
            st.subheader("Log Distribution by Author")
            
            author_data = pd.DataFrame({
                "Author": list(author_counts.keys()),
                "Count": list(author_counts.values())
            })
            
            # Sort by count descending
            author_data = author_data.sort_values("Count", ascending=False)
            
            fig = px.bar(
                author_data,
                x="Author",
                y="Count",
                title="Log Entries by Author",
                color="Count",
                color_continuous_scale=px.colors.sequential.Viridis
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Activity timeline
        st.subheader("Build Activity Timeline")
        
        # Create date range for all days
        if date_range > 0:
            date_range_list = [earliest_date.date() + timedelta(days=x) for x in range(date_range)]
            date_range_strs = [date.isoformat() for date in date_range_list]
            
            # Create counts for each date (filling in zeros for dates with no logs)
            timeline_counts = [logs_by_date.get(date_str, 0) for date_str in date_range_strs]
            
            # Create formatted date strings for display
            display_dates = [date.strftime("%b %d") for date in date_range_list]
            
            # Create timeline data
            timeline_data = pd.DataFrame({
                "Date": display_dates,
                "Log Entries": timeline_counts
            })
            
            # Only include up to the last 60 days if the range is larger
            if len(timeline_data) > 60:
                timeline_data = timeline_data.iloc[-60:]
            
            fig = px.line(
                timeline_data,
                x="Date",
                y="Log Entries",
                title="Build Log Activity Over Time",
                markers=True
            )
            
            # Improve layout
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Number of Log Entries",
                xaxis=dict(
                    tickmode="auto",
                    nticks=20,
                    tickangle=45
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Category log trends over time
        st.subheader("Category Trends Over Time")
        
        # Group logs by month and category
        logs_by_month_category = {}
        for log in logs:
            log_date = datetime.fromisoformat(log.get("date"))
            month_year = log_date.strftime("%b %Y")
            category = log.get("category", "Other")
            
            key = (month_year, category)
            if key in logs_by_month_category:
                logs_by_month_category[key] += 1
            else:
                logs_by_month_category[key] = 1
        
        # Create a list of all month-years
        all_months = sorted(list(set([k[0] for k in logs_by_month_category.keys()])), key=lambda x: datetime.strptime(x, "%b %Y"))
        
        # Create a dataframe for visualization
        category_trend_data = []
        for month in all_months:
            for category in LOG_CATEGORIES:
                count = logs_by_month_category.get((month, category), 0)
                category_trend_data.append({
                    "Month": month,
                    "Category": category,
                    "Count": count
                })
        
        category_trend_df = pd.DataFrame(category_trend_data)
        
        # Create stacked bar chart
        fig = px.bar(
            category_trend_df,
            x="Month",
            y="Count",
            color="Category",
            title="Log Entries by Category Over Time",
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        
        # Improve layout
        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Number of Log Entries",
            xaxis=dict(
                tickangle=45
            ),
            barmode="stack"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Export options
        st.subheader("Export Build Log Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export to CSV"):
                # Create dataframe of logs
                export_data = []
                for log in logs:
                    log_date = datetime.fromisoformat(log.get("date"))
                    formatted_date = log_date.strftime("%Y-%m-%d %H:%M:%S")
                    
                    export_data.append({
                        "ID": log.get("id", ""),
                        "Title": log.get("title", ""),
                        "Category": log.get("category", ""),
                        "Author": log.get("author", ""),
                        "Date": formatted_date,
                        "Description": log.get("description", "").replace("\n", " "),
                        "Image Description": log.get("image_description", "").replace("\n", " ")
                    })
                
                export_df = pd.DataFrame(export_data)
                
                # Create download link
                csv = export_df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="build_logs.csv">Download CSV file</a>'
                st.markdown(href, unsafe_allow_html=True)
        
        with col2:
            if st.button("Generate Report Summary"):
                # Create summary
                st.markdown("### Build Log Summary Report")
                st.markdown(f"**Report Date:** {datetime.now().strftime('%B %d, %Y')}")
                st.markdown(f"**Total Entries:** {total_logs}")
                st.markdown(f"**Date Range:** {earliest_date.strftime('%B %d, %Y')} to {latest_date.strftime('%B %d, %Y')}")
                st.markdown(f"**Most Active Category:** {most_common_category}")
                
                # Most active team members
                st.markdown("#### Most Active Team Members")
                active_members = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)
                for author, count in active_members[:3]:
                    st.markdown(f"- **{author}:** {count} entries")
                
                # Recent entries
                st.markdown("#### Recent Log Entries")
                recent_logs = sorted(logs, key=lambda x: datetime.fromisoformat(x.get("date")), reverse=True)[:5]
                for log in recent_logs:
                    log_date = datetime.fromisoformat(log.get("date"))
                    formatted_date = log_date.strftime("%B %d, %Y")
                    st.markdown(f"- **{log.get('title')}** - {formatted_date} ({log.get('category')})")
    else:
        st.info("No log entries available for analysis. Add some using the 'Add New Log Entry' button.")

st.markdown("---")
st.caption("Circuit Breakers Team Hub - Build Logbook")
