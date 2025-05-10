import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os
import json
import sys

# Add the parent directory to the path to import from the app root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import load_tasks, load_logs, load_events, load_messages

# Page configuration
st.set_page_config(
    page_title="Dashboard - Circuit Breakers",
    page_icon="⚡",
    layout="wide"
)

# Check if user is authenticated
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("Please login to access this page.")
    st.stop()

# Initialize demo data
import data

# Page title
st.title("Team Dashboard")
st.write("Overview of team progress, upcoming events, and important metrics")

# Load data
tasks = load_tasks()
logs = load_logs()
events = load_events()
messages = load_messages()

# Calculate metrics
total_tasks = len(tasks)
completed_tasks = sum(1 for task in tasks if task.get("status") == "Completed")
in_progress_tasks = sum(1 for task in tasks if task.get("status") == "In Progress")
pending_tasks = total_tasks - completed_tasks - in_progress_tasks

# Filter upcoming events
now = datetime.now()
upcoming_events = [event for event in events if datetime.fromisoformat(event.get("start_time")) > now]
upcoming_events.sort(key=lambda x: datetime.fromisoformat(x.get("start_time")))

# Create metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Total Tasks", value=total_tasks)

with col2:
    completion_percentage = 0 if total_tasks == 0 else round((completed_tasks / total_tasks) * 100)
    st.metric(label="Task Completion", value=f"{completion_percentage}%")

with col3:
    days_to_next_event = None
    event_name = "No events scheduled"
    
    if upcoming_events:
        next_event = upcoming_events[0]
        next_event_date = datetime.fromisoformat(next_event.get("start_time"))
        days_to_next_event = (next_event_date - now).days
        event_name = next_event.get("title")
    
    st.metric(label=f"Next Event: {event_name}", value=f"{days_to_next_event} days" if days_to_next_event is not None else "N/A")

with col4:
    recent_logs = len([log for log in logs if datetime.fromisoformat(log.get("date")) > (now - timedelta(days=7))])
    st.metric(label="Weekly Build Log Entries", value=recent_logs)

# Create main dashboard layout
left_col, right_col = st.columns([2, 1])

with left_col:
    # Task Progress Chart
    st.subheader("Task Progress")
    
    if total_tasks > 0:
        # Create data for pie chart
        task_status = {
            "Status": ["Completed", "In Progress", "Pending"],
            "Count": [completed_tasks, in_progress_tasks, pending_tasks]
        }
        
        df_status = pd.DataFrame(task_status)
        
        # Set colors for each status
        colors = {"Completed": "#28a745", "In Progress": "#ffc107", "Pending": "#6c757d"}
        
        # Create pie chart
        fig = px.pie(
            df_status, 
            names="Status", 
            values="Count",
            color="Status",
            color_discrete_map=colors,
            title="Task Status Distribution"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No tasks available. Create tasks in the Project Management section.")
    
    # Recent Build Log Entries
    st.subheader("Recent Build Log Entries")
    
    if logs:
        # Sort logs by date (newest first)
        sorted_logs = sorted(logs, key=lambda x: datetime.fromisoformat(x.get("date")), reverse=True)
        recent_logs = sorted_logs[:3]  # Get 3 most recent logs
        
        for i, log in enumerate(recent_logs):
            log_date = datetime.fromisoformat(log.get("date"))
            formatted_date = log_date.strftime("%m/%d/%Y")
            
            with st.expander(f"{log.get('title')} - {formatted_date}"):
                st.write(f"**Category:** {log.get('category')}")
                st.write(f"**Author:** {log.get('author')}")
                st.write(log.get('description'))
    else:
        st.info("No build logs available. Add entries in the Build Logbook section.")

with right_col:
    # Upcoming Events
    st.subheader("Upcoming Events")
    
    if upcoming_events:
        for i, event in enumerate(upcoming_events[:5]):  # Show next 5 events
            event_start = datetime.fromisoformat(event.get("start_time"))
            formatted_date = event_start.strftime("%a, %b %d, %Y")
            formatted_time = event_start.strftime("%I:%M %p")
            
            # Different colors for different event types
            event_colors = {
                "Meeting": "#17a2b8",
                "Competition": "#dc3545",
                "Outreach": "#28a745",
                "Testing": "#fd7e14",
                "Workshop": "#6f42c1"
            }
            
            event_color = event_colors.get(event.get("category"), "#6c757d")
            
            st.markdown(
                f"""
                <div style="border-left: 4px solid {event_color}; padding-left: 10px; margin-bottom: 15px;">
                    <strong>{event.get('title')}</strong><br>
                    {formatted_date} at {formatted_time}<br>
                    <small>Location: {event.get('location')}</small>
                </div>
                """, 
                unsafe_allow_html=True
            )
    else:
        st.info("No upcoming events scheduled. Add events in the Team Calendar section.")
    
    # Recent Team Announcements
    st.subheader("Team Announcements")
    
    # Filter announcements
    announcements = [msg for msg in messages if msg.get("category") == "Announcement"]
    
    if announcements:
        # Sort by timestamp (newest first)
        sorted_announcements = sorted(announcements, key=lambda x: datetime.fromisoformat(x.get("timestamp")), reverse=True)
        
        for i, announcement in enumerate(sorted_announcements[:3]):  # Show 3 most recent
            announcement_date = datetime.fromisoformat(announcement.get("timestamp"))
            formatted_date = announcement_date.strftime("%m/%d/%Y")
            
            with st.expander(f"{announcement.get('title')} - {formatted_date}"):
                st.write(f"**Posted by:** {announcement.get('author')}")
                st.write(announcement.get('content'))
    else:
        st.info("No announcements available. Post messages in the Team Communication section.")

# Activity Feed at the bottom
st.markdown("---")
st.subheader("Recent Team Activity")

# Combine logs, tasks and messages for activity feed
activities = []

# Add log entries
for log in logs:
    activities.append({
        "type": "Log Entry",
        "description": f"Added build log: {log.get('title')}",
        "user": log.get('author'),
        "timestamp": log.get('date')
    })

# Add tasks with status changes
for task in tasks:
    if task.get("status") == "Completed":
        activities.append({
            "type": "Task",
            "description": f"Completed task: {task.get('title')}",
            "user": task.get('assigned_to'),
            "timestamp": datetime.now().isoformat()  # This would normally come from task history
        })
    elif task.get("status") == "In Progress":
        activities.append({
            "type": "Task",
            "description": f"Started task: {task.get('title')}",
            "user": task.get('assigned_to'),
            "timestamp": task.get('created_at')
        })

# Add messages
for message in messages:
    activities.append({
        "type": "Message",
        "description": f"Posted: {message.get('title', 'Response')}",
        "user": message.get('author'),
        "timestamp": message.get('timestamp')
    })

# Sort activities by timestamp (newest first)
activities.sort(key=lambda x: datetime.fromisoformat(x.get("timestamp")), reverse=True)

# Display activities
if activities:
    activity_data = {
        "Date": [],
        "User": [],
        "Activity": [],
        "Type": []
    }
    
    for activity in activities[:10]:  # Show 10 most recent activities
        activity_date = datetime.fromisoformat(activity.get("timestamp"))
        formatted_date = activity_date.strftime("%m/%d/%Y %I:%M %p")
        
        activity_data["Date"].append(formatted_date)
        activity_data["User"].append(activity.get("user"))
        activity_data["Activity"].append(activity.get("description"))
        activity_data["Type"].append(activity.get("type"))
    
    activity_df = pd.DataFrame(activity_data)
    st.dataframe(activity_df, use_container_width=True)
else:
    st.info("No recent team activity to display.")

st.markdown("---")
st.caption("Circuit Breakers Team Hub - Dashboard")
