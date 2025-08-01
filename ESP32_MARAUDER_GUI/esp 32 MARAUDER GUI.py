#
# ESP32 Marauder GUI - Final Version
#
# Required library: pyserial
# Install it using: pip install pyserial
#

import tkinter as tk
from tkinter import messagebox, Frame, Label, Button, Entry, Listbox, Text, Canvas, OptionMenu, StringVar
import serial
import serial.tools.list_ports
import threading
import time
from random import choice, randint

# --- Marauder Commands ---
MARAUDER_COMMANDS = [
    "channel -s", "settings -s", "settings -r", "clearlist -a", "clearlist -c", "clearlist -s",
    "reboot", "update -s", "update -w", "ls", "led -s", "led -p", "gpsdata",
    "gps", "nmea", "evilportal", "packetcount", "pingscan", "portscan", "sigmon",
    "scanall", "scanap", "scansta", "sniffraw", "sniffbeacon", "sniffprobe",
    "sniffpwn", "sniffpinescan", "sniffmultissid", "sniffesp", "sniffdeauth",
    "sniffpmkid", "stopscan", "attack -t beacon", "attack -t deauth", "attack -t probe",
    "attack -t rickroll", "info", "list -s", "list -a", "list -c", "list -t",
    "list -i", "select -a", "select -s", "select -c", "ssid -a", "ssid -r",
    "save -a", "save -s", "load -a", "load -s", "join -a", "sniffbt", "blespam",
    "spoofat", "sniffskim", "stop"
]

class MarauderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.ser = None
        
        # --- UI Styling ---
        self.FONT = ("Consolas", 11)
        self.BG = "#1e1e2f"
        self.FG = "#ffffff"
        self.BTN_BG = "#2d2d44"
        self.BTN_HOVER = "#444466"
        self.ACCENT = "#00ffaa"
        self.RED = "#ff5555"
        self.CYAN = "#89ddff"

        self.animation_running = False

        self._setup_window()
        self._create_widgets()
        self._animate_background()
        self._update_time()

    def _setup_window(self):
        """Configure the main window."""
        self.title("🚀 ESP32 Marauder GUI")
        self.geometry("950x700")
        self.config(bg=self.BG)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.resizable(False, False)

    def _create_widgets(self):
        """Create and place all the widgets in the window."""
        self._create_animated_bg()
        
        # --- Live Time Display ---
        self.time_label = Label(self, font=("Consolas", 14), fg=self.ACCENT, bg="#0f0f0f")
        self.time_label.place(x=10, y=10)

        # --- Port Section (Top Frame) ---
        port_frame = Frame(self, bg=self.BG)
        port_frame.pack(pady=10)
        self._create_port_section(port_frame)
        
        # --- Output Area & Status Label ---
        self.output_text = Text(self, height=10, width=90, bg="black", fg=self.ACCENT, font=("Consolas", 10), bd=0, relief="flat")
        self.output_text.pack(pady=10)
        self.output_text.config(state=tk.DISABLED)

        self.status_label = Label(self, text="Status: Disconnected", font=("Consolas", 12), bg=self.BG, fg=self.RED)
        self.status_label.pack(pady=5)
        
        # --- Scan & SSID List ---
        self._style_button(Button(self, text="📡 Scan Wi-Fi", command=self._start_wifi_scan)).pack(pady=5)
        self.ssid_listbox = Listbox(self, height=8, width=90, bg="#282c34", fg="lightgreen", font=self.FONT, bd=0, relief="flat")
        self.ssid_listbox.pack(pady=10)
        
        # --- Attack & SSID Entry Buttons ---
        attack_frame = Frame(self, bg=self.BG)
        attack_frame.pack(pady=5)
        
        self._create_attack_controls(attack_frame)
        
        # --- Command Entry ---
        cmd_and_suggestion_frame = Frame(self, bg=self.BG)
        cmd_and_suggestion_frame.pack(pady=5)
        self._create_command_entry(cmd_and_suggestion_frame)
        
        self.lift()
        self.attributes('-topmost', True)
        self.after_idle(self.attributes, '-topmost', False)

    def _create_animated_bg(self):
        """Create the canvas for the matrix background with a "hacking" text effect."""
        self.bg_canvas = Canvas(self, bg="#0f0f0f", highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.dot_matrix = []
        hacker_chars = list("0123456789abcdefghijklmnopqrstuvwxyz!@#$%^&*()_+-=[]{};:'\"|\\,.<>/?")
        for _ in range(250): # Increased number of characters for a denser effect
            x = randint(0, 950)
            y = randint(0, 700)
            char = choice(hacker_chars)
            color = choice(["#00ff00", "#00dd88", "#00ffaa", "#00ffcc", "#ffffff"]) # Added white for contrast
            speed = randint(1, 5) # Varied speed for a more dynamic effect
            item = self.bg_canvas.create_text(x, y, text=char, fill=color, font=("Consolas", randint(8, 14)))
            self.dot_matrix.append((item, speed))

    def _create_port_section(self, parent_frame):
        """Create widgets for serial port connection."""
        Label(parent_frame, text="🔌 COM Port:", font=self.FONT, fg=self.FG, bg=self.BG).pack(side="left", padx=5)
        self.port_var = StringVar()
        ports = self._get_ports()
        self.port_var.set(ports[0] if ports else "No COM found")
        self.port_menu = OptionMenu(parent_frame, self.port_var, *ports if ports else ["No COM found"])
        self.port_menu.config(bg=self.BTN_BG, fg=self.FG, font=self.FONT, relief="flat", activebackground=self.BTN_HOVER, width=15)
        self.port_menu['menu'].config(bg=self.BTN_BG, fg=self.FG)
        self.port_menu.pack(side="left", padx=5)

        self._style_button(Button(parent_frame, text="Refresh", command=self._refresh_ports)).pack(side="left", padx=5)
        self.connect_btn = self._style_button(Button(parent_frame, text="Connect", command=self._toggle_connection))
        self.connect_btn.pack(side="left", padx=5)
    
    def _create_attack_controls(self, parent_frame):
        """Create the attack buttons and fake SSID entry."""
        self._style_button(Button(parent_frame, text="➕ Add Fake SSID", command=self._add_fake_ssid)).pack(side="left", padx=5)
        self._style_button(Button(parent_frame, text="📡 Start Beacon", command=self._start_beacon_attack)).pack(side="left", padx=5)
        self._style_button(Button(parent_frame, text="💣 Start Deauth", command=self._start_deauth_attack)).pack(side="left", padx=5)
        self._style_button(Button(parent_frame, text="🛑 Stop", command=lambda: self._send_command("stop"))).pack(side="left", padx=5)
        
        Label(parent_frame, text="Fake SSID:", font=self.FONT, fg=self.FG, bg=self.BG).pack(side="left", padx=10)
        self.ssid_entry = Entry(parent_frame, width=20, font=self.FONT, bg="#282c34", fg=self.FG, insertbackground=self.FG)
        self.ssid_entry.insert(0, "Free WiFi")
        self.ssid_entry.pack(side="left")

    def _create_command_entry(self, parent_frame):
        """Create the custom command entry and suggestion box."""
        Label(parent_frame, text="⌨️ Custom Command:", font=self.FONT, fg=self.FG, bg=self.BG).pack(side="left", padx=5)
        self.cmd_entry = Entry(parent_frame, width=30, font=self.FONT, bg="#282c34", fg=self.FG, insertbackground=self.FG)
        self.cmd_entry.pack(side="left", padx=5)
        self.cmd_entry.bind("<KeyRelease>", self._show_suggestions)
        self.cmd_entry.bind("<Return>", lambda event: self._send_command(self.cmd_entry.get()))
        
        self._style_button(Button(parent_frame, text="Send", command=lambda: self._send_command(self.cmd_entry.get()))).pack(side="left", padx=5)

        self.suggestion_box = Listbox(parent_frame, height=6, width=30, font=("Consolas", 10), bg="#111", fg=self.CYAN, highlightthickness=0, bd=0)
        self.suggestion_box.bind("<<ListboxSelect>>", self._select_suggestion)
        self.bind("<Button-1>", lambda event: self.suggestion_box.place_forget())

    # --- UI Styling & Animation ---
    def _style_button(self, btn):
        """Apply a consistent style to a button."""
        btn.config(bg=self.BTN_BG, fg=self.FG, font=self.FONT, relief="flat", activebackground=self.BTN_HOVER, padx=10, pady=5)
        btn.bind("<Enter>", lambda e: e.widget.config(bg=self.BTN_HOVER))
        btn.bind("<Leave>", lambda e: e.widget.config(bg=self.BTN_BG))
        return btn

    def _animate_background(self):
        """Move the characters on the background canvas."""
        for item, speed in self.dot_matrix:
            self.bg_canvas.move(item, 0, speed)
            x, y = self.bg_canvas.coords(item)
            if y > self.winfo_height():
                self.bg_canvas.coords(item, randint(0, self.winfo_width()), 0)
                self.bg_canvas.itemconfig(item, text=choice("0123456789abcdefghijklmnopqrstuvwxyz!@#$%^&*()_+-=[]{};:'\"|\\,.<>/?"))
        self.after(50, self._animate_background)
        
    def _update_time(self):
        """Update the time label with the current system time."""
        current_time = time.strftime("%H:%M:%S")
        self.time_label.config(text=current_time)
        self.after(1000, self._update_time) # Call this method every 1000ms (1 second)
        
    def _update_status(self, text, color):
        """Update the status label text and color."""
        self.status_label.config(text=f"Status: {text}", fg=color)
    
    def _show_animated_status(self, status_text, color1, color2, final_text, duration_s):
        """Show a temporary flashing animation for a given duration."""
        self.animation_running = True
        end_time = time.time() + duration_s
        colors = [color1, color2]
        
        def animate():
            if time.time() < end_time and self.animation_running:
                current_color = colors[int(time.time() * 2) % 2]
                self._update_status(status_text, current_color)
                self.after(100, animate)
            else:
                self.animation_running = False
                self._update_status(final_text, self.CYAN)
        
        animate()

    # --- Serial Communication ---
    def _get_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def _refresh_ports(self):
        ports = self._get_ports()
        menu = self.port_menu["menu"]
        menu.delete(0, "end")
        if ports:
            for port in ports:
                menu.add_command(label=port, command=lambda value=port: self.port_var.set(value))
            self.port_var.set(ports[0])
        else:
            self.port_var.set("No COM found")
            menu.add_command(label="No COM found", command=lambda: self.port_var.set("No COM found"))
    
    def _toggle_connection(self):
        if self.ser and self.ser.is_open:
            self._disconnect_serial()
        else:
            self._connect_serial()
            
    def _connect_serial(self):
        selected_port = self.port_var.get()
        if "No COM" in selected_port:
            messagebox.showerror("Connection Error", "No COM port selected or available.")
            return
        try:
            self.ser = serial.Serial(selected_port, 115200, timeout=1)
            time.sleep(2)
            threading.Thread(target=self._read_serial, daemon=True).start()
            self._append_text(f"✅ Connected to {selected_port}\n")
            self._update_status(f"Connected to {selected_port}", self.ACCENT)
            self.connect_btn.config(text="Disconnect")
        except serial.SerialException as e:
            messagebox.showerror("Connection Error", str(e))
            self.ser = None
            
    def _disconnect_serial(self):
        if self.ser:
            self.ser.close()
            self.ser = None
        self._append_text("🔌 Disconnected.\n")
        self._update_status("Disconnected", self.RED)
        self.connect_btn.config(text="Connect")

    def _send_command(self, cmd):
        cmd = cmd.strip()
        if not cmd:
            return
        if self.ser and self.ser.is_open:
            try:
                self.ser.write((cmd + '\n').encode())
                self._append_text(f"➡️ SENT: {cmd}\n")
            except Exception as e:
                self._append_text(f"❌ Send Error: {e}\n")
                self._disconnect_serial()
        else:
            self._append_text("⚠️ Not connected to ESP32\n")
        self.cmd_entry.delete(0, tk.END)
        self.suggestion_box.place_forget()

    def _read_serial(self):
        while self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self.after(0, self._process_serial_line, line)
            except serial.SerialException:
                self.after(0, self._disconnect_serial)
                break
            except Exception as e:
                self.after(0, self._append_text, f"❌ ERROR: {e}\n")
            time.sleep(0.05)
    
    def _process_serial_line(self, line):
        self._append_text(f"⬅️ RECV: {line}\n")
        if "SSID" in line and "CH:" in line:
            self.ssid_listbox.insert(tk.END, line)
        if "scan complete" in line.lower():
            self._update_status("Wi-Fi Scan Complete!", self.CYAN)
        if "[Deauth]" in line or "[Beacon]" in line:
            self._update_status("Attack started!", self.RED)
            
    def _append_text(self, text):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)

    # --- Command Helpers ---
    def _start_wifi_scan(self):
        self._update_status("Scanning for Wi-Fi...", self.CYAN)
        self.ssid_listbox.delete(0, tk.END)
        self._send_command("scan -t wifi")

    def _start_beacon_attack(self):
        self._update_status("Starting Beacon Attack!", self.RED)
        self._send_command("attack -t beacon")

    def _start_deauth_attack(self):
        self._update_status("Starting Deauth Attack!", self.RED)
        self._send_command("attack -t deauth")

    def _add_fake_ssid(self):
        ssid = self.ssid_entry.get()
        if ssid:
            self._send_command(f'ssid -a "{ssid}"')
        else:
            messagebox.showwarning("Input Error", "Fake SSID cannot be empty.")

    # --- Command Suggestions ---
    def _show_suggestions(self, event):
        typed = self.cmd_entry.get().lower()
        self.suggestion_box.delete(0, tk.END)
        if not typed:
            self.suggestion_box.place_forget()
            return
        
        matches = [cmd for cmd in MARAUDER_COMMANDS if cmd.startswith(typed)]
        if matches:
            for i, match in enumerate(matches):
                self.suggestion_box.insert(tk.END, match)
                self.suggestion_box.itemconfig(i, {'fg': self.CYAN})
            
            self.cmd_entry.update_idletasks()
            x = self.cmd_entry.winfo_x() + self.cmd_entry.winfo_width() + 10
            y = self.cmd_entry.winfo_y()
            self.suggestion_box.place(x=x, y=y)
        else:
            self.suggestion_box.place_forget()

    def _select_suggestion(self, event):
        if self.suggestion_box.curselection():
            selected = self.suggestion_box.get(self.suggestion_box.curselection())
            self.cmd_entry.delete(0, tk.END)
            self.cmd_entry.insert(0, selected)
            self.suggestion_box.place_forget()
            self.cmd_entry.focus()
            
    def _on_closing(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.destroy()

if __name__ == "__main__":
    app = MarauderApp()
    app.mainloop()
