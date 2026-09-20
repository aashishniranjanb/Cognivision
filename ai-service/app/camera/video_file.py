import cv2
import time
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_VIDEO = BASE_DIR / "data" / "videos" / "test_video.mp4"

def main(video_path: str = str(DEFAULT_VIDEO)):
    print(f"Opening recorded video: {video_path}")
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    source_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"Resolution : {width}x{height}")
    print(f"Source FPS : {source_fps:.1f}")
    print(f"Total Frames: {total_frames} (~{total_frames/source_fps:.1f}s)")
    print("Playing video. Press 'q' to exit.")

    frame_count = 0
    start_time = time.perf_counter()

    while True:
        ret, frame = cap.read()

        if not ret:
            # Loop back to beginning for continuous demonstration
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            if not ret:
                break

        frame_count += 1

        elapsed = time.perf_counter() - start_time
        processing_fps = frame_count / elapsed if elapsed > 0 else 0

        cv2.putText(
            frame,
            f"Recorded Video | FPS: {processing_fps:.1f}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"Resolution: {width}x{height}",
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2
        )

        cv2.imshow("AI Attendance - Video", frame)

        # Match replay speed approximately with source fps
        delay = max(1, int(1000 / source_fps))
        if cv2.waitKey(delay) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
