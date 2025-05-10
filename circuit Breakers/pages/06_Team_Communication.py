import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime, timedelta

# Add the parent directory to the path to import from the app root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from util import load_messages, save_messages, load_team_members, generate_id

# Page configuration
st.set_page_config(
    page_title="Team Communication - Circuit Breakers",
    page_icon="💬",
    layout="wide"
)

# Check if user is authenticated
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("Please login to access this page.")
    st.stop()

# Page title
st.title("Team Communication")
st.write("Group discussions, announcements, and team message board")

# Define message categories
MESSAGE_CATEGORIES = ["Announcement", "Question", "Discussion", "Response", "Alert", "Update", "Other"]
MESSAGE_PRIORITIES = ["Low", "Normal", "High", "Urgent"]

# Initialize session state
if 'selected_channel' not in st.session_state:
    st.session_state.selected_channel = "General"
if 'reply_to' not in st.session_state:
    st.session_state.reply_to = None
if 'view_thread' not in st.session_state:
    st.session_state.view_thread = None
if 'edit_message' not in st.session_state:
    st.session_state.edit_message = None
if 'new_post' not in st.session_state:
    st.session_state.new_post = False
if 'show_new_post_form' not in st.session_state:
    st.session_state.show_new_post_form = False

# Load messages
messages = load_messages()

# Load team members for mentions
team_members = load_team_members()
team_member_names = [member["name"] for member in team_members]

# Define communication channels
CHANNELS = ["General", "Engineering", "Design", "Competition", "Outreach", "Admin"]

# Function to toggle reply mode
def toggle_reply(message_id):
    if st.session_state.reply_to == message_id:
        st.session_state.reply_to = None
    else:
        st.session_state.reply_to = message_id
        st.session_state.edit_message = None

# Function to view thread
def view_thread(message_id):
    st.session_state.view_thread = message_id
    st.session_state.reply_to = message_id

# Function to edit message
def edit_message(message_id):
    st.session_state.edit_message = message_id
    st.session_state.reply_to = None

# Function to delete message
def delete_message(message_id):
    # Also delete all replies to this message
    global messages
    messages = [msg for msg in messages if msg['id'] != message_id and msg.get('parent_id') != message_id]
    save_messages(messages)
    
    # Reset thread view if we're deleting the thread parent
    if st.session_state.view_thread == message_id:
        st.session_state.view_thread = None
    
    st.success("Message deleted successfully!")
    st.rerun()

# Sidebar for channel selection
with st.sidebar:
    st.header("Channels")
    
    for channel in CHANNELS:
        # Count unread messages (would be implemented in a real app)
        channel_messages = [msg for msg in messages if msg.get('channel') == channel]
        
        if st.button(f"{channel} ({len(channel_messages)})", key=f"channel_{channel}"):
            st.session_state.selected_channel = channel
            st.session_state.view_thread = None
            st.rerun()
    
    # Display online team members (simulated in this example)
    st.markdown("---")
    st.subheader("Team Online")
    
    # In a real app, you would track actual online status
    for i, member in enumerate(team_members[:5]):  # Show first 5 members as online
        st.markdown(f"🟢 {member['name']}")
    
    if len(team_members) > 5:
        st.markdown(f"🔘 +{len(team_members) - 5} more")

# Main communication area
if st.session_state.view_thread:
    # Show thread view
    thread_parent = next((msg for msg in messages if msg['id'] == st.session_state.view_thread), None)
    
    if thread_parent:
        # Show back button
        if st.button("← Back to Channel"):
            st.session_state.view_thread = None
            st.rerun()
        
        # Display thread parent
        st.subheader(f"Thread: {thread_parent.get('title', 'Conversation')}")
        
        # Display parent message
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{thread_parent.get('author')}**")
            with col2:
                timestamp = datetime.fromisoformat(thread_parent.get('timestamp'))
                st.markdown(f"*{timestamp.strftime('%m/%d/%Y %I:%M %p')}*")
            
            if st.session_state.edit_message == thread_parent['id']:
                # Edit form
                with st.form(key=f"edit_message_form_{thread_parent['id']}"):
                    edit_title = st.text_input("Title", value=thread_parent.get('title', ''))
                    edit_content = st.text_area("Message", value=thread_parent.get('content', ''), height=100)
                    edit_category = st.selectbox("Category", MESSAGE_CATEGORIES, index=MESSAGE_CATEGORIES.index(thread_parent.get('category', 'Discussion')) if thread_parent.get('category') in MESSAGE_CATEGORIES else 0)
                    edit_priority = st.selectbox("Priority", MESSAGE_PRIORITIES, index=MESSAGE_PRIORITIES.index(thread_parent.get('priority', 'Normal')) if thread_parent.get('priority') in MESSAGE_PRIORITIES else 1)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        save_edit = st.form_submit_button("Save Changes")
                    with col2:
                        cancel_edit = st.form_submit_button("Cancel")
                    
                    if save_edit:
                        # Update message
                        for msg in messages:
                            if msg['id'] == thread_parent['id']:
                                msg['title'] = edit_title
                                msg['content'] = edit_content
                                msg['category'] = edit_category
                                msg['priority'] = edit_priority
                                break
                        
                        save_messages(messages)
                        st.session_state.edit_message = None
                        st.success("Message updated successfully!")
                        st.rerun()
                    
                    if cancel_edit:
                        st.session_state.edit_message = None
                        st.rerun()
            else:
                # Normal display
                if thread_parent.get('title'):
                    st.markdown(f"### {thread_parent.get('title')}")
                
                st.markdown(thread_parent.get('content', ''))
                
                # Display category and priority badges
                col1, col2 = st.columns(2)
                with col1:
                    category = thread_parent.get('category', 'Discussion')
                    priority = thread_parent.get('priority', 'Normal')
                    
                    # Define colors for different categories and priorities
                    category_colors = {
                        "Announcement": "#17a2b8",  # Info blue
                        "Question": "#6f42c1",  # Purple
                        "Discussion": "#28a745",  # Success green
                        "Response": "#6c757d",  # Secondary gray
                        "Alert": "#dc3545",  # Danger red
                        "Update": "#fd7e14",  # Warning orange
                        "Other": "#6c757d"  # Secondary gray
                    }
                    
                    priority_colors = {
                        "Low": "#6c757d",  # Secondary gray
                        "Normal": "#17a2b8",  # Info blue
                        "High": "#fd7e14",  # Warning orange
                        "Urgent": "#dc3545"  # Danger red
                    }
                    
                    st.markdown(
                        f"""
                        <span style="background-color: {category_colors.get(category, '#6c757d')}; padding: 3px 8px; border-radius: 10px; color: white; margin-right: 5px;">{category}</span>
                        <span style="background-color: {priority_colors.get(priority, '#6c757d')}; padding: 3px 8px; border-radius: 10px; color: white;">{priority}</span>
                        """,
                        unsafe_allow_html=True
                    )
                
                # Message actions
                if thread_parent.get('author') == st.session_state.user or st.session_state.role in ['admin', 'lead']:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("Reply", key=f"reply_{thread_parent['id']}"):
                            toggle_reply(thread_parent['id'])
                    with col2:
                        if st.button("Edit", key=f"edit_{thread_parent['id']}"):
                            edit_message(thread_parent['id'])
                    with col3:
                        if st.button("Delete", key=f"delete_{thread_parent['id']}"):
                            delete_message(thread_parent['id'])
                else:
                    if st.button("Reply", key=f"reply_{thread_parent['id']}"):
                        toggle_reply(thread_parent['id'])
        
        st.markdown("---")
        
        # Display replies
        replies = [msg for msg in messages if msg.get('parent_id') == thread_parent['id']]
        replies.sort(key=lambda x: datetime.fromisoformat(x.get('timestamp')))
        
        if replies:
            st.subheader(f"Replies ({len(replies)})")
            
            for reply in replies:
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{reply.get('author')}**")
                    with col2:
                        timestamp = datetime.fromisoformat(reply.get('timestamp'))
                        st.markdown(f"*{timestamp.strftime('%m/%d/%Y %I:%M %p')}*")
                    
                    if st.session_state.edit_message == reply['id']:
                        # Edit form for reply
                        with st.form(key=f"edit_reply_form_{reply['id']}"):
                            edit_content = st.text_area("Message", value=reply.get('content', ''), height=100)
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                save_edit = st.form_submit_button("Save Changes")
                            with col2:
                                cancel_edit = st.form_submit_button("Cancel")
                            
                            if save_edit:
                                # Update message
                                for msg in messages:
                                    if msg['id'] == reply['id']:
                                        msg['content'] = edit_content
                                        break
                                
                                save_messages(messages)
                                st.session_state.edit_message = None
                                st.success("Reply updated successfully!")
                                st.rerun()
                            
                            if cancel_edit:
                                st.session_state.edit_message = None
                                st.rerun()
                    else:
                        # Normal display
                        st.markdown(reply.get('content', ''))
                        
                        # Reply actions
                        if reply.get('author') == st.session_state.user or st.session_state.role in ['admin', 'lead']:
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Edit", key=f"edit_{reply['id']}"):
                                    edit_message(reply['id'])
                            with col2:
                                if st.button("Delete", key=f"delete_{reply['id']}"):
                                    delete_message(reply['id'])
                    
                    st.markdown("---")
        
        # Reply form
        if st.session_state.reply_to == thread_parent['id']:
            st.subheader("Post a Reply")
            
            with st.form(key="reply_form"):
                reply_content = st.text_area("Reply", height=100)
                
                col1, col2 = st.columns(2)
                with col1:
                    submit_reply = st.form_submit_button("Submit Reply")
                with col2:
                    cancel_reply = st.form_submit_button("Cancel")
                
                if submit_reply:
                    if reply_content:
                        # Create new reply
                        new_reply = {
                            "id": generate_id(),
                            "content": reply_content,
                            "author": st.session_state.user,
                            "timestamp": datetime.now().isoformat(),
                            "parent_id": thread_parent['id'],
                            "channel": thread_parent.get('channel', 'General'),
                            "category": "Response"
                        }
                        
                        messages.append(new_reply)
                        save_messages(messages)
                        
                        st.session_state.reply_to = None
                        st.success("Reply posted successfully!")
                        st.rerun()
                    else:
                        st.error("Reply content cannot be empty!")
                
                if cancel_reply:
                    st.session_state.reply_to = None
                    st.rerun()
    else:
        st.error("Thread not found!")
        if st.button("Back to Channel"):
            st.session_state.view_thread = None
            st.rerun()
else:
    # Show channel view
    st.subheader(f"#{st.session_state.selected_channel}")
    
    # Add new post button
    if st.button("New Post"):
        st.session_state.show_new_post_form = True
    
    # New post form
    if st.session_state.show_new_post_form:
        with st.form(key="new_post_form"):
            st.subheader("Create New Post")
            
            post_title = st.text_input("Title")
            post_content = st.text_area("Message", height=150)
            
            col1, col2 = st.columns(2)
            with col1:
                post_category = st.selectbox("Category", MESSAGE_CATEGORIES)
            with col2:
                post_priority = st.selectbox("Priority", MESSAGE_PRIORITIES, index=1)  # Normal priority by default
            
            col1, col2 = st.columns(2)
            with col1:
                submit_post = st.form_submit_button("Post Message")
            with col2:
                cancel_post = st.form_submit_button("Cancel")
            
            if submit_post:
                if post_content:
                    # Create new post
                    new_post = {
                        "id": generate_id(),
                        "title": post_title,
                        "content": post_content,
                        "author": st.session_state.user,
                        "timestamp": datetime.now().isoformat(),
                        "channel": st.session_state.selected_channel,
                        "category": post_category,
                        "priority": post_priority
                    }
                    
                    messages.append(new_post)
                    save_messages(messages)
                    
                    st.session_state.show_new_post_form = False
                    st.success("Message posted successfully!")
                    st.rerun()
                else:
                    st.error("Message content cannot be empty!")
            
            if cancel_post:
                st.session_state.show_new_post_form = False
                st.rerun()
    
    # Filter messages for current channel
    channel_messages = [msg for msg in messages if msg.get('channel') == st.session_state.selected_channel and not msg.get('parent_id')]
    
    # Sort by timestamp (newest first)
    channel_messages.sort(key=lambda x: datetime.fromisoformat(x.get('timestamp')), reverse=True)
    
    # Add filtering options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_category = st.multiselect("Filter by Category", ["All"] + MESSAGE_CATEGORIES, default=["All"])
    
    with col2:
        filter_time = st.selectbox("Filter by Time", ["All Time", "Today", "Past Week", "Past Month"])
    
    with col3:
        search_messages = st.text_input("Search in messages", key="search_messages")
    
    # Apply filters
    filtered_messages = channel_messages
    
    # Category filter
    if not ("All" in filter_category or len(filter_category) == 0):
        filtered_messages = [msg for msg in filtered_messages if msg.get('category') in filter_category]
    
    # Time filter
    now = datetime.now()
    if filter_time == "Today":
        filtered_messages = [msg for msg in filtered_messages if datetime.fromisoformat(msg.get('timestamp')).date() == now.date()]
    elif filter_time == "Past Week":
        filtered_messages = [msg for msg in filtered_messages if datetime.fromisoformat(msg.get('timestamp')) > (now - timedelta(days=7))]
    elif filter_time == "Past Month":
        filtered_messages = [msg for msg in filtered_messages if datetime.fromisoformat(msg.get('timestamp')) > (now - timedelta(days=30))]
    
    # Search filter
    if search_messages:
        search_term = search_messages.lower()
        filtered_messages = [
            msg for msg in filtered_messages 
            if (search_term in msg.get('title', '').lower() or 
                search_term in msg.get('content', '').lower() or 
                search_term in msg.get('author', '').lower())
        ]
    
    # Display messages
    if filtered_messages:
        for message in filtered_messages:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{message.get('author')}**")
                with col2:
                    timestamp = datetime.fromisoformat(message.get('timestamp'))
                    st.markdown(f"*{timestamp.strftime('%m/%d/%Y %I:%M %p')}*")
                
                # Display message content
                if message.get('title'):
                    st.markdown(f"### {message.get('title')}")
                
                st.markdown(message.get('content', ''))
                
                # Display category and priority badges
                col1, col2 = st.columns(2)
                with col1:
                    category = message.get('category', 'Discussion')
                    priority = message.get('priority', 'Normal')
                    
                    # Define colors for different categories and priorities
                    category_colors = {
                        "Announcement": "#17a2b8",  # Info blue
                        "Question": "#6f42c1",  # Purple
                        "Discussion": "#28a745",  # Success green
                        "Response": "#6c757d",  # Secondary gray
                        "Alert": "#dc3545",  # Danger red
                        "Update": "#fd7e14",  # Warning orange
                        "Other": "#6c757d"  # Secondary gray
                    }
                    
                    priority_colors = {
                        "Low": "#6c757d",  # Secondary gray
                        "Normal": "#17a2b8",  # Info blue
                        "High": "#fd7e14",  # Warning orange
                        "Urgent": "#dc3545"  # Danger red
                    }
                    
                    st.markdown(
                        f"""
                        <span style="background-color: {category_colors.get(category, '#6c757d')}; padding: 3px 8px; border-radius: 10px; color: white; margin-right: 5px;">{category}</span>
                        <span style="background-color: {priority_colors.get(priority, '#6c757d')}; padding: 3px 8px; border-radius: 10px; color: white;">{priority}</span>
                        """,
                        unsafe_allow_html=True
                    )
                
                # Count replies
                replies = [msg for msg in messages if msg.get('parent_id') == message['id']]
                
                # Message actions
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"View Thread ({len(replies)})", key=f"view_{message['id']}"):
                        view_thread(message['id'])
                with col2:
                    if st.button("Reply", key=f"reply_{message['id']}"):
                        toggle_reply(message['id'])
                
                # Edit/delete actions (only for author or admin/lead)
                if message.get('author') == st.session_state.user or st.session_state.role in ['admin', 'lead']:
                    with col3:
                        # Use a dropdown for edit/delete to save space
                        action = st.selectbox("Actions", ["Select Action", "Edit", "Delete"], key=f"action_{message['id']}")
                        
                        if action == "Edit":
                            edit_message(message['id'])
                            st.rerun()
                        elif action == "Delete":
                            delete_message(message['id'])
                
                # Reply form
                if st.session_state.reply_to == message['id']:
                    with st.form(key=f"reply_form_{message['id']}"):
                        reply_content = st.text_area("Reply", height=100)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            submit_reply = st.form_submit_button("Submit Reply")
                        with col2:
                            cancel_reply = st.form_submit_button("Cancel")
                        
                        if submit_reply:
                            if reply_content:
                                # Create new reply
                                new_reply = {
                                    "id": generate_id(),
                                    "content": reply_content,
                                    "author": st.session_state.user,
                                    "timestamp": datetime.now().isoformat(),
                                    "parent_id": message['id'],
                                    "channel": message.get('channel', 'General'),
                                    "category": "Response"
                                }
                                
                                messages.append(new_reply)
                                save_messages(messages)
                                
                                st.session_state.reply_to = None
                                st.success("Reply posted successfully!")
                                st.rerun()
                            else:
                                st.error("Reply content cannot be empty!")
                        
                        if cancel_reply:
                            st.session_state.reply_to = None
                            st.rerun()
                
                st.markdown("---")
    else:
        st.info("No messages found in this channel. Be the first to post!")

# Footer
st.caption("Circuit Breakers Team Hub - Team Communication")
