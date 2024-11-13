import tkinter as tk
from tkinter import ttk, messagebox
from paho.mqtt.client import Client as MqttClient
from datetime import datetime
import sqlite3
import RPi.GPIO as GPIO
import time
import hashlib

# ===== Global Configuration =====
# MQTT broker settings for communication
mqtt_broker = "broker.hivemq.com"  # Public MQTT broker
mqtt_port = 1883                   # Default MQTT port
topic_prefix = "parking/slots/"    # Topic prefix for parking slots

# ===== GPIO Configuration =====
GPIO.setwarnings(False)            # Disable GPIO warnings
GPIO.setmode(GPIO.BCM)            # Use Broadcom pin-numbering scheme

# Pin definitions for hardware components
SERVO_PIN = 17                    # GPIO pin for servo motor control
IR_PIN = 4                        # GPIO pin for IR sensor input

# Configure GPIO pins
GPIO.setup(SERVO_PIN, GPIO.OUT)   # Set servo pin as output
GPIO.setup(IR_PIN, GPIO.IN)       # Set IR sensor pin as input

# Initialize servo motor
servo = GPIO.PWM(SERVO_PIN, 50)   # PWM frequency: 50Hz
servo.start(0)                    # Start PWM with 0% duty cycle

class LoginSystem:
    """
    Handles user authentication and database management for the parking system.
    Provides login interface and user registration functionality.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Parking System - Login")
        self.setup_database()
        self.create_login_gui()
        
    def setup_database(self):
        """
        Initializes SQLite database and creates necessary tables.
        Sets up default admin user if not exists.
        """
        self.conn = sqlite3.connect("parking_system.db")
        self.cursor = self.conn.cursor()
        
        # Create users table for authentication
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL
            )
        """)
        
        # Create table for parking records
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS parking_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slot INTEGER,
                entry_time TEXT,
                exit_time TEXT,
                duration TEXT
            )
        """)
        
        # Create default admin account
        default_password = hashlib.sha256("admin123".encode()).hexdigest()
        try:
            self.cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                ("admin", default_password, "admin")
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            # Skip if admin user already exists
            pass

    def create_login_gui(self):
        """
        Creates the login interface with username and password fields.
        Includes options for login and registration.
        """
        # Window configuration
        self.root.configure(bg="#2C3E50")
        window_width = 400
        window_height = 500
        
        # Center window on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Main container frame
        main_frame = tk.Frame(self.root, bg="#2C3E50")
        main_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Application title
        title_label = tk.Label(
            main_frame,
            text="Smart Parking System",
            font=("Helvetica", 24, "bold"),
            fg="#ECF0F1",
            bg="#2C3E50"
        )
        title_label.pack(pady=20)

        # Login form container
        login_frame = tk.Frame(main_frame, bg="#34495E", padx=30, pady=30)
        login_frame.pack()

        # Username field
        username_label = tk.Label(
            login_frame,
            text="Username:",
            font=("Helvetica", 12),
            fg="#ECF0F1",
            bg="#34495E"
        )
        username_label.pack(anchor="w")
        self.username_entry = ttk.Entry(login_frame, width=30)
        self.username_entry.pack(pady=(5, 15))

        # Password field
        password_label = tk.Label(
            login_frame,
            text="Password:",
            font=("Helvetica", 12),
            fg="#ECF0F1",
            bg="#34495E"
        )
        password_label.pack(anchor="w")
        self.password_entry = ttk.Entry(login_frame, show="Ã¢â‚¬Â¢", width=30)
        self.password_entry.pack(pady=(5, 20))

        # Login button
        login_button = tk.Button(
            login_frame,
            text="Login",
            command=self.login,
            font=("Helvetica", 12, "bold"),
            bg="#2ECC71",
            fg="white",
            padx=30,
            pady=10,
            relief="flat"
        )
        login_button.pack(pady=10)

        # Register button
        register_button = tk.Button(
            login_frame,
            text="Register",
            command=self.show_register,
            font=("Helvetica", 12),
            bg="#3498DB",
            fg="white",
            padx=25,
            pady=8,
            relief="flat"
        )
        register_button.pack(pady=10)

    def login(self):
        """
        Handles user login authentication.
        Verifies credentials against database and opens parking management window if successful.
        """
        username = self.username_entry.get()
        # Hash password for security
        password = hashlib.sha256(self.password_entry.get().encode()).hexdigest()
        
        # Check credentials
        self.cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = self.cursor.fetchone()
        
        if user:
            self.root.withdraw()  # Hide login window
            parking_window = tk.Toplevel()
            app = ParkingSlotGUI(parking_window, self)
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def show_register(self):
        """
        Displays the registration window for new user signup.
        """
        register_window = tk.Toplevel(self.root)
        register_window.title("Register New User")
        register_window.configure(bg="#2C3E50")
        
        # Center registration window
        window_width = 400
        window_height = 400
        screen_width = register_window.winfo_screenwidth()
        screen_height = register_window.winfo_screenheight()
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        register_window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Registration form container
        frame = tk.Frame(register_window, bg="#34495E", padx=30, pady=30)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        # Registration form title
        title = tk.Label(
            frame,
            text="Register New User",
            font=("Helvetica", 16, "bold"),
            fg="#ECF0F1",
            bg="#34495E"
        )
        title.pack(pady=20)

        # Username field
        username_label = tk.Label(
            frame,
            text="Username:",
            font=("Helvetica", 12),
            fg="#ECF0F1",
            bg="#34495E"
        )
        username_label.pack(anchor="w")
        username_entry = ttk.Entry(frame, width=30)
        username_entry.pack(pady=(5, 15))

        # Password field
        password_label = tk.Label(
            frame,
            text="Password:",
            font=("Helvetica", 12),
            fg="#ECF0F1",
            bg="#34495E"
        )
        password_label.pack(anchor="w")
        password_entry = ttk.Entry(frame, show="Ã¢â‚¬Â¢", width=30)
        password_entry.pack(pady=(5, 15))

        # Confirm password field
        confirm_label = tk.Label(
            frame,
            text="Confirm Password:",
            font=("Helvetica", 12),
            fg="#ECF0F1",
            bg="#34495E"
        )
        confirm_label.pack(anchor="w")
        confirm_entry = ttk.Entry(frame, show="Ã¢â‚¬Â¢", width=30)
        confirm_entry.pack(pady=(5, 20))

        def register():
            """
            Handles the registration process for new users.
            Validates input and creates new user in database.
            """
            username = username_entry.get()
            password = password_entry.get()
            confirm = confirm_entry.get()

            # Input validation
            if not username or not password or not confirm:
                messagebox.showerror("Error", "All fields are required")
                return

            if password != confirm:
                messagebox.showerror("Error", "Passwords do not match")
                return

            try:
                # Hash password and store user
                hashed_password = hashlib.sha256(password.encode()).hexdigest()
                self.cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    (username, hashed_password, "user")
                )
                self.conn.commit()
                messagebox.showinfo("Success", "Registration successful!")
                register_window.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists")

        # Register button
        register_btn = tk.Button(
            frame,
            text="Register",
            command=register,
            font=("Helvetica", 12, "bold"),
            bg="#2ECC71",
            fg="white",
            padx=30,
            pady=10,
            relief="flat"
        )
        register_btn.pack(pady=20)

class ParkingSlotGUI:
    """
    Main parking management interface.
    Handles parking slot status, timing, and MQTT communication.
    """
    def __init__(self, root, login_system):
        self.root = root
        self.login_system = login_system
        self.root.title("Smart Parking Management System")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Configure main window
        window_width = 1000
        window_height = 600
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.configure(bg="#2C3E50")

        # Initialize tracking dictionaries
        self.slots_labels = {}         # Status labels for each slot
        self.entry_time_labels = {}    # Entry time labels
        self.exit_time_labels = {}     # Exit time labels
        self.duration_labels = {}      # Duration labels
        self.entry_times = {}          # Track entry times
        self.occupancy_status = {}     # Track slot occupancy

        # Setup GUI components
        self.setup_gui()
        
        # Initialize MQTT client
        self.setup_mqtt()
        
        # Start IR sensor monitoring
        self.check_ir_sensor()

    def setup_gui(self):
        """
        Creates the main parking management interface.
        Sets up display for parking slots and their status.
        """
        # Header section
        header_frame = tk.Frame(self.root, bg="#34495E", height=100)
        header_frame.pack(fill="x", pady=(0, 20))
        header_frame.pack_propagate(False)

        # Main title
        title_label = tk.Label(
            header_frame,
            text="Smart Parking Management System",
            font=("Helvetica", 24, "bold"),
            fg="#ECF0F1",
            bg="#34495E"
        )
        title_label.place(relx=0.5, rely=0.5, anchor="center")

        # Logout button
        logout_btn = tk.Button(
            header_frame,
            text="Logout",
            command=self.logout,
            font=("Helvetica", 12),
            bg="#E74C3C",
            fg="white",
            padx=20,
            pady=5,
            relief="flat"
        )
        logout_btn.place(relx=0.95, rely=0.5, anchor="e")

        # Main content area
        content_frame = tk.Frame(self.root, bg="#2C3E50")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Create parking slot displays
        for slot_num in range(1, 3):
            # Slot container
            slot_frame = tk.Frame(
                content_frame,
                bg="#34495E",
                padx=30,
                pady=20,
                relief="raised",
                bd=1
            )
            slot_frame.pack(fill="x", pady=10)

            # Slot number header
            slot_label = tk.Label(
                slot_frame,
                text=f"Parking Slot {slot_num}",
                font=("Helvetica", 18, "bold"),
                fg="#ECF0F1",
                bg="#34495E"
            )
            slot_label.pack()

            # Status indicator
            status_label = tk.Label(
                slot_frame,
                text="Status: Empty",
                font=("Helvetica", 14),
                fg="#2ECC71",
                bg="#34495E"
            )
            status_label.pack(pady=10)
            self.slots_labels[slot_num] = status_label

            # Time information container
            time_frame = tk.Frame(slot_frame, bg="#34495E")
            time_frame.pack(fill="x", pady=5)

            # Entry time display
            entry_time_label = tk.Label(
                time_frame,
                text="Entry: N/A",
                font=("Helvetica", 12),
                fg="#ECF0F1",
                bg="#34495E"
            )
            entry_time_label.pack(pady=5)
            self.entry_time_labels[slot_num] = entry_time_label

            # Exit time display
            exit_time_label = tk.Label(
                time_frame,
                text="Exit: N/A",
                font=("Helvetica", 12),
                fg="#ECF0F1",
                bg="#34495E"
            )
            exit_time_label.pack(pady=5)
            self.exit_time_labels[slot_num] = exit_time_label

            # Duration display
            duration_label = tk.Label(
                time_frame,
                text="Duration: 0 min 0 sec",
                font=("Helvetica", 12),
                fg="#ECF0F1",
                bg="#34495E"
            )
            duration_label.pack(pady=5)
            self.duration_labels[slot_num] = duration_label

            # Initialize tracking variables
            self.entry_times[slot_num] = None
            self.occupancy_status[slot_num] = "Empty"

    def check_ir_sensor(self):
        """
        Monitors IR sensor status and controls gate accordingly.
        Runs every 100ms.
        """
        if GPIO.input(IR_PIN):
            self.open_gate()
        else:
            self.close_gate()
        self.root.after(100, self.check_ir_sensor)

    def open_gate(self):
        """Controls servo to open the parking gate"""
        servo.ChangeDutyCycle(7)  # 90-degree position
        time.sleep(1)
        servo.ChangeDutyCycle(0)  # Stop servo jitter

    def close_gate(self):
        """Controls servo to close the parking gate"""
        servo.ChangeDutyCycle(2.5)  # 0-degree position
        time.sleep(1)
        servo.ChangeDutyCycle(0)  # Stop servo jitter

    def logout(self):
        """Handles user logout and returns to login screen"""
        self.root.destroy()
        self.login_system.root.deiconify()

    def on_closing(self):
        """Cleanup on window close"""
        self.root.destroy()
        self.login_system.root.destroy()

    def setup_mqtt(self):
        """
        Initializes MQTT client and connects to broker.
        Sets up message handling for parking slot status updates.
        """
        self.mqtt_client = MqttClient()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect(mqtt_broker, mqtt_port, 60)
        self.mqtt_client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        """Callback for when MQTT client connects to broker"""
        client.subscribe(topic_prefix + "#")

    def on_message(self, client, userdata, message):
        """
        Handles incoming MQTT messages.
        Updates parking slot status and timing information.
        """
        try:
            topic = message.topic
            payload = message.payload.decode()
            slot_num = int(topic.split('/')[-1])

            if slot_num in self.slots_labels and payload in ["occupied", "empty"]:
                new_status = "Occupied" if payload == "occupied" else "Empty"
                
                # Update slot status if changed
                if self.occupancy_status[slot_num] != new_status:
                    self.occupancy_status[slot_num] = new_status
                    if new_status == "Occupied":
                        self.start_timer(slot_num)
                    else:
                        self.stop_timer(slot_num)
                    
                    # Update display
                    color = "#E74C3C" if new_status == "Occupied" else "#2ECC71"
                    self.slots_labels[slot_num].config(
                        text=f"Status: {new_status}",
                        fg=color
                    )

        except Exception as e:
            print(f"Error processing message: {e}")

    def start_timer(self, slot_num):
        """
        Starts timing for an occupied parking slot.
        Records entry time and begins duration updates.
        """
        entry_time = datetime.now()
        self.entry_times[slot_num] = entry_time
        self.entry_time_labels[slot_num].config(
            text=f"Entry: {entry_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        self.update_elapsed_time(slot_num)

    def stop_timer(self, slot_num):
        """
        Stops timing for a parking slot.
        Records exit time and calculates total duration.
        """
        entry_time = self.entry_times.get(slot_num)
        if entry_time:
            exit_time = datetime.now()
            elapsed_time = exit_time - entry_time
            duration_text = f"{int(elapsed_time.total_seconds() // 60)} min {int(elapsed_time.total_seconds() % 60)} sec"
            
            # Update display
            self.exit_time_labels[slot_num].config(
                text=f"Exit: {exit_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            self.duration_labels[slot_num].config(
                text=f"Duration: {duration_text}"
            )

            # Save parking record
            self.save_record(slot_num, entry_time, exit_time, duration_text)
            self.entry_times[slot_num] = None

    def save_record(self, slot, entry_time, exit_time, duration):
        """
        Saves parking record to database.
        Records slot number, entry/exit times, and duration.
        """
        try:
            self.login_system.cursor.execute("""
                INSERT INTO parking_records (slot, entry_time, exit_time, duration)
                VALUES (?, ?, ?, ?)
            """, (
                slot,
                entry_time.strftime("%Y-%m-%d %H:%M:%S"),
                exit_time.strftime("%Y-%m-%d %H:%M:%S"),
                duration
            ))
            self.login_system.conn.commit()
        except sqlite3.Error as e:
            print(f"Error saving record: {e}")

    def update_elapsed_time(self, slot_num):
        """
        Updates the displayed duration for an occupied parking slot.
        Updates every second while slot is occupied.
        """
        if slot_num in self.entry_times and self.entry_times[slot_num]:
            elapsed = datetime.now() - self.entry_times[slot_num]
            minutes, seconds = divmod(elapsed.total_seconds(), 60)
            time_text = f"Duration: {int(minutes)} min {int(seconds)} sec"
            self.duration_labels[slot_num].config(text=time_text)
            self.root.after(1000, lambda: self.update_elapsed_time(slot_num))

if __name__ == "__main__":
    try:
        root = tk.Tk()
        login_system = LoginSystem(root)
        root.mainloop()
    finally:
        GPIO.cleanup()  # Ensure proper GPIO cleanup on exit
