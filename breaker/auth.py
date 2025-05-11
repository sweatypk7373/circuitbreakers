import streamlit as st
import pandas as pd
import hashlib
import json
import os
from datetime import datetime

# Create directory for data storage if it doesn't exist
os.makedirs("data", exist_ok=True)

# Define user data file path
USER_DATA_FILE = "breaker/data/users.json"

# Hash password function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize the database with a default admin user if no users exist
def initialize_user_data():
    # Check if user data file exists, if not create it with default admin
    if not os.path.exists(USER_DATA_FILE) or os.path.getsize(USER_DATA_FILE) == 0:
        default_users = {
            "admin": {
                "password": hash_password("admin123"),
                "name": "Admin User",
                "role": "admin",
                "email": "admin@circuitbreakers.org",
                "created_at": datetime.now().isoformat(),
                "id": 1
            }
        }
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(default_users, f, indent=4)
        return default_users

    # Otherwise, load existing users
    try:
        with open(USER_DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        # If there's an error reading the file, create a fresh one
        default_users = {
            "admin": {
                "password": hash_password("admin123"),
                "name": "Admin User",
                "role": "admin",
                "email": "admin@circuitbreakers.org",
                "created_at": datetime.now().isoformat(),
                "id": 1
            }
        }
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(default_users, f, indent=4)
        return default_users

# Validate user credentials
def authenticate(username, password):
    try:
        # Load users from JSON file
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'r') as f:
                users = json.load(f)
            
            if username in users:
                user_data = users[username]
                if user_data.get('password') == hash_password(password):
                    return True, user_data.get('name', ''), user_data.get('role', 'member'), user_data.get('id', None)
        
        return False, None, None, None
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return False, None, None, None

# Create new user
def create_user(username, password, name, email, role, department=None):
    try:
        # Load existing users
        if os.path.exists(USER_DATA_FILE):
            try:
                with open(USER_DATA_FILE, 'r') as f:
                    users = json.load(f)
            except:
                users = {}
        else:
            users = {}
        
        # Check if username exists
        if username in users:
            return False, "Username already exists"
        
        # Generate a new ID
        new_id = 1
        if users:
            # Find the highest ID and increment
            existing_ids = [user_data.get('id', 0) for user_data in users.values()]
            existing_ids = [id for id in existing_ids if id is not None]
            new_id = max(existing_ids) + 1 if existing_ids else 1
            
        # Create new user entry
        users[username] = {
            "password": hash_password(password),
            "name": name,
            "role": role,
            "email": email,
            "department": department,
            "created_at": datetime.now().isoformat(),
            "id": new_id
        }
        
        # Save users back to file
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(users, f, indent=4)
        
        return True, "User created successfully"
    except Exception as e:
        return False, f"Error creating user: {str(e)}"

# Show login page
def show_login_page():
    st.title("Circuit Breakers Team Hub")
    st.subheader("Login")
    
    # Ensure user data is initialized
    initialize_user_data()
    
    login_tab, about_tab = st.tabs(["Login", "About"])
    
    with login_tab:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if username and password:
                success, name, role, user_id = authenticate(username, password)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.user = name
                    st.session_state.role = role
                    st.session_state.user_id = user_id
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter both username and password")
    
    with about_tab:
        st.markdown("""
        ## Circuit Breakers STEM Racing Team
        
        This application serves as a centralized hub for the Circuit Breakers STEM racing team. 
        It provides tools for team communication, project management, build documentation, and outreach.
        
        ### Default Login
        - Username: admin
        - Password: admin123
        
        Please change these credentials after your first login.
        """)

# Show user registration form (admin only)
def show_user_registration():
    st.subheader("Create New User")
    
    new_username = st.text_input("Username", key="new_username")
    new_password = st.text_input("Password", type="password", key="new_password")
    confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
    full_name = st.text_input("Full Name", key="full_name")
    email = st.text_input("Email", key="email")
    role = st.selectbox("Role", ["member", "lead", "admin"], key="role")
    
    if st.button("Create User"):
        if new_password != confirm_password:
            st.error("Passwords do not match")
            return
        
        if not (new_username and new_password and full_name and email):
            st.warning("All fields are required")
            return
        
        success, message = create_user(new_username, new_password, full_name, email, role)
        if success:
            st.success(message)
        else:
            st.error(message)
