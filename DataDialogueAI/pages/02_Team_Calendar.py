import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Add the parent directory to the path to import from the app root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import load_events, save_events, check_role_access

# Page configuration
st.set_page_config(
    page_title="Team Calendar - Circuit Breakers",
    page_icon="📅",
    layout="wide"
)

# Check if user is authenticated
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("Please login to access this page.")
    st.stop()

# Page title
st.title("Team Calendar")
st.write("Schedule and track team events, meetings, and competitions")

# Initialize session state for event form
if 'show_event_form' not in st.session_state:
    st.session_state.show_event_form = False
if 'editing_event' not in st.session_state:
    st.session_state.editing_event = None

# Define event categories and colors
EVENT_CATEGORIES = ["Meeting", "Competition", "Outreach", "Testing", "Workshop", "Other"]
EVENT_COLORS = {
    "Meeting": "#17a2b8",
    "Competition": "#dc3545",
    "Outreach": "#28a745", 
    "Testing": "#fd7e14",
    "Workshop": "#6f42c1",
    "Other": "#6c757d"
}

# Load events
events = load_events()

# Helper function to parse datetime strings
def parse_datetime(dt_str):
    return datetime.fromisoformat(dt_str)

# Function to toggle event form visibility
def toggle_event_form():
    st.session_state.show_event_form = not st.session_state.show_event_form
    st.session_state.editing_event = None

# Function to edit an existing event
def edit_event(event_id):
    st.session_state.editing_event = event_id
    st.session_state.show_event_form = True

# Function to delete an event
def delete_event(event_id):
    global events
    events = [event for event in events if event['id'] != event_id]
    save_events(events)
    st.success("Event deleted successfully!")
    st.rerun()

# Create tabs for different calendar views
tab1, tab2, tab3 = st.tabs(["Calendar View", "List View", "Add/Edit Event"])

with tab1:
    st.subheader("Calendar View")
    
    # Create month navigation
    if 'current_month' not in st.session_state:
        st.session_state.current_month = datetime.now().month
    if 'current_year' not in st.session_state:
        st.session_state.current_year = datetime.now().year
    
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        if st.button("← Previous Month"):
            if st.session_state.current_month == 1:
                st.session_state.current_month = 12
                st.session_state.current_year -= 1
            else:
                st.session_state.current_month -= 1
    
    with col2:
        st.subheader(f"{datetime(st.session_state.current_year, st.session_state.current_month, 1).strftime('%B %Y')}")
    
    with col3:
        if st.button("Next Month →"):
            if st.session_state.current_month == 12:
                st.session_state.current_month = 1
                st.session_state.current_year += 1
            else:
                st.session_state.current_month += 1
    
    # Create calendar view
    # Get first and last day of the current month
    first_day = datetime(st.session_state.current_year, st.session_state.current_month, 1)
    if st.session_state.current_month == 12:
        last_day = datetime(st.session_state.current_year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(st.session_state.current_year, st.session_state.current_month + 1, 1) - timedelta(days=1)
    
    # Get the day of the week for the first day (0 = Monday, 6 = Sunday)
    first_weekday = first_day.weekday()
    
    # Calculate how many weeks we need to display
    days_in_month = (last_day - first_day).days + 1
    weeks_needed = (first_weekday + days_in_month + 6) // 7
    
    # Create calendar grid
    days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    
    # Display days of the week header
    cols = st.columns(7)
    for i, col in enumerate(cols):
        with col:
            st.markdown(f"**{days_of_week[i]}**")
    
    # Filter events for current month
    month_events = [
        event for event in events 
        if parse_datetime(event['start_time']).month == st.session_state.current_month 
        and parse_datetime(event['start_time']).year == st.session_state.current_year
    ]
    
    # Group events by date
    events_by_date = {}
    for event in month_events:
        event_date = parse_datetime(event['start_time']).date()
        if event_date not in events_by_date:
            events_by_date[event_date] = []
        events_by_date[event_date].append(event)
    
    # Display calendar days
    day_counter = 1 - first_weekday
    for week in range(weeks_needed):
        cols = st.columns(7)
        for i, col in enumerate(cols):
            with col:
                if day_counter <= 0 or day_counter > days_in_month:
                    # Display empty cell for days outside current month
                    st.markdown("&nbsp;", unsafe_allow_html=True)
                else:
                    # Display day number
                    current_date = datetime(st.session_state.current_year, st.session_state.current_month, day_counter).date()
                    
                    # Highlight current day
                    if current_date == datetime.now().date():
                        st.markdown(f"**{day_counter}** 📌", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**{day_counter}**", unsafe_allow_html=True)
                    
                    # Display events for this day
                    if current_date in events_by_date:
                        for event in events_by_date[current_date]:
                            event_start = parse_datetime(event['start_time'])
                            event_category = event.get('category', 'Other')
                            event_color = EVENT_COLORS.get(event_category, "#6c757d")
                            
                            st.markdown(
                                f"""
                                <div style="background-color:{event_color}; padding:2px 5px; border-radius:3px; margin:2px 0; color:white; font-size:0.8em">
                                    {event_start.strftime('%H:%M')} {event['title']}
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )
                day_counter += 1

with tab2:
    st.subheader("Event List")
    
    # Create filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_category = st.selectbox("Filter by Category", ["All"] + EVENT_CATEGORIES)
    
    with col2:
        filter_options = ["All", "Upcoming", "Past", "Today"]
        filter_time = st.selectbox("Filter by Time", filter_options)
    
    with col3:
        days_to_show = st.number_input("Days to show", min_value=7, max_value=365, value=30, step=1)
    
    # Apply filters
    filtered_events = events.copy()
    
    if filter_category != "All":
        filtered_events = [event for event in filtered_events if event.get('category') == filter_category]
    
    now = datetime.now()
    if filter_time == "Upcoming":
        filtered_events = [event for event in filtered_events if parse_datetime(event['start_time']) > now]
    elif filter_time == "Past":
        filtered_events = [event for event in filtered_events if parse_datetime(event['start_time']) < now]
    elif filter_time == "Today":
        filtered_events = [
            event for event in filtered_events 
            if parse_datetime(event['start_time']).date() == now.date()
        ]
    
    # Further filter by days to show
    if filter_time == "Upcoming":
        future_date = now + timedelta(days=days_to_show)
        filtered_events = [
            event for event in filtered_events 
            if parse_datetime(event['start_time']) < future_date
        ]
    elif filter_time == "Past":
        past_date = now - timedelta(days=days_to_show)
        filtered_events = [
            event for event in filtered_events 
            if parse_datetime(event['start_time']) > past_date
        ]
    
    # Sort events by start time
    filtered_events.sort(key=lambda x: parse_datetime(x['start_time']))
    
    # Display events in a table or list
    if filtered_events:
        # Create dataframe for display
        event_data = []
        for event in filtered_events:
            event_start = parse_datetime(event['start_time'])
            event_end = parse_datetime(event['end_time'])
            
            event_data.append({
                "Date": event_start.strftime("%a, %b %d, %Y"),
                "Time": f"{event_start.strftime('%I:%M %p')} - {event_end.strftime('%I:%M %p')}",
                "Title": event['title'],
                "Location": event['location'],
                "Category": event.get('category', 'Other'),
                "ID": event['id']
            })
        
        event_df = pd.DataFrame(event_data)
        
        # Display each event as an expandable card
        for i, row in event_df.iterrows():
            event_id = row['ID']
            event = next((e for e in events if e['id'] == event_id), None)
            
            if event:
                event_category = event.get('category', 'Other')
                event_color = EVENT_COLORS.get(event_category, "#6c757d")
                
                expander_title = f"{row['Date']} | {row['Title']} ({row['Category']})"
                with st.expander(expander_title):
                    st.markdown(f"**Time:** {row['Time']}")
                    st.markdown(f"**Location:** {row['Location']}")
                    st.markdown(f"**Description:** {event['description']}")
                    st.markdown(f"**Organizer:** {event['organizer']}")
                    st.markdown(f"**Participants:** {', '.join(event['participants'])}")
                    
                    # Only admin and lead can edit/delete events
                    if st.session_state.role in ['admin', 'lead']:
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Edit Event", key=f"edit_{event_id}"):
                                edit_event(event_id)
                        with col2:
                            if st.button("Delete Event", key=f"delete_{event_id}"):
                                delete_event(event_id)
    else:
        st.info("No events found matching the selected filters.")

with tab3:
    st.subheader("Manage Events")
    
    # Only admin and lead can add events
    if not check_role_access(['admin', 'lead']):
        st.warning("You don't have permission to add or edit events. Contact an administrator.")
    else:
        if not st.session_state.show_event_form:
            st.button("Add New Event", on_click=toggle_event_form)
        
        if st.session_state.show_event_form:
            # Determine if we're editing or creating a new event
            editing = st.session_state.editing_event is not None
            
            if editing:
                event_to_edit = next((e for e in events if e['id'] == st.session_state.editing_event), None)
                form_title = "Edit Event"
                
                # Pre-fill the form with event data
                default_title = event_to_edit['title']
                default_description = event_to_edit['description']
                default_location = event_to_edit['location']
                default_category = event_to_edit.get('category', 'Other')
                default_start = parse_datetime(event_to_edit['start_time'])
                default_end = parse_datetime(event_to_edit['end_time'])
                default_organizer = event_to_edit['organizer']
                default_participants = ", ".join(event_to_edit['participants'])
            else:
                form_title = "Add New Event"
                
                # Default values for new event
                default_title = ""
                default_description = ""
                default_location = ""
                default_category = "Meeting"
                default_start = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                default_end = default_start + timedelta(hours=1)
                default_organizer = st.session_state.user
                default_participants = ""
            
            st.subheader(form_title)
            
            with st.form("event_form"):
                event_title = st.text_input("Event Title*", value=default_title)
                event_description = st.text_area("Description", value=default_description)
                event_location = st.text_input("Location*", value=default_location)
                event_category = st.selectbox("Category", EVENT_CATEGORIES, index=EVENT_CATEGORIES.index(default_category))
                
                col1, col2 = st.columns(2)
                with col1:
                    event_date = st.date_input("Date*", value=default_start.date())
                    event_start_time = st.time_input("Start Time*", value=default_start.time())
                with col2:
                    end_date = st.date_input("End Date*", value=default_end.date())
                    event_end_time = st.time_input("End Time*", value=default_end.time())
                
                event_organizer = st.text_input("Organizer*", value=default_organizer)
                event_participants = st.text_input("Participants (comma separated)", value=default_participants)
                
                col1, col2 = st.columns(2)
                with col1:
                    submit_button = st.form_submit_button("Save Event")
                with col2:
                    cancel_button = st.form_submit_button("Cancel")
                
                if cancel_button:
                    st.session_state.show_event_form = False
                    st.session_state.editing_event = None
                    st.rerun()
                
                if submit_button:
                    # Validate inputs
                    if not (event_title and event_location and event_organizer):
                        st.error("Please fill in all required fields marked with *")
                    else:
                        # Create datetime objects for start and end
                        event_start_datetime = datetime.combine(event_date, event_start_time)
                        event_end_datetime = datetime.combine(end_date, event_end_time)
                        
                        # Validate end time is after start time
                        if event_end_datetime <= event_start_datetime:
                            st.error("End time must be after start time")
                        else:
                            # Process participant list
                            participants_list = [p.strip() for p in event_participants.split(",") if p.strip()]
                            
                            if editing:
                                # Update existing event
                                for event in events:
                                    if event['id'] == st.session_state.editing_event:
                                        event['title'] = event_title
                                        event['description'] = event_description
                                        event['start_time'] = event_start_datetime.isoformat()
                                        event['end_time'] = event_end_datetime.isoformat()
                                        event['location'] = event_location
                                        event['organizer'] = event_organizer
                                        event['participants'] = participants_list
                                        event['category'] = event_category
                                        break
                                
                                success_message = "Event updated successfully!"
                            else:
                                # Create new event
                                new_event = {
                                    'id': f"event{len(events) + 1:03d}",
                                    'title': event_title,
                                    'description': event_description,
                                    'start_time': event_start_datetime.isoformat(),
                                    'end_time': event_end_datetime.isoformat(),
                                    'location': event_location,
                                    'organizer': event_organizer,
                                    'participants': participants_list,
                                    'category': event_category
                                }
                                
                                events.append(new_event)
                                success_message = "Event created successfully!"
                            
                            # Save events to file
                            save_events(events)
                            
                            # Reset form state
                            st.session_state.show_event_form = False
                            st.session_state.editing_event = None
                            
                            st.success(success_message)
                            st.rerun()

# Display upcoming events timeline at the bottom
st.markdown("---")
st.subheader("Upcoming Events Timeline")

# Filter for upcoming events
now = datetime.now()
future_date = now + timedelta(days=30)  # Show next 30 days
upcoming_events = [
    event for event in events 
    if parse_datetime(event['start_time']) > now and parse_datetime(event['start_time']) < future_date
]
upcoming_events.sort(key=lambda x: parse_datetime(x['start_time']))

if upcoming_events:
    # Create timeline data
    timeline_data = []
    for event in upcoming_events:
        event_start = parse_datetime(event['start_time'])
        event_end = parse_datetime(event['end_time'])
        event_category = event.get('category', 'Other')
        
        # Create timeline entry
        timeline_data.append({
            "Task": event['title'],
            "Start": event_start,
            "Finish": event_end,
            "Category": event_category
        })
    
    # Create Gantt chart
    df = pd.DataFrame(timeline_data)
    
    fig = go.Figure()
    
    for i, task in enumerate(df["Task"]):
        task_start = df.Start[i]
        task_end = df.Finish[i]
        task_category = df.Category[i]
        task_color = EVENT_COLORS.get(task_category, "#6c757d")
        
        # Add task to Gantt chart
        fig.add_trace(go.Bar(
            x=[task_end - task_start],
            y=[task],
            orientation='h',
            base=task_start,
            marker_color=task_color,
            text=task_category,
            hoverinfo="text",
            showlegend=False
        ))
    
    # Update layout
    fig.update_layout(
        title="Team Events Timeline (Next 30 Days)",
        xaxis_title="Date",
        yaxis_title="Event",
        height=400,
        xaxis=dict(
            type='date',
            tickformat='%d %b',
            tickangle=-45
        ),
        yaxis=dict(
            autorange="reversed"
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Create legend
    st.subheader("Category Legend")
    legend_cols = st.columns(len(EVENT_CATEGORIES))
    for i, (category, color) in enumerate(EVENT_COLORS.items()):
        with legend_cols[i]:
            st.markdown(
                f"""
                <div style="display:flex; align-items:center;">
                    <div style="background-color:{color}; width:15px; height:15px; margin-right:5px;"></div>
                    <span>{category}</span>
                </div>
                """, 
                unsafe_allow_html=True
            )
else:
    st.info("No upcoming events in the next 30 days. Add events using the form above.")

st.markdown("---")
st.caption("Circuit Breakers Team Hub - Team Calendar")
