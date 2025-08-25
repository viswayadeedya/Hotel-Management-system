import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from db_helper import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class StaffCustomerManagementScreen(ctk.CTkFrame):
    def __init__(self, parent, controller, db):
        super().__init__(parent)
        self.controller = controller
        self.db = db
        self.current_user = None

        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Create components
        self.create_sidebar()
        self.create_main_content()

        # Load initial data
        self.filter_customers("all")

    def create_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=250, fg_color="#f0f9ff", corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")

        # Navigation items
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
            is_active = frame_name == "StaffCustomerManagementScreen"
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
            command=self.controller.logout
        ).pack(fill="x")

    def create_main_content(self):
        """Create the main content area with customer management"""
        # Main container
        main = ctk.CTkFrame(self, fg_color="white")
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_rowconfigure(1, weight=1)
        main.grid_columnconfigure(0, weight=1)

        # Header section
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

        # Content area
        content = ctk.CTkFrame(main, fg_color="#f8fafc")
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        content.grid_columnconfigure(0, weight=1)

        # Title
        title_frame = ctk.CTkFrame(content, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w", pady=(0, 20))

        ctk.CTkLabel(
            title_frame,
            text="Customer Management",
            font=("Arial", 18, "bold"),
            text_color="#2c3e50"
        ).pack(side="left")

        # Search and filter section
        search_filter_frame = ctk.CTkFrame(content, fg_color="transparent")
        search_filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        search_filter_frame.grid_columnconfigure(0, weight=1)
        search_filter_frame.grid_columnconfigure(1, weight=0)

        # Search entry
        self.search_entry = ctk.CTkEntry(
            search_filter_frame,
            placeholder_text="Search customers...",
            width=300
        )
        self.search_entry.grid(row=0, column=0, sticky="w")
        self.search_entry.bind("<KeyRelease>", self.search_customers)

        # Add customer button
        ctk.CTkButton(
            search_filter_frame,
            text="+ Add Customer",
            fg_color="#3b82f6",
            command=self.open_add_customer_dialog,
            width=120
        ).grid(row=0, column=1, padx=(10, 0))

        # Filter buttons
        filter_frame = ctk.CTkFrame(content, fg_color="transparent")
        filter_frame.grid(row=2, column=0, sticky="w", pady=(0, 20))

        self.active_filter = tk.StringVar(value="all")

        ctk.CTkButton(
            filter_frame,
            text="All",
            fg_color="#3b82f6" if self.active_filter.get() == "all" else "#e2e8f0",
            text_color="white" if self.active_filter.get() == "all" else "#2c3e50",
            command=lambda: self.filter_customers("all"),
            width=80,
            height=30
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            filter_frame,
            text="Active",
            fg_color="#3b82f6" if self.active_filter.get() == "active" else "#e2e8f0",
            text_color="white" if self.active_filter.get() == "active" else "#2c3e50",
            command=lambda: self.filter_customers("active"),
            width=80,
            height=30
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            filter_frame,
            text="Inactive",
            fg_color="#3b82f6" if self.active_filter.get() == "inactive" else "#e2e8f0",
            text_color="white" if self.active_filter.get() == "inactive" else "#2c3e50",
            command=lambda: self.filter_customers("inactive"),
            width=80,
            height=30
        ).pack(side="left", padx=5)

        # Create Treeview with scrollbars
        tree_frame = ctk.CTkFrame(content, fg_color="white", corner_radius=10)
        tree_frame.grid(row=3, column=0, sticky="nsew", pady=(0, 20))
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        # Create a style for the Treeview
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background="#ffffff",
                        foreground="black",
                        rowheight=35,
                        fieldbackground="#ffffff",
                        borderwidth=0)
        style.map('Treeview', background=[('selected', '#3b82f6')])

        style.configure("Treeview.Heading",
                        background="#f1f5f9",
                        foreground="#64748b",
                        font=('Arial', 12, 'bold'),
                        padding=5,
                        borderwidth=0)

        # Create Treeview widget
        self.tree = ttk.Treeview(
            tree_frame,
            columns=("ID", "Name", "Email", "Phone", "Status"),
            show="headings",
            selectmode="browse",
            style="Treeview"
        )

        # Configure columns
        self.tree.heading("ID", text="ID", anchor="w")
        self.tree.heading("Name", text="Name", anchor="w")
        self.tree.heading("Email", text="Email", anchor="w")
        self.tree.heading("Phone", text="Phone", anchor="w")
        self.tree.heading("Status", text="Status", anchor="center")

        self.tree.column("ID", width=80, anchor="w")
        self.tree.column("Name", width=150, anchor="w")
        self.tree.column("Email", width=200, anchor="w")
        self.tree.column("Phone", width=120, anchor="w")
        self.tree.column("Status", width=100, anchor="center")

        # Configure tags for status badges
        self.tree.tag_configure('active_badge', background='#10b981', foreground='white')
        self.tree.tag_configure('inactive_badge', background='#6b7280', foreground='white')

        # Add scrollbars
        y_scroll = ctk.CTkScrollbar(tree_frame, orientation="vertical", command=self.tree.yview)
        x_scroll = ctk.CTkScrollbar(tree_frame, orientation="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        # Action buttons frame
        action_frame = ctk.CTkFrame(content, fg_color="transparent")
        action_frame.grid(row=4, column=0, sticky="e", pady=(0, 20))

        # Edit button
        edit_btn = ctk.CTkButton(
            action_frame,
            text="Edit Selected",
            fg_color="#3b82f6",
            command=self.edit_selected_customer,
            width=120
        )
        edit_btn.pack(side="left", padx=5)

        # Delete button
        delete_btn = ctk.CTkButton(
            action_frame,
            text="Delete Selected",
            fg_color="#ef4444",
            command=self.delete_selected_customer,
            width=120
        )
        delete_btn.pack(side="left", padx=5)

        # Bind double-click to edit
        self.tree.bind("<Double-1>", lambda e: self.edit_selected_customer())

    def populate_table(self, customers):
        """Populate the Treeview with customer data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not customers:
            return

        # Add customer data
        for customer in customers:
            item_id = self.tree.insert("", "end", values=(
                customer['customer_id'],
                customer['full_name'],
                customer['email'],
                customer['phone'],
                customer['status']
            ))

            # Apply tag based on status
            if customer['status'] == 'Active':
                self.tree.item(item_id, tags=('active_badge',))
            else:
                self.tree.item(item_id, tags=('inactive_badge',))

    def get_selected_customer(self):
        """Get the currently selected customer"""
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a customer first")
            return None

        item_data = self.tree.item(selected_item)
        return {
            'customer_id': item_data['values'][0],
            'full_name': item_data['values'][1],
            'email': item_data['values'][2],
            'phone': item_data['values'][3],
            'status': item_data['values'][4]
        }

    def edit_selected_customer(self):
        """Edit the selected customer"""
        customer = self.get_selected_customer()
        if customer:
            self.edit_customer(customer)

    def delete_selected_customer(self):
        """Delete the selected customer"""
        customer = self.get_selected_customer()
        if customer:
            self.delete_customer(customer)

    def filter_customers(self, status):
        """Filter customers by status"""
        self.active_filter.set(status)
        try:
            customers = self.db.get_customers(status)
            self.populate_table(customers)
        except Exception as e:
            logger.error(f"Error filtering customers: {e}")
            messagebox.showerror("Error", "Failed to filter customers")

    def search_customers(self, event):
        """Search customers based on input"""
        query = self.search_entry.get().strip()

        if not query:
            self.filter_customers(self.active_filter.get())
            return

        try:
            customers = self.db.search_customers(query)
            self.populate_table(customers)
        except Exception as e:
            logger.error(f"Error searching customers: {e}")
            messagebox.showerror("Error", "Failed to search customers")

    def open_add_customer_dialog(self):
        """Open dialog to add new customer"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add New Customer")
        dialog.geometry("500x650")
        dialog.grab_set()

        # Form fields
        customer_id = self.generate_customer_id()
        fields = [
            ("ID Number", "text_disabled", customer_id),
            ("Name", "text", ""),
            ("Email", "text", ""),
            ("Address", "text", ""),
            ("Phone", "text", ""),
            ("Status", "combobox", "Active")
        ]

        self.setup_customer_form(dialog, fields, self.add_customer, "Add Customer")

    def generate_customer_id(self):
        """Generate a new customer ID like CUST0001"""
        try:
            with self.db.connection.cursor() as cursor:
                cursor.execute("SELECT MAX(CAST(SUBSTRING(customer_id, 5) AS UNSIGNED)) FROM customers")
                result = cursor.fetchone()
                max_id = result[0] if result and result[0] is not None else 0
                return f"CUST{max_id + 1:04d}"
        except Exception as e:
            import time
            logger.error(f"Error generating customer ID: {str(e)}")
            return f"CUST{int(time.time())}"
 

    def edit_customer(self, customer):
        """Open dialog to edit existing customer"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Customer")
        dialog.geometry("500x500")
        dialog.grab_set()

        # Form fields with existing data
        fields = [
            ("ID Number", "text_disabled", customer['customer_id']),
            ("Name", "text", customer['full_name']),
            ("Email", "text", customer['email']),
            ("Phone", "text", customer['phone']),
            ("Status", "combobox", customer['status'])
        ]

        self.setup_customer_form(dialog, fields,
                                 lambda entries, dlg: self.update_customer(customer['customer_id'], entries, dlg),
                                 "Update Customer")

    def setup_customer_form(self, dialog, fields, submit_action, submit_text):
        """Helper method to setup customer form"""
        entries = {}

        for label, field_type, default_value in fields:
            frame = ctk.CTkFrame(dialog, fg_color="transparent")
            frame.pack(fill="x", padx=20, pady=10)

            ctk.CTkLabel(frame, text=label).pack(anchor="w")

            if field_type == "text":
                entry = ctk.CTkEntry(frame)
                if default_value:
                    entry.insert(0, default_value)
                entry.pack(fill="x")
                entries[label] = entry
            elif field_type == "text_disabled":
                entry = ctk.CTkEntry(frame)
                if default_value:
                    entry.insert(0, default_value)
                entry.configure(state="disabled")
                entry.pack(fill="x")
                entries[label] = entry
            elif field_type == "combobox":
                combo = ctk.CTkComboBox(frame, values=["Active", "Inactive"])
                combo.set(default_value)
                combo.pack(fill="x")
                entries[label] = combo

        # Submit button
        submit_btn = ctk.CTkButton(
            dialog,
            text=submit_text,
            command=lambda: submit_action(entries, dialog)
        )
        submit_btn.pack(pady=20)

    def add_customer(self, entries, dialog):
        """Add new customer to database"""
        customer_data = {
            'customer_id': entries["ID Number"].get(),
            'full_name': entries["Name"].get(),
            'email': entries["Email"].get(),
            'address': entries["Address"].get(), 
            'phone': entries["Phone"].get(),
            'status': entries["Status"].get()
        }

        if not all(customer_data.values()):
            messagebox.showerror("Error", "Please fill in all fields")
            return

        try:
            if self.db.add_customer(customer_data):
                messagebox.showinfo("Success", "Customer added successfully!")
                self.filter_customers(self.active_filter.get())
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to add customer")
        except Exception as e:
            logger.error(f"Error adding customer: {e}")
            messagebox.showerror("Error", "Failed to add customer")

    def update_customer(self, customer_id, entries, dialog):
        """Update existing customer in database"""
        updated_data = {
            'full_name': entries["Name"].get(),
            'email': entries["Email"].get(),
            'phone': entries["Phone"].get(),
            'status': entries["Status"].get()
        }

        if not all(updated_data.values()):
            messagebox.showerror("Error", "Please fill in all fields")
            return

        try:
            if self.db.update_customer(customer_id, updated_data):
                messagebox.showinfo("Success", "Customer updated successfully!")
                self.filter_customers(self.active_filter.get())
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to update customer")
        except Exception as e:
            logger.error(f"Error updating customer: {e}")
            messagebox.showerror("Error", "Failed to update customer")

    def delete_customer(self, customer):
        """Delete customer from database"""
        if messagebox.askyesno("Confirm", f"Delete customer {customer['full_name']}?"):
            try:
                if self.db.delete_customer(customer['customer_id']):
                    messagebox.showinfo("Success", "Customer deleted")
                    self.filter_customers(self.active_filter.get())
                else:
                    messagebox.showerror("Error", "Failed to delete customer")
            except Exception as e:
                logger.error(f"Error deleting customer: {e}")
                messagebox.showerror("Error", "Failed to delete customer")

    def update_user_display(self, user_data):
        """Update the display with user information"""
        self.current_user = user_data

    def __del__(self):
        """Clean up resources"""
        if hasattr(self, 'db'):
            try:
                self.db.close()
            except:
                pass