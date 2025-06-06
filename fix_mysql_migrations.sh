#!/bin/bash

echo "🔧 Fixing Django MySQL Migration Issues"
echo "======================================"

# Step 1: Setup MySQL database (you'll need to adjust these credentials)
echo "📊 Setting up MySQL database..."
echo "Make sure MySQL is running and create the database:"
echo "  mysql -u root -p"
echo "  CREATE DATABASE social_auth_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
echo "  CREATE USER 'django_user'@'localhost' IDENTIFIED BY 'secure_password_123';"
echo "  GRANT ALL PRIVILEGES ON social_auth_db.* TO 'django_user'@'localhost';"
echo "  FLUSH PRIVILEGES;"
echo ""

# Step 2: Set environment variables
export DB_ENGINE="django.db.backends.mysql"
export DB_NAME="social_auth_db"
export DB_USER="django_user"
export DB_PASSWORD="secure_password_123"
export DB_HOST="localhost"
export DB_PORT="3306"

# Step 3: Activate virtual environment
echo "🐍 Activating virtual environment..."
source social_venv/bin/activate

# Step 4: Install dependencies
echo "📦 Installing MySQL dependencies..."
pip install mysqlclient

# Step 5: Create static directory if it doesn't exist
echo "📁 Creating static directory..."
mkdir -p static

# Step 6: Reset migrations (DANGEROUS - only do this if you can lose data)
echo "⚠️  WARNING: This will reset all migrations!"
read -p "Do you want to reset migrations? This will DELETE ALL DATA! (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Removing migration files..."
    find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
    find . -path "*/migrations/*.pyc" -delete
    
    echo "📝 Creating fresh migrations..."
    python manage.py makemigrations authentication
    python manage.py makemigrations
fi

# Step 7: Run migrations in correct order
echo "🚀 Running migrations in correct order..."

# First, ensure basic Django apps are migrated
python manage.py migrate contenttypes
python manage.py migrate auth
python manage.py migrate sessions
python manage.py migrate sites

# Then migrate our custom authentication app
python manage.py migrate authentication

# Finally, migrate allauth apps
python manage.py migrate account
python manage.py migrate socialaccount

# Migrate any remaining apps
python manage.py migrate

echo "✅ Migration fix completed!"
echo "🎉 You can now run: python manage.py runserver" 