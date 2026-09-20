"""Week 1 Pipeline: Ingestion -> Buffer -> Decoupled Consumer & HUD Display."""
import time
import cv2
import numpy as np
import psutil

from app.camera.camera_manager import CameraManager
from app.buffer.frame_buffer import FramePacket

class Week1Pipeline:
    def __init__(self, camera_manager: CameraManager):
        self.mgr = camera_manager
        self.running = False

    def draw_hud(self, canvas: np.ndarray, summary: dict) -> np.ndarray:
        h, w = canvas.shape[:2]
        # HUD Panel at the bottom
        panel_h = 160
        hud = np.zeros((panel_h, w, 3), dtype=np.uint8)
        hud[:] = (24, 24, 27)

        # Header divider
        cv2.line(hud, (0, 0), (w, 0), (70, 70, 75), 2)
        cv2.putText(
            hud,
            "AI VIDEO ATTENDANCE — WEEK 1 INGESTION ENGINE",
            (20, 28),
            cv2.FONT_HERSHEY_DUPLEX,
            0.65,
            (0, 220, 255),
            1
        )

        # System resources
        cpu_usage = psutil.cpu_percent()
        ram_usage = psutil.virtual_memory().percent
        res_str = f"CPU: {cpu_usage:.1f}%  |  RAM: {ram_usage:.1f}%"
        cv2.putText(hud, res_str, (w - 300, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

        # Per-camera metrics column
        col_w = w // max(len(summary), 1)
        for i, (cam_id, stats) in enumerate(summary.items()):
            col_x = 20 + i * col_w
            status_text = "ONLINE" if stats["connected"] else f"OFFLINE ({stats['reconnect_attempts']} retries)"
            status_color = (0, 255, 100) if stats["connected"] else (0, 70, 255)

            cv2.putText(
                hud,
                f"[{cam_id}] {stats['location']} ({stats['direction']})",
                (col_x, 58),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                1
            )
            cv2.putText(
                hud,
                f"Status: {status_text}",
                (col_x, 80),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                status_color,
                1
            )
            metrics_line1 = (
                f"Input FPS: {stats['input_fps']:.1f}  |  "
                f"Proc FPS: {stats['processing_fps']:.1f}  |  "
                f"Latency: {stats['latency_ms']:.1f}ms"
            )
            cv2.putText(hud, metrics_line1, (col_x, 104), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

            metrics_line2 = (
                f"Queue: {stats['queue_size']}/{stats['queue_max']}  |  "
                f"Dropped: {stats['dropped_frames']} frames  |  "
                f"Res: {stats['resolution'][0]}x{stats['resolution'][1]}"
            )
            cv2.putText(hud, metrics_line2, (col_x, 126), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 210, 255), 1)

        # Stack video and HUD
        combined = np.vstack([canvas, hud])
        return combined

    def run_live(self, display: bool = True, max_frames: int = -1):
        self.mgr.start_all()
        self.running = True
        frame_idx = 0

        cam_ids = list(self.mgr.readers.keys())
        target_w, target_h = 640, 360

        try:
            while self.running:
                frames_to_display = []
                now = time.time()

                for cam_id in cam_ids:
                    buf = self.mgr.buffers[cam_id]
                    metrics = self.mgr.metrics[cam_id]

                    # Non-blocking pop to consume frame
                    packet = buf.pop(timeout=0.01)
                    if packet is not None:
                        latency = (now - packet.timestamp) * 1000.0
                        metrics.record_processed_frame(latency)
                        frame_img = packet.frame
                    else:
                        # Fallback to peek or black frame
                        peek = buf.peek_latest()
                        if peek is not None:
                            frame_img = peek.frame
                        else:
                            frame_img = np.zeros((target_h, target_w, 3), dtype=np.uint8)
                            cv2.putText(
                                frame_img,
                                f"{cam_id} WAITING...",
                                (180, 180),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.7,
                                (100, 100, 100),
                                2
                            )

                    # Resize for grid view
                    resized = cv2.resize(frame_img, (target_w, target_h))
                    frames_to_display.append(resized)

                # Stitch cameras horizontally
                if len(frames_to_display) == 1:
                    canvas = frames_to_display[0]
                else:
                    canvas = np.hstack(frames_to_display)

                summary = self.mgr.get_status_summary()
                dashboard_frame = self.draw_hud(canvas, summary)

                if display:
                    cv2.imshow("AI Video Attendance - Week 1 Demo", dashboard_frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q') or key == 27:
                        self.running = False
                        break

                frame_idx += 1
                if max_frames > 0 and frame_idx >= max_frames:
                    break

        finally:
            self.stop()
            if display:
                cv2.destroyAllWindows()

    def stop(self):
        self.running = False
        self.mgr.stop_all()
