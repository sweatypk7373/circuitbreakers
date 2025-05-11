import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import base64
from io import BytesIO

# Create data directories if they don't exist
def initialize_data_directories():
    directories = [
        "data",
        "data/tasks",
        "data/logs",
        "data/resources",
        "data/media",
        "data/sponsors",
        "data/events",
        "data/messages"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# Check if user has required role
def check_role_access(required_roles):
    if st.session_state.role not in required_roles:
        st.warning(f"You don't have permission to access this section. Required role: {' or '.join(required_roles)}")
        return False
    return True

# Load a task file
def load_tasks():
    task_file = "breaker/data/tasks/tasks.json"
    if not os.path.exists(task_file):
        tasks = []
        with open(task_file, 'w') as f:
            json.dump(tasks, f, indent=4)
        return tasks
    
    with open(task_file, 'r') as f:
        return json.load(f)

# Save tasks to file
def save_tasks(tasks):
    task_file = "breaker/data/tasks/tasks.json"
    with open(task_file, 'w') as f:
        json.dump(tasks, f, indent=4)

# Load build log entries
def load_logs():
    log_file = "breaker/data/logs/build_logs.json"
    if not os.path.exists(log_file):
        logs = []
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=4)
        return logs
    
    with open(log_file, 'r') as f:
        return json.load(f)

# Save build log entries
def save_logs(logs):
    log_file = "breaker/data/logs/build_logs.json"
    with open(log_file, 'w') as f:
        json.dump(logs, f, indent=4)

# Load resources/documents
def load_resources():
    resource_file = "breaker/data/resources/resources.json"
    if not os.path.exists(resource_file):
        resources = []
        with open(resource_file, 'w') as f:
            json.dump(resources, f, indent=4)
        return resources
    
    with open(resource_file, 'r') as f:
        return json.load(f)

# Save resources/documents
def save_resources(resources):
    resource_file = "breaker/data/resources/resources.json"
    with open(resource_file, 'w') as f:
        json.dump(resources, f, indent=4)

# Load media items
def load_media():
    media_file = "breaker/data/media/media_items.json"
    if not os.path.exists(media_file):
        media_items = []
        with open(media_file, 'w') as f:
            json.dump(media_items, f, indent=4)
        return media_items
    
    with open(media_file, 'r') as f:
        return json.load(f)

# Save media items
def save_media(media_items):
    media_file = "breaker/data/media/media_items.json"
    with open(media_file, 'w') as f:
        json.dump(media_items, f, indent=4)

# Load sponsors
def load_sponsors():
    sponsor_file = "breaker/data/sponsors/sponsors.json"
    if not os.path.exists(sponsor_file):
        sponsors = []
        with open(sponsor_file, 'w') as f:
            json.dump(sponsors, f, indent=4)
        return sponsors
    
    with open(sponsor_file, 'r') as f:
        return json.load(f)

# Save sponsors
def save_sponsors(sponsors):
    sponsor_file = "breaker/data/sponsors/sponsors.json"
    with open(sponsor_file, 'w') as f:
        json.dump(sponsors, f, indent=4)

# Load events
def load_events():
    event_file = "breaker/data/events/events.json"
    if not os.path.exists(event_file):
        events = []
        with open(event_file, 'w') as f:
            json.dump(events, f, indent=4)
        return events
    
    with open(event_file, 'r') as f:
        return json.load(f)

# Save events
def save_events(events):
    event_file = "breaker/data/events/events.json"
    with open(event_file, 'w') as f:
        json.dump(events, f, indent=4)

# Load team members
def load_team_members():
    user_data_file = "breaker/data/users.json"
    if not os.path.exists(user_data_file):
        return []
    
    with open(user_data_file, 'r') as f:
        user_data = json.load(f)
    
    members = []
    for username, data in user_data.items():
        member = {
            "username": username,
            "name": data["name"],
            "role": data["role"],
            "email": data["email"]
        }
        members.append(member)
    
    return members

# Load messages
def load_messages():
    message_file = "breaker/data/messages/messages.json"
    if not os.path.exists(message_file):
        messages = []
        with open(message_file, 'w') as f:
            json.dump(messages, f, indent=4)
        return messages
    
    with open(message_file, 'r') as f:
        return json.load(f)

# Save messages
def save_messages(messages):
    message_file = "breaker/data/messages/messages.json"
    with open(message_file, 'w') as f:
        json.dump(messages, f, indent=4)

# Format date from ISO format to user-friendly display
def format_date(iso_date):
    date_obj = datetime.fromisoformat(iso_date)
    return date_obj.strftime("%m/%d/%Y %I:%M %p")

# Generate a task ID
def generate_id():
    return datetime.now().strftime("%Y%m%d%H%M%S")

# Load SVG file
def load_svg(svg_path):
    # Create a default SVG for Circuit Breakers logo if file doesn't exist
    if not os.path.exists(svg_path):
        os.makedirs(os.path.dirname(svg_path), exist_ok=True)
        default_svg = """
        <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
            <circle cx="100" cy="100" r="90" fill="#1f1f1f" stroke="#00B4D8" stroke-width="5"/>
            <text x="100" y="90" font-family="Arial" font-size="18" fill="#00B4D8" text-anchor="middle">CIRCUIT</text>
            <text x="100" y="115" font-family="Arial" font-size="18" fill="#00B4D8" text-anchor="middle">BREAKERS</text>
            <path d="M80,130 L95,150 L110,130 L125,150" stroke="#C0C0C0" stroke-width="4" fill="none"/>
            <path d="M60,120 L140,120" stroke="#00B4D8" stroke-width="3" fill="none"/>
            <path d="M70,60 L130,60" stroke="#00B4D8" stroke-width="3" fill="none"/>
            <path d="M90,60 L90,120" stroke="#00B4D8" stroke-width="3" fill="none"/>
            <path d="M110,60 L110,120" stroke="#00B4D8" stroke-width="3" fill="none"/>
        </svg>
        """
        with open(svg_path, 'w') as f:
            f.write(default_svg.strip())
        return default_svg
    
    with open(svg_path, 'r') as f:
        return f.read()

# Initialize data directories when module is imported
initialize_data_directories()
