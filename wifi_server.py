import socket
from picarx import Picarx

HOST = "192.168.0.233"     
PORT = 65432          

SPEED = 30           
TURN_ANGLE = 30       

px = Picarx()
state = {"direction": "stop", "speed": 0}


def cpu_temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return round(int(f.read()) / 1000, 1)
    except Exception:
        return "n/a"


def stop_car():
    """Stop the motors using every method the library offers, then center steering."""
    for _ in range(2):                     
        for action in (
            lambda: px.stop(),
            lambda: px.forward(0),
            lambda: px.set_motor_speed(1, 0),
            lambda: px.set_motor_speed(2, 0),
        ):
            try:
                action()
            except Exception as e:
                print("stop step failed:", e)
    try:
        px.set_dir_servo_angle(0)
    except Exception as e:
        print("steering reset failed:", e)
    state.update(direction="stop", speed=0)


def handle_command(cmd):
    if cmd == "forward":
        px.set_dir_servo_angle(0)
        px.forward(SPEED)
        state.update(direction="forward", speed=SPEED)
    elif cmd == "backward":
        px.set_dir_servo_angle(0)
        px.backward(SPEED)
        state.update(direction="backward", speed=SPEED)
    elif cmd == "left":
        px.set_dir_servo_angle(-TURN_ANGLE)
        px.forward(SPEED)
        state.update(direction="left", speed=SPEED)
    elif cmd == "right":
        px.set_dir_servo_angle(TURN_ANGLE)
        px.forward(SPEED)
        state.update(direction="right", speed=SPEED)
    elif cmd == "stop":
        stop_car()

    return "direction: {} | speed: {} | cpu temp: {} C".format(
        state["direction"], state["speed"], cpu_temp())


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print("Listening on port", PORT)

    try:
        while True:
            client, clientInfo = s.accept()
            client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            print("connected:", clientInfo)
            buf = b""
            try:
                while True:
                    data = client.recv(1024)
                    if data == b"":
                        break                      
                    buf += data
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        cmd = line.decode().strip().lower()
                        if cmd:
                            print("command:", cmd)
                            reply = handle_command(cmd)
                            client.sendall((reply + "\n").encode())
            except ConnectionError:
                pass
            finally:
                stop_car()                      
                client.close()
                print("disconnected")
    except KeyboardInterrupt:
        print("Closing socket")
    finally:
        stop_car()
        s.close()