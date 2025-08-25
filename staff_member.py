import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
from db_helper import DatabaseManager
import re


class StaffMemberScreen(ctk.CTkFrame):
    def __init__(self, parent, controller, db=None):
        super().__init__(parent)
        self.controller = controller
        self.db = db if db is not None else controller.db

        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Create components
        self.create_sidebar()
        self.create_main_content()

        # Load initial data
        self.filter_staff("all")

    def create_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=250, fg_color="#f0f9ff", corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew")

        # Navigation items
        nav_items = [
            ("Dashboard", "📊", "HotelBookingDashboard"),
            ("Reservations", "🛒", "HotelReservationsPage"),
            ("Customers", "👥", "CustomerManagementScreen"),
            ("Reports", "📄", "HotelReportsPage"),
            ("Staff Members", "👨‍💼", "StaffMemberScreen"),
        ]

        # Add padding
        padding = ctk.CTkLabel(sidebar, text="", fg_color="transparent")
        padding.pack(pady=(20, 10))

        # Add navigation buttons
        for item, icon, frame_name in nav_items:
            is_active = frame_name == "StaffMemberScreen"
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
        """Create the main content area with staff member management"""
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

        # ===== SCROLLABLE CONTENT AREA =====
        content = ctk.CTkScrollableFrame(main, fg_color="#f8fafc")
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        content.grid_columnconfigure(0, weight=1)

        # Search and filter section
        search_filter_frame = ctk.CTkFrame(content, fg_color="transparent")
        search_filter_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        search_filter_frame.grid_columnconfigure(0, weight=1)
        search_filter_frame.grid_columnconfigure(1, weight=0)

        # Search entry
        self.search_entry = ctk.CTkEntry(
            search_filter_frame,
            placeholder_text="Search staff members...",
            width=300
        )
        self.search_entry.grid(row=0, column=0, sticky="w")
        self.search_entry.bind("<KeyRelease>", self.search_staff)

        # Add staff button
        ctk.CTkButton(
            search_filter_frame,
            text="+ Add Staff Member",
            fg_color="#3b82f6",
            command=self.open_add_staff_dialog,
            width=160
        ).grid(row=0, column=1, padx=(10, 0))

        # Filter buttons
        filter_frame = ctk.CTkFrame(content, fg_color="transparent")
        filter_frame.grid(row=1, column=0, sticky="w", pady=(0, 20))

        self.active_filter = tk.StringVar(value="all")

        ctk.CTkButton(
            filter_frame,
            text="All",
            fg_color="#3b82f6" if self.active_filter.get() == "all" else "#e2e8f0",
            text_color="white" if self.active_filter.get() == "all" else "#2c3e50",
            command=lambda: self.filter_staff("all"),
            width=80,
            height=30
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            filter_frame,
            text="Active",
            fg_color="#3b82f6" if self.active_filter.get() == "active" else "#e2e8f0",
            text_color="white" if self.active_filter.get() == "active" else "#2c3e50",
            command=lambda: self.filter_staff("active"),
            width=80,
            height=30
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            filter_frame,
            text="Inactive",
            fg_color="#3b82f6" if self.active_filter.get() == "inactive" else "#e2e8f0",
            text_color="white" if self.active_filter.get() == "inactive" else "#2c3e50",
            command=lambda: self.filter_staff("inactive"),
            width=80,
            height=30
        ).pack(side="left", padx=5)

        # Create Treeview Frame
        self.tree_frame = ctk.CTkFrame(content, fg_color="white", corner_radius=10)
        self.tree_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 20))
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)

        # Create Treeview
        self.tree = ttk.Treeview(
            self.tree_frame,
            columns=("staff_id", "name", "email", "phone", "address", "status"),
            show="headings",
            selectmode="browse",
            style="Custom.Treeview"
        )

        # Configure Treeview style
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Custom.Treeview",
                        background="white",
                        foreground="#334155",
                        rowheight=40,
                        fieldbackground="white",
                        bordercolor="#e2e8f0",
                        borderwidth=1)
        style.configure("Custom.Treeview.Heading",
                        background="#f1f5f9",
                        foreground="#64748b",
                        font=('Arial', 12, 'bold'),
                        padding=(10, 5),
                        relief="flat")
        style.map("Custom.Treeview",
                  background=[('selected', '#dbeafe')],
                  foreground=[('selected', '#1e40af')])

        # Define columns
        self.tree.heading("staff_id", text="Staff ID", anchor="w")
        self.tree.heading("name", text="Name", anchor="w")
        self.tree.heading("email", text="Email", anchor="w")
        self.tree.heading("phone", text="Phone", anchor="w")
        self.tree.heading("address", text="Address", anchor="w")
        self.tree.heading("status", text="Status", anchor="w")

        # Configure column widths
        self.tree.column("staff_id", width=120, anchor="w")
        self.tree.column("name", width=180, anchor="w")
        self.tree.column("email", width=200, anchor="w")
        self.tree.column("phone", width=120, anchor="w")
        self.tree.column("address", width=200, anchor="w")
        self.tree.column("status", width=100, anchor="w")

        # Add scrollbars
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Grid the treeview and scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Create action buttons frame
        self.action_frame = ctk.CTkFrame(content, fg_color="transparent")
        self.action_frame.grid(row=3, column=0, sticky="e", pady=(0, 20))

        # Edit button (will be enabled when a row is selected)
        self.edit_btn = ctk.CTkButton(
            self.action_frame,
            text="Edit",
            fg_color="#3b82f6",
            text_color="white",
            width=80,
            height=30,
            state="disabled",
            command=self.edit_selected_staff
        )
        self.edit_btn.pack(side="left", padx=5)

        # Delete button (will be enabled when a row is selected)
        self.delete_btn = ctk.CTkButton(
            self.action_frame,
            text="Delete",
            fg_color="#ef4444",
            text_color="white",
            width=80,
            height=30,
            state="disabled",
            command=self.delete_selected_staff
        )
        self.delete_btn.pack(side="left", padx=5)

        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def populate_table(self, staff_members):
        """Populate the treeview with staff member data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not staff_members:
            return

        # Add staff members to treeview
        for staff in staff_members:
            status = staff['status']
            tags = ('active',) if status == 'Active' else ('inactive',)

            self.tree.insert("", "end",
                             values=(
                                 staff['staff_id'],
                                 staff['full_name'],
                                 staff['email'],
                                 staff['phone'],
                                 staff['address'],
                                 status
                             ),
                             tags=tags)

        # Configure tag colors
        self.tree.tag_configure('active', background='#f0fdf4', foreground='#166534')
        self.tree.tag_configure('inactive', background='#fef2f2', foreground='#991b1b')

    def on_tree_select(self, event):
        """Handle treeview selection event"""
        selected = self.tree.selection()
        if selected:
            self.edit_btn.configure(state="normal")
            self.delete_btn.configure(state="normal")
        else:
            self.edit_btn.configure(state="disabled")
            self.delete_btn.configure(state="disabled")

    def get_selected_staff(self):
        """Get the currently selected staff member"""
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0], 'values')
            return {
                'staff_id': values[0],
                'full_name': values[1],
                'email': values[2],
                'phone': values[3],
                'address': values[4],
                'status': values[5]
            }
        return None

    def edit_selected_staff(self):
        """Edit the selected staff member"""
        staff = self.get_selected_staff()
        if staff:
            self.edit_staff(staff)

    def delete_selected_staff(self):
        """Delete the selected staff member"""
        staff = self.get_selected_staff()
        if staff:
            self.delete_staff(staff)

    def filter_staff(self, status):
        """Filter staff members by status"""
        self.active_filter.set(status)
        staff_members = self.db.get_staff_members(status)
        self.populate_table(staff_members)
        # Clear selection
        self.tree.selection_remove(self.tree.selection())

    def search_staff(self, event):
        """Search staff members based on input"""
        query = self.search_entry.get().strip()

        if not query:
            self.filter_staff(self.active_filter.get())
            return

        staff_members = self.db.search_staff_members(query)
        self.populate_table(staff_members)
        # Clear selection
        self.tree.selection_remove(self.tree.selection())

    def open_add_staff_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add New Staff Member")
        dialog.geometry("500x600")
        dialog.grab_set()

        # === Scrollable frame setup ===
        outer_frame = ctk.CTkFrame(dialog)
        outer_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(outer_frame, highlightthickness=0, bg="#ffffff")
        scrollbar = ctk.CTkScrollbar(outer_frame, orientation="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Scrollable content frame
        form_frame = ctk.CTkFrame(canvas)
        form_window = canvas.create_window((0, 0), window=form_frame, anchor="nw")

        # Update scrollregion when the frame resizes
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        form_frame.bind("<Configure>", on_frame_configure)

        # Update window width when the dialog resizes
        def on_canvas_configure(event):
            canvas.itemconfig(form_window, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)

        # Optional: enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # === Build form fields ===
        self.staff_form_vars = {}
        fields = [
            ("Staff ID", "text", ""),
            ("Name", "text", ""),
            ("Email", "text", ""),
            ("Phone", "text", ""),
            ("Address", "text", ""),
            ("Gender", "combobox", "Other", ["Male", "Female", "Other"]),
            ("Status", "combobox", "Active", ["Active", "Inactive"]),
            ("Password", "password", ""),
            ("Confirm Password", "password", "")
        ]

        for label_text, field_type, default, *extra in fields:
            container = ctk.CTkFrame(form_frame, fg_color="transparent")
            container.pack(fill="x", padx=20, pady=8)

            ctk.CTkLabel(container, text=label_text).pack(anchor="w")

            if field_type == "text":
                entry = ctk.CTkEntry(container)
                entry.insert(0, default)
            elif field_type == "password":
                entry = ctk.CTkEntry(container, show="*")
                entry.insert(0, default)
            elif field_type == "combobox":
                entry = ctk.CTkComboBox(container, values=extra[0])
                entry.set(default)
            else:
                continue

            entry.pack(fill="x", pady=4)
            self.staff_form_vars[label_text] = entry

        # === Confirm Button ===
        confirm_btn = ctk.CTkButton(
            form_frame,
            text="Confirm",
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=lambda: self.add_staff(dialog)
        )
        confirm_btn.pack(pady=20)
 


    def edit_staff(self, staff):
        """Open dialog to edit existing staff member"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Staff Member")
        dialog.geometry("500x600")
        dialog.grab_set()

        # Get the staff's gender from the database
        staff_details = self.db.search_staff_members(staff['staff_id'])
        if staff_details and len(staff_details) > 0:
            gender = staff_details[0].get('gender', 'Other')
        else:
            gender = 'Other'

        # Form fields with existing data
        fields = [
            ("Staff ID", "text_disabled", staff['staff_id']),
            ("Name", "text", staff['full_name']),
            ("Email", "text", staff['email']),
            ("Phone", "text", staff['phone']),
            ("Address", "text", staff['address']),
            ("Gender", "combobox", gender, ["Male", "Female", "Other"]),
            ("Status", "combobox", staff['status'], ["Active", "Inactive"]),
            ("Password", "password", ""),  # Empty for new password
            ("Confirm Password", "password", "")
        ]

        self.setup_staff_form(dialog, fields,
                              lambda entries, dlg: self.update_staff(staff['staff_id'], entries, dlg),
                              "Update Staff Member")

    def setup_staff_form(self, dialog, fields, submit_action, submit_text):
        """Helper method to setup staff member form"""
        entries = {}

        for label, field_type, default_value, *options in fields:
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
            elif field_type == "password":
                entry = ctk.CTkEntry(frame, show="•")
                if default_value:
                    entry.insert(0, default_value)
                entry.pack(fill="x")
                entries[label] = entry
            elif field_type == "combobox":
                combo = ctk.CTkComboBox(frame, values=options[0] if options else ["Active", "Inactive"])
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

    def add_staff(self, dialog):
        """Add new staff member to database"""
        staff_data = {
            'staff_id': self.staff_form_vars["Staff ID"].get(),
            'full_name': self.staff_form_vars["Name"].get(),
            'email': self.staff_form_vars["Email"].get().lower(),
            'phone': self.staff_form_vars["Phone"].get(),
            'address': self.staff_form_vars["Address"].get(),
            'gender': self.staff_form_vars["Gender"].get(),
            'status': self.staff_form_vars["Status"].get(),
            'password': self.staff_form_vars["Password"].get(),
            'confirm_password': self.staff_form_vars["Confirm Password"].get()
        }

        # Validate required fields
        required_fields = ['staff_id', 'full_name', 'email', 'password', 'confirm_password']
        if not all(staff_data[field] for field in required_fields):
            messagebox.showerror("Error", "All required fields must be filled")
            return

        # Validate password match
        if staff_data['password'] != staff_data['confirm_password']:
            messagebox.showerror("Error", "Passwords do not match")
            return

        # Validate password length
        if len(staff_data['password']) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters")
            return

        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", staff_data['email']):
            messagebox.showerror("Error", "Please enter a valid email address")
            return

        try:
            success, message = self.db.add_staff_member(staff_data)
            if success:
                messagebox.showinfo("Success", message)
                self.filter_staff(self.active_filter.get())
                dialog.destroy()
            else:
                messagebox.showerror("Error", message)
        except Exception as e:
            messagebox.showerror("Database Error", f"An error occurred: {str(e)}")

    def update_staff(self, staff_id, entries, dialog):
        """Update existing staff member in database"""
        updated_data = {
            'full_name': entries["Name"].get(),
            'email': entries["Email"].get().lower(),
            'phone': entries["Phone"].get(),
            'address': entries["Address"].get(),
            'gender': entries["Gender"].get(),
            'status': entries["Status"].get()
        }

        # Only update password if changed (not empty)
        password = entries["Password"].get()
        confirm_password = entries["Confirm Password"].get()

        if password:  # Only update if password field is not empty
            if password != confirm_password:
                messagebox.showerror("Error", "Passwords do not match")
                return
            if len(password) < 8:
                messagebox.showerror("Error", "Password must be at least 8 characters")
                return
            updated_data['password'] = password

        # Validate required fields
        required_fields = ['full_name', 'email']
        if not all(updated_data[field] for field in required_fields):
            messagebox.showerror("Error", "Please fill in all required fields")
            return

        try:
            if self.db.update_staff_member(staff_id, updated_data):
                messagebox.showinfo("Success", "Staff member updated successfully!")
                self.filter_staff(self.active_filter.get())
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to update staff member")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update staff member: {str(e)}")

    def delete_staff(self, staff):
        """Delete staff member from database"""
        if messagebox.askyesno("Confirm", f"Delete staff member {staff['full_name']}?"):
            if self.db.delete_staff_member(staff['staff_id']):
                messagebox.showinfo("Success", "Staff member deleted")
                self.filter_staff(self.active_filter.get())
            else:
                messagebox.showerror("Error", "Failed to delete staff member")

    def __del__(self):
        """Clean up database connection when frame is destroyed"""
        if hasattr(self, 'db'):
            self.db.close()