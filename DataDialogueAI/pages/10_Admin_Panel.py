import streamlit as st
import pandas as pd
import json
import os
import sys
import random
from datetime import datetime, timedelta
import hashlib
import plotly.express as px

# Add the parent directory to the path to import from the app root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import check_role_access, generate_id

# Page configuration
st.set_page_config(
    page_title="Admin Panel - Circuit Breakers",
    page_icon="⚙️",
    layout="wide"
)

# Check if user is authenticated and has admin role
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("Please login to access this page.")
    st.stop()

if not check_role_access(['admin']):
    st.error("You don't have permission to access the Admin Panel. This section is restricted to administrators.")
    st.stop()

# Page title
st.title("Admin Panel")
st.write("System administration, user management, and application settings")

# File paths
USER_DATA_FILE = "data/users.json"
APP_SETTINGS_FILE = "data/settings.json"

# Helper functions
def load_users():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    
    with open(USER_DATA_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def load_settings():
    if not os.path.exists(APP_SETTINGS_FILE):
        # Create default settings
        default_settings = {
            "app_name": "Circuit Breakers Team Hub",
            "team_logo": "assets/logo.svg",
            "primary_color": "#00B4D8",  # Electric Blue
            "contact_email": "admin@circuitbreakers.org",
            "competition_date": (datetime.now() + timedelta(days=90)).isoformat(),
            "competition_name": "Regional STEM Racing Championship",
            "enable_notifications": True,
            "message_retention_days": 180,
            "last_backup": None
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(APP_SETTINGS_FILE), exist_ok=True)
        
        with open(APP_SETTINGS_FILE, 'w') as f:
            json.dump(default_settings, f, indent=4)
        
        return default_settings
    
    with open(APP_SETTINGS_FILE, 'r') as f:
        return json.load(f)

def save_settings(settings):
    with open(APP_SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Load data
users = load_users()
settings = load_settings()

# Create tabs for different admin functions
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard", "User Management", "App Settings", "System Maintenance", "Logs & Activity"])

with tab1:
    st.subheader("Admin Dashboard")
    
    # Create metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    # Count users by role
    admin_count = sum(1 for user in users.values() if user.get('role') == 'admin')
    lead_count = sum(1 for user in users.values() if user.get('role') == 'lead')
    member_count = sum(1 for user in users.values() if user.get('role') == 'member')
    total_users = len(users)
    
    with col1:
        st.metric("Total Users", total_users)
    
    with col2:
        st.metric("Admin Users", admin_count)
    
    with col3:
        st.metric("Team Leads", lead_count)
    
    with col4:
        st.metric("Team Members", member_count)
    
    # System status
    st.subheader("System Status")
    
    # Mock status checks (in a real app, these would do actual checks)
    status_checks = {
        "Database Connection": {"status": "Operational", "details": "Connected to user database"},
        "File Storage": {"status": "Operational", "details": "1.2 GB used (40%)"},
        "Task Scheduler": {"status": "Operational", "details": "Next scheduled task: Daily backup at midnight"},
        "Email Notifications": {"status": "Warning", "details": "SMTP configuration incomplete"}
    }
    
    # Create status table
    status_data = []
    for service, details in status_checks.items():
        status = details["status"]
        status_emoji = "✅" if status == "Operational" else "⚠️" if status == "Warning" else "❌"
        
        status_data.append({
            "Service": service,
            "Status": f"{status_emoji} {status}",
            "Details": details["details"]
        })
    
    status_df = pd.DataFrame(status_data)
    st.dataframe(status_df, use_container_width=True)
    
    # Recent activity
    st.subheader("Recent System Activity")
    
    # In a real app, this would load from logs
    activity_data = [
        {"timestamp": (datetime.now() - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"), 
         "user": "admin", "action": "Updated system settings", "ip": "192.168.1.5"},
        {"timestamp": (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"), 
         "user": "maria.garcia", "action": "Added new sponsor", "ip": "192.168.1.10"},
        {"timestamp": (datetime.now() - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"), 
         "user": "jamal.williams", "action": "Uploaded new resource document", "ip": "192.168.1.15"},
        {"timestamp": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"), 
         "user": "admin", "action": "Created new user account", "ip": "192.168.1.5"},
        {"timestamp": (datetime.now() - timedelta(days=1, hours=6)).strftime("%Y-%m-%d %H:%M:%S"), 
         "user": "sarah.chen", "action": "Modified calendar event", "ip": "192.168.1.20"}
    ]
    
    activity_df = pd.DataFrame(activity_data)
    st.dataframe(activity_df, use_container_width=True)
    
    # User registration over time
    st.subheader("User Registration Over Time")
    
    # Extract registration dates from users
    registration_dates = []
    for username, user_data in users.items():
        if 'created_at' in user_data:
            registration_dates.append({
                "username": username,
                "date": datetime.fromisoformat(user_data['created_at']).date(),
                "role": user_data.get('role', 'member')
            })
    
    if registration_dates:
        # Create DataFrame for visualization
        reg_df = pd.DataFrame(registration_dates)
        
        # Sort by date
        reg_df = reg_df.sort_values("date")
        
        # Create cumulative count
        reg_df['count'] = range(1, len(reg_df) + 1)
        
        # Create line chart
        st.line_chart(reg_df.set_index('date')['count'])
    else:
        st.info("No user registration data available.")

with tab2:
    st.subheader("User Management")
    
    # Create a table of all users
    user_data = []
    for username, user_info in users.items():
        user_data.append({
            "Username": username,
            "Name": user_info.get('name', 'Unknown'),
            "Email": user_info.get('email', ''),
            "Role": user_info.get('role', 'member').capitalize(),
            "Department": user_info.get('department', 'Unassigned'),
            "Last Login": "N/A"  # In a real app, this would track login timestamps
        })
    
    user_df = pd.DataFrame(user_data)
    
    # Display table with filters
    st.markdown("### User Accounts")
    
    # Add search functionality
    user_search = st.text_input("Search users", key="user_search")
    
    # Filter user data based on search term
    if user_search:
        search_term = user_search.lower()
        filtered_user_df = user_df[
            user_df['Username'].str.lower().str.contains(search_term) | 
            user_df['Name'].str.lower().str.contains(search_term) | 
            user_df['Email'].str.lower().str.contains(search_term) | 
            user_df['Role'].str.lower().str.contains(search_term) | 
            user_df['Department'].str.lower().str.contains(search_term)
        ]
    else:
        filtered_user_df = user_df
    
    # Display the filtered user table
    st.dataframe(filtered_user_df, use_container_width=True)
    
    # User actions
    st.markdown("### User Actions")
    
    # New User Creation
    with st.expander("Create New User"):
        with st.form("new_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username*")
                new_password = st.text_input("Password*", type="password")
                confirm_password = st.text_input("Confirm Password*", type="password")
            
            with col2:
                full_name = st.text_input("Full Name*")
                email = st.text_input("Email*")
                role = st.selectbox("Role*", ["admin", "lead", "member"], format_func=lambda x: x.capitalize())
                department = st.selectbox("Department", ["", "Engineering", "Design", "Electrical", "Software", "Outreach", "Media", "Safety", "Management"])
            
            submit_new_user = st.form_submit_button("Create User")
            
            if submit_new_user:
                if not new_username or not new_password or not full_name or not email:
                    st.error("All fields marked with * are required!")
                elif new_password != confirm_password:
                    st.error("Passwords do not match!")
                elif new_username in users:
                    st.error(f"Username '{new_username}' already exists!")
                else:
                    # Create new user
                    new_user = {
                        'name': full_name,
                        'email': email,
                        'role': role,
                        'password': hash_password(new_password),
                        'department': department,
                        'created_at': datetime.now().isoformat()
                    }
                    
                    users[new_username] = new_user
                    save_users(users)
                    
                    st.success(f"User '{new_username}' created successfully!")
                    st.rerun()
    
    # Edit User
    with st.expander("Edit Existing User"):
        # Select user to edit
        edit_username = st.selectbox(
            "Select User to Edit",
            list(users.keys()),
            format_func=lambda x: f"{x} ({users[x].get('name', 'Unknown')})"
        )
        
        if edit_username:
            user_to_edit = users[edit_username]
            
            with st.form("edit_user_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    edit_name = st.text_input("Full Name", value=user_to_edit.get('name', ''))
                    edit_email = st.text_input("Email", value=user_to_edit.get('email', ''))
                    
                    # Don't allow changing the last admin to a different role
                    admin_count = sum(1 for user in users.values() if user.get('role') == 'admin')
                    disable_role = user_to_edit.get('role') == 'admin' and admin_count <= 1
                    
                    current_role_index = ["admin", "lead", "member"].index(user_to_edit.get('role', 'member'))
                    edit_role = st.selectbox(
                        "Role", 
                        ["admin", "lead", "member"], 
                        index=current_role_index,
                        format_func=lambda x: x.capitalize(),
                        disabled=disable_role
                    )
                    
                    if disable_role:
                        st.info("Cannot change role of the last admin user.")
                
                with col2:
                    dept_options = ["", "Engineering", "Design", "Electrical", "Software", "Outreach", "Media", "Safety", "Management"]
                    current_dept = user_to_edit.get('department', '')
                    dept_index = dept_options.index(current_dept) if current_dept in dept_options else 0
                    
                    edit_department = st.selectbox("Department", dept_options, index=dept_index)
                    reset_password = st.checkbox("Reset Password")
                    
                    if reset_password:
                        new_password = st.text_input("New Password", type="password")
                        confirm_new_password = st.text_input("Confirm New Password", type="password")
                
                submit_edit = st.form_submit_button("Save Changes")
                
                if submit_edit:
                    if not edit_name or not edit_email:
                        st.error("Name and email are required!")
                    elif reset_password and not new_password:
                        st.error("New password is required when resetting password!")
                    elif reset_password and new_password != confirm_new_password:
                        st.error("Passwords do not match!")
                    else:
                        # Update user
                        users[edit_username]['name'] = edit_name
                        users[edit_username]['email'] = edit_email
                        users[edit_username]['role'] = edit_role
                        users[edit_username]['department'] = edit_department
                        
                        if reset_password:
                            users[edit_username]['password'] = hash_password(new_password)
                        
                        save_users(users)
                        
                        st.success(f"User '{edit_username}' updated successfully!")
                        st.rerun()
    
    # Delete User
    with st.expander("Delete User"):
        # Select user to delete
        delete_username = st.selectbox(
            "Select User to Delete",
            list(users.keys()),
            format_func=lambda x: f"{x} ({users[x].get('name', 'Unknown')})"
        )
        
        if delete_username:
            user_to_delete = users[delete_username]
            
            # Don't allow deleting the last admin
            admin_count = sum(1 for user in users.values() if user.get('role') == 'admin')
            if user_to_delete.get('role') == 'admin' and admin_count <= 1:
                st.error("Cannot delete the last admin user!")
            else:
                st.warning(f"Are you sure you want to delete user '{delete_username}' ({user_to_delete.get('name', 'Unknown')})? This cannot be undone!")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Confirm Delete"):
                        del users[delete_username]
                        save_users(users)
                        
                        st.success(f"User '{delete_username}' deleted successfully!")
                        st.rerun()
                with col2:
                    if st.button("Cancel"):
                        st.rerun()
    
    # User role distribution chart
    st.markdown("### User Role Distribution")
    
    # Count roles
    role_counts = {"admin": 0, "lead": 0, "member": 0}
    for user_data in users.values():
        role = user_data.get('role', 'member')
        if role in role_counts:
            role_counts[role] += 1
        else:
            role_counts['member'] += 1
    
    # Create dataframe for visualization
    role_df = pd.DataFrame({
        "Role": [role.capitalize() for role in role_counts.keys()],
        "Count": list(role_counts.values())
    })
    
    # Create a pie chart
    st.bar_chart(role_df.set_index("Role"))

with tab3:
    st.subheader("Application Settings")
    
    # General Settings
    with st.expander("General Settings", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            app_name = st.text_input("Application Name", value=settings.get('app_name', 'Circuit Breakers Team Hub'))
            contact_email = st.text_input("Contact Email", value=settings.get('contact_email', 'admin@circuitbreakers.org'))
        
        with col2:
            # These would handle actual file uploads in a real application
            st.text_input("Team Logo Path", value=settings.get('team_logo', 'assets/logo.svg'), disabled=True)
            st.file_uploader("Upload New Logo", type=["svg", "png"])
            
            primary_color = st.color_picker("Primary Color", value=settings.get('primary_color', '#00B4D8'))
        
        # Competition settings
        st.subheader("Competition Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            competition_name = st.text_input("Competition Name", value=settings.get('competition_name', 'Regional STEM Racing Championship'))
        
        with col2:
            # Parse the date from ISO format if it exists
            if 'competition_date' in settings:
                competition_date_default = datetime.fromisoformat(settings['competition_date']).date()
            else:
                competition_date_default = (datetime.now() + timedelta(days=90)).date()
            
            competition_date = st.date_input("Competition Date", value=competition_date_default)
        
        # Save general settings
        if st.button("Save General Settings"):
            # Update settings
            settings['app_name'] = app_name
            settings['contact_email'] = contact_email
            settings['primary_color'] = primary_color
            settings['competition_name'] = competition_name
            settings['competition_date'] = datetime.combine(competition_date, datetime.min.time()).isoformat()
            
            save_settings(settings)
            
            st.success("Settings saved successfully!")
    
    # Notification Settings
    with st.expander("Notification Settings"):
        enable_notifications = st.checkbox("Enable System Notifications", value=settings.get('enable_notifications', True))
        notification_types = st.multiselect(
            "Notification Types",
            ["Task assignments", "Calendar events", "Build log updates", "New resources", "Team messages", "Sponsor updates"],
            default=settings.get('notification_types', ["Task assignments", "Calendar events", "Team messages"])
        )
        
        # Email notification settings
        st.subheader("Email Notifications")
        
        enable_emails = st.checkbox("Enable Email Notifications", value=settings.get('enable_emails', False))
        
        if enable_emails:
            col1, col2 = st.columns(2)
            
            with col1:
                smtp_server = st.text_input("SMTP Server", value=settings.get('smtp_server', ''))
                smtp_port = st.number_input("SMTP Port", value=settings.get('smtp_port', 587), min_value=1, max_value=65535)
            
            with col2:
                smtp_username = st.text_input("SMTP Username", value=settings.get('smtp_username', ''))
                smtp_password = st.text_input("SMTP Password", type="password", value=settings.get('smtp_password', ''))
            
            smtp_use_tls = st.checkbox("Use TLS", value=settings.get('smtp_use_tls', True))
        
        # Save notification settings
        if st.button("Save Notification Settings"):
            # Update settings
            settings['enable_notifications'] = enable_notifications
            settings['notification_types'] = notification_types
            settings['enable_emails'] = enable_emails
            
            if enable_emails:
                settings['smtp_server'] = smtp_server
                settings['smtp_port'] = smtp_port
                settings['smtp_username'] = smtp_username
                settings['smtp_password'] = smtp_password
                settings['smtp_use_tls'] = smtp_use_tls
            
            save_settings(settings)
            
            st.success("Notification settings saved successfully!")
    
    # Data Retention Settings
    with st.expander("Data Retention Settings"):
        message_retention = st.number_input(
            "Message Retention (days)",
            min_value=30,
            max_value=365,
            value=settings.get('message_retention_days', 180),
            help="How long to keep messages before automatic archiving"
        )
        
        log_retention = st.number_input(
            "System Log Retention (days)",
            min_value=30,
            max_value=365,
            value=settings.get('log_retention_days', 90),
            help="How long to keep system logs before automatic deletion"
        )
        
        # Save data retention settings
        if st.button("Save Data Retention Settings"):
            # Update settings
            settings['message_retention_days'] = message_retention
            settings['log_retention_days'] = log_retention
            
            save_settings(settings)
            
            st.success("Data retention settings saved successfully!")
    
    # Custom Fields Settings
    with st.expander("Custom Fields"):
        st.markdown("Configure custom fields for different sections of the application.")
        
        # Task custom fields
        st.subheader("Task Custom Fields")
        
        task_fields = settings.get('task_custom_fields', [])
        
        # Display existing fields
        if task_fields:
            task_field_data = pd.DataFrame(task_fields)
            st.dataframe(task_field_data, use_container_width=True)
        
        # Add new field
        st.markdown("### Add New Task Field")
        
        with st.form("add_task_field"):
            col1, col2 = st.columns(2)
            
            with col1:
                field_name = st.text_input("Field Name", key="task_field_name")
                field_type = st.selectbox("Field Type", ["Text", "Number", "Date", "Dropdown", "Checkbox"])
            
            with col2:
                field_required = st.checkbox("Required Field")
                field_description = st.text_input("Field Description")
            
            # Additional options for dropdown type
            if field_type == "Dropdown":
                dropdown_options = st.text_input("Dropdown Options (comma separated)", help="Example: Option 1, Option 2, Option 3")
            
            submit_field = st.form_submit_button("Add Field")
            
            if submit_field:
                if not field_name:
                    st.error("Field name is required!")
                elif field_type == "Dropdown" and not dropdown_options:
                    st.error("Dropdown options are required for dropdown fields!")
                else:
                    # Create new field
                    new_field = {
                        "name": field_name,
                        "type": field_type,
                        "required": field_required,
                        "description": field_description
                    }
                    
                    if field_type == "Dropdown":
                        new_field["options"] = [opt.strip() for opt in dropdown_options.split(",") if opt.strip()]
                    
                    # Add to settings
                    if 'task_custom_fields' not in settings:
                        settings['task_custom_fields'] = []
                    
                    settings['task_custom_fields'].append(new_field)
                    save_settings(settings)
                    
                    st.success("Custom field added successfully!")
                    st.rerun()

with tab4:
    st.subheader("System Maintenance")
    
    # Database Backup
    with st.expander("Database Backup & Restore", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Create Backup")
            
            backup_name = st.text_input("Backup Name", value=f"circuit_breakers_backup_{datetime.now().strftime('%Y%m%d')}")
            include_media = st.checkbox("Include Media Files", value=True)
            
            if st.button("Create Backup"):
                # In a real application, this would create an actual backup
                st.info("Creating backup... (This is a simulation)")
                
                # Update last backup time
                settings['last_backup'] = datetime.now().isoformat()
                save_settings(settings)
                
                # Show success message
                st.success("Backup created successfully!")
                st.markdown(f"Backup saved as: {backup_name}.zip (simulated)")
        
        with col2:
            st.markdown("### Restore from Backup")
            
            # In a real app, this would show actual backups
            backup_options = [
                f"circuit_breakers_backup_{(datetime.now() - timedelta(days=i)).strftime('%Y%m%d')}" 
                for i in range(5)
            ]
            
            selected_backup = st.selectbox("Select Backup", backup_options)
            
            st.warning("Restoring from backup will overwrite current data. This cannot be undone!")
            
            if st.button("Restore Backup"):
                # In a real application, this would restore from the backup
                st.info("Restoring from backup... (This is a simulation)")
                
                # Show success message after a short delay
                st.success("Restore completed successfully! (simulated)")
    
    # Data Management
    with st.expander("Data Management"):
        st.markdown("### Data Cleanup")
        
        cleanup_options = [
            "Remove expired sponsors",
            "Archive completed tasks older than 90 days",
            "Delete temporary files",
            "Optimize database"
        ]
        
        selected_cleanup = st.multiselect("Select Cleanup Operations", cleanup_options)
        
        if st.button("Run Cleanup") and selected_cleanup:
            # In a real application, this would perform the selected cleanup operations
            st.info("Running cleanup operations... (This is a simulation)")
            
            for operation in selected_cleanup:
                st.write(f"Completed: {operation}")
            
            st.success("Cleanup operations completed successfully! (simulated)")
        
        st.markdown("### Reset Application")
        
        st.error("⚠️ DANGER ZONE: These operations cannot be undone!")
        
        reset_options = [
            "Reset user data (preserves admin account)",
            "Reset all calendar events",
            "Reset tasks and logs",
            "Reset media gallery",
            "Reset sponsors",
            "Factory reset (all data)"
        ]
        
        selected_reset = st.selectbox("Select Reset Operation", ["Select an option..."] + reset_options)
        
        if selected_reset != "Select an option...":
            confirmation_text = st.text_input("Type 'CONFIRM' to proceed:")
            
            if st.button("Execute Reset") and confirmation_text == "CONFIRM":
                # In a real application, this would perform the reset operation
                st.info(f"Executing: {selected_reset}... (This is a simulation)")
                
                # Show success message
                st.success("Reset operation completed successfully! (simulated)")
    
    # System Information
    with st.expander("System Information"):
        st.markdown("### System Details")
        
        # In a real application, these would be actual system values
        system_info = {
            "Application Version": "1.0.0",
            "Streamlit Version": "1.20.0",
            "Python Version": "3.9.7",
            "Operating System": "Linux",
            "Database": "File-based JSON",
            "Total User Count": len(users),
            "Total Storage Used": "512 MB",
            "Available Storage": "2.5 GB",
            "Last Backup": settings.get('last_backup', 'Never') if settings.get('last_backup') else 'Never'
        }
        
        # Convert last backup from ISO to readable format if it exists
        if system_info["Last Backup"] != 'Never':
            last_backup_date = datetime.fromisoformat(system_info["Last Backup"])
            system_info["Last Backup"] = last_backup_date.strftime("%Y-%m-%d %H:%M:%S")
        
        # Display as table
        system_df = pd.DataFrame({
            "Property": list(system_info.keys()),
            "Value": list(system_info.values())
        })
        
        st.dataframe(system_df, use_container_width=True)

with tab5:
    st.subheader("System Logs & Activity")
    
    # Log filtering options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        log_type = st.selectbox("Log Type", ["All Logs", "User Activity", "System Events", "Errors", "Security"])
    
    with col2:
        log_period = st.selectbox("Time Period", ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"])
    
    with col3:
        log_user = st.selectbox("Filter by User", ["All Users"] + list(users.keys()))
    
    # Generate sample log data (in a real app, this would come from actual logs)
    logs = []
    
    # Map log period to days
    if log_period == "Last 24 Hours":
        days_back = 1
    elif log_period == "Last 7 Days":
        days_back = 7
    elif log_period == "Last 30 Days":
        days_back = 30
    else:  # All Time
        days_back = 365
    
    # Sample log types and messages
    log_types = {
        "User Activity": ["User login", "User logout", "Profile updated", "Password changed", "Created new resource", "Updated task"],
        "System Events": ["Backup completed", "Cleanup operation", "Settings updated", "System restart", "Database optimized"],
        "Errors": ["Database connection failed", "File not found", "Permission denied", "Invalid configuration", "API timeout"],
        "Security": ["Failed login attempt", "Password reset", "Role changed", "Access denied", "New admin user created"]
    }
    
    # Generate sample logs
    for i in range(50):  # Generate 50 sample logs
        # Random time within the selected period
        log_time = datetime.now() - timedelta(days=random.random() * days_back)
        
        # Random log type
        if log_type == "All Logs":
            selected_type = random.choice(list(log_types.keys()))
        else:
            selected_type = log_type
        
        # Skip if the type doesn't match our filter (except for "All Logs")
        if log_type != "All Logs" and selected_type != log_type:
            continue
        
        # Random user
        if log_user == "All Users":
            selected_user = random.choice(list(users.keys()) + ["system"])
        else:
            selected_user = log_user
        
        # Skip if the user doesn't match our filter (except for "All Users")
        if log_user != "All Users" and selected_user != log_user:
            continue
        
        # Random message based on type
        if selected_type in log_types:
            message = random.choice(log_types[selected_type])
        else:
            message = "Unknown event"
        
        # IP address (random for demonstration)
        ip = f"192.168.1.{random.randint(1, 254)}"
        
        logs.append({
            "Timestamp": log_time.strftime("%Y-%m-%d %H:%M:%S"),
            "Type": selected_type,
            "User": selected_user,
            "Message": message,
            "IP Address": ip
        })
    
    # Sort logs by timestamp (newest first)
    logs.sort(key=lambda x: x["Timestamp"], reverse=True)
    
    # Display logs
    if logs:
        logs_df = pd.DataFrame(logs)
        st.dataframe(logs_df, use_container_width=True)
        
        # Export options
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export Logs to CSV"):
                # In a real app, this would create an actual CSV file
                st.success("Logs exported successfully! (simulated)")
        
        with col2:
            if st.button("Clear Displayed Logs"):
                st.rerun()
    else:
        st.info("No logs found matching the selected filters.")
    
    # Log statistics
    st.subheader("Log Statistics")
    
    if logs:
        # Count by type
        type_counts = {}
        for log in logs:
            log_type = log["Type"]
            if log_type in type_counts:
                type_counts[log_type] += 1
            else:
                type_counts[log_type] = 1
        
        # Create dataframe for visualization
        type_df = pd.DataFrame({
            "Log Type": list(type_counts.keys()),
            "Count": list(type_counts.values())
        })
        
        # Create a bar chart
        st.bar_chart(type_df.set_index("Log Type"))
    else:
        st.info("No log data available for statistics.")

st.caption("Circuit Breakers Team Hub - Admin Panel")
