import customtkinter as ctk
from PIL import Image, ImageTk, ImageFilter
import tkinter.messagebox as messagebox
import hashlib
import re


class LoginApp(ctk.CTkFrame):
    def __init__(self, parent, controller, db=None):
        super().__init__(parent)
        self.controller = controller
        self.db = db
        self.user_type = "customer"  # Default to customer

        # Configure window
        self.configure(fg_color="#f0f8ff")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Background Image
        try:
            bg_image = Image.open("Welcome.jpg")
            bg_image = bg_image.resize((1920, 1080), Image.LANCZOS)
            blurred_bg_image = bg_image.filter(ImageFilter.GaussianBlur(radius=5))
            # Use CTkImage instead of ImageTk.PhotoImage for better high DPI support
            self.bg_photo = ctk.CTkImage(light_image=blurred_bg_image,
                                         dark_image=blurred_bg_image,
                                         size=(1920, 1080))
            self.bg_label = ctk.CTkLabel(self, image=self.bg_photo, text="")
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print(f"Background image error: {e}")

        # Main login frame
        self.main_frame = ctk.CTkFrame(self,
                                       corner_radius=5,
                                       fg_color="white",
                                       bg_color="transparent")
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.4, relheight=0.6)

        # Login title
        self.login_title = ctk.CTkLabel(self.main_frame,
                                        text="Welcome Back",
                                        font=("Arial", 32, "bold"),
                                        text_color="#3b82f6")
        self.login_title.pack(pady=(30, 20))

        # Email Entry
        email_frame = ctk.CTkFrame(self.main_frame, fg_color="white")
        email_frame.pack(fill="x", padx=40)

        ctk.CTkLabel(email_frame, text="Email:", font=("Arial", 12, "bold")).pack(anchor="w")
        self.email_entry = ctk.CTkEntry(email_frame,
                                        placeholder_text="Enter your email",
                                        width=300,
                                        height=40,
                                        corner_radius=22,
                                        border_color="#d1d5db",
                                        border_width=1)
        self.email_entry.pack(fill="x", pady=(0, 10))

        # Password Entry
        password_frame = ctk.CTkFrame(self.main_frame, fg_color="white")
        password_frame.pack(fill="x", padx=40)

        ctk.CTkLabel(password_frame, text="Password:", font=("Arial", 12, "bold")).pack(anchor="w")

        self.password_container = ctk.CTkFrame(password_frame, fg_color="white")
        self.password_container.pack(fill="x")

        self.password_entry = ctk.CTkEntry(self.password_container,
                                           placeholder_text="Enter your password",
                                           show="*",
                                           width=300,
                                           height=40,
                                           corner_radius=22,
                                           border_color="#d1d5db",
                                           border_width=1)
        self.password_entry.pack(side="left", expand=True, fill="x")

        self.show_password_btn = ctk.CTkButton(self.password_container,
                                               text="👁",
                                               width=40,
                                               height=40,
                                               fg_color="#f0f0f0",
                                               hover_color="#e0e0e0",
                                               text_color="black",
                                               command=self.toggle_password)
        self.show_password_btn.pack(side="right", padx=(5, 0))

        # Login Button
        self.login_button = ctk.CTkButton(self.main_frame,
                                          text="Login",
                                          width=350,
                                          height=40,
                                          corner_radius=22,
                                          fg_color="#3b82f6",
                                          hover_color="#2563eb",
                                          command=self.attempt_login)
        self.login_button.pack(pady=10)

        # Additional Links
        self.links_frame = ctk.CTkFrame(self.main_frame, fg_color="white")
        self.links_frame.pack(pady=10)

        self.register_link = ctk.CTkLabel(self.links_frame,
                                          text="Don't have an account? Register",
                                          font=("Arial", 10, "bold"),
                                          text_color="#3b82f6",
                                          cursor="hand2")
        # Don't pack the register link here - it will be controlled by set_user_type
        self.register_link.bind("<Button-1>", lambda e: self.controller.show_frame("RegistrationApp"))

        # Back to landing page link
        self.back_link = ctk.CTkLabel(self.main_frame,
                                      text="← Back to Home",
                                      font=("Arial", 10),
                                      text_color="#6b7280",
                                      cursor="hand2")
        self.back_link.pack(pady=(0, 10))
        self.back_link.bind("<Button-1>", lambda e: self.controller.show_frame("HotelBookingSystem"))

        # Footer
        self.footer_label = ctk.CTkLabel(self.main_frame,
                                         text="© 2024 Hotel Management System",
                                         font=("Arial", 8, "bold"),
                                         text_color="#6b7280")
        self.footer_label.pack(pady=(20, 10))

        # Bind Enter key to login
        self.bind('<Return>', lambda event: self.attempt_login())

        # Initialize the user type and UI
        self.set_user_type(self.user_type)

    def set_user_type(self, user_type):
        """Set the user type and adjust UI accordingly"""
        self.user_type = user_type

        # Update login title based on user type
        user_type_display = user_type.capitalize()
        self.login_title.configure(text=f"{user_type_display} Login")

        # Show register link only for customers
        if user_type == "customer":
            self.register_link.pack(pady=5)  # Show register link for customers
        else:
            self.register_link.pack_forget()  # Hide register link for admin and staff

    def toggle_password(self):
        """Toggle password visibility"""
        current_show = self.password_entry.cget("show")
        self.password_entry.configure(show="" if current_show == "*" else "*")
        self.show_password_btn.configure(text="🔒" if current_show == "*" else "👁")

    def attempt_login(self, event=None):
        """Handle login attempt with database verification"""
        email = self.email_entry.get().strip().lower()
        password = self.password_entry.get()

        if not email or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            messagebox.showerror("Error", "Please enter a valid email address")
            return

        try:
            user = self.db.authenticate_user(email, password, self.user_type)
            if user:
                # Verify user type matches the selected login type
                if user.get("role") != self.user_type:
                    messagebox.showerror(
                        "Access Denied",
                        f"Your account is not authorized for {self.user_type} access"
                    )
                    return

                # Additional check for staff - ensure staff record exists
                if self.user_type == "staff" and not user.get("staff_id"):
                    messagebox.showerror(
                        "Account Error",
                        "Staff record not found. Please contact administrator."
                    )
                    return

                # Check if staff account is active
                if self.user_type == "staff" and user.get("status") != "Active":
                    messagebox.showerror(
                        "Account Inactive",
                        "Your staff account is not active. Please contact administrator."
                    )
                    return

                messagebox.showinfo("Success", f"Welcome back, {user['full_name']}!")

                # Navigate to appropriate dashboard
                if self.user_type == "admin":
                    self.controller.successful_login(user, "HotelBookingDashboard")
                elif self.user_type == "staff":
                    self.controller.successful_login(user, "StaffDashboard")
                else:  # customer
                    self.controller.successful_login(user, "CustomerDashboard")

                # Clear fields
                self.email_entry.delete(0, 'end')
                self.password_entry.delete(0, 'end')
            else:
                messagebox.showerror(
                    "Login Failed",
                    "Invalid credentials or account not active.\n"
                    "Please check your email and password."
                )
        except Exception as e:
            messagebox.showerror(
                "System Error",
                f"Login failed due to system error:\n{str(e)}"
            )

    def __del__(self):
        """Clean up resources"""
        pass