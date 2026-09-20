"""Week 3 Day 2 Integrated Pipeline: Tracking -> Recognition -> Virtual Line -> Attendance Engine & HUD."""
import argparse
import sys
import os
import time
import threading
from pathlib import Path
import cv2
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.camera.source import VideoSource
from app.pipeline.frame_queue import FrameBuffer, BufferedFrame
from app.metrics.ingestion_metrics import IngestionMetrics
from app.tracking.tracker import ByteTrackTracker
from app.face.detector import FaceDetector
from app.face.quality import FaceQualityAssessor
from app.face.embedder import FaceEmbedder
from app.face.matcher import FaceMatcher
from app.identity.identity_manager import TemporalIdentityManager
from app.enrollment.registry import StudentRegistry
from app.attendance.attendance_engine import AttendanceEngine
from app.attendance.zone import VirtualLine

def build_attendance_hud(frame_w: int, metrics_data: dict, recent_events: list) -> np.ndarray:
    hud_h = 180
    hud = np.zeros((hud_h, frame_w, 3), dtype=np.uint8)
    hud[:] = (20, 20, 24)

    cv2.line(hud, (0, 0), (frame_w, 0), (0, 220, 255), 2)
    cv2.putText(
        hud,
        "AI VIDEO ATTENDANCE — WEEK 3: ATTENDANCE & IN/OUT ENGINE",
        (20, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 220, 255),
        2
    )

    col1_x = 25
    col2_x = max(frame_w // 3, 310)
    col3_x = max((frame_w // 3) * 2, 620)

    # Column 1: Occupancy & Status
    cv2.putText(hud, f"ROOM       : {metrics_data['location']}", (col1_x, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(hud, f"INSIDE NOW : {metrics_data['inside_count']} students", (col1_x, 82), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 120), 2)
    active_str = ", ".join(metrics_data['inside_list'][:3]) or "None"
    cv2.putText(hud, f"PRESENT    : {active_str}", (col1_x, 106), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    cv2.putText(hud, f"TOTAL EVTS : {metrics_data['total_events']}", (col1_x, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 210, 255), 1)

    # Column 2: Stream & Processing
    cv2.putText(hud, f"INPUT FPS  : {metrics_data['input_fps']:.1f}", (col2_x, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(hud, f"ENGINE FPS : {metrics_data['engine_fps']:.1f}  ({metrics_data['latency_ms']:.1f}ms)", (col2_x, 82), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(hud, f"TRACKS     : {metrics_data['active_tracks']} active", (col2_x, 106), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    cv2.putText(hud, f"QUEUE      : {metrics_data['queue_size']}/{metrics_data['max_queue']}", (col2_x, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 210, 255), 1)

    # Column 3: Live Audited Event Feed
    cv2.putText(hud, "AUDITED EVENT FEED:", (col3_x, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 210, 50), 1)
    if recent_events:
        for idx, evt in enumerate(reversed(recent_events[-3:])):
            dur_info = metrics_data.get('sessions', {}).get(evt.student_id, '')
            dur_str = f" [{dur_info}]" if dur_info else ""
            line = f"{evt.timestamp_iso[-8:]} {evt.student_id} -> {evt.direction}{dur_str}"
            evt_color = (0, 255, 120) if evt.direction == "IN" else (0, 160, 255)
            cv2.putText(hud, line, (col3_x, 82 + idx * 24), cv2.FONT_HERSHEY_SIMPLEX, 0.45, evt_color, 1)
    else:
        cv2.putText(hud, "Waiting for line crossing...", (col3_x, 82), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (130, 130, 130), 1)

    cv2.putText(hud, "Press 'q' or ESC to exit", (frame_w - 200, 165), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (110, 110, 110), 1)
    return hud

def main():
    default_video = Path(__file__).resolve().parent.parent / "data" / "videos" / "pedestrians_sample.mp4"

    parser = argparse.ArgumentParser(description="AI Video Attendance - Attendance & Event Engine")
    parser.add_argument("--source", type=str, default="webcam", help="'webcam' (or 0) for laptop camera, or path to MP4 video")
    parser.add_argument("--no-display", action="store_true", help="Run without UI window")
    parser.add_argument("--max-frames", type=int, default=-1, help="Max frames to process")
    args = parser.parse_args()

    if args.source == "webcam" or args.source == "0":
        src_target = 0
        src_label = "LAPTOP WEBCAM"
    else:
        src_target = args.source if os.path.isabs(args.source) or os.path.exists(args.source) else str(default_video)
        src_label = f"VIDEO ({Path(src_target).name})"

    print("=" * 65)
    print("  AI VIDEO ATTENDANCE — ATTENDANCE & IN/OUT EVENT ENGINE")
    print("=" * 65)
    print(f" Source      : {src_label} [{src_target}]")
    print("=" * 65)

    try:
        video_src = VideoSource(src_target, loop=True)
    except Exception as e:
        print(f"[ERROR] Failed to open video source: {e}")
        return

    buffer = FrameBuffer(max_size=30)
    metrics = IngestionMetrics(window_sec=3.0)
    
    # Initialize Engine Components
    tracker = ByteTrackTracker(model_name="yolov8n.pt", conf_thresh=0.35, device="cpu")
    face_detector = FaceDetector()
    quality_assessor = FaceQualityAssessor()
    embedder = FaceEmbedder(device="cpu")
    matcher = FaceMatcher()
    id_manager = TemporalIdentityManager(confirm_threshold=0.60, min_observations=2)
    registry = StudentRegistry()

    # Define Virtual Entry/Exit Line at 50% height of 720p/540p display
    line_y = 270
    door_line = VirtualLine(pt1=(30, line_y), pt2=(930, line_y), name="CLASSROOM_DOOR")
    attendance_engine = AttendanceEngine(
        camera_id="ENTRY_CAM_01",
        location_id="CLASSROOM_203",
        virtual_line=door_line
    )
    running = True

    def capture_worker():
        frame_counter = 0
        while running:
            ret, frame = video_src.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            frame_counter += 1
            now = time.perf_counter()
            metrics.record_input()

            pkt = BufferedFrame(
                frame_id=frame_counter,
                timestamp=now,
                frame=frame,
                source_name=src_label
            )
            buffer.put(pkt)

            if isinstance(src_target, str) and video_src.fps() > 0:
                time.sleep(1.0 / (video_src.fps() * 1.1))

    capture_thread = threading.Thread(target=capture_worker, name="CaptureWorker", daemon=True)
    capture_thread.start()

    consumed = 0
    display_w, display_h = 960, 540
    pipe_latency_ms = 0.0

    try:
        while running:
            pkt = buffer.get(timeout=0.05)
            now = time.perf_counter()

            if pkt is not None:
                orig_frame = pkt.frame
                start_proc = time.perf_counter()

                # Step 1: ByteTrack Multi-Person Tracking
                tracks, track_lat = tracker.update(orig_frame)

                # Step 2: Recognition & Line-Crossing
                for t in tracks:
                    x1, y1, x2, y2 = t.bbox
                    h, w = orig_frame.shape[:2]
                    person_crop = orig_frame[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]

                    faces = face_detector.detect_in_person_crop(person_crop, offset=(x1, y1))
                    matched_id = None
                    similarity = 0.0
                    reliability = 0.0

                    if faces:
                        best_face = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
                        quality_report = quality_assessor.assess(best_face.crop)
                        reliability = quality_report.overall_reliability

                        if quality_report.is_usable:
                            emb = embedder.extract(best_face.crop)
                            matches = matcher.search(emb, top_k=1)
                            if matches:
                                matched_id = matches[0].student_id
                                similarity = matches[0].similarity

                    decision = id_manager.update_track_evidence(
                        track_id=t.track_id,
                        candidate_id=matched_id,
                        similarity=similarity,
                        reliability=reliability
                    )

                    # Scale centroid to display coordinates for line crossing check
                    scale_x = display_w / orig_frame.shape[1]
                    scale_y = display_h / orig_frame.shape[0]
                    disp_cx = int(t.centroid[0] * scale_x)
                    disp_cy = int(t.centroid[1] * scale_y)

                    # Step 3: Attendance Line Crossing & Event Emission
                    event = attendance_engine.process_observation(
                        track_id=t.track_id,
                        student_id=decision.student_id,
                        centroid=(disp_cx, disp_cy),
                        confidence=decision.fused_score,
                        is_confirmed=(decision.state == "CONFIRMED")
                    )

                    # Badge color based on state
                    if decision.state == "CONFIRMED":
                        stud_name = registry.get(decision.student_id).name if registry.get(decision.student_id) else decision.student_id
                        sess = attendance_engine.duration_engine.get_session(decision.student_id)
                        dur_str = f" | {sess.current_duration_formatted}" if sess else ""
                        badge_color = (0, 255, 100)
                        label = f"ID:{t.track_id} | {decision.student_id} ({stud_name}){dur_str}"
                    elif decision.state == "TENTATIVE":
                        badge_color = (0, 200, 255)
                        label = f"ID:{t.track_id} | {decision.student_id or 'Searching'} | TENTATIVE"
                    else:
                        badge_color = (180, 180, 180)
                        label = f"ID:{t.track_id} | UNKNOWN"

                    cv2.rectangle(orig_frame, (x1, y1), (x2, y2), badge_color, 2)
                    cv2.putText(
                        orig_frame,
                        label,
                        (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.55,
                        badge_color,
                        2
                    )

                pipe_latency_ms = (time.perf_counter() - start_proc) * 1000.0
                metrics.record_processed(pipe_latency_ms)
                consumed += 1
                frame_to_show = orig_frame
            else:
                frame_to_show = np.zeros((display_h, display_w, 3), dtype=np.uint8)

            resized_frame = cv2.resize(frame_to_show, (display_w, display_h))

            # Draw Virtual Attendance Line on video
            cv2.line(resized_frame, door_line.pt1, door_line.pt2, (0, 140, 255), 2)
            cv2.putText(
                resized_frame,
                "--- VIRTUAL ATTENDANCE BOUNDARY (IN / OUT) ---",
                (door_line.pt1[0] + 160, line_y - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                (0, 140, 255),
                2
            )

            summary = attendance_engine.get_summary()
            metrics_payload = {
                "source_type": src_label,
                "location": attendance_engine.location_id,
                "inside_count": summary["inside_count"],
                "inside_list": summary["inside_students"],
                "total_events": summary["total_events"],
                "active_tracks": len(tracker.trajectory_history),
                "input_fps": metrics.input_fps,
                "engine_fps": metrics.process_fps,
                "latency_ms": pipe_latency_ms,
                "queue_size": buffer.size(),
                "max_queue": buffer.max_size,
                "sessions": summary["active_sessions"]
            }

            hud = build_attendance_hud(display_w, metrics_payload, attendance_engine.recent_events)
            canvas = np.vstack([resized_frame, hud])

            if not args.no_display:
                cv2.imshow("AI Attendance - In/Out Event Engine", canvas)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    break

            if args.max_frames > 0 and consumed >= args.max_frames:
                break

    finally:
        running = False
        capture_thread.join(timeout=1.0)
        video_src.release()
        if not args.no_display:
            cv2.destroyAllWindows()
        print(f"Attendance engine stopped. Total processed frames: {consumed}")

if __name__ == "__main__":
    main()
