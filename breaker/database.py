"""
This module provides JSON-based data storage functionality as a replacement
for the SQLAlchemy database functionality.
"""

import os
import json
from datetime import datetime

# Create data directory
os.makedirs("data", exist_ok=True)

# Define paths for data files
USERS_FILE = "data/users.json"
TASKS_FILE = "data/tasks.json"
BUILD_LOGS_FILE = "data/build_logs.json"
RESOURCES_FILE = "data/resources.json"
MEDIA_ITEMS_FILE = "data/media_items.json"
MESSAGES_FILE = "data/messages.json"
EVENTS_FILE = "data/events.json"
SPONSORS_FILE = "data/sponsors.json"
SETTINGS_FILE = "data/settings.json"

# Initialize default files if they don't exist
def create_tables():
    """Create all data files if they don't exist."""
    # Users
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)
    
    # Tasks
    if not os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, 'w') as f:
            json.dump([], f)
    
    # Build Logs
    if not os.path.exists(BUILD_LOGS_FILE):
        with open(BUILD_LOGS_FILE, 'w') as f:
            json.dump([], f)
    
    # Resources
    if not os.path.exists(RESOURCES_FILE):
        with open(RESOURCES_FILE, 'w') as f:
            json.dump([], f)
    
    # Media Items
    if not os.path.exists(MEDIA_ITEMS_FILE):
        with open(MEDIA_ITEMS_FILE, 'w') as f:
            json.dump([], f)
    
    # Messages
    if not os.path.exists(MESSAGES_FILE):
        with open(MESSAGES_FILE, 'w') as f:
            json.dump([], f)
    
    # Events
    if not os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, 'w') as f:
            json.dump([], f)
    
    # Sponsors
    if not os.path.exists(SPONSORS_FILE):
        with open(SPONSORS_FILE, 'w') as f:
            json.dump([], f)
    
    # Settings
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'w') as f:
            json.dump({}, f)
    
    return True

def migrate_data_from_json():
    """
    This function is kept for compatibility, but doesn't do anything
    since we're already using JSON files as the primary data store.
    """
    pass

def get_db():
    """
    This function is kept for compatibility but returns None.
    JSON operations are performed directly in the utility functions.
    """
    return None

# Stub classes to maintain compatibility with existing code
class User:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class Task:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class BuildLog:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class Resource:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class MediaItem:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class Message:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class Event:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class Sponsor:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class AppSetting:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# Dummy session class for compatibility
class SessionLocal:
    def __init__(self):
        pass
    
    def close(self):
        pass
    
    def commit(self):
        pass
    
    def rollback(self):
        pass
    
    def add(self, obj):
        pass
    
    def query(self, cls):
        return DummyQuery(cls)

class DummyQuery:
    def __init__(self, cls):
        self.cls = cls
    
    def filter(self, *args, **kwargs):
        return self
    
    def first(self):
        return None
    
    def all(self):
        return []
    
    def count(self):
        return 0

# Utility functions to read/write JSON files
def read_json_file(file_path, default=None):
    """Read and return data from a JSON file."""
    if default is None:
        default = [] if not file_path.endswith(('settings.json', 'users.json')) else {}
        
    try:
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, 'r') as f:
                return json.load(f)
        return default
    except Exception as e:
        print(f"Error reading {file_path}: {str(e)}")
        return default

def write_json_file(file_path, data):
    """Write data to a JSON file."""
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error writing to {file_path}: {str(e)}")
        return False
