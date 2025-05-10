import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime
import hashlib

# Add the parent directory to the path to import from the app root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import check_role_access, generate_id

# Global variable to store users data
users = {}

# Import database functionality
database_available = False
try:
    from database import SessionLocal, User
    import auth

    database_available = True
except Exception as e:
    st.warning(f"Database connection not available: {str(e)}")

# Page configuration
st.set_page_config(
    page_title="Team Profiles - Circuit Breakers",
    page_icon="👥",
    layout="wide"
)

# Check if user is authenticated
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("Please login to access this page.")
    st.stop()

# Page title
st.title("Team Profiles")
st.write("Team member information, roles, and contact details")

# Define roles and departments
TEAM_ROLES = ["member", "lead", "admin"]
TEAM_DEPARTMENTS = ["Engineering", "Design", "Electrical", "Software", "Outreach", "Media", "Safety", "Management"]

# Initialize session state for member form
if 'show_member_form' not in st.session_state:
    st.session_state.show_member_form = False
if 'editing_member' not in st.session_state:
    st.session_state.editing_member = None
if 'member_search' not in st.session_state:
    st.session_state.member_search = ""
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "cards"  # or "table"


# Load team members
def get_user_data_file():
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return os.path.join(data_dir, "users.json")


def load_users():
    global users

    # Only try database if available
    if database_available:
        try:
            # First try to load from database
            db = SessionLocal()
            try:
                # Load users from database
                db_users = db.query(User).all()

                # Create dictionary structure
                users_dict = {}
                for db_user in db_users:
                    users_dict[db_user.username] = {
                        'name': db_user.name,
                        'email': db_user.email,
                        'role': db_user.role,
                        'password': db_user.password,
                        'department': db_user.department,
                        'created_at': db_user.created_at.isoformat() if db_user.created_at else datetime.now().isoformat()
                    }

                # If database has users, return them
                if users_dict:
                    return users_dict
            except Exception as e:
                st.warning(f"Error loading users from database: {str(e)}. Falling back to JSON file.")
            finally:
                db.close()
        except:
            pass

    # As fallback, load from JSON file
    user_data_file = get_user_data_file()
    if not os.path.exists(user_data_file):
        # If file doesn't exist, return default admin user
        default_users = {
            "admin": {
                "name": "Administrator",
                "email": "admin@example.com",
                "role": "admin",
                "password": hashlib.sha256("admin123".encode()).hexdigest(),
                "department": "Management",
                "created_at": datetime.now().isoformat()
            }
        }
        # Save default users to file
        with open(user_data_file, 'w') as f:
            json.dump(default_users, f, indent=4)
        return default_users

    try:
        with open(user_data_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading user data: {str(e)}")
        return {}


def save_users(user_data):
    global users
    users = user_data

    # Save to JSON file (for backward compatibility)
    user_data_file = get_user_data_file()
    with open(user_data_file, 'w') as f:
        json.dump(user_data, f, indent=4)

    # Only try database if available
    if database_available:
        try:
            # Also save to database
            db = SessionLocal()
            try:
                for username, user_data in user_data.items():
                    # Check if user exists in database
                    db_user = db.query(User).filter(User.username == username).first()

                    if db_user:
                        # Update existing user
                        db_user.name = user_data.get('name', '')
                        db_user.email = user_data.get('email', '')
                        db_user.role = user_data.get('role', 'member')
                        db_user.department = user_data.get('department', None)
                        # Only update password if it's changed
                        if 'password' in user_data:
                            db_user.password = user_data['password']
                    else:
                        # Create new user
                        new_user = User(
                            username=username,
                            password=user_data.get('password', ''),
                            name=user_data.get('name', ''),
                            email=user_data.get('email', ''),
                            role=user_data.get('role', 'member'),
                            department=user_data.get('department', None),
                            created_at=datetime.fromisoformat(user_data.get('created_at', datetime.now().isoformat()))
                        )
                        db.add(new_user)

                db.commit()
            except Exception as e:
                db.rollback()
                st.error(f"Error saving to database: {str(e)}")
            finally:
                db.close()
        except:
            st.warning("Changes saved to JSON file only. Database not available.")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Load users data
users = load_users()


# Function to toggle member form visibility
def toggle_member_form():
    st.session_state.show_member_form = not st.session_state.show_member_form
    st.session_state.editing_member = None


# Function to edit an existing member
def edit_member(username):
    st.session_state.editing_member = username
    st.session_state.show_member_form = True


# Function to delete a member
def delete_member(username):
    global users

    if not check_role_access(['admin']):
        st.error("You don't have permission to delete team members.")
        return

    if username in users:
        # Don't allow deleting the last admin
        admin_count = sum(1 for user in users.values() if user.get('role') == 'admin')
        if users[username].get('role') == 'admin' and admin_count <= 1:
            st.error("Cannot delete the last admin user.")
            return

        # Delete from JSON user object
        users.pop(username)

        # Delete from database if available
        if database_available:
            try:
                db = SessionLocal()
                try:
                    # Find user in database
                    db_user = db.query(User).filter(User.username == username).first()
                    if db_user:
                        db.delete(db_user)
                        db.commit()
                except Exception as e:
                    db.rollback()
                    st.error(f"Error deleting user from database: {str(e)}")
                finally:
                    db.close()
            except:
                pass

        # Save updated JSON
        save_users(users)
        st.success(f"User {username} deleted successfully!")
        st.rerun()
    else:
        st.error(f"User {username} not found.")


# Create top action buttons
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    # Only admin can add team members
    if check_role_access(['admin']):
        if st.button("Add New Team Member 👤"):
            toggle_member_form()

with col2:
    # Toggle view mode
    view_options = ["Card View", "Table View"]
    selected_view = st.radio("View Mode", view_options, horizontal=True,
                             index=0 if st.session_state.view_mode == "cards" else 1)

    if selected_view == "Card View":
        st.session_state.view_mode = "cards"
    else:
        st.session_state.view_mode = "table"

with col3:
    st.session_state.member_search = st.text_input("Search team members...", value=st.session_state.member_search)

# Create tabs
tab1, tab2 = st.tabs(["All Team Members", "Team Structure"])

with tab1:
    # Filter members based on search term
    filtered_members = []

    for username, user_data in users.items():
        if st.session_state.member_search.lower() in username.lower() or \
                st.session_state.member_search.lower() in user_data.get('name', '').lower() or \
                st.session_state.member_search.lower() in user_data.get('role', '').lower() or \
                st.session_state.member_search.lower() in user_data.get('email', '').lower() or \
                st.session_state.member_search.lower() in user_data.get('department', '').lower():
            # Add username to user_data for convenience
            member_info = user_data.copy()
            member_info['username'] = username
            filtered_members.append(member_info)

    # Filter options
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        filter_role = st.multiselect("Filter by Role", ["All"] + TEAM_ROLES, default=["All"])

    with filter_col2:
        # Get unique departments from users
        all_departments = set()
        for user_data in users.values():
            if 'department' in user_data and user_data['department']:
                all_departments.add(user_data['department'])

        filter_department = st.multiselect("Filter by Department", ["All"] + list(all_departments), default=["All"])

    with filter_col3:
        sort_options = ["Name (A-Z)", "Role", "Department", "Join Date"]
        sort_by = st.selectbox("Sort by", sort_options)

    # Apply filters
    # Role filter
    if not ("All" in filter_role or len(filter_role) == 0):
        filtered_members = [member for member in filtered_members if member.get('role', '') in filter_role]

    # Department filter
    if not ("All" in filter_department or len(filter_department) == 0):
        filtered_members = [member for member in filtered_members if member.get('department', '') in filter_department]

    # Apply sorting
    if sort_by == "Name (A-Z)":
        filtered_members.sort(key=lambda x: x.get('name', '').lower())
    elif sort_by == "Role":
        # Define role order for sorting
        role_order = {"admin": 0, "lead": 1, "member": 2}
        filtered_members.sort(key=lambda x: role_order.get(x.get('role', ''), 999))
    elif sort_by == "Department":
        filtered_members.sort(key=lambda x: x.get('department', '').lower())
    elif sort_by == "Join Date":
        filtered_members.sort(key=lambda x: x.get('created_at', ''), reverse=True)

    # Display members based on view mode
    if st.session_state.view_mode == "cards":
        if filtered_members:
            # Display in a grid of cards
            num_cols = 3
            for i in range(0, len(filtered_members), num_cols):
                cols = st.columns(num_cols)
                for j in range(num_cols):
                    idx = i + j
                    if idx < len(filtered_members):
                        member = filtered_members[idx]
                        with cols[j]:
                            # Get role color
                            role_colors = {
                                "admin": "#dc3545",  # red
                                "lead": "#fd7e14",  # orange
                                "member": "#28a745"  # green
                            }
                            role_color = role_colors.get(member.get('role', 'member'), "#6c757d")

                            # Create card
                            with st.container():
                                st.markdown(
                                    f"""
                                    <div style="border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 15px;">
                                        <h3 style="margin-top: 0;">
                                            {member.get('name', 'Unknown')}
                                            <span style="background-color: {role_color}; padding: 2px 8px; border-radius: 10px; color: white; font-size: 0.7em; vertical-align: middle; margin-left: 5px;">
                                                {member.get('role', 'member').upper()}
                                            </span>
                                        </h3>
                                        <p><strong>Username:</strong> {member.get('username')}</p>
                                        <p><strong>Email:</strong> {member.get('email', 'No email provided')}</p>
                                        <p><strong>Department:</strong> {member.get('department', 'Unassigned')}</p>
                                    """,
                                    unsafe_allow_html=True
                                )

                                # Show skills if available
                                if 'skills' in member and member['skills']:
                                    skills_list = ', '.join(member['skills'])
                                    st.markdown(f"**Skills:** {skills_list}")

                                # Show join date if available
                                if 'created_at' in member:
                                    try:
                                        created_at = datetime.fromisoformat(member['created_at'])
                                        st.markdown(f"**Joined:** {created_at.strftime('%B %d, %Y')}")
                                    except:
                                        st.markdown(f"**Joined:** Unknown")

                                # Add action buttons if admin
                                if check_role_access(['admin']):
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.button("Edit", key=f"edit_{member['username']}"):
                                            edit_member(member['username'])
                                    with col2:
                                        if st.button("Delete", key=f"delete_{member['username']}"):
                                            delete_member(member['username'])
        else:
            st.info("No team members found matching your search criteria.")
    else:
        # Table view
        if filtered_members:
            # Convert to DataFrame
            members_df = pd.DataFrame(filtered_members)

            # Format columns for display
            if 'created_at' in members_df.columns:
                members_df['created_at'] = members_df['created_at'].apply(
                    lambda x: datetime.fromisoformat(x).strftime('%Y-%m-%d') if x else "Unknown"
                )

            # Select columns to display
            display_columns = ['username', 'name', 'email', 'role', 'department']
            if 'created_at' in members_df.columns:
                display_columns.append('created_at')

            # Rename columns for display
            columns_display = {
                'username': 'Username',
                'name': 'Name',
                'email': 'Email',
                'role': 'Role',
                'department': 'Department',
                'created_at': 'Joined Date'
            }

            # Keep only the columns to display and that exist in the DataFrame
            display_columns = [col for col in display_columns if col in members_df.columns]

            # Rename columns
            display_df = members_df[display_columns].rename(columns=columns_display)


            # Apply color to roles
            def style_role(val):
                if val == 'admin':
                    return 'background-color: #ffcccc'
                elif val == 'lead':
                    return 'background-color: #ffedcc'
                else:
                    return 'background-color: #deffcc'


            # Display table
            st.dataframe(display_df.style.applymap(style_role, subset=['Role']), use_container_width=True)

            # Action buttons for table view
            if check_role_access(['admin']):
                st.subheader("Team Member Actions")
                action_col1, action_col2 = st.columns(2)

                with action_col1:
                    selected_user = st.selectbox("Select Team Member",
                                                 options=[f"{member.get('name', 'Unknown')} ({member.get('username')})"
                                                          for member in filtered_members])

                with action_col2:
                    action_options = ["Edit", "Delete"]
                    selected_action = st.selectbox("Select Action", action_options)

                if st.button("Perform Action"):
                    # Extract username from selection
                    selected_username = selected_user.split('(')[-1].split(')')[0]

                    if selected_action == "Edit":
                        edit_member(selected_username)
                    elif selected_action == "Delete":
                        delete_member(selected_username)
        else:
            st.info("No team members found matching your search criteria.")

with tab2:
    # Team structure visualization
    st.subheader("Team Hierarchy")

    # Group members by department
    departments = {}
    for username, user_data in users.items():
        dept = user_data.get('department', 'Unassigned')
        if dept not in departments:
            departments[dept] = []

        # Add user to department list with role info
        user_info = {
            'username': username,
            'name': user_data.get('name', 'Unknown'),
            'role': user_data.get('role', 'member')
        }
        departments[dept].append(user_info)

    # Sort departments alphabetically - handle None values
    # Replace None with "Unassigned" to avoid sorting errors
    departments_to_sort = list(departments.keys())
    for i, dept in enumerate(departments_to_sort):
        if dept is None:
            # If a department is None, update both the list and the departments dict
            departments_to_sort[i] = "Unassigned"
            members = departments.pop(None)
            departments["Unassigned"] = members

    sorted_departments = sorted(departments_to_sort)

    # Create department cards
    for dept in sorted_departments:
        with st.expander(f"{dept} Team", expanded=True):
            # Sort members by role importance
            members = departments[dept]
            role_importance = {"admin": 0, "lead": 1, "member": 2}
            members.sort(key=lambda x: (role_importance.get(x.get('role'), 999), x.get('name', '').lower()))

            # Display members in a grid
            num_cols = min(4, len(members))
            if num_cols > 0:
                cols = st.columns(num_cols)
                for i, member in enumerate(members):
                    with cols[i % num_cols]:
                        role = member.get('role', 'member')
                        role_emoji = '👑' if role == 'admin' else '🔶' if role == 'lead' else '👤'

                        st.markdown(f"""
                        <div style="text-align: center; padding: 10px; margin-bottom: 10px; border: 1px solid #eee; border-radius: 5px;">
                            <h4 style="margin: 0;">{role_emoji} {member.get('name', 'Unknown')}</h4>
                            <p style="color: #666; margin: 5px 0;">{role.capitalize()}</p>
                        </div>
                        """, unsafe_allow_html=True)

# Member form (for adding/editing team members)
if st.session_state.show_member_form:
    st.markdown("---")

    if st.session_state.editing_member:
        st.subheader(f"Edit Team Member: {st.session_state.editing_member}")
        user_to_edit = users.get(st.session_state.editing_member, {})
        username_to_edit = st.session_state.editing_member
        editable_username = False
    else:
        st.subheader("Add New Team Member")
        user_to_edit = {}
        username_to_edit = ""
        editable_username = True

    with st.form("member_form"):
        col1, col2 = st.columns(2)

        with col1:
            username = st.text_input("Username", value=username_to_edit, disabled=not editable_username)
            name = st.text_input("Full Name", value=user_to_edit.get('name', ''))
            email = st.text_input("Email", value=user_to_edit.get('email', ''))

            if st.session_state.editing_member:
                change_password = st.checkbox("Change Password")
                if change_password:
                    password = st.text_input("New Password", type="password")
                    confirm_password = st.text_input("Confirm New Password", type="password")
            else:
                password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")

        with col2:
            role = st.selectbox("Role", TEAM_ROLES,
                                index=TEAM_ROLES.index(user_to_edit.get('role', 'member')) if user_to_edit.get(
                                    'role') in TEAM_ROLES else 2)
            department = st.selectbox("Department", [""] + TEAM_DEPARTMENTS, index=(
                        TEAM_DEPARTMENTS.index(user_to_edit.get('department')) + 1) if user_to_edit.get(
                'department') in TEAM_DEPARTMENTS else 0)

        # Submit buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            submit_button = st.form_submit_button("Save Member")
        with col2:
            cancel_button = st.form_submit_button("Cancel")

    # Handle form submission
    if cancel_button:
        st.session_state.show_member_form = False
        st.session_state.editing_member = None
        st.rerun()

    if submit_button:
        # Form validation
        error = False

        if not username:
            st.error("Username is required.")
            error = True
        elif not st.session_state.editing_member and username in users:
            st.error(f"Username '{username}' already exists.")
            error = True
        elif not name:
            st.error("Name is required.")
            error = True
        elif not email:
            st.error("Email is required.")
            error = True
        elif not role:
            st.error("Role is required.")
            error = True
        elif not st.session_state.editing_member and not password:
            st.error("Password is required for new users.")
            error = True

        # Password validation
        password_to_save = None
        if st.session_state.editing_member and 'change_password' in locals() and change_password:
            if not password:
                st.error("Password is required.")
                error = True
            elif password != confirm_password:
                st.error("Passwords do not match.")
                error = True
            else:
                password_to_save = hash_password(password)
        elif not st.session_state.editing_member:  # New user
            if password != confirm_password:
                st.error("Passwords do not match.")
                error = True
            else:
                password_to_save = hash_password(password)

        if not error:
            # Create a copy of the users dict for modification
            updated_users = users.copy()

            # Create or update user data
            if st.session_state.editing_member:
                # Get existing user data
                user_data = updated_users[username_to_edit].copy() if username_to_edit in updated_users else {}

                # Update fields
                user_data['name'] = name
                user_data['email'] = email
                user_data['role'] = role
                user_data['department'] = department if department else None

                # Only update password if changing it
                if password_to_save:
                    user_data['password'] = password_to_save

                # Handle username change if needed
                if username_to_edit != username and editable_username:
                    # Create new entry with updated username
                    updated_users[username] = user_data
                    # Remove old username entry
                    updated_users.pop(username_to_edit)
                else:
                    # Update existing username entry
                    updated_users[username_to_edit] = user_data

                action = "updated"
            else:
                # Create new user
                updated_users[username] = {
                    'name': name,
                    'email': email,
                    'role': role,
                    'password': password_to_save,
                    'department': department if department else None,
                    'created_at': datetime.now().isoformat()
                }
                action = "added"

            # Save changes
            save_users(updated_users)

            # Reset form state
            st.session_state.show_member_form = False
            st.session_state.editing_member = None

            # Show success message and refresh
            st.success(f"Team member {username} {action} successfully!")
            st.rerun()