import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tksheet
import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class StaffDashboard(ctk.CTkFrame):
    def __init__(self, parent, controller, db):
        super().__init__(parent)
        self.controller = controller
        self.db = db
        self.current_user = None
        self.sheet = None

        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Create components
        self.create_sidebar()
        self.create_main_content()
        logger.info("StaffDashboard initialized")

    def update_user_display(self, user_data: Dict) -> None:
        """Update the display with user information"""
        try:
            self.current_user = user_data
            logger.info(f"Updating dashboard for staff: {user_data.get('email', 'unknown')}")
            self.refresh_dashboard_data()
        except Exception as e:
            logger.error(f"Error updating staff display: {e}")
            raise

    def refresh_dashboard_data(self) -> None:
        """Refresh all data-dependent widgets"""
        try:
            if hasattr(self, 'metrics_frame'):
                self.metrics_frame.destroy()
                self.create_metrics(self.scrollable_content)

            if hasattr(self, 'welcome_frame'):
                for widget in self.welcome_frame.winfo_children():
                    widget.destroy()
                self.create_welcome_message()

            if hasattr(self, 'sheet'):
                self.update_reservations_table()

        except Exception as e:
            logger.error(f"Error during dashboard refresh: {e}")

    def create_sidebar(self) -> None:
        """Create sidebar navigation"""
        try:
            sidebar = ctk.CTkFrame(self, width=250, fg_color="#f0f9ff", corner_radius=0)
            sidebar.grid(row=0, column=0, sticky="nsew")

            nav_items = [
                ("Dashboard", "📊", "StaffDashboard"),
                ("Reservations", "🛒", "StaffReservationsPage"),
                ("Customers", "👥", "StaffCustomerManagementScreen"),
            ]

            # Add padding
            padding = ctk.CTkLabel(sidebar, text="", fg_color="transparent")
            padding.pack(pady=(20, 10))

            # Add navigation buttons
            for item, icon, frame_name in nav_items:
                is_active = frame_name == "StaffDashboard"
                btn_color = "#dbeafe" if is_active else "transparent"

                btn_frame = ctk.CTkFrame(sidebar, fg_color=btn_color, corner_radius=8)
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
            logout_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
            logout_frame.pack(side="bottom", fill="x", padx=15, pady=20)

            ctk.CTkButton(
                logout_frame,
                text="Logout",
                fg_color="#ef4444",
                hover_color="#dc2626",
                command=self.controller.logout
            ).pack(fill="x")

        except Exception as e:
            logger.error(f"Error creating sidebar: {e}")
            raise

    def create_main_content(self) -> None:
        """Create the main content area"""
        try:
            main = ctk.CTkFrame(self, fg_color="white")
            main.grid(row=0, column=1, sticky="nsew")
            main.grid_rowconfigure(1, weight=1)
            main.grid_columnconfigure(0, weight=1)

            self.create_header(main)
            self.create_scrollable_content(main)

        except Exception as e:
            logger.error(f"Error creating main content: {e}")
            raise

    def create_header(self, parent) -> None:
        """Create the header section"""
        header_frame = ctk.CTkFrame(parent, height=70, fg_color="white", corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)

        header_frame.grid_columnconfigure(0, weight=0)  # Logo
        header_frame.grid_columnconfigure(1, weight=1)  # Nav Items
        header_frame.grid_columnconfigure(2, weight=0)  # User info

        # Logo
        ctk.CTkLabel(
            header_frame,
            text="Hotel Booking System - Staff",
            font=("Arial", 16, "bold"),
            text_color="#2c3e50"
        ).grid(row=0, column=0, padx=(20, 10), pady=20, sticky="w")

        # Navigation items in header
        nav_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        nav_frame.grid(row=0, column=1, sticky="")

        nav_items = [
            ("Dashboard", "StaffDashboard"),
            ("Reservations", "StaffReservationsPage"),
            ("Customers", "StaffCustomerManagementScreen"),
        ]

        for item, frame_name in nav_items:
            text_color = "#3b82f6" if frame_name == "StaffDashboard" else "#64748b"
            btn = ctk.CTkButton(
                nav_frame,
                text=item,
                fg_color="transparent",
                text_color=text_color,
                hover_color="#f0f0f0",
                corner_radius=5,
                height=32,
                border_width=0,
                command=lambda fn=frame_name: self.controller.show_frame(fn)
            )
            btn.pack(side="left", padx=15)

        # User info
        if self.current_user:
            user_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
            user_frame.grid(row=0, column=2, padx=20, pady=10, sticky="e")

            ctk.CTkLabel(
                user_frame,
                text=f"Welcome, {self.current_user.get('full_name', 'Staff')}",
                font=("Arial", 12),
                text_color="#2c3e50"
            ).pack(side="left", padx=10)

    def create_scrollable_content(self, parent) -> None:
        """Create scrollable content area with proper grid layout"""
        try:
            self.scrollable_content = ctk.CTkScrollableFrame(parent, fg_color="#f8fafc")
            self.scrollable_content.grid(row=1, column=0, sticky="nsew")

            # Configure grid layout for the content frame
            self.scrollable_content.grid_columnconfigure(0, weight=1)
            self.scrollable_content.grid_rowconfigure(0, weight=0)  # Welcome message
            self.scrollable_content.grid_rowconfigure(1, weight=0)  # Metrics
            self.scrollable_content.grid_rowconfigure(2, weight=0)  # Revenue graph
            self.scrollable_content.grid_rowconfigure(3, weight=0)  # Quick access
            self.scrollable_content.grid_rowconfigure(4, weight=1)  # Bookings table

            # Welcome message
            self.welcome_frame = ctk.CTkFrame(self.scrollable_content, fg_color="transparent")
            self.welcome_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
            self.create_welcome_message()

            # Create metrics
            self.create_metrics(self.scrollable_content)

            # Monthly revenue graph
            self.create_revenue_graph(self.scrollable_content)

            # Quick access section
            self.create_quick_access(self.scrollable_content)

            # Recent bookings table
            self.create_reservations_table(self.scrollable_content)

        except Exception as e:
            logger.error(f"Error creating scrollable content: {e}")
            raise

    def create_welcome_message(self) -> None:
        """Create welcome message with user's name"""
        welcome_text = "Welcome Staff"
        if self.current_user and 'full_name' in self.current_user:
            welcome_text = f"Welcome back, {self.current_user['full_name']}"

        ctk.CTkLabel(
            self.welcome_frame,
            text=welcome_text,
            font=("Arial", 20, "bold"),
            text_color="#2c3e50"
        ).pack(side="left")

    def create_metrics(self, parent) -> None:
        """Create metrics cards with live data using grid layout"""
        try:
            self.metrics_frame = ctk.CTkFrame(parent, fg_color="transparent")
            self.metrics_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=20)

            # Configure the metrics frame for grid layout
            self.metrics_frame.grid_columnconfigure(0, weight=1)
            self.metrics_frame.grid_columnconfigure(1, weight=1)
            self.metrics_frame.grid_columnconfigure(2, weight=1)

            # Get data from database with error handling
            try:
                total_bookings = self.db.get_total_reservations() or 0
                active_customers = self.db.get_active_customers_count() or 0
                pending_reservations = self.db.get_pending_reservations_count() or 0
            except Exception as e:
                logger.error(f"Error fetching metrics: {e}")
                total_bookings = active_customers = pending_reservations = 0

            metrics = [
                (0, f"{total_bookings:,}", "Total bookings", "StaffReservationsPage"),
                (1, f"{active_customers:,}", "Active customers", "StaffCustomerManagementScreen"),
                (2, f"{pending_reservations:,}", "Pending reservations", "StaffReservationsPage"),
            ]

            for col, value, label, target_frame in metrics:
                card = ctk.CTkFrame(
                    self.metrics_frame,
                    fg_color="white",
                    corner_radius=12,
                    height=120
                )
                card.grid(row=0, column=col, sticky="ew", padx=10, pady=5)

                # Make entire card clickable
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

        except Exception as e:
            logger.error(f"Error creating metrics: {e}")
            raise

    def create_revenue_graph(self, parent) -> None:
        """Create monthly revenue graph using grid layout"""
        try:
            revenue_frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
            revenue_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))

            ctk.CTkLabel(
                revenue_frame,
                text="Monthly Revenue",
                font=("Arial", 16, "bold"),
                text_color="#2c3e50"
            ).pack(pady=(20, 15), padx=20, anchor="w")

            # Get data from database with error handling
            try:
                revenue_data = self.db.get_revenue_trends() or {}
                months = list(revenue_data.keys()) or ["Jan", "Feb", "Mar"]
                revenue = list(revenue_data.values()) or [0, 0, 0]
            except Exception as e:
                logger.error(f"Error fetching revenue data: {e}")
                months = ["Jan", "Feb", "Mar"]
                revenue = [0, 0, 0]

            fig, ax = plt.subplots(figsize=(10, 3), dpi=100)
            ax.plot(months, revenue, color='#3b82f6', linewidth=2, marker='o')
            ax.fill_between(months, revenue, color='#3b82f6', alpha=0.1)
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            ax.set_facecolor('white')
            fig.patch.set_facecolor('white')

            for spine in ax.spines.values():
                spine.set_visible(False)

            canvas = FigureCanvasTkAgg(fig, master=revenue_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x", padx=20, pady=(0, 20))

        except Exception as e:
            logger.error(f"Error creating revenue graph: {e}")
            raise

    def create_quick_access(self, parent) -> None:
        """Create quick access cards using grid layout"""
        try:
            quick_access_frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
            quick_access_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))

            ctk.CTkLabel(
                quick_access_frame,
                text="Quick Actions",
                font=("Arial", 16, "bold"),
                text_color="#2c3e50"
            ).pack(pady=(20, 15), padx=20, anchor="w")

            row_frame = ctk.CTkFrame(quick_access_frame, fg_color="transparent")
            row_frame.pack(padx=20, pady=(0, 20), fill="x")

            quick_items = [
                ("📅", "New Reservation", "StaffReservationsPage"),
                ("👥", "Add Customer", "StaffCustomerManagementScreen"),
            ]

            for icon, title, frame_name in quick_items:
                card = ctk.CTkFrame(
                    row_frame,
                    fg_color="#f8fafc",
                    corner_radius=12,
                    height=100,
                    width=200
                )
                card.pack(side="left", expand=True, fill="both", padx=10)

                # Make entire card clickable
                card.bind("<Button-1>", lambda e, fn=frame_name: self.controller.show_frame(fn))
                for child in card.winfo_children():
                    child.bind("<Button-1>", lambda e, fn=frame_name: self.controller.show_frame(fn))

                icon_frame = ctk.CTkFrame(card, fg_color="transparent")
                icon_frame.pack(pady=(15, 5), padx=15, anchor="w")

                ctk.CTkLabel(
                    icon_frame,
                    text=icon,
                    font=("Arial", 20),
                    text_color="#3b82f6",
                    cursor="hand2"
                ).pack(side="left", padx=(0, 10))

                btn = ctk.CTkButton(
                    icon_frame,
                    text=title,
                    font=("Arial", 14, "bold"),
                    text_color="#2c3e50",
                    fg_color="transparent",
                    hover_color="#f0f0f0",
                    command=lambda fn=frame_name: self.controller.show_frame(fn),
                    cursor="hand2"
                )
                btn.pack(side="left")

                ctk.CTkLabel(
                    card,
                    text=f"Click to {title.lower()}",
                    font=("Arial", 12),
                    text_color="#7f8c8d",
                    anchor="w",
                    justify="left",
                    cursor="hand2"
                ).pack(pady=(0, 15), padx=15, fill="x")

        except Exception as e:
            logger.error(f"Error creating quick access: {e}")
            raise

    def create_reservations_table(self, parent) -> None:
        """Create recent reservations table using grid layout"""
        try:
            bookings_frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
            bookings_frame.grid(row=4, column=0, sticky="nsew", padx=20, pady=(0, 20))

            header_frame = ctk.CTkFrame(bookings_frame, fg_color="white")
            header_frame.pack(fill="x", padx=20, pady=(20, 10))

            ctk.CTkLabel(
                header_frame,
                text="Recent Reservations",
                font=("Arial", 16, "bold"),
                text_color="#2c3e50"
            ).pack(side="left")

            ctk.CTkButton(
                header_frame,
                text="View All",
                fg_color="transparent",
                text_color="#3b82f6",
                hover_color="#f0f0f0",
                border_width=1,
                border_color="#3b82f6",
                command=lambda: self.controller.show_frame("StaffReservationsPage")
            ).pack(side="right")

            self.sheet = tksheet.Sheet(
                bookings_frame,
                align="w",
                header_align="center",
                column_width=150,
                show_x_scrollbar=True,
                show_y_scrollbar=True,
                height=400
            )
            self.sheet.enable_bindings()
            self.sheet.pack(fill="both", expand=True, padx=20, pady=(0, 20))

            self.update_reservations_table()

        except Exception as e:
            logger.error(f"Error creating reservations table: {e}")
            raise

    # def update_reservations_table(self) -> None:
    #     """Update the reservations table with current data"""
    #     try:
    #         headers = ["Reservation ID", "Room", "Check-In", "Check-Out", "Status", "Payment", "Amount"]
    #         self.sheet.headers(headers)
    #
    #         # Get data from database with error handling
    #         try:
    #             reservations = self.db.get_reservations() or []
    #             # Limit to 10 most recent reservations
    #             reservations = reservations[:10]
    #         except Exception as e:
    #             logger.error(f"Error fetching reservations: {e}")
    #             reservations = []
    #
    #         data = []
    #         for res in reservations:
    #             try:
    #                 # Get amount and format it properly
    #                 amount = res.get("amount", "N/A")
    #                 if isinstance(amount, str) and amount.startswith('$'):
    #                     amount = amount[1:]
    #                 try:
    #                     amount_float = float(amount)
    #                     formatted_amount = f"${amount_float:,.2f}"
    #                 except (ValueError, TypeError):
    #                     formatted_amount = amount
    #
    #                 row = [
    #                     str(res.get("reservation_id", "N/A")),
    #                     str(res.get("guest_name", "N/A")),
    #                     str(res.get("room_type", "N/A")),
    #                     str(res.get("check_in", "N/A")),
    #                     str(res.get("check_out", "N/A")),
    #                     str(res.get("status", "Pending")),
    #                     str(res.get("payment_status", "Pending")),
    #                     formatted_amount  # Use the properly formatted amount
    #                 ]
    #                 data.append(row)
    #             except Exception as e:
    #                 logger.error(f"Error processing reservation row: {e}")
    #                 continue
    #
    #         self.sheet.set_sheet_data(data if data else [["No data available"] * len(headers)])
    #
    #         # Configure columns
    #         self.sheet.column_width(column=0, width=120)  # ID
    #         self.sheet.column_width(column=2, width=100)  # Room
    #         self.sheet.column_width(column=3, width=100)  # Check-In
    #         self.sheet.column_width(column=4, width=100)  # Check-Out
    #         self.sheet.column_width(column=5, width=100)  # Status
    #         self.sheet.column_width(column=6, width=100)  # Payment
    #         self.sheet.column_width(column=7, width=100)  # Amount
    #
    #         self.format_table()
    #
    #     except Exception as e:
    #         logger.error(f"Error updating reservations table: {e}")
    #         if hasattr(self, 'sheet'):
    #             self.sheet.set_sheet_data([["Error loading data"] * len(headers)])
    #
    # def format_table(self) -> None:
    #     """Apply formatting to the table"""
    #     try:
    #         if not self.sheet:
    #             return
    #
    #         for r, row in enumerate(self.sheet.get_sheet_data()):
    #             status = row[5] if len(row) > 5 else ""  # Status is column 5
    #             payment = row[6] if len(row) > 6 else ""  # Payment is column 6
    #             amount = row[6] if len(row) > 6 else ""  # Amount is now column 6
    #
    #             # Default colors
    #             bg = "#ffffff" if r % 2 == 0 else "#f8f9fa"
    #             fg = "#2c3e50"
    #             status_bg = bg
    #             status_fg = fg
    #             payment_bg = bg
    #             payment_fg = fg
    #             amount_bg = bg
    #             amount_fg = "#1e40af"  # Blue color for amounts
    #
    #             # Status colors
    #             if "confirm" in status.lower():
    #                 status_bg = "#d4edda"
    #                 status_fg = "#155724"
    #             elif "pend" in status.lower():
    #                 status_bg = "#fff3cd"
    #                 status_fg = "#856404"
    #             elif "cancel" in status.lower():
    #                 status_bg = "#f8d7da"
    #                 status_fg = "#721c24"
    #
    #             # Payment colors
    #             if "paid" in payment.lower():
    #                 payment_bg = "#d4edda"
    #                 payment_fg = "#155724"
    #             elif "pend" in payment.lower():
    #                 payment_bg = "#fff3cd"
    #                 payment_fg = "#856404"
    #             elif "refund" in payment.lower():
    #                 payment_bg = "#f8d7da"
    #                 payment_fg = "#721c24"
    #
    #             # Apply formatting to entire row
    #             self.sheet.highlight_cells(row=r, bg=bg, fg=fg, canvas="table")
    #
    #             # Apply special formatting to status and payment columns
    #             self.sheet.highlight_cells(row=r, column=5, bg=status_bg, fg=status_fg, canvas="table")
    #             self.sheet.highlight_cells(row=r, column=6, bg=payment_bg, fg=payment_fg, canvas="table")
    #
    #     except Exception as e:
    #         logger.error(f"Error formatting table: {e}")
    def update_reservations_table(self) -> None:
        """Update the reservations table with current data - matching admin dashboard exactly"""
        try:
            # Match admin dashboard headers exactly
            headers = ["Booking ID", "Check-In", "Check-Out", "Status", "Payment", "Amount"]
            self.sheet.headers(headers)

            # Get data from database with error handling
            try:
                reservations = self.db.get_reservations() or []
                # Limit to 10 most recent reservations like admin dashboard
                reservations = reservations[:10]
            except Exception as e:
                logger.error(f"Error fetching reservations: {e}")
                reservations = []

            data = []
            for res in reservations:
                try:
                    # Match admin dashboard data formatting exactly
                    amount = res.get("booking_amount", res.get("amount", 0))
                    if isinstance(amount, str) and amount.startswith('$'):
                        amount = amount[1:]
                    try:
                        formatted_amount = f"${float(amount):,.2f}"
                    except (ValueError, TypeError):
                        formatted_amount = f"${0:,.2f}"

                    row = [
                        str(res.get("reservation_id", "N/A")),
                        str(res.get("checkin_date", res.get("check_in", "N/A"))),
                        str(res.get("checkout_date", res.get("check_out", "N/A"))),
                        str(res.get("fulfillment_status", res.get("status", "Pending"))),
                        str(res.get("payment_status", "Pending")),
                        formatted_amount
                    ]
                    data.append(row)
                except Exception as e:
                    logger.error(f"Error processing reservation row: {e}")
                    continue

            self.sheet.set_sheet_data(data if data else [["No data available"] * len(headers)])

            # Match admin dashboard column widths exactly
            self.sheet.column_width(column=0, width=100)  # Booking ID
            self.sheet.column_width(column=1, width=100)  # Check-In
            self.sheet.column_width(column=2, width=100)  # Check-Out
            self.sheet.column_width(column=3, width=100)  # Status
            self.sheet.column_width(column=4, width=100)  # Payment
            self.sheet.column_width(column=5, width=120)  # Amount (matches admin dashboard)

            self.format_table()

        except Exception as e:
            logger.error(f"Error updating reservations table: {e}")
            if hasattr(self, 'sheet'):
                self.sheet.set_sheet_data([["Error loading data"] * len(headers)])

    def format_table(self) -> None:
        """Apply identical formatting to admin dashboard"""
        try:
            if not self.sheet:
                return

            for r, row in enumerate(self.sheet.get_sheet_data()):
                # Column indices matching admin dashboard:
                # [0] Booking ID, [1] Check-In, [2] Check-Out, [3] Status, [4] Payment, [5] Amount
                status = row[3] if len(row) > 3 else ""
                payment = row[4] if len(row) > 4 else ""
                amount = row[5] if len(row) > 5 else ""

                # Identical color scheme to admin dashboard
                bg = "#ffffff" if r % 2 == 0 else "#f8f9fa"
                fg = "#2c3e50"
                status_bg = bg
                status_fg = fg
                payment_bg = bg
                payment_fg = fg
                amount_bg = bg
                amount_fg = "#1e40af"  # Blue for amounts (matches admin)

                # Status colors (identical to admin)
                if status == "Confirmed":
                    status_bg = "#d4edda"
                    status_fg = "#155724"
                elif status == "Pending":
                    status_bg = "#fff3cd"
                    status_fg = "#856404"
                elif status == "Cancelled":
                    status_bg = "#f8d7da"
                    status_fg = "#721c24"

                # Payment colors (identical to admin)
                if payment == "Paid":
                    payment_bg = "#d4edda"
                    payment_fg = "#155724"
                elif payment == "Pending":
                    payment_bg = "#fff3cd"
                    payment_fg = "#856404"
                elif payment == "Cancelled":
                    payment_bg = "#f8d7da"
                    payment_fg = "#721c24"

                # Apply formatting (identical to admin)
                self.sheet.highlight_cells(row=r, bg=bg, fg=fg, canvas="table")
                self.sheet.highlight_cells(row=r, column=3, bg=status_bg, fg=status_fg, canvas="table")
                self.sheet.highlight_cells(row=r, column=4, bg=payment_bg, fg=payment_fg, canvas="table")
                self.sheet.highlight_cells(row=r, column=5, bg=amount_bg, fg=amount_fg, canvas="table")

                # Right-align amount like admin dashboard
                # self.sheet.cell_align(r, 5, align="right")

        except Exception as e:
            logger.error(f"Error formatting table: {e}")