import customtkinter as ctk
from datetime import datetime
import logging
from typing import Dict, Optional, List
from PIL import Image, ImageTk
import os
from CustomerDashboard import CustomerDashboard
from datetime import datetime, timedelta
import tkinter as tk
from tkcalendar import Calendar
import re
import tkinter.ttk as ttk

logger = logging.getLogger(__name__)


class CustomerReservationPage(ctk.CTkFrame):
    def __init__(self, parent, controller, db=None):
        super().__init__(parent)
        self.controller = controller
        self.db = db
        self.current_user: Optional[Dict] = None
        self.reservations: List[Dict] = []
        self.calendar_window = None
        self.active_date_field = None

        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create components
        self.create_widgets()
        logger.info("CustomerReservationsPage initialized")

    def update_user_display(self, user_data: Dict) -> None:
        """Update the display with user information"""
        self.current_user = user_data
        logger.info(f"Updating reservations page for user: {user_data.get('email', 'unknown')}")
        self.load_user_reservations()

    def load_user_reservations(self):
        """Load user's existing reservations from the database"""
        if not self.current_user or not self.db:
            return

        try:
            user_id = self.current_user['user_id']
            # Get reservations from database
            self.reservations = self.db.get_user_reservations(user_id)
        
            # Process the dates - No need for manual processing since DB query already formats them
            for reservation in self.reservations:
                # Ensure the dates are properly set from DB results
                reservation['check_in'] = reservation.get('check_in', 'N/A')
                reservation['check_out'] = reservation.get('check_out', 'N/A')
                reservation['checkin_date'] = reservation.get('check_in', 'N/A')
                reservation['checkout_date'] = reservation.get('check_out', 'N/A')

            logger.info(f"Loaded {len(self.reservations)} reservations for user {user_id}")
            self.update_reservation_table()

        except Exception as e:
            logger.error(f"Error loading reservations: {e}")

    def create_widgets(self):
        """Create all widgets for the reservations page"""
        # Main container
        main = ctk.CTkFrame(self, fg_color="white")
        main.grid(row=0, column=0, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)  # Content row should expand
        main.grid_columnconfigure(0, weight=1)

        # Header section
        header_frame = ctk.CTkFrame(main, height=70, fg_color="white", corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_frame,
            text="Hotel Booking System",
            font=("Arial", 16, "bold"),
            text_color="#2c3e50"
        ).grid(row=0, column=0, padx=20, pady=20, sticky="w")

        # Content area with tabs
        content_frame = ctk.CTkFrame(main, fg_color="#f8fafc")
        content_frame.grid(row=1, column=0, sticky="nsew", padx=30, pady=20)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_rowconfigure(0, weight=0)  # Tabs don't expand
        content_frame.grid_rowconfigure(1, weight=1)  # Content expands

        # Tab view
        self.tab_view = ctk.CTkTabview(content_frame, fg_color="#f8fafc")
        self.tab_view.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))

        # Create tabs
        self.new_reservation_tab = self.tab_view.add("New Reservation")
        self.my_reservations_tab = self.tab_view.add("My Reservations")

        # Set up new reservation form
        self.setup_new_reservation_form()

        # Set up reservations table
        self.setup_reservations_table()

        # Status message area at the bottom of content frame
        self.status_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        self.status_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))

    def setup_new_reservation_form(self):
        """Set up the new reservation form tab"""
        # Create main container frame
        main_frame = ctk.CTkFrame(self.new_reservation_tab, fg_color="white", corner_radius=12)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Get the screen height (or window height) to calculate 70%
        screen_height = self.winfo_screenheight()
        min_height = int(screen_height * 0.7)

        # Create a scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color="white", height=min_height)
        scroll_frame.pack(fill="both", expand=True)
        scroll_frame.pack_propagate(True)

        # Reservation ID
        id_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        id_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(id_frame, text="Reservation ID", font=("Arial", 14), text_color="#475569").pack(anchor="w")

        self.reservation_id_entry = ctk.CTkEntry(id_frame, height=40, fg_color="#f3f4f6", border_color="#d1d5db",
                                                 border_width=1, corner_radius=8, state="disabled")
        self.reservation_id_entry.pack(fill="x")
        self.reservation_id_entry.insert(0, "Generating ID...")

        # Room Type
        room_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        room_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(room_frame, text="Room Type", font=("Arial", 14), text_color="#475569").pack(anchor="w")

        self.room_combo = ctk.CTkComboBox(
            room_frame,
            values=["Single", "Double", "Suite", "Deluxe"],
            height=40,
            fg_color="white",
            border_color="#d1d5db",
            button_color="#3b82f6",
            dropdown_fg_color="white",
            dropdown_text_color="#475569",
            dropdown_hover_color="#f0f0f0",
            corner_radius=8
        )
        self.room_combo.set("Single")
        self.room_combo.pack(fill="x")

        # Check-in
        checkin_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        checkin_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(checkin_frame, text="Check-in Date", font=("Arial", 14), text_color="#475569").pack(anchor="w")
        checkin_container = ctk.CTkFrame(checkin_frame, fg_color="transparent")
        checkin_container.pack(fill="x")

        self.checkin_entry = ctk.CTkEntry(checkin_container, placeholder_text="Select date...", height=40,
                                          fg_color="white", border_color="#d1d5db", border_width=1, corner_radius=8)
        self.checkin_entry.pack(side="left", fill="x", expand=True)

        checkin_button = ctk.CTkButton(checkin_container, text="📅", width=40, height=40, fg_color="#3b82f6",
                                       hover_color="#2563eb", command=lambda: self.open_calendar("checkin"))
        checkin_button.pack(side="right", padx=(5, 0))

        # Check-out
        checkout_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        checkout_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(checkout_frame, text="Check-out Date", font=("Arial", 14), text_color="#475569").pack(anchor="w")
        checkout_container = ctk.CTkFrame(checkout_frame, fg_color="transparent")
        checkout_container.pack(fill="x")

        self.checkout_entry = ctk.CTkEntry(checkout_container, placeholder_text="Select date...", height=40,
                                           fg_color="white", border_color="#d1d5db", border_width=1, corner_radius=8)
        self.checkout_entry.pack(side="left", fill="x", expand=True)

        checkout_button = ctk.CTkButton(checkout_container, text="📅", width=40, height=40, fg_color="#3b82f6",
                                        hover_color="#2563eb", command=lambda: self.open_calendar("checkout"))
        checkout_button.pack(side="right", padx=(5, 0))

        # Amount
        amount_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        amount_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(amount_frame, text="Total Booking Amount", font=("Arial", 14), text_color="#475569").pack(
            anchor="w")

        self.amount_entry = ctk.CTkEntry(amount_frame, placeholder_text="$0.00", height=40, fg_color="white",
                                         border_color="#d1d5db", border_width=1, corner_radius=8)
        self.amount_entry.pack(fill="x")

        # Auto-update amount on room type change
        def update_price(*args):
            price_map = {
                "Single": "$100.00",
                "Double": "$150.00",
                "Suite": "$200.00",
                "Deluxe": "$250.00"
            }
            room_type = self.room_combo.get()
            price = price_map.get(room_type, "$0.00")
            self.amount_entry.delete(0, tk.END)
            self.amount_entry.insert(0, price)

        self.room_combo.configure(command=update_price)
        update_price()

        # Payment Status
        payment_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        payment_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(payment_frame, text="Payment Status", font=("Arial", 14), text_color="#475569").pack(anchor="w")

        self.payment_status_combo = ctk.CTkComboBox(payment_frame, values=["Pending", "Paid"], height=40,
                                                    fg_color="white", border_color="#d1d5db", button_color="#3b82f6",
                                                    dropdown_fg_color="white", dropdown_text_color="#475569",
                                                    dropdown_hover_color="#f0f0f0", corner_radius=8)
        self.payment_status_combo.set("Pending")
        self.payment_status_combo.pack(fill="x")

        # Reservation Status
        status_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        status_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(status_frame, text="Reservation Status", font=("Arial", 14), text_color="#475569").pack(anchor="w")

        self.fulfillment_status_combo = ctk.CTkComboBox(status_frame, values=["Pending", "Confirmed"], height=40,
                                                        fg_color="white", border_color="#d1d5db",
                                                        button_color="#3b82f6", dropdown_fg_color="white",
                                                        dropdown_text_color="#475569", dropdown_hover_color="#f0f0f0",
                                                        corner_radius=8)
        self.fulfillment_status_combo.set("Pending")
        self.fulfillment_status_combo.pack(fill="x")

        # Buttons
        button_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)

        ctk.CTkButton(button_frame, text="Submit", fg_color="#3b82f6", hover_color="#2563eb",
                      command=self.submit_reservation, height=40).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Clear", fg_color="#64748b", hover_color="#475569", command=self.clear_form,
                      height=40).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Back to Dashboard", fg_color="#ef4444", hover_color="#dc2626",
                      command=self.close_form, height=40).pack(side="left", padx=10)

        # Generate reservation ID
        if self.db:
            self.reservation_id_entry.configure(state="normal")
            self.reservation_id_entry.delete(0, "end")
            self.reservation_id_entry.insert(0, self.db.generate_reservation_id())
            self.reservation_id_entry.configure(state="disabled")

    def open_calendar(self, field_name):
        """Open a calendar popup for date selection"""
        if self.calendar_window:
            self.calendar_window.destroy()

        self.active_date_field = field_name

        # Get current date from entry if available
        current_entry = self.checkin_entry if field_name == "checkin" else self.checkout_entry
        current_date = current_entry.get()
        try:
            if current_date:
                selected_date = self.parse_date_string(current_date)
            else:
                # Default to today for check-in, tomorrow for check-out
                selected_date = datetime.now()
                if field_name == "checkout":
                    selected_date += timedelta(days=1)
        except ValueError:
            selected_date = datetime.now()
            if field_name == "checkout":
                selected_date += timedelta(days=1)

        # Create a toplevel window
        self.calendar_window = tk.Toplevel()
        self.calendar_window.title(f"Select {field_name.capitalize()} Date")
        self.calendar_window.geometry("300x300")
        self.calendar_window.transient(self)
        self.calendar_window.grab_set()

        # Create calendar
        min_date = datetime.now() if field_name == "checkin" else None
        if field_name == "checkout" and self.checkin_entry.get():
            try:
                min_date = self.parse_date_string(self.checkin_entry.get()) + timedelta(days=1)
            except ValueError:
                min_date = datetime.now() + timedelta(days=1)

        cal = Calendar(
            self.calendar_window,
            selectmode='day',
            year=selected_date.year,
            month=selected_date.month,
            day=selected_date.day,
            mindate=min_date,
            background="#3b82f6",
            foreground="white",
            selectbackground="#2563eb",
            headersbackground="#60a5fa",
            normalbackground="white",
            weekendbackground="#f1f5f9"
        )
        cal.pack(fill="both", expand=True, padx=10, pady=10)

        # Button to confirm selection
        confirm_button = ctk.CTkButton(
            self.calendar_window,
            text="Confirm",
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=lambda: self.set_date(cal.get_date())
        )
        confirm_button.pack(padx=10, pady=10)

    def parse_date_string(self, date_str):
        """Parse date string from various possible formats"""
        if not date_str or not isinstance(date_str, str):
            return datetime.now()
        
        date_formats = [
            "%Y-%m-%d",       # Database format
            "%b %d, %Y",      # Display format
            "%m/%d/%y",       # Calendar format
            "%m/%d/%Y",       # US date format
            "%d/%m/%Y",       # European date format
            "%B %d, %Y",      # Full month name
            "%Y/%m/%d",       # ISO-like format
        ]  
    
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
    
        # Log the failure and return current date as fallback
        logger.error(f"Failed to parse date string: {date_str}")
        return datetime.now()

    def set_date(self, selected_date):
        """Set the selected date to the appropriate entry field"""
        try:
            # Convert the selected date to datetime object
            date_obj = self.parse_date_string(selected_date)
            # Format to match the display format
            formatted_date = date_obj.strftime("%b %d, %Y")

            # Set the date in the appropriate entry
            if self.active_date_field == "checkin":
                self.checkin_entry.delete(0, "end")
                self.checkin_entry.insert(0, formatted_date)

                # If setting check-in date, update minimum date for check-out
                if not self.checkout_entry.get():
                    # If no checkout date, set to check-in date + 1 day
                    next_day = date_obj + timedelta(days=1)
                    self.checkout_entry.delete(0, "end")
                    self.checkout_entry.insert(0, next_day.strftime("%b %d, %Y"))
            else:
                self.checkout_entry.delete(0, "end")
                self.checkout_entry.insert(0, formatted_date)

            # Close the calendar window
            if self.calendar_window:
                self.calendar_window.destroy()
                self.calendar_window = None

        except Exception as e:
            logger.error(f"Error setting date: {e}")
            self.show_message(f"Failed to set date: {str(e)}", "error")

    def setup_reservations_table(self):
        """Set up the reservations table view using Treeview"""
        # Create frame for the table
        table_frame = ctk.CTkFrame(self.my_reservations_tab, fg_color="white", corner_radius=12)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create scrollable frame
        scroll_frame = ctk.CTkFrame(table_frame, fg_color="white")
        scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Create vertical scrollbar
        scrollbar = ttk.Scrollbar(scroll_frame)
        scrollbar.pack(side="right", fill="y")

        # Create the Treeview widget
        self.reservations_tree = ttk.Treeview(
            scroll_frame,
            yscrollcommand=scrollbar.set,
            selectmode="browse",
            style="Custom.Treeview"
        )

        # Configure the style
        style = ttk.Style()
        style.theme_use("default")

        # Configure the Treeview colors
        style.configure("Custom.Treeview",
                        background="white",
                        foreground="#334155",
                        rowheight=35,
                        fieldbackground="white",
                        bordercolor="#d1d5db",
                        borderwidth=1,
                        font=('Arial', 11)
                        )
        style.configure("Custom.Treeview.Heading",
                        background="#f1f5f9",
                        foreground="#334155",
                        relief="flat",
                        font=('Arial', 12, 'bold'),
                        padding=(10, 5)
                        )
        style.map("Custom.Treeview",
                  background=[('selected', '#3b82f6')],
                  foreground=[('selected', 'white')]
                  )

        # Define columns
        self.reservations_tree['columns'] = ('reservation_id', 'room_type', 'check_in', 'check_out', 'amount', 'status')

        # Format columns
        self.reservations_tree.column('#0', width=0, stretch=False)  # Hide first empty column
        self.reservations_tree.column('reservation_id', anchor='w', width=150, minwidth=100)
        self.reservations_tree.column('room_type', anchor='w', width=100, minwidth=80)
        self.reservations_tree.column('check_in', anchor='w', width=120, minwidth=100)
        self.reservations_tree.column('check_out', anchor='w', width=120, minwidth=100)
        self.reservations_tree.column('amount', anchor='w', width=100, minwidth=80)
        self.reservations_tree.column('status', anchor='w', width=100, minwidth=80)

        # Create headings
        self.reservations_tree.heading('reservation_id', text='Reservation ID', anchor='w')
        self.reservations_tree.heading('room_type', text='Room Type', anchor='w')
        self.reservations_tree.heading('check_in', text='Check-in', anchor='w')
        self.reservations_tree.heading('check_out', text='Check-out', anchor='w')
        self.reservations_tree.heading('amount', text='Amount', anchor='w')
        self.reservations_tree.heading('status', text='Status', anchor='w')

        self.reservations_tree.pack(fill="both", expand=True, padx=0, pady=0)
        scrollbar.config(command=self.reservations_tree.yview)

        # Add tag for alternating row colors
        self.reservations_tree.tag_configure('oddrow', background='white')
        self.reservations_tree.tag_configure('evenrow', background='#f8fafc')

        # Button frame for Refresh and Cancel buttons
        button_frame = ctk.CTkFrame(table_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)

        # Refresh button
        ctk.CTkButton(
            button_frame,
            text="Refresh",
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=self.load_user_reservations,
            height=35,
            width=100
        ).pack(side="right", padx=5)

        # Delete button
        ctk.CTkButton(
            button_frame,
            text="Back to Dashboard",
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=self.close_reservations_tab,
            height=35,
            width=100
        ).pack(side="right", padx=5)

    def update_reservation_table(self):
        """Update the Treeview with reservation data"""
        # Clear existing items
        for item in self.reservations_tree.get_children():
            self.reservations_tree.delete(item)

        # Show message if no reservations
        if not self.reservations:
            self.no_data_label = ctk.CTkLabel(
                self.reservations_tree.master,
                text="No reservations found.",
                font=("Arial", 12),
                text_color="#64748b"
            )
            self.no_data_label.place(relx=0.5, rely=0.5, anchor="center")
            return
        else:
            # Remove the no data label if it exists
            if hasattr(self, 'no_data_label') and self.no_data_label.winfo_exists():
                self.no_data_label.destroy()

        # Sort reservations by check-in date if possible
        try:
            sorted_reservations = sorted(
                self.reservations,
                key=lambda x: self.parse_date_string(x.get("check_in", "Jan 01, 2000")),
                reverse=True
            )
        except Exception as e:
            logger.error(f"Error sorting reservations: {e}")
            sorted_reservations = self.reservations

        # Add data to the Treeview
        for i, res in enumerate(sorted_reservations):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
        
            # Format amount
            amount_str = res.get("amount", "$0.00")
            if isinstance(amount_str, (int, float)):
                amount_str = f"${amount_str:.2f}"
            elif isinstance(amount_str, str) and not amount_str.startswith('$'):
                try:
                    amount_float = float(re.sub(r'[^\d.]', '', amount_str))
                    amount_str = f"${amount_float:.2f}"
                except (ValueError, TypeError):
                    pass  # Keep as is
                
            self.reservations_tree.insert(
                parent='',
                index='end',
                iid=i,
                text='',
                values=(
                    res.get("reservation_id", ""),
                    res.get("room_type", ""),
                    res.get("check_in", ""),
                    res.get("check_out", ""),
                    amount_str,
                    res.get("status", "Pending")
                ),
                tags=(tag,)
            )

    def close_reservations_tab(self):
        """Close the reservations tab and return to dashboard"""
        if hasattr(self.controller, "show_frame"):
            self.controller.show_frame("CustomerDashboard")
            logger.info("Returned to dashboard from reservations tab")
        else:
            self.pack_forget()
            logger.info("Closed reservations tab")

        self.show_message("Closed reservations view", "info")

    def submit_reservation(self):
        """Handle reservation submission"""
        try:
            if not self.current_user:
                logger.error("No user logged in")
                self.show_message("Please log in to create a reservation", "error")
                return

            # Get form data
            reservation_id = self.reservation_id_entry.get()
            room_type = self.room_combo.get()
            check_in = self.checkin_entry.get()
            check_out = self.checkout_entry.get()
            amount = self.amount_entry.get()
            payment_status = self.payment_status_combo.get()
            fulfillment_status = self.fulfillment_status_combo.get()

            # Validate required fields
            if not all([room_type, check_in, check_out]):
                logger.error("Missing required fields")
                self.show_message("Please fill in all required fields", "error")
                return

            # Date validation with consistent format
            try:
                checkin_date = self.parse_date_string(check_in)
                checkout_date = self.parse_date_string(check_out)

                if checkin_date >= checkout_date:
                    self.show_message("Check-out date must be after check-in date", "error")
                    return

                if checkin_date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
                    self.show_message("Check-in date cannot be in the past", "warning")
                    return
            except ValueError:
                self.show_message("Please enter valid dates in 'MMM DD, YYYY' format", "error")
                return

            # Validate amount (consistent with db_helper format)
            try:
                amount_value = float(re.sub(r'[^\d.]', '', amount))
                if amount_value <= 0:
                    self.show_message("Booking amount must be positive", "error")
                    return
            except ValueError:
                self.show_message("Please enter a valid booking amount", "error")
                return

            # Save to database
            if self.db:
                # Get customer_id from user_id
                customer_id = None
                if 'customer_id' in self.current_user:
                    customer_id = self.current_user['customer_id']
                else:
                    # Try to get customer_id from database if not in current_user
                    customer_data = self.db.get_customer_by_email(self.current_user['email'])
                    if customer_data:
                        customer_id = customer_data.get('customer_id')

                new_reservation = {
                    "reservation_id": reservation_id,
                    "user_id": self.current_user['user_id'],
                    "customer_id": customer_id,
                    "guest_name": self.current_user.get('full_name', 'Guest'),
                    "room_type": room_type,
                    "checkin_date": checkin_date.strftime("%Y-%m-%d"),
                    "checkout_date": checkout_date.strftime("%Y-%m-%d"),
                    "booking_amount": amount_value,
                    "payment_status": payment_status,
                    "fulfillment_status": fulfillment_status
                }

                logger.debug(f"Creating reservation with data: {new_reservation}")

                success = self.db.create_reservation(new_reservation)
                if success:
                    logger.info(f"Reservation created with ID: {reservation_id}")
                    self.show_message("Reservation created successfully!", "success")
                    self.clear_form()

                    # Generate new ID for next reservation
                    self.reservation_id_entry.configure(state="normal")
                    self.reservation_id_entry.delete(0, "end")
                    self.reservation_id_entry.insert(0, self.db.generate_reservation_id())
                    self.reservation_id_entry.configure(state="disabled")

                    # Switch to the reservations tab and refresh the table
                    self.tab_view.set("My Reservations")
                    self.load_user_reservations()
                else:
                    self.show_message("Failed to create reservation", "error")
            else:
                self.show_message("Database connection error", "error")

        except Exception as e:
            logger.error(f"Error submitting reservation: {e}")
            self.show_message(f"An error occurred: {str(e)}", "error")

    def clear_form(self):
        """Clear all form fields"""
        self.room_combo.set("")
        self.checkin_entry.delete(0, "end")
        self.checkout_entry.delete(0, "end")
        self.amount_entry.delete(0, "end")
        self.amount_entry.insert(0, "$0.00")
        self.payment_status_combo.set("Pending")
        self.fulfillment_status_combo.set("Pending")

    def close_form(self):
        """Close the reservation form and return to the main window"""
        # First clear any entered data
        self.clear_form()

        # Navigate back to the main dashboard if available
        if hasattr(self.controller, "show_frame"):
            self.controller.show_frame("CustomerDashboard")
            logger.info("Navigated back to dashboard")
        else:
            self.pack_forget()
            self.grid_forget()
            logger.info("Form closed")

        self.show_message("Reservation cancelled", "info")

    def show_message(self, message, message_type="info"):
        """Show a status message with appropriate styling"""
        # Clear any existing messages
        for widget in self.status_frame.winfo_children():
            widget.destroy()

        # Set colors based on message type
        if message_type == "success":
            bg_color = "#dcfce7"
            text_color = "#166534"
            icon = "✓"
            border_color = "#86efac"
        elif message_type == "error":
            bg_color = "#fee2e2"
            text_color = "#991b1b"
            icon = "✕"
            border_color = "#fca5a5"
        elif message_type == "warning":
            bg_color = "#fef3c7"
            text_color = "#92400e"
            icon = "⚠"
            border_color = "#fcd34d"
        else:  # info
            bg_color = "#e0f2fe"
            text_color = "#0369a1"
            icon = "ℹ"
            border_color = "#7dd3fc"

        # Create message frame
        message_frame = ctk.CTkFrame(
            self.status_frame,
            fg_color=bg_color,
            corner_radius=6,
            border_width=1,
            border_color=border_color
        )
        message_frame.pack(fill="x", expand=True)

        # Message with icon
        message_label = ctk.CTkLabel(
            message_frame,
            text=f"{icon} {message}",
            text_color=text_color,
            font=("Arial", 13)
        )
        message_label.pack(padx=15, pady=10)

        # Auto-dismiss after 5 seconds
        self.after(5000, message_frame.destroy)