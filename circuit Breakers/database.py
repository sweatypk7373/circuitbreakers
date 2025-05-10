import os
import json
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection setup - MODIFY THESE VALUES FOR YOUR OWN DATABASE
# You can either set environment variables or modify the default values below

# Option 1: Set DATABASE_URL directly (recommended)
DATABASE_URL = os.environ.get('DATABASE_URL')

# Option 2: Configure individual components
if not DATABASE_URL:
    # Change these default values to match your database configuration
    db_user = os.environ.get('PGUSER', 'postgres')  # Your database username
    db_password = os.environ.get('PGPASSWORD', 'your_password')  # Your database password
    db_host = os.environ.get('PGHOST', 'localhost')  # Your database host
    db_port = os.environ.get('PGPORT', '5432')  # Your database port
    db_name = os.environ.get('PGDATABASE', 'circuit_breakers')  # Your database name
    
    DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    print(f"Constructed DATABASE_URL from local configuration")

print(f"Connecting to database...")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    name = Column(String)
    email = Column(String)
    role = Column(String)
    department = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    tasks = relationship("Task", back_populates="assignee", cascade="all, delete-orphan")
    logs = relationship("BuildLog", back_populates="author", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="author", cascade="all, delete-orphan")
    resources = relationship("Resource", back_populates="author", cascade="all, delete-orphan")
    media_items = relationship("MediaItem", back_populates="author", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="creator", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(Text)
    status = Column(String)
    priority = Column(String)
    due_date = Column(String, nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    assignee = relationship("User", back_populates="tasks")

class BuildLog(Base):
    __tablename__ = "build_logs"
    
    id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(Text)
    category = Column(String)
    date = Column(String)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    author = relationship("User", back_populates="logs")

class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(Text)
    category = Column(String)
    url = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    author = relationship("User", back_populates="resources")

class MediaItem(Base):
    __tablename__ = "media_items"
    
    id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(Text, nullable=True)
    media_type = Column(String)
    url = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    event = Column(String, nullable=True)
    date = Column(String)
    author_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    author = relationship("User", back_populates="media_items")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True)
    title = Column(String)
    content = Column(Text)
    category = Column(String)
    author_id = Column(Integer, ForeignKey("users.id"))
    parent_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    author = relationship("User", back_populates="messages")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(Text, nullable=True)
    event_type = Column(String)
    start_date = Column(String)
    end_date = Column(String, nullable=True)
    location = Column(String, nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    creator = relationship("User", back_populates="events")

class Sponsor(Base):
    __tablename__ = "sponsors"
    
    id = Column(String, primary_key=True)
    name = Column(String)
    contact_name = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    sponsorship_level = Column(String)
    amount = Column(Float, nullable=True)
    date_added = Column(String)
    notes = Column(Text, nullable=True)
    logo_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

class AppSetting(Base):
    __tablename__ = "app_settings"
    
    key = Column(String, primary_key=True)
    value = Column(String)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

# Initialize database
def create_tables():
    Base.metadata.create_all(bind=engine)

# Function to migrate data from JSON to database
def migrate_data_from_json():
    db = SessionLocal()
    try:
        # First check if there's any data in the database already
        if db.query(User).count() > 0:
            logger.info("Database already has data, skipping migration")
            return
        
        # Migrate users
        user_mapping = {}  # Store mapping of usernames to user IDs
        if os.path.exists("data/users.json"):
            with open("data/users.json", 'r') as f:
                users_data = json.load(f)
                for username, user_data in users_data.items():
                    user = User(
                        username=username,
                        password=user_data.get('password', ''),
                        name=user_data.get('name', ''),
                        email=user_data.get('email', ''),
                        role=user_data.get('role', 'member'),
                        department=user_data.get('department', None),
                        created_at=datetime.fromisoformat(user_data.get('created_at', datetime.now().isoformat()))
                    )
                    db.add(user)
                    db.flush()  # To get the user ID
                    user_mapping[username] = user.id
            logger.info(f"Migrated {len(users_data)} users")
        
        # Migrate tasks
        if os.path.exists("data/tasks/tasks.json"):
            with open("data/tasks/tasks.json", 'r') as f:
                tasks_data = json.load(f)
                for task_data in tasks_data:
                    # Map assignee to user ID if present
                    assignee_id = None
                    assignee = task_data.get('assignee', None)
                    if assignee and assignee in user_mapping:
                        assignee_id = user_mapping[assignee]
                    
                    task = Task(
                        id=task_data.get('id', ''),
                        title=task_data.get('title', ''),
                        description=task_data.get('description', ''),
                        status=task_data.get('status', 'Not Started'),
                        priority=task_data.get('priority', 'Medium'),
                        due_date=task_data.get('due_date', None),
                        assignee_id=assignee_id,
                        created_at=datetime.now()
                    )
                    db.add(task)
            logger.info(f"Migrated {len(tasks_data)} tasks")
                    
        # Migrate build logs
        if os.path.exists("data/logs/build_logs.json"):
            with open("data/logs/build_logs.json", 'r') as f:
                logs_data = json.load(f)
                for log_data in logs_data:
                    # Map author to user ID if present
                    author_id = None
                    author = log_data.get('author', None)
                    if author and author in user_mapping:
                        author_id = user_mapping[author]
                    else:
                        # Assign to admin if author not found
                        admin_user = db.query(User).filter(User.role == 'admin').first()
                        if admin_user:
                            author_id = admin_user.id
                    
                    log = BuildLog(
                        id=log_data.get('id', ''),
                        title=log_data.get('title', ''),
                        description=log_data.get('description', ''),
                        category=log_data.get('category', 'General'),
                        date=log_data.get('date', datetime.now().isoformat()),
                        author_id=author_id,
                        created_at=datetime.now()
                    )
                    db.add(log)
            logger.info(f"Migrated {len(logs_data)} build logs")
                    
        # Migrate resources
        if os.path.exists("data/resources/resources.json"):
            with open("data/resources/resources.json", 'r') as f:
                resources_data = json.load(f)
                for resource_data in resources_data:
                    # Map author to user ID if present
                    author_id = None
                    author = resource_data.get('author', None)
                    if author and author in user_mapping:
                        author_id = user_mapping[author]
                    else:
                        # Assign to admin if author not found
                        admin_user = db.query(User).filter(User.role == 'admin').first()
                        if admin_user:
                            author_id = admin_user.id
                    
                    resource = Resource(
                        id=resource_data.get('id', ''),
                        title=resource_data.get('title', ''),
                        description=resource_data.get('description', ''),
                        category=resource_data.get('category', 'General'),
                        url=resource_data.get('url', None),
                        file_path=resource_data.get('file_path', None),
                        author_id=author_id,
                        created_at=datetime.now()
                    )
                    db.add(resource)
            logger.info(f"Migrated {len(resources_data)} resources")
        
        # Migrate media items
        if os.path.exists("data/media/media_items.json"):
            with open("data/media/media_items.json", 'r') as f:
                media_data = json.load(f)
                for media_item_data in media_data:
                    # Map author to user ID if present
                    author_id = None
                    author = media_item_data.get('author', None)
                    if author and author in user_mapping:
                        author_id = user_mapping[author]
                    else:
                        # Assign to admin if author not found
                        admin_user = db.query(User).filter(User.role == 'admin').first()
                        if admin_user:
                            author_id = admin_user.id
                    
                    media_item = MediaItem(
                        id=media_item_data.get('id', ''),
                        title=media_item_data.get('title', ''),
                        description=media_item_data.get('description', ''),
                        media_type=media_item_data.get('media_type', 'Image'),
                        url=media_item_data.get('url', None),
                        file_path=media_item_data.get('file_path', None),
                        event=media_item_data.get('event', None),
                        date=media_item_data.get('date', datetime.now().isoformat()),
                        author_id=author_id,
                        created_at=datetime.now()
                    )
                    db.add(media_item)
            logger.info(f"Migrated {len(media_data)} media items")
                    
        # Migrate messages
        if os.path.exists("data/messages/messages.json"):
            with open("data/messages/messages.json", 'r') as f:
                messages_data = json.load(f)
                for message_data in messages_data:
                    # Map author to user ID if present
                    author_id = None
                    author = message_data.get('author', None)
                    if author and author in user_mapping:
                        author_id = user_mapping[author]
                    else:
                        # Assign to admin if author not found
                        admin_user = db.query(User).filter(User.role == 'admin').first()
                        if admin_user:
                            author_id = admin_user.id
                    
                    message = Message(
                        id=message_data.get('id', ''),
                        title=message_data.get('title', ''),
                        content=message_data.get('content', ''),
                        category=message_data.get('category', 'General'),
                        author_id=author_id,
                        parent_id=message_data.get('parent_id', None),
                        created_at=datetime.now()
                    )
                    db.add(message)
            logger.info(f"Migrated {len(messages_data)} messages")
                    
        # Migrate events
        if os.path.exists("data/events/events.json"):
            with open("data/events/events.json", 'r') as f:
                events_data = json.load(f)
                for event_data in events_data:
                    # Map creator to user ID if present
                    creator_id = None
                    creator = event_data.get('creator', None)
                    if creator and creator in user_mapping:
                        creator_id = user_mapping[creator]
                    else:
                        # Assign to admin if creator not found
                        admin_user = db.query(User).filter(User.role == 'admin').first()
                        if admin_user:
                            creator_id = admin_user.id
                    
                    event = Event(
                        id=event_data.get('id', ''),
                        title=event_data.get('title', ''),
                        description=event_data.get('description', ''),
                        event_type=event_data.get('event_type', 'Meeting'),
                        start_date=event_data.get('start_date', datetime.now().isoformat()),
                        end_date=event_data.get('end_date', None),
                        location=event_data.get('location', None),
                        creator_id=creator_id,
                        created_at=datetime.now()
                    )
                    db.add(event)
            logger.info(f"Migrated {len(events_data)} events")
                    
        # Migrate sponsors
        if os.path.exists("data/sponsors/sponsors.json"):
            with open("data/sponsors/sponsors.json", 'r') as f:
                sponsors_data = json.load(f)
                for sponsor_data in sponsors_data:
                    sponsor = Sponsor(
                        id=sponsor_data.get('id', ''),
                        name=sponsor_data.get('name', ''),
                        contact_name=sponsor_data.get('contact_name', None),
                        contact_email=sponsor_data.get('contact_email', None),
                        contact_phone=sponsor_data.get('contact_phone', None),
                        sponsorship_level=sponsor_data.get('sponsorship_level', 'Bronze'),
                        amount=sponsor_data.get('amount', None),
                        date_added=sponsor_data.get('date_added', datetime.now().isoformat()),
                        notes=sponsor_data.get('notes', None),
                        logo_path=sponsor_data.get('logo_path', None),
                        created_at=datetime.now()
                    )
                    db.add(sponsor)
            logger.info(f"Migrated {len(sponsors_data)} sponsors")
        
        # Migrate app settings
        if os.path.exists("data/settings.json"):
            with open("data/settings.json", 'r') as f:
                settings_data = json.load(f)
                for key, value in settings_data.items():
                    # Convert non-string values to string
                    if not isinstance(value, str):
                        if isinstance(value, bool) or isinstance(value, int) or isinstance(value, float):
                            value = str(value)
                        else:
                            value = json.dumps(value)
                            
                    setting = AppSetting(
                        key=key,
                        value=value,
                        updated_at=datetime.now()
                    )
                    db.add(setting)
            logger.info("Migrated app settings")
                        
        db.commit()
        logger.info("Data migration completed successfully")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error during migration: {str(e)}")
        raise
    finally:
        db.close()

# Database access functions
def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

# Initialize database when module is imported
create_tables()
migrate_data_from_json()