from ultralytics import YOLO
import os

if __name__ == '__main__':
    # Load the model
    try:
        model = YOLO('yolo26s.pt')
    except:
        print("yolo26s.pt not found, using yolo11s.pt instead.")
        model = YOLO('yolo11s.pt')

    # Start training
    model.train(
        data='baseline1.v1-baseline1.yolov11/data.yaml',
        epochs=100,
        imgsz=640,
        device='cpu'  # <--- CHANGE THIS FROM 0 TO 'cpu'
    )