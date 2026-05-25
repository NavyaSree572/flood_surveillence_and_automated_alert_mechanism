import os

label_dirs = [
    "baseline1.v1-baseline1.yolov11/train/labels",
    "baseline1.v1-baseline1.yolov11/valid/labels",
    "baseline1.v1-baseline1.yolov11/test/labels"
]

removed = 0

for dir in label_dirs:
    if not os.path.exists(dir):
        continue

    for file in os.listdir(dir):
        path = os.path.join(dir, file)

        with open(path, "r") as f:
            content = f.read().strip()

        if content == "":
            os.remove(path)
            removed += 1
            print(f"Deleted empty label: {file}")

print(f"\nTotal removed: {removed}")