import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime, timedelta
import plotly.express as px

# Add the parent directory to the path to import from the app root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import load_tasks, save_tasks, check_role_access, generate_id

# Page configuration
st.set_page_config(
    page_title="Project Management - Circuit Breakers",
    page_icon="📋",
    layout="wide"
)

# Check if user is authenticated
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("Please login to access this page.")
    st.stop()

# Page title
st.title("Project Management")
st.write("Track team tasks, assignments, and project progress")

# Initialize session state
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "kanban"
if 'new_task' not in st.session_state:
    st.session_state.new_task = False
if 'edit_task_id' not in st.session_state:
    st.session_state.edit_task_id = None

# Define task constants
TASK_STATUSES = ["To Do", "In Progress", "Blocked", "Completed"]
TASK_PRIORITIES = ["Low", "Medium", "High", "Critical"]
TASK_CATEGORIES = ["Engineering", "Design", "Outreach", "Logistics", "Testing", "Documentation", "Other"]

# Load tasks
tasks = load_tasks()

# Load team members for assignments
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import load_team_members
team_members = load_team_members()
team_member_names = [member["name"] for member in team_members]

# View selector
view_col1, view_col2, view_col3 = st.columns([1, 2, 1])
with view_col1:
    view_options = ["Kanban Board", "List View", "Analytics"]
    selected_view = st.radio("View Mode", view_options, horizontal=True, index=view_options.index("Kanban Board") if st.session_state.view_mode == "kanban" else (view_options.index("List View") if st.session_state.view_mode == "list" else view_options.index("Analytics")))
    
    # Update view mode in session state
    if selected_view == "Kanban Board":
        st.session_state.view_mode = "kanban"
    elif selected_view == "List View":
        st.session_state.view_mode = "list"
    else:
        st.session_state.view_mode = "analytics"

with view_col3:
    # Only admin and lead can add tasks
    if st.session_state.role in ['admin', 'lead'] or True:  # Temporarily allowing all users to add tasks
        if st.button("Add New Task ➕"):
            st.session_state.new_task = True
            st.session_state.edit_task_id = None

# Function to handle task status change
def change_task_status(task_id, new_status):
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = new_status
            save_tasks(tasks)
            break
    st.rerun()

# Function to edit task
def edit_task(task_id):
    st.session_state.edit_task_id = task_id
    st.session_state.new_task = True

# Function to delete task
def delete_task(task_id):
    global tasks
    tasks = [task for task in tasks if task["id"] != task_id]
    save_tasks(tasks)
    st.success("Task deleted successfully!")
    st.rerun()

# Kanban board view
if st.session_state.view_mode == "kanban":
    # Create columns for each status
    status_cols = st.columns(len(TASK_STATUSES))
    
    # Prepare tasks by status
    tasks_by_status = {status: [] for status in TASK_STATUSES}
    for task in tasks:
        status = task.get("status", "To Do")
        if status in tasks_by_status:
            tasks_by_status[status].append(task)
    
    # Display each status column
    for i, status in enumerate(TASK_STATUSES):
        with status_cols[i]:
            st.subheader(status)
            
            # Define color for status column header
            status_colors = {
                "To Do": "#6c757d",  # Gray
                "In Progress": "#ffc107",  # Yellow
                "Blocked": "#dc3545",  # Red
                "Completed": "#28a745"  # Green
            }
            
            st.markdown(
                f"<div style='background-color: {status_colors[status]}; padding: 5px; border-radius: 5px; color: white; text-align: center; margin-bottom: 10px;'>{status} ({len(tasks_by_status[status])})</div>",
                unsafe_allow_html=True
            )
            
            # Display tasks for this status
            for task in tasks_by_status[status]:
                priority_colors = {
                    "Low": "#6c757d",  # Gray
                    "Medium": "#17a2b8",  # Blue
                    "High": "#fd7e14",  # Orange
                    "Critical": "#dc3545"  # Red
                }
                
                priority = task.get("priority", "Medium")
                priority_color = priority_colors.get(priority, "#6c757d")
                
                with st.container():
                    st.markdown(
                        f"<div style='border-left: 5px solid {priority_color}; padding-left: 10px; margin-bottom: 10px;'>",
                        unsafe_allow_html=True
                    )
                    st.subheader(task["title"], anchor=f"task_{task['id']}")
                    st.write(f"**Priority:** {priority}")
                    st.write(f"**Assigned to:** {task.get('assigned_to', 'Unassigned')}")
                    st.write(f"**Category:** {task.get('category', 'Other')}")
                    
                    # Display due date with color coding
                    due_date = datetime.fromisoformat(task.get("due_date", datetime.now().isoformat()))
                    days_remaining = (due_date - datetime.now()).days
                    
                    if days_remaining < 0:
                        st.markdown(f"**Due Date:** <span style='color: red;'>{due_date.strftime('%m/%d/%Y')} (Overdue)</span>", unsafe_allow_html=True)
                    elif days_remaining <= 2:
                        st.markdown(f"**Due Date:** <span style='color: orange;'>{due_date.strftime('%m/%d/%Y')} ({days_remaining} days left)</span>", unsafe_allow_html=True)
                    else:
                        st.write(f"**Due Date:** {due_date.strftime('%m/%d/%Y')}")
                    
                    with st.expander("Details"):
                        st.write(task.get("description", "No description provided."))
                        
                        # Task actions
                        action_col1, action_col2 = st.columns(2)
                        
                        # Status change actions
                        with action_col1:
                            new_status_options = [s for s in TASK_STATUSES if s != status]
                            new_status = st.selectbox(
                                "Change Status", 
                                new_status_options,
                                key=f"status_change_{task['id']}"
                            )
                            if st.button("Update Status", key=f"update_status_{task['id']}"):
                                change_task_status(task["id"], new_status)
                        
                        # Edit/Delete actions (admin/lead only)
                        with action_col2:
                            if st.session_state.role in ['admin', 'lead'] or task.get('assigned_to') == st.session_state.user or task.get('created_by') == st.session_state.user:
                                if st.button("Edit Task", key=f"edit_{task['id']}"):
                                    edit_task(task["id"])
                                if st.button("Delete Task", key=f"delete_{task['id']}"):
                                    delete_task(task["id"])
                    
                    st.markdown("</div>", unsafe_allow_html=True)

# List view
elif st.session_state.view_mode == "list":
    # Create filters
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
    
    with filter_col1:
        filter_status = st.multiselect("Status", TASK_STATUSES, default=TASK_STATUSES)
    
    with filter_col2:
        filter_priority = st.multiselect("Priority", TASK_PRIORITIES, default=TASK_PRIORITIES)
    
    with filter_col3:
        filter_category = st.multiselect("Category", TASK_CATEGORIES, default=TASK_CATEGORIES)
    
    with filter_col4:
        filter_assigned = st.multiselect("Assigned To", ["Unassigned"] + team_member_names, default=["Unassigned"] + team_member_names)
    
    # Apply filters
    filtered_tasks = [
        task for task in tasks 
        if task.get("status", "To Do") in filter_status
        and task.get("priority", "Medium") in filter_priority
        and task.get("category", "Other") in filter_category
        and (task.get("assigned_to", "Unassigned") in filter_assigned or ("Unassigned" in filter_assigned and not task.get("assigned_to")))
    ]
    
    # Sort options
    sort_col1, sort_col2 = st.columns(2)
    
    with sort_col1:
        sort_by = st.selectbox("Sort by", ["Due Date", "Priority", "Status", "Title", "Category"])
    
    with sort_col2:
        sort_order = st.radio("Order", ["Ascending", "Descending"], horizontal=True)
    
    # Sort tasks
    if sort_by == "Due Date":
        filtered_tasks.sort(key=lambda x: datetime.fromisoformat(x.get("due_date", datetime.now().isoformat())), reverse=(sort_order == "Descending"))
    elif sort_by == "Priority":
        # Custom priority sorting order
        priority_order = {"Critical": 3, "High": 2, "Medium": 1, "Low": 0}
        filtered_tasks.sort(key=lambda x: priority_order.get(x.get("priority", "Medium"), 0), reverse=(sort_order == "Descending"))
    elif sort_by == "Status":
        # Custom status sorting order
        status_order = {"To Do": 0, "In Progress": 1, "Blocked": 2, "Completed": 3}
        filtered_tasks.sort(key=lambda x: status_order.get(x.get("status", "To Do"), 0), reverse=(sort_order == "Descending"))
    else:
        # Sort by title or category alphabetically
        filtered_tasks.sort(key=lambda x: x.get(sort_by.lower(), ""), reverse=(sort_order == "Descending"))
    
    # Display tasks in a table
    if filtered_tasks:
        # Create DataFrame for display
        task_data = []
        for task in filtered_tasks:
            due_date = datetime.fromisoformat(task.get("due_date", datetime.now().isoformat()))
            days_remaining = (due_date - datetime.now()).days
            
            task_data.append({
                "ID": task["id"],
                "Title": task["title"],
                "Status": task.get("status", "To Do"),
                "Priority": task.get("priority", "Medium"),
                "Assigned To": task.get("assigned_to", "Unassigned"),
                "Due Date": due_date.strftime("%m/%d/%Y"),
                "Days Left": days_remaining,
                "Category": task.get("category", "Other")
            })
        
        task_df = pd.DataFrame(task_data)
        
        # Apply styling (highlighting)
        def highlight_overdue(val):
            try:
                days = int(val)
                if days < 0:
                    return 'color: red; font-weight: bold'
                elif days <= 2:
                    return 'color: orange'
                else:
                    return ''
            except:
                return ''
        
        def highlight_priority(val):
            if val == "Critical":
                return 'background-color: #dc3545; color: white'
            elif val == "High":
                return 'background-color: #fd7e14; color: white'
            elif val == "Medium":
                return 'background-color: #17a2b8; color: white'
            else:
                return 'background-color: #6c757d; color: white'
        
        def highlight_status(val):
            if val == "Completed":
                return 'background-color: #28a745; color: white'
            elif val == "In Progress":
                return 'background-color: #ffc107; color: black'
            elif val == "Blocked":
                return 'background-color: #dc3545; color: white'
            else:
                return 'background-color: #6c757d; color: white'
        
        # Apply styling
        styled_df = task_df.style.applymap(highlight_overdue, subset=['Days Left']) \
                              .applymap(highlight_priority, subset=['Priority']) \
                              .applymap(highlight_status, subset=['Status'])
        
        # Display table
        st.dataframe(styled_df, use_container_width=True)
        
        # Task details and actions
        st.subheader("Task Details")
        
        # Let user select a task to view details
        selected_task_id = st.selectbox("Select a task to view details", task_df["ID"].tolist(), format_func=lambda x: next((task["title"] for task in filtered_tasks if task["id"] == x), x))
        
        # Display selected task details
        selected_task = next((task for task in filtered_tasks if task["id"] == selected_task_id), None)
        
        if selected_task:
            task_col1, task_col2 = st.columns(2)
            
            with task_col1:
                st.markdown(f"**Title:** {selected_task['title']}")
                st.markdown(f"**Description:** {selected_task.get('description', 'No description provided.')}")
                st.markdown(f"**Category:** {selected_task.get('category', 'Other')}")
                st.markdown(f"**Created by:** {selected_task.get('created_by', 'Unknown')}")
                created_date = datetime.fromisoformat(selected_task.get("created_at", datetime.now().isoformat()))
                st.markdown(f"**Created on:** {created_date.strftime('%m/%d/%Y')}")
            
            with task_col2:
                st.markdown(f"**Status:** {selected_task.get('status', 'To Do')}")
                st.markdown(f"**Priority:** {selected_task.get('priority', 'Medium')}")
                st.markdown(f"**Assigned to:** {selected_task.get('assigned_to', 'Unassigned')}")
                due_date = datetime.fromisoformat(selected_task.get("due_date", datetime.now().isoformat()))
                st.markdown(f"**Due Date:** {due_date.strftime('%m/%d/%Y')}")
                days_remaining = (due_date - datetime.now()).days
                if days_remaining < 0:
                    st.markdown(f"**Days Remaining:** <span style='color: red; font-weight: bold;'>{days_remaining} (Overdue)</span>", unsafe_allow_html=True)
                elif days_remaining <= 2:
                    st.markdown(f"**Days Remaining:** <span style='color: orange;'>{days_remaining}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"**Days Remaining:** {days_remaining}")
            
            # Task actions
            st.subheader("Task Actions")
            action_col1, action_col2, action_col3 = st.columns(3)
            
            with action_col1:
                new_status = st.selectbox("Change Status", TASK_STATUSES, index=TASK_STATUSES.index(selected_task.get("status", "To Do")))
                if st.button("Update Status"):
                    change_task_status(selected_task["id"], new_status)
            
            with action_col2:
                if st.session_state.role in ['admin', 'lead'] or selected_task.get('assigned_to') == st.session_state.user or selected_task.get('created_by') == st.session_state.user:
                    if st.button("Edit Task"):
                        edit_task(selected_task["id"])
            
            with action_col3:
                if st.session_state.role in ['admin', 'lead'] or selected_task.get('created_by') == st.session_state.user:
                    if st.button("Delete Task"):
                        delete_task(selected_task["id"])
    else:
        st.info("No tasks match the selected filters.")

# Analytics view
elif st.session_state.view_mode == "analytics":
    st.subheader("Task Analytics")
    
    # Tasks by status
    status_counts = {}
    for status in TASK_STATUSES:
        status_counts[status] = len([task for task in tasks if task.get("status", "To Do") == status])
    
    status_df = pd.DataFrame({
        "Status": list(status_counts.keys()),
        "Count": list(status_counts.values())
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Tasks by Status")
        
        # Set colors for status chart
        status_colors = {
            "To Do": "#6c757d",  # Gray
            "In Progress": "#ffc107",  # Yellow
            "Blocked": "#dc3545",  # Red
            "Completed": "#28a745"  # Green
        }
        
        color_map = [status_colors[status] for status in status_df["Status"]]
        
        fig = px.pie(
            status_df,
            values="Count",
            names="Status",
            title="Task Distribution by Status",
            color="Status",
            color_discrete_map={status: status_colors[status] for status in TASK_STATUSES}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Tasks by priority
    priority_counts = {}
    for priority in TASK_PRIORITIES:
        priority_counts[priority] = len([task for task in tasks if task.get("priority", "Medium") == priority])
    
    priority_df = pd.DataFrame({
        "Priority": list(priority_counts.keys()),
        "Count": list(priority_counts.values())
    })
    
    with col2:
        st.subheader("Tasks by Priority")
        
        # Set colors for priority chart
        priority_colors = {
            "Low": "#6c757d",  # Gray
            "Medium": "#17a2b8",  # Blue
            "High": "#fd7e14",  # Orange
            "Critical": "#dc3545"  # Red
        }
        
        fig = px.pie(
            priority_df,
            values="Count",
            names="Priority",
            title="Task Distribution by Priority",
            color="Priority",
            color_discrete_map={priority: priority_colors[priority] for priority in TASK_PRIORITIES}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Tasks by category
    category_counts = {}
    for category in TASK_CATEGORIES:
        category_counts[category] = len([task for task in tasks if task.get("category", "Other") == category])
    
    category_df = pd.DataFrame({
        "Category": list(category_counts.keys()),
        "Count": list(category_counts.values())
    })
    
    # Sort by count, descending
    category_df = category_df.sort_values("Count", ascending=False)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Tasks by Category")
        
        fig = px.bar(
            category_df,
            x="Category",
            y="Count",
            title="Task Distribution by Category",
            color="Count",
            color_continuous_scale=px.colors.sequential.Blues
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Tasks by assignee
    assignee_counts = {}
    for member in team_member_names:
        assignee_counts[member] = len([task for task in tasks if task.get("assigned_to") == member])
    
    # Add unassigned tasks
    assignee_counts["Unassigned"] = len([task for task in tasks if not task.get("assigned_to")])
    
    assignee_df = pd.DataFrame({
        "Assignee": list(assignee_counts.keys()),
        "Count": list(assignee_counts.values())
    })
    
    # Sort by count, descending
    assignee_df = assignee_df.sort_values("Count", ascending=False)
    
    with col4:
        st.subheader("Tasks by Assignee")
        
        fig = px.bar(
            assignee_df,
            x="Assignee",
            y="Count",
            title="Task Distribution by Assignee",
            color="Count",
            color_continuous_scale=px.colors.sequential.Plasma
        )
        
        # Rotate x-axis labels for better readability
        fig.update_layout(xaxis_tickangle=-45)
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Task due date analysis
    st.subheader("Due Date Analysis")
    
    task_timeline = []
    overdue_count = 0
    due_soon_count = 0
    future_count = 0
    
    now = datetime.now()
    
    for task in tasks:
        if task.get("status") != "Completed":  # Exclude completed tasks
            due_date = datetime.fromisoformat(task.get("due_date", now.isoformat()))
            days_remaining = (due_date - now).days
            
            task_timeline.append({
                "Task": task["title"],
                "Days Remaining": days_remaining,
                "Status": task.get("status", "To Do"),
                "Priority": task.get("priority", "Medium")
            })
            
            if days_remaining < 0:
                overdue_count += 1
            elif days_remaining <= 7:
                due_soon_count += 1
            else:
                future_count += 1
    
    # Create bar chart for due date distribution
    due_date_data = {
        "Timeframe": ["Overdue", "Due within a week", "Due later"],
        "Count": [overdue_count, due_soon_count, future_count],
        "Color": ["#dc3545", "#ffc107", "#28a745"]
    }
    
    due_date_df = pd.DataFrame(due_date_data)
    
    col5, col6 = st.columns(2)
    
    with col5:
        fig = px.bar(
            due_date_df,
            x="Timeframe",
            y="Count",
            title="Task Distribution by Due Date",
            color="Timeframe",
            color_discrete_map={
                "Overdue": "#dc3545",
                "Due within a week": "#ffc107",
                "Due later": "#28a745"
            }
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col6:
        if task_timeline:
            # Create a dataframe
            timeline_df = pd.DataFrame(task_timeline)
            
            # Sort by days remaining
            timeline_df = timeline_df.sort_values("Days Remaining")
            
            # Create horizontal bar chart for tasks due timeline
            fig = px.bar(
                timeline_df,
                y="Task",
                x="Days Remaining",
                title="Upcoming Task Timeline",
                color="Priority",
                orientation="h",
                color_discrete_map={
                    "Critical": "#dc3545",
                    "High": "#fd7e14",
                    "Medium": "#17a2b8",
                    "Low": "#6c757d"
                }
            )
            
            # Add a vertical line at x=0 (today)
            fig.add_vline(x=0, line_width=2, line_dash="dash", line_color="black")
            
            # Add annotation for today
            fig.add_annotation(
                x=0,
                y=0,
                text="Today",
                showarrow=False,
                yshift=10
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No incomplete tasks to display.")

# Task form (add/edit)
if st.session_state.new_task:
    st.markdown("---")
    
    # Determine if we're editing or creating a new task
    editing = st.session_state.edit_task_id is not None
    
    if editing:
        task_to_edit = next((task for task in tasks if task["id"] == st.session_state.edit_task_id), None)
        st.subheader(f"Edit Task: {task_to_edit['title']}")
    else:
        st.subheader("Create New Task")
    
    # Create form
    with st.form("task_form"):
        # Pre-fill values if editing
        if editing:
            title_value = task_to_edit["title"]
            description_value = task_to_edit.get("description", "")
            status_index = TASK_STATUSES.index(task_to_edit.get("status", "To Do"))
            priority_index = TASK_PRIORITIES.index(task_to_edit.get("priority", "Medium")) if task_to_edit.get("priority") in TASK_PRIORITIES else 1
            category_index = TASK_CATEGORIES.index(task_to_edit.get("category", "Other")) if task_to_edit.get("category") in TASK_CATEGORIES else -1
            assigned_to_index = team_member_names.index(task_to_edit.get("assigned_to")) if task_to_edit.get("assigned_to") in team_member_names else -1
            due_date_value = datetime.fromisoformat(task_to_edit.get("due_date", datetime.now().isoformat())).date()
        else:
            title_value = ""
            description_value = ""
            status_index = 0  # To Do
            priority_index = 1  # Medium
            category_index = -1  # No default category
            assigned_to_index = -1  # No default assignee
            due_date_value = (datetime.now() + timedelta(days=7)).date()  # Default due date 1 week from now
        
        # Form fields
        task_title = st.text_input("Task Title*", value=title_value)
        task_description = st.text_area("Description", value=description_value)
        
        col1, col2 = st.columns(2)
        
        with col1:
            task_status = st.selectbox("Status", TASK_STATUSES, index=status_index)
            task_category = st.selectbox("Category", TASK_CATEGORIES, index=category_index)
        
        with col2:
            task_priority = st.selectbox("Priority", TASK_PRIORITIES, index=priority_index)
            task_assigned_to = st.selectbox("Assigned To", ["--Select--"] + team_member_names, index=assigned_to_index + 1)
        
        task_due_date = st.date_input("Due Date", value=due_date_value)
        
        # Submit buttons
        col1, col2 = st.columns(2)
        
        with col1:
            submit_button = st.form_submit_button("Save Task")
        
        with col2:
            cancel_button = st.form_submit_button("Cancel")
        
        if cancel_button:
            st.session_state.new_task = False
            st.session_state.edit_task_id = None
            st.rerun()
        
        if submit_button:
            # Validate required fields
            if not task_title:
                st.error("Task title is required!")
            else:
                # Process form submission
                due_date_datetime = datetime.combine(task_due_date, datetime.min.time())
                
                # Format assigned_to
                assigned_to = None if task_assigned_to == "--Select--" else task_assigned_to
                
                if editing:
                    # Update existing task
                    for task in tasks:
                        if task["id"] == st.session_state.edit_task_id:
                            task["title"] = task_title
                            task["description"] = task_description
                            task["status"] = task_status
                            task["priority"] = task_priority
                            task["category"] = task_category
                            task["assigned_to"] = assigned_to
                            task["due_date"] = due_date_datetime.isoformat()
                            break
                    
                    success_message = "Task updated successfully!"
                else:
                    # Create new task
                    new_task = {
                        "id": generate_id(),
                        "title": task_title,
                        "description": task_description,
                        "status": task_status,
                        "priority": task_priority,
                        "category": task_category,
                        "assigned_to": assigned_to,
                        "created_by": st.session_state.user,
                        "created_at": datetime.now().isoformat(),
                        "due_date": due_date_datetime.isoformat()
                    }
                    
                    tasks.append(new_task)
                    success_message = "Task created successfully!"
                
                # Save tasks to file
                save_tasks(tasks)
                
                # Reset form
                st.session_state.new_task = False
                st.session_state.edit_task_id = None
                
                st.success(success_message)
                st.rerun()

st.markdown("---")
st.caption("Circuit Breakers Team Hub - Project Management")
