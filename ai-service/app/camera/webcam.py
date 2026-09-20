import cv2
import time


def main():
    print("Opening laptop webcam (index 0)...")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise RuntimeError("Could not open laptop webcam")

    frame_count = 0
    start_time = time.perf_counter()

    print("Webcam active. Press 'q' on the window to exit.")

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Failed to read frame")
            break

        frame_count += 1

        elapsed = time.perf_counter() - start_time
        fps = frame_count / elapsed if elapsed > 0 else 0

        cv2.putText(
            frame,
            f"Webcam | FPS: {fps:.1f}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        cv2.imshow("AI Attendance - Webcam", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
