#!/bin/bash

# Wait for MySQL to be ready
echo "Waiting for MySQL to be ready..."
while ! mysqladmin ping -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" --silent; do
    sleep 1
done

# Create database if it doesn't exist
mysql -h"$DB_HOST" -u"$DB_USER" -p"$DB_PASSWORD" << EOF
CREATE DATABASE IF NOT EXISTS ${DB_NAME};
USE ${DB_NAME};

# Drop existing tables if they exist
DROP TABLE IF EXISTS account_emailaddress;
DROP TABLE IF EXISTS account_emailconfirmation;
DROP TABLE IF EXISTS socialaccount_socialaccount;
DROP TABLE IF EXISTS socialaccount_socialapp;
DROP TABLE IF EXISTS socialaccount_socialtoken;
DROP TABLE IF EXISTS auth_user;
DROP TABLE IF EXISTS django_session;
DROP TABLE IF EXISTS django_site;
DROP TABLE IF EXISTS django_migrations;
DROP TABLE IF EXISTS django_content_type;
DROP TABLE IF EXISTS django_admin_log;
DROP TABLE IF EXISTS authtoken_token;

# Grant privileges
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'%';
FLUSH PRIVILEGES;
EOF

echo "Database initialization completed." 