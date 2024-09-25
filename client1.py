import cv2
import socket
import pickle
import struct
import torch

# 소켓 생성 및 연결
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.10.90', 5555))  # 서버의 IP 주소로 변경

# YOLOv5 모델 로드
model = torch.hub.load('ultralytics/yolov5', 'custom', path='/Users/choi/Desktop/pyworks/asd/yolov8parkingspace/best.pt')  # best.pt 경로 수정

while True:
    # 메시지 크기 수신
    message_size = struct.calcsize("L")
    data = b""

    while len(data) < message_size:
        packet = client_socket.recv(4 * 1024)  # 4KB씩 수신
        if not packet:
            break
        data += packet

    if not data:
        break

    msg_size = struct.unpack("L", data[:message_size])[0]  # 메시지 크기 추출
    data = data[message_size:]

    # 모든 데이터 수신
    while len(data) < msg_size:
        packet = client_socket.recv(4 * 1024)
        if not packet:
            break
        data += packet

    frame_data = data[:msg_size]
    data = data[msg_size:]

    # 프레임 복원
    frame = pickle.loads(frame_data)

    # YOLOv5로 객체 인식
    results = model(frame)
    # 결과를 이미지로 변환
    img = results.render()[0]

    # 감지된 객체에 대해 처리
    for det in results.xyxy[0]:  # 감지된 객체의 좌표와 클래스를 반복
        x1, y1, x2, y2, conf, cls = det
        if int(cls) == 0:  # 총기 클래스 ID가 0이라고 가정
            print("총기 인식됨")  # 콘솔에 출력

    # 결과 이미지 표시
    cv2.imshow('Client Camera Feed', img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

client_socket.close()
cv2.destroyAllWindows()
