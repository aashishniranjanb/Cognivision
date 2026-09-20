"""Comprehensive Demo: Robust Identity + Virtual Classroom Boundary + Period Attendance + Exception Logging."""
import argparse
import sys
import os
import time
import threading
from pathlib import Path
from datetime import datetime
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
from app.enrollment.registry import StudentRegistry
from app.attendance.comprehensive_engine import ComprehensiveAttendanceEngine
from app.attendance.zone import VirtualLine

def draw_comprehensive_hud(frame_w: int, metrics: dict, engine: ComprehensiveAttendanceEngine) -> np.ndarray:
    hud_h = 200
    hud = np.zeros((hud_h, frame_w, 3), dtype=np.uint8)
    hud[:] = (20, 20, 24)

    cv2.line(hud, (0, 0), (frame_w, 0), (0, 220, 255), 2)
    cv2.putText(
        hud,
        "AI ATTENDANCE — ROBUST IDENTITY & PERIOD ENGINE",
        (20, 26),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 220, 255),
        2
    )

    c1 = 25
    c2 = max(frame_w // 3, 310)
    c3 = max((frame_w // 3) * 2, 620)

    # Column 1: Classroom Occupancy & Active Period
    cur_p = engine.schedule_manager.get_active_period(engine.classroom_id)
    p_name = f"{cur_p.period_id} ({cur_p.subject})" if cur_p else "Free Period"
    cv2.putText(hud, f"ROOM       : {engine.classroom_id}", (c1, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(hud, f"PERIOD     : {p_name}", (c1, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 215, 0), 1)
    inside_stus = [sid for sid, st in engine.state_machine.states.items() if st.current_status == "INSIDE"]
    cv2.putText(hud, f"INSIDE NOW : {len(inside_stus)} present", (c1, 104), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 120), 2)
    cv2.putText(hud, f"STUDENTS   : {', '.join(inside_stus[:3]) or 'None'}", (c1, 128), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    cv2.putText(hud, f"TOTAL EVTS : {len(engine.recent_events)}", (c1, 152), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 210, 255), 1)

    # Column 2: System Telemetry & Pipeline Performance
    cv2.putText(hud, f"SOURCE     : {metrics['source_type']}", (c2, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1)
    cv2.putText(hud, f"INPUT FPS  : {metrics['input_fps']:.1f}", (c2, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1)
    cv2.putText(hud, f"ENGINE FPS : {metrics['engine_fps']:.1f} ({metrics['latency_ms']:.1f}ms)", (c2, 104), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1)
    cv2.putText(hud, f"TRACKS     : {metrics['active_tracks']} active", (c2, 128), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (200, 200, 200), 1)
    cv2.putText(hud, f"QUEUE      : {metrics['queue_size']}/{metrics['max_queue']}", (c2, 152), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (160, 210, 255), 1)

    # Column 3: Live Audited Feed & Exception Monitor
    cv2.putText(hud, "LIVE AUDIT / EXCEPTION FEED:", (c3, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 210, 50), 1)
    feed_lines = []
    for evt in reversed(engine.recent_events[-2:]):
        dur = engine.duration_engine.get_session(evt.student_id)
        dstr = f" [{dur.current_duration_formatted}]" if dur else ""
        feed_lines.append((f"{evt.timestamp_iso[-8:]} {evt.student_id} -> {evt.direction}{dstr}", (0, 255, 120) if evt.direction=="IN" else (0, 160, 255)))
    for exc in reversed(engine.recent_exceptions[-2:]):
        t_str = datetime.fromtimestamp(exc.timestamp).strftime("%H:%M:%S")
        feed_lines.append((f"{t_str} [EXC] {exc.anomaly_type}", (0, 100, 255)))

    for idx, (line, color) in enumerate(feed_lines[:4]):
        cv2.putText(hud, line, (c3, 80 + idx * 24), cv2.FONT_HERSHEY_SIMPLEX, 0.44, color, 1)

    cv2.putText(hud, "Press 'q' or ESC to exit", (frame_w - 200, 185), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1)
    return hud

def main():
    default_video = Path(__file__).resolve().parent.parent / "data" / "videos" / "pedestrians_sample.mp4"

    parser = argparse.ArgumentParser(description="AI Attendance - Robust Identity & Period Engine")
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
    print("  AI VIDEO ATTENDANCE — ROBUST IDENTITY & PERIOD ENGINE")
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

    tracker = ByteTrackTracker(model_name="yolov8n.pt", conf_thresh=0.35, device="cpu")
    face_detector = FaceDetector()
    quality_assessor = FaceQualityAssessor()
    embedder = FaceEmbedder(device="cpu")
    matcher = FaceMatcher()
    registry = StudentRegistry()

    line_y = 270
    door_line = VirtualLine(pt1=(30, line_y), pt2=(930, line_y), name="CLASSROOM_DOOR")
    engine = ComprehensiveAttendanceEngine(
        camera_id="ENTRY_CAM_01",
        classroom_id="CLASSROOM_203",
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
            metrics.record_input()
            pkt = BufferedFrame(frame_id=frame_counter, timestamp=time.perf_counter(), frame=frame, source_name=src_label)
            buffer.put(pkt)

            if isinstance(src_target, str) and video_src.fps() > 0:
                time.sleep(1.0 / (video_src.fps() * 1.1))

    capture_thread = threading.Thread(target=capture_worker, name="CaptureWorker", daemon=True)
    capture_thread.start()

    consumed = 0
    display_w, display_h = 960, 540
    latency_ms = 0.0

    try:
        while running:
            pkt = buffer.get(timeout=0.05)
            if pkt is not None:
                orig_frame = pkt.frame
                start_proc = time.perf_counter()

                tracks, _ = tracker.update(orig_frame)

                for t in tracks:
                    x1, y1, x2, y2 = t.bbox
                    h, w = orig_frame.shape[:2]
                    person_crop = orig_frame[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]

                    faces = face_detector.detect_in_person_crop(person_crop, offset=(x1, y1))
                    cand_id = None
                    sim = 0.0
                    rel = 0.0

                    if faces:
                        best_face = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
                        q_rep = quality_assessor.assess(best_face.crop)
                        rel = q_rep.overall_reliability

                        if q_rep.is_usable:
                            emb = embedder.extract(best_face.crop)
                            matches = matcher.search(emb, top_k=1)
                            if matches:
                                cand_id = matches[0].student_id
                                sim = matches[0].similarity

                    # Calculate display-scaled centroid
                    disp_cx = int(t.centroid[0] * (display_w / orig_frame.shape[1]))
                    disp_cy = int(t.centroid[1] * (display_h / orig_frame.shape[0]))

                    # Process through Robust Engine
                    status, confirmed_id, evt = engine.process_frame_observation(
                        track_id=t.track_id,
                        raw_face_candidate_id=cand_id,
                        face_similarity=sim,
                        face_reliability=rel,
                        centroid=(disp_cx, disp_cy)
                    )

                    # Badge styling
                    if status == "CONFIRMED":
                        stud_name = registry.get(confirmed_id).name if registry.get(confirmed_id) else confirmed_id
                        sess = engine.duration_engine.get_session(confirmed_id)
                        dur_str = f" | {sess.current_duration_formatted}" if sess else ""
                        color = (0, 255, 100)
                        badge = f"ID:{t.track_id} | {confirmed_id} ({stud_name}){dur_str}"
                    elif status == "TENTATIVE":
                        color = (0, 200, 255)
                        badge = f"ID:{t.track_id} | {confirmed_id or 'Acquiring...'} | TENTATIVE"
                    elif status == "UNCERTAIN":
                        color = (0, 140, 255)
                        badge = f"ID:{t.track_id} | UNCERTAIN"
                    else:
                        color = (160, 160, 160)
                        badge = f"ID:{t.track_id} | UNKNOWN"

                    cv2.rectangle(orig_frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(orig_frame, badge, (x1, max(y1 - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.52, color, 2)

                latency_ms = (time.perf_counter() - start_proc) * 1000.0
                metrics.record_processed(latency_ms)
                consumed += 1
                frame_to_show = orig_frame
            else:
                frame_to_show = np.zeros((display_h, display_w, 3), dtype=np.uint8)

            resized_frame = cv2.resize(frame_to_show, (display_w, display_h))

            # Virtual Line overlay
            cv2.line(resized_frame, door_line.pt1, door_line.pt2, (0, 140, 255), 2)
            cv2.putText(
                resized_frame,
                "--- VIRTUAL CLASSROOM BOUNDARY (IN / OUT) ---",
                (door_line.pt1[0] + 160, line_y - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.52,
                (0, 140, 255),
                2
            )

            metrics_payload = {
                "source_type": src_label,
                "input_fps": metrics.input_fps,
                "engine_fps": metrics.process_fps,
                "latency_ms": latency_ms,
                "active_tracks": len(tracker.trajectory_history),
                "queue_size": buffer.size(),
                "max_queue": buffer.max_size
            }

            hud = draw_comprehensive_hud(display_w, metrics_payload, engine)
            canvas = np.vstack([resized_frame, hud])

            if not args.no_display:
                cv2.imshow("AI Attendance - Robust Identity & Period Engine", canvas)
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
        print(f"Engine stopped. Total frames: {consumed}")

if __name__ == "__main__":
    main()
