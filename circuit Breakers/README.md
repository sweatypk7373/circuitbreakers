# Circuit Breakers Team Hub

A comprehensive management application for the Circuit Breakers STEM racing team. This Streamlit-based application provides a centralized hub for team communication, project management, resource sharing, and sponsor outreach.

## Features

- **Team Dashboard:** Overview of team activities, events, and announcements
- **Team Calendar:** Schedule and manage team events, meetings, and competitions
- **Project Management:** Task tracking and assignment system
- **Build Logbook:** Documentation of vehicle construction and technical decisions
- **Resources Library:** Centralized repository for team documents and links
- **Team Communication:** Internal messaging system for team members
- **Media Gallery:** Storage for photos, videos, and media assets
- **Sponsors Outreach:** Management of sponsor relationships and contributions
- **Team Profiles:** Team member information and role management
- **Admin Panel:** System configuration and administration tools

## Database Setup

This application uses PostgreSQL for data storage. Here's how to set up the database for your own use:

### Option 1: Quick Configuration (Recommended)

1. Install PostgreSQL on your system if not already installed.
2. Create a new database in PostgreSQL for the application.
3. Edit the `config.py` file to set your database credentials:

```python
# Database Configuration
DB_USER = "your_username"      # Your PostgreSQL username
DB_PASSWORD = "your_password"  # Your PostgreSQL password
DB_HOST = "localhost"          # Database host (usually localhost)
DB_PORT = "5432"               # PostgreSQL port (5432 is default)
DB_NAME = "circuit_breakers"   # Your database name
```

4. Run the application with `streamlit run app.py`

### Option 2: Environment Variables

You can also set environment variables instead of editing the config file:

```bash
# Linux/Mac
export DATABASE_URL=postgresql://username:password@localhost:5432/dbname
export PGUSER=username
export PGPASSWORD=password
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=dbname

# Windows
set DATABASE_URL=postgresql://username:password@localhost:5432/dbname
set PGUSER=username
set PGPASSWORD=password
set PGHOST=localhost
set PGPORT=5432
set PGDATABASE=dbname
```

### Option 3: Manual Database Setup

If you prefer to manually set up the database:

1. Edit the `database.py` file directly:

```python
# Find this section in database.py
# Database connection setup - MODIFY THESE VALUES FOR YOUR OWN DATABASE
# You can either set environment variables or modify the default values below

# Option 1: Set DATABASE_URL directly (recommended)
DATABASE_URL = os.environ.get('DATABASE_URL')

# Option 2: Configure individual components
if not DATABASE_URL:
    # Change these default values to match your database configuration
    db_user = os.environ.get('PGUSER', 'your_username')  # Your database username
    db_password = os.environ.get('PGPASSWORD', 'your_password')  # Your database password
    db_host = os.environ.get('PGHOST', 'localhost')  # Your database host
    db_port = os.environ.get('PGPORT', '5432')  # Your database port
    db_name = os.environ.get('PGDATABASE', 'your_dbname')  # Your database name
```

## Installation

1. Clone this repository
2. Install the required packages:

```bash
pip install streamlit pandas plotly psycopg2-binary sqlalchemy
```

3. Set up your PostgreSQL database (see Database Setup section)
4. Run the application:

```bash
streamlit run app.py
```

## Default Credentials

Upon first initialization, the system creates a default admin user:

- **Username:** admin
- **Password:** admin123

You should change this password immediately after your first login through the Admin Panel.

## Data Migration

The application automatically migrates any existing data from JSON files to the database on first run. This ensures a smooth transition if you've been using an earlier version with JSON storage.

## Connecting from Multiple Computers

To allow team members to access the application from different computers:

1. Host the application on a server with a public IP address
2. Configure the PostgreSQL database to accept remote connections
3. Update the database connection settings to point to your hosted database

## Cloud Deployment Options

This application can be deployed to various cloud platforms:

### Heroku
- Use the Heroku PostgreSQL add-on
- Set the `DATABASE_URL` environment variable in your Heroku app settings

### AWS
- Use Amazon RDS for the PostgreSQL database
- Update the database connection settings accordingly

### Google Cloud
- Use Cloud SQL for PostgreSQL
- Set the proper connection parameters in `config.py`

## Support and Contributions

For questions, issues, or contributions, please contact the Circuit Breakers development team.

## License

This project is licensed under the MIT License - see the LICENSE file for details.