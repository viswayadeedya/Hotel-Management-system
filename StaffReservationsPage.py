import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
from db_helper import DatabaseManager
import logging
from tkcalendar import Calendar

logger = logging.getLogger(__name__)


class StaffReservationsPage(ctk.CTkFrame):
    def __init__(self, parent, controller, db=None):
        super().__init__(parent)
        self.controller = controller
        self.db = db if db is not None else DatabaseManager()

        # Initialize data
        self.reservations = []
        self.selected_row = None
        self.selected_reservation_id = None
        self.sort_column = None
        self.sort_descending = False

        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Create components
        self.create_sidebar()
        self.create_main_content()

        # Load initial data
        self.load_data()

    def load_data(self):
        """Load reservations data from database"""
        try:
            if not hasattr(self, 'db') or not self.db.connection.is_connected():
                self.db = DatabaseManager()
                self.db.connect()

            with self.db.connection.cursor(dictionary=True) as cursor:
                cursor.execute("""
                    SELECT 
                        reservation_id as id,
                        guest_name as name,
                        room_type,
                        DATE_FORMAT(checkin_date, '%b %d, %Y') as checkin,
                        DATE_FORMAT(checkout_date, '%b %d, %Y') as checkout,
                        CONCAT('$', FORMAT(booking_amount, 2)) as amount,
                        payment_status,
                        fulfillment_status
                    FROM reservations
                    ORDER BY checkin_date DESC
                """)
                self.reservations = cursor.fetchall()

            self.display_reservations()

        except Exception as e:
            logger.error(f"Error loading reservations: {str(e)}")
            self.reservations = []
            self.display_reservations()

    def save_data(self, reservation_data=None, delete_id=None):
        """Save or delete reservation data in database"""
        try:
            if not hasattr(self, 'db') or not self.db.connection.is_connected():
                self.db = DatabaseManager()
                self.db.connect()

            with self.db.connection.cursor() as cursor:
                if reservation_data and 'id' in reservation_data:
                    try:
                        checkin_date = datetime.strptime(reservation_data['checkin'], "%b %d, %Y").date()
                        checkout_date = datetime.strptime(reservation_data['checkout'], "%b %d, %Y").date()
                        amount = float(reservation_data['amount'].replace('$', '').replace(',', ''))
                        payment_status = reservation_data.get('payment_status', 'Pending')
                        fulfillment_status = reservation_data.get('fulfillment_status', 'Pending')
                        room_type = reservation_data.get('room_type', 'Single')
                    except ValueError as e:
                        messagebox.showerror("Error", f"Invalid format: {str(e)}")
                        return False

                    if any(r['id'] == reservation_data['id'] for r in self.reservations):
                        cursor.execute("""
                            UPDATE reservations 
                            SET guest_name = %s, 
                                room_type = %s,
                                checkin_date = %s, 
                                checkout_date = %s,
                                booking_amount = %s,
                                payment_status = %s,
                                fulfillment_status = %s
                            WHERE reservation_id = %s
                        """, (
                            reservation_data['name'],
                            room_type,
                            checkin_date,
                            checkout_date,
                            amount,
                            payment_status,
                            fulfillment_status,
                            reservation_data['id']
                        ))
                    else:
                        # Generate new ID if not provided
                        if not reservation_data.get('id'):
                            reservation_data['id'] = self.db.generate_reservation_id()

                        cursor.execute("""
                            INSERT INTO reservations 
                            (reservation_id, guest_name, room_type, checkin_date, checkout_date, 
                             booking_amount, payment_status, fulfillment_status)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            reservation_data['id'],
                            reservation_data['name'],
                            room_type,
                            checkin_date,
                            checkout_date,
                            amount,
                            payment_status,
                            fulfillment_status
                        ))
                elif delete_id:
                    cursor.execute("""
                        DELETE FROM reservations 
                        WHERE reservation_id = %s
                    """, (delete_id,))

                self.db.connection.commit()
                self.load_data()
                return True

        except Exception as e:
            logger.error(f"Error saving reservation: {str(e)}")
            messagebox.showerror("Error", f"Database operation failed: {str(e)}")
            if "MySQL Connection not available" in str(e):
                try:
                    self.db.connect()
                    return self.save_data(reservation_data, delete_id)
                except:
                    pass
            return False

    def create_sidebar(self):
        """Create the sidebar navigation"""
        sidebar = ctk.CTkFrame(self, width=250, fg_color="#f0f9ff", corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")

        nav_items = [
            ("Dashboard", "📊", "StaffDashboard"),
            ("Reservations", "🛒", "StaffReservationsPage"),
            ("Customers", "👥", "StaffCustomerManagementScreen"),
        ]

        padding = ctk.CTkLabel(sidebar, text="", fg_color="transparent")
        padding.pack(pady=(20, 10))

        for item, icon, frame_name in nav_items:
            is_active = frame_name == "StaffReservationsPage"
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
        """Create the main content area with reservations table"""
        main = ctk.CTkFrame(self, fg_color="white")
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        # Header section
        header_frame = ctk.CTkFrame(main, height=70, fg_color="white", corner_radius=0)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(0, weight=0)
        header_frame.grid_columnconfigure(1, weight=1)
        header_frame.grid_columnconfigure(2, weight=0)

        logo_label = ctk.CTkLabel(
            header_frame,
            text="Hotel Booking and Management System",
            font=("Arial", 16, "bold"),
            text_color="#2c3e50"
        )
        logo_label.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="w")

        nav_items = [
            ("Dashboard", "StaffDashboard"),
            ("Reservations", "StaffReservationsPage"),
            ("Customers", "StaffCustomerManagementScreen"),
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

        if hasattr(self.controller, 'current_user') and self.controller.current_user:
            username = self.controller.current_user.get('full_name', '').split()[0]
            if username:
                icons_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
                icons_frame.grid(row=0, column=2, padx=20, sticky="e")

                ctk.CTkLabel(
                    icons_frame,
                    text=username,
                    font=("Arial", 14),
                    text_color="#64748b"
                ).pack(side="left", padx=5)

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
            text="All Reservations",
            font=("Arial", 24, "bold"),
            text_color="#2c3e50"
        ).pack(side="left")

        action_frame = ctk.CTkFrame(title_frame, fg_color="transparent")
        action_frame.pack(side="right")

        new_btn = ctk.CTkButton(
            action_frame,
            text="New Reservation",
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=self.add_reservation
        )
        new_btn.pack(side="left", padx=5)

        edit_btn = ctk.CTkButton(
            action_frame,
            text="Edit",
            fg_color="#f59e0b",
            hover_color="#d97706",
            command=self.edit_reservation
        )
        edit_btn.pack(side="left", padx=5)

        delete_btn = ctk.CTkButton(
            action_frame,
            text="Cancel",
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=self.cancel_reservation
        )
        delete_btn.pack(side="left", padx=5)

        search_frame = ctk.CTkFrame(content, fg_color="transparent")
        search_frame.pack(fill="x", padx=30, pady=(0, 20))

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search by ID, Name or Date",
            width=400,
            height=40,
            fg_color="white",
            border_color="#d1d5db",
            border_width=1,
            corner_radius=8
        )
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", self.search_reservations)

        # Treeview container
        tree_container = ctk.CTkFrame(content, fg_color="white", corner_radius=12)
        tree_container.pack(fill="both", expand=True, padx=30, pady=(0, 30))

        # Create Treeview with custom style
        style = ttk.Style()
        style.theme_use("default")

        # Configure the Treeview style
        style.configure("Custom.Treeview",
                        background="white",
                        foreground="#475569",
                        fieldbackground="white",
                        borderwidth=0,
                        font=('Arial', 12))

        style.configure("Custom.Treeview.Heading",
                        background="white",
                        foreground="#64748b",
                        font=('Arial', 12, 'bold'),
                        padding=(0, 10),
                        borderwidth=0)

        style.map("Custom.Treeview",
                  background=[('selected', '#e0f2fe')],
                  foreground=[('selected', '#475569')])

        # Left-align heading text
        style.layout("Custom.Treeview.Heading", [
            ('Treeheading.cell', {'sticky': 'w'}),
            ('Treeheading.border', {'sticky': 'nswe', 'children': [
                ('Treeheading.padding', {'sticky': 'nswe', 'children': [
                    ('Treeheading.image', {'sticky': 'e'}),
                    ('Treeheading.text', {'sticky': 'w'})
                ]})
            ]}),
            ('Treeheading.separator', {'sticky': 'nswe'})
        ])

        # Create the Treeview widget with all columns
        self.tree = ttk.Treeview(
            tree_container,
            style="Custom.Treeview",
            columns=("id", "name", "room_type", "checkin", "checkout", "amount", "payment", "fulfillment"),
            show="headings",
            selectmode="browse"
        )

        # Define headings with left alignment
        self.tree.heading("id", text="ID", anchor="w", command=lambda: self.sort_tree("id"))
        self.tree.heading("name", text="Guest Name", anchor="w", command=lambda: self.sort_tree("name"))
        self.tree.heading("room_type", text="Room Type", anchor="w", command=lambda: self.sort_tree("room_type"))
        self.tree.heading("checkin", text="Check-in", anchor="w", command=lambda: self.sort_tree("checkin"))
        self.tree.heading("checkout", text="Check-out", anchor="w", command=lambda: self.sort_tree("checkout"))
        self.tree.heading("amount", text="Amount", anchor="w", command=lambda: self.sort_tree("amount"))
        self.tree.heading("payment", text="Payment", anchor="w", command=lambda: self.sort_tree("payment"))
        self.tree.heading("fulfillment", text="Status", anchor="w", command=lambda: self.sort_tree("fulfillment"))

        # Configure column widths with left alignment
        self.tree.column("id", width=100, anchor="w")
        self.tree.column("name", width=150, anchor="w")
        self.tree.column("room_type", width=100, anchor="w")
        self.tree.column("checkin", width=100, anchor="w")
        self.tree.column("checkout", width=100, anchor="w")
        self.tree.column("amount", width=100, anchor="w")
        self.tree.column("payment", width=100, anchor="w")
        self.tree.column("fulfillment", width=100, anchor="w")

        # Configure tag for cancelled reservations
        self.tree.tag_configure('cancelled', foreground='red')

        # Add scrollbar
        tree_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll.grid(row=0, column=1, sticky="ns")

        # Configure grid weights
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        content.bind("<Configure>", configure_scroll_region)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)

    def on_tree_select(self, event):
        """Handle treeview selection"""
        selected_item = self.tree.focus()
        if selected_item:
            self.selected_row = selected_item
            self.selected_reservation_id = self.tree.item(selected_item)['values'][0]

    def display_reservations(self, reservations=None):
        """Display reservations in the treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.selected_row = None
        self.selected_reservation_id = None

        display_data = reservations if reservations is not None else self.reservations

        if not display_data:
            return

        for reservation in display_data:
            is_cancelled = reservation.get("fulfillment_status", "").lower() == "cancelled"
            tags = ("cancelled",) if is_cancelled else ()
            self.tree.insert("", "end", values=(
                reservation["id"],
                reservation["name"],
                reservation.get("room_type", ""),
                reservation["checkin"],
                reservation.get("checkout", ""),
                reservation["amount"],
                reservation.get("payment_status", "Pending"),
                reservation.get("fulfillment_status", "Pending")
            ),  tags=tags)

    def search_reservations(self, event=None):
        """Filter reservations based on search query"""
        query = self.search_entry.get().lower()

        if not query:
            self.display_reservations()
            return

        filtered = [
            r for r in self.reservations
            if (query in r["id"].lower() or
                query in r["name"].lower() or
                query in r.get("room_type", "").lower() or
                query in r["checkin"].lower() or
                query in r.get("checkout", "").lower() or
                query in r.get("payment_status", "").lower() or
                query in r.get("fulfillment_status", "").lower())
        ]

        self.display_reservations(filtered)

    def sort_tree(self, column):
        """Sort tree by column"""
        column_mapping = {
            "id": 0,
            "name": 1,
            "room_type": 2,
            "checkin": 3,
            "checkout": 4,
            "amount": 5,
            "payment": 6,
            "fulfillment": 7
        }

        col_index = column_mapping.get(column, 0)
        items = [(self.tree.set(child, col_index), child) for child in self.tree.get_children('')]

        if self.sort_column == column:
            self.sort_descending = not self.sort_descending
        else:
            self.sort_column = column
            self.sort_descending = False

        if column in ("checkin", "checkout"):
            items.sort(key=lambda x: datetime.strptime(x[0], "%b %d, %Y") if x[0] else datetime.min,
                       reverse=self.sort_descending)
        elif column in ("amount"):
            items.sort(key=lambda x: float(x[0].replace("$", "").replace(",", "")) if x[0] else 0,
                       reverse=self.sort_descending)
        else:
            items.sort(key=lambda x: x[0].lower() if x[0] else "", reverse=self.sort_descending)

        for index, (val, child) in enumerate(items):
            self.tree.move(child, '', index)

        for col in ["id", "name", "room_type", "checkin", "checkout", "amount", "payment", "fulfillment"]:
            self.tree.heading(col, text=self.tree.heading(col)['text'].rstrip(" ↑↓"))

        sort_symbol = " ↓" if self.sort_descending else " ↑"
        current_text = self.tree.heading(column)['text']
        self.tree.heading(column, text=current_text + sort_symbol)

    def open_calendar(self, parent, key, entries):
        """Open a calendar popup for date selection"""

        def set_date():
            selected_date = cal.get_date()
            # Format the date as "MMM DD, YYYY"
            formatted_date = datetime.strptime(selected_date, "%m/%d/%y").strftime("%b %d, %Y")
            entries[key].configure(text=formatted_date)
            top.destroy()

        top = ctk.CTkToplevel(parent)
        top.title("Select Date")
        top.transient(parent)
        top.grab_set()

        # Use tkinter's Frame for the calendar since tkcalendar expects it
        cal_frame = ttk.Frame(top)
        cal_frame.pack(padx=10, pady=10)

        cal = Calendar(cal_frame, selectmode="day")
        cal.pack(pady=10)

        btn_frame = ctk.CTkFrame(top, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(
            btn_frame,
            text="Select",
            command=set_date
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=top.destroy
        ).pack(side="left", padx=5)

    def add_reservation(self):
        """Open dialog to add a new reservation"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add New Reservation")
        dialog.geometry("500x800")
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

        entries = {}

        def update_price(*args):
            price_map = {
                "Single": "$100.00",
                "Double": "$150.00",
                "Suite": "$200.00",
                "Deluxe": "$250.00"
            }
            room_type = entries["room_type"].get()
            price = price_map.get(room_type, "$0.00")
            entries["amount"].delete(0, tk.END)
            entries["amount"].insert(0, price)

        fields = [
            ("ID Number", "#", "id", "entry", True),
            ("Guest Name", "Full name", "name", "entry"),
            ("Room Type", "Single", "room_type", "dropdown", ["Single", "Double", "Suite", "Deluxe"]),
            ("Check-in Date", "Select date", "checkin", "calendar"),
            ("Check-out Date", "Select date", "checkout", "calendar"),
            ("Total Booking Amount", "$0.00", "amount", "entry"),
            ("Payment Status", "Pending", "payment_status", "dropdown", ["Paid", "Pending"]),
            ("Reservation Status", "Pending", "fulfillment_status", "dropdown", ["Confirmed", "Pending"])
        ]

        for i, (label, placeholder, key, field_type, *options) in enumerate(fields):
            frame = ctk.CTkFrame(dialog, fg_color="transparent")
            frame.pack(fill="x", padx=20, pady=10)

            ctk.CTkLabel(
                frame,
                text=label,
                font=("Arial", 14),
                text_color="#475569"
            ).pack(anchor="w")

            if field_type == "entry":
                entry = ctk.CTkEntry(
                    frame,
                    placeholder_text=placeholder,
                    height=40,
                    fg_color="white",
                    border_color="#d1d5db",
                    border_width=1,
                    corner_radius=8
                )
                if key == "id":
                    entry.insert(0, self.db.generate_reservation_id())
                    entry.configure(state="disabled")
                entry.pack(fill="x")
                entries[key] = entry

            elif field_type == "dropdown":
                dropdown = ctk.CTkComboBox(
                    frame,
                    values=options[0],
                    height=40,
                    fg_color="white",
                    border_color="#d1d5db",
                    button_color="#3b82f6",
                    dropdown_fg_color="white",
                    dropdown_text_color="#475569",
                    dropdown_hover_color="#f0f0f0",
                    corner_radius=8,
                    command=update_price if key == "room_type" else None
                )
                dropdown.set(placeholder)
                dropdown.pack(fill="x")
                entries[key] = dropdown

            elif field_type == "calendar":
                cal_frame = ctk.CTkFrame(frame, fg_color="transparent")
                cal_frame.pack(fill="x")

                cal_button = ctk.CTkButton(
                    cal_frame,
                    text=placeholder,
                    height=40,
                    fg_color="white",
                    text_color="#475569",
                    border_color="#d1d5db",
                    border_width=1,
                    corner_radius=8,
                    command=lambda k=key: self.open_calendar(dialog, k, entries)
                )
                cal_button.pack(fill="x")
                entries[key] = cal_button

        update_price("Single")  # initial price

        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)

        def save():
            new_reservation = {}
            for key, entry in entries.items():
                if isinstance(entry, ctk.CTkComboBox):
                    value = entry.get().strip()
                elif isinstance(entry, ctk.CTkButton):
                    value = entry.cget("text")
                else:
                    value = entry.get().strip()

                if not value or value == "Select date":
                    messagebox.showerror("Error", f"Please select {key}")
                    return
                new_reservation[key] = value

            try:
                checkin = datetime.strptime(new_reservation["checkin"], "%b %d, %Y")
                checkout = datetime.strptime(new_reservation["checkout"], "%b %d, %Y")
                float(new_reservation["amount"].replace("$", "").replace(",", ""))
                if checkout <= checkin:
                    messagebox.showerror("Error", "Check-out date must be after check-in date")
                    return
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid format: {str(e)}")
                return

            if self.save_data(reservation_data=new_reservation):
                dialog.destroy()
                messagebox.showinfo("Success", "Reservation added successfully")

        ctk.CTkButton(
            button_frame,
            text="Save",
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=save
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            fg_color="#64748b",
            hover_color="#475569",
            command=dialog.destroy
        ).pack(side="left", padx=10)

    def edit_reservation(self):
        """Open dialog to edit selected reservation"""
        if not hasattr(self, 'selected_reservation_id') or not self.selected_reservation_id:
            messagebox.showwarning("Warning", "Please select a reservation to edit")
            return

        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "No reservation selected")
            return

        reservation_data = self.tree.item(selected_item)['values']

        # Check if reservation is already cancelled
        if reservation_data[7].lower() == 'cancelled':
            messagebox.showwarning(
                "Cannot Edit",
                "This reservation has been cancelled and cannot be modified."
            )
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Reservation")
        dialog.geometry("500x800")
        dialog.transient(self)
        dialog.grab_set()

        dialog.update_idletasks()
        width = dialog.winfo_width()
        height = dialog.winfo_height()
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")

        fields = [
            ("ID Number", reservation_data[0], "id", False, "entry"),
            ("Guest Name", reservation_data[1], "name", True, "entry"),
            ("Room Type", reservation_data[2], "room_type", True, "dropdown", ["Single", "Double", "Suite", "Deluxe"]),
            ("Check-in Date", reservation_data[3], "checkin", True, "calendar"),
            ("Check-out Date", reservation_data[4], "checkout", True, "calendar"),
            ("Total Booking Amount", reservation_data[5], "amount", True, "entry"),
            ("Payment Status", reservation_data[6], "payment_status", True, "dropdown", ["Paid", "Pending", "Cancelled"]),
            ("Reservation Status", reservation_data[7], "fulfillment_status", True, "dropdown", ["Confirmed", "Pending", "Cancelled"])
        ]

        entries = {}

        for label, value, key, editable, field_type, *options in fields:
            frame = ctk.CTkFrame(dialog, fg_color="transparent")
            frame.pack(fill="x", padx=20, pady=10)

            ctk.CTkLabel(
                frame,
                text=label,
                font=("Arial", 14),
                text_color="#475569"
            ).pack(anchor="w")

            if field_type == "entry":
                entry = ctk.CTkEntry(
                    frame,
                    placeholder_text=label,
                    height=40,
                    fg_color="white",
                    border_color="#d1d5db",
                    border_width=1,
                    corner_radius=8
                )
                entry.insert(0, value)
                entry.configure(state="normal" if editable else "disabled")
                entry.pack(fill="x")
                entries[key] = entry
            elif field_type == "dropdown":
                dropdown = ctk.CTkComboBox(
                    frame,
                    values=options[0],
                    height=40,
                    fg_color="white",
                    border_color="#d1d5db",
                    button_color="#3b82f6",
                    dropdown_fg_color="white",
                    dropdown_text_color="#475569",
                    dropdown_hover_color="#f0f0f0",
                    corner_radius=8
                )
                dropdown.set(value)
                dropdown.configure(state="normal" if editable else "disabled")
                dropdown.pack(fill="x")
                entries[key] = dropdown
            elif field_type == "calendar":
                cal_frame = ctk.CTkFrame(frame, fg_color="transparent")
                cal_frame.pack(fill="x")

                cal_button = ctk.CTkButton(
                    cal_frame,
                    text=value,
                    height=40,
                    fg_color="white",
                    text_color="#475569",
                    border_color="#d1d5db",
                    border_width=1,
                    corner_radius=8,
                    command=lambda k=key: self.open_calendar(dialog, k, entries)
                )
                cal_button.pack(fill="x")
                entries[key] = cal_button

        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)

        def save():
            updated_reservation = {'id': reservation_data[0]}
            for key, entry in entries.items():
                if isinstance(entry, ctk.CTkComboBox):
                    if entry.cget("state") != "disabled":
                        updated_reservation[key] = entry.get().strip()
                elif isinstance(entry, ctk.CTkButton):
                    if entry.cget("text") != "Select date":
                        updated_reservation[key] = entry.cget("text")
                else:
                    if entry.cget("state") != "disabled":
                        updated_reservation[key] = entry.get().strip()

            def parse_any(date_str):
                try:
                    return datetime.strptime(date_str, "%b %d, %Y")
                except ValueError:
                    return datetime.strptime(date_str, "%Y-%m-%d")

            try:
                checkin = parse_any(updated_reservation.get("checkin", reservation_data[3]))
                checkout = parse_any(updated_reservation.get("checkout", reservation_data[4]))
                amount_str = updated_reservation.get("amount", reservation_data[5])
                float(amount_str.replace("$", "").replace(",", ""))

                if checkout <= checkin:
                    messagebox.showerror("Error", "Check-out date must be after check-in date")
                    return
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid format: {str(e)}")
                return

            if self.save_data(reservation_data=updated_reservation):
                dialog.destroy()
                messagebox.showinfo("Success", "Reservation updated successfully")

        ctk.CTkButton(
            button_frame,
            text="Save",
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=save
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            fg_color="#64748b",
            hover_color="#475569",
            command=dialog.destroy
        ).pack(side="left", padx=10)

    # def delete_reservation(self):
    #     """Delete selected reservation"""
    #     if not hasattr(self, 'selected_reservation_id') or not self.selected_reservation_id:
    #         messagebox.showwarning("Warning", "Please select a reservation to delete")
    #         return

    #     reservation = next(
    #         (r for r in self.reservations if r["id"] == self.selected_reservation_id),
    #         None
    #     )

    #     if not reservation:
    #         messagebox.showerror("Error", "Selected reservation not found")
    #         return

    #     if not messagebox.askyesno(
    #             "Confirm",
    #             f"Are you sure you want to delete reservation {reservation['id']} for {reservation['name']}?"
    #     ):
    #         return

    #     if self.save_data(delete_id=self.selected_reservation_id):
    #         self.selected_row = None
    #         self.selected_reservation_id = None
    #         messagebox.showinfo("Success", "Reservation deleted successfully")

    def cancel_reservation(self):
        """Cancel selected reservation instead of deleting"""
        if not self.selected_reservation_id:
            messagebox.showwarning("Warning", "Please select a reservation to cancel")
            return

        reservation = next(
            (r for r in self.reservations if r["id"] == self.selected_reservation_id),
            None
        )

        if not reservation:
            messagebox.showerror("Error", "Selected reservation not found")
            return

        if reservation.get("fulfillment_status", "").lower() == "cancelled":
            messagebox.showinfo("Info", "Reservation is already cancelled")
            return

        if not messagebox.askyesno(
            "Confirm Cancellation",
            f"Are you sure you want to cancel reservation {reservation['id']} for {reservation['name']}?\n"
            "This will mark the reservation as 'Cancelled' but retain the record."
        ):
            return

        try:
            with self.db.connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE reservations
                    SET fulfillment_status = %s,
                        payment_status = %s
                    WHERE reservation_id = %s
                """, ("Cancelled", "Cancelled", reservation["id"]))
            self.db.connection.commit()
            self.load_data()
            messagebox.showinfo("Success", "Reservation marked as cancelled")
        except Exception as e:
            logger.error(f"Error cancelling reservation: {str(e)}")
            messagebox.showerror("Error", f"Failed to cancel reservation: {str(e)}")
