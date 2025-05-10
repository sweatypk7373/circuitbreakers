import streamlit as st
import pandas as pd
import hashlib
import json
import os
from datetime import datetime
from database import SessionLocal, User, get_db

# Keep JSON file as a backup/migration option
# Create directory for data storage if it doesn't exist
os.makedirs("data", exist_ok=True)

# Define user data file path (for backward compatibility)
USER_DATA_FILE = "data/users.json"

# Hash password function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Initialize the database with a default admin user if no users exist
def initialize_user_data():
    db = SessionLocal()
    try:
        # Check if any users exist
        user_count = db.query(User).count()
        if user_count == 0:
            # Create default admin user
            admin_user = User(
                username="admin",
                password=hash_password("admin123"),
                name="Admin User",
                role="admin",
                email="admin@circuitbreakers.org",
                created_at=datetime.now()
            )
            db.add(admin_user)
            db.commit()
            
            # For backward compatibility, also create the JSON file
            default_users = {
                "admin": {
                    "password": hash_password("admin123"),
                    "name": "Admin User",
                    "role": "admin",
                    "email": "admin@circuitbreakers.org",
                    "created_at": datetime.now().isoformat()
                }
            }
            with open(USER_DATA_FILE, 'w') as f:
                json.dump(default_users, f, indent=4)
            
            # Return dictionary format for backward compatibility
            all_users = {}
            for user in db.query(User).all():
                all_users[user.username] = {
                    "password": user.password,
                    "name": user.name,
                    "role": user.role,
                    "email": user.email,
                    "created_at": user.created_at.isoformat() if user.created_at else datetime.now().isoformat()
                }
            return all_users
        
        # Return all users as a dictionary for backward compatibility
        all_users = {}
        for user in db.query(User).all():
            all_users[user.username] = {
                "password": user.password,
                "name": user.name,
                "role": user.role,
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else datetime.now().isoformat(),
                "id": user.id
            }
        return all_users
    
    finally:
        db.close()

# Validate user credentials
def authenticate(username, password):
    try:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == username).first()
            
            if user and user.password == hash_password(password):
                return True, user.name, user.role, user.id
            return False, None, None, None
        
        except Exception as e:
            # If there's a database error, log it and try using the JSON file as fallback
            print(f"Database error during authentication: {str(e)}")
            
            # Fallback to JSON file
            if os.path.exists(USER_DATA_FILE):
                with open(USER_DATA_FILE, 'r') as f:
                    users = json.load(f)
                
                if username in users:
                    user_data = users[username]
                    if user_data.get('password') == hash_password(password):
                        return True, user_data.get('name', ''), user_data.get('role', 'member'), user_data.get('id', None)
            
            return False, None, None, None
        
        finally:
            db.close()
    except Exception as e:
        print(f"Critical error in authentication process: {str(e)}")
        return False, None, None, None

# Create new user
def create_user(username, password, name, email, role, department=None):
    # First, try to save to the database
    db_success = False
    
    try:
        db = SessionLocal()
        try:
            # Check if username exists
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                return False, "Username already exists"
            
            # Create new user
            new_user = User(
                username=username,
                password=hash_password(password),
                name=name,
                email=email,
                role=role,
                department=department,
                created_at=datetime.now()
            )
            
            db.add(new_user)
            db.commit()
            db_success = True
            
        except Exception as e:
            db.rollback()
            print(f"Database error when creating user: {str(e)}")
            # Continue to try saving to JSON file even if database fails
        finally:
            db.close()
    except Exception as e:
        print(f"Critical error in create_user database operation: {str(e)}")
    
    # For backward compatibility, and as a fallback, always update the JSON file
    json_success = False
    try:
        if os.path.exists(USER_DATA_FILE):
            try:
                with open(USER_DATA_FILE, 'r') as f:
                    users = json.load(f)
            except:
                users = {}
        else:
            users = {}
            
        users[username] = {
            "password": hash_password(password),
            "name": name,
            "role": role,
            "email": email,
            "department": department,
            "created_at": datetime.now().isoformat()
        }
        
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(users, f, indent=4)
        json_success = True
    except Exception as e:
        print(f"Error saving user to JSON file: {str(e)}")
    
    # Return success if either method worked
    if db_success or json_success:
        return True, "User created successfully"
    else:
        return False, "Error creating user: Could not save to database or JSON file"

# Show login page
def show_login_page():
    st.title("Circuit Breakers Team Hub")
    st.subheader("Login")
    
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
