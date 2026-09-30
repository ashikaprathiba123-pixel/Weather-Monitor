import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
import random
import re
import csv
import os

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except:
    PIL_AVAILABLE = False


# ================= CONFIG =================
DB_FILE = "weather_monitor.db"
LOGO_FILE = "logo1.png"

# Professional attractive light colors
BG = "#F3F7FB"
CARD = "#FFFFFF"
SIDEBAR = "#DDECF6"
HEADER = "#EAF4FB"

PRIMARY = "#2D5D7B"
PRIMARY_DARK = "#123047"
TEXT = "#1F2D3D"
MUTED = "#60758A"
BORDER = "#C9D8E8"

BLUE = "#4F7CAC"
GREEN = "#6A994E"
AMBER = "#BC8A3C"
RED = "#B85C5C"
PURPLE = "#7B6D9C"

GOOD_BG = "#EAF7EF"
MODERATE_BG = "#FFF4D9"
POOR_BG = "#FBEAEA"


# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS weather_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity INTEGER NOT NULL,
            aqi INTEGER NOT NULL,
            weather TEXT NOT NULL,
            alert TEXT NOT NULL,
            recommendation TEXT NOT NULL,
            recorded_at TEXT NOT NULL
        )
    """)

    cur.execute("PRAGMA table_info(weather_records)")
    columns = [col[1] for col in cur.fetchall()]

    if "recommendation" not in columns:
        cur.execute("ALTER TABLE weather_records ADD COLUMN recommendation TEXT DEFAULT ''")

    conn.commit()
    conn.close()


def run_query(query, params=(), fetch=False):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(query, params)
    data = cur.fetchall() if fetch else None
    conn.commit()
    conn.close()
    return data


# ================= VALIDATIONS =================
def validate_city(city):
    if city == "":
        return False, "City name is required."

    if len(city) < 2:
        return False, "City name must contain at least 2 letters."

    if len(city) > 30:
        return False, "City name should not be more than 30 letters."

    if not re.match(r"^[A-Za-z ]+$", city):
        return False, "City name should contain only alphabets and spaces."

    return True, ""


def validate_temperature(temp):
    try:
        value = float(temp)

        if value < -20 or value > 60:
            return False, "Temperature must be between -20°C and 60°C."

        return True, value

    except ValueError:
        return False, "Temperature must be a valid number."


def validate_humidity(humidity):
    try:
        value = int(humidity)

        if value < 0 or value > 100:
            return False, "Humidity must be between 0 and 100."

        return True, value

    except ValueError:
        return False, "Humidity must be a whole number."


def validate_aqi(aqi):
    try:
        value = int(aqi)

        if value < 0 or value > 500:
            return False, "AQI must be between 0 and 500."

        return True, value

    except ValueError:
        return False, "AQI must be a whole number."


def validate_date(date_text):
    if date_text == "" or date_text == "YYYY-MM-DD":
        return True, ""

    try:
        datetime.strptime(date_text, "%Y-%m-%d")
        return True, ""

    except ValueError:
        return False, "Date must be in YYYY-MM-DD format."


# ================= WEATHER LOGIC =================
def sample_weather():
    temperature = random.randint(24, 36)
    humidity = random.randint(45, 90)
    aqi = random.randint(20, 170)
    weather = random.choice(["Clear Sky", "Cloudy", "Partly Cloudy", "Rainy", "Foggy"])
    return temperature, humidity, aqi, weather


def get_aqi_status(aqi):
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive People"
    else:
        return "Poor / Unhealthy"


def get_alert(weather, aqi):
    if weather == "Rainy":
        return "Carry an umbrella today."
    elif weather == "Foggy":
        return "Drive carefully due to fog."
    elif aqi > 100:
        return "Air quality is unhealthy."
    else:
        return "No major alert."


def get_recommendation(weather, aqi, humidity):
    if aqi > 150:
        return "Avoid outdoor activities."
    elif aqi > 100:
        return "Use mask while travelling."
    elif weather == "Rainy":
        return "Carry umbrella and protect electronics."
    elif weather == "Foggy":
        return "Avoid early morning travel if possible."
    elif humidity > 80:
        return "High humidity. Drink water and stay comfortable."
    else:
        return "Weather condition is normal."


# ================= MAIN APP =================
class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Local Weather and Air Quality Monitor")
        self.root.geometry("1450x850")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.login_attempts = 0
        self.bg_photo = None

        init_db()
        self.setup_style()
        self.login_page()

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=CARD,
            foreground=TEXT,
            rowheight=27,
            fieldbackground=CARD,
            font=("Segoe UI", 9)
        )

        style.configure(
            "Treeview.Heading",
            background=HEADER,
            foreground=TEXT,
            font=("Segoe UI", 9, "bold")
        )

        style.map("Treeview", background=[("selected", "#C9D8E8")])

    def clear(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    # ================= LOGIN PAGE =================
    def login_page(self):
        self.clear()

        if PIL_AVAILABLE and os.path.exists(LOGO_FILE):
            img = Image.open(LOGO_FILE)
            img = img.resize((1450, 850))
            self.bg_photo = ImageTk.PhotoImage(img)

            bg_label = tk.Label(self.root, image=self.bg_photo)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        else:
            self.root.configure(bg=BG)

        overlay = tk.Frame(self.root, bg="#F8FBFD")
        overlay.place(x=0, y=0, width=1450, height=850)

        header = tk.Frame(overlay, bg=HEADER, height=150)
        header.pack(fill="x")

        tk.Label(
            header,
            text="Local Weather and Air Quality Monitor",
            font=("Segoe UI", 31, "bold"),
            bg=HEADER,
            fg=PRIMARY_DARK
        ).pack(pady=(35, 5))

        tk.Label(
            header,
            text="Professional Environmental Monitoring System",
            font=("Segoe UI", 14),
            bg=HEADER,
            fg=MUTED
        ).pack()

        login_card = tk.Frame(
            overlay,
            bg=CARD,
            width=460,
            height=455,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        login_card.place(x=495, y=235)
        login_card.pack_propagate(False)

        tk.Label(
            login_card,
            text="Admin Login",
            font=("Segoe UI", 26, "bold"),
            bg=CARD,
            fg=PRIMARY_DARK
        ).pack(pady=(50, 28))

        tk.Label(
            login_card,
            text="Username",
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=80)

        self.username = tk.Entry(
            login_card,
            font=("Segoe UI", 14),
            width=30,
            relief="solid",
            bd=1
        )
        self.username.pack(pady=8)
        self.username.insert(0, "admin")

        tk.Label(
            login_card,
            text="Password",
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=80)

        self.password = tk.Entry(
            login_card,
            font=("Segoe UI", 14),
            width=30,
            show="*",
            relief="solid",
            bd=1
        )
        self.password.pack(pady=8)

        tk.Button(
            login_card,
            text="LOGIN",
            font=("Segoe UI", 13, "bold"),
            bg=PRIMARY_DARK,
            fg="white",
            width=24,
            relief="flat",
            command=self.check_login
        ).pack(pady=30)

        tk.Label(
            login_card,
            text="Username: admin   Password: admin123",
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 10)
        ).pack()

    def check_login(self):
        username = self.username.get().strip()
        password = self.password.get().strip()

        if username == "":
            messagebox.showerror("Validation Error", "Username is required.")
            return

        if password == "":
            messagebox.showerror("Validation Error", "Password is required.")
            return

        if username == "admin" and password == "admin123":
            self.dashboard()
        else:
            self.login_attempts += 1

            if self.login_attempts >= 3:
                messagebox.showerror("Blocked", "Too many wrong attempts. Application will close.")
                self.root.destroy()
            else:
                messagebox.showerror(
                    "Login Failed",
                    f"Invalid username or password. Attempts left: {3 - self.login_attempts}"
                )

    # ================= MAIN LAYOUT =================
    def dashboard(self):
        self.clear()

        sidebar = tk.Frame(self.root, bg=SIDEBAR, width=230)
        sidebar.pack(side="left", fill="y")

        main = tk.Frame(self.root, bg=BG)
        main.pack(side="right", fill="both", expand=True)

        tk.Label(
            sidebar,
            text="WEATHER",
            font=("Segoe UI", 22, "bold"),
            bg=SIDEBAR,
            fg=PRIMARY_DARK
        ).pack(pady=(35, 4))

        tk.Label(
            sidebar,
            text="Monitoring System",
            font=("Segoe UI", 11),
            bg=SIDEBAR,
            fg=MUTED
        ).pack(pady=(0, 25))

        self.nav_button(sidebar, "Dashboard", self.show_dashboard)
        self.nav_button(sidebar, "History", self.show_history)
        self.nav_button(sidebar, "Reports", self.show_reports)
        self.nav_button(sidebar, "Analytics", self.show_analytics)

        tk.Button(
            sidebar,
            text="Logout",
            font=("Segoe UI", 13, "bold"),
            bg=RED,
            fg="white",
            width=17,
            relief="flat",
            command=self.login_page
        ).pack(pady=45)

        self.content = tk.Frame(main, bg=BG)
        self.content.pack(fill="both", expand=True)

        self.show_dashboard()

    def nav_button(self, parent, text, command):
        tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 13, "bold"),
            bg=CARD,
            fg=TEXT,
            width=17,
            relief="flat",
            command=command
        ).pack(pady=8)

    # ================= DASHBOARD PAGE =================
    def show_dashboard(self):
        self.clear_content()

        header = tk.Frame(self.content, bg=BG)
        header.pack(fill="x", padx=25, pady=(18, 8))

        title_box = tk.Frame(header, bg=BG)
        title_box.pack(side="left")

        tk.Label(
            title_box,
            text="Weather Monitoring Dashboard",
            font=("Segoe UI", 26, "bold"),
            bg=BG,
            fg=PRIMARY_DARK
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="Track temperature, humidity, AQI, weather condition and stored records",
            font=("Segoe UI", 11),
            bg=BG,
            fg=MUTED
        ).pack(anchor="w")

        self.clock = tk.Label(
            header,
            font=("Segoe UI", 12, "bold"),
            bg=BG,
            fg=PRIMARY
        )
        self.clock.pack(side="right")
        self.update_clock()

        self.summary_frame = tk.Frame(self.content, bg=BG)
        self.summary_frame.pack(fill="x", padx=25, pady=(8, 8))
        self.load_summary_cards()

        input_card = tk.Frame(
            self.content,
            bg=CARD,
            height=82,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        input_card.pack(fill="x", padx=25, pady=(0, 8))
        input_card.pack_propagate(False)

        tk.Label(
            input_card,
            text="City Name",
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 11, "bold")
        ).grid(row=0, column=0, padx=18, pady=24, sticky="w")

        self.city_entry = tk.Entry(input_card, font=("Segoe UI", 12), width=25)
        self.city_entry.grid(row=0, column=1, padx=8)

        tk.Button(
            input_card,
            text="Auto Fetch",
            bg=BLUE,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            width=13,
            relief="flat",
            command=self.auto_fetch
        ).grid(row=0, column=2, padx=8)

        tk.Button(
            input_card,
            text="Save Manual",
            bg=GREEN,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            width=13,
            relief="flat",
            command=self.save_manual
        ).grid(row=0, column=3, padx=8)

        tk.Button(
            input_card,
            text="Clear",
            bg=AMBER,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            width=10,
            relief="flat",
            command=self.clear_inputs
        ).grid(row=0, column=4, padx=8)

        cards = tk.Frame(self.content, bg=BG)
        cards.pack(fill="x", padx=25, pady=(0, 8))

        self.temp_card = self.big_card(cards, "Temperature", "-- °C", PRIMARY_DARK, 0)
        self.hum_card = self.big_card(cards, "Humidity", "-- %", GREEN, 1)
        self.aqi_card = self.big_card(cards, "AQI", "--", AMBER, 2)
        self.weather_card = self.big_card(cards, "Weather", "--", PURPLE, 3)

        manual_card = tk.Frame(
            self.content,
            bg=CARD,
            height=88,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        manual_card.pack(fill="x", padx=25, pady=(0, 8))
        manual_card.pack_propagate(False)

        tk.Label(
            manual_card,
            text="Manual Data Entry With Validation",
            bg=CARD,
            fg=TEXT,
            font=("Segoe UI", 13, "bold")
        ).grid(row=0, column=0, columnspan=8, sticky="w", padx=18, pady=(8, 0))

        tk.Label(manual_card, text="Temp", bg=CARD, fg=MUTED).grid(row=1, column=0, padx=12)
        self.temp_entry = tk.Entry(manual_card, width=12, font=("Segoe UI", 10))
        self.temp_entry.grid(row=1, column=1, padx=5)

        tk.Label(manual_card, text="Humidity", bg=CARD, fg=MUTED).grid(row=1, column=2, padx=12)
        self.humidity_entry = tk.Entry(manual_card, width=12, font=("Segoe UI", 10))
        self.humidity_entry.grid(row=1, column=3, padx=5)

        tk.Label(manual_card, text="AQI", bg=CARD, fg=MUTED).grid(row=1, column=4, padx=12)
        self.aqi_entry = tk.Entry(manual_card, width=12, font=("Segoe UI", 10))
        self.aqi_entry.grid(row=1, column=5, padx=5)

        tk.Label(manual_card, text="Weather", bg=CARD, fg=MUTED).grid(row=1, column=6, padx=12)
        self.weather_combo = ttk.Combobox(
            manual_card,
            values=["Clear Sky", "Cloudy", "Partly Cloudy", "Rainy", "Foggy"],
            state="readonly",
            width=18
        )
        self.weather_combo.grid(row=1, column=7, padx=5)

        tk.Label(
            self.content,
            text="Recent Weather Records",
            bg=BG,
            fg=PRIMARY_DARK,
            font=("Segoe UI", 16, "bold")
        ).pack(anchor="w", padx=25, pady=(4, 2))

        self.history_table(self.content, small=True)

    def load_summary_cards(self):
        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        rows = run_query("SELECT temperature, humidity, aqi, city FROM weather_records", fetch=True)

        total = len(rows)
        avg_temp = round(sum(r[0] for r in rows) / total, 1) if total else 0
        avg_aqi = round(sum(r[2] for r in rows) / total, 1) if total else 0
        poor = len([r for r in rows if r[2] > 100])

        self.small_card(self.summary_frame, "Total Records", total, PRIMARY_DARK, 0)
        self.small_card(self.summary_frame, "Average Temp", f"{avg_temp} °C", GREEN, 1)
        self.small_card(self.summary_frame, "Average AQI", avg_aqi, AMBER, 2)
        self.small_card(self.summary_frame, "Poor AQI Count", poor, RED, 3)

    def small_card(self, parent, title, value, color, col):
        frame = tk.Frame(
            parent,
            bg=CARD,
            width=255,
            height=78,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        frame.grid(row=0, column=col, padx=8)
        frame.pack_propagate(False)

        tk.Label(
            frame,
            text=title,
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", padx=16, pady=(9, 0))

        tk.Label(
            frame,
            text=value,
            bg=CARD,
            fg=color,
            font=("Segoe UI", 20, "bold")
        ).pack(anchor="w", padx=16)

    def big_card(self, parent, title, value, color, column):
        frame = tk.Frame(
            parent,
            bg=CARD,
            width=255,
            height=96,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        frame.grid(row=0, column=column, padx=8)
        frame.pack_propagate(False)

        tk.Label(
            frame,
            text=title,
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=16, pady=(10, 0))

        label = tk.Label(
            frame,
            text=value,
            bg=CARD,
            fg=color,
            font=("Segoe UI", 23, "bold")
        )
        label.pack(anchor="w", padx=16)

        return label

    def update_clock(self):
        if hasattr(self, "clock"):
            self.clock.config(text=datetime.now().strftime("%d-%m-%Y  %I:%M:%S %p"))
            self.root.after(1000, self.update_clock)

    # ================= SAVE FUNCTIONS =================
    def auto_fetch(self):
        city = self.city_entry.get().strip().title()

        valid, msg = validate_city(city)
        if not valid:
            messagebox.showerror("Validation Error", msg)
            return

        temp, humidity, aqi, weather = sample_weather()
        self.save_display(city, temp, humidity, aqi, weather)

    def save_manual(self):
        city = self.city_entry.get().strip().title()

        valid, msg = validate_city(city)
        if not valid:
            messagebox.showerror("Validation Error", msg)
            return

        valid, temp = validate_temperature(self.temp_entry.get().strip())
        if not valid:
            messagebox.showerror("Validation Error", temp)
            return

        valid, humidity = validate_humidity(self.humidity_entry.get().strip())
        if not valid:
            messagebox.showerror("Validation Error", humidity)
            return

        valid, aqi = validate_aqi(self.aqi_entry.get().strip())
        if not valid:
            messagebox.showerror("Validation Error", aqi)
            return

        weather = self.weather_combo.get().strip()
        if weather == "":
            messagebox.showerror("Validation Error", "Please select weather condition.")
            return

        self.save_display(city, temp, humidity, aqi, weather)

    def save_display(self, city, temp, humidity, aqi, weather):
        alert = get_alert(weather, aqi)
        status = get_aqi_status(aqi)
        recommendation = get_recommendation(weather, aqi, humidity)

        self.temp_card.config(text=f"{temp} °C")
        self.hum_card.config(text=f"{humidity} %")
        self.aqi_card.config(text=str(aqi))
        self.weather_card.config(text=weather)

        run_query("""
            INSERT INTO weather_records
            (city, temperature, humidity, aqi, weather, alert, recommendation, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            city,
            temp,
            humidity,
            aqi,
            weather,
            alert,
            recommendation,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        self.load_table()
        self.load_summary_cards()

        prediction = self.predict_temperature(city)

        messagebox.showinfo(
            "Weather Record Saved",
            f"City: {city}\n"
            f"Temperature: {temp} °C\n"
            f"Humidity: {humidity}%\n"
            f"AQI Status: {status}\n"
            f"Prediction: {prediction}\n\n"
            f"Alert: {alert}\n"
            f"Suggestion: {recommendation}"
        )

    def predict_temperature(self, city):
        rows = run_query("""
            SELECT temperature FROM weather_records
            WHERE city=?
            ORDER BY id DESC
            LIMIT 7
        """, (city,), fetch=True)

        if len(rows) < 3:
            return "Need at least 3 records"

        temps = [r[0] for r in rows]
        return f"{round(sum(temps) / len(temps), 1)} °C"

    def clear_inputs(self):
        self.city_entry.delete(0, tk.END)
        self.temp_entry.delete(0, tk.END)
        self.humidity_entry.delete(0, tk.END)
        self.aqi_entry.delete(0, tk.END)
        self.weather_combo.set("")

    # ================= TABLE =================
    def history_table(self, parent, small=False):
        table_frame = tk.Frame(parent, bg=BG)
        table_frame.pack(fill="both", expand=True, padx=25, pady=(0, 10))

        columns = ("ID", "Date & Time", "City", "Temp", "Humidity", "AQI", "Weather", "Alert", "Suggestion")

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=6 if small else 18
        )

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")

        self.tree.column("ID", width=45)
        self.tree.column("Date & Time", width=150)
        self.tree.column("Suggestion", width=220)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree.tag_configure("good", background=GOOD_BG)
        self.tree.tag_configure("moderate", background=MODERATE_BG)
        self.tree.tag_configure("poor", background=POOR_BG)

        self.load_table()

    def load_table(self, keyword="", date_value=""):
        if not hasattr(self, "tree"):
            return

        for row in self.tree.get_children():
            self.tree.delete(row)

        query = """
            SELECT id, recorded_at, city, temperature, humidity, aqi, weather, alert, recommendation
            FROM weather_records
            WHERE 1=1
        """
        params = []

        if keyword:
            query += " AND city LIKE ?"
            params.append(f"%{keyword}%")

        if date_value:
            query += " AND recorded_at LIKE ?"
            params.append(f"{date_value}%")

        query += " ORDER BY id DESC LIMIT 100"

        records = run_query(query, tuple(params), fetch=True)

        for record in records:
            aqi = record[5]

            if aqi <= 50:
                tag = "good"
            elif aqi <= 100:
                tag = "moderate"
            else:
                tag = "poor"

            self.tree.insert("", "end", values=record, tags=(tag,))

    # ================= HISTORY PAGE =================
    def show_history(self):
        self.clear_content()

        tk.Label(
            self.content,
            text="Weather History Records",
            font=("Segoe UI", 25, "bold"),
            bg=BG,
            fg=PRIMARY_DARK
        ).pack(anchor="w", padx=25, pady=18)

        controls = tk.Frame(self.content, bg=BG)
        controls.pack(fill="x", padx=25)

        tk.Label(
            controls,
            text="City:",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 12, "bold")
        ).pack(side="left")

        self.search_city = tk.Entry(controls, font=("Segoe UI", 12), width=18)
        self.search_city.pack(side="left", padx=8)

        tk.Label(
            controls,
            text="Date:",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 12, "bold")
        ).pack(side="left", padx=(10, 0))

        self.search_date = tk.Entry(controls, font=("Segoe UI", 12), width=14)
        self.search_date.pack(side="left", padx=8)
        self.search_date.insert(0, "YYYY-MM-DD")

        tk.Button(
            controls,
            text="Search",
            bg=BLUE,
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            command=self.search_records
        ).pack(side="left", padx=5)

        tk.Button(
            controls,
            text="Delete Selected",
            bg=RED,
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            command=self.delete_selected
        ).pack(side="left", padx=5)

        tk.Button(
            controls,
            text="Clear All",
            bg=AMBER,
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            command=self.clear_all
        ).pack(side="left", padx=5)

        tk.Button(
            controls,
            text="Export CSV",
            bg=GREEN,
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            command=self.export_csv
        ).pack(side="left", padx=5)

        self.history_table(self.content)

    def search_records(self):
        city = self.search_city.get().strip().title()
        date_value = self.search_date.get().strip()

        if date_value == "YYYY-MM-DD":
            date_value = ""

        if city:
            valid, msg = validate_city(city)
            if not valid:
                messagebox.showerror("Validation Error", msg)
                return

        valid, msg = validate_date(date_value)
        if not valid:
            messagebox.showerror("Validation Error", msg)
            return

        self.load_table(city, date_value)

    def delete_selected(self):
        selected = self.tree.focus()

        if not selected:
            messagebox.showerror("Error", "Please select one record.")
            return

        values = self.tree.item(selected, "values")
        record_id = values[0]

        if messagebox.askyesno("Confirm Delete", "Do you want to delete selected record?"):
            run_query("DELETE FROM weather_records WHERE id=?", (record_id,))
            self.load_table()
            messagebox.showinfo("Deleted", "Record deleted successfully.")

    def clear_all(self):
        if messagebox.askyesno("Confirm Clear", "Do you want to delete all records?"):
            run_query("DELETE FROM weather_records")
            self.load_table()
            messagebox.showinfo("Cleared", "All records deleted successfully.")

    def export_csv(self):
        records = run_query("""
            SELECT id, recorded_at, city, temperature, humidity, aqi, weather, alert, recommendation
            FROM weather_records
            ORDER BY id DESC
        """, fetch=True)

        if not records:
            messagebox.showerror("Error", "No records available to export.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Save Weather Report"
        )

        if file_path == "":
            return

        with open(file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([
                "ID",
                "Date & Time",
                "City",
                "Temperature",
                "Humidity",
                "AQI",
                "Weather",
                "Alert",
                "Suggestion"
            ])
            writer.writerows(records)

        messagebox.showinfo("Exported", "CSV report exported successfully.")

    # ================= REPORTS PAGE =================
    def show_reports(self):
        self.clear_content()

        tk.Label(
            self.content,
            text="Weather Reports and Analysis",
            font=("Segoe UI", 25, "bold"),
            bg=BG,
            fg=PRIMARY_DARK
        ).pack(anchor="w", padx=25, pady=18)

        report_frame = tk.Frame(self.content, bg=BG)
        report_frame.pack(fill="both", expand=True, padx=25, pady=10)

        rows = run_query("""
            SELECT city, temperature, humidity, aqi, weather, recorded_at
            FROM weather_records
        """, fetch=True)

        if not rows:
            tk.Label(
                report_frame,
                text="No records available for report",
                bg=BG,
                fg=RED,
                font=("Segoe UI", 16, "bold")
            ).pack(pady=50)
            return

        total = len(rows)
        avg_temp = round(sum(r[1] for r in rows) / total, 1)
        avg_humidity = round(sum(r[2] for r in rows) / total, 1)
        avg_aqi = round(sum(r[3] for r in rows) / total, 1)
        highest = max(rows, key=lambda x: x[1])
        lowest = min(rows, key=lambda x: x[1])
        poor_count = len([r for r in rows if r[3] > 100])

        city_count = {}
        for r in rows:
            city_count[r[0]] = city_count.get(r[0], 0) + 1

        most_searched_city = max(city_count, key=city_count.get)

        data = [
            ("Total Records", total, PRIMARY_DARK),
            ("Average Temperature", f"{avg_temp} °C", GREEN),
            ("Average Humidity", f"{avg_humidity} %", PURPLE),
            ("Average AQI", avg_aqi, AMBER),
            ("Poor AQI Records", poor_count, RED),
            ("Highest Temperature", f"{highest[1]} °C - {highest[0]}", RED),
            ("Lowest Temperature", f"{lowest[1]} °C - {lowest[0]}", BLUE),
            ("Most Searched City", most_searched_city, PRIMARY_DARK),
        ]

        for i, (title, value, color) in enumerate(data):
            frame = tk.Frame(
                report_frame,
                bg=CARD,
                width=335,
                height=110,
                highlightbackground=BORDER,
                highlightthickness=1
            )
            frame.grid(row=i // 3, column=i % 3, padx=12, pady=12)
            frame.pack_propagate(False)

            tk.Label(
                frame,
                text=title,
                bg=CARD,
                fg=MUTED,
                font=("Segoe UI", 12, "bold")
            ).pack(pady=(18, 5))

            tk.Label(
                frame,
                text=value,
                bg=CARD,
                fg=color,
                font=("Segoe UI", 17, "bold")
            ).pack()

    # ================= ANALYTICS PAGE =================
    def show_analytics(self):
        self.clear_content()

        tk.Label(
            self.content,
            text="Weather Analytics",
            font=("Segoe UI", 25, "bold"),
            bg=BG,
            fg=PRIMARY_DARK
        ).pack(anchor="w", padx=25, pady=18)

        rows = run_query("""
            SELECT city, temperature, humidity, aqi, weather
            FROM weather_records
            ORDER BY id DESC
            LIMIT 10
        """, fetch=True)

        if not rows:
            tk.Label(
                self.content,
                text="No records available for analytics",
                font=("Segoe UI", 16, "bold"),
                bg=BG,
                fg=RED
            ).pack(pady=60)
            return

        chart_area = tk.Frame(self.content, bg=BG)
        chart_area.pack(fill="both", expand=True, padx=25, pady=10)

        self.draw_bar_graph(chart_area, rows)
        self.draw_pie_chart(chart_area, rows)

    def draw_bar_graph(self, parent, rows):
        frame = tk.Frame(
            parent,
            bg=CARD,
            width=555,
            height=500,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        frame.grid(row=0, column=0, padx=12, pady=10)
        frame.pack_propagate(False)

        tk.Label(
            frame,
            text="Temperature Bar Graph",
            font=("Segoe UI", 17, "bold"),
            bg=CARD,
            fg=PRIMARY_DARK
        ).pack(pady=15)

        canvas = tk.Canvas(frame, width=520, height=390, bg=CARD, highlightthickness=0)
        canvas.pack()

        data = rows[::-1]
        cities = [r[0] for r in data]
        temps = [float(r[1]) for r in data]
        max_temp = max(temps)

        canvas.create_line(60, 330, 490, 330, fill=TEXT, width=2)
        canvas.create_line(60, 60, 60, 330, fill=TEXT, width=2)

        colors = ["#BBD7EA", "#CDE7D8", "#F3D9A4", "#D7CEE8", "#EAC7C7"]

        x = 85
        for i, temp in enumerate(temps):
            height = int((temp / max_temp) * 230)
            y = 330 - height
            color = colors[i % len(colors)]

            canvas.create_rectangle(x, y, x + 32, 330, fill=color, outline="#C9D6E2")
            canvas.create_text(x + 16, y - 12, text=f"{temp}°",
                               fill=TEXT, font=("Segoe UI", 9, "bold"))
            canvas.create_text(x + 16, 350, text=cities[i][:6],
                               fill=MUTED, font=("Segoe UI", 8, "bold"), angle=35)
            x += 44

        canvas.create_text(
            270,
            375,
            text="Last 10 temperature records",
            fill=MUTED,
            font=("Segoe UI", 10, "bold")
        )

    def draw_pie_chart(self, parent, rows):
        frame = tk.Frame(
            parent,
            bg=CARD,
            width=555,
            height=500,
            highlightbackground=BORDER,
            highlightthickness=1
        )
        frame.grid(row=0, column=1, padx=12, pady=10)
        frame.pack_propagate(False)

        tk.Label(
            frame,
            text="AQI Category Pie Chart",
            font=("Segoe UI", 17, "bold"),
            bg=CARD,
            fg=PRIMARY_DARK
        ).pack(pady=15)

        canvas = tk.Canvas(frame, width=520, height=390, bg=CARD, highlightthickness=0)
        canvas.pack()

        good = len([r for r in rows if r[3] <= 50])
        moderate = len([r for r in rows if 51 <= r[3] <= 100])
        poor = len([r for r in rows if r[3] > 100])

        pie_data = [
            ("Good", good, "#CDE7D8"),
            ("Moderate", moderate, "#F3D9A4"),
            ("Poor", poor, "#EAC7C7")
        ]

        total = good + moderate + poor
        start = 0

        for name, value, color in pie_data:
            if value == 0:
                continue

            extent = (value / total) * 360
            canvas.create_arc(
                120, 70, 360, 310,
                start=start,
                extent=extent,
                fill=color,
                outline=CARD
            )
            start += extent

        canvas.create_oval(190, 140, 290, 240, fill=CARD, outline=CARD)

        canvas.create_text(
            240,
            185,
            text="AQI",
            fill=PRIMARY_DARK,
            font=("Segoe UI", 18, "bold")
        )

        legend_x = 390
        legend_y = 110

        for name, value, color in pie_data:
            percent = round((value / total) * 100, 1) if total else 0

            canvas.create_rectangle(
                legend_x, legend_y,
                legend_x + 18, legend_y + 18,
                fill=color,
                outline="#C9D6E2"
            )

            canvas.create_text(
                legend_x + 30,
                legend_y + 9,
                text=f"{name}: {value} ({percent}%)",
                anchor="w",
                fill=TEXT,
                font=("Segoe UI", 10, "bold")
            )

            legend_y += 35

        canvas.create_text(
            260,
            355,
            text="AQI distribution from latest 10 records",
            fill=MUTED,
            font=("Segoe UI", 10, "bold")
        )


# ================= RUN APP =================
if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    root.mainloop()