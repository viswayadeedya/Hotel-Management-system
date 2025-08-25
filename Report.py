import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import csv
import os
from fpdf import FPDF


class HotelReportsPage(ctk.CTkFrame):
    def __init__(self, parent, controller, db=None):
        super().__init__(parent)
        self.controller = controller
        self.db = db if db is not None else controller.db

        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Initialize with default data structure
        self.reports_data = {
            "new_customers": {},
            "total_customers": {},
            "revenue_data": {},
            "booking_data": {},
            "new_customers_list": []
        }

        self.create_sidebar()
        self.create_main_content()
        self.refresh_data()
        self.after(30000, self.auto_refresh)

    def refresh_data(self):
        """Refresh all data from database"""
        try:
            # Get data from database
            customer_growth = self.db.get_customer_growth() or {}
            total_customers = self._calculate_cumulative_customers(customer_growth)
            booking_trends = self.db.get_booking_trends() or {}
            revenue_trends = self.db.get_revenue_trends() or {}
            total_revenue = self.db.get_total_bookings_cost() or 0.0


            self.reports_data = {
                "new_customers": customer_growth,
                "total_customers": total_customers,
                "revenue_data": {"Total": total_revenue},
                "booking_data": booking_trends,
                "new_customers_list": self.db.get_recent_customers(5) or []
            }

            # Fill in missing months with zeros
            months = self._get_last_six_months()
            for metric in ["new_customers", "total_customers", "revenue_data", "booking_data"]:
                for month in months:
                    if month not in self.reports_data[metric]:
                        self.reports_data[metric][month] = 0

            self.update_ui()

        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load data: {str(e)}")
            months = self._get_last_six_months()
            self.reports_data = {
                "new_customers": {month: 0 for month in months},
                "total_customers": {month: 0 for month in months},
                "revenue_data": {month: 0 for month in months},
                "booking_data": {month: 0 for month in months},
                "new_customers_list": []
            }
            self.update_ui()

    def _calculate_cumulative_customers(self, customer_growth):
        """Calculate cumulative total customers from growth data"""
        total = 0
        cumulative = {}
        for month, count in sorted(customer_growth.items()):
            total += count
            cumulative[month] = total
        return cumulative

    def _get_last_six_months(self):
        """Helper to get last 6 month abbreviations"""
        return [(datetime.now() - timedelta(days=30 * i)).strftime('%b') for i in range(6)][::-1]

    def update_ui(self):
        """Update all UI components"""
        self.update_metrics()
        self.update_charts()

    def update_metrics(self):
        """Update the metric displays"""
        try:
            months = list(self.reports_data["new_customers"].keys())
            if not months:
                return

            last_month = months[-1]

            # Total Customers
            total = self.db.get_total_customers()
            self.total_customers_label.configure(text=f"{total:,}")

            # Bookings
            bookings = sum(self.reports_data["booking_data"].values())
            self.bookings_label.configure(text=f"{bookings:,}")

            # Revenue
            revenue = sum(self.reports_data["revenue_data"].values())
            self.revenue_label.configure(text=f"${revenue:,.2f}")

        except Exception as e:
            messagebox.showerror("UI Error", f"Failed to update metrics: {str(e)}")

    def update_charts(self):
        """Update all charts with current data"""
        try:
            if hasattr(self, 'revenue_canvas'):
                self.revenue_canvas.delete("all")
                self.draw_revenue_chart()

            if hasattr(self, 'bookings_canvas'):
                self.bookings_canvas.delete("all")
                self.draw_bookings_chart()

            if hasattr(self, 'new_customers_card'):
                for widget in self.new_customers_card.winfo_children():
                    if isinstance(widget, ctk.CTkFrame) and hasattr(widget, 'is_bar'):
                        widget.destroy()
                self.draw_new_customers_chart()

            if hasattr(self, 'total_customers_canvas'):
                self.total_customers_canvas.delete("all")
                self.draw_total_customers_chart()

            # Update the treeview with customer data
            if hasattr(self, 'customer_tree'):
                # Clear existing data
                for item in self.customer_tree.get_children():
                    self.customer_tree.delete(item)

                # Add new data
                for customer in self.reports_data["new_customers_list"]:
                    self.customer_tree.insert("", "end", values=(
                        customer.get("name", "N/A"),
                        customer.get("email", "N/A"),
                        customer.get("phone", "N/A"),
                        customer.get("signup_date", "N/A")
                    ))

                # Show message if no customers
                if not self.reports_data["new_customers_list"]:
                    self.customer_tree.insert("", "end", values=("No recent customers found", "", "", ""))

        except Exception as e:
            messagebox.showerror("Chart Error", f"Failed to update charts: {str(e)}")

    def draw_total_customers_chart(self):
        """Draw the total customers line chart"""
        months = list(self.reports_data["total_customers"].keys())
        if not months:
            return

        width = self.total_customers_canvas.winfo_width()
        height = 150
        padding = 30

        data = self.reports_data["total_customers"]
        values = [data[month] for month in months]
        min_value = min(values)
        max_value = max(values)
        value_range = max_value - min_value if max_value != min_value else 1

        points = []
        for i, month in enumerate(months):
            x = padding + (i * ((width - 2 * padding) / (len(months) - 1)))
            y = height - padding - ((data[month] - min_value) / value_range) * (height - 2 * padding)
            points.append((x, y))

            self.total_customers_canvas.create_text(
                x, height - 10,
                text=month,
                fill="#64748b",
                font=("Arial", 10)
            )

        for i in range(len(points) - 1):
            self.total_customers_canvas.create_line(
                points[i][0], points[i][1],
                points[i + 1][0], points[i + 1][1],
                fill="#3b82f6", width=2
            )

            self.total_customers_canvas.create_text(
                points[i][0], points[i][1] - 15,
                text=f"{values[i]:,}",
                fill="#3b82f6",
                font=("Arial", 8)
            )

        self.total_customers_canvas.create_text(
            points[-1][0], points[-1][1] - 15,
            text=f"{values[-1]:,}",
            fill="#3b82f6",
            font=("Arial", 8)
        )

    def draw_new_customers_chart(self):
        """Draw the new customers bar chart"""
        months = list(self.reports_data["new_customers"].keys())
        if not months:
            return

        data = self.reports_data["new_customers"]
        max_value = max(data.values()) or 1

        for month in months:
            bar_frame = ctk.CTkFrame(self.new_customers_card, fg_color="transparent")
            bar_frame.is_bar = True
            bar_frame.pack(fill="x", padx=20, pady=5)

            ctk.CTkLabel(
                bar_frame,
                text=month,
                font=("Arial", 12),
                text_color="#64748b",
                width=30
            ).pack(side="left", padx=(0, 10))

            bar_container = ctk.CTkFrame(bar_frame, height=10, fg_color="#e2e8f0", corner_radius=5)
            bar_container.pack(side="left", fill="x", expand=True)

            width_percent = (data[month] / max_value) * 100
            bar = ctk.CTkFrame(bar_container, height=10, fg_color="#3b82f6", corner_radius=5)
            bar.place(relx=0, rely=0, relwidth=width_percent / 100, relheight=1)

    def draw_revenue_chart(self):
        """Draw the revenue bar chart"""
        months = list(self.reports_data["revenue_data"].keys())
        if not months:
            return

        width = self.revenue_canvas.winfo_width()
        height = 100
        padding = 30

        data = self.reports_data["revenue_data"]
        values = [data[month] for month in months]
        max_value = max(values) or 1

        bar_width = width / len(months) * 0.6
        spacing = width / len(months)

        for i, (month, value) in enumerate(zip(months, values)):
            x = padding + (i * spacing)
            bar_height = (value / max_value) * (height - 2 * padding - 20)

            self.revenue_canvas.create_rectangle(
                x, height - padding - bar_height,
                   x + bar_width, height - padding,
                fill="#10b981", outline=""
            )

            self.revenue_canvas.create_text(
                x + bar_width / 2, height - padding - bar_height - 10,
                text=f"${value / 1000:.1f}k" if value >= 1000 else f"${value:.0f}",
                fill="#10b981", font=("Arial", 8)
            )

            self.revenue_canvas.create_text(
                x + bar_width / 2, height - 10,
                text=month, fill="#64748b", font=("Arial", 10)
            )

    def draw_bookings_chart(self):
        """Draw the bookings line chart"""
        months = list(self.reports_data["booking_data"].keys())
        if not months:
            return

        width = self.bookings_canvas.winfo_width()
        height = 100
        padding = 30

        data = self.reports_data["booking_data"]
        values = [data[month] for month in months]

        points = []
        for i, (month, value) in enumerate(zip(months, values)):
            x = padding + (i * ((width - 2 * padding) / (len(months) - 1)))
            y = height - padding - (value / max(values) * (height - 2 * padding - 20)) if max(
                values) > 0 else height - padding
            points.append((x, y))

            self.bookings_canvas.create_text(
                x, height - 10,
                text=month, fill="#64748b", font=("Arial", 10)
            )

        for i in range(len(points) - 1):
            self.bookings_canvas.create_line(
                points[i][0], points[i][1],
                points[i + 1][0], points[i + 1][1],
                fill="#f59e0b", width=2
            )

            self.bookings_canvas.create_oval(
                points[i][0] - 3, points[i][1] - 3,
                points[i][0] + 3, points[i][1] + 3,
                fill="#f59e0b", outline=""
            )
            self.bookings_canvas.create_text(
                points[i][0], points[i][1] - 15,
                text=f"{values[i]}",
                fill="#f59e0b",
                font=("Arial", 8)
            )

        self.bookings_canvas.create_oval(
            points[-1][0] - 3, points[-1][1] - 3,
            points[-1][0] + 3, points[-1][1] + 3,
            fill="#f59e0b", outline=""
        )
        self.bookings_canvas.create_text(
            points[-1][0], points[-1][1] - 15,
            text=f"{values[-1]}",
            fill="#f59e0b",
            font=("Arial", 8)
        )

    def auto_refresh(self):
        """Auto-refresh data at intervals"""
        self.refresh_data()
        self.after(10000, self.auto_refresh)

    def create_sidebar(self):
        """Create the sidebar navigation"""
        sidebar = ctk.CTkFrame(self, width=250, fg_color="#f0f9ff", corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")

        # Navigation items
        nav_items = [
            ("Dashboard", "📊", "HotelBookingDashboard"),
            ("Reservations", "🛒", "HotelReservationsPage"),
            ("Customers", "👥", "CustomerManagementScreen"),
            ("Reports", "📄", "HotelReportsPage"),
            ("Staff Members", "👨‍💼", "StaffMemberScreen")
        ]

        # Add padding
        padding = ctk.CTkLabel(sidebar, text="", fg_color="transparent")
        padding.pack(pady=(20, 10))

        # Add navigation buttons
        for item, icon, frame_name in nav_items:
            is_active = frame_name == "HotelReportsPage"
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

        # Add logout button
        logout_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logout_frame.pack(side="bottom", fill="x", padx=15, pady=20)

        ctk.CTkButton(
            logout_frame,
            text="Logout",
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=lambda: self.controller.show_frame("LoginApp")
        ).pack(fill="x")

    def create_main_content(self):
        """Create the main content area"""
        main = ctk.CTkFrame(self, fg_color="white")
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        # Header section
        header_frame = ctk.CTkFrame(main, height=70, fg_color="white", corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)

        # Header layout
        header_frame.grid_columnconfigure(0, weight=0)
        header_frame.grid_columnconfigure(1, weight=1)
        header_frame.grid_columnconfigure(2, weight=0)

        # Logo
        logo_label = ctk.CTkLabel(
            header_frame,
            text="Hotel Booking and Management System",
            font=("Arial", 16, "bold"),
            text_color="#2c3e50"
        )
        logo_label.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="w")

        # Navigation
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
            text_color = "#3b82f6" if frame_name == self.__class__.__name__ else "#64748b"
            btn = ctk.CTkButton(
                nav_frame,
                text=item,
                fg_color="transparent",
                text_color=text_color,
                hover_color="#f8f8f8",
                corner_radius=5,
                height=32,
                border_width=0,
                command=lambda fn=frame_name: self.controller.show_frame(fn)
            )
            btn.pack(side="left", padx=15)

        # Scrollable content area
        canvas_frame = ctk.CTkFrame(main, fg_color="#f8fafc")
        canvas_frame.grid(row=1, column=0, sticky="nsew")
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        canvas = ctk.CTkCanvas(canvas_frame, bg="#f8fafc", highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(canvas_frame, orientation="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.grid(row=0, column=1, sticky="ns")
        canvas.grid(row=0, column=0, sticky="nsew")

        content = ctk.CTkFrame(canvas, fg_color="#f8fafc")
        canvas_window = canvas.create_window((0, 0), window=content, anchor="nw")

        # Page title
        title_frame = ctk.CTkFrame(content, fg_color="transparent")
        title_frame.pack(fill="x", padx=30, pady=(30, 20))

        ctk.CTkLabel(
            title_frame,
            text="Hotel Performance Reports",
            font=("Arial", 24, "bold"),
            text_color="#2c3e50"
        ).pack(side="left")

        # Action buttons
        action_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        action_frame.pack(side="right")

        ctk.CTkButton(
            action_frame,
            text="Generate Report",
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=self.generate_report
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            action_frame,
            text="Export Data",
            fg_color="#10b981",
            hover_color="#059669",
            command=self.export_data
        ).pack(side="left", padx=5)

        # Metrics cards
        self.create_metrics_cards(content)

        # Customer list
        self.create_customer_list(content)

        # Configure scrolling
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        content.bind("<Configure>", configure_scroll_region)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)

        def on_frame_configure(event):
            canvas.configure(width=event.width)
            canvas.itemconfig(canvas_window, width=event.width)

        canvas.bind("<Configure>", on_frame_configure)

    def create_metrics_cards(self, parent):
        """Create the metrics cards"""
        cards_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cards_frame.pack(fill="x", padx=30, pady=10)
        cards_frame.grid_columnconfigure(0, weight=1)
        cards_frame.grid_columnconfigure(1, weight=1)

        # New Customers Card
        self.new_customers_card = ctk.CTkFrame(cards_frame, fg_color="white", corner_radius=12)
        self.new_customers_card.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="nsew")

        ctk.CTkLabel(
            self.new_customers_card,
            text="New Customers",
            font=("Arial", 16, "bold"),
            text_color="#475569"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.growth_label = ctk.CTkLabel(
            self.new_customers_card,
            text="+2%",
            font=("Arial", 32, "bold"),
            text_color="#3b82f6"
        )
        self.growth_label.pack(anchor="w", padx=20, pady=(0, 20))

        # Total Customers Card
        total_customers_card = ctk.CTkFrame(cards_frame, fg_color="white", corner_radius=12)
        total_customers_card.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="nsew")

        ctk.CTkLabel(
            total_customers_card,
            text="Total Customers",
            font=("Arial", 16, "bold"),
            text_color="#475569"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.total_customers_label = ctk.CTkLabel(
            total_customers_card,
            text="0",
            font=("Arial", 32, "bold"),
            text_color="#3b82f6"
        )
        self.total_customers_label.pack(anchor="w", padx=20, pady=(0, 20))

        self.total_customers_canvas = ctk.CTkCanvas(
            total_customers_card,
            height=150,
            bg="white",
            highlightthickness=0
        )
        self.total_customers_canvas.pack(fill="x", padx=20, pady=(10, 20))

        # Second row of cards
        cards_frame_2 = ctk.CTkFrame(parent, fg_color="transparent")
        cards_frame_2.pack(fill="x", padx=30, pady=10)
        cards_frame_2.grid_columnconfigure(0, weight=1)
        cards_frame_2.grid_columnconfigure(1, weight=1)

        # Revenue Card
        revenue_card = ctk.CTkFrame(cards_frame_2, fg_color="white", corner_radius=12)
        revenue_card.grid(row=0, column=0, padx=(0, 10), pady=10, sticky="nsew")

        ctk.CTkLabel(
            revenue_card,
            text="Total Revenue",
            font=("Arial", 16, "bold"),
            text_color="#475569"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.revenue_label = ctk.CTkLabel(
            revenue_card,
            text="$0.00",
            font=("Arial", 32, "bold"),
            text_color="#10b981"
        )
        self.revenue_label.pack(anchor="w", padx=20, pady=(0, 20))

        # self.revenue_canvas = ctk.CTkCanvas(revenue_card, height=100, bg="white", highlightthickness=0)
        # self.revenue_canvas.pack(fill="x", padx=20, pady=(10, 20))

        # Bookings Card
        bookings_card = ctk.CTkFrame(cards_frame_2, fg_color="white", corner_radius=12)
        bookings_card.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="nsew")

        ctk.CTkLabel(
            bookings_card,
            text="Monthly Bookings",
            font=("Arial", 16, "bold"),
            text_color="#475569"
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.bookings_label = ctk.CTkLabel(
            bookings_card,
            text="0",
            font=("Arial", 32, "bold"),
            text_color="#f59e0b"
        )
        self.bookings_label.pack(anchor="w", padx=20, pady=(0, 20))

        self.bookings_canvas = ctk.CTkCanvas(bookings_card, height=100, bg="white", highlightthickness=0)
        self.bookings_canvas.pack(fill="x", padx=20, pady=(10, 20))

    def create_customer_list(self, parent):
        """Create the recent customers list using ttk.Treeview instead of CTkTreeview"""
        ctk.CTkLabel(
            parent,
            text="Recent Customers",
            font=("Arial", 18, "bold"),
            text_color="#2c3e50"
        ).pack(anchor="w", padx=30, pady=(30, 10))

        # Create a frame to hold the Treeview and scrollbar
        table_frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
        table_frame.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        # Configure grid layout for the frame
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Create style for ttk.Treeview
        style = ttk.Style()
        style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground="#2c3e50")
        style.configure("Treeview.Heading", background="#f8fafc", foreground="#475569", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", "#1e40af")])

        # Create standard ttk.Treeview widget
        columns = ("name", "email", "phone", "signup_date")
        self.customer_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=10,  # Shows 10 rows by default
            selectmode="browse"
        )
        self.customer_tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Define headings
        self.customer_tree.heading("name", text="Name", anchor="w")
        self.customer_tree.heading("email", text="Email", anchor="w")
        self.customer_tree.heading("phone", text="Phone", anchor="w")
        self.customer_tree.heading("signup_date", text="Sign-up Date", anchor="w")

        # Configure column widths
        self.customer_tree.column("name", width=150, anchor="w")
        self.customer_tree.column("email", width=200, anchor="w")
        self.customer_tree.column("phone", width=120, anchor="w")
        self.customer_tree.column("signup_date", width=120, anchor="w")

        # Add scrollbar
        scrollbar = ctk.CTkScrollbar(
            table_frame,
            orientation="vertical",
            command=self.customer_tree.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.customer_tree.configure(yscrollcommand=scrollbar.set)

        # Populate the treeview with initial data
        for customer in self.reports_data["new_customers_list"]:
            self.customer_tree.insert("", "end",
                                      values=(
                                          customer.get("name", "N/A"),
                                          customer.get("email", "N/A"),
                                          customer.get("phone", "N/A"),
                                          customer.get("signup_date", "N/A")
                                      ))

        # Show message if no customers
        if not self.reports_data["new_customers_list"]:
            self.customer_tree.insert("", "end", values=("No recent customers found", "", "", ""))

    def generate_report(self):
        """Generate a comprehensive PDF report and save to user's device"""
        try:
            # Ask user where to save the report
            initial_dir = os.path.expanduser("~/Documents")
            if not os.path.exists(initial_dir):
                initial_dir = os.path.expanduser("~")

            file_path = filedialog.asksaveasfilename(
                initialdir=initial_dir,
                title="Save Report As",
                defaultextension=".pdf",
                filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")]
            )

            if not file_path:  # User cancelled
                return

            # Create PDF report
            self._create_pdf_report(file_path)

            messagebox.showinfo(
                "Report Generated",
                f"Report successfully saved to:\n{file_path}"
            )
        except Exception as e:
            messagebox.showerror(
                "Report Generation Failed",
                f"Error generating report: {str(e)}"
            )

    def _create_pdf_report(self, file_path):
        """Helper method to create PDF report"""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Add title
        pdf.cell(200, 10, txt="Hotel Performance Report", ln=1, align='C')
        pdf.ln(10)

        # Add date
        pdf.cell(200, 10, txt=f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=1)
        pdf.ln(10)

        # Add summary statistics
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Summary Statistics", ln=1)
        pdf.set_font("Arial", size=10)

        # Safely compute stats
        latest_total_customers = self.db.get_total_customers() or 0
        latest_new_customers = self.reports_data["new_customers"].get(
            list(self.reports_data["new_customers"].keys())[-1], 0) or 0

        total_revenue = sum(v or 0 for v in self.reports_data["revenue_data"].values())
        total_bookings = sum(v or 0 for v in self.reports_data["booking_data"].values())

        stats = [
            ("Total Customers", latest_total_customers),
            ("Total Revenue", f"${total_revenue:,.2f}"),
            ("Total Bookings", total_bookings),
            ("New Customers (Last Month)", latest_new_customers)
        ]

        for label, value in stats:
            pdf.cell(100, 8, txt=f"{label}:", ln=0)
            pdf.cell(90, 8, txt=str(value), ln=1)

        # Add monthly data table
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Monthly Performance Data", ln=1)
        pdf.set_font("Arial", size=10)

        # Table header
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(40, 8, "Month", 1, 0, 'C', 1)
        pdf.cell(30, 8, "New Customers", 1, 0, 'C', 1)
        pdf.cell(30, 8, "Total Customers", 1, 0, 'C', 1)
        pdf.cell(30, 8, "Revenue", 1, 0, 'C', 1)
        pdf.cell(30, 8, "Bookings", 1, 1, 'C', 1)

        # Table rows
        pdf.set_fill_color(255, 255, 255)
        months = list(self.reports_data["new_customers"].keys())
        for month in months:
            new_cust = self.reports_data["new_customers"].get(month, 0) or 0
            total_cust = self.reports_data["total_customers"].get(month, 0) or 0
            revenue = self.reports_data["revenue_data"].get(month, 0.0) or 0.0
            bookings = self.reports_data["booking_data"].get(month, 0) or 0

            pdf.cell(40, 8, month, 1)
            pdf.cell(30, 8, str(new_cust), 1, 0, 'R')
            pdf.cell(30, 8, str(total_cust), 1, 0, 'R')
            pdf.cell(30, 8, f"${revenue:,.2f}", 1, 0, 'R')
            pdf.cell(30, 8, str(bookings), 1, 1, 'R')

        # Add recent customers
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Recent Customers", ln=1)
        pdf.set_font("Arial", size=10)

        # Table header
        pdf.set_fill_color(200, 220, 255)
        pdf.cell(60, 8, "Name", 1, 0, 'C', 1)
        pdf.cell(70, 8, "Email", 1, 0, 'C', 1)
        pdf.cell(30, 8, "Phone", 1, 0, 'C', 1)
        pdf.cell(30, 8, "Sign-up Date", 1, 1, 'C', 1)

        # Table rows
        pdf.set_fill_color(255, 255, 255)
        for customer in self.reports_data.get("new_customers_list", []):
            pdf.cell(60, 8, customer.get("name", "N/A"), 1)
            pdf.cell(70, 8, customer.get("email", "N/A"), 1)
            pdf.cell(30, 8, customer.get("phone", "N/A"), 1)
            pdf.cell(30, 8, customer.get("signup_date", "N/A"), 1, 1)

        pdf.output(file_path)

    def export_data(self):
        """Export data to CSV file on user's device"""
        try:
            # Set default save location
            initial_dir = os.path.expanduser("~/Documents")
            if not os.path.exists(initial_dir):
                initial_dir = os.path.expanduser("~")

            # Get current timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"hotel_report_{timestamp}.csv"

            # Ask user where to save
            file_path = filedialog.asksaveasfilename(
                initialdir=initial_dir,
                initialfile=default_name,
                title="Save Data As",
                defaultextension=".csv",
                filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
            )

            if not file_path:  # User cancelled
                return

            # Write data to CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Write header
                writer.writerow(['Month', 'New Customers', 'Total Customers',
                                 'Revenue ($)', 'Bookings'])

                # Write metrics data
                months = list(self.reports_data["new_customers"].keys())
                for month in months:
                    writer.writerow([
                        month,
                        self.reports_data["new_customers"].get(month, 0),
                        self.reports_data["total_customers"].get(month, 0),
                        self.reports_data["revenue_data"].get(month, 0),
                        self.reports_data["booking_data"].get(month, 0)
                    ])

                # Write summary section
                writer.writerow([])
                writer.writerow(['SUMMARY STATISTICS'])
                writer.writerow(['Total Customers', sum(self.reports_data["new_customers"].values())])
                writer.writerow(['Total Revenue', f"${sum(self.reports_data['revenue_data'].values()):,.2f}"])
                writer.writerow(['Total Bookings', sum(self.reports_data["booking_data"].values())])

                # Write recent customers
                writer.writerow([])
                writer.writerow(['RECENT CUSTOMERS'])
                writer.writerow(['Name', 'Email', 'Phone', 'Sign-up Date'])
                for customer in self.reports_data["new_customers_list"]:
                    writer.writerow([
                        customer.get('name', ''),
                        customer.get('email', ''),
                        customer.get('phone', ''),
                        customer.get('signup_date', '')
                    ])

            messagebox.showinfo(
                "Export Successful",
                f"Data successfully exported to:\n{file_path}"
            )
        except Exception as e:
            messagebox.showerror(
                "Export Failed",
                f"Error exporting data: {str(e)}"
            )