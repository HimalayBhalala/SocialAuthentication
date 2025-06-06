#!/usr/bin/env python
"""
Script to fix Django migration issues with allauth and custom User model.
This script ensures migrations run in the correct order.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.core.management.base import CommandError

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'social_authentication.settings')
    django.setup()

def run_management_command(command_args):
    """Run a Django management command"""
    try:
        execute_from_command_line(['manage.py'] + command_args)
        return True
    except CommandError as e:
        print(f"Command failed: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def fix_migrations():
    """Fix migration issues by running them in correct order"""
    print("🔧 Starting migration fix process...")
    
    # Step 1: Make migrations for authentication app first
    print("📝 Creating migrations for authentication app...")
    if not run_management_command(['makemigrations', 'authentication']):
        print("❌ Failed to make migrations for authentication app")
        return False
    
    # Step 2: Run core Django migrations first (contenttypes, auth, etc.)
    print("🚀 Running core Django migrations...")
    core_apps = ['contenttypes', 'auth', 'sessions', 'sites', 'admin']
    for app in core_apps:
        print(f"  Running {app} migrations...")
        if not run_management_command(['migrate', app]):
            print(f"❌ Failed to migrate {app}")
            return False
    
    # Step 3: Run authentication app migrations
    print("🔐 Running authentication app migrations...")
    if not run_management_command(['migrate', 'authentication']):
        print("❌ Failed to migrate authentication app")
        return False
    
    # Step 4: Run allauth migrations
    print("🌐 Running allauth migrations...")
    allauth_apps = ['account', 'socialaccount']
    for app in allauth_apps:
        print(f"  Running {app} migrations...")
        if not run_management_command(['migrate', app]):
            print(f"❌ Failed to migrate {app}")
            return False
    
    # Step 5: Run remaining migrations
    print("📦 Running remaining migrations...")
    if not run_management_command(['migrate']):
        print("❌ Failed to run remaining migrations")
        return False
    
    print("✅ Migration fix completed successfully!")
    return True

def main():
    """Main function"""
    setup_django()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--use-sqlite':
        os.environ['USE_SQLITE_FALLBACK'] = 'true'
        print("🗄️  Using SQLite database for testing...")
    
    success = fix_migrations()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 