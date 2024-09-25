import cv2
import torch

# YOLOv5 모델 로드
model_path = '/Users/choi/Desktop/pyworks/asd/yolov8parkingspace/best.pt'
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, force_reload=True)

# CCTV 스트림 URL 설정
cctv_stream_url = 'rtsp://210.99.70.120:1935/live/cctv049.stream'

# 동영상 캡처 객체 생성
cap = cv2.VideoCapture(cctv_stream_url)

while True:
    ret, frame = cap.read()
    if not ret:
        print("프레임을 읽을 수 없습니다. 종료합니다.")
        break  # 더 이상 프레임이 없으면 종료

    # 입력 이미지를 YOLOv5에 맞는 크기로 조정
    img = cv2.resize(frame, (640, 640))  # 640x640으로 조정

    # YOLOv5로 객체 인식
    results = model(img)  # 모델을 프레임에 적용
    # 결과를 이미지로 변환
    img = results.render()[0]  # 첫 번째 이미지에 대한 결과 렌더링

    # 결과 이미지 표시
    cv2.imshow('CCTV Feed', img)

    # 총기가 인식되면 콘솔에 출력
    for *xyxy, conf, cls in results.xyxy[0]:
        if int(cls) == 0:  # 클래스 0이 총기라고 가정 (클래스 인덱스는 모델에 따라 다름)
            print("총기 인식됨!")

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 리소스 해제
cap.release()
cv2.destroyAllWindows()
