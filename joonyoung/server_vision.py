import cv2
import socket
import pickle
import struct

# 소켓 생성 및 바인딩
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 5555))  # 모든 인터페이스에서 수신
server_socket.listen(5)
print("Server is listening...")

conn, addr = server_socket.accept()  # 클라이언트의 연결 대기
print(f"Connection from {addr} has been established!")

# 웹캠 초기화
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    conn.close()
    server_socket.close()
    exit(1)

while True:
    try:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        # 카메라 피드가 제대로 읽히고 있는지 출력
        cv2.imshow('Server Camera Feed', frame)

        data = pickle.dumps(frame)  # 프레임을 직렬화
        message_size = struct.pack("Q", len(data))  # 메시지 크기 패킹
        conn.sendall(message_size + data)  # 데이터 전송

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    except Exception as e:
        print(f"Error: {e}")
        break

cap.release()
conn.close()
server_socket.close()
cv2.destroyAllWindows()
