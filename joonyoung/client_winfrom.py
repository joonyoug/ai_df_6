import cv2
import socket
import pickle
import struct
import torch
from tkinter import *
from PIL import Image, ImageTk
import threading
import queue
import time

is_running = False
frame_queue = queue.Queue()  # 프레임을 담을 큐
socket_lock = threading.Lock()  # 소켓을 위한 Lock

# YOLOv5 모델 로드
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = torch.hub.load('ultralytics/yolov5', 'custom', path='/Users/choi/Desktop/pyworks/asd/yolov8parkingspace/gun_best.pt')
model.to(device)

def create_socket():
    """새로운 소켓을 생성하여 반환합니다."""
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 데이터를 수신하는 스레드
def receive_frames(client_socket):
    global is_running
    data = b""  # 수신 데이터 초기화
    payload_size = struct.calcsize("L")  # 메시지 크기를 위한 'L'의 크기

    try:
        while is_running:
            while len(data) < payload_size:
                packet = client_socket.recv(4 * 1024)  # 4KB씩 수신
                if not packet:
                    return
                data += packet

            msg_size = struct.unpack("L", data[:payload_size])[0]

            while len(data) < msg_size + payload_size:
                packet = client_socket.recv(4 * 1024)
                if not packet:
                    return
                data += packet

            if len(data) >= msg_size + payload_size:
                frame_data = data[payload_size:msg_size + payload_size]
                data = data[msg_size + payload_size:]

                frame = pickle.loads(frame_data)

                if frame_queue.qsize() < 10:  # 큐가 너무 커지지 않도록 제한
                    frame_queue.put(frame)

    except Exception as e:
        print(f"Error in receiving frames: {e}")
        is_running = False

# 객체 탐지 및 화면 업데이트 (메인 스레드에서 실행)
def show_frames():
    if not frame_queue.empty():
        try:
            frame = frame_queue.get()
            results = model(frame, size=640)
            frame_with_boxes = results.render()[0]

            img = Image.fromarray(cv2.cvtColor(frame_with_boxes, cv2.COLOR_BGR2RGB))
            imgtk = ImageTk.PhotoImage(image=img)
            lbl_video.imgtk = imgtk
            lbl_video.configure(image=imgtk)

        except Exception as e:
            print(f"Error in processing frames: {e}")

    if is_running:
        window.after(10, show_frames)

# 통신 실행 (웹캠 시작)
def start_video():
    global is_running
    with socket_lock:
        if is_running:
            return

        is_running = True
        client_socket = create_socket()  # 새로운 소켓 생성

        try:
            client_socket.connect(('192.168.10.90', 5555))  # 서버 IP 주소와 포트
        except OSError as e:
            print(f"Socket connection error: {e}")
            is_running = False
            return

        # 프레임 수신 스레드 시작
        threading.Thread(target=receive_frames, args=(client_socket,), daemon=True).start()

    show_frames()

# 영상을 멈추는 함수 (통신 중지)
def stop_video():
    global is_running
    with socket_lock:
        if not is_running:
            return

        is_running = False
        # 여기서는 소켓을 클로즈하지 않음, 소켓은 스레드 안에서 닫힘
        cv2.destroyAllWindows()

# Tkinter 윈도우 설정
window = Tk()
window.title("실시간 웹캠 영상")
window.geometry("800x600")

lbl_video = Label(window)
lbl_video.grid(row=1, column=0, padx=10, pady=10, rowspan=2)

frame_buttons = Frame(window)
frame_buttons.grid(row=1, column=1, padx=10, pady=10, sticky=N)

btn_start = Button(frame_buttons, text="통신 실행", command=start_video, font=("Arial", 12), width=10)
btn_start.pack(pady=5)

btn_stop = Button(frame_buttons, text="스탑", command=stop_video, font=("Arial", 12), width=10)
btn_stop.pack(pady=5)

def on_closing():
    stop_video()
    window.destroy()

window.protocol("WM_DELETE_WINDOW", on_closing)
window.mainloop()
