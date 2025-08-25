import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageTk, ImageFilter
import os


class HotelBookingSystem(ctk.CTkFrame):
    def __init__(self, parent, controller, db=None):  # Added db parameter
        super().__init__(parent)
        self.controller = controller
        self.db = db  # Store the database connection/object

        # Configure window with yellow tinge background
        self.configure(fg_color="#fff8dc")

        # Load the hotel lobby image
        try:
            # Get the directory of the current script
            current_dir = os.path.dirname(os.path.abspath(__file__))

            # Path to the hotel lobby image - adjust filename as needed
            image_path = os.path.join(current_dir, "hotel_lobby.jpg")

            # Load and resize the image
            self.bg_image = Image.open(image_path)
            self.bg_image = self.bg_image.resize((2000, 1000), Image.Resampling.LANCZOS)

            # Apply blur effect to the image
            self.blurred_image = self.bg_image.filter(ImageFilter.GaussianBlur(radius=5))

            # Use CTkImage instead of ImageTk.PhotoImage for better high DPI support
            self.bg_photo = ctk.CTkImage(light_image=self.blurred_image,
                                         dark_image=self.blurred_image,
                                         size=(2000, 1000))

            # Create a label to display the background image
            self.bg_label = ctk.CTkLabel(self, image=self.bg_photo, text="")
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        except Exception as e:
            print(f"Error loading image: {e}")
            # Use a light yellow background if image fails to load
            self.configure(fg_color="#fff8dc")

        # Create top header frame with transparent background
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent", height=40, corner_radius=0)
        self.header_frame.pack(fill="x", pady=(0, 0))
        self.header_frame.pack_propagate(False)

        # Title on left
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="Hotel Booking and Management System",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="blue"
        )
        self.title_label.pack(side="left", padx=20, pady=10)

        # Sign-in button on right
        self.signin_button = ctk.CTkButton(
            self.header_frame,
            text="Sign-in",
            width=80,
            height=28,
            corner_radius=5,
            command=lambda: self.show_login_as("customer")  # Updated to use new method
        )
        self.signin_button.pack(side="right", padx=20, pady=5)

        # Create center content frame with yellow background
        self.content_frame = ctk.CTkFrame(
            self,
            fg_color="#fffacd",
            corner_radius=10,
            width=850,
            height=300
        )
        self.content_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.content_frame.pack_propagate(False)

        # Add title to content frame
        self.system_title_label = ctk.CTkLabel(
            self.content_frame,
            text="HOTEL BOOKING\nMANAGEMENT\nSYSTEM",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="blue"
        )
        self.system_title_label.place(relx=0.5, rely=0.3, anchor="center")

        # Add welcome label
        self.welcome_label = ctk.CTkLabel(
            self.content_frame,
            text="Welcome! Get started as:",
            font=ctk.CTkFont(size=16),
            text_color="#333333"
        )
        self.welcome_label.place(relx=0.5, rely=0.55, anchor="center")

        # Add three buttons for Admin, Customer, and Staff
        # Admin button
        self.admin_button = ctk.CTkButton(
            self.content_frame,
            text="Admin",
            font=ctk.CTkFont(size=14),
            fg_color="#1e3a8a",
            hover_color="#2563eb",
            corner_radius=5,
            width=120,
            height=35,
            command=lambda: self.show_login_as("admin")  # Updated command
        )
        self.admin_button.place(relx=0.25, rely=0.75, anchor="center")

        # Customer button
        self.customer_button = ctk.CTkButton(
            self.content_frame,
            text="Customer",
            font=ctk.CTkFont(size=14),
            fg_color="#166534",
            hover_color="#22c55e",
            corner_radius=5,
            width=120,
            height=35,
            command=lambda: self.show_login_as("customer")  # Updated command
        )
        self.customer_button.place(relx=0.5, rely=0.75, anchor="center")

        # Staff button
        self.staff_button = ctk.CTkButton(
            self.content_frame,
            text="Staff",
            font=ctk.CTkFont(size=14),
            fg_color="#7c2d12",
            hover_color="#ea580c",
            corner_radius=5,
            width=120,
            height=35,
            command=lambda: self.show_login_as("staff")  # Updated command
        )
        self.staff_button.place(relx=0.75, rely=0.75, anchor="center")

    def show_login_as(self, user_type):
        """Show login page with specified user type"""
        login_frame = self.controller.frames["LoginApp"]
        login_frame.set_user_type(user_type)
        self.controller.show_frame("LoginApp")