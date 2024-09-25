import cv2
import socket
import pickle
import struct
import torch
from tkinter import *
from PIL import Image, ImageTk


# 상태를 저장하는 전역 변수
is_running = False
cap = None  # 전역 변수로 웹캠 객체를 정의 (초기 값은 None)
# YOLOv5 모델 로드
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')  # GPU 사용 여부 확인
model = torch.hub.load('ultralytics/yolov5', 'custom', path='C:/Users/UserK/Desktop/Percept to AI/ai_df_6/gun_best.pt')
model.to(device)  # 모델을 GPU로 이동

# 소켓 생성 및 연결
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.10.90', 5555))  # 서버 IP 주소와 포트

data = b""  # 수신 데이터 초기화
payload_size = struct.calcsize("L")  # 메시지 크기를 위한 'L'의 크기

# YOLOv5 모델 로드
# model = torch.hub.load('ultralytics/yolov5', 'custom', path='/Users/choi/Desktop/pyworks/asd/yolov8parkingspace/best.pt')  # best.pt 경로 수정

# OpenCV에서/ 웹캠 영상 가져오기
def show_frames():
    while True:
        try:
            # 데이터가 payload_size보다 작을 때까지 수신
            while len(data) < payload_size:
                packet = client_socket.recv(4 * 1024)  # 4KB씩 수신
                if not packet:
                    break
                data += packet

            # 수신이 종료된 경우
            if not packet:
                break

            # 메시지 크기 추출
            msg_size = struct.unpack("L", data[:payload_size])[0]

            # msg_size보다 데이터가 작을 때까지 수신
            while len(data) < msg_size + payload_size:
                packet = client_socket.recv(4 * 1024)
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

                # YOLOv5 객체 탐지
                results = model(frame, size=640)  # 이미지 크기 조정 (속도 개선)

                # 탐지 결과를 이미지에 그리기
                frame_with_boxes = results.render()[0]

                # 클라이언트 화면에 이미지 표시
                cv2.imshow("Client Camera Feed", frame_with_boxes)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        except Exception as e:
            print(f"Error: {e}")
            break

    # 소켓 및 윈도우 종료
    client_socket.close()
    cv2.destroyAllWindows()


# 통신 실행 (웹캠 시작)
def start_video():
    global is_running, cap
    if not is_running:
        cap = cv2.VideoCapture(0)  # 웹캠을 연결
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # 웹캠 해상도 설정
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if not cap.isOpened():
            print("웹캠을 열 수 없습니다.")
            return
        is_running = True
        lbl_info.config(text="통신 상태: 정상")  # 상태 메시지 업데이트

# 영상을 멈추는 함수 (통신 중지)
def stop_video():
    global is_running, cap
    if is_running and cap is not None:
        is_running = False
        cap.release()  # 웹캠 장치 해제
        cap = None  # cap 객체를 해제 상태로 만듦
        lbl_info.config(text="통신 상태: 통신 대기중")  # 상태 메시지 업데이트

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

# 웹캠 크기 가져오기
cap = cv2.VideoCapture(0)
width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
cap.release()  # 영상 초기화 후 해제

# 영상 스트림을 표시하기 위한 함수 호출
show_frames()

# 윈도우 닫을 때 자원 해제
def on_closing():
    stop_video()  # 영상 중지
    window.destroy()  # 윈도우 종료

window.protocol("WM_DELETE_WINDOW", on_closing)

# Tkinter 루프 시작
window.mainloop()

# 작업이 끝나면 비디오 스트림 해제
if cap is not None and cap.isOpened():
    cap.release()
cv2.destroyAllWindows()
