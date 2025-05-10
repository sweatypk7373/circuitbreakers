import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime, timedelta
import plotly.express as px

# Add the parent directory to the path to import from the app root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import load_sponsors, save_sponsors, check_role_access, generate_id

# Page configuration
st.set_page_config(
    page_title="Sponsors & Outreach - Circuit Breakers",
    page_icon="🏆",
    layout="wide"
)

# Check if user is authenticated
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("Please login to access this page.")
    st.stop()

# Page title
st.title("Sponsors & Outreach")
st.write("Track sponsors, manage outreach activities, and organize promotional efforts")

# Define sponsor levels and colors
SPONSOR_LEVELS = ["Platinum", "Gold", "Silver", "Bronze", "Supporting", "In-Kind"]
SPONSOR_COLORS = {
    "Platinum": "#E5E4E2",
    "Gold": "#FFD700",
    "Silver": "#C0C0C0",
    "Bronze": "#CD7F32",
    "Supporting": "#00B4D8",
    "In-Kind": "#28a745"
}

# Initialize session state for sponsor form
if 'show_sponsor_form' not in st.session_state:
    st.session_state.show_sponsor_form = False
if 'editing_sponsor' not in st.session_state:
    st.session_state.editing_sponsor = None
if 'sponsor_search' not in st.session_state:
    st.session_state.sponsor_search = ""
if 'current_view' not in st.session_state:
    st.session_state.current_view = "Sponsors"  # or "Outreach"

# Load sponsors
sponsors = load_sponsors()

# Function to toggle sponsor form visibility
def toggle_sponsor_form():
    st.session_state.show_sponsor_form = not st.session_state.show_sponsor_form
    st.session_state.editing_sponsor = None

# Function to edit an existing sponsor
def edit_sponsor(sponsor_id):
    st.session_state.editing_sponsor = sponsor_id
    st.session_state.show_sponsor_form = True

# Function to delete a sponsor
def delete_sponsor(sponsor_id):
    global sponsors
    sponsors = [sponsor for sponsor in sponsors if sponsor['id'] != sponsor_id]
    save_sponsors(sponsors)
    st.success("Sponsor deleted successfully!")
    st.rerun()

# Function to toggle between Sponsors and Outreach views
def toggle_view():
    if st.session_state.current_view == "Sponsors":
        st.session_state.current_view = "Outreach"
    else:
        st.session_state.current_view = "Sponsors"

# Create view toggle
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    view_options = ["Sponsors", "Outreach"]
    selected_view = st.radio("View", view_options, horizontal=True, index=view_options.index(st.session_state.current_view))
    
    # Update view in session state
    st.session_state.current_view = selected_view

with col3:
    if st.session_state.current_view == "Sponsors":
        st.session_state.sponsor_search = st.text_input("Search sponsors...", value=st.session_state.sponsor_search)

# Sponsors view
if st.session_state.current_view == "Sponsors":
    # Action buttons
    if st.button("Add New Sponsor 🏢"):
        toggle_sponsor_form()
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Sponsor List", "Sponsor Dashboard", "Sponsorship Packages"])
    
    with tab1:
        # Filter sponsors based on search term
        filtered_sponsors = sponsors
        if st.session_state.sponsor_search:
            search_term = st.session_state.sponsor_search.lower()
            filtered_sponsors = [
                sponsor for sponsor in sponsors 
                if (search_term in sponsor.get("name", "").lower() or 
                    search_term in sponsor.get("contact_name", "").lower() or 
                    search_term in sponsor.get("description", "").lower() or
                    search_term in sponsor.get("level", "").lower())
            ]
        
        # Add filtering options
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            filter_level = st.multiselect("Filter by Level", ["All"] + SPONSOR_LEVELS, default=["All"])
        
        with filter_col2:
            filter_status = st.selectbox("Filter by Status", ["All", "Active", "Expired"])
        
        with filter_col3:
            sort_options = ["Name (A-Z)", "Level", "Contribution Amount", "Start Date"]
            sort_by = st.selectbox("Sort by", sort_options)
        
        # Apply filters
        # Level filter
        if not ("All" in filter_level or len(filter_level) == 0):
            filtered_sponsors = [sponsor for sponsor in filtered_sponsors if sponsor.get("level", "") in filter_level]
        
        # Status filter
        now = datetime.now()
        if filter_status == "Active":
            filtered_sponsors = [
                sponsor for sponsor in filtered_sponsors 
                if datetime.fromisoformat(sponsor.get("end_date", now.isoformat())) > now
            ]
        elif filter_status == "Expired":
            filtered_sponsors = [
                sponsor for sponsor in filtered_sponsors 
                if datetime.fromisoformat(sponsor.get("end_date", now.isoformat())) <= now
            ]
        
        # Apply sorting
        if sort_by == "Name (A-Z)":
            filtered_sponsors.sort(key=lambda x: x.get("name", "").lower())
        elif sort_by == "Level":
            # Custom level sorting order
            level_order = {level: i for i, level in enumerate(SPONSOR_LEVELS)}
            filtered_sponsors.sort(key=lambda x: level_order.get(x.get("level", ""), 999))
        elif sort_by == "Contribution Amount":
            # Sort by contribution amount (strip non-numeric characters)
            def extract_amount(sponsor):
                contribution = sponsor.get("contribution", "$0")
                # Remove any non-digit characters except the decimal point
                digits = ''.join(c for c in contribution if c.isdigit() or c == '.')
                try:
                    return float(digits)
                except ValueError:
                    return 0
            
            filtered_sponsors.sort(key=extract_amount, reverse=True)
        elif sort_by == "Start Date":
            filtered_sponsors.sort(key=lambda x: datetime.fromisoformat(x.get("start_date", "2000-01-01T00:00:00")))
        
        # Display sponsors in a list
        if filtered_sponsors:
            for sponsor in filtered_sponsors:
                with st.container():
                    # Define color based on level
                    level = sponsor.get("level", "Supporting")
                    level_color = SPONSOR_COLORS.get(level, "#00B4D8")
                    
                    # Calculate status
                    now = datetime.now()
                    end_date = datetime.fromisoformat(sponsor.get("end_date", now.isoformat()))
                    is_active = end_date > now
                    status_color = "#28a745" if is_active else "#dc3545"  # Green if active, red if expired
                    status_text = "Active" if is_active else "Expired"
                    
                    # Create sponsor card
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # Title with level badge
                        st.markdown(
                            f"""
                            <h3>
                                {sponsor.get('name')} 
                                <span style="background-color: {level_color}; padding: 2px 8px; border-radius: 10px; color: black; font-size: 0.8em; vertical-align: middle;">
                                    {level}
                                </span>
                                <span style="background-color: {status_color}; padding: 2px 8px; border-radius: 10px; color: white; font-size: 0.7em; vertical-align: middle; margin-left: 5px;">
                                    {status_text}
                                </span>
                            </h3>
                            """,
                            unsafe_allow_html=True
                        )
                        
                        # Contribution
                        st.markdown(f"**Contribution:** {sponsor.get('contribution', 'Not specified')}")
                        
                        # Description
                        st.markdown(f"**Description:** {sponsor.get('description', 'No description provided.')}")
                        
                        # Contact info
                        st.markdown(f"**Contact:** {sponsor.get('contact_name', 'N/A')}")
                        st.markdown(f"**Email:** {sponsor.get('contact_email', 'N/A')}")
                        
                        # Website
                        if sponsor.get('website'):
                            st.markdown(f"**Website:** [{sponsor.get('website')}](https://{sponsor.get('website')})")
                    
                    with col2:
                        # Date information
                        start_date = datetime.fromisoformat(sponsor.get("start_date"))
                        end_date = datetime.fromisoformat(sponsor.get("end_date"))
                        
                        st.markdown(f"**Start Date:** {start_date.strftime('%m/%d/%Y')}")
                        st.markdown(f"**End Date:** {end_date.strftime('%m/%d/%Y')}")
                        
                        # Add edit/delete buttons
                        if check_role_access(['admin', 'lead']):
                            if st.button("Edit", key=f"edit_{sponsor['id']}"):
                                edit_sponsor(sponsor["id"])
                            
                            if st.button("Delete", key=f"delete_{sponsor['id']}"):
                                delete_sponsor(sponsor["id"])
                    
                    st.markdown("---")
        else:
            st.info("No sponsors found matching your filters. Add some using the 'Add New Sponsor' button.")
    
    with tab2:
        st.subheader("Sponsor Dashboard")
        
        if sponsors:
            # Calculate metrics
            total_sponsors = len(sponsors)
            
            # Calculate active sponsors
            now = datetime.now()
            active_sponsors = [sponsor for sponsor in sponsors if datetime.fromisoformat(sponsor.get("end_date", now.isoformat())) > now]
            active_count = len(active_sponsors)
            
            # Calculate total sponsorship value (approximate)
            total_value = 0
            for sponsor in active_sponsors:
                contribution = sponsor.get("contribution", "$0")
                # Remove any non-digit characters except the decimal point
                digits = ''.join(c for c in contribution if c.isdigit() or c == '.')
                try:
                    value = float(digits)
                    total_value += value
                except ValueError:
                    pass
            
            # Display metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Sponsors", total_sponsors)
            
            with col2:
                st.metric("Active Sponsorships", active_count)
            
            with col3:
                st.metric("Total Sponsorship Value", f"${total_value:,.2f}")
            
            # Create visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Sponsors by level
                level_counts = {}
                for level in SPONSOR_LEVELS:
                    level_counts[level] = len([sponsor for sponsor in sponsors if sponsor.get("level") == level])
                
                # Filter out levels with 0 sponsors
                level_counts = {k: v for k, v in level_counts.items() if v > 0}
                
                # Create DataFrame for chart
                level_df = pd.DataFrame({
                    "Level": list(level_counts.keys()),
                    "Count": list(level_counts.values())
                })
                
                # Create pie chart
                fig = px.pie(
                    level_df,
                    values="Count",
                    names="Level",
                    title="Sponsors by Level",
                    color="Level",
                    color_discrete_map={level: SPONSOR_COLORS.get(level, "#00B4D8") for level in level_counts.keys()}
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Sponsorship timeline
                # Create a list of sponsors with their start and end dates
                timeline_data = []
                for sponsor in sponsors:
                    start_date = datetime.fromisoformat(sponsor.get("start_date"))
                    end_date = datetime.fromisoformat(sponsor.get("end_date"))
                    
                    timeline_data.append({
                        "Sponsor": sponsor.get("name"),
                        "Level": sponsor.get("level"),
                        "Start": start_date,
                        "End": end_date
                    })
                
                # Create DataFrame
                timeline_df = pd.DataFrame(timeline_data)
                
                # Sort by end date
                timeline_df = timeline_df.sort_values("End")
                
                # Create a Gantt chart
                fig = px.timeline(
                    timeline_df,
                    x_start="Start",
                    x_end="End",
                    y="Sponsor",
                    color="Level",
                    title="Sponsorship Timeline",
                    color_discrete_map=SPONSOR_COLORS
                )
                
                # Add a vertical line for today
                fig.add_vline(x=datetime.now(), line_width=2, line_dash="dash", line_color="red")
                
                # Update layout
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Sponsor",
                    legend_title="Level"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Upcoming renewals
            st.subheader("Upcoming Sponsorship Renewals")
            
            # Get sponsors with end dates in the next 90 days
            upcoming_end = [
                sponsor for sponsor in sponsors 
                if now < datetime.fromisoformat(sponsor.get("end_date")) < (now + timedelta(days=90))
            ]
            
            # Sort by end date
            upcoming_end.sort(key=lambda x: datetime.fromisoformat(x.get("end_date")))
            
            if upcoming_end:
                # Create table data
                renewal_data = []
                for sponsor in upcoming_end:
                    end_date = datetime.fromisoformat(sponsor.get("end_date"))
                    days_left = (end_date - now).days
                    
                    renewal_data.append({
                        "Sponsor": sponsor.get("name"),
                        "Level": sponsor.get("level"),
                        "Contact": sponsor.get("contact_name"),
                        "End Date": end_date.strftime("%m/%d/%Y"),
                        "Days Left": days_left
                    })
                
                # Create DataFrame
                renewal_df = pd.DataFrame(renewal_data)
                
                # Display table
                st.dataframe(renewal_df, use_container_width=True)
            else:
                st.info("No sponsorships are up for renewal in the next 90 days.")
        else:
            st.info("No sponsor data available. Add sponsors to see analytics.")
    
    with tab3:
        st.subheader("Sponsorship Packages")
        
        # Create expandable sections for each sponsorship level
        st.markdown("""
        Below are the sponsorship levels available for the Circuit Breakers team. Each level comes with
        different benefits and recognition opportunities.
        """)
        
        with st.expander("Platinum Sponsor - $10,000+"):
            st.markdown("""
            ### Platinum Sponsor - $10,000+
            
            **Benefits include:**
            
            - Prominent logo placement on the vehicle
            - Large logo on team uniforms
            - Featured position on team website with company description
            - Social media recognition (minimum 10 posts per season)
            - Acknowledgment in all press releases and media communications
            - Team appearances at sponsor events (up to 4 per year)
            - Invitation to exclusive team events
            - Personalized thank-you plaque
            - Vehicle demonstration at sponsor location
            """)
        
        with st.expander("Gold Sponsor - $5,000 to $9,999"):
            st.markdown("""
            ### Gold Sponsor - $5,000 to $9,999
            
            **Benefits include:**
            
            - Logo placement on the vehicle
            - Logo on team uniforms
            - Company listing on team website with link
            - Social media recognition (minimum 6 posts per season)
            - Acknowledgment in press releases
            - Team appearances at sponsor events (up to 2 per year)
            - Invitation to team events
            - Thank-you plaque
            """)
        
        with st.expander("Silver Sponsor - $2,500 to $4,999"):
            st.markdown("""
            ### Silver Sponsor - $2,500 to $4,999
            
            **Benefits include:**
            
            - Medium-sized logo on the vehicle
            - Logo on team website with link
            - Social media recognition (minimum 4 posts per season)
            - Team appearances at sponsor events (1 per year)
            - Invitation to team events
            - Certificate of appreciation
            """)
        
        with st.expander("Bronze Sponsor - $1,000 to $2,499"):
            st.markdown("""
            ### Bronze Sponsor - $1,000 to $2,499
            
            **Benefits include:**
            
            - Small logo on the vehicle
            - Name listed on team website
            - Social media recognition (minimum 2 posts per season)
            - Invitation to team events
            - Certificate of appreciation
            """)
        
        with st.expander("Supporting Sponsor - $500 to $999"):
            st.markdown("""
            ### Supporting Sponsor - $500 to $999
            
            **Benefits include:**
            
            - Name listed on team website
            - Social media recognition (1 post per season)
            - Invitation to team events
            - Thank-you letter
            """)
        
        with st.expander("In-Kind Sponsor - Value based on donation"):
            st.markdown("""
            ### In-Kind Sponsor - Value based on donation
            
            For sponsors providing goods, services, equipment, or other non-monetary support.
            Benefits commensurate with the estimated value of the donation.
            
            **Typical benefits may include:**
            
            - Recognition appropriate to the donation value level
            - Special acknowledgment of the specific contribution
            - Custom benefits tailored to the sponsor's needs
            """)
        
        # Sponsorship materials
        st.subheader("Sponsorship Materials")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            ### Available Resources
            
            - Sponsorship Packet (PDF)
            - Sponsor Request Letter Template
            - Sponsor Thank You Letter Template
            - Sponsorship Agreement Form
            - Sponsor Recognition Plan
            """)
            
            # These buttons would normally download or display actual files
            if st.button("Download Sponsorship Packet"):
                st.info("In a complete implementation, this would download the sponsorship packet PDF.")
        
        with col2:
            st.markdown("""
            ### Sponsor Acquisition Process
            
            1. Identify potential sponsors that align with team values
            2. Send initial contact email or letter using templates
            3. Follow up by phone within 1 week
            4. Schedule in-person or virtual meeting to present opportunities
            5. Provide sponsorship packet with clear benefits
            6. Complete sponsorship agreement form
            7. Send thank you letter and begin fulfilling benefits
            """)

# Outreach view
else:  # st.session_state.current_view == "Outreach"
    st.subheader("Team Outreach")
    
    # Create tabs for different outreach activities
    tab1, tab2, tab3, tab4 = st.tabs(["Upcoming Events", "Past Events", "Community Impact", "Outreach Resources"])
    
    with tab1:
        st.markdown("### Upcoming Outreach Events")
        
        # In a full implementation, this would load from a database
        # Sample data for demonstration
        upcoming_events = [
            {
                "title": "STEM Showcase at Lincoln Elementary",
                "date": (datetime.now() + timedelta(days=5)).strftime("%A, %B %d, %Y"),
                "time": "3:30 PM - 5:00 PM",
                "location": "Lincoln Elementary School Gymnasium",
                "description": "Interactive demonstration of vehicle design and racing concepts for 3rd-5th grade students.",
                "team_members": "Alex Johnson, Maria Garcia, Jamal Williams, Sarah Chen",
                "materials": "Demo vehicle, safety gear, interactive display boards, handouts"
            },
            {
                "title": "Community Science Fair",
                "date": (datetime.now() + timedelta(days=12)).strftime("%A, %B %d, %Y"),
                "time": "10:00 AM - 4:00 PM",
                "location": "City Convention Center",
                "description": "Booth showcasing STEM racing concepts and team achievements.",
                "team_members": "David Kim, Carlos Rodriguez, Aisha Patel",
                "materials": "Display vehicle, posters, brochures, sign-up sheet for interested students"
            },
            {
                "title": "Engineering Career Day Presentation",
                "date": (datetime.now() + timedelta(days=18)).strftime("%A, %B %d, %Y"),
                "time": "1:00 PM - 2:30 PM",
                "location": "Westside High School",
                "description": "Panel discussion and Q&A about STEM careers in automotive and racing industries.",
                "team_members": "Admin User, Alex Johnson, Sarah Chen",
                "materials": "Presentation slides, career pathway handouts, team brochures"
            }
        ]
        
        # Display upcoming events
        for event in upcoming_events:
            with st.expander(f"{event['title']} - {event['date']}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Date:** {event['date']}")
                    st.markdown(f"**Time:** {event['time']}")
                    st.markdown(f"**Location:** {event['location']}")
                
                with col2:
                    st.markdown(f"**Team Members:** {event['team_members']}")
                    st.markdown(f"**Materials Needed:** {event['materials']}")
                
                st.markdown(f"**Description:** {event['description']}")
                
                # Action buttons (would be connected to functionality in a full implementation)
                button_col1, button_col2, button_col3 = st.columns(3)
                
                with button_col1:
                    st.button("Volunteer to Participate", key=f"volunteer_{event['title']}")
                
                with button_col2:
                    st.button("Edit Event Details", key=f"edit_{event['title']}")
                
                with button_col3:
                    st.button("View Event Brief", key=f"brief_{event['title']}")
        
        # Event planning
        st.markdown("### Event Planning")
        
        # In a real implementation, this would be a form that submits to a database
        with st.expander("Plan New Outreach Event"):
            with st.form("new_outreach_event"):
                event_title = st.text_input("Event Title")
                event_date = st.date_input("Event Date", value=datetime.now() + timedelta(days=14))
                
                time_col1, time_col2 = st.columns(2)
                with time_col1:
                    start_time = st.time_input("Start Time", value=datetime.strptime("10:00", "%H:%M").time())
                with time_col2:
                    end_time = st.time_input("End Time", value=datetime.strptime("12:00", "%H:%M").time())
                
                event_location = st.text_input("Location")
                event_description = st.text_area("Description")
                
                # Team member selection
                team_members = st.multiselect(
                    "Team Members Needed",
                    ["Alex Johnson", "Maria Garcia", "Jamal Williams", "Sarah Chen", "David Kim", "Carlos Rodriguez", "Aisha Patel", "Michael Brown"]
                )
                
                materials_needed = st.text_area("Materials Needed")
                
                st.form_submit_button("Save Event")
    
    with tab2:
        st.markdown("### Past Outreach Events")
        
        # Sample past events
        past_events = [
            {
                "title": "Girls in STEM Workshop",
                "date": (datetime.now() - timedelta(days=15)).strftime("%A, %B %d, %Y"),
                "location": "Community Center",
                "attendees": 24,
                "team_members": 5,
                "description": "Interactive workshop encouraging girls to explore STEM fields through racing and automotive design concepts.",
                "outcomes": "8 students expressed interest in joining future team activities."
            },
            {
                "title": "City Science Festival",
                "date": (datetime.now() - timedelta(days=45)).strftime("%A, %B %d, %Y"),
                "location": "Downtown Plaza",
                "attendees": 150,
                "team_members": 8,
                "description": "Public festival booth with racing demonstrations and interactive STEM activities.",
                "outcomes": "Collected 35 email sign-ups for newsletter. Made connection with potential new sponsor."
            },
            {
                "title": "Elementary School Demo Day",
                "date": (datetime.now() - timedelta(days=62)).strftime("%A, %B %d, %Y"),
                "location": "Washington Elementary",
                "attendees": 78,
                "team_members": 4,
                "description": "Series of classroom demonstrations on physics principles in racing.",
                "outcomes": "Teachers requested follow-up curriculum resources. Principal invited team back for future events."
            }
        ]
        
        # Create a DataFrame for display
        past_events_data = pd.DataFrame(past_events)
        
        # Display the table
        st.dataframe(past_events_data[["title", "date", "location", "attendees"]], use_container_width=True)
        
        # Show details for selected event
        selected_event_title = st.selectbox(
            "Select an event to view details",
            [event["title"] for event in past_events]
        )
        
        # Display selected event details
        selected_event = next((event for event in past_events if event["title"] == selected_event_title), None)
        
        if selected_event:
            st.markdown(f"### {selected_event['title']}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Date:** {selected_event['date']}")
                st.markdown(f"**Location:** {selected_event['location']}")
                st.markdown(f"**Team Members Involved:** {selected_event['team_members']}")
            
            with col2:
                st.markdown(f"**Total Attendees:** {selected_event['attendees']}")
                st.markdown(f"**Outcomes:** {selected_event['outcomes']}")
            
            st.markdown(f"**Description:** {selected_event['description']}")
            
            # Event media would go here in a full implementation
            st.markdown("### Event Media")
            
            media_col1, media_col2, media_col3 = st.columns(3)
            
            with media_col1:
                # Placeholder for image
                st.markdown(
                    """
                    <div style="background-color: #f0f0f0; height: 150px; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 48px;">📷</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with media_col2:
                # Placeholder for image
                st.markdown(
                    """
                    <div style="background-color: #f0f0f0; height: 150px; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 48px;">📷</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            with media_col3:
                # Placeholder for image
                st.markdown(
                    """
                    <div style="background-color: #f0f0f0; height: 150px; display: flex; align-items: center; justify-content: center;">
                        <span style="font-size: 48px;">📷</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            
            # Feedback and analytics
            st.markdown("### Event Feedback")
            
            # Sample feedback metrics
            feedback_data = {
                "Rating": ["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very Dissatisfied"],
                "Count": [12, 8, 3, 1, 0]
            }
            
            feedback_df = pd.DataFrame(feedback_data)
            
            # Create a simple horizontal bar chart
            fig = px.bar(
                feedback_df,
                x="Count",
                y="Rating",
                orientation="h",
                title="Participant Satisfaction",
                color="Count",
                color_continuous_scale=px.colors.sequential.Viridis
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("### Community Impact")
        
        # Impact metrics
        impact_col1, impact_col2, impact_col3, impact_col4 = st.columns(4)
        
        with impact_col1:
            st.metric("Total Outreach Events", "15")
        
        with impact_col2:
            st.metric("People Reached", "1,250+")
        
        with impact_col3:
            st.metric("Educational Hours", "45")
        
        with impact_col4:
            st.metric("Community Partners", "8")
        
        # Impact by demographics (sample data)
        st.subheader("Impact Demographics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Age groups reached
            age_data = {
                "Age Group": ["Elementary (K-5)", "Middle School (6-8)", "High School (9-12)", "College", "Adults"],
                "Percentage": [35, 25, 20, 10, 10]
            }
            
            age_df = pd.DataFrame(age_data)
            
            fig = px.pie(
                age_df,
                values="Percentage",
                names="Age Group",
                title="Audience by Age Group",
                color_discrete_sequence=px.colors.qualitative.Vivid
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Topics covered
            topic_data = {
                "Topic": ["Engineering Design", "Physics", "Electrical", "Teamwork", "Career Pathways", "Sustainability"],
                "Hours": [12, 10, 8, 5, 5, 5]
            }
            
            topic_df = pd.DataFrame(topic_data)
            
            fig = px.bar(
                topic_df,
                x="Topic",
                y="Hours",
                title="Educational Hours by Topic",
                color="Hours",
                color_continuous_scale=px.colors.sequential.Viridis
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Map of outreach locations
        st.subheader("Outreach Locations")
        
        # Sample location data - in a real implementation, this would be actual coordinates
        location_data = {
            "Location": ["Washington Elementary", "Lincoln Middle School", "Downtown Plaza", "Community Center", "Westside High School", "Public Library", "Science Museum", "Tech Conference Center"],
            "lat": [37.7749, 37.7849, 37.7949, 37.8049, 37.7649, 37.7549, 37.7449, 37.7349],
            "lon": [-122.4194, -122.4294, -122.4394, -122.4494, -122.4094, -122.3994, -122.3894, -122.3794],
            "Events": [2, 1, 3, 2, 1, 3, 2, 1]
        }
        
        location_df = pd.DataFrame(location_data)
        
        # Create a scatter mapbox
        fig = px.scatter_mapbox(
            location_df,
            lat="lat",
            lon="lon",
            hover_name="Location",
            size="Events",
            color="Events",
            color_continuous_scale=px.colors.cyclical.IceFire,
            size_max=15,
            zoom=10,
            mapbox_style="carto-positron"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Impact stories
        st.subheader("Impact Stories")
        
        with st.expander("Student Inspiration"):
            st.markdown("""
            After attending our STEM workshop at Lincoln Middle School, 7th grader Jessica Martinez was inspired to join her school's science club. She recently contacted us to share that she's now leading a team in a regional science competition, focusing on renewable energy in transportation.
            
            "I never thought engineering could be so exciting until I saw the Circuit Breakers team demonstrate their vehicle. Now I want to be an engineer too!" - Jessica
            """)
        
        with st.expander("Teacher Collaboration"):
            st.markdown("""
            Mr. Ramirez, a physics teacher at Westside High School, has incorporated our racing demonstrations into his curriculum after our visit. He reports that student engagement has increased significantly, with more students connecting theoretical physics concepts to real-world applications.
            
            We're now developing a teaching module with Mr. Ramirez that can be shared with other schools.
            """)
        
        with st.expander("Community Recognition"):
            st.markdown("""
            The Circuit Breakers team was featured in the local newspaper following our booth at the City Science Festival. The article highlighted our commitment to community education and inspiring the next generation of engineers.
            
            This exposure has led to two new community partnerships and increased interest from potential sponsors.
            """)
    
    with tab4:
        st.markdown("### Outreach Resources")
        
        # Presentation materials
        st.subheader("Presentation Materials")
        
        presentation_col1, presentation_col2 = st.columns(2)
        
        with presentation_col1:
            st.markdown("""
            **Available Presentations:**
            - "Introduction to STEM Racing" (Elementary)
            - "Physics of Racing" (Middle/High School)
            - "Engineering Design Process" (All ages)
            - "Careers in Automotive Engineering" (High School)
            - "Team Building Through STEM" (Educational Professionals)
            """)
            
            # These buttons would download actual files in a full implementation
            if st.button("Download Presentations Package"):
                st.info("In a complete implementation, this would download the presentations ZIP file.")
        
        with presentation_col2:
            st.markdown("""
            **Demonstration Kits:**
            - Mini Vehicle Build Kit
            - Forces in Motion Kit
            - Electrical Circuits Demo
            - Materials Testing Station
            - Design Challenge Activity
            """)
            
            if st.button("View Kit Contents and Setup Instructions"):
                st.info("In a complete implementation, this would show kit details.")
        
        # Outreach planning resources
        st.subheader("Outreach Planning Resources")
        
        with st.expander("Event Planning Checklist"):
            st.markdown("""
            ### Event Planning Checklist
            
            #### 2-4 Weeks Before
            - [ ] Confirm event date, time, and location
            - [ ] Determine team members who will participate
            - [ ] Select appropriate presentations and activities
            - [ ] Prepare materials list
            - [ ] Contact venue to confirm logistics (tables, power, space)
            
            #### 1 Week Before
            - [ ] Confirm team member participation
            - [ ] Finalize presentation materials
            - [ ] Prepare and test demonstrations
            - [ ] Create sign-in sheet or feedback forms
            - [ ] Pack team brochures and promotional materials
            
            #### Day Before
            - [ ] Confirm transportation arrangements
            - [ ] Charge all electronic devices
            - [ ] Final check of all materials
            - [ ] Team briefing on roles and responsibilities
            
            #### Day of Event
            - [ ] Arrive 30-45 minutes early for setup
            - [ ] Take before photos of setup
            - [ ] Track attendance and collect contact information
            - [ ] Document event with photos and video
            - [ ] Collect feedback from participants
            
            #### After Event
            - [ ] Send thank you to host/venue
            - [ ] Document event in team records
            - [ ] Follow up with interested participants
            - [ ] Team debrief to discuss what worked well and improvements
            - [ ] Update outreach metrics
            """)
        
        with st.expander("Outreach Scripts and Talking Points"):
            st.markdown("""
            ### Outreach Scripts and Talking Points
            
            #### Introduction to the Team
            "Hi! We're the Circuit Breakers, a STEM racing team from [School/Organization]. We design, build, and race electric vehicles while learning engineering, teamwork, and problem-solving skills."
            
            #### Explaining the Vehicle
            "Our vehicle uses [key technologies] and can reach speeds of [speed]. The most challenging part of our design was [challenge], which we solved by [solution]."
            
            #### Encouraging Participation
            "Anyone interested in science, technology, engineering, or math can get involved in projects like ours. You don't need prior experience - just curiosity and willingness to learn!"
            
            #### Discussing STEM Careers
            "The skills we learn on this team prepare us for careers in fields like automotive engineering, renewable energy, electronics, computer science, and project management."
            
            #### Answering "What's the Hardest Part?"
            "The most challenging aspect is [honest challenge - e.g., balancing performance with safety, time management, troubleshooting electrical issues]. We overcome this by [strategy]."
            
            #### Explaining the Competition
            "We compete against teams from [scope of competition] in events that test not just speed, but also design innovation, energy efficiency, and technical knowledge."
            """)
        
        # Feedback forms
        st.subheader("Feedback Collection Forms")
        
        feedback_col1, feedback_col2 = st.columns(2)
        
        with feedback_col1:
            st.markdown("""
            **Available Forms:**
            - Student Participant Feedback
            - Educator Feedback
            - Event Host Evaluation
            - Team Member Event Reflection
            """)
            
            if st.button("Download Feedback Form Templates"):
                st.info("In a complete implementation, this would download form templates.")
        
        with feedback_col2:
            st.markdown("""
            **Data Collection Guides:**
            - Attendance Tracking Templates
            - Impact Metrics Worksheet
            - Follow-up Contact Management
            - Qualitative Feedback Analysis Guide
            """)

# Sponsor form
if st.session_state.show_sponsor_form and st.session_state.current_view == "Sponsors":
    st.markdown("---")
    
    # Determine if we're editing or creating a new sponsor
    editing = st.session_state.editing_sponsor is not None
    
    if editing:
        sponsor_to_edit = next((sponsor for sponsor in sponsors if sponsor["id"] == st.session_state.editing_sponsor), None)
        st.subheader(f"Edit Sponsor: {sponsor_to_edit['name']}")
    else:
        st.subheader("Add New Sponsor")
    
    # Create form
    with st.form("sponsor_form"):
        # Pre-fill values if editing
        if editing:
            name_value = sponsor_to_edit["name"]
            level_index = SPONSOR_LEVELS.index(sponsor_to_edit.get("level")) if sponsor_to_edit.get("level") in SPONSOR_LEVELS else 0
            contribution_value = sponsor_to_edit.get("contribution", "")
            contact_name_value = sponsor_to_edit.get("contact_name", "")
            contact_email_value = sponsor_to_edit.get("contact_email", "")
            website_value = sponsor_to_edit.get("website", "")
            description_value = sponsor_to_edit.get("description", "")
            start_date_value = datetime.fromisoformat(sponsor_to_edit.get("start_date")).date()
            end_date_value = datetime.fromisoformat(sponsor_to_edit.get("end_date")).date()
        else:
            name_value = ""
            level_index = 0
            contribution_value = ""
            contact_name_value = ""
            contact_email_value = ""
            website_value = ""
            description_value = ""
            start_date_value = datetime.now().date()
            end_date_value = (datetime.now() + timedelta(days=365)).date()  # Default to 1 year sponsorship
        
        # Form fields
        sponsor_name = st.text_input("Sponsor Name*", value=name_value)
        
        col1, col2 = st.columns(2)
        
        with col1:
            sponsor_level = st.selectbox("Sponsorship Level*", SPONSOR_LEVELS, index=level_index)
            sponsor_contribution = st.text_input("Contribution Amount*", value=contribution_value, help="Example: $5,000")
        
        with col2:
            start_date = st.date_input("Start Date*", value=start_date_value)
            end_date = st.date_input("End Date*", value=end_date_value)
        
        # Contact information
        st.subheader("Contact Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            contact_name = st.text_input("Contact Person", value=contact_name_value)
            contact_email = st.text_input("Contact Email", value=contact_email_value)
        
        with col2:
            website = st.text_input("Website", value=website_value, help="Example: www.company-example.com")
        
        # Description
        sponsor_description = st.text_area("Description", value=description_value, height=100, help="Brief description of the sponsor organization")
        
        # Submit buttons
        col1, col2 = st.columns(2)
        
        with col1:
            submit_button = st.form_submit_button("Save Sponsor")
        
        with col2:
            cancel_button = st.form_submit_button("Cancel")
        
        if cancel_button:
            st.session_state.show_sponsor_form = False
            st.session_state.editing_sponsor = None
            st.rerun()
        
        if submit_button:
            # Validate required fields
            if not sponsor_name or not sponsor_level or not sponsor_contribution:
                st.error("Sponsor name, level, and contribution amount are required!")
            elif end_date <= start_date:
                st.error("End date must be after start date!")
            else:
                # Prepare date strings
                start_datetime = datetime.combine(start_date, datetime.min.time())
                end_datetime = datetime.combine(end_date, datetime.max.time())
                
                if editing:
                    # Update existing sponsor
                    for sponsor in sponsors:
                        if sponsor["id"] == st.session_state.editing_sponsor:
                            sponsor["name"] = sponsor_name
                            sponsor["level"] = sponsor_level
                            sponsor["contribution"] = sponsor_contribution
                            sponsor["contact_name"] = contact_name
                            sponsor["contact_email"] = contact_email
                            sponsor["website"] = website
                            sponsor["description"] = sponsor_description
                            sponsor["start_date"] = start_datetime.isoformat()
                            sponsor["end_date"] = end_datetime.isoformat()
                            break
                    
                    success_message = "Sponsor updated successfully!"
                else:
                    # Create new sponsor
                    new_sponsor = {
                        "id": generate_id(),
                        "name": sponsor_name,
                        "level": sponsor_level,
                        "contribution": sponsor_contribution,
                        "contact_name": contact_name,
                        "contact_email": contact_email,
                        "website": website,
                        "description": sponsor_description,
                        "start_date": start_datetime.isoformat(),
                        "end_date": end_datetime.isoformat()
                    }
                    
                    sponsors.append(new_sponsor)
                    success_message = "Sponsor added successfully!"
                
                # Save sponsors to file
                save_sponsors(sponsors)
                
                # Reset form
                st.session_state.show_sponsor_form = False
                st.session_state.editing_sponsor = None
                
                st.success(success_message)
                st.rerun()

st.caption("Circuit Breakers Team Hub - Sponsors & Outreach")
