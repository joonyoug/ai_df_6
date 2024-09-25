import torch
import cv2
from yolov5.utils.general import non_max_suppression, scale_boxes

# YOLOv5 모델 로드 (로컬 best.pt 파일 사용)
model_path = '/Users/choi/Desktop/pyworks/asd/yolov8parkingspace/best1.pt'
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = torch.load(model_path, map_location=device)['model'].float()  # 모델 로드
model.to(device).eval()

# 동영상 파일 경로 설정
video_path = '/Users/choi/Desktop/pyworks/asd/yolov8parkingspace/부산MBC).mp4'

# 동영상 캡처 객체 생성
cap = cv2.VideoCapture(video_path)

# 동영상 재생 루프
while cap.isOpened():
    ret, frame = cap.read()

    if not ret:
        break  # 더 이상 프레임이 없으면 종료

    # 프레임 리사이즈 (640x640 또는 416x416 등으로 조정)
    img = cv2.resize(frame, (640, 640))  # 원하는 크기로 조정
    img = torch.from_numpy(img).to(device).float() / 255.0  # 이미지를 텐서로 변환
    img = img.permute(2, 0, 1).unsqueeze(0)  # (H, W, C) -> (C, H, W)로 변경하고 배치 차원 추가

    # 모델 예측
    pred = model(img)[0]
    pred = non_max_suppression(pred, 0.25, 0.45)  # NMS 적용

    # 결과를 프레임에 표시
    for det in pred:  # 감지된 객체에 대해
        if len(det):
            det[:, :4] = scale_boxes(img.shape[2:], det[:, :4], frame.shape).round()  # scale_boxes 사용

            for *xyxy, conf, cls in det:
                label = f'{int(cls)} {conf:.2f}'

                # 총기 인식 시 콘솔에 출력
                if int(cls) == 0:  # 총기 클래스 번호에 맞게 수정
                    print("총기 인식됨")

                # 바운딩 박스 그리기
                xyxy = [int(x) for x in xyxy]  # 좌표를 정수로 변환
                cv2.rectangle(frame, (xyxy[0], xyxy[1]), (xyxy[2], xyxy[3]), (0, 255, 0), 2)  # 바운딩 박스 그리기

                # 라벨 그리기
                cv2.putText(frame, label, (xyxy[0], xyxy[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # 화면에 출력
    cv2.imshow('Object Detection', frame)

    # 'q' 키를 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 리소스 해제
cap.release()
cv2.destroyAllWindows()
