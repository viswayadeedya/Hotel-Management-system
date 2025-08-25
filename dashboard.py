import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tksheet
import logging
from typing import Dict  # Added import for Dict type hint

logger = logging.getLogger(__name__)


class HotelBookingDashboard(ctk.CTkFrame):
    def __init__(self, parent, controller, db=None):
        super().__init__(parent)
        self.controller = controller
        self.db = db  # Use the passed database connection

        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        print("Admin dashboard initialized-------->>>")
        # Create components
        self.create_sidebar()
        self.create_main_content()
        logger.info("HotelBookingDashboard initialized")

    def update_user_display(self, user_data: Dict) -> None:
        """Update the display with user information"""
        try:
            self.current_user = user_data
            logger.info(f"Updating dashboard for user: {user_data.get('email', 'unknown')}")
            self.refresh_dashboard_data()
        except Exception as e:
            logger.error(f"Error updating user display: {e}")
            raise

    def refresh_dashboard_data(self) -> None:
        """Refresh all data-dependent widgets"""
        try:
            # Get the parent of the metrics_frame
            content_parent = None
            if hasattr(self, 'metrics_frame'):
                content_parent = self.metrics_frame.master
                self.metrics_frame.destroy()

            # Only create metrics if we have a parent to create them in
            if content_parent:
                self.create_metrics(content_parent)

            if hasattr(self, 'welcome_frame'):
                for widget in self.welcome_frame.winfo_children():
                    widget.destroy()
                self.create_welcome_message()

            if hasattr(self, 'sheet'):
                self.update_bookings_table()
        except Exception as e:
            logger.error(f"Error refreshing dashboard data: {e}")
            raise

    def create_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=250, fg_color="#f0f9ff", corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")

        # Navigation buttons with explicit frame names
        nav_items = [
            ("Dashboard", "📊", "HotelBookingDashboard"),
            ("Reservations", "🛒", "HotelReservationsPage"),
            ("Customers", "👥", "CustomerManagementScreen"),
            ("Reports", "📄", "HotelReportsPage"),
            ("Staff Members", "👨‍💼", "StaffMemberScreen"),
        ]

        # Add padding at the top
        padding = ctk.CTkLabel(sidebar, text="", fg_color="transparent")
        padding.pack(pady=(20, 10))

        for item, icon, frame_name in nav_items:
            # Determine if this is the active item
            is_active = frame_name == "HotelBookingDashboard"
            btn_color = "#dbeafe" if is_active else "transparent"

            btn_frame = ctk.CTkFrame(sidebar, fg_color=btn_color, corner_radius=8)
            btn_frame.pack(fill="x", padx=15, pady=5)

            # Container for icon and text
            content_frame = ctk.CTkFrame(btn_frame, fg_color="transparent")
            content_frame.pack(pady=8, padx=15, anchor="w")

            # Icon
            ctk.CTkLabel(
                content_frame,
                text=icon,
                font=("Arial", 16),
                text_color="#64748b"
            ).pack(side="left", padx=(0, 10))

            # Text
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

        # Logout button at the bottom
        logout_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logout_frame.pack(side="bottom", fill="x", padx=15, pady=20)

        ctk.CTkButton(
            logout_frame,
            text="Logout",
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=self.controller.logout
        ).pack(fill="x")

    def create_main_content(self):
        """Create the main content area with dashboard widgets"""
        # Main container
        main = ctk.CTkFrame(self, fg_color="white")
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        # ===== HEADER SECTION =====
        header_frame = ctk.CTkFrame(main, height=70, fg_color="white", corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)

        # Create header with evenly spaced items
        header_frame.grid_columnconfigure(0, weight=0)  # Logo
        header_frame.grid_columnconfigure(1, weight=1)  # Nav Items (centered)
        header_frame.grid_columnconfigure(2, weight=0)  # Icons

        # Logo
        logo_label = ctk.CTkLabel(
            header_frame,
            text="Hotel Booking and Management System",
            font=("Arial", 16, "bold"),
            text_color="#2c3e50"
        )
        logo_label.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="w")

        # Navigation items in header
        nav_items = [
            ("Dashboard", "HotelBookingDashboard"),
            ("Customers", "CustomerManagementScreen"),
            ("Reservations", "HotelReservationsPage"),
            ("Reports", "HotelReportsPage"),
            ("Staff Members", "StaffMemberScreen")
        ]

        nav_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        nav_frame.grid(row=0, column=1, sticky="")

        for item, frame_name in nav_items:
            text_color = "#3b82f6" if frame_name == "HotelBookingDashboard" else "#64748b"
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

        # ===== CONTENT AREA =====
        content = ctk.CTkScrollableFrame(main, fg_color="#f8fafc")
        content.grid(row=1, column=0, sticky="nsew")

        # Configure grid layout for the content frame
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=0)  # Welcome message
        content.grid_rowconfigure(1, weight=0)  # Metrics
        content.grid_rowconfigure(2, weight=0)  # Revenue graph
        content.grid_rowconfigure(3, weight=0)  # Quick access
        content.grid_rowconfigure(4, weight=1)  # Bookings table

        # Welcome message
        self.welcome_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.welcome_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.create_welcome_message()

        # Create metrics
        self.create_metrics(content)

        # Monthly revenue graph
        self.create_revenue_graph(content)

        # Quick access section
        self.create_quick_access(content)

        # Recent bookings table
        self.create_bookings_table(content)

    def create_welcome_message(self):
        welcome_text = "Good morning, Admin"
        if hasattr(self, 'current_user') and self.current_user:
            welcome_text = f"Welcome back, {self.current_user.get('full_name', 'Admin')}"

        ctk.CTkLabel(
            self.welcome_frame,
            text=welcome_text,
            font=("Arial", 20, "bold"),
            text_color="#2c3e50"
        ).pack(side="left")

    def create_metrics(self, parent):
        """Create metrics cards with live data"""
        try:
            # Changed to use the parent parameter instead of self.winfo_children()
            self.metrics_frame = ctk.CTkFrame(parent, fg_color="transparent")
            self.metrics_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=20)

            # Configure the metrics frame for grid layout to match parent
            self.metrics_frame.grid_columnconfigure(0, weight=1)
            self.metrics_frame.grid_columnconfigure(1, weight=1)
            self.metrics_frame.grid_columnconfigure(2, weight=1)
            self.metrics_frame.grid_columnconfigure(3, weight=1)

            # Get data from database
            total_bookings_cost = self.db.get_total_bookings_cost()
            active_customers = self.db.get_active_customers_count()
            total_reservations = self.db.get_total_reservations()
            pending_reservations = self.db.get_pending_reservations_count()

            metrics = [
                (0, f"${total_bookings_cost:,.2f}", "Total bookings cost", "HotelReservationsPage"),
                (1, f"{active_customers:,}", "Active customers", "CustomerManagementScreen"),
                (2, f"{total_reservations:,}", "Total reservations", "HotelReservationsPage"),
                (3, f"{pending_reservations:,}", "Pending reservations", "HotelReservationsPage")
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

    def create_revenue_graph(self, parent):
        """Create monthly revenue graph"""
        try:
            revenue_frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
            revenue_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))

            ctk.CTkLabel(
                revenue_frame,
                text="Monthly revenue",
                font=("Arial", 16, "bold"),
                text_color="#2c3e50"
            ).pack(pady=(20, 15), padx=20, anchor="w")

            # Get data from database
            revenue_data = self.db.get_revenue_trends()
            months = list(revenue_data.keys())
            revenue = list(revenue_data.values())

            # Create matplotlib figure
            fig, ax = plt.subplots(figsize=(10, 3), dpi=100)
            ax.plot(months, revenue, color='#3b82f6', linewidth=2, marker='o')
            ax.fill_between(months, revenue, color='#3b82f6', alpha=0.1)
            ax.grid(axis='y', linestyle='--', alpha=0.7)
            ax.set_facecolor('white')
            fig.patch.set_facecolor('white')

            # Remove borders
            for spine in ax.spines.values():
                spine.set_visible(False)

            # Embed in Tkinter
            canvas = FigureCanvasTkAgg(fig, master=revenue_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="x", padx=20, pady=(0, 20))

        except Exception as e:
            logger.error(f"Error creating revenue graph: {e}")
            raise

    def create_quick_access(self, parent):
        """Create quick access cards"""
        try:
            quick_access_frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
            quick_access_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))

            ctk.CTkLabel(
                quick_access_frame,
                text="Quick access",
                font=("Arial", 16, "bold"),
                text_color="#2c3e50"
            ).pack(pady=(20, 15), padx=20, anchor="w")

            # Single row frame for all items
            row_frame = ctk.CTkFrame(quick_access_frame, fg_color="transparent")
            row_frame.pack(padx=20, pady=(0, 20), fill="x")

            quick_items = [
                ("👥", "Customers", "CustomerManagementScreen"),
                ("📅", "Reservations", "HotelReservationsPage"),
                ("📊", "Reports", "HotelReportsPage")
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

                # Icon and title row
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

                # Description
                ctk.CTkLabel(
                    card,
                    text=f"View and manage {title.lower()}",
                    font=("Arial", 12),
                    text_color="#7f8c8d",
                    anchor="w",
                    justify="left",
                    cursor="hand2"
                ).pack(pady=(0, 15), padx=15, fill="x")

        except Exception as e:
            logger.error(f"Error creating quick access: {e}")
            raise

    def create_bookings_table(self, parent):
        """Create recent bookings table"""
        try:
            bookings_frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
            bookings_frame.grid(row=4, column=0, sticky="nsew", padx=20, pady=(0, 20))

            # Header
            header_frame = ctk.CTkFrame(bookings_frame, fg_color="white")
            header_frame.pack(fill="x", padx=20, pady=(20, 10))

            ctk.CTkLabel(
                header_frame,
                text="Recent bookings",
                font=("Arial", 16, "bold"),
                text_color="#2c3e50"
            ).pack(side="left")

            # Create the sheet with proper expansion
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

            self.update_bookings_table()

        except Exception as e:
            logger.error(f"Error creating bookings table: {e}")
            raise

    def update_bookings_table(self):
        """Update the bookings table with current reservation data"""
        try:
            # Set headers
            headers = ["Booking ID", "Check-In", "Check-Out", "Status", "Payment", "Amount"]
            self.sheet.headers(headers)

            # Get data from database
            reservations = self.db.get_reservations()  # This now returns all needed fields

            # Prepare data for the sheet
            data = []
            for res in reservations[:10]:  # Show only 10 most recent
                amount = res.get("amount", "N/A")
                # Format amount if it's numeric (remove $ if already present and format)
                if isinstance(amount, str) and amount.startswith('$'):
                    amount = amount[1:]
                try:
                    amount_float = float(amount)
                    formatted_amount = f"${amount_float:,.2f}"
                except (ValueError, TypeError):
                    formatted_amount = amount

                row = [
                    res.get("reservation_id", "N/A"),
                    res.get("check_in", "N/A"),
                    res.get("check_out", "N/A"),
                    res.get("status", "Pending"),
                    res.get("payment_status", "Pending"),
                    formatted_amount
                ]
                data.append(row)

            self.sheet.set_sheet_data(data)

            # Configure column widths
            self.sheet.column_width(column=0, width=100)  # Booking ID
            self.sheet.column_width(column=1, width=100)  # Check-In
            self.sheet.column_width(column=2, width=100)  # Check-Out
            self.sheet.column_width(column=3, width=100)  # Status
            self.sheet.column_width(column=4, width=100)  # Payment
            self.sheet.column_width(column=5, width=120)  # Amount (wider for formatted numbers)

            # Apply formatting
            self.format_table()

        except Exception as e:
            logger.error(f"Error updating bookings table: {e}")
            raise

    def format_table(self):
        """Apply enhanced formatting and colors to the table"""
        try:
            if not self.sheet:
                return

            for r, row in enumerate(self.sheet.get_sheet_data()):
                # The columns in the data array correspond to:
                # [0] Booking ID, [1] Check-In, [2] Check-Out, [3] Status, [4] Payment, [5] Amount
                # Adjusting indices to match the correct columns
                status = row[3] if len(row) > 3 else ""  # Status is at index 3
                payment = row[4] if len(row) > 4 else ""  # Payment is at index 4
                amount = row[5] if len(row) > 5 else ""

                # Default colors
                bg = "#ffffff" if r % 2 == 0 else "#f8f9fa"
                fg = "#2c3e50"
                status_bg = bg
                status_fg = fg
                payment_bg = bg
                payment_fg = fg
                amount_bg = bg
                amount_fg = "#1e40af"  # Blue color for amounts

                # Status colors
                if status == "Confirmed":
                    status_bg = "#d4edda"
                    status_fg = "#155724"
                elif status == "Pending":
                    status_bg = "#fff3cd"
                    status_fg = "#856404"
                elif status == "Cancelled":
                    status_bg = "#f8d7da"
                    status_fg = "#721c24"

                # Payment colors
                if payment == "Paid":
                    payment_bg = "#d4edda"
                    payment_fg = "#155724"
                elif payment == "Pending":
                    payment_bg = "#fff3cd"
                    payment_fg = "#856404"
                elif payment == "Refunded":
                    payment_bg = "#f8d7da"
                    payment_fg = "#721c24"

                # Apply formatting to all cells in row
                self.sheet.highlight_cells(row=r, bg=bg, fg=fg, canvas="table")

                # Apply specific formatting to status cell (index 3)
                if len(row) > 3:
                    self.sheet.highlight_cells(
                        row=r, column=3,
                        bg=status_bg, fg=status_fg,
                        canvas="table"
                    )

                # Apply specific formatting to payment cell (index 4)
                if len(row) > 4:
                    self.sheet.highlight_cells(
                        row=r, column=4,
                        bg=payment_bg, fg=payment_fg,
                        canvas="table"
                    )

                    # Apply specific formatting to amount cell (index 5)
                    if len(row) > 5:
                        self.sheet.highlight_cells(
                            row=r, column=5,
                            bg=amount_bg, fg=amount_fg,
                            canvas="table"
                        )


        except Exception as e:
            logger.error(f"Error formatting table: {e}")
            raise