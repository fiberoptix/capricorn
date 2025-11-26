#!/usr/bin/env python3
"""
Create database tables from SQLAlchemy models
Run inside Docker container: docker exec capricorn-backend python create_tables.py
"""
from app.core.database import engine
from app.models import Base

print("🚀 Creating database tables...")
print(f"📍 Database URL: {engine.url}")

try:
    Base.metadata.create_all(bind=engine)
    
    print("\n✅ Database tables created successfully!")
    print("\n📋 Tables created:")
    for table_name in Base.metadata.tables.keys():
        print(f"   - {table_name}")
        
except Exception as e:
    print(f"\n❌ Error creating tables: {e}")
    import traceback
    traceback.print_exc()

