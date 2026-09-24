# SRM AI Automated Attendance System — Camera Calibration & Corridor Setup

## 1. Physical Doorway Geometry & Capture Corridor

The success of automated biometric recognition depends heavily on physical geometry. A student whose face appears at 35 pixels cannot be recognized reliably by any model.

```text
                  CLASSROOM INTERIOR
                         │
                         │
                  ┌──────┴──────┐
                  │             │
                  │   CAPTURE   │  Length: 1.5m - 2.5m
                  │    ZONE     │  Width:  1.0m - 1.4m
                  │             │
                  │      👤     │  Face Width >= 80px
                  │      👤     │  Frontal Yaw <= 25°
                  └──────┬──────┘
                         │
                   CROSSING LINE
═════════════════════════╪════════════════════════
                         │
                     CCTV CAMERA (Mount: 2.5m - 2.8m, Downward Tilt: 15° - 20°)
```

---

## 2. Hard Calibration Benchmarks

Every camera stream must satisfy the following thresholds (verified automatically via `GET /api/cameras/{camera_id}/survey`):

1. **Face Pixel Width ($\ge 80\text{ px}$)**:
   - For a 1080p stream at a distance of 2.5m with a 4.0mm lens, a human face (approx. 16cm physical width) spans approx. **95 - 110 pixels**.
   - If face size falls below 80px, replace lens with 6.0mm or reposition camera closer to doorway.

2. **Optical Sharpness ($\text{Laplacian Variance} \ge 100$)**:
   - Out-of-focus or smeared lenses reduce landmark extraction accuracy.
   - Clean the optical housing dome weekly and adjust manual focus ring.

3. **Illumination ($50\text{ to }250\text{ lux}$)**:
   - Below 50 lux: sensor gain introduces high noise, degrading feature vectors.
   - Above 250 lux: direct backlight washes out facial landmarks.
   - Recommendation: Install a 10W neutral-white LED downlight directly over the capture zone corridor.

4. **Mounting Angles**:
   - **Mount Height**: $2.5\text{m} - 2.8\text{m}$ (never mount above 3.2m to prevent steep top-of-head perspective distortion).
   - **Downward Tilt**: $15^\circ - 20^\circ$.
   - **Horizontal Angle**: $\le 15^\circ$ aligned with corridor centerline.

5. **RTSP Stream Latency ($\le 120\text{ ms}$)**:
   - Enforce sub-120ms network latency to prevent track drops during rapid student entry batches.
   - Use dedicated CCTV switch on a separated VLAN.
