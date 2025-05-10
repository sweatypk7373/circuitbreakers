import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import base64
from io import BytesIO
from database import (
    SessionLocal, User, Task, BuildLog, Resource, 
    MediaItem, Message, Event, Sponsor, AppSetting
)
from sqlalchemy import desc

# Create data directories if they don't exist (for backward compatibility)
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

# Load tasks from database
def load_tasks():
    # Try to load from database first
    db = SessionLocal()
    try:
        tasks = []
        db_tasks = db.query(Task).order_by(desc(Task.created_at)).all()
        
        for task in db_tasks:
            # Get assignee name if available
            assignee_name = None
            if task.assignee_id:
                user = db.query(User).filter(User.id == task.assignee_id).first()
                if user:
                    assignee_name = user.name
            
            tasks.append({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "due_date": task.due_date,
                "assignee": assignee_name
            })
        
        if tasks:
            return tasks
        
        # Fallback to JSON if database is empty (for migration)
        task_file = "data/tasks/tasks.json"
        if os.path.exists(task_file):
            with open(task_file, 'r') as f:
                json_tasks = json.load(f)
                
                # Migrate tasks to the database if found in JSON
                if json_tasks:
                    for task_data in json_tasks:
                        # Map assignee to user ID if possible
                        assignee_id = None
                        assignee_name = task_data.get('assignee')
                        if assignee_name:
                            user = db.query(User).filter(User.name == assignee_name).first()
                            if user:
                                assignee_id = user.id
                        
                        new_task = Task(
                            id=task_data.get('id', generate_id()),
                            title=task_data.get('title', ''),
                            description=task_data.get('description', ''),
                            status=task_data.get('status', 'Not Started'),
                            priority=task_data.get('priority', 'Medium'),
                            due_date=task_data.get('due_date', None),
                            assignee_id=assignee_id
                        )
                        db.add(new_task)
                    
                    db.commit()
                    return json_tasks
        
        # If nothing found, return empty list
        return []
    
    except Exception as e:
        print(f"Database error in load_tasks: {str(e)}")
        # Fallback to JSON
        task_file = "data/tasks/tasks.json"
        if os.path.exists(task_file):
            with open(task_file, 'r') as f:
                return json.load(f)
        return []
    
    finally:
        db.close()

# Save tasks to database
def save_tasks(tasks):
    db = SessionLocal()
    try:
        # Clear existing tasks if replacing all
        if tasks:
            # Get existing task IDs
            existing_ids = [task.id for task in db.query(Task).all()]
            new_ids = [task['id'] for task in tasks if 'id' in task]
            
            # Delete tasks not in the new list
            for task_id in existing_ids:
                if task_id not in new_ids:
                    db.query(Task).filter(Task.id == task_id).delete()
            
            # Update or insert tasks
            for task_data in tasks:
                # Find user ID for assignee if present
                assignee_id = None
                if 'assignee' in task_data and task_data['assignee']:
                    user = db.query(User).filter(User.name == task_data['assignee']).first()
                    if user:
                        assignee_id = user.id
                
                # Check if task exists
                task_id = task_data.get('id')
                existing_task = db.query(Task).filter(Task.id == task_id).first() if task_id else None
                
                if existing_task:
                    # Update existing task
                    existing_task.title = task_data.get('title', existing_task.title)
                    existing_task.description = task_data.get('description', existing_task.description)
                    existing_task.status = task_data.get('status', existing_task.status)
                    existing_task.priority = task_data.get('priority', existing_task.priority)
                    existing_task.due_date = task_data.get('due_date', existing_task.due_date)
                    existing_task.assignee_id = assignee_id
                else:
                    # Create new task
                    new_task = Task(
                        id=task_data.get('id', generate_id()),
                        title=task_data.get('title', ''),
                        description=task_data.get('description', ''),
                        status=task_data.get('status', 'Not Started'),
                        priority=task_data.get('priority', 'Medium'),
                        due_date=task_data.get('due_date', None),
                        assignee_id=assignee_id
                    )
                    db.add(new_task)
            
            db.commit()
        
        # For backward compatibility and backup, also save to JSON
        task_file = "data/tasks/tasks.json"
        with open(task_file, 'w') as f:
            json.dump(tasks, f, indent=4)
    
    except Exception as e:
        db.rollback()
        print(f"Database error in save_tasks: {str(e)}")
        
        # Fallback to JSON only
        task_file = "data/tasks/tasks.json"
        with open(task_file, 'w') as f:
            json.dump(tasks, f, indent=4)
    
    finally:
        db.close()

# Load build log entries
def load_logs():
    db = SessionLocal()
    try:
        logs = []
        db_logs = db.query(BuildLog).order_by(desc(BuildLog.created_at)).all()
        
        for log in db_logs:
            # Get author name if available
            author_name = None
            if log.author_id:
                user = db.query(User).filter(User.id == log.author_id).first()
                if user:
                    author_name = user.name
            
            logs.append({
                "id": log.id,
                "title": log.title,
                "description": log.description,
                "category": log.category,
                "date": log.date,
                "author": author_name
            })
        
        if logs:
            return logs
        
        # Fallback to JSON if database is empty
        log_file = "data/logs/build_logs.json"
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                return json.load(f)
        
        return []
    
    except Exception as e:
        print(f"Database error in load_logs: {str(e)}")
        # Fallback to JSON
        log_file = "data/logs/build_logs.json"
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                return json.load(f)
        return []
    
    finally:
        db.close()

# Save build log entries
def save_logs(logs):
    db = SessionLocal()
    try:
        # Process logs
        if logs:
            # Get existing log IDs
            existing_ids = [log.id for log in db.query(BuildLog).all()]
            new_ids = [log['id'] for log in logs if 'id' in log]
            
            # Delete logs not in the new list
            for log_id in existing_ids:
                if log_id not in new_ids:
                    db.query(BuildLog).filter(BuildLog.id == log_id).delete()
            
            # Update or insert logs
            for log_data in logs:
                # Find user ID for author if present
                author_id = None
                if 'author' in log_data and log_data['author']:
                    user = db.query(User).filter(User.name == log_data['author']).first()
                    if user:
                        author_id = user.id
                
                # Check if log exists
                log_id = log_data.get('id')
                existing_log = db.query(BuildLog).filter(BuildLog.id == log_id).first() if log_id else None
                
                if existing_log:
                    # Update existing log
                    existing_log.title = log_data.get('title', existing_log.title)
                    existing_log.description = log_data.get('description', existing_log.description)
                    existing_log.category = log_data.get('category', existing_log.category)
                    existing_log.date = log_data.get('date', existing_log.date)
                    existing_log.author_id = author_id
                else:
                    # Create new log
                    new_log = BuildLog(
                        id=log_data.get('id', generate_id()),
                        title=log_data.get('title', ''),
                        description=log_data.get('description', ''),
                        category=log_data.get('category', 'General'),
                        date=log_data.get('date', datetime.now().isoformat()),
                        author_id=author_id
                    )
                    db.add(new_log)
            
            db.commit()
        
        # For backward compatibility, also save to JSON
        log_file = "data/logs/build_logs.json"
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=4)
    
    except Exception as e:
        db.rollback()
        print(f"Database error in save_logs: {str(e)}")
        
        # Fallback to JSON only
        log_file = "data/logs/build_logs.json"
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=4)
    
    finally:
        db.close()

# Load resources/documents
def load_resources():
    db = SessionLocal()
    try:
        resources = []
        db_resources = db.query(Resource).order_by(desc(Resource.created_at)).all()
        
        for resource in db_resources:
            # Get author name if available
            author_name = None
            if resource.author_id:
                user = db.query(User).filter(User.id == resource.author_id).first()
                if user:
                    author_name = user.name
            
            resources.append({
                "id": resource.id,
                "title": resource.title,
                "description": resource.description,
                "category": resource.category,
                "url": resource.url,
                "file_path": resource.file_path,
                "author": author_name
            })
        
        if resources:
            return resources
        
        # Fallback to JSON if database is empty
        resource_file = "data/resources/resources.json"
        if os.path.exists(resource_file):
            with open(resource_file, 'r') as f:
                return json.load(f)
        
        return []
    
    except Exception as e:
        print(f"Database error in load_resources: {str(e)}")
        # Fallback to JSON
        resource_file = "data/resources/resources.json"
        if os.path.exists(resource_file):
            with open(resource_file, 'r') as f:
                return json.load(f)
        return []
    
    finally:
        db.close()

# Save resources/documents
def save_resources(resources):
    db = SessionLocal()
    try:
        # Process resources
        if resources:
            # Get existing resource IDs
            existing_ids = [resource.id for resource in db.query(Resource).all()]
            new_ids = [resource['id'] for resource in resources if 'id' in resource]
            
            # Delete resources not in the new list
            for resource_id in existing_ids:
                if resource_id not in new_ids:
                    db.query(Resource).filter(Resource.id == resource_id).delete()
            
            # Update or insert resources
            for resource_data in resources:
                # Find user ID for author if present
                author_id = None
                if 'author' in resource_data and resource_data['author']:
                    user = db.query(User).filter(User.name == resource_data['author']).first()
                    if user:
                        author_id = user.id
                
                # Check if resource exists
                resource_id = resource_data.get('id')
                existing_resource = db.query(Resource).filter(Resource.id == resource_id).first() if resource_id else None
                
                if existing_resource:
                    # Update existing resource
                    existing_resource.title = resource_data.get('title', existing_resource.title)
                    existing_resource.description = resource_data.get('description', existing_resource.description)
                    existing_resource.category = resource_data.get('category', existing_resource.category)
                    existing_resource.url = resource_data.get('url', existing_resource.url)
                    existing_resource.file_path = resource_data.get('file_path', existing_resource.file_path)
                    existing_resource.author_id = author_id
                else:
                    # Create new resource
                    new_resource = Resource(
                        id=resource_data.get('id', generate_id()),
                        title=resource_data.get('title', ''),
                        description=resource_data.get('description', ''),
                        category=resource_data.get('category', 'General'),
                        url=resource_data.get('url', None),
                        file_path=resource_data.get('file_path', None),
                        author_id=author_id
                    )
                    db.add(new_resource)
            
            db.commit()
        
        # For backward compatibility, also save to JSON
        resource_file = "data/resources/resources.json"
        with open(resource_file, 'w') as f:
            json.dump(resources, f, indent=4)
    
    except Exception as e:
        db.rollback()
        print(f"Database error in save_resources: {str(e)}")
        
        # Fallback to JSON only
        resource_file = "data/resources/resources.json"
        with open(resource_file, 'w') as f:
            json.dump(resources, f, indent=4)
    
    finally:
        db.close()

# Load media items
def load_media():
    db = SessionLocal()
    try:
        media_items = []
        db_media = db.query(MediaItem).order_by(desc(MediaItem.created_at)).all()
        
        for media in db_media:
            # Get author name if available
            author_name = None
            if media.author_id:
                user = db.query(User).filter(User.id == media.author_id).first()
                if user:
                    author_name = user.name
            
            media_items.append({
                "id": media.id,
                "title": media.title,
                "description": media.description,
                "media_type": media.media_type,
                "url": media.url,
                "file_path": media.file_path,
                "event": media.event,
                "date": media.date,
                "author": author_name
            })
        
        if media_items:
            return media_items
        
        # Fallback to JSON if database is empty
        media_file = "data/media/media_items.json"
        if os.path.exists(media_file):
            with open(media_file, 'r') as f:
                return json.load(f)
        
        return []
    
    except Exception as e:
        print(f"Database error in load_media: {str(e)}")
        # Fallback to JSON
        media_file = "data/media/media_items.json"
        if os.path.exists(media_file):
            with open(media_file, 'r') as f:
                return json.load(f)
        return []
    
    finally:
        db.close()

# Save media items
def save_media(media_items):
    db = SessionLocal()
    try:
        # Process media items
        if media_items:
            # Get existing media IDs
            existing_ids = [media.id for media in db.query(MediaItem).all()]
            new_ids = [media['id'] for media in media_items if 'id' in media]
            
            # Delete media items not in the new list
            for media_id in existing_ids:
                if media_id not in new_ids:
                    db.query(MediaItem).filter(MediaItem.id == media_id).delete()
            
            # Update or insert media items
            for media_data in media_items:
                # Find user ID for author if present
                author_id = None
                if 'author' in media_data and media_data['author']:
                    user = db.query(User).filter(User.name == media_data['author']).first()
                    if user:
                        author_id = user.id
                
                # Check if media item exists
                media_id = media_data.get('id')
                existing_media = db.query(MediaItem).filter(MediaItem.id == media_id).first() if media_id else None
                
                if existing_media:
                    # Update existing media item
                    existing_media.title = media_data.get('title', existing_media.title)
                    existing_media.description = media_data.get('description', existing_media.description)
                    existing_media.media_type = media_data.get('media_type', existing_media.media_type)
                    existing_media.url = media_data.get('url', existing_media.url)
                    existing_media.file_path = media_data.get('file_path', existing_media.file_path)
                    existing_media.event = media_data.get('event', existing_media.event)
                    existing_media.date = media_data.get('date', existing_media.date)
                    existing_media.author_id = author_id
                else:
                    # Create new media item
                    new_media = MediaItem(
                        id=media_data.get('id', generate_id()),
                        title=media_data.get('title', ''),
                        description=media_data.get('description', ''),
                        media_type=media_data.get('media_type', 'Image'),
                        url=media_data.get('url', None),
                        file_path=media_data.get('file_path', None),
                        event=media_data.get('event', None),
                        date=media_data.get('date', datetime.now().isoformat()),
                        author_id=author_id
                    )
                    db.add(new_media)
            
            db.commit()
        
        # For backward compatibility, also save to JSON
        media_file = "data/media/media_items.json"
        with open(media_file, 'w') as f:
            json.dump(media_items, f, indent=4)
    
    except Exception as e:
        db.rollback()
        print(f"Database error in save_media: {str(e)}")
        
        # Fallback to JSON only
        media_file = "data/media/media_items.json"
        with open(media_file, 'w') as f:
            json.dump(media_items, f, indent=4)
    
    finally:
        db.close()

# Load sponsors
def load_sponsors():
    db = SessionLocal()
    try:
        sponsors = []
        db_sponsors = db.query(Sponsor).order_by(desc(Sponsor.created_at)).all()
        
        for sponsor in db_sponsors:
            sponsors.append({
                "id": sponsor.id,
                "name": sponsor.name,
                "contact_name": sponsor.contact_name,
                "contact_email": sponsor.contact_email,
                "contact_phone": sponsor.contact_phone,
                "sponsorship_level": sponsor.sponsorship_level,
                "amount": sponsor.amount,
                "date_added": sponsor.date_added,
                "notes": sponsor.notes,
                "logo_path": sponsor.logo_path
            })
        
        if sponsors:
            return sponsors
        
        # Fallback to JSON if database is empty
        sponsor_file = "data/sponsors/sponsors.json"
        if os.path.exists(sponsor_file):
            with open(sponsor_file, 'r') as f:
                return json.load(f)
        
        return []
    
    except Exception as e:
        print(f"Database error in load_sponsors: {str(e)}")
        # Fallback to JSON
        sponsor_file = "data/sponsors/sponsors.json"
        if os.path.exists(sponsor_file):
            with open(sponsor_file, 'r') as f:
                return json.load(f)
        return []
    
    finally:
        db.close()

# Save sponsors
def save_sponsors(sponsors):
    db = SessionLocal()
    try:
        # Process sponsors
        if sponsors:
            # Get existing sponsor IDs
            existing_ids = [sponsor.id for sponsor in db.query(Sponsor).all()]
            new_ids = [sponsor['id'] for sponsor in sponsors if 'id' in sponsor]
            
            # Delete sponsors not in the new list
            for sponsor_id in existing_ids:
                if sponsor_id not in new_ids:
                    db.query(Sponsor).filter(Sponsor.id == sponsor_id).delete()
            
            # Update or insert sponsors
            for sponsor_data in sponsors:
                # Check if sponsor exists
                sponsor_id = sponsor_data.get('id')
                existing_sponsor = db.query(Sponsor).filter(Sponsor.id == sponsor_id).first() if sponsor_id else None
                
                if existing_sponsor:
                    # Update existing sponsor
                    existing_sponsor.name = sponsor_data.get('name', existing_sponsor.name)
                    existing_sponsor.contact_name = sponsor_data.get('contact_name', existing_sponsor.contact_name)
                    existing_sponsor.contact_email = sponsor_data.get('contact_email', existing_sponsor.contact_email)
                    existing_sponsor.contact_phone = sponsor_data.get('contact_phone', existing_sponsor.contact_phone)
                    existing_sponsor.sponsorship_level = sponsor_data.get('sponsorship_level', existing_sponsor.sponsorship_level)
                    existing_sponsor.amount = sponsor_data.get('amount', existing_sponsor.amount)
                    existing_sponsor.date_added = sponsor_data.get('date_added', existing_sponsor.date_added)
                    existing_sponsor.notes = sponsor_data.get('notes', existing_sponsor.notes)
                    existing_sponsor.logo_path = sponsor_data.get('logo_path', existing_sponsor.logo_path)
                else:
                    # Create new sponsor
                    new_sponsor = Sponsor(
                        id=sponsor_data.get('id', generate_id()),
                        name=sponsor_data.get('name', ''),
                        contact_name=sponsor_data.get('contact_name', None),
                        contact_email=sponsor_data.get('contact_email', None),
                        contact_phone=sponsor_data.get('contact_phone', None),
                        sponsorship_level=sponsor_data.get('sponsorship_level', 'Bronze'),
                        amount=sponsor_data.get('amount', None),
                        date_added=sponsor_data.get('date_added', datetime.now().isoformat()),
                        notes=sponsor_data.get('notes', None),
                        logo_path=sponsor_data.get('logo_path', None)
                    )
                    db.add(new_sponsor)
            
            db.commit()
        
        # For backward compatibility, also save to JSON
        sponsor_file = "data/sponsors/sponsors.json"
        with open(sponsor_file, 'w') as f:
            json.dump(sponsors, f, indent=4)
    
    except Exception as e:
        db.rollback()
        print(f"Database error in save_sponsors: {str(e)}")
        
        # Fallback to JSON only
        sponsor_file = "data/sponsors/sponsors.json"
        with open(sponsor_file, 'w') as f:
            json.dump(sponsors, f, indent=4)
    
    finally:
        db.close()

# Load events
def load_events():
    db = SessionLocal()
    try:
        events = []
        db_events = db.query(Event).order_by(desc(Event.created_at)).all()
        
        for event in db_events:
            # Get creator name if available
            creator_name = None
            if event.creator_id:
                user = db.query(User).filter(User.id == event.creator_id).first()
                if user:
                    creator_name = user.name
            
            events.append({
                "id": event.id,
                "title": event.title,
                "description": event.description,
                "event_type": event.event_type,
                "start_date": event.start_date,
                "end_date": event.end_date,
                "location": event.location,
                "creator": creator_name
            })
        
        if events:
            return events
        
        # Fallback to JSON if database is empty
        event_file = "data/events/events.json"
        if os.path.exists(event_file):
            with open(event_file, 'r') as f:
                return json.load(f)
        
        return []
    
    except Exception as e:
        print(f"Database error in load_events: {str(e)}")
        # Fallback to JSON
        event_file = "data/events/events.json"
        if os.path.exists(event_file):
            with open(event_file, 'r') as f:
                return json.load(f)
        return []
    
    finally:
        db.close()

# Save events
def save_events(events):
    db = SessionLocal()
    try:
        # Process events
        if events:
            # Get existing event IDs
            existing_ids = [event.id for event in db.query(Event).all()]
            new_ids = [event['id'] for event in events if 'id' in event]
            
            # Delete events not in the new list
            for event_id in existing_ids:
                if event_id not in new_ids:
                    db.query(Event).filter(Event.id == event_id).delete()
            
            # Update or insert events
            for event_data in events:
                # Find user ID for creator if present
                creator_id = None
                if 'creator' in event_data and event_data['creator']:
                    user = db.query(User).filter(User.name == event_data['creator']).first()
                    if user:
                        creator_id = user.id
                
                # Check if event exists
                event_id = event_data.get('id')
                existing_event = db.query(Event).filter(Event.id == event_id).first() if event_id else None
                
                if existing_event:
                    # Update existing event
                    existing_event.title = event_data.get('title', existing_event.title)
                    existing_event.description = event_data.get('description', existing_event.description)
                    existing_event.event_type = event_data.get('event_type', existing_event.event_type)
                    existing_event.start_date = event_data.get('start_date', existing_event.start_date)
                    existing_event.end_date = event_data.get('end_date', existing_event.end_date)
                    existing_event.location = event_data.get('location', existing_event.location)
                    existing_event.creator_id = creator_id
                else:
                    # Create new event
                    new_event = Event(
                        id=event_data.get('id', generate_id()),
                        title=event_data.get('title', ''),
                        description=event_data.get('description', ''),
                        event_type=event_data.get('event_type', 'Meeting'),
                        start_date=event_data.get('start_date', datetime.now().isoformat()),
                        end_date=event_data.get('end_date', None),
                        location=event_data.get('location', None),
                        creator_id=creator_id
                    )
                    db.add(new_event)
            
            db.commit()
        
        # For backward compatibility, also save to JSON
        event_file = "data/events/events.json"
        with open(event_file, 'w') as f:
            json.dump(events, f, indent=4)
    
    except Exception as e:
        db.rollback()
        print(f"Database error in save_events: {str(e)}")
        
        # Fallback to JSON only
        event_file = "data/events/events.json"
        with open(event_file, 'w') as f:
            json.dump(events, f, indent=4)
    
    finally:
        db.close()

# Load team members from database
def load_team_members():
    db = SessionLocal()
    try:
        members = []
        db_users = db.query(User).all()
        
        for user in db_users:
            members.append({
                "username": user.username,
                "name": user.name,
                "role": user.role,
                "email": user.email,
                "department": user.department
            })
        
        if members:
            return members
        
        # Fallback to JSON if database is empty
        user_data_file = "data/users.json"
        if os.path.exists(user_data_file):
            with open(user_data_file, 'r') as f:
                user_data = json.load(f)
            
            json_members = []
            for username, data in user_data.items():
                member = {
                    "username": username,
                    "name": data["name"],
                    "role": data["role"],
                    "email": data["email"]
                }
                json_members.append(member)
            
            return json_members
        
        return []
    
    except Exception as e:
        print(f"Database error in load_team_members: {str(e)}")
        # Fallback to JSON
        user_data_file = "data/users.json"
        if os.path.exists(user_data_file):
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
        
        return []
    
    finally:
        db.close()

# Load messages
def load_messages():
    db = SessionLocal()
    try:
        messages = []
        db_messages = db.query(Message).order_by(desc(Message.created_at)).all()
        
        for message in db_messages:
            # Get author name if available
            author_name = None
            if message.author_id:
                user = db.query(User).filter(User.id == message.author_id).first()
                if user:
                    author_name = user.name
            
            messages.append({
                "id": message.id,
                "title": message.title,
                "content": message.content,
                "category": message.category,
                "author": author_name,
                "parent_id": message.parent_id,
                "created_at": message.created_at.isoformat() if message.created_at else datetime.now().isoformat()
            })
        
        if messages:
            return messages
        
        # Fallback to JSON if database is empty
        message_file = "data/messages/messages.json"
        if os.path.exists(message_file):
            with open(message_file, 'r') as f:
                return json.load(f)
        
        return []
    
    except Exception as e:
        print(f"Database error in load_messages: {str(e)}")
        # Fallback to JSON
        message_file = "data/messages/messages.json"
        if os.path.exists(message_file):
            with open(message_file, 'r') as f:
                return json.load(f)
        return []
    
    finally:
        db.close()

# Save messages
def save_messages(messages):
    db = SessionLocal()
    try:
        # Process messages
        if messages:
            # Get existing message IDs
            existing_ids = [message.id for message in db.query(Message).all()]
            new_ids = [message['id'] for message in messages if 'id' in message]
            
            # Delete messages not in the new list
            for message_id in existing_ids:
                if message_id not in new_ids:
                    db.query(Message).filter(Message.id == message_id).delete()
            
            # Update or insert messages
            for message_data in messages:
                # Find user ID for author if present
                author_id = None
                if 'author' in message_data and message_data['author']:
                    user = db.query(User).filter(User.name == message_data['author']).first()
                    if user:
                        author_id = user.id
                
                # Check if message exists
                message_id = message_data.get('id')
                existing_message = db.query(Message).filter(Message.id == message_id).first() if message_id else None
                
                if existing_message:
                    # Update existing message
                    existing_message.title = message_data.get('title', existing_message.title)
                    existing_message.content = message_data.get('content', existing_message.content)
                    existing_message.category = message_data.get('category', existing_message.category)
                    existing_message.author_id = author_id
                    existing_message.parent_id = message_data.get('parent_id', existing_message.parent_id)
                else:
                    # Create new message
                    new_message = Message(
                        id=message_data.get('id', generate_id()),
                        title=message_data.get('title', ''),
                        content=message_data.get('content', ''),
                        category=message_data.get('category', 'General'),
                        author_id=author_id,
                        parent_id=message_data.get('parent_id', None)
                    )
                    db.add(new_message)
            
            db.commit()
        
        # For backward compatibility, also save to JSON
        message_file = "data/messages/messages.json"
        with open(message_file, 'w') as f:
            json.dump(messages, f, indent=4)
    
    except Exception as e:
        db.rollback()
        print(f"Database error in save_messages: {str(e)}")
        
        # Fallback to JSON only
        message_file = "data/messages/messages.json"
        with open(message_file, 'w') as f:
            json.dump(messages, f, indent=4)
    
    finally:
        db.close()

# Format date from ISO format to user-friendly display
def format_date(iso_date):
    try:
        date_obj = datetime.fromisoformat(iso_date)
        return date_obj.strftime("%m/%d/%Y %I:%M %p")
    except:
        return iso_date

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