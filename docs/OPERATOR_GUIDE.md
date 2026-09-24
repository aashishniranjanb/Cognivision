# SRM AI Automated Attendance System — Campus Operator Manual

## 1. Daily Operating Sequence

### Morning Boot (08:30 AM)
1. Verify host server is online and connected to the CCTV network.
2. Confirm service status by opening the Command Center UI (`http://localhost:5173` or port 8000).
3. Check the **Camera Health** widget: all 10 cameras must display a green indicator (`HEALTHY`).
4. Ensure SQLite database storage has $\ge 5\text{ GB}$ free disk space.

---

## 2. Operating the Command Center

### Overview Tab
- **Command Center KPIs**: Displays live count of enrolled students, active physical bodies on campus, identified students, official period attendance, and open exceptions.
- **Four Truths Telemetry**: Compares Physical Reality, Identity, Occupancy, and Academic Attendance.
- **Hourly Movement Trend**: Visualizes live inflow and outflow across morning arrival, lunch transit, and evening dispersal.

### Classrooms Tab
- View real-time occupancy vs capacity for each of the 5 classrooms (C101, C203, C301, C401, C501).
- Interactive room floorplan displays physical student positions (👤) with live track IDs and confidence scores.

### Cameras Tab
- 10-camera grid displaying live stream state, FPS, latency, face resolution gauge, blur gauge, and illumination status.
- Trigger optical survey calibration tests for any camera stream on demand.

### Students Tab & Forensic Evidence Drawer
- Search any enrolled student by ID or name.
- Click any student to open the slide-out **Forensic Evidence Drawer**:
  - Review best-frame capture crop.
  - Review ArcFace biometric similarity score.
  - Review OSNet body re-identification score.
  - Review combined adaptive fusion decision.
  - Review entry/exit crossing events, total room presence duration, and official status.

### Reports Tab & Official Attendance Export
- Period-by-period attendance grid for P1 through P8.
- Filter by date, classroom, or department.
- Single-click CSV export: downloads certified attendance log (`SRM_Attendance_Report.csv`).

---

## 3. Exception Handling & Manual Verification

| Symptom | Cause | Operator Action |
| :--- | :--- | :--- |
| **Occupancy Mismatch (Physical > Enrolled)** | Non-enrolled visitor or student from another section entered the room. | Click classroom in Classrooms tab; check unidentified track IDs; dispatch floor assistant if necessary. |
| **Camera Stream "OFFLINE"** | Network drop or PoE switch reboot. | Check physical ethernet connection; verify ping to camera IP; service will auto-reconnect once stream returns. |
| **Student marked "UNCERTAIN"** | Student wore heavy winter mask/scarf or profile yaw exceeded $65^\circ$. | Open student profile in Students tab; review evidence crop; click "Confirm Manual Override" if verified. |
| **Early Departure ("PARTIAL")** | Student left room before 75% required period duration was reached. | Review student duration timer (e.g., 18.5m / 45m). Academic rule automatically records PARTIAL. |
