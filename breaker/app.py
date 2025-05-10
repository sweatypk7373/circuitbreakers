import streamlit as st
import pandas as pd
import os
import auth
from util import load_svg
from database import create_tables, migrate_data_from_json
import config  # Import the new configuration file

# Set page configuration
st.set_page_config(
    page_title="Circuit Breakers Team Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for data persistence
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'role' not in st.session_state:
    st.session_state.role = None

# Authentication
if not st.session_state.authenticated:
    auth.show_login_page()
else:
    # Main App
    with st.sidebar:
        logo_svg = load_svg("assets/logo.svg")
        st.image(logo_svg, width=150)
        
        st.title("Circuit Breakers")
        st.write(f"Welcome, {st.session_state.user}")
        st.write(f"Role: {st.session_state.role}")
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user = None
            st.session_state.role = None
            st.rerun()
    
    # App Home Page
    st.title("Circuit Breakers Team Hub")
    
    st.markdown("""
    Welcome to the Circuit Breakers Team Hub - your centralized platform for:
    
    - Team collaboration and communication
    - Project management and tracking
    - Build documentation and logging
    - Media and resource management
    - Sponsor and outreach coordination
    
    Navigate through the sections using the sidebar menu.
    """)
    
    # Quick Overview Cards (3 column layout)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("### Next Meeting\nTeam Strategy Session\n**Tomorrow, 4:00 PM**\nEngineering Lab")
    
    with col2:
        st.success("### Build Progress\n**78%** Complete\nDrivetrain assembly in progress")
        
    with col3:
        st.warning("### Upcoming Event\nRegional Competition\n**15 days remaining**\nPrepare documentation!")
    
    # Team Announcements
    st.subheader("Team Announcements")
    
    st.info("""
    **Parts Delivery Update - 10/25/2023**
    
    The new suspension components have arrived. Engineering team members, please check with the 
    faculty advisor to coordinate assembly time.
    """)
    
    st.info("""
    **Documentation Reminder - 10/22/2023**
    
    All team members should update their work logs by Friday. Media team needs photos of 
    the latest build progress.
    """)
    
    # Recent Team Activity
    st.subheader("Recent Team Activity")
    
    # Sample activity data (would normally come from a database)
    activity_data = {
        "Date": ["10/25/2023", "10/24/2023", "10/23/2023", "10/22/2023"],
        "Member": ["Alex Johnson", "Maria Garcia", "Jamal Williams", "Sarah Chen"],
        "Activity": [
            "Updated drivetrain documentation",
            "Added new sponsor to the outreach database",
            "Uploaded 15 new photos to Media Gallery",
            "Completed safety checklist for electrical components"
        ]
    }
    
    activity_df = pd.DataFrame(activity_data)
    st.dataframe(activity_df, use_container_width=True)
    
    st.markdown("---")
    st.caption("Circuit Breakers Team Hub - Powered by STEM Racing")
