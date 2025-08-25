from datetime import datetime, timedelta
import random
from faker import Faker
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseManager:
    def __init__(self):
        """Initialize database connection"""
        self.connection = None
        self._connect()
        
    def _connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv("DB_HOST"),
                port=int(os.getenv("DB_PORT")),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                database=os.getenv("DB_NAME")
            )
            print("✅ Connected to database")
        except Error as e:
            print(f"❌ Connection error: {e}")
            raise

    def add_customer(self, customer_data):
        """Add a new customer"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO customers 
                (customer_id, full_name, email, address, phone, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                customer_data['customer_id'],
                customer_data['full_name'],
                customer_data['email'],
                customer_data['address'],
                customer_data['phone'],
                customer_data['status']
            ))
            self.connection.commit()
            return True
        except Error as e:
            print(f"Error adding customer: {e}")
            return False

    def get_customers(self):
        """Get all customers"""
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM customers")
            return cursor.fetchall()
        except Error as e:
            print(f"Error fetching customers: {e}")
            return []

    def close(self):
        """Close the connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()

def populate_dashboard_data(db):
    """Populate database with realistic test data"""
    fake = Faker()
    
    # Clear existing test data
    with db.connection.cursor() as cursor:
        cursor.execute("DELETE FROM transactions")
        cursor.execute("DELETE FROM room_occupancy")
        cursor.execute("DELETE FROM customers")
        db.connection.commit()
    
    # Generate 50 customers
    for i in range(1, 51):
        customer_id = f"CUST{1000 + i}"
        first_name = fake.first_name()
        last_name = fake.last_name()
        
        db.add_customer({
            'customer_id': customer_id,
            'full_name': f"{first_name} {last_name}",
            'email': f"{first_name.lower()}.{last_name.lower()}@example.com",
            'address': fake.address().replace("\n", ", "),
            'phone': f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}",
            'status': random.choice(['Active', 'Active', 'Active', 'Inactive'])
        })
    
    # Generate transactions for last 6 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    for i in range(200):
        amount = round(random.uniform(50, 500), 2)
        days_ago = random.randint(0, 180)
        transaction_date = end_date - timedelta(days=days_ago)
        customer_id = f"CUST{random.randint(1001, 1050)}"
        
        db.connection.cursor().execute("""
            INSERT INTO transactions (customer_id, amount, transaction_date)
            VALUES (%s, %s, %s)
        """, (customer_id, amount, transaction_date))
    
    # Generate daily room occupancy
    current_date = start_date
    while current_date <= end_date:
        occupied = random.randint(65, 98) if current_date.weekday() >= 5 else random.randint(50, 85)
        
        db.connection.cursor().execute("""
            INSERT INTO room_occupancy (date, occupied_rooms, total_rooms)
            VALUES (%s, %s, %s)
        """, (current_date.date(), occupied, 100))
        
        current_date += timedelta(days=1)
    
    db.connection.commit()
    print("✅ Test data populated successfully")

if __name__ == "__main__":
    try:
        # Install required package if needed
        try:
            from faker import Faker
        except ImportError:
            import subprocess
            subprocess.run(["pip", "install", "faker"])
            from faker import Faker

        db = DatabaseManager()
        populate_dashboard_data(db)
        
        # Verify data
        print(f"\nTotal customers: {len(db.get_customers())}")
        print("Sample customer:", db.get_customers()[0])
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'db' in locals():
            db.close()