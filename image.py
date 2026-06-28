import cv2
import os

name = input("Enter Name: ").strip()
roll_no = input("Enter Roll Number: ").strip()

# Folder name: RollNo_Name
folder_name = f"{roll_no}_{name}"
path = os.path.join("dataset", folder_name)

os.makedirs(path, exist_ok=True)

cap = cv2.VideoCapture(0)

count = 0

while count < 100:
    ret, frame = cap.read()

    if not ret:
        print("Cannot read camera")
        break

    cv2.imshow("Capture Faces", frame)

    # Save images as 1.jpg, 2.jpg, ...
    img_path = os.path.join(path, f"{count + 1}.jpg")
    cv2.imwrite(img_path, frame)

    print(f"Saved {img_path}")
    count += 1

    # Capture every 100 ms
    cv2.waitKey(100)

    # Press 'q' to stop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print("Images Saved Successfully!")