import time
import win32gui
import win32con
import win32process
import psutil
import ctypes
from ttkbootstrap import Style
import tkinter as tk
from tkinter import ttk

user32 = ctypes.windll.user32

# Set target resolution (change to match your monitor)
TARGET_WIDTH = 2560
TARGET_HEIGHT = 1440

def list_running_apps():
    """Returns a list of currently running applications with visible windows."""
    apps = []

    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):  # Only include visible windows
            title = win32gui.GetWindowText(hwnd).strip()
            if title:
                pid = win32process.GetWindowThreadProcessId(hwnd)[1]
                process_name = psutil.Process(pid).name() if pid else "Unknown Process"
                apps.append((title, process_name, hwnd))  # Store title, process name, and handle

    win32gui.EnumWindows(callback, None)

    # Sort and remove duplicates
    unique_apps = {}
    for title, process, hwnd in apps:
        if process not in unique_apps:
            unique_apps[process] = (title, process, hwnd)

    return list(unique_apps.values())

def find_window_by_process(process_name):
    """Finds the first window handle for the given process name."""
    for title, process, hwnd in list_running_apps():
        if process.lower() == process_name.lower():
            return hwnd
    return None

def make_borderless(hwnd):
    """Remove the title bar and borders from the selected window."""
    if not hwnd:
        status_label.config(text="❌ Window handle invalid!")
        return

    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    new_style = style & ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME)
    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, new_style)

    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    new_ex_style = ex_style & ~(win32con.WS_EX_DLGMODALFRAME | win32con.WS_EX_WINDOWEDGE | win32con.WS_EX_CLIENTEDGE | win32con.WS_EX_STATICEDGE)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, new_ex_style)

    SCREEN_WIDTH = user32.GetSystemMetrics(0)
    SCREEN_HEIGHT = user32.GetSystemMetrics(1)

    X_POS = (SCREEN_WIDTH - TARGET_WIDTH) // 2
    Y_POS = 0

    win32gui.SetWindowPos(hwnd, None, X_POS, Y_POS, TARGET_WIDTH, TARGET_HEIGHT,
                          win32con.SWP_FRAMECHANGED | win32con.SWP_NOZORDER | win32con.SWP_SHOWWINDOW)

    status_label.config(text=f"🚀 Applied borderless mode to {game_var.get()}!")

def start_borderless():
    """Fetch selected game from dropdown and apply borderless mode."""
    selected_game = game_var.get()
    if not selected_game:
        status_label.config(text="❌ No game selected!")
        return

    process_name = app_dict.get(selected_game)  # Get process name
    hwnd = find_window_by_process(process_name)

    if hwnd:
        make_borderless(hwnd)
    else:
        status_label.config(text="❌ No valid window found for this application!")

def refresh_list():
    """Refresh the dropdown list with active applications."""
    global app_dict
    app_dict = {title: process for title, process, hwnd in list_running_apps()}  # Update process list
    game_dropdown["values"] = list(app_dict.keys())  # Update dropdown options
    status_label.config(text="🔄 Application list updated!")

# GUI Setup
root = tk.Tk()
root.title("Border Terminator")
root.geometry("420x200")
root.configure(bg="#2c3e50")
root.attributes("-alpha", 0.95)  # Slight transparency effect

# Bootstrap theme
style = Style(theme="darkly")

# Main frame
frame = tk.Frame(root, bg="#2c3e50")
frame.pack(pady=10, expand=True)

# Header text
header_label = tk.Label(frame, text="Select an Application:", font=("Arial", 10, "bold"), bg="#2c3e50", fg="white")
header_label.pack(pady=(0, 2))

# Initialize app list
app_dict = {title: process for title, process, hwnd in list_running_apps()}
game_var = tk.StringVar()

# Drop-down menu
game_dropdown = ttk.Combobox(frame, textvariable=game_var, values=list(app_dict.keys()), state="readonly", width=38, bootstyle="primary")
game_dropdown.pack(pady=(0, 8))

# Refresh list button
refresh_button = tk.Button(frame, text="Refresh List", command=refresh_list, font=("Arial", 9, "bold"), bg="#2980b9", fg="white", relief="raised", padx=8, pady=4)
refresh_button.pack(pady=5)

# Apply button
start_button = ttk.Button(frame, text="Apply Borderless Mode", command=start_borderless, bootstyle="success", padding=(12, 6))
start_button.pack(pady=10)  # Missing pack before!

# Status label
status_label = tk.Label(root, text="", font=("Arial", 9), wraplength=400, bg="#2c3e50", fg="white")
status_label.pack()

root.mainloop()
