import cv2
import socket
import pickle
import struct
import torch
from tkinter import *
from PIL import Image, ImageTk
import threading
import queue
import yaml  # YAML 모듈 임포트
from sms_sender import SMSSender  # SMS 모듈 임포트
import serial

# YAML 파일에서 설정 읽기
with open("/Users/choi/Desktop/pyworks/asd/yolov8parkingspace/api.yaml", "r") as file:
    config = yaml.safe_load(file)

is_running = False
frame_queue = queue.Queue()  # 프레임을 담을 큐
socket_lock = threading.Lock()  # 소켓을 위한 Lock

# YOLOv5 모델 로드
device = torch.device('mps' if torch.backends.mps.is_available() else 'cpu')
model = torch.hub.load('ultralytics/yolov5', 'custom', path='/Users/choi/Desktop/pyworks/asd/yolov8parkingspace/gun_best.pt')
model.to(device)

# Vonage SMS Sender 초기화
sms_sender = SMSSender(key=config['vonage']['key'], secret=config['vonage']['secret'])


arduino = serial.Serial('/dev/cu.usbserial-110', 9600, timeout=1)

# 메시지 전송 여부를 확인하는 변수
message_sent = False

def create_socket():
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 데이터를 수신하는 스레드
def receive_frames(client_socket):
    global is_running
    data = b""
    payload_size = struct.calcsize("L")

    try:
        while is_running:
            while len(data) < payload_size:
                packet = client_socket.recv(4 * 1024)
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

                if frame_queue.qsize() < 10:
                    frame_queue.put(frame)

    except Exception as e:
        print(f"프레임 수신 중 오류: {e}")
        is_running = False

# 객체 탐지 및 화면 업데이트
def show_frames():
    global message_sent, signal_sent  # 메시지 전송 여부를 확인하기 위해 전역 변수 사용

    if not frame_queue.empty():
        try:
            frame = frame_queue.get()
            results = model(frame, size=640)

            detections = results.xyxy[0]
            for *box, conf, cls in detections:
                if conf >= 0.8:
                    if not message_sent:
                        # SMS 전송
                        sms_sender.send_sms("+821083988226", "An incident has occurred!!!!\n")
                        message_sent = True  # 메시지를 전송한 상태로 변경
                        arduino.write(b'1')

                    cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (255, 0, 0), 2)

            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            imgtk = ImageTk.PhotoImage(image=img)
            lbl_video.imgtk = imgtk
            lbl_video.configure(image=imgtk)

        except Exception as e:
            print(f"프레임 처리 중 오류: {e}")

    if is_running:
        window.after(10, show_frames)

# 상태 업데이트 함수
def update_status(message, color):
    lbl_status.config(text=message, fg=color)
    window.update_idletasks()

# 통신 실행
def start_video():
    global is_running, message_sent, signal_sent
    message_sent = False  # 새로 시작할 때 메시지 전송 여부 초기화
    signal_sent = False  # 신호 전송 여부 초기화

    with socket_lock:
        if is_running:
            return

        is_running = True
        client_socket = create_socket()

        try:
            client_socket.connect(('192.168.10.90', 5555))
            update_status("상태: 연결 중...", "#FFD700")
        except OSError as e:
            print(f"소켓 연결 오류: {e}")
            update_status("상태: 연결 실패", "#FF0000")
            is_running = False
            return

        threading.Thread(target=receive_frames, args=(client_socket,), daemon=True).start()

    update_status("상태: 연결됨", "#00FF00")
    show_frames()

def on_closing():
    stop_video()
    window.destroy()

def test_led():
    arduino.write(b'2')  # 아두이노에 신호 보내기


# 영상을 멈추는 함수
def stop_video():
    global is_running
    with socket_lock:
        if not is_running:
            return

        is_running = False
        update_status("상태: 중지됨", "#FF0000")
        cv2.destroyAllWindows()

# Tkinter 윈도우 설정
window = Tk()
window.title("총감지")
window.geometry("800x600")
window.eval('tk::PlaceWindow . center')
window.geometry("+{0}+{1}".format(int(window.winfo_screenwidth()/2 - 400), int(window.winfo_screenheight()/2 - 300)))
window.configure(bg='#282C34')

lbl_video = Label(window, bg='#ABB2BF')
lbl_video.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

frame_buttons = Frame(window, bd=2, relief="solid", padx=10, pady=10, bg='#282C34')
frame_buttons.grid(row=0, column=1, padx=10, pady=10, sticky="n")

btn_start = Button(frame_buttons, text="통신 실행", command=start_video, font=("Arial", 12, 'bold'), width=15, bg='#98C379', fg='#000000')
btn_start.pack(pady=5)

btn_stop = Button(frame_buttons, text="스탑", command=stop_video, font=("Arial", 12, 'bold'), width=15, bg='#E06C75', fg='#000000')
btn_stop.pack(pady=5)

btn_test = Button(frame_buttons, text="테스트", command=test_led, font=("Arial", 12, 'bold'), width=15, bg='#D19A66', fg='#000000')
btn_test.pack(pady=5)

btn_exit = Button(frame_buttons, text="종료", command=on_closing, font=("Arial", 12, 'bold'), width=15, bg='#D19A66', fg='#000000')
btn_exit.pack(pady=5)

lbl_status = Label(window, text="상태: 준비", font=("Arial", 10), bg='#282C34', fg='white')
lbl_status.grid(row=2, column=0, columnspan=2, sticky="w", padx=10, pady=5)

window.protocol("WM_DELETE_WINDOW", on_closing)
window.grid_rowconfigure(0, weight=1)
window.grid_columnconfigure(0, weight=1)

window.mainloop()
