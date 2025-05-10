import os

# Database Configuration
# ---------------------
# You can modify these settings for your local database setup
# If environment variables are set, they will override these values

# Database connection (PostgreSQL)
DB_USER = "postgres"  # Default username for PostgreSQL
DB_PASSWORD = "your_password"  # Replace with your database password
DB_HOST = "localhost"  # Database host address
DB_PORT = "5432"  # Default PostgreSQL port
DB_NAME = "circuit_breakers"  # Name for your database

# Construct the database URL
DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Application Settings
# -------------------
# Default admin user that will be created if no users exist
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_ADMIN_NAME = "Administrator"
DEFAULT_ADMIN_EMAIL = "admin@circuitbreakers.com"

# Function to setup environment variables
def configure_environment():
    """
    Sets up environment variables for the application.
    Priority: Existing environment variables > config.py settings
    """
    # Only set if not already in environment
    if not os.environ.get('DATABASE_URL'):
        os.environ['DATABASE_URL'] = DB_URL
    
    if not os.environ.get('PGUSER'):
        os.environ['PGUSER'] = DB_USER
    
    if not os.environ.get('PGPASSWORD'):
        os.environ['PGPASSWORD'] = DB_PASSWORD
    
    if not os.environ.get('PGHOST'):
        os.environ['PGHOST'] = DB_HOST
    
    if not os.environ.get('PGPORT'):
        os.environ['PGPORT'] = DB_PORT
    
    if not os.environ.get('PGDATABASE'):
        os.environ['PGDATABASE'] = DB_NAME

# Configure environment when module is imported
configure_environment()