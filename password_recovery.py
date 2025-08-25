import customtkinter as ctk
from PIL import Image, ImageTk, ImageFilter
import tkinter.messagebox as messagebox
import re
import hashlib
import logging

logger = logging.getLogger(__name__)


class PasswordRecoveryApp(ctk.CTkFrame):
    def __init__(self, parent, controller, db=None):
        super().__init__(parent)
        self.controller = controller
        self.db = db  # Store the database connection

        self.configure(fg_color="#f0f8ff")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Background Image (Blurred)
        try:
            bg_image = Image.open("password.jpg")
            bg_image = bg_image.resize((1920, 1080), Image.LANCZOS)

            # Apply blur effect
            blurred_bg_image = bg_image.filter(ImageFilter.GaussianBlur(radius=5))

            self.bg_photo = ImageTk.PhotoImage(blurred_bg_image)

            self.bg_label = ctk.CTkLabel(self, image=self.bg_photo, text="")
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print(f"Error loading background image: {e}")

        # Main Password Recovery Frame
        self.main_frame = ctk.CTkFrame(self,
                                       corner_radius=22,
                                       fg_color="white",
                                       bg_color="transparent")
        self.main_frame.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.4, relheight=0.65)

        # Password Recovery Title
        self.recovery_title = ctk.CTkLabel(self.main_frame,
                                           text="Password Recovery",
                                           font=("Arial", 32, "bold"),
                                           text_color="blue")
        self.recovery_title.pack(pady=(30, 15))

        # Email Entry
        email_frame = ctk.CTkFrame(self.main_frame, fg_color="white")
        email_frame.pack(fill="x", padx=40, pady=(0, 10))

        ctk.CTkLabel(email_frame, text="Registered Email:", font=("Arial", 12, "bold"), anchor="w").pack(anchor="w")
        self.email_entry = ctk.CTkEntry(email_frame,
                                        placeholder_text="Enter your registered email",
                                        width=600,
                                        height=40,
                                        corner_radius=22,
                                        border_color="lightblue",
                                        border_width=1)
        self.email_entry.pack(fill="x", pady=(0, 5))

        # New Password Entry with Toggle
        new_password_frame = ctk.CTkFrame(self.main_frame, fg_color="white")
        new_password_frame.pack(fill="x", padx=40, pady=(0, 10))

        ctk.CTkLabel(new_password_frame, text="New Password:", font=("Arial", 12, "bold"), anchor="w").pack(anchor="w")

        self.new_password_container = ctk.CTkFrame(new_password_frame, fg_color="white")
        self.new_password_container.pack(fill="x")

        self.new_password_entry = ctk.CTkEntry(self.new_password_container,
                                               placeholder_text="Enter new password",
                                               width=600,
                                               height=40,
                                               corner_radius=22,
                                               border_color="lightblue",
                                               border_width=1,
                                               show="*")
        self.new_password_entry.pack(side="left", expand=True, fill="x")

        # Show/Hide button for new password
        self.show_new_password_btn = ctk.CTkButton(self.new_password_container,
                                                   text="👁",
                                                   width=40,
                                                   height=40,
                                                   fg_color="#f0f0f0",
                                                   hover_color="#e0e0e0",
                                                   text_color="black",
                                                   command=lambda: self.toggle_password(self.new_password_entry,
                                                                                        self.show_new_password_btn))
        self.show_new_password_btn.pack(side="right", padx=(5, 0))

        # Password Requirements Label
        self.password_reqs_label = ctk.CTkLabel(new_password_frame,
                                                text="• 8+ characters\n• Uppercase & lowercase\n• Number\n• Special character (!@#$)",
                                                font=("Arial", 10),
                                                text_color="gray",
                                                justify="left")
        self.password_reqs_label.pack(anchor="w", pady=(5, 0))

        # Confirm Password Entry with Toggle
        confirm_password_frame = ctk.CTkFrame(self.main_frame, fg_color="white")
        confirm_password_frame.pack(fill="x", padx=40, pady=(0, 15))

        ctk.CTkLabel(confirm_password_frame, text="Confirm Password:", font=("Arial", 12, "bold"), anchor="w").pack(
            anchor="w")

        self.confirm_password_container = ctk.CTkFrame(confirm_password_frame, fg_color="white")
        self.confirm_password_container.pack(fill="x")

        self.confirm_password_entry = ctk.CTkEntry(self.confirm_password_container,
                                                   placeholder_text="Confirm new password",
                                                   width=600,
                                                   height=40,
                                                   corner_radius=22,
                                                   border_color="lightblue",
                                                   border_width=1,
                                                   show="*")
        self.confirm_password_entry.pack(side="left", expand=True, fill="x")

        # Show/Hide button for confirm password
        self.show_confirm_password_btn = ctk.CTkButton(self.confirm_password_container,
                                                       text="👁",
                                                       width=40,
                                                       height=40,
                                                       fg_color="#f0f0f0",
                                                       hover_color="#e0e0e0",
                                                       text_color="black",
                                                       command=lambda: self.toggle_password(self.confirm_password_entry,
                                                                                            self.show_confirm_password_btn))
        self.show_confirm_password_btn.pack(side="right", padx=(5, 0))

        # Continue Button
        self.continue_button = ctk.CTkButton(self.main_frame,
                                             text="Reset Password",
                                             width=350,
                                             height=40,
                                             corner_radius=22,
                                             fg_color="blue",
                                             hover_color="darkblue",
                                             command=self.reset_password)
        self.continue_button.pack(pady=(15, 10))

        # Back to Login Link
        self.back_to_login_link = ctk.CTkLabel(self.main_frame,
                                               text="← Back to Login",
                                               font=("Arial", 10, "bold"),
                                               text_color="blue",
                                               cursor="hand2")
        self.back_to_login_link.pack(pady=(5, 0))
        self.back_to_login_link.bind("<Button-1>", lambda e: self.controller.show_frame("LoginApp"))

    def toggle_password(self, entry, button):
        """Toggle password visibility with visual feedback"""
        if entry.cget("show") == "*":
            entry.configure(show="")
            button.configure(text="🔒")
        else:
            entry.configure(show="*")
            button.configure(text="👁")

    def reset_password(self):
        email = self.email_entry.get().strip()
        new_password = self.new_password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        # Validate email format
        if not self.validate_email(email):
            messagebox.showerror("Error", "Please enter a valid email address")
            self.email_entry.configure(border_color="red")
            return
        else:
            self.email_entry.configure(border_color="lightblue")

        # Validate password
        if not self.validate_password(new_password):
            messagebox.showerror("Error",
                                 "Password must:\n• Be 8+ characters\n• Contain uppercase & lowercase\n• Contain a number\n• Contain a special character (!@#$)")
            self.new_password_entry.configure(border_color="red")
            return
        else:
            self.new_password_entry.configure(border_color="lightblue")

        # Check if passwords match
        if new_password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match")
            self.confirm_password_entry.configure(border_color="red")
            return
        else:
            self.confirm_password_entry.configure(border_color="lightblue")

        # Update password in database
        try:
            if not self.db or not self.db.connection.is_connected():
                messagebox.showerror("Error", "Database connection error")
                return

            # Hash the new password
            hashed_password = hashlib.sha256(new_password.encode()).hexdigest()

            with self.db.connection.cursor() as cursor:
                # Check if email exists
                cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()

                if not user:
                    messagebox.showerror("Error", "Email not found in our system")
                    return

                # Update password
                cursor.execute(
                    "UPDATE users SET password_hash = %s WHERE email = %s",
                    (hashed_password, email)
                )
                self.db.connection.commit()

                # messagebox.showinfo("Success", "Password has been reset successfully!")
                self.controller.show_frame("LoginApp")

        except Exception as e:
            logger.error(f"Password reset failed: {e}")
            # messagebox.showerror("Error", f"Password reset failed: {str(e)}")

    def validate_email(self, email):
        """Basic email validation using regex"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def validate_password(self, password):
        """Password validation:
        - At least 8 characters
        - At least one uppercase
        - At least one lowercase
        - At least one digit
        - At least one special character
        """
        if len(password) < 8:
            return False
        if not re.search(r'[A-Z]', password):
            return False
        if not re.search(r'[a-z]', password):
            return False
        if not re.search(r'[0-9]', password):
            return False
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False
        return True