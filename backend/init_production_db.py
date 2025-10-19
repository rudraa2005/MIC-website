#!/usr/bin/env python3
"""
Production database initialization script for Render deployment
"""

import os
from app import app, db
from models import Event, Resource, Contact, Newsletter, ChatSession, ChatMessage
from datetime import datetime, timedelta

def init_production_database():
    """Initialize database for production deployment"""
    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("Production database tables created successfully")
            
            # Check if we have any data
            event_count = Event.query.count()
            resource_count = Resource.query.count()
            contact_count = Contact.query.count()
            newsletter_count = Newsletter.query.count()
            
            print(f"Current data counts:")
            print(f"  - Events: {event_count}")
            print(f"  - Resources: {resource_count}")
            print(f"  - Contacts: {contact_count}")
            print(f"  - Newsletter subscribers: {newsletter_count}")
            
            # Add sample data if no data exists
            if event_count == 0 and resource_count == 0:
                print("Adding sample data for production...")
                add_sample_data()
            
            return True
            
        except Exception as e:
            print(f"Error initializing production database: {e}")
            return False

def add_sample_data():
    """Add sample data to the production database"""
    try:
        # Sample events
        events = [
            Event(
                title="Innovation Workshop 2024",
                description="Join us for an exciting workshop on innovation and technology.",
                date=datetime.now() + timedelta(days=30),
                location="MIC Innovation Center",
                image_url="",
                status="upcoming"
            ),
            Event(
                title="Tech Talk: AI and Machine Learning",
                description="Learn about the latest trends in AI and machine learning.",
                date=datetime.now() + timedelta(days=45),
                location="Online",
                image_url="",
                status="upcoming"
            )
        ]
        
        # Sample resources
        resources = [
            Resource(
                title="Innovation Guide 2024",
                description="A comprehensive guide to innovation in the modern world.",
                category="Guide",
                file_url="",
                is_featured=True
            ),
            Resource(
                title="Technology Trends Report",
                description="Latest technology trends and predictions.",
                category="Report",
                file_url="",
                is_featured=False
            )
        ]
        
        # Add to database
        for event in events:
            db.session.add(event)
        
        for resource in resources:
            db.session.add(resource)
        
        db.session.commit()
        print("Sample data added successfully to production database")
        
    except Exception as e:
        print(f"Error adding sample data: {e}")
        db.session.rollback()

if __name__ == '__main__':
    success = init_production_database()
    if success:
        print("Production database initialization completed successfully!")
    else:
        print("Production database initialization failed!")
        exit(1)
