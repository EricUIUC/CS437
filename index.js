var server_port = 65432;
var server_addr = "192.168.0.233";   // the IP address of your Raspberry PI

// WASD -> direction name
const KEY_MAP = {
    w: "forward",
    a: "left",
    s: "backward",
    d: "right"
};

// ---------- UI (does not depend on networking) ----------
function show_status(text) {
    const el = document.getElementById("greet_from_server");
    if (el) el.innerHTML = text;
}

function set_direction(direction, key) {
    document.getElementById("direction").innerHTML = direction;
    document.querySelectorAll(".key").forEach(el => el.classList.remove("active"));
    if (key) {
        document.getElementById("key-" + key).classList.add("active");
    }
}

function press(key) {
    const direction = KEY_MAP[key];
    if (!direction) return;
    set_direction(direction, key);
    send_to_pi(direction);
}

function release() {
    set_direction("Stopped", null);
    send_to_pi("stop");
}

// keyboard handlers, registered immediately
window.addEventListener("keydown", (e) => {
    document.getElementById("last_key").innerHTML = e.key;
    if (e.repeat) return;
    press(e.key.toLowerCase());
});

window.addEventListener("keyup", (e) => {
    if (KEY_MAP[e.key.toLowerCase()]) release();
});

window.addEventListener("DOMContentLoaded", () => {
    Object.keys(KEY_MAP).forEach((k) => {
        const btn = document.getElementById("key-" + k);
        btn.addEventListener("mousedown", () => press(k));
        btn.addEventListener("mouseup", release);
        btn.addEventListener("mouseleave", () => {
            if (btn.classList.contains("active")) release();
        });
    });
});

// ---------- networking (one persistent connection to the Pi) ----------
let net = null;
let sock = null;
let connected = false;
let rxbuf = "";

try {
    net = require('net');
} catch (err) {
    window.addEventListener("DOMContentLoaded", () => {
        show_status("Networking unavailable: " + err.message);
    });
}

function connect() {
    if (!net) return;

    sock = net.createConnection({ port: server_port, host: server_addr }, () => {
        connected = true;
        sock.setNoDelay(true);
        show_status("Connected to Pi");
    });

    sock.on('data', (data) => {
        rxbuf += data.toString();
        let lines = rxbuf.split("\n");
        rxbuf = lines.pop();
        if (lines.length > 0) {
            show_status(lines[lines.length - 1]);
        }
    });

    sock.on('error', (err) => {
        show_status("Error: " + err.message);
    });

    sock.on('close', () => {
        connected = false;
        show_status("Disconnected, retrying...");
        setTimeout(connect, 1000);
    });
}

function send_to_pi(message) {
    if (!net) {
        show_status("Networking unavailable (require('net') failed)");
    } else if (connected) {
        sock.write(message + "\n");
    } else {
        show_status("Not connected to Pi");
    }
}

window.addEventListener("DOMContentLoaded", connect);