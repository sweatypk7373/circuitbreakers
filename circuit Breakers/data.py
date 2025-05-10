import json
import os
from datetime import datetime, timedelta
import random

# Function to create initial demo data for the application
def initialize_demo_data():
    # Create directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/tasks", exist_ok=True)
    os.makedirs("data/logs", exist_ok=True)
    os.makedirs("data/resources", exist_ok=True)
    os.makedirs("data/media", exist_ok=True)
    os.makedirs("data/sponsors", exist_ok=True)
    os.makedirs("data/events", exist_ok=True)
    os.makedirs("data/messages", exist_ok=True)
    
    # Sample team members
    team_members = ["Alex Johnson", "Maria Garcia", "Jamal Williams", "Sarah Chen", 
                    "David Kim", "Carlos Rodriguez", "Aisha Patel", "Michael Brown"]
    
    # Generate sample tasks
    tasks = [
        {
            "id": "task001",
            "title": "Design drivetrain mounting brackets",
            "description": "Create CAD files for custom drivetrain mounting brackets",
            "status": "In Progress",
            "priority": "High",
            "assigned_to": "Alex Johnson",
            "created_by": "Admin User",
            "created_at": (datetime.now() - timedelta(days=5)).isoformat(),
            "due_date": (datetime.now() + timedelta(days=3)).isoformat(),
            "category": "Engineering"
        },
        {
            "id": "task002",
            "title": "Update sponsor page on website",
            "description": "Add new sponsors and update existing sponsor information",
            "status": "To Do",
            "priority": "Medium",
            "assigned_to": "Maria Garcia",
            "created_by": "Admin User",
            "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
            "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
            "category": "Outreach"
        },
        {
            "id": "task003",
            "title": "Test electrical system",
            "description": "Complete full electrical system testing and document results",
            "status": "Completed",
            "priority": "Critical",
            "assigned_to": "Jamal Williams",
            "created_by": "Admin User",
            "created_at": (datetime.now() - timedelta(days=10)).isoformat(),
            "due_date": (datetime.now() - timedelta(days=1)).isoformat(),
            "category": "Engineering"
        },
        {
            "id": "task004",
            "title": "Order safety equipment",
            "description": "Order new safety gloves, glasses, and fire extinguishers",
            "status": "Blocked",
            "priority": "High",
            "assigned_to": "Sarah Chen",
            "created_by": "Admin User",
            "created_at": (datetime.now() - timedelta(days=3)).isoformat(),
            "due_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "category": "Logistics"
        }
    ]
    
    # Generate sample build logs
    logs = [
        {
            "id": "log001",
            "date": (datetime.now() - timedelta(days=1)).isoformat(),
            "title": "Drivetrain Assembly Progress",
            "description": "Completed 75% of drivetrain assembly. Need additional bolts and washers for mounting.",
            "author": "Alex Johnson",
            "category": "Engineering",
            "image_description": "Drivetrain assembly with motor mounts"
        },
        {
            "id": "log002",
            "date": (datetime.now() - timedelta(days=3)).isoformat(),
            "title": "Electrical Wiring Completed",
            "description": "Finished main electrical wiring harness. All connections tested and working.",
            "author": "Jamal Williams",
            "category": "Electrical",
            "image_description": "Electrical wiring harness with battery connections"
        },
        {
            "id": "log003",
            "date": (datetime.now() - timedelta(days=5)).isoformat(),
            "title": "Sponsor Meeting Notes",
            "description": "Met with potential new sponsors. Tech Innovations expressed interest in gold-level sponsorship.",
            "author": "Maria Garcia",
            "category": "Outreach",
            "image_description": "Team members meeting with sponsor representatives"
        }
    ]
    
    # Generate sample resources
    resources = [
        {
            "id": "res001",
            "title": "Competition Rulebook 2023",
            "description": "Official competition rulebook with technical specifications and guidelines",
            "category": "Competition",
            "uploaded_by": "Admin User",
            "upload_date": (datetime.now() - timedelta(days=30)).isoformat(),
            "file_type": "PDF",
            "file_size": "3.2 MB",
            "tags": ["rules", "competition", "technical"]
        },
        {
            "id": "res002",
            "title": "Motor Specifications",
            "description": "Technical specifications for the drive motors including power curves",
            "category": "Engineering",
            "uploaded_by": "Alex Johnson",
            "upload_date": (datetime.now() - timedelta(days=15)).isoformat(),
            "file_type": "PDF",
            "file_size": "1.7 MB",
            "tags": ["motors", "specifications", "engineering"]
        },
        {
            "id": "res003",
            "title": "Team Budget Spreadsheet",
            "description": "Current season budget tracking with expenses and remaining funds",
            "category": "Administrative",
            "uploaded_by": "Maria Garcia",
            "upload_date": (datetime.now() - timedelta(days=5)).isoformat(),
            "file_type": "XLSX",
            "file_size": "0.5 MB",
            "tags": ["budget", "finance", "tracking"]
        },
        {
            "id": "res004",
            "title": "Suspension Design Drawings",
            "description": "Technical drawings for front and rear suspension components",
            "category": "Engineering",
            "uploaded_by": "Jamal Williams",
            "upload_date": (datetime.now() - timedelta(days=10)).isoformat(),
            "file_type": "DWG",
            "file_size": "4.1 MB",
            "tags": ["suspension", "design", "engineering"]
        }
    ]
    
    # Generate sample media items
    media_items = [
        {
            "id": "media001",
            "title": "Team Photo at Regional Competition",
            "description": "Full team photo after winning 2nd place at regional competition",
            "category": "Team Photos",
            "uploaded_by": "Sarah Chen",
            "upload_date": (datetime.now() - timedelta(days=45)).isoformat(),
            "media_type": "Photo",
            "tags": ["competition", "team", "awards"]
        },
        {
            "id": "media002",
            "title": "Chassis Assembly Timelapse",
            "description": "Timelapse video showing the full chassis assembly process",
            "category": "Build Process",
            "uploaded_by": "David Kim",
            "upload_date": (datetime.now() - timedelta(days=20)).isoformat(),
            "media_type": "Video",
            "tags": ["chassis", "assembly", "build"]
        },
        {
            "id": "media003",
            "title": "Motor Testing Results",
            "description": "Photos of motor testing setup with power measurement results",
            "category": "Testing",
            "uploaded_by": "Jamal Williams",
            "upload_date": (datetime.now() - timedelta(days=7)).isoformat(),
            "media_type": "Photo",
            "tags": ["motor", "testing", "results"]
        }
    ]
    
    # Generate sample sponsors
    sponsors = [
        {
            "id": "sponsor001",
            "name": "Tech Innovations Inc.",
            "level": "Gold",
            "contribution": "$5,000",
            "contact_name": "Jennifer Lee",
            "contact_email": "jlee@techinnovations.example.com",
            "website": "www.techinnovations-example.com",
            "description": "Leading technology company specializing in electronics and automation",
            "start_date": (datetime.now() - timedelta(days=60)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=305)).isoformat()
        },
        {
            "id": "sponsor002",
            "name": "Metro Engineering",
            "level": "Silver",
            "contribution": "$2,500",
            "contact_name": "Robert Chen",
            "contact_email": "rchen@metroeng.example.com",
            "website": "www.metroengineering-example.com",
            "description": "Engineering firm providing technical support and materials",
            "start_date": (datetime.now() - timedelta(days=90)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=275)).isoformat()
        },
        {
            "id": "sponsor003",
            "name": "Community College of Engineering",
            "level": "Bronze",
            "contribution": "$1,000",
            "contact_name": "Dr. Melissa Johnson",
            "contact_email": "mjohnson@cce.example.edu",
            "website": "www.cce-example.edu",
            "description": "Local engineering college providing educational support and facilities",
            "start_date": (datetime.now() - timedelta(days=120)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=245)).isoformat()
        }
    ]
    
    # Generate sample events
    events = [
        {
            "id": "event001",
            "title": "Team Strategy Meeting",
            "description": "Weekly team strategy meeting to review progress and set goals",
            "start_time": (datetime.now() + timedelta(days=1, hours=16)).isoformat(),
            "end_time": (datetime.now() + timedelta(days=1, hours=18)).isoformat(),
            "location": "Engineering Lab",
            "organizer": "Admin User",
            "participants": ["All team members"],
            "category": "Meeting"
        },
        {
            "id": "event002",
            "title": "Regional Competition",
            "description": "Annual regional competition with teams from 10 counties",
            "start_time": (datetime.now() + timedelta(days=15, hours=8)).isoformat(),
            "end_time": (datetime.now() + timedelta(days=16, hours=17)).isoformat(),
            "location": "State Fairgrounds, Main Exhibition Hall",
            "organizer": "Regional STEM Association",
            "participants": ["All team members"],
            "category": "Competition"
        },
        {
            "id": "event003",
            "title": "Sponsor Demo Day",
            "description": "Demonstration day for current and potential sponsors",
            "start_time": (datetime.now() + timedelta(days=7, hours=13)).isoformat(),
            "end_time": (datetime.now() + timedelta(days=7, hours=16)).isoformat(),
            "location": "School Parking Lot",
            "organizer": "Maria Garcia",
            "participants": ["Maria Garcia", "Admin User", "David Kim", "Sarah Chen"],
            "category": "Outreach"
        },
        {
            "id": "event004",
            "title": "Drivetrain Testing",
            "description": "Performance testing of the new drivetrain configuration",
            "start_time": (datetime.now() + timedelta(days=3, hours=15, minutes=30)).isoformat(),
            "end_time": (datetime.now() + timedelta(days=3, hours=17, minutes=30)).isoformat(),
            "location": "Engineering Lab",
            "organizer": "Alex Johnson",
            "participants": ["Alex Johnson", "Jamal Williams", "Carlos Rodriguez"],
            "category": "Testing"
        }
    ]
    
    # Generate sample messages
    messages = [
        {
            "id": "msg001",
            "title": "Parts Delivery Update",
            "content": "The new suspension components have arrived. Engineering team members, please check with the faculty advisor to coordinate assembly time.",
            "author": "Admin User",
            "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
            "category": "Announcement",
            "priority": "Normal"
        },
        {
            "id": "msg002",
            "title": "Documentation Reminder",
            "content": "All team members should update their work logs by Friday. Media team needs photos of the latest build progress.",
            "author": "Admin User",
            "timestamp": (datetime.now() - timedelta(days=3)).isoformat(),
            "category": "Announcement",
            "priority": "High"
        },
        {
            "id": "msg003",
            "title": "Question about wiring diagram",
            "content": "Can someone clarify the connection between the motor controller and the power distribution board? The diagram on page 5 seems to conflict with the written instructions.",
            "author": "Jamal Williams",
            "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
            "category": "Question",
            "priority": "Normal"
        },
        {
            "id": "msg004",
            "content": "I've uploaded the revised wiring diagram to the resources section. The previous version had an error on pin connections.",
            "author": "Sarah Chen",
            "timestamp": (datetime.now() - timedelta(days=2, hours=2)).isoformat(),
            "category": "Response",
            "priority": "Normal",
            "parent_id": "msg003"
        }
    ]
    
    # Save all data
    with open("data/tasks/tasks.json", 'w') as f:
        json.dump(tasks, f, indent=4)
    
    with open("data/logs/build_logs.json", 'w') as f:
        json.dump(logs, f, indent=4)
    
    with open("data/resources/resources.json", 'w') as f:
        json.dump(resources, f, indent=4)
    
    with open("data/media/media_items.json", 'w') as f:
        json.dump(media_items, f, indent=4)
    
    with open("data/sponsors/sponsors.json", 'w') as f:
        json.dump(sponsors, f, indent=4)
    
    with open("data/events/events.json", 'w') as f:
        json.dump(events, f, indent=4)
    
    with open("data/messages/messages.json", 'w') as f:
        json.dump(messages, f, indent=4)

# Call this function when importing the module to ensure data is initialized
if __name__ == "__main__":
    initialize_demo_data()
