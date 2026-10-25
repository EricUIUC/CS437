import socket
import threading
import queue
import tkinter as tk

HOST = "88:A2:9E:3A:62:9B"   
CHANNEL = 1                  

KEY_MAP = {
    "w": "forward",
    "a": "left",
    "s": "backward",
    "d": "right",
}

sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
sock.settimeout(10)
sock.connect((HOST, CHANNEL))
sock.settimeout(None)
print("connected to", HOST)

replies = queue.Queue()


def reader():
    """Read newline-separated status replies from the Pi."""
    buf = ""
    while True:
        try:
            data = sock.recv(1024)
        except OSError:
            break
        if not data:
            break
        buf += data.decode()
        lines = buf.split("\n")
        buf = lines.pop()
        for line in lines:
            if line.strip():
                replies.put(line.strip())
    replies.put("Disconnected from Pi")


def send_to_pi(message):
    try:
        sock.send((message + "\n").encode())
    except OSError:
        status_var.set("Not connected to Pi")


root = tk.Tk()
root.title("PiCar Remote (Bluetooth)")

tk.Label(root, text="PiCar Remote Control", font=("Arial", 18, "bold")).pack(pady=(15, 5))
tk.Label(root, text="Press W A S D (or click the buttons) to drive").pack()

tk.Label(root, text="Direction:").pack(pady=(15, 0))
direction_var = tk.StringVar(value="Stopped")
tk.Label(root, textvariable=direction_var, font=("Arial", 32)).pack(pady=5)

pad = tk.Frame(root)
pad.pack(pady=10)
buttons = {}
layout = {"w": (0, 1), "a": (1, 0), "s": (1, 1), "d": (1, 2)}
for k, (r, c) in layout.items():
    b = tk.Button(pad, text=k.upper(), width=5, height=2, font=("Arial", 16))
    b.grid(row=r, column=c, padx=4, pady=4)
    buttons[k] = b

status_var = tk.StringVar(value="Connected to Pi")
tk.Label(root, text="Server response:").pack(pady=(10, 0))
tk.Label(root, textvariable=status_var, fg="#555").pack(pady=(0, 15))

held = set()


def highlight(active_key):
    for k, b in buttons.items():
        b.config(bg="#4caf50" if k == active_key else "SystemButtonFace")


def press(key):
    direction = KEY_MAP[key]
    direction_var.set(direction)
    highlight(key)
    send_to_pi(direction)


def release():
    direction_var.set("Stopped")
    highlight(None)
    send_to_pi("stop")


def on_key_press(event):
    k = event.keysym.lower()
    if k in KEY_MAP and k not in held:     
        held.add(k)
        press(k)


def on_key_release(event):
    k = event.keysym.lower()
    if k in held:
        held.discard(k)
        release()


root.bind("<KeyPress>", on_key_press)
root.bind("<KeyRelease>", on_key_release)

for k, b in buttons.items():
    b.bind("<ButtonPress-1>", lambda e, k=k: press(k))
    b.bind("<ButtonRelease-1>", lambda e: release())


def poll_replies():
    while not replies.empty():
        status_var.set(replies.get())
    root.after(50, poll_replies)


def on_close():
    try:
        send_to_pi("stop")
        sock.close()
    except OSError:
        pass
    root.destroy()


root.protocol("WM_DELETE_WINDOW", on_close)
threading.Thread(target=reader, daemon=True).start()
poll_replies()
root.mainloop()