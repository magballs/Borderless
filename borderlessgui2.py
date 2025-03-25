import time
import win32gui
import win32con
import win32process
import psutil
import ctypes
import logging
from ttkbootstrap import Style
import tkinter as tk
from tkinter import ttk

# Introduce logging features
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("border_terminator.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

user32 = ctypes.windll.user32

SUPPORTED_RESOLUTIONS = {
    "16:9": ["1920x1080", "2560x1440", "3840x2160"],
    "21:9": ["2560x1080", "3440x1440"],
    "32:9": ["5120x1440"],
}

ALL_RESOLUTIONS = sum(SUPPORTED_RESOLUTIONS.values(), [])


def list_running_apps():
    """Returns a list of currently running applications with visible windows."""
    logging.info("Scanning for applications...")
    apps = []

    def callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):  # Only include visible windows
            title = win32gui.GetWindowText(hwnd).strip()
            if title:
                try:
                    pid = win32process.GetWindowThreadProcessId(hwnd)[1]
                    process_name = (
                        psutil.Process(pid).name() if pid else "Unknown Process"
                    )
                    apps.append(
                        (title, process_name, hwnd)
                    )  # Store title, process name, and handle
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

    win32gui.EnumWindows(callback, None)

    # Sort and remove duplicates
    unique_apps = {}
    for title, process, hwnd in apps:
        if process not in unique_apps:
            unique_apps[process] = (title, process, hwnd)

    logging.info(f"Found {len(unique_apps)} unique applications.")
    return list(unique_apps.values())


def find_window_by_process(process_name):
    """Finds the first window handle for the given process name."""
    logging.info(f"Looking for window with process name: {process_name}")
    for title, process, hwnd in list_running_apps():
        if process.lower() == process_name.lower():
            logging.info(f"Found window handle {hwnd} for process '{process_name}'")
            return hwnd
    logging.warning(f"No window found for process '{process_name}'")
    return None


def make_borderless(hwnd):
    """Remove the title bar and borders from the selected window."""
    if not hwnd:
        logging.error("❌ Window handle is invalid!")
        status_label.config(text="Window handle invalid!")
        return
    try:
        # Gather window info
        title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process_name = psutil.Process(pid).name()
        logging.info(
            f"🪟 Applying borderless mode to: {title} [{process_name}] (PID: {pid})"
        )

        # Get resolution from user selection
        selected_res = resolution_var.get()
        try:
            target_width, target_height = map(int, selected_res.split("x"))
        except ValueError:
            logging.error(f"Invalid resolution selected: {selected_res}")
            status_label.config(text="❌ Invalid resolution selected!")
            return

        logging.info(f"🖥️ Target Resolution: {target_width}x{target_height}")

        # Style manipulation
        original_style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        new_style = original_style & ~(win32con.WS_CAPTION | win32con.WS_THICKFRAME)
        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, new_style)
        confirmed_style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)

        original_exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        new_ex_style = original_exstyle & ~(
            win32con.WS_EX_DLGMODALFRAME
            | win32con.WS_EX_WINDOWEDGE
            | win32con.WS_EX_CLIENTEDGE
            | win32con.WS_EX_STATICEDGE
        )

        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, new_ex_style)
        confirmed_exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

        logging.debug(f"Style change: {original_style:#010x} → {confirmed_style:#010x}")
        logging.debug(
            f"ExStyle change: {original_exstyle:#010x} → {confirmed_exstyle:#010x}"
        )

        if confirmed_style != new_style or confirmed_exstyle != new_ex_style:
            logging.warning("⚠️ Style changes may not have been applied correctly.")
            status_label.config(
                text="⚠️ Borderless mode may not have been fully applied."
            )
        else:
            logging.info("✅ Style changes confirmed.")

        # DPI Awareness (optional)
        try:
            awareness = ctypes.c_int()
            ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
            logging.info(f"🔍 DPI Awareness Level: {awareness.value}")
        except Exception:
            logging.warning("Unable to retrieve DPI awareness.")

        SCREEN_WIDTH = user32.GetSystemMetrics(0)
        SCREEN_HEIGHT = user32.GetSystemMetrics(1)

        X_POS = (SCREEN_WIDTH - TARGET_WIDTH) // 2
        Y_POS = 0

        win32gui.SetWindowPos(
            hwnd,
            None,
            X_POS,
            Y_POS,
            TARGET_WIDTH,
            TARGET_HEIGHT,
            win32con.SWP_FRAMECHANGED | win32con.SWP_NOZORDER | win32con.SWP_SHOWWINDOW,
        )

        rect = win32gui.GetWindowRect(hwnd)
        applied_width = rect[2] - rect[0]
        applied_height = rect[3] - rect[1]
        logging.info(
            f"📐 Applied Window Size: {applied_width}x{applied_height} at ({rect[0]}, {rect[1]})"
        )

        if applied_width != target_width or applied_height != target_height:
            logging.warning(
                "⚠️ Window size mismatch! Actual size does not match target."
            )
        else:
            logging.info("✅ Window size confirmed.")

        status_label.config(text=f"🚀 Applied borderless mode to {game_var.get()}!")

    except Exception as e:
        logging.exception("❌ Failed to apply borderless mode.")
        status_label.config(text="❌ An unexpected error occurred!")


def start_borderless():
    """Fetch selected game from dropdown and apply borderless mode."""
    selected_game = game_var.get()
    logging.info(f"Selected game: {selected_game}")
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
    logging.info("Refreshing application list...")
    global app_dict
    app_dict = {
        title: process for title, process, hwnd in list_running_apps()
    }  # Update process list
    game_dropdown["values"] = list(app_dict.keys())  # Update dropdown options
    status_label.config(text="🔄 Application list updated!")


# GUI Setup
root = tk.Tk()
root.title("Border Terminator")
root.geometry("420x250")
root.configure(bg="#2c3e50")
root.attributes("-alpha", 0.95)  # Slight transparency effect

# Bootstrap theme
style = Style(theme="darkly")

# Main frame
frame = tk.Frame(root, bg="#2c3e50")
frame.pack(pady=10, expand=True)

# Header text
header_label = tk.Label(
    frame,
    text="Select an Application:",
    font=("Arial", 10, "bold"),
    bg="#2c3e50",
    fg="white",
)
header_label.pack(pady=(0, 2))

# Initialize app list
app_dict = {title: process for title, process, hwnd in list_running_apps()}
game_var = tk.StringVar()

resolution_var = tk.StringVar(value="2560x1440")  # Default resolution


# Drop-down menu
game_dropdown = ttk.Combobox(
    frame,
    textvariable=game_var,
    values=list(app_dict.keys()),
    state="readonly",
    width=38,
    bootstyle="primary",
)
game_dropdown.pack(pady=(0, 8))

# Resolution dropdown
resolution_dropdown = ttk.Combobox(
    frame,
    textvariable=resolution_var,
    values=ALL_RESOLUTIONS,
    state="readonly",
    width=38,
    bootstyle="info",
)
resolution_dropdown.pack(pady=(0, 8))

# Refresh list button
refresh_button = tk.Button(
    frame,
    text="Refresh List",
    command=refresh_list,
    font=("Arial", 9, "bold"),
    bg="#2980b9",
    fg="white",
    relief="raised",
    padx=8,
    pady=4,
)
refresh_button.pack(pady=5)

# Apply button
start_button = ttk.Button(
    frame,
    text="Apply Borderless Mode",
    command=start_borderless,
    bootstyle="success",
    padding=(12, 6),
)
start_button.pack(pady=10)  # Missing pack before!

# Status label
status_label = tk.Label(
    root, text="", font=("Arial", 9), wraplength=400, bg="#2c3e50", fg="white"
)
status_label.pack()

root.mainloop()
