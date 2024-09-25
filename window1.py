import cv2
import socket
import pickle
import struct
import torch
from tkinter import *
from PIL import Image, ImageTk

is_running = False
cap = None  # 전역 변수로 웹캠 객체를 정의 (초기 값은 None)

# YOLOv5 모델 로드
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')  # GPU 사용 여부 확인
model = torch.hub.load('ultralytics/yolov5', 'custom', path='/Users/choi/Desktop/pyworks/asd/yolov8parkingspace/gun_best.pt')
model.to(device)  # 모델을 GPU로 이동

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# OpenCV에서 웹캠 영상 가져오기
def show_frames():
    global is_running
    data = b""  # 수신 데이터 초기화
    payload_size = struct.calcsize("L")  # 메시지 크기를 위한 'L'의 크기

    if is_running:
        try:
            # 데이터가 payload_size보다 작을 때까지 수신
            while len(data) < payload_size:
                packet = client_socket.recv(8 * 1024)  # 패킷 크기를 8KB로 변경
                if not packet:
                    break
                data += packet

            # 메시지 크기 추출
            msg_size = struct.unpack("L", data[:payload_size])[0]

            # msg_size보다 데이터가 작을 때까지 수신
            while len(data) < msg_size + payload_size:
                packet = client_socket.recv(8 * 1024)
                if not packet:
                    break
                data += packet

            # 메시지가 정상적으로 수신된 경우
            if len(data) >= msg_size + payload_size:
                # 이미지 데이터 추출
                frame_data = data[payload_size:msg_size + payload_size]
                data = data[msg_size + payload_size:]

                # 이미지 디코딩
                frame = pickle.loads(frame_data)

                # YOLOv5 객체 탐지 (이미지 크기 320으로 조정하여 성능 개선)
                results = model(frame, size=320)
                frame_with_boxes = results.render()[0]

                # PIL 이미지를 사용해 Tkinter Label에 표시
                img = Image.fromarray(cv2.cvtColor(frame_with_boxes, cv2.COLOR_BGR2RGB))
                imgtk = ImageTk.PhotoImage(image=img)
                lbl_video.imgtk = imgtk
                lbl_video.configure(image=imgtk)

        except Exception as e:
            print(f"Error: {e}")

        # 업데이트 간격을 30ms로 변경 (성능 개선)
        window.after(30, show_frames)

# 통신 실행 (웹캠 시작)
def start_video():
    global is_running
    is_running = True
    client_socket.connect(('192.168.10.90', 5555))  # 서버 IP 주소와 포트
    show_frames()

# 영상을 멈추는 함수 (통신 중지)
def stop_video():
    global is_running
    is_running = False
    client_socket.close()
    cv2.destroyAllWindows()

# Tkinter 윈도우 설정
window = Tk()
window.title("실시간 웹캠 영상")

# 레이아웃 설정
window.geometry("800x600")  # 윈도우 크기 설정

# 상단 가운데에 통신 관련 정보를 표시할 Label
lbl_info = Label(window, text="통신 상태: 통신 대기중", font=("Arial", 14))
lbl_info.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky=N)  # 상단 가운데 배치

# 좌측에 실시간 영상이 표시될 Label
lbl_video = Label(window)
lbl_video.grid(row=1, column=0, padx=10, pady=10, rowspan=2)  # 영상은 두 줄 크기로 좌측에 배치

# 가운데에 통신 실행 버튼과 스탑 버튼 배치
frame_buttons = Frame(window)
frame_buttons.grid(row=1, column=1, padx=10, pady=10, sticky=N)  # 가운데 배치

btn_start = Button(frame_buttons, text="통신 실행", command=start_video, font=("Arial", 12), width=10)
btn_start.pack(pady=5)  # 통신 실행 버튼

btn_stop = Button(frame_buttons, text="스탑", command=stop_video, font=("Arial", 12), width=10)
btn_stop.pack(pady=5)  # 스탑 버튼

# 윈도우 닫을 때 자원 해제
def on_closing():
    stop_video()  # 영상 중지
    window.destroy()  # 윈도우 종료

window.protocol("WM_DELETE_WINDOW", on_closing)

# Tkinter 루프 시작
window.mainloop()
