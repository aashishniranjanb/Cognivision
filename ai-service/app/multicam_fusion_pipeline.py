"""Week 4 Integrated Dual-Camera Multimodal Attendance Engine: Entry + Exit Cameras with Adaptive Fusion."""
import argparse
import sys
import os
import time
from pathlib import Path
from datetime import datetime
import cv2
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.camera.source import VideoSource
from app.tracking.tracker import ByteTrackTracker
from app.face.detector import FaceDetector
from app.face.quality import FaceQualityAssessor
from app.face.embedder import FaceEmbedder
from app.face.matcher import FaceMatcher
from app.reid.extractor import BodyEmbedder
from app.reid.quality import BodyQualityAssessor
from app.reid.matcher import BodyMatcher
from app.fusion.observation import ModalityObservation
from app.fusion.adaptive_fusion import AdaptiveFusionEngine
from app.multicam.coordinator import MultiCameraCoordinator
from app.attendance.event import AttendanceEvent
from app.attendance.zone import VirtualLine, LineCrossingDetector
from app.enrollment.registry import StudentRegistry

class CameraStreamWorker:
    def __init__(self, camera_id: str, location_id: str, source_path: str, line_y: int = 200, direction_type: str = "IN"):
        self.camera_id = camera_id
        self.location_id = location_id
        self.source_path = source_path
        self.direction_type = direction_type
        self.video_src = VideoSource(source_path, loop=True)
        self.tracker = ByteTrackTracker(model_name="yolov8n.pt", conf_thresh=0.35, device="cpu")
        self.door_line = VirtualLine(pt1=(20, line_y), pt2=(460, line_y), name=f"{camera_id}_LINE")
        self.crossing_detector = LineCrossingDetector(self.door_line, cooldown_seconds=4.0)

def draw_dual_cam_hud(canvas_w: int, coord: MultiCameraCoordinator, fusion_audit: list) -> np.ndarray:
    hud_h = 200
    hud = np.zeros((hud_h, canvas_w, 3), dtype=np.uint8)
    hud[:] = (20, 20, 24)

    cv2.line(hud, (0, 0), (canvas_w, 0), (0, 220, 255), 2)
    cv2.putText(
        hud,
        "AI ATTENDANCE — WEEK 4: MULTI-CAMERA DUAL STREAM & ADAPTIVE FUSION",
        (20, 26),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 220, 255),
        2
    )

    c1 = 25
    c2 = max(canvas_w // 3, 310)
    c3 = max((canvas_w // 3) * 2, 620)

    summary = coord.get_summary()

    # Column 1: Global Presence State
    cv2.putText(hud, f"ROOM       : CLASSROOM_203", (c1, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1)
    cv2.putText(hud, f"INSIDE NOW : {summary['inside_count']} students", (c1, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 120), 2)
    in_str = ", ".join(summary['inside_students'][:3]) or "None"
    cv2.putText(hud, f"PRESENT    : {in_str}", (c1, 104), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (200, 200, 200), 1)
    cv2.putText(hud, f"EXITED     : {summary['exited_count']} students", (c1, 128), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (160, 210, 255), 1)
    cv2.putText(hud, f"TOTAL EVTS : {summary['total_events']}", (c1, 152), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 215, 0), 1)

    # Column 2: Adaptive Fusion Weights & Audit
    cv2.putText(hud, "ADAPTIVE FUSION WEIGHTS:", (c2, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 215, 0), 1)
    if fusion_audit:
        last_f = fusion_audit[-1]
        w_dict = last_f.get("weights", {})
        w_str = " | ".join([f"{m.upper()}: {w*100:.1f}%" for m, w in w_dict.items()])
        cv2.putText(hud, f"Active Weights: {w_str}", (c2, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 255, 120), 1)
        cv2.putText(hud, f"Last Decision : {last_f.get('decision')} ({last_f.get('confidence', 0):.2f})", (c2, 104), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 1)
    else:
        cv2.putText(hud, "Waiting for multi-modal observation...", (c2, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (140, 140, 140), 1)

    # Column 3: Reconciled Global Event Feed
    cv2.putText(hud, "RECONCILED GLOBAL EVENT FEED:", (c3, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 210, 50), 1)
    for idx, evt in enumerate(reversed(coord.global_events[-3:])):
        color = (0, 255, 120) if evt.direction == "IN" else (0, 160, 255)
        line = f"{evt.timestamp_iso[-8:]} [{evt.camera_id[:9]}] {evt.student_id} -> {evt.direction}"
        cv2.putText(hud, line, (c3, 80 + idx * 24), cv2.FONT_HERSHEY_SIMPLEX, 0.44, color, 1)

    cv2.putText(hud, "Press 'q' or ESC to exit", (canvas_w - 200, 185), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1)
    return hud

def main():
    sample_video = "ai-service/data/videos/pedestrians_sample.mp4"

    parser = argparse.ArgumentParser(description="Week 4 Dual Camera & Adaptive Fusion Attendance")
    parser.add_argument("--no-display", action="store_true", help="Run without UI display")
    parser.add_argument("--max-frames", type=int, default=-1, help="Max frames to process")
    args = parser.parse_args()

    print("=" * 65)
    print("  AI ATTENDANCE — WEEK 4: DUAL CAMERA & ADAPTIVE FUSION")
    print("=" * 65)

    # Ingest dual camera streams: ENTRY_CAM_01 and EXIT_CAM_01
    entry_worker = CameraStreamWorker("ENTRY_CAM_01", "CLASSROOM_203", sample_video, line_y=180, direction_type="IN")
    exit_worker = CameraStreamWorker("EXIT_CAM_01", "CLASSROOM_203", sample_video, line_y=180, direction_type="OUT")

    # Shared Biometric Extractor Components
    face_detector = FaceDetector()
    face_quality = FaceQualityAssessor()
    face_embedder = FaceEmbedder(device="cpu")
    face_matcher = FaceMatcher()

    body_embedder = BodyEmbedder(device="cpu")
    body_quality = BodyQualityAssessor()
    body_matcher = BodyMatcher()

    fusion_engine = AdaptiveFusionEngine(acceptance_threshold=0.48)
    coordinator = MultiCameraCoordinator()
    registry = StudentRegistry()

    fusion_audit_history = []
    cam_w, cam_h = 480, 270

    frame_idx = 0
    try:
        while True:
            t_start = time.time()
            ret1, frame1 = entry_worker.video_src.read()
            ret2, frame2 = exit_worker.video_src.read()
            if not ret1 or not ret2:
                break

            workers_and_frames = [(entry_worker, frame1), (exit_worker, frame2)]
            rendered_cam_views = []

            for worker, frame in workers_and_frames:
                orig_h, orig_w = frame.shape[:2]
                tracks, _ = worker.tracker.update(frame)

                for t in tracks:
                    x1, y1, x2, y2 = t.bbox
                    person_crop = frame[max(0, y1):min(orig_h, y2), max(0, x1):min(orig_w, x2)]

                    # Modality 1: Face Analysis
                    faces = face_detector.detect_in_person_crop(person_crop, offset=(x1, y1))
                    face_obs = ModalityObservation("face", None, 0.0, 0.0, t.track_id, t_start)
                    if faces:
                        bf = max(faces, key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]))
                        f_rep = face_quality.assess(bf.crop)
                        if f_rep.is_usable:
                            f_emb = face_embedder.extract(bf.crop)
                            f_matches = face_matcher.search(f_emb, top_k=1)
                            if f_matches:
                                face_obs.candidate_id = f_matches[0].student_id
                                face_obs.identity_score = f_matches[0].similarity
                                face_obs.reliability = f_rep.overall_reliability

                    # Modality 2: Body Re-ID Analysis
                    body_obs = ModalityObservation("body", None, 0.0, 0.0, t.track_id, t_start)
                    b_rep = body_quality.assess(person_crop)
                    if b_rep.is_usable:
                        b_emb = body_embedder.extract(person_crop)
                        b_matches = body_matcher.search(b_emb, top_k=1)
                        if b_matches:
                            body_obs.candidate_id = b_matches[0].student_id
                            body_obs.identity_score = b_matches[0].similarity
                            body_obs.reliability = b_rep.overall_reliability

                    # Adaptive Multimodal Fusion
                    fused_result = fusion_engine.fuse(t.track_id, [face_obs, body_obs])
                    if fused_result.decision:
                        fusion_audit_history.append(fused_result.audit_trail["fusion"])
                        if len(fusion_audit_history) > 20:
                            fusion_audit_history.pop(0)

                    # Check Line Crossing
                    scale_x = cam_w / float(orig_w)
                    scale_y = cam_h / float(orig_h)
                    disp_cx = int(t.centroid[0] * scale_x)
                    disp_cy = int(t.centroid[1] * scale_y)

                    crossing_dir = worker.crossing_detector.check_crossing(t.track_id, (disp_cx, disp_cy))
                    if crossing_dir is not None and fused_result.decision:
                        evt = AttendanceEvent(
                            event_id=f"EVT-{int(time.time()*1000)%1000000}",
                            student_id=fused_result.decision,
                            camera_id=worker.camera_id,
                            location_id=worker.location_id,
                            direction=worker.direction_type,
                            timestamp=t_start,
                            timestamp_iso=datetime.fromtimestamp(t_start).strftime("%Y-%m-%dT%H:%M:%S"),
                            track_id=t.track_id,
                            confidence=fused_result.confidence
                        )
                        coordinator.handle_event(evt)

                    # Bounding Box
                    color = (0, 255, 100) if fused_result.decision else (160, 160, 160)
                    label = f"ID:{t.track_id} | {fused_result.decision or 'Scanning'}"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, label, (x1, max(y1 - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                view_resized = cv2.resize(frame, (cam_w, cam_h))
                cv2.line(view_resized, worker.door_line.pt1, worker.door_line.pt2, (0, 140, 255), 2)
                cv2.putText(view_resized, f"[{worker.camera_id}] ({worker.direction_type})", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 2)
                rendered_cam_views.append(view_resized)

            dual_view = np.hstack(rendered_cam_views)
            hud = draw_dual_cam_hud(dual_view.shape[1], coordinator, fusion_audit_history)
            final_display = np.vstack([dual_view, hud])

            if not args.no_display:
                cv2.imshow("AI Attendance - Week 4 Multi-Camera & Adaptive Fusion", final_display)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    break

            frame_idx += 1
            if args.max_frames > 0 and frame_idx >= args.max_frames:
                break

    finally:
        entry_worker.video_src.release()
        exit_worker.video_src.release()
        if not args.no_display:
            cv2.destroyAllWindows()
        print(f"Dual-camera engine stopped. Processed {frame_idx} frames.")

if __name__ == "__main__":
    main()
