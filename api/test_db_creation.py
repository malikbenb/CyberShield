from database import Base, engine
from models_fastapi import User, ScanHistory, Report, Subscription, SubscriptionPlan
print("Attempting to create database tables...")
try:
Base.metadata.create_all(engine)
print("Tables created successfully!")
except Exception as e:
print(f"Error creating tables: {e}")
