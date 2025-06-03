import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import serial
import serial.tools.list_ports
import threading
import json
import time
import os

PROFILES_FILE = "profiles.json"

def load_profiles():
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, "r") as f:
            return json.load(f)
    return {}

def save_profiles(profiles):
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=4)

class SerialLoggerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Serial Command Logger & Profile Executor")

        self.serial_port = None
        self.running = False
        self.listener_thread = None
        self.profiles = load_profiles()

        self.create_widgets()

    def create_widgets(self):
        top = ttk.Frame(self.root, padding=10)
        top.grid(row=0, column=0, sticky="ew")

        ttk.Label(top, text="COM Port:").grid(row=0, column=0)
        self.port_combo = ttk.Combobox(top, width=10)
        self.port_combo.grid(row=0, column=1)
        self.refresh_ports()
        ttk.Button(top, text="\U0001F504", width=3, command=self.refresh_ports).grid(row=0, column=2)

        ttk.Label(top, text="Baud:").grid(row=0, column=3)
        self.baud_var = tk.StringVar(value="115200")
        ttk.Entry(top, textvariable=self.baud_var, width=8).grid(row=0, column=4)

        self.connect_btn = ttk.Button(top, text="Connect", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=5, padx=5)

        ttk.Label(top, text="Profile:").grid(row=1, column=0)
        self.profile_combo = ttk.Combobox(top, values=list(self.profiles.keys()), width=20)
        self.profile_combo.grid(row=1, column=1, columnspan=2)

        ttk.Button(top, text="Edit Profile", command=self.edit_profile).grid(row=1, column=3)
        ttk.Button(top, text="New Profile", command=self.new_profile).grid(row=1, column=4)
        ttk.Button(top, text="Delete Profile", command=self.delete_profile).grid(row=1, column=6)
        ttk.Button(top, text="Execute", command=self.execute_profile).grid(row=1, column=5, padx=5)

        self.output_text = tk.Text(self.root, height=20, width=90)
        self.output_text.grid(row=2, column=0, padx=10, pady=10)

    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.set(ports[0])

    def toggle_connection(self):
        if self.running:
            self.disconnect_port()
        else:
            self.connect_port()

    def connect_port(self):
        port = self.port_combo.get()
        try:
            baud = int(self.baud_var.get())
            self.serial_port = serial.Serial(port, baudrate=baud, bytesize=8, parity='N', stopbits=1, timeout=0.1)
            self.running = True
            self.listener_thread = threading.Thread(target=self.listen_serial, daemon=True)
            self.listener_thread.start()
            self.connect_btn.config(text="Disconnect")
            self.log(f"✅ Connected to {port} at {baud} baud.")
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def disconnect_port(self):
        self.running = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.connect_btn.config(text="Connect")
        self.log(f"❌ Disconnected.")

    def listen_serial(self):
        while self.running and self.serial_port and self.serial_port.is_open:
            try:
                data = self.serial_port.read(self.serial_port.in_waiting or 1)
                if data:
                    decoded = data.decode(errors='ignore')
                    self.log(f"⬅️ RX: {decoded.strip()}")
            except Exception as e:
                self.log(f"❗ Listen Error: {e}")
                break
            time.sleep(0.01)

    def log(self, message):
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)

    def new_profile(self):
        name = simpledialog.askstring("New Profile", "Enter profile name:")
        if name and name not in self.profiles:
            self.profiles[name] = {"steps": [], "is_hex": False}
            self.profile_combo['values'] = list(self.profiles.keys())
            self.profile_combo.set(name)
            self.edit_profile()
        else:
            messagebox.showinfo("Info", "Profile already exists or invalid name.")

    def delete_profile(self):
        name = self.profile_combo.get()
        if not name:
            messagebox.showerror("Delete Error", "No profile selected.")
            return
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete profile '{name}'?"):
            if name in self.profiles:
                del self.profiles[name]
                save_profiles(self.profiles)
                self.profile_combo['values'] = list(self.profiles.keys())
                self.profile_combo.set("")
                self.log(f"🗑️ Profile '{name}' deleted.")
            else:
                messagebox.showerror("Delete Error", f"Profile '{name}' not found.")

    def edit_profile(self):
        name = self.profile_combo.get()
        if name not in self.profiles:
            return messagebox.showerror("Profile Error", "Select a valid profile.")

        profile = self.profiles[name]

        editor = tk.Toplevel(self.root)
        editor.title(f"Edit Profile - {name}")
        editor.geometry("600x400")

        step_frame = ttk.Frame(editor)
        step_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(step_frame)
        scrollbar = ttk.Scrollbar(step_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        step_widgets = []

        def render_steps():
            for widget in scrollable_frame.winfo_children():
                widget.destroy()
            step_widgets.clear()

            for idx, step in enumerate(profile["steps"]):
                row = ttk.Frame(scrollable_frame)
                row.pack(fill=tk.X, pady=2)

                cmd_var = tk.StringVar(value=step["cmd"])
                delay_var = tk.StringVar(value=str(step.get("delay", 1.0)))
                step_widgets.append((cmd_var, delay_var))

                ttk.Entry(row, textvariable=cmd_var, width=60).pack(side=tk.LEFT, padx=2)
                ttk.Entry(row, textvariable=delay_var, width=6).pack(side=tk.LEFT, padx=2)
                ttk.Button(row, text="↑", width=2, command=lambda i=idx: move_step(i, -1)).pack(side=tk.LEFT)
                ttk.Button(row, text="↓", width=2, command=lambda i=idx: move_step(i, 1)).pack(side=tk.LEFT)
                ttk.Button(row, text="❌", command=lambda i=idx: delete_step(i)).pack(side=tk.LEFT)

        def move_step(index, direction):
            new_index = index + direction
            if 0 <= new_index < len(profile["steps"]):
                profile["steps"][index], profile["steps"][new_index] = profile["steps"][new_index], profile["steps"][index]
                render_steps()

        def delete_step(index):
            if index < len(profile["steps"]):
                del profile["steps"][index]
                render_steps()

        def add_step():
            profile["steps"].append({"cmd": "", "delay": 1.0})
            render_steps()

        render_steps()

        bottom = ttk.Frame(editor)
        bottom.pack(fill=tk.X, pady=10)

        is_hex_var = tk.BooleanVar(value=profile.get("is_hex", False))
        ttk.Checkbutton(bottom, text="Send as HEX", variable=is_hex_var).pack(side=tk.LEFT, padx=10)

        ttk.Button(bottom, text="Add Step", command=add_step).pack(side=tk.LEFT)
        ttk.Button(bottom, text="Save", command=lambda: self.save_profile(editor, name, is_hex_var, step_widgets)).pack(side=tk.RIGHT, padx=10)

    def save_profile(self, editor, name, is_hex_var, step_widgets):
        updated_steps = []
        for cmd_var, delay_var in step_widgets:
            try:
                delay = float(delay_var.get())
                updated_steps.append({"cmd": cmd_var.get().strip(), "delay": delay})
            except ValueError:
                continue

        self.profiles[name] = {"steps": updated_steps, "is_hex": is_hex_var.get()}
        save_profiles(self.profiles)
        self.profile_combo['values'] = list(self.profiles.keys())
        self.log(f"📝 Profile '{name}' saved.")
        editor.destroy()

    def execute_profile(self):
        name = self.profile_combo.get()
        if name not in self.profiles:
            return messagebox.showerror("Profile Error", "Select a valid profile.")

        if not self.serial_port or not self.serial_port.is_open:
            return messagebox.showerror("Port Error", "Connect to COM port first.")

        profile = self.profiles[name]
        steps = profile.get("steps", [])
        is_hex = profile.get("is_hex", False)

        threading.Thread(target=self.send_sequence, args=(steps, is_hex), daemon=True).start()

    def send_sequence(self, steps, is_hex):
        for step in steps:
            cmd = step["cmd"]
            delay = step.get("delay", 1.0)

            try:
                if is_hex:
                    bytes_to_send = bytes.fromhex(cmd)
                    self.serial_port.write(bytes_to_send)
                    self.log(f"➡️ Sent (HEX): {cmd}")
                else:
                    self.serial_port.write((cmd + "\r\n").encode())
                    self.log(f"➡️ Sent (ASCII): {cmd}")

                time.sleep(delay)

            except Exception as e:
                self.log(f"❗ Error: {e}")
                break

        self.log("✅ Sequence complete.")

    def close(self):
        self.disconnect_port()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialLoggerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()
