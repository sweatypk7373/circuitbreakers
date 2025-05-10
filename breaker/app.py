import streamlit as st
import pandas as pd
import os
import sys

# Set page configuration - THIS MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Circuit Breakers Team Hub",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure assets directory exists
os.makedirs("assets", exist_ok=True)

# Check if logo file exists, if not create a default one
if not os.path.exists("assets/logo.svg"):
    # Create a default logo SVG file
    default_logo = """<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
        <circle cx="100" cy="100" r="90" fill="#f1f1f1" stroke="#0084D8" stroke-width="5"/>
        <text x="100" y="90" font-family="Arial" font-size="18" fill="#0084D8" text-anchor="middle">CIRCUIT</text>
        <text x="100" y="115" font-family="Arial" font-size="18" fill="#0084D8" text-anchor="middle">BREAKERS</text>
        <path d="M80,130 L95,150 L110,130 L125,150" stroke="#C0C0C0" stroke-width="4" fill="none"/>
        <path d="M60,120 L140,120" stroke="#0084D8" stroke-width="3" fill="none"/>
        <path d="M70,60 L130,60" stroke="#0084D8" stroke-width="3" fill="none"/>
        <path d="M90,60 L90,120" stroke="#0084D8" stroke-width="3" fill="none"/>
        <path d="M110,60 L110,120" stroke="#0084D8" stroke-width="3" fill="none"/>
    </svg>"""
    
    with open("assets/logo.svg", "w") as f:
        f.write(default_logo)

# Import auth (after creating assets)
import auth
from database import create_tables, migrate_data_from_json
import config  # Import the new configuration file

# Utility function to load SVG
def load_svg(svg_path):
    """Load an SVG file or return a default SVG if the file doesn't exist."""
    try:
        if os.path.exists(svg_path):
            with open(svg_path, 'r') as f:
                return f.read()
        else:
            # Return a default SVG logo if the file doesn't exist
            return """<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
                <circle cx="100" cy="100" r="90" fill="#f1f1f1" stroke="#0084D8" stroke-width="5"/>
                <text x="100" y="90" font-family="Arial" font-size="18" fill="#0084D8" text-anchor="middle">CIRCUIT</text>
                <text x="100" y="115" font-family="Arial" font-size="18" fill="#0084D8" text-anchor="middle">BREAKERS</text>
                <path d="M80,130 L95,150 L110,130 L125,150" stroke="#C0C0C0" stroke-width="4" fill="none"/>
                <path d="M60,120 L140,120" stroke="#0084D8" stroke-width="3" fill="none"/>
                <path d="M70,60 L130,60" stroke="#0084D8" stroke-width="3" fill="none"/>
                <path d="M90,60 L90,120" stroke="#0084D8" stroke-width="3" fill="none"/>
                <path d="M110,60 L110,120" stroke="#0084D8" stroke-width="3" fill="none"/>
            </svg>"""
    except Exception as e:
        st.warning(f"Could not load SVG: {e}")
        # Return a minimal SVG as fallback
        return """<svg width="150" height="50" xmlns="http://www.w3.org/2000/svg">
            <rect width="150" height="50" fill="#0084D8"/>
            <text x="75" y="30" font-family="Arial" font-size="16" fill="white" text-anchor="middle">Circuit Breakers</text>
        </svg>"""

# Initialize required data structures and directories
config.configure_environment()
create_tables()
migrate_data_from_json()

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
        try:
            # Try to load the logo SVG
            logo_svg = load_svg("assets/logo.svg")
            st.image(logo_svg, width=150)
        except Exception as e:
            # If loading fails, use a text header instead
            st.markdown("## ⚡ Circuit Breakers")
        
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
    
    # Sample activity data
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
