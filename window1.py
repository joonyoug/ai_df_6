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

# OpenCV에서 웹캠 영상 가져오기
def show_frames():
    global cap
    if is_running and cap is not None and cap.isOpened():
        # 웹캠에서 실시간 프레임을 가져오고, BGR에서 RGB로 색상 변환
        ret, cv2image = cap.read()
        if ret:
            cv2image = cv2.cvtColor(cv2image, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            imgtk = ImageTk.PhotoImage(image=img)

            # Tkinter Label에 영상 표시
            lbl_video.imgtk = imgtk
            lbl_video.configure(image=imgtk)
        else:
            print("프레임을 가져오는 데 실패했습니다.")
    else:
        # 웹캠 크기와 대기 이미지 크기를 맞추기 위해 리사이즈
        try:
            stop_img = Image.open("stop_image.png")
            stop_img = stop_img.resize((int(width), int(height)))  # 웹캠 크기로 리사이즈
            stop_img = ImageTk.PhotoImage(stop_img)
            lbl_video.imgtk = stop_img
            lbl_video.configure(image=stop_img)
        except FileNotFoundError:
            print("stop_image.png를 찾을 수 없습니다.")

    # 10ms마다 업데이트 (실시간 영상처럼 보이게 함)
    lbl_video.after(10, show_frames)

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
