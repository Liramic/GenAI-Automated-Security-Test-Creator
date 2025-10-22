"""
Environment Configuration Loader
Loads environment variables from .env file using python-dotenv
"""
import os
from pathlib import Path

def load_env():
    """
    Loads environment variables from .env file.
    Falls back to system environment variables if python-dotenv is not installed.
    """
    try:
        from dotenv import load_dotenv
        
        # Find .env file in project root
        env_path = Path(__file__).parent.parent / '.env'
        
        if env_path.exists():
            load_dotenv(env_path)
            return True
        else:
            print(f"⚠️  Warning: .env file not found at {env_path}")
            print("   Using system environment variables instead.")
            return False
            
    except ImportError:
        print("⚠️  Warning: python-dotenv not installed.")
        print("   Install with: pip install python-dotenv")
        print("   Using system environment variables instead.")
        return False

def get_env_var(key, default=None):
    """
    Get environment variable with optional default value.
    """
    return os.getenv(key, default)

# Auto-load on import
load_env()
