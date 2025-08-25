import mysql.connector
from mysql.connector import Error, errorcode
from dotenv import load_dotenv
import os
import hashlib
import re
from typing import Optional, Dict, Tuple, List
import logging
from datetime import datetime, timedelta
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class DatabaseManager:
    def __init__(self):
        """Initialize database connection with enhanced error handling"""
        self.connection = None
        self._connect()
        self._initialize_database()
        logger.info("DatabaseManager initialized")

    def _connect(self) -> bool:
        """Establish secure connection with retry logic"""
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                self.connection = mysql.connector.connect(
                    host=os.getenv("DB_HOST"),
                    port=int(os.getenv("DB_PORT")),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    database=os.getenv("DB_NAME"),
                    ssl_disabled=False,
                    connect_timeout=5,
                    connection_timeout=30,
                    autocommit=True
                )

                if self.connection.is_connected():
                    logger.info(f"✅ Connected to MySQL database (Attempt {attempt + 1})")
                    return True

            except Error as err:
                logger.error(f"❌ Connection attempt {attempt + 1} failed: {err}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    continue
                raise RuntimeError(f"Failed to connect after {max_retries} attempts") from err

    def _initialize_database(self) -> None:
        """Initialize database schema with verification and updates"""
        if not self.connection or not self.connection.is_connected():
            self._connect()

        tables = {
            "users": """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    full_name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL COLLATE utf8mb4_bin,
                    password_hash VARCHAR(255) NOT NULL,
                    gender ENUM('Male','Female','Other') NOT NULL,
                    role ENUM('admin','staff','customer') NOT NULL DEFAULT 'customer',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE INDEX idx_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            "user_sessions": """
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id VARCHAR(255) PRIMARY KEY,
                    user_id INT NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            "auth_logs": """
                CREATE TABLE IF NOT EXISTS auth_logs (
                    log_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NULL,
                    email VARCHAR(100) NOT NULL,
                    action ENUM('register','login','logout','fail') NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            "customers": """
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id VARCHAR(20) PRIMARY KEY,
                    user_id INT,
                    full_name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL COLLATE utf8mb4_bin,
                    address TEXT NOT NULL,
                    phone VARCHAR(20) NOT NULL,
                    status ENUM('Active','Inactive') NOT NULL DEFAULT 'Active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                    UNIQUE INDEX idx_email (email),
                    INDEX idx_status (status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            "staff": """
                CREATE TABLE IF NOT EXISTS staff (
                    staff_id VARCHAR(20) PRIMARY KEY,
                    user_id INT,
                    full_name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) NOT NULL COLLATE utf8mb4_bin,
                    phone VARCHAR(20) NOT NULL,
                    address TEXT NOT NULL,
                    status ENUM('Active','Inactive') NOT NULL DEFAULT 'Active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
                    UNIQUE INDEX idx_staff_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            "reservations": """
                CREATE TABLE IF NOT EXISTS reservations (
                    reservation_id VARCHAR(20) PRIMARY KEY,
                    user_id INT NOT NULL,
                    customer_id VARCHAR(20),
                    guest_name VARCHAR(100) NOT NULL,
                    room_type VARCHAR(50) NOT NULL,
                    checkin_date DATE NOT NULL,
                    checkout_date DATE NOT NULL,
                    booking_amount DECIMAL(10,2) NOT NULL,
                    payment_status ENUM('Paid', 'Pending', 'Cancelled') DEFAULT 'Pending',
                    fulfillment_status ENUM('Confirmed', 'Pending', 'Cancelled') DEFAULT 'Pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL,
                    INDEX idx_reservations_created (created_at),
                    INDEX idx_reservations_user (user_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            "transactions": """
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
                    customer_id VARCHAR(20),
                    reservation_id VARCHAR(20),
                    amount DECIMAL(10,2) NOT NULL,
                    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) 
                        ON DELETE SET NULL
                        ON UPDATE CASCADE,
                    FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id)
                        ON DELETE SET NULL
                        ON UPDATE CASCADE,
                    INDEX idx_transactions_date (transaction_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            "room_occupancy": """
                CREATE TABLE IF NOT EXISTS room_occupancy (
                    record_id INT AUTO_INCREMENT PRIMARY KEY,
                    date DATE NOT NULL,
                    occupied_rooms INT NOT NULL,
                    total_rooms INT NOT NULL,
                    UNIQUE KEY unique_date (date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """,
            "password_recovery_requests": """
                CREATE TABLE IF NOT EXISTS password_recovery_requests (
                    request_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    username VARCHAR(100) NOT NULL,
                    full_name VARCHAR(100) NOT NULL,
                    request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    INDEX idx_recovery_status (status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        }

        # Critical columns that must exist
        required_columns = {
            "users": [("role", "ENUM('admin','staff','customer') NOT NULL DEFAULT 'customer'")],
            "reservations": [
                ("room_type", "VARCHAR(50) NOT NULL"),
                ("checkout_date", "DATE NOT NULL"),
                ("fulfillment_status", "ENUM('Confirmed', 'Pending', 'Cancelled') DEFAULT 'Pending'")
            ],
            "customers": [
                ("user_id", "INT"),
                ("FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL")
            ]
        }

        try:
            with self.connection.cursor() as cursor:
                # Create all tables
                for table_name, ddl in tables.items():
                    try:
                        cursor.execute(ddl)
                        logger.info(f"Table '{table_name}' created/verified")
                    except Error as err:
                        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                            logger.debug(f"Table '{table_name}' exists, checking columns...")
                            # Add missing columns
                            if table_name in required_columns:
                                for column, definition in required_columns[table_name]:
                                    try:
                                        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column} {definition}")
                                        logger.info(f"Added column '{column}' to '{table_name}'")
                                    except Error as alter_err:
                                        if alter_err.errno == errorcode.ER_DUP_FIELDNAME:
                                            logger.debug(f"Column '{column}' already exists")
                                        else:
                                            logger.error(f"Error adding column '{column}': {alter_err}")
                                            raise
                        else:
                            raise

                self.connection.commit()
                self._create_default_admin()

        except Error as err:
            logger.error(f"Database initialization failed: {err}")
            raise

    def _create_default_admin(self):
        """Create default admin user if not exists"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM users WHERE email = 'admin@example.com'")
                if not cursor.fetchone():
                    password_hash = hashlib.sha256("admin123".encode("utf-8")).hexdigest()
                    cursor.execute(
                        """
                        INSERT INTO users 
                        (full_name, email, password_hash, gender, role)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        ("Admin User", "admin@example.com", password_hash, "Male", "admin")
                    )
                    self.connection.commit()
                    logger.info("Default admin user created")
        except Error as err:
            logger.error(f"Error creating default admin: {err}")

    def authenticate_user(self, email: str, password: str, user_type: str) -> Optional[Dict]:
        """Authenticate user with role verification and complete data"""
        try:
            email = email.strip().lower()
            password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

            query = """
                SELECT user_id, full_name, email, gender, role, is_active 
                FROM users 
                WHERE email = %s COLLATE utf8mb4_bin 
                AND password_hash = %s
                AND is_active = TRUE
                AND role = %s
            """

            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, (email, password_hash, user_type))
                user = cursor.fetchone()

                if user:
                    self._log_auth_action(user["user_id"], email, "login")
                    logger.info(f"Successful {user_type} login for {email}")

                    # For staff, get additional details from staff table
                    if user_type == "staff":
                        staff_details = self.get_staff_by_email(email)
                        if not staff_details:
                            logger.error(f"Staff record missing for {email}")
                            return None
                        user.update(staff_details)

                    # For customers, get additional details from customers table
                    elif user_type == "customer":
                        customer_details = self.get_customer_by_email(email)
                        if customer_details:
                            user.update(customer_details)

                    return user
                else:
                    self._log_auth_action(None, email, "fail")
                    logger.warning(f"Failed {user_type} login attempt for {email}")
                    return None

        except Error as err:
            logger.error(f"Authentication error for {email}: {err}")
            return None

    def register_user(
            self, full_name: str, email: str, password: str, gender: str, role: str = "customer"
    ) -> Tuple[bool, str]:
        """Register a new user with comprehensive validation"""
        try:
            email = email.strip().lower()

            # Validate input
            if not all([full_name, email, password, gender]):
                return False, "All fields are required"

            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                return False, "Invalid email format"

            if len(password) < 8:
                return False, "Password must be at least 8 characters"

            # Hash password consistently
            password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
            logger.debug(f"Registering user {email} with hash: {password_hash[:8]}...")

            with self.connection.cursor() as cursor:
                # Check if email exists
                cursor.execute("SELECT 1 FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    return False, "Email already registered"

                # Insert new user
                cursor.execute(
                    """INSERT INTO users (full_name, email, password_hash, gender, role)
                    VALUES (%s, %s, %s, %s, %s)""",
                    (full_name, email, password_hash, gender, role),
                )

                # Log the registration
                user_id = cursor.lastrowid
                self._log_auth_action(user_id, email, "register")

            return True, "Registration successful"

        except Error as err:
            logger.error(f"Registration failed for {email}: {err}")
            if err.errno == errorcode.ER_DUP_ENTRY:
                return False, "Email already registered"
            return False, "Registration failed"

    def register_customer(self, full_name: str, email: str, password: str, gender: str) -> Tuple[bool, str]:
        """Register a new customer with automatic customer record creation"""
        try:
            # First register as user
            success, message = self.register_user(full_name, email, password, gender, "customer")
            if not success:
                return False, message

            # Then create customer record
            with self.connection.cursor() as cursor:
                # Get the newly created user_id
                cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
                result = cursor.fetchone()
                if not result:
                    return False, "Failed to retrieve user ID after registration"

                user_id = result[0]

                # Generate customer ID
                customer_id = f"CUST{user_id:04d}"

                # Check if customers table has user_id column
                cursor.execute("SHOW COLUMNS FROM customers LIKE 'user_id'")
                has_user_id = cursor.fetchone() is not None

                if has_user_id:
                    cursor.execute("""
                        INSERT INTO customers 
                        (customer_id, user_id, full_name, email, address, phone, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                                   (customer_id, user_id, full_name, email, "Not specified", "Not specified", "Active"))
                else:
                    cursor.execute("""
                        INSERT INTO customers 
                        (customer_id, full_name, email, address, phone, status)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                                   (customer_id, full_name, email, "Not specified", "Not specified", "Active"))

                self.connection.commit()
                return True, "Customer registration successful"

        except Error as err:
            logger.error(f"Customer registration failed: {err}")
            self.connection.rollback()
            return False, f"Customer registration failed: {err}"

    def _log_auth_action(self, user_id: Optional[int], email: str, action: str) -> None:
        """Log authentication attempts for security monitoring"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO auth_logs 
                    (user_id, email, action, ip_address, user_agent)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (user_id, email, action, "127.0.0.1", "Python App"),
                )
        except Error as err:
            logger.error(f"Failed to log auth action: {err}")

    def get_customer_by_email(self, email: str) -> Optional[Dict]:
        """Get customer details by email"""
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT customer_id, full_name, phone, status
                    FROM customers
                    WHERE email = %s
                """, (email,))
                return cursor.fetchone()
        except Error as err:
            logger.error(f"Error getting customer by email: {err}")
            return None

    def get_customer_total_bookings_cost(self, user_id: int) -> float:
        """Get total bookings cost for specific customer"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT SUM(booking_amount) 
                    FROM reservations 
                    WHERE user_id = %s
                """, (user_id,))
                result = cursor.fetchone()[0]
                return float(result) if result else 0.0
        except Error as err:
            logger.error(f"Error getting customer bookings cost: {err}")
            return 0.0
        
    # In db_helper.py, add this method to the DatabaseManager class
    def generate_reservation_id(self):
        """Generate a unique reservation ID"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            with self.connection.cursor() as cursor:
                # Option 1: Get the highest numeric ID
                cursor.execute("SELECT MAX(CAST(SUBSTRING(reservation_id, 5) AS UNSIGNED)) FROM reservations")
                result = cursor.fetchone()
                max_id = result[0] if result and result[0] is not None else 0

                # Generate new ID with prefix and increment
                new_id = f"RES{max_id + 1:05d}"  # Formats as RES00001, RES00002, etc.

                # Verify uniqueness
                cursor.execute("SELECT COUNT(*) FROM reservations WHERE reservation_id = %s", (new_id,))
                if cursor.fetchone()[0] > 0:
                    # If exists (unlikely), use timestamp fallback
                    new_id = f"RES{int(time.time())}"

                return new_id

        except Exception as e:
            logger.error(f"Error generating reservation ID: {str(e)}")
            # Fallback to timestamp-based ID
            return f"RES{int(time.time())}"

    def get_customer_upcoming_reservations_count(self, user_id: int) -> int:
        """Get count of upcoming reservations for customer"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM reservations 
                    WHERE user_id = %s 
                    AND checkin_date >= CURDATE()
                """, (user_id,))
                return cursor.fetchone()[0] or 0
        except Error as err:
            logger.error(f"Error getting customer upcoming reservations: {err}")
            return 0

    def get_user_reservations(self, user_id: int) -> List[Dict]:
        """Get all reservations for a user with formatted dates and room types"""
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT 
                        reservation_id,
                        guest_name,
                        room_type,
                        checkin_date,
                        checkout_date,
                        CONCAT('$', FORMAT(booking_amount, 2)) AS amount,
                        payment_status,
                        fulfillment_status AS status
                    FROM reservations
                    WHERE user_id = %s
                    ORDER BY checkin_date DESC
                """, (user_id,))

                # Convert to list of dictionaries and format dates
                results = []
                for row in cursor.fetchall():
                    # Format dates in Python instead of SQL
                    check_in = row['checkin_date'].strftime('%b %d, %Y') if row['checkin_date'] else ''
                    check_out = row['checkout_date'].strftime('%b %d, %Y') if row['checkout_date'] else ''

                    results.append({
                        'reservation_id': row['reservation_id'],
                        'guest_name': row['guest_name'],
                        'room_type': row['room_type'],
                        'check_in': check_in,
                        'check_out': check_out,
                        'amount': row['amount'],
                        'payment_status': row['payment_status'],
                        'status': row['status']
                    })
                return results

        except Error as err:
            logger.error(f"Error getting user reservations: {err}")
            return []
    
    def get_staff_by_email(self, email: str) -> Optional[Dict]:
        """Get complete staff member details by email"""
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT 
                        staff_id, 
                        full_name, 
                        email, 
                        phone, 
                        address, 
                        status,
                        DATE_FORMAT(created_at, '%Y-%m-%d') AS join_date
                    FROM staff
                    WHERE email = %s
                """, (email,))
                return cursor.fetchone()
        except Error as err:
            logger.error(f"Error getting staff by email: {err}")
            return None

    def get_total_bookings_cost(self) -> float:
        """Get the total cost of all bookings"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT SUM(booking_amount) FROM reservations")
                result = cursor.fetchone()[0]
                return float(result) if result else 0.0
        except Error as err:
            logger.error(f"Error getting total bookings cost: {err}")
            return 0.0

    def get_total_reservations(self) -> int:
        """Get the total number of reservations"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM reservations")
                return cursor.fetchone()[0] or 0
        except Error as err:
            logger.error(f"Error getting total reservations: {err}")
            return 0

    def get_active_customers_count(self) -> int:
        """Get count of active customers"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM customers WHERE status = 'Active'")
                return cursor.fetchone()[0] or 0
        except Error as err:
            logger.error(f"Error getting active customers count: {err}")
            return 0

    def get_total_customers(self) -> int:
        """Get total count of all customers (active and inactive)"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM customers")
                return cursor.fetchone()[0] or 0
        except Error as err:
            logger.error(f"Error getting total customers count: {err}")
            return 0

    def get_pending_reservations_count(self) -> int:
        """Get count of pending reservations"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM reservations 
                    WHERE fulfillment_status = 'Pending'
                """)
                return cursor.fetchone()[0] or 0
        except Error as err:
            logger.error(f"Error getting pending reservations count: {err}")
            return 0

    def get_recent_customers(self, limit: int = 5) -> List[Dict]:
        """Get recent customers with detailed information"""
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT 
                        customer_id,
                        full_name AS name,
                        email,
                        phone,
                        status,
                        DATE_FORMAT(created_at, '%Y-%m-%d') AS signup_date
                    FROM customers
                    ORDER BY created_at DESC
                    LIMIT %s
                """, (limit,))
                return cursor.fetchall()
        except Error as err:
            logger.error(f"Error fetching recent customers: {err}")
            return []

    def get_customer_growth(self, months: int = 6) -> Dict[str, int]:
        """Get customer growth data for the last N months"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30 * months)

            query = """
                SELECT 
                    DATE_FORMAT(created_at, '%Y-%m') AS month_group,
                    DATE_FORMAT(created_at, '%b') AS month,
                    COUNT(*) AS new_customers
                FROM customers
                WHERE created_at BETWEEN %s AND %s
                GROUP BY month_group, month
                ORDER BY month_group ASC
            """

            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, (start_date, end_date))
                results = cursor.fetchall()

            # Fill in missing months with 0 values
            all_months = {}
            current_date = start_date
            while current_date <= end_date:
                month_key = current_date.strftime('%b')
                all_months[month_key] = 0
                current_date += timedelta(days=30)

            # Update with actual data
            for row in results:
                all_months[row['month']] = int(row['new_customers'])

            return all_months
        except Error as err:
            logger.error(f"Error fetching customer growth data: {err}")
            return {}

    # def get_revenue_trends(self, months: int = 6) -> Dict[str, float]:
    #     """Get revenue trends for the last N months"""
    #     try:
    #         end_date = datetime.now()
    #         start_date = end_date - timedelta(days=30 * months)

    #         query = """
    #             SELECT 
    #                 DATE_FORMAT(transaction_date, '%Y-%m') AS month_group,
    #                 DATE_FORMAT(transaction_date, '%b') AS month,
    #                 SUM(amount) AS revenue
    #             FROM transactions
    #             WHERE transaction_date BETWEEN %s AND %s
    #             GROUP BY month_group, month
    #             ORDER BY month_group ASC
    #         """

    #         with self.connection.cursor(dictionary=True) as cursor:
    #             cursor.execute(query, (start_date, end_date))
    #             results = cursor.fetchall()

    #         # Fill in missing months
    #         all_months = {}
    #         current_date = start_date
    #         while current_date <= end_date:
    #             month_key = current_date.strftime('%b')
    #             all_months[month_key] = 0.0
    #             current_date += timedelta(days=30)

    #         for row in results:
    #             all_months[row['month']] = float(row['revenue'])

    #         return all_months
    #     except Error as err:
    #         logger.error(f"Error getting revenue trends: {err}")
    #         return {}

    def get_revenue_trends(self, months: int = 6) -> Dict[str, float]:
        """Get monthly booking_amount from reservations (excluding Cancelled/Pending)"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30 * months)

            query = """
                SELECT 
                    created_at,
                    booking_amount
                FROM reservations
                WHERE created_at BETWEEN %s AND %s
                AND LOWER(fulfillment_status) != 'cancelled'
                AND LOWER(payment_status) NOT IN ('cancelled', 'pending')
            """

            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, (start_date, end_date))
                results = cursor.fetchall()

            # Initialize dictionary with all recent months as 0.0
            all_months = {}
            month_iter = start_date.replace(day=1)
            while month_iter <= end_date:
                month_key = month_iter.strftime('%b')
                all_months[month_key] = 0.0
                month_iter += timedelta(days=32)
                month_iter = month_iter.replace(day=1)

            # Group and sum revenue per month using Python
            for row in results:
                created_at = row['created_at']
                amount = float(row['booking_amount'])
                month_key = created_at.strftime('%b')
                all_months[month_key] += amount

            return all_months

        except Error as err:
            logger.error(f"Error getting revenue trends from reservations: {err}")
            return {}

    
    def get_booking_trends(self, months: int = 6) -> Dict[str, int]:
        """Get booking trends for the last N months"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30 * months)

            query = """
                SELECT 
                    DATE_FORMAT(created_at, '%Y-%m') AS month_group,
                    DATE_FORMAT(created_at, '%b') AS month,
                    COUNT(*) AS bookings
                FROM reservations
                WHERE created_at BETWEEN %s AND %s
                GROUP BY month_group, month
                ORDER BY month_group ASC
            """

            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, (start_date, end_date))
                results = cursor.fetchall()

            # Fill in missing months
            all_months = {}
            current_date = start_date
            while current_date <= end_date:
                month_key = current_date.strftime('%b')
                all_months[month_key] = 0
                current_date += timedelta(days=30)

            for row in results:
                all_months[row['month']] = int(row['bookings'])

            return all_months
        except Error as err:
            logger.error(f"Error getting booking trends: {err}")
            return {}

    def get_customers(self, status_filter: str = "all") -> List[Dict]:
        """Get customers with optional status filter"""
        try:
            query = """
                SELECT customer_id, full_name, email, address, phone, status 
                FROM customers
            """
            params = ()

            if status_filter.lower() != "all":
                query += " WHERE status = %s"
                params = (status_filter.capitalize(),)

            query += " ORDER BY full_name ASC"

            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()

        except Error as err:
            logger.error(f"Error fetching customers: {err}")
            return []

    def search_customers(self, search_query: str) -> List[Dict]:
        """Search customers by name, email, address or phone"""
        try:
            query = """
                SELECT customer_id, full_name, email, address, phone, status 
                FROM customers 
                WHERE full_name LIKE %s 
                   OR email LIKE %s 
                   OR address LIKE %s 
                   OR phone LIKE %s
                ORDER BY full_name ASC
            """
            search_param = f"%{search_query}%"

            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(
                    query,
                    (search_param, search_param, search_param, search_param)
                )
                return cursor.fetchall()
        except Error as err:
            logger.error(f"Error searching customers: {err}")
            return []

    def add_customer(self, customer_data: Dict) -> bool:
        """Add a new customer to the database"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO customers 
                    (customer_id, full_name, email, address, phone, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        customer_data["customer_id"],
                        customer_data["full_name"],
                        customer_data["email"],
                        customer_data["address"],
                        customer_data["phone"],
                        customer_data["status"]
                    )
                )
                self.connection.commit()
                return True
        except Error as err:
            logger.error(f"Error adding customer: {err}")
            self.connection.rollback()
            return False

    def update_customer(self, customer_id: str, updated_data: Dict) -> bool:
        """Update an existing customer"""
        try:
            with self.connection.cursor() as cursor:
                query = "UPDATE customers SET "
                params = []

                if 'full_name' in updated_data:
                    query += "full_name = %s, "
                    params.append(updated_data['full_name'])
                if 'email' in updated_data:
                    query += "email = %s, "
                    params.append(updated_data['email'])
                if 'address' in updated_data:
                    query += "address = %s, "
                    params.append(updated_data['address'])
                if 'phone' in updated_data:
                    query += "phone = %s, "
                    params.append(updated_data['phone'])
                if 'status' in updated_data:
                    query += "status = %s, "
                    params.append(updated_data['status'])

                # Remove trailing comma and space
                query = query.rstrip(', ')

                query += " WHERE customer_id = %s"
                params.append(customer_id)

                cursor.execute(query, params)
                self.connection.commit()
                return cursor.rowcount > 0
        except Error as err:
            logger.error(f"Error updating customer: {err}")
            self.connection.rollback()
            return False

    def delete_customer(self, customer_id: str) -> bool:
        """Delete a customer from the database"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM customers WHERE customer_id = %s",
                    (customer_id,)
                )
                self.connection.commit()
                return cursor.rowcount > 0
        except Error as err:
            logger.error(f"Error deleting customer: {err}")
            self.connection.rollback()
            return False

    def get_reservations(self, status_filter: str = "all") -> List[Dict]:
        """Get reservations with optional status filter"""
        try:
            query = """
                SELECT 
                    r.reservation_id,
                    r.guest_name AS guest_name,
                    r.room_type,
                    DATE_FORMAT(r.checkin_date, '%Y-%m-%d') AS check_in,
                    DATE_FORMAT(r.checkout_date, '%Y-%m-%d') AS check_out,
                    r.booking_amount AS amount,
                    r.payment_status,
                    r.fulfillment_status AS status,
                    COALESCE(c.full_name, 'N/A') AS customer_name
                FROM reservations r
                LEFT JOIN customers c ON r.customer_id = c.customer_id
            """
            params = ()

            if status_filter.lower() != "all":
                query += " WHERE r.fulfillment_status = %s"
                params = (status_filter.capitalize(),)

            query += " ORDER BY r.checkin_date DESC"

            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()

        except Error as err:
            logger.error(f"Error fetching reservations: {err}")
            return []

    def create_reservation(self, reservation_data: Dict) -> bool:
        """Create a new reservation with proper customer_id handling"""
        try:
            with self.connection.cursor() as cursor:
                # Get customer_id from user_id if not provided
                if 'customer_id' not in reservation_data and 'user_id' in reservation_data:
                    cursor.execute("SELECT customer_id FROM customers WHERE user_id = %s",
                                   (reservation_data['user_id'],))
                    result = cursor.fetchone()
                    if result:
                        reservation_data['customer_id'] = result[0]

                cursor.execute(
                    """
                    INSERT INTO reservations 
                    (reservation_id, user_id, customer_id, guest_name, room_type,
                     checkin_date, checkout_date, booking_amount, 
                     payment_status, fulfillment_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        reservation_data["reservation_id"],
                        reservation_data.get("user_id"),
                        reservation_data.get("customer_id"),
                        reservation_data["guest_name"],
                        reservation_data.get("room_type", "Single"),
                        reservation_data["checkin_date"],
                        reservation_data["checkout_date"],
                        float(reservation_data.get("booking_amount", 0)),
                        reservation_data.get("payment_status", "Pending"),
                        reservation_data.get("fulfillment_status", "Pending"),
                    ),
                )
                return True
        except Error as err:
            logger.error(f"Error creating reservation: {err}")
            return False

    def get_reservation_by_id(self, reservation_id: str) -> Optional[Dict]:
        """Get a specific reservation by ID with all details"""
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT 
                        reservation_id,
                        user_id,
                        customer_id,
                        guest_name,
                        room_type,
                        checkin_date,
                        checkout_date,
                        booking_amount,
                        payment_status,
                        fulfillment_status
                    FROM reservations
                    WHERE reservation_id = %s
                """, (reservation_id,))
                return cursor.fetchone()
        except Error as err:
            logger.error(f"Error getting reservation {reservation_id}: {err}")
            return None

    def get_reservations_by_user(self, user_id: int) -> List[Dict]:
        """Get all reservations for a specific user with formatted dates"""
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT 
                        reservation_id,
                        room_type,
                        DATE_FORMAT(checkin_date, '%%b %%d, %%Y') AS check_in,
                        DATE_FORMAT(checkout_date, '%%b %%d, %%Y') AS check_out,
                        CONCAT('$', FORMAT(booking_amount, 2)) AS amount,
                        payment_status,
                        fulfillment_status AS status
                    FROM reservations
                    WHERE user_id = %s
                    ORDER BY checkin_date DESC
                """, (user_id,))
                return cursor.fetchall()
        except Error as err:
            logger.error(f"Error getting reservations for user {user_id}: {err}")
            return []

    def update_reservation(self, reservation_id: str, updated_data: Dict) -> bool:
        """Update an existing reservation"""
        try:
            with self.connection.cursor() as cursor:
                query = "UPDATE reservations SET "
                params = []

                if 'guest_name' in updated_data:
                    query += "guest_name = %s, "
                    params.append(updated_data['guest_name'])
                if 'room_type' in updated_data:
                    query += "room_type = %s, "
                    params.append(updated_data['room_type'])
                if 'checkin_date' in updated_data:
                    query += "checkin_date = %s, "
                    params.append(updated_data['checkin_date'])
                if 'checkout_date' in updated_data:
                    query += "checkout_date = %s, "
                    params.append(updated_data['checkout_date'])
                if 'booking_amount' in updated_data:
                    query += "booking_amount = %s, "
                    params.append(updated_data['booking_amount'])
                if 'payment_status' in updated_data:
                    query += "payment_status = %s, "
                    params.append(updated_data['payment_status'])
                if 'fulfillment_status' in updated_data:
                    query += "fulfillment_status = %s, "
                    params.append(updated_data['fulfillment_status'])

                # Remove trailing comma and space
                query = query.rstrip(', ')

                query += " WHERE reservation_id = %s"
                params.append(reservation_id)

                cursor.execute(query, params)
                return cursor.rowcount > 0
        except Error as err:
            logger.error(f"Error updating reservation: {err}")
            return False

    def delete_reservation(self, reservation_id: str) -> bool:
        """Delete a reservation from the database"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM reservations 
                    WHERE reservation_id = %s
                    """,
                    (reservation_id,),
                )
                return cursor.rowcount > 0
        except Error as err:
            logger.error(f"Error deleting reservation: {err}")
            return False

    def get_staff_members(self, status="all"):
        """Get staff members filtered by status"""
        query = """
            SELECT staff_id, full_name, email, phone, address, status, 
                   (SELECT gender FROM users WHERE email = staff.email) as gender
            FROM staff
        """
        params = ()

        if status == "active":
            query += " WHERE status = 'Active'"
        elif status == "inactive":
            query += " WHERE status = 'Inactive'"

        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Error as err:
            logger.error(f"Error fetching staff members: {err}")
            return []

    def add_staff_member(self, staff_data):
        """Add a new staff member with complete validation"""
        try:
            # Validate password exists and meets requirements
            if not staff_data.get('password'):
                return False, "Password is required"
            if len(staff_data['password']) < 8:
                return False, "Password must be at least 8 characters"

            # First register as user with hashed password
            password_hash = hashlib.sha256(staff_data['password'].encode("utf-8")).hexdigest()

            with self.connection.cursor() as cursor:
                # Check if email already exists
                cursor.execute("SELECT 1 FROM users WHERE email = %s", (staff_data['email'],))
                if cursor.fetchone():
                    return False, "Email already registered"

                # Insert into users table
                cursor.execute(
                    """INSERT INTO users 
                    (full_name, email, password_hash, gender, role) 
                    VALUES (%s, %s, %s, %s, %s)""",
                    (
                        staff_data['full_name'],
                        staff_data['email'],
                        password_hash,
                        staff_data.get('gender', 'Other'),
                        'staff'
                    )
                )
                user_id = cursor.lastrowid

                # Insert into staff table
                cursor.execute("""
                    INSERT INTO staff 
                    (staff_id, user_id, full_name, email, phone, address, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    staff_data['staff_id'],
                    user_id,
                    staff_data['full_name'],
                    staff_data['email'],
                    staff_data['phone'],
                    staff_data['address'],
                    staff_data['status']
                ))

                self.connection.commit()
                return True, "Staff member added successfully"
        except Error as err:
            logger.error(f"Error adding staff member: {err}")
            if err.errno == errorcode.ER_DUP_ENTRY:
                return False, "Staff ID or email already exists"
            return False, "Failed to add staff member"

    def search_staff_members(self, search_query):
        """Search staff members by name, email or staff ID"""
        query = """
            SELECT staff_id, full_name, email, phone, address, status
            FROM staff
            WHERE full_name LIKE %s 
               OR email LIKE %s 
               OR staff_id LIKE %s
            ORDER BY full_name ASC
        """
        search_param = f"%{search_query}%"

        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, (search_param, search_param, search_param))
                return cursor.fetchall()
        except Error as err:
            logger.error(f"Error searching staff members: {err}")
            return []

    def update_staff_member(self, staff_id, updated_data):
        """Update staff member details"""
        try:
            with self.connection.cursor() as cursor:
                # Update staff table
                staff_query = "UPDATE staff SET "
                staff_params = []

                if 'full_name' in updated_data:
                    staff_query += "full_name = %s, "
                    staff_params.append(updated_data['full_name'])
                if 'email' in updated_data:
                    staff_query += "email = %s, "
                    staff_params.append(updated_data['email'])
                if 'phone' in updated_data:
                    staff_query += "phone = %s, "
                    staff_params.append(updated_data['phone'])
                if 'address' in updated_data:
                    staff_query += "address = %s, "
                    staff_params.append(updated_data['address'])
                if 'status' in updated_data:
                    staff_query += "status = %s, "
                    staff_params.append(updated_data['status'])

                # Remove trailing comma and space
                staff_query = staff_query.rstrip(', ')

                staff_query += " WHERE staff_id = %s"
                staff_params.append(staff_id)

                # Update users table if email or name changed
                user_query = """
                    UPDATE users 
                    SET full_name = %s, email = %s, gender = %s
                    WHERE user_id = (SELECT user_id FROM staff WHERE staff_id = %s)
                """
                user_params = [
                    updated_data['full_name'],
                    updated_data['email'],
                    updated_data.get('gender', 'Other'),
                    staff_id
                ]

                # Update password if provided
                if 'password' in updated_data:
                    password_hash = hashlib.sha256(updated_data['password'].encode("utf-8")).hexdigest()
                    cursor.execute(
                        "UPDATE users SET password_hash = %s WHERE user_id = "
                        "(SELECT user_id FROM staff WHERE staff_id = %s)",
                        (password_hash, staff_id)
                    )

                cursor.execute(staff_query, staff_params)
                cursor.execute(user_query, user_params)
                self.connection.commit()
                return cursor.rowcount > 0
        except Error as err:
            logger.error(f"Error updating staff member: {err}")
            self.connection.rollback()
            return False

    def delete_staff_member(self, staff_id):
        """Delete a staff member and associated user"""
        try:
            with self.connection.cursor() as cursor:
                # First get user_id to delete from users table
                cursor.execute("SELECT user_id FROM staff WHERE staff_id = %s", (staff_id,))
                result = cursor.fetchone()
                if not result:
                    return False

                user_id = result[0]

                # Delete from staff table
                cursor.execute("DELETE FROM staff WHERE staff_id = %s", (staff_id,))

                # Delete from users table
                cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))

                self.connection.commit()
                return True
        except Error as err:
            logger.error(f"Error deleting staff member: {err}")
            self.connection.rollback()
            return False

    def add_reservation(self, reservation_data: Dict) -> Optional[int]:
        """Add a new reservation to the database with proper date handling"""
        try:
            with self.connection.cursor() as cursor:
                # Generate reservation ID
                cursor.execute(
                    "SELECT IFNULL(MAX(CAST(SUBSTRING(reservation_id, 5) AS UNSIGNED)), 0) FROM reservations")
                max_id = cursor.fetchone()[0]
                reservation_id = f"RES{max_id + 1:05d}"

                # Get customer_id from user_id if available
                customer_id = None
                if 'user_id' in reservation_data:
                    cursor.execute("SELECT customer_id FROM customers WHERE user_id = %s",
                                   (reservation_data['user_id'],))
                    result = cursor.fetchone()
                    if result:
                        customer_id = result[0]

                cursor.execute(
                    """
                    INSERT INTO reservations 
                    (reservation_id, user_id, customer_id, guest_name, room_type,
                     checkin_date, checkout_date, booking_amount, 
                     payment_status, fulfillment_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        reservation_id,
                        reservation_data.get("user_id"),
                        customer_id,
                        reservation_data.get("guest_name", "Guest"),
                        reservation_data.get("room_type", "Standard"),
                        reservation_data.get("checkin_date"),
                        reservation_data.get("checkout_date"),
                        float(reservation_data.get("booking_amount", 0)),
                        reservation_data.get("payment_status", "Pending"),
                        reservation_data.get("fulfillment_status", "Pending"),
                    ),
                )
                self.connection.commit()
                return cursor.lastrowid
        except Error as err:
            logger.error(f"Error adding reservation: {err}")
            self.connection.rollback()
            return None

    def get_room_types(self) -> List[Dict]:
        """Get available room types and their rates"""
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT DISTINCT room_type 
                    FROM reservations 
                    WHERE room_type IS NOT NULL
                """)
                room_types = [row['room_type'] for row in cursor.fetchall()]

                if not room_types:
                    return [
                        {"type": "Single", "rate": 99, "description": "Standard single room"},
                        {"type": "Double", "rate": 129, "description": "Standard double room"},
                        {"type": "Suite", "rate": 199, "description": "Luxury suite with extra space"},
                        {"type": "Deluxe", "rate": 249, "description": "Premium deluxe room with amenities"}
                    ]

                return [{"type": rt, "rate": 0, "description": ""} for rt in room_types]
        except Error as err:
            logger.error(f"Error getting room types: {err}")
            return [
                {"type": "Single", "rate": 99, "description": "Standard single room"},
                {"type": "Double", "rate": 129, "description": "Standard double room"},
                {"type": "Suite", "rate": 199, "description": "Luxury suite with extra space"},
                {"type": "Deluxe", "rate": 249, "description": "Premium deluxe room with amenities"}
            ]

    def get_customer_reservations(self, user_id: int) -> List[Dict]:
        """Get all reservations for a specific user with formatted dates"""
        try:
            with self.connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT 
                        reservation_id,
                        room_type,
                        DATE_FORMAT(checkin_date, '%%b %%d, %%Y') AS check_in,
                        DATE_FORMAT(checkout_date, '%%b %%d, %%Y') AS check_out,
                        CONCAT('$', FORMAT(booking_amount, 2)) AS amount,
                        payment_status,
                        fulfillment_status AS status
                    FROM reservations
                    WHERE user_id = %s
                    ORDER BY checkin_date DESC
                """, (user_id,))
                return cursor.fetchall()
        except Error as err:
            logger.error(f"Error getting reservations for user {user_id}: {err}")
            return []

    def get_customer_past_reservations_count(self, user_id: int) -> int:
        """Get count of past reservations for a customer"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM reservations 
                    WHERE user_id = %s 
                    AND checkout_date < CURDATE()
                """, (user_id,))
                return cursor.fetchone()[0] or 0
        except Error as err:
            logger.error(f"Error getting past reservations count: {err}")
            return 0


    def close(self) -> None:
        """Close connection with proper resource cleanup"""
        if self.connection and self.connection.is_connected():
            try:
                self.connection.close()
                logger.info("Database connection closed")
            except Error as err:
                logger.error(f"Error closing connection: {err}")
        self.connection = None

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def connect(self):
        """Public method to connect to database"""
        self._connect()


def hash_password(password: str) -> str:
    """Standardized password hashing using SHA-256 with UTF-8 encoding"""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    # Test the database connection and methods
    with DatabaseManager() as db:
        # Test all critical methods
        methods_to_test = [
            'get_total_bookings_cost',
            'get_customers',
            'get_customer_growth',
            'get_total_reservations',
            'get_active_customers_count',
            'get_pending_reservations_count'
        ]

        for method in methods_to_test:
            try:
                result = getattr(db, method)()
                print(f"{method}(): {result}")
            except Exception as e:
                print(f"Error testing {method}: {e}")

        # Test basic operations
        print("\nTesting basic operations:")
        print("Admin login:", db.authenticate_user("admin@example.com", "admin123", "admin"))
        print("Customer registration:", db.register_customer("Test User", "test@example.com", "password123", "Male"))
        print("Customer login:", db.authenticate_user("test@example.com", "password123", "customer"))