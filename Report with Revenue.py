import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
import csv

class HotelReportsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.db = controller.db
        
        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Initialize with default data structure
        self.reports_data = {
            "new_customers": {},
            "total_customers": {},
            "revenue_data": {},
            "occupancy_data": {},
            "new_customers_list": []
        }
        
        self.create_sidebar()
        self.create_main_content()
        self.refresh_data()
        self.after(30000, self.auto_refresh)  # Auto-refresh every 30 seconds

    def refresh_data(self):
        """Refresh all data from database with proper error handling"""
        try:
            # Get data from database
            self.reports_data = {
                "new_customers": self.db.get_customer_growth() or {},
                "total_customers": self.db.get_total_customers() or {},
                "revenue_data": self.db.get_revenue_data() or {},
                "occupancy_data": self.db.get_occupancy_data() or {},
                "new_customers_list": self.db.get_recent_customers(5) or []
            }
            
            # Fill in missing months with zeros
            months = self._get_last_six_months()
            for metric in ["new_customers", "total_customers", "revenue_data", "occupancy_data"]:
                for month in months:
                    if month not in self.reports_data[metric]:
                        self.reports_data[metric][month] = 0
            
            self.update_ui()
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to load data: {str(e)}")
            # Initialize with empty data if database fails
            months = self._get_last_six_months()
            self.reports_data = {
                "new_customers": {month: 0 for month in months},
                "total_customers": {month: 0 for month in months},
                "revenue_data": {month: 0 for month in months},
                "occupancy_data": {month: 0 for month in months},
                "new_customers_list": []
            }
            self.update_ui()

    def _get_last_six_months(self):
        """Helper to get last 6 month abbreviations"""
        return [(datetime.now() - timedelta(days=30*i)).strftime('%b') for i in range(6)][::-1]

    def update_ui(self):
        """Update all UI components"""
        self.update_metrics()
        self.update_charts()
        self.update_customer_list()

    def update_metrics(self):
        """Update the metric displays"""
        try:
            months = list(self.reports_data["new_customers"].keys())
            if not months:
                return
                
            last_month = months[-1]
            
            # New Customers Growth
            if len(months) >= 2:
                current = self.reports_data["new_customers"].get(last_month, 0)
                previous = self.reports_data["new_customers"].get(months[-2], 0)
                growth_pct = ((current - previous) / previous * 100) if previous != 0 else 0
                self.growth_label.configure(text=f"{growth_pct:+.1f}%")
            
            # Total Customers
            total = self.reports_data["total_customers"].get(last_month, 0)
            self.total_customers_label.configure(text=f"{total:,}")
            
            # Revenue
            revenue = self.reports_data["revenue_data"].get(last_month, 0)
            self.revenue_label.configure(text=f"${revenue:,.2f}")
            
            # Occupancy Rate
            occupancy = self.reports_data["occupancy_data"].get(last_month, 0)
            self.occupancy_label.configure(text=f"{occupancy:.1f}%")
            
        except Exception as e:
            messagebox.showerror("UI Error", f"Failed to update metrics: {str(e)}")

    def update_charts(self):
        """Update all charts with current data"""
        try:
            if hasattr(self, 'revenue_canvas'):
                self.revenue_canvas.delete("all")
                self.draw_revenue_chart()
                
            if hasattr(self, 'occupancy_canvas'):
                self.occupancy_canvas.delete("all")
                self.draw_occupancy_chart()
                
            if hasattr(self, 'new_customers_card'):
                for widget in self.new_customers_card.winfo_children():
                    if isinstance(widget, ctk.CTkFrame) and hasattr(widget, 'is_bar'):
                        widget.destroy()
                self.draw_new_customers_chart()
                
            if hasattr(self, 'total_customers_canvas'):
                self.total_customers_canvas.delete("all")
                self.draw_total_customers_chart()
                
        except Exception as e:
            messagebox.showerror("Chart Error", f"Failed to update charts: {str(e)}")

    def update_customer_list(self):
        """Update the recent customers list"""
        try:
            if hasattr(self, 'customer_list_frame'):
                # Clear existing rows (keeping headers)
                for widget in self.customer_list_frame.winfo_children()[2:]:
                    widget.destroy()
                
                # Add current data
                for customer in self.reports_data["new_customers_list"]:
                    self.add_customer_row(customer)
                    
                # Show message if no customers
                if not self.reports_data["new_customers_list"]:
                    ctk.CTkLabel(
                        self.customer_list_frame,
                        text="No recent customers found",
                        text_color="#64748b"
                    ).pack(pady=20)
                    
        except Exception as e:
            messagebox.showerror("List Error", f"Failed to update customer list: {str(e)}")

    def auto_refresh(self):
        """Auto-refresh data at intervals"""
        self.refresh_data()
        self.after(30000, self.auto_refresh)

    def create_sidebar(self):
        """Create the sidebar navigation"""
        sidebar = ctk.CTkFrame(self, width=250, fg_color="#f0f9ff", corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        
        # Navigation items
        nav_items = [
            ("Dashboard", "📊", "HotelBookingDashboard"),
            ("Reservations", "🛒", "HotelReservationsPage"),
            ("Customers", "👥", "CustomerManagementScreen"),
            ("Reports", "📄", "HotelReportsPage")
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
            text="Hotel Booking System", 
            font=("Arial", 16, "bold"), 
            text_color="#2c3e50"
        )
        logo_label.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="w")
        
        # Navigation
        nav_items = [
            ("Dashboard", "HotelBookingDashboard"),
            ("Customers", "CustomerManagementScreen"),
            ("Reservations", "HotelReservationsPage"),
            ("Reports", "HotelReportsPage")
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
        
        # Icons
        icons_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        icons_frame.grid(row=0, column=2, padx=20, sticky="e")
        
        ctk.CTkLabel(icons_frame, text="🔍", font=("Arial", 20)).pack(side="left", padx=10)
        ctk.CTkLabel(icons_frame, text="🔔", font=("Arial", 20)).pack(side="left", padx=10)
        ctk.CTkLabel(icons_frame, text="👤", font=("Arial", 20)).pack(side="left", padx=10)
        
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
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
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
            text="+0%",
            font=("Arial", 32, "bold"),
            text_color="#3b82f6"
        )
        self.growth_label.pack(anchor="w", padx=20, pady=(0, 20))
        
        # Total Customers Card
        self.total_customers_card = ctk.CTkFrame(cards_frame, fg_color="white", corner_radius=12)
        self.total_customers_card.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="nsew")
        
        ctk.CTkLabel(
            self.total_customers_card,
            text="Total Customers",
            font=("Arial", 16, "bold"),
            text_color="#475569"
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        self.total_customers_label = ctk.CTkLabel(
            self.total_customers_card,
            text="0",
            font=("Arial", 32, "bold"),
            text_color="#3b82f6"
        )
        self.total_customers_label.pack(anchor="w", padx=20, pady=(0, 20))
        
        self.total_customers_canvas = ctk.CTkCanvas(
            self.total_customers_card, 
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
            text="Monthly Revenue",
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
        
        self.revenue_canvas = ctk.CTkCanvas(revenue_card, height=100, bg="white", highlightthickness=0)
        self.revenue_canvas.pack(fill="x", padx=20, pady=(10, 20))
        
        # Occupancy Card
        occupancy_card = ctk.CTkFrame(cards_frame_2, fg_color="white", corner_radius=12)
        occupancy_card.grid(row=0, column=1, padx=(10, 0), pady=10, sticky="nsew")
        
        ctk.CTkLabel(
            occupancy_card,
            text="Occupancy Rate",
            font=("Arial", 16, "bold"),
            text_color="#475569"
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        self.occupancy_label = ctk.CTkLabel(
            occupancy_card,
            text="0%",
            font=("Arial", 32, "bold"),
            text_color="#f59e0b"
        )
        self.occupancy_label.pack(anchor="w", padx=20, pady=(0, 20))
        
        self.occupancy_canvas = ctk.CTkCanvas(occupancy_card, height=100, bg="white", highlightthickness=0)
        self.occupancy_canvas.pack(fill="x", padx=20, pady=(10, 20))

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
            bar.place(relx=0, rely=0, relwidth=width_percent/100, relheight=1)

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
                points[i+1][0], points[i+1][1],
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
                x + bar_width/2, height - padding - bar_height - 10,
                text=f"${value/1000:.1f}k" if value >= 1000 else f"${value:.0f}",
                fill="#10b981", font=("Arial", 8)
            )
            
            self.revenue_canvas.create_text(
                x + bar_width/2, height - 10,
                text=month, fill="#64748b", font=("Arial", 10)
            )

    def draw_occupancy_chart(self):
        """Draw the occupancy line chart"""
        months = list(self.reports_data["occupancy_data"].keys())
        if not months:
            return
            
        width = self.occupancy_canvas.winfo_width()
        height = 100
        padding = 30
        
        data = self.reports_data["occupancy_data"]
        values = [data[month] for month in months]
        
        points = []
        for i, (month, value) in enumerate(zip(months, values)):
            x = padding + (i * ((width - 2 * padding) / (len(months) - 1)))
            y = height - padding - (value / 100) * (height - 2 * padding - 20)
            points.append((x, y))
            
            self.occupancy_canvas.create_text(
                x, height - 10,
                text=month, fill="#64748b", font=("Arial", 10)
            )
        
        for i in range(len(points) - 1):
            self.occupancy_canvas.create_line(
                points[i][0], points[i][1], 
                points[i+1][0], points[i+1][1],
                fill="#f59e0b", width=2
            )
            
            self.occupancy_canvas.create_oval(
                points[i][0] - 3, points[i][1] - 3,
                points[i][0] + 3, points[i][1] + 3,
                fill="#f59e0b", outline=""
            )
            self.occupancy_canvas.create_text(
                points[i][0], points[i][1] - 15,
                text=f"{values[i]}%",
                fill="#f59e0b",
                font=("Arial", 8)
            )
        
        self.occupancy_canvas.create_oval(
            points[-1][0] - 3, points[-1][1] - 3,
            points[-1][0] + 3, points[-1][1] + 3,
            fill="#f59e0b", outline=""
        )
        self.occupancy_canvas.create_text(
            points[-1][0], points[-1][1] - 15,
            text=f"{values[-1]}%",
            fill="#f59e0b",
            font=("Arial", 8)
        )

    def create_customer_list(self, parent):
        """Create the recent customers list"""
        ctk.CTkLabel(
            parent,
            text="Recent Customers",
            font=("Arial", 18, "bold"),
            text_color="#2c3e50"
        ).pack(anchor="w", padx=30, pady=(30, 20))
        
        self.customer_list_frame = ctk.CTkFrame(parent, fg_color="white", corner_radius=12)
        self.customer_list_frame.pack(fill="x", padx=30, pady=(0, 30), anchor="n")
        
        # Headers
        headers = ["Name", "Email", "Phone", "Sign-up Date"]
        header_frame = ctk.CTkFrame(self.customer_list_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        for header in headers:
            ctk.CTkLabel(
                header_frame,
                text=header,
                font=("Arial", 14, "bold"),
                text_color="#64748b"
            ).pack(side="left", expand=True, fill="x")
        
        # Separator
        ctk.CTkFrame(self.customer_list_frame, height=1, fg_color="#e2e8f0").pack(fill="x", padx=20)
        
        # Add customer rows
        for customer in self.reports_data["new_customers_list"]:
            self.add_customer_row(customer)

    def add_customer_row(self, customer):
        """Add a row to the customer list"""
        row_frame = ctk.CTkFrame(self.customer_list_frame, fg_color="transparent")
        row_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            row_frame,
            text=customer.get("name", "N/A"),
            font=("Arial", 14),
            text_color="#475569"
        ).pack(side="left", expand=True, fill="x")
        
        ctk.CTkLabel(
            row_frame,
            text=customer.get("email", "N/A"),
            font=("Arial", 14),
            text_color="#475569"
        ).pack(side="left", expand=True, fill="x")
        
        ctk.CTkLabel(
            row_frame,
            text=customer.get("phone", "N/A"),
            font=("Arial", 14),
            text_color="#475569"
        ).pack(side="left", expand=True, fill="x")
        
        ctk.CTkLabel(
            row_frame,
            text=customer.get("signup_date", "N/A"),
            font=("Arial", 14),
            text_color="#475569"
        ).pack(side="left", expand=True, fill="x")
        
        if customer != self.reports_data["new_customers_list"][-1]:
            ctk.CTkFrame(self.customer_list_frame, height=1, fg_color="#f1f5f9").pack(fill="x", padx=20)

    def generate_report(self):
        """Generate a report dialog"""
        messagebox.showinfo("Generate Report", "Report generation would open a dialog with options")

    def export_data(self):
        """Export data to CSV"""
        try:
            filename = f"hotel_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write metrics header
                writer.writerow(['Month', 'New Customers', 'Total Customers', 'Revenue', 'Occupancy Rate'])
                
                # Write metrics data
                months = list(self.reports_data["new_customers"].keys())
                for month in months:
                    writer.writerow([
                        month,
                        self.reports_data["new_customers"].get(month, 0),
                        self.reports_data["total_customers"].get(month, 0),
                        f"${self.reports_data['revenue_data'].get(month, 0):.2f}",
                        f"{self.reports_data['occupancy_data'].get(month, 0)}%"
                    ])
                
                # Write recent customers
                writer.writerow([])
                writer.writerow(['Recent Customers'])
                writer.writerow(['Name', 'Email', 'Phone', 'Sign-up Date'])
                for customer in self.reports_data["new_customers_list"]:
                    writer.writerow([
                        customer.get('name', ''),
                        customer.get('email', ''),
                        customer.get('phone', ''),
                        customer.get('signup_date', '')
                    ])
            
            messagebox.showinfo("Export Successful", f"Data exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Error exporting data: {str(e)}")