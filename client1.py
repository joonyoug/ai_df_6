import cv2
import socket
import pickle
import struct
import torch

# YOLOv5 모델 로드
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')  # GPU 사용 여부 확인
model = torch.hub.load('ultralytics/yolov5', 'custom', path='/Users/choi/Desktop/pyworks/asd/yolov8parkingspace/gun_best.pt')
model.to(device)  # 모델을 GPU로 이동

# 소켓 생성 및 연결
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.10.90', 5555))  # 서버 IP 주소와 포트

data = b""  # 수신 데이터 초기화
payload_size = struct.calcsize("L")  # 메시지 크기를 위한 'L'의 크기

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
