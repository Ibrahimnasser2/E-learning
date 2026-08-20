#!/usr/bin/env python3
"""
سكريبت إعداد قاعدة البيانات لروبوت المحادثة RAG - إصدار Windows
هذا السكريبت يقوم بإعداد PostgreSQL مع إضافة pgvector لـ Windows
"""

import psycopg2
import sys
import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

def setup_database():
    """
    إعداد قاعدة البيانات لروبوت المحادثة RAG
    يقوم بإنشاء قاعدة البيانات والجداول المطلوبة
    """
    
    # معاملات الاتصال بقاعدة البيانات
    DB_HOST = "localhost"
    DB_PORT = "5432"
    DB_USER = "postgres"
    DB_PASSWORD = "hema1234"
    DB_NAME = "maha_db"
    
    try:
        # أولاً، الاتصال بـ PostgreSQL لإنشاء قاعدة البيانات إذا لم تكن موجودة
        print("Connecting to PostgreSQL...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres"  # الاتصال بقاعدة البيانات الافتراضية أولاً
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # التحقق من وجود قاعدة البيانات
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Creating database '{DB_NAME}'...")
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"Database '{DB_NAME}' created successfully!")
        else:
            print(f"Database '{DB_NAME}' already exists.")
        
        cursor.close()
        conn.close()
        
        # الآن الاتصال بقاعدة البيانات rag_db وتشغيل سكريبت التهيئة
        print("Connecting to database rag_db...")
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # قراءة وتنفيذ سكريبت التهيئة SQL
        init_sql_path = os.path.join(os.path.dirname(__file__), "init.sql")
        print(f"Reading initialization script from: {init_sql_path}")
        
        with open(init_sql_path, 'r') as file:
            sql_script = file.read()
        
        # تقسيم السكريبت إلى عبارات منفصلة وتنفيذها
        statements = sql_script.split(';')
        
        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                    print(f"Executed: {statement[:50]}...")
                except Exception as e:
                    print(f"Warning: Cannot execute statement: {e}")
                    print(f"Statement: {statement[:100]}...")
        
        print("Database setup completed successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error setting up database: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check if the password is correct")
        print("3. Make sure PostgreSQL is installed with pgvector extension")
        print("4. Check if postgres user has the required permissions")
        sys.exit(1)

if __name__ == "__main__":
    print("RAG Chatbot Database Setup - Windows")
    print("=" * 50)
    
    print("\n⚠️  Prerequisites:")
    print("1. PostgreSQL must be installed with pgvector extension")
    print("2. Database 'rag_db' must exist")
    print("3. User 'postgres' with password 'hema1234' must exist")
    print("4. User must have appropriate permissions")
    
    input("\nPress Enter to continue with database setup...")
    setup_database() 