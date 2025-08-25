from db_helper import DatabaseManager, hash_password

def test_authentication():
    test_email = "test@example.com"
    test_password = "TestPassword123"
    
    with DatabaseManager() as db:
        # Cleanup existing test user
        with db.connection.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE email = %s", (test_email,))
            db.connection.commit()
        
        # Test registration
        print("\n=== TESTING REGISTRATION ===")
        success, message = db.register_user(
            "Test User",
            test_email,
            test_password,
            "Male"
        )
        print(f"Registration result: {success}, {message}")
        
        # Test authentication
        print("\n=== TESTING AUTHENTICATION ===")
        print("Testing with CORRECT password:")
        user = db.authenticate_user(test_email, test_password)
        print(f"Auth result: {bool(user)}")
        
        print("\nTesting with WRONG password:")
        user = db.authenticate_user(test_email, "WrongPassword")
        print(f"Auth result: {bool(user)}")

if __name__ == "__main__":
    test_authentication()