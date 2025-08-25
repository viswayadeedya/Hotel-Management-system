from db_helper import DatabaseManager

if __name__ == "__main__":
    with DatabaseManager() as db:
        print("✅ Database tables created successfully")