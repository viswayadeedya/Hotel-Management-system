# Sample script to populate test data
def populate_test_data(db):
    from datetime import datetime, timedelta
    import random
    
    # Add sample transactions
    for i in range(100):
        amount = random.randint(50, 500)
        days_ago = random.randint(0, 180)
        transaction_date = datetime.now() - timedelta(days=days_ago)
        
        db.connection.cursor().execute("""
            INSERT INTO transactions (customer_id, amount, transaction_date)
            VALUES (%s, %s, %s)
        """, (f"CUST{random.randint(1000, 9999)}", amount, transaction_date))
    
    # Add sample occupancy data
    start_date = datetime.now() - timedelta(days=180)
    for i in range(180):
        date = start_date + timedelta(days=i)
        occupied = random.randint(70, 95)
        total = 100
        
        db.connection.cursor().execute("""
            INSERT INTO room_occupancy (date, occupied_rooms, total_rooms)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                occupied_rooms = VALUES(occupied_rooms),
                total_rooms = VALUES(total_rooms)
        """, (date.date(), occupied, total))
    
    db.connection.commit()