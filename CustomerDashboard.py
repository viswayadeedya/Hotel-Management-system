import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tksheet
from tkinter import messagebox
from datetime import datetime
import tkinter.ttk as ttk
import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class CustomerDashboard(ctk.CTkFrame):
    def __init__(self, parent, controller, db):
        super().__init__(parent)
        self.controller = controller
        self.db = db  # Using the shared DatabaseManager instance
        self.current_user = None
        self.sheet = None

        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Create empty containers
        self.sidebar = ctk.CTkFrame(self, width=250, fg_color="#f0f9ff", corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self.main_content = ctk.CTkFrame(self, fg_color="white")
        self.main_content.grid(row=0, column=1, sticky="nsew")
        self.main_content.grid_rowconfigure(1, weight=1)
        self.main_content.grid_columnconfigure(0, weight=1)

        # Placeholder for initial empty state
        self.show_loading_state()
        logger.info("CustomerDashboard initialized")

    def update_user_display(self, user_data: Dict) -> None:
        """Update the dashboard with user data"""
        try:
            logger.info(f"Updating dashboard for customer: {user_data.get('email', 'unknown')}")
            self.current_user = user_data

            # Clear existing widgets
            for widget in self.sidebar.winfo_children():
                widget.destroy()

            for widget in self.main_content.winfo_children():
                widget.destroy()

            # Recreate components
            self.create_sidebar()
            self.create_main_content()

        except Exception as e:
            error_msg = f"Failed to update dashboard: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
            self.show_error_state()

    def show_loading_state(self) -> None:
        """Show loading state before user data is available"""
        loading_frame = ctk.CTkFrame(self.main_content, fg_color="white")
        loading_frame.pack(expand=True, fill="both")

        ctk.CTkLabel(
            loading_frame,
            text="Loading dashboard...",
            font=("Arial", 16),
            text_color="#64748b"
        ).pack(pady=50)

    def show_error_state(self) -> None:
        """Show error state if something goes wrong"""
        for widget in self.main_content.winfo_children():
            widget.destroy()

        error_frame = ctk.CTkFrame(self.main_content, fg_color="white")
        error_frame.pack(expand=True, fill="both")

        ctk.CTkLabel(
            error_frame,
            text="Failed to load dashboard",
            font=("Arial", 16),
            text_color="#ef4444"
        ).pack(pady=20)

        ctk.CTkButton(
            error_frame,
            text="Retry",
            command=lambda: self.update_user_display(self.current_user)
        ).pack()

    def create_sidebar(self) -> None:
        """Create sidebar navigation"""
        try:
            # Navigation buttons
            nav_items = [
                ("Dashboard", "📊", "CustomerDashboard"),
                ("Reservations", "🛒", "CustomerReservationPage")
            ]

            # Add padding at the top
            ctk.CTkLabel(self.sidebar, text="", fg_color="transparent").pack(pady=(20, 10))

            for item, icon, frame_name in nav_items:
                is_active = frame_name == "CustomerDashboard"
                btn_color = "#dbeafe" if is_active else "transparent"

                btn_frame = ctk.CTkFrame(self.sidebar, fg_color=btn_color, corner_radius=8)
                btn_frame.pack(fill="x", padx=15, pady=5)

                content_frame = ctk.CTkFrame(btn_frame, fg_color="transparent")
                content_frame.pack(pady=8, padx=15, anchor="w")

                ctk.CTkLabel(
                    content_frame,
                    text=icon,
                    font=("Arial", 16),
                    text_color="#64748b"
                ).pack(side="left", padx=(0, 10))

                btn = ctk.CTkButton(
                    content_frame,
                    text=item,
                    font=("Arial", 14),
                    text_color="#64748b",
                    fg_color="transparent",
                    hover_color="#f0f0f0",
                    anchor="w",
                    command=lambda fn=frame_name: self.controller.show_frame(fn)
                )
                btn.pack(side="left")

            # Logout button
            logout_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            logout_frame.pack(side="bottom", fill="x", padx=15, pady=20)

            ctk.CTkButton(
                logout_frame,
                text="Logout",
                fg_color="#ef4444",
                hover_color="#dc2626",
                command=self.controller.logout
            ).pack(fill="x")

        except Exception as e:
            logger.error(f"Error creating sidebar: {str(e)}")
            raise

    def create_main_content(self) -> None:
        """Create the main content area with dashboard widgets"""
        try:
            if not self.current_user:
                return

            # ===== HEADER SECTION =====
            header_frame = ctk.CTkFrame(self.main_content, height=70, fg_color="white", corner_radius=0)
            header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
            header_frame.grid_columnconfigure(0, weight=0)
            header_frame.grid_columnconfigure(1, weight=1)
            header_frame.grid_columnconfigure(2, weight=0)

            # Logo
            ctk.CTkLabel(
                header_frame,
                text="Hotel Booking System",
                font=("Arial", 16, "bold"),
                text_color="#2c3e50"
            ).grid(row=0, column=0, padx=(20, 10), pady=20, sticky="w")

            # Navigation
            nav_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            nav_frame.grid(row=0, column=1, sticky="")

            for item, frame_name in [("Dashboard", "CustomerDashboard"), ("Reservations", "CustomerReservationPage")]:
                text_color = "#3b82f6" if frame_name == "CustomerDashboard" else "#64748b"
                ctk.CTkButton(
                    nav_frame,
                    text=item,
                    fg_color="transparent",
                    text_color=text_color,
                    hover_color="#f0f0f0",
                    corner_radius=5,
                    height=32,
                    border_width=0,
                    command=lambda fn=frame_name: self.controller.show_frame(fn)
                ).pack(side="left", padx=15)

            # User info
            if self.current_user:
                username = self.current_user.get('full_name', '').split()[0]
                if username:
                    user_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
                    user_frame.grid(row=0, column=2, padx=20, sticky="e")

                    ctk.CTkLabel(
                        user_frame,
                        text=username,
                        font=("Arial", 14),
                        text_color="#64748b"
                    ).pack(side="left", padx=5)

            # ===== CONTENT AREA =====
            content = ctk.CTkScrollableFrame(self.main_content, fg_color="#f8fafc")
            content.grid(row=1, column=0, sticky="nsew")

            # Welcome message
            welcome_frame = ctk.CTkFrame(content, fg_color="transparent")
            welcome_frame.pack(fill="x", padx=20, pady=(20, 10))

            ctk.CTkLabel(
                welcome_frame,
                text=f"Welcome back, {self.current_user.get('full_name', 'Customer')}",
                font=("Arial", 20, "bold"),
                text_color="#2c3e50"
            ).pack(side="left")

            # ===== METRICS CARDS =====
            metrics_frame = ctk.CTkFrame(content, fg_color="transparent")
            metrics_frame.pack(fill="x", padx=20, pady=20)

            try:
                total_bookings_cost = self.db.get_customer_total_bookings_cost(self.current_user['user_id'])
                upcoming_reservations = self.db.get_customer_upcoming_reservations_count(self.current_user['user_id'])
                past_reservations = self.db.get_customer_past_reservations_count(self.current_user['user_id'])
            except Exception as e:
                logger.error(f"Database error loading metrics: {e}")
                messagebox.showerror("Database Error", f"Failed to load metrics: {str(e)}")
                total_bookings_cost = 0
                upcoming_reservations = 0
                past_reservations = 0

            metrics = [
                (f"${total_bookings_cost:,.2f}", "Total bookings cost", "CustomerReservationPage"),
                (f"{upcoming_reservations:,}", "Upcoming reservations", "CustomerReservationPage"),
                (f"{past_reservations:,}", "Past reservations", "CustomerReservationPage"),
            ]

            for value, label, target_frame in metrics:
                card = ctk.CTkFrame(metrics_frame, fg_color="white", corner_radius=12, height=120)
                card.pack(side="left", expand=True, fill="both", padx=10)

                # Make clickable
                card.bind("<Button-1>", lambda e, fn=target_frame: self.controller.show_frame(fn))
                for child in card.winfo_children():
                    child.bind("<Button-1>", lambda e, fn=target_frame: self.controller.show_frame(fn))

                ctk.CTkLabel(
                    card,
                    text=value,
                    font=("Arial", 24, "bold"),
                    text_color="#2c3e50",
                    cursor="hand2"
                ).pack(pady=(25, 5), padx=20, anchor="w")

                ctk.CTkLabel(
                    card,
                    text=label,
                    font=("Arial", 14),
                    text_color="#7f8c8d",
                    cursor="hand2"
                ).pack(pady=(0, 20), padx=20, anchor="w")

            # ===== RECENT BOOKINGS SECTION =====
            recent_bookings_frame = ctk.CTkFrame(content, fg_color="white", corner_radius=12)
            recent_bookings_frame.pack(fill="both", expand=True, padx=20, pady=(20, 20))

            # Header
            header_frame = ctk.CTkFrame(recent_bookings_frame, fg_color="white")
            header_frame.pack(fill="x", padx=20, pady=(20, 10))

            ctk.CTkLabel(
                header_frame,
                text="Recent Bookings",
                font=("Arial", 16, "bold"),
                text_color="#2c3e50"
            ).pack(side="left")

            # View All button
            view_all_btn = ctk.CTkButton(
                header_frame,
                text="View All",
                fg_color="transparent",
                text_color="#3b82f6",
                hover_color="#f0f0f0",
                command=lambda: self.controller.show_frame("CustomerReservationPage"),
                width=80,
                height=30
            )
            view_all_btn.pack(side="right")

            # Create Treeview for recent bookings
            try:
                # Get recent bookings (limit to 5 most recent)
                all_bookings = self.db.get_user_reservations(self.current_user['user_id'])
                recent_bookings = sorted(
                    all_bookings,
                    key=lambda x: self.parse_date_string(x.get("check_in", "Jan 01, 2000")),
                    reverse=True
                )[:5]  # Only show 5 most recent

                # Create scrollable frame
                scroll_frame = ctk.CTkFrame(recent_bookings_frame, fg_color="white")
                scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)

                # Create vertical scrollbar
                scrollbar = ttk.Scrollbar(scroll_frame)
                scrollbar.pack(side="right", fill="y")

                # Create the Treeview widget
                self.reservations_tree = ttk.Treeview(
                    scroll_frame,
                    yscrollcommand=scrollbar.set,
                    selectmode="browse",
                    height=5,  # Show 5 rows by default
                    style="Custom.Treeview"
                )

                # Configure the style (same as in CustomerReservationPage)
                style = ttk.Style()
                style.theme_use("default")

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

                # Add data to the Treeview
                if not recent_bookings:
                    no_data_label = ctk.CTkLabel(
                        scroll_frame,
                        text="No recent bookings found",
                        font=("Arial", 12),
                        text_color="#64748b"
                    )
                    no_data_label.pack(pady=50)
                else:
                    for i, res in enumerate(recent_bookings):
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

            except Exception as e:
                logger.error(f"Error creating recent bookings table: {str(e)}")
                ctk.CTkLabel(
                    recent_bookings_frame,
                    text="Could not load recent bookings",
                    text_color="#ef4444"
                ).pack(pady=50)

        except Exception as e:
            logger.error(f"Error creating dashboard content: {str(e)}")
            messagebox.showerror("Error", f"Failed to create dashboard content: {str(e)}")
            self.show_error_state()

    def parse_date_string(self, date_str):
        """Parse date string from various possible formats (same as in CustomerReservationPage)"""
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


    def format_table(self) -> None:
        """Apply formatting to the table"""
        try:
            if not self.sheet:
                return

            for r, row in enumerate(self.sheet.get_sheet_data()):
                status = row[4] if len(row) > 4 else ""

                # Default colors
                bg = "#ffffff" if r % 2 == 1 else "#f8f9fa"
                fg = "#2c3e50"
                status_bg = bg
                status_fg = fg

                # Status-specific colors
                if status == "Confirmed":
                    status_bg = "#d4edda"
                    status_fg = "#155724"
                elif status == "Pending":
                    status_bg = "#fff3cd"
                    status_fg = "#856404"
                elif status == "Cancelled":
                    status_bg = "#f8d7da"
                    status_fg = "#721c24"

                # Apply row formatting
                self.sheet.highlight_cells(row=r, bg=bg, fg=fg, canvas="table")
                self.sheet.highlight_cells(row=r, column=4, bg=status_bg, fg=status_fg, canvas="table")

        except Exception as e:
            logger.error(f"Error formatting table: {str(e)}")