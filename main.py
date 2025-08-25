import customtkinter as ctk
from dashboard import HotelBookingDashboard
from login import LoginApp
from register import RegistrationApp
from landing import HotelBookingSystem
from password_recovery import PasswordRecoveryApp
from mcustomer import CustomerManagementScreen
from Report import HotelReportsPage
from Reservations import HotelReservationsPage
from staff_member import StaffMemberScreen
from CustomerDashboard import CustomerDashboard
from StaffDashboard import StaffDashboard
from StaffReservationsPage import StaffReservationsPage
from StaffCustomerManagementScreen import StaffCustomerManagementScreen
from CustomerReservationPage import CustomerReservationPage
from db_helper import DatabaseManager
import logging

class HotelApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Hotel Management System")
        self.geometry("1400x900")
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        # Initialize database connection with retry logic
        max_retries = 3
        retry_delay = 2
        for attempt in range(max_retries):
            try:
                self.db = DatabaseManager()
                self.current_user = None
                break
            except Exception as e:
                logging.error(f"Database initialization attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    logging.critical("Failed to initialize database after multiple attempts")
                    raise
                import time
                time.sleep(retry_delay)

        # Create container frame
        self.container = ctk.CTkFrame(self)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Initialize all frames with error handling
        self.frames = {}
        frames_classes = [
            ("HotelBookingSystem", HotelBookingSystem),
            ("LoginApp", LoginApp),
            ("RegistrationApp", RegistrationApp),
            ("HotelBookingDashboard", HotelBookingDashboard),
            ("CustomerManagementScreen", CustomerManagementScreen),
            ("HotelReportsPage", HotelReportsPage),
            ("HotelReservationsPage", HotelReservationsPage),
            ("StaffMemberScreen", StaffMemberScreen),
            ("CustomerDashboard", CustomerDashboard),
            ("StaffDashboard", StaffDashboard),
            ("StaffReservationsPage", StaffReservationsPage),
            ("StaffCustomerManagementScreen", StaffCustomerManagementScreen),
            ("CustomerReservationPage", CustomerReservationPage)
        ]

        for name, FrameClass in frames_classes:
            try:
                frame = FrameClass(parent=self.container, controller=self, db=self.db)
                self.frames[name] = frame
                frame.grid(row=0, column=0, sticky="nsew")
                logging.info(f"Successfully initialized frame: {name}")
            except Exception as e:
                logging.error(f"Failed to initialize frame {name}: {str(e)}")
                if name in ["StaffReservationsPage", "StaffCustomerManagementScreen", "StaffPasswordRecoveryPage"]:
                    # Create placeholder frame if essential staff frames fail
                    placeholder = ctk.CTkFrame(self.container)
                    self.frames[name] = placeholder
                    placeholder.grid(row=0, column=0, sticky="nsew")
                    logging.warning(f"Created placeholder for {name}")

        self.show_frame("HotelBookingSystem")

    def show_frame(self, page_name, user_type=None):
        """Show a frame and update window title"""
        frame = self.frames.get(page_name)
        if not frame:
            logging.error(f"Frame {page_name} not found in available frames: {list(self.frames.keys())}")
            return

        frame.tkraise()

        # Update window title
        titles = {
            "HotelBookingSystem": "Hotel Booking System",
            "LoginApp": "Login - Hotel Management",
            "RegistrationApp": "Register - Hotel Management",
            "HotelBookingDashboard": "Admin Dashboard - Hotel Management",
            "CustomerDashboard": "Customer Dashboard - Hotel Management",
            "StaffDashboard": "Staff Dashboard - Hotel Management",
            "CustomerManagementScreen": "Customers - Hotel Management",
            "HotelReportsPage": "Reports - Hotel Management",
            "HotelReservationsPage": "Reservations - Hotel Management",
            "StaffMemberScreen": "Staff Members - Hotel Management",
            "StaffReservationsPage": "Reservations - Staff View",
            "StaffCustomerManagementScreen": "Customers - Staff View",
            "CustomerReservationPage": "My Reservations - Hotel Management"
        }
        self.title(titles.get(page_name, "Hotel Management System"))

        # Update user display if applicable
        if (page_name.endswith("Dashboard") or
            page_name.endswith("Page") or
            page_name.endswith("Screen")) and self.current_user:
            if hasattr(frame, 'update_user_display'):
                try:
                    frame.update_user_display(self.current_user)
                    logging.info(f"Updated user display for {page_name}")
                except Exception as e:
                    logging.error(f"Failed to update user display: {e}")

        # Pass user_type to LoginApp if provided
        if page_name == "LoginApp" and user_type and hasattr(frame, 'set_user_type'):
            frame.set_user_type(user_type)

    def successful_login(self, user_data, dashboard_name):
        """Handle post-login operations"""
        try:
            self.current_user = user_data
            self.show_frame(dashboard_name)
            logging.info(f"User {user_data.get('email', 'unknown')} logged in successfully")
        except Exception as e:
            logging.error(f"Login failed: {e}")
            self.show_frame("LoginApp")

    def logout(self):
        """Handle logout operation"""
        try:
            username = self.current_user.get('email', 'unknown') if self.current_user else 'unknown'
            self.current_user = None
            self.show_frame("HotelBookingSystem")
            logging.info(f"User {username} logged out")
        except Exception as e:
            logging.error(f"Logout failed: {e}")
            self.show_frame("HotelBookingSystem")

    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'db'):
            try:
                self.db.close()
                logging.info("Application shutdown - database connection closed")
            except Exception as e:
                logging.error(f"Failed to close database connection: {e}")

if __name__ == "__main__":
    try:
        app = HotelApp()
        app.mainloop()
    except Exception as e:
        logging.critical(f"Application crashed: {e}")
        raise
