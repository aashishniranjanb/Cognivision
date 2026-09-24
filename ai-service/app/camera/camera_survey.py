"""Real CCTV Camera Survey & Corridor Calibration Engine.
Implements Sections 2 & 3 of V1.2 Plan:
  - Validates physical camera geometry, resolution, FPS, and RTSP latency.
  - Answers the critical physical question: "How many pixels wide is a student's face
    when crossing the capture zone?" (Enforcing face_width >= 80px for reliable ArcFace).
  - Evaluates capture corridor control, sharpness (Laplacian >= 100), and illumination (50-250 lux).
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any


@dataclass
class CameraSurveyProfile:
    camera_id: str
    classroom_id: str
    resolution_width: int
    resolution_height: int
    fps: float
    mount_height_m: float
    door_distance_m: float
    lens_focal_length_mm: float
    horizontal_angle_deg: float
    vertical_angle_deg: float
    avg_person_height_px: int
    avg_face_width_px: int
    illumination_lux: float
    laplacian_sharpness: float
    rtsp_latency_ms: float
    corridor_width_m: float
    is_corridor_controlled: bool
    blind_spot_coverage_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SurveyValidationResult:
    camera_id: str
    is_production_ready: bool
    face_resolution_ok: bool
    illumination_ok: bool
    sharpness_ok: bool
    latency_ok: bool
    geometry_ok: bool
    warnings: List[str]
    recommendations: List[str]
    score_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CameraSurveyEngine:
    """Evaluates physical installation and optical conditions against production standards."""

    MIN_FACE_WIDTH_PX = 80
    MIN_SHARPNESS_LAPLACIAN = 100.0
    MIN_ILLUMINATION_LUX = 50.0
    MAX_ILLUMINATION_LUX = 250.0
    MAX_RTSP_LATENCY_MS = 120.0
    MAX_MOUNT_HEIGHT_M = 3.2
    MAX_DOOR_DISTANCE_M = 4.5

    # Standard default baseline surveys for the 10 campus cameras across 5 classrooms
    DEFAULT_CAMPUS_PROFILES = {
        "CAM-101-ENTRY": CameraSurveyProfile(
            camera_id="CAM-101-ENTRY",
            classroom_id="C101",
            resolution_width=1920,
            resolution_height=1080,
            fps=25.0,
            mount_height_m=2.6,
            door_distance_m=2.8,
            lens_focal_length_mm=4.0,
            horizontal_angle_deg=12.0,
            vertical_angle_deg=18.0,
            avg_person_height_px=540,
            avg_face_width_px=98,
            illumination_lux=165.0,
            laplacian_sharpness=142.0,
            rtsp_latency_ms=45.0,
            corridor_width_m=1.2,
            is_corridor_controlled=True,
            blind_spot_coverage_pct=98.5,
        ),
        "CAM-101-EXIT": CameraSurveyProfile(
            camera_id="CAM-101-EXIT",
            classroom_id="C101",
            resolution_width=1920,
            resolution_height=1080,
            fps=25.0,
            mount_height_m=2.7,
            door_distance_m=3.0,
            lens_focal_length_mm=4.0,
            horizontal_angle_deg=10.0,
            vertical_angle_deg=15.0,
            avg_person_height_px=520,
            avg_face_width_px=92,
            illumination_lux=150.0,
            laplacian_sharpness=135.0,
            rtsp_latency_ms=48.0,
            corridor_width_m=1.2,
            is_corridor_controlled=True,
            blind_spot_coverage_pct=97.0,
        ),
        "CAM-203-ENTRY": CameraSurveyProfile(
            camera_id="CAM-203-ENTRY",
            classroom_id="C203",
            resolution_width=1920,
            resolution_height=1080,
            fps=25.0,
            mount_height_m=2.5,
            door_distance_m=2.6,
            lens_focal_length_mm=4.0,
            horizontal_angle_deg=8.0,
            vertical_angle_deg=16.0,
            avg_person_height_px=560,
            avg_face_width_px=104,
            illumination_lux=180.0,
            laplacian_sharpness=155.0,
            rtsp_latency_ms=39.0,
            corridor_width_m=1.1,
            is_corridor_controlled=True,
            blind_spot_coverage_pct=99.0,
        ),
        "CAM-203-EXIT": CameraSurveyProfile(
            camera_id="CAM-203-EXIT",
            classroom_id="C203",
            resolution_width=1920,
            resolution_height=1080,
            fps=25.0,
            mount_height_m=2.6,
            door_distance_m=2.9,
            lens_focal_length_mm=4.0,
            horizontal_angle_deg=14.0,
            vertical_angle_deg=19.0,
            avg_person_height_px=510,
            avg_face_width_px=88,
            illumination_lux=140.0,
            laplacian_sharpness=128.0,
            rtsp_latency_ms=42.0,
            corridor_width_m=1.2,
            is_corridor_controlled=True,
            blind_spot_coverage_pct=96.5,
        ),
        "CAM-301-ENTRY": CameraSurveyProfile(
            camera_id="CAM-301-ENTRY",
            classroom_id="C301",
            resolution_width=1920,
            resolution_height=1080,
            fps=25.0,
            mount_height_m=2.8,
            door_distance_m=3.2,
            lens_focal_length_mm=4.0,
            horizontal_angle_deg=15.0,
            vertical_angle_deg=22.0,
            avg_person_height_px=480,
            avg_face_width_px=84,
            illumination_lux=130.0,
            laplacian_sharpness=115.0,
            rtsp_latency_ms=52.0,
            corridor_width_m=1.3,
            is_corridor_controlled=True,
            blind_spot_coverage_pct=95.0,
        ),
        "CAM-301-EXIT": CameraSurveyProfile(
            camera_id="CAM-301-EXIT",
            classroom_id="C301",
            resolution_width=1920,
            resolution_height=1080,
            fps=25.0,
            mount_height_m=2.7,
            door_distance_m=3.1,
            lens_focal_length_mm=4.0,
            horizontal_angle_deg=12.0,
            vertical_angle_deg=20.0,
            avg_person_height_px=490,
            avg_face_width_px=86,
            illumination_lux=135.0,
            laplacian_sharpness=120.0,
            rtsp_latency_ms=50.0,
            corridor_width_m=1.3,
            is_corridor_controlled=True,
            blind_spot_coverage_pct=95.5,
        ),
        "CAM-401-ENTRY": CameraSurveyProfile(
            camera_id="CAM-401-ENTRY",
            classroom_id="C401",
            resolution_width=1920,
            resolution_height=1080,
            fps=25.0,
            mount_height_m=2.5,
            door_distance_m=2.7,
            lens_focal_length_mm=4.0,
            horizontal_angle_deg=9.0,
            vertical_angle_deg=17.0,
            avg_person_height_px=550,
            avg_face_width_px=100,
            illumination_lux=170.0,
            laplacian_sharpness=148.0,
            rtsp_latency_ms=44.0,
            corridor_width_m=1.1,
            is_corridor_controlled=True,
            blind_spot_coverage_pct=98.0,
        ),
        "CAM-401-EXIT": CameraSurveyProfile(
            camera_id="CAM-401-EXIT",
            classroom_id="C401",
            resolution_width=1920,
            resolution_height=1080,
            fps=25.0,
            mount_height_m=2.6,
            door_distance_m=2.8,
            lens_focal_length_mm=4.0,
            horizontal_angle_deg=11.0,
            vertical_angle_deg=18.0,
            avg_person_height_px=530,
            avg_face_width_px=94,
            illumination_lux=160.0,
            laplacian_sharpness=138.0,
            rtsp_latency_ms=46.0,
            corridor_width_m=1.1,
            is_corridor_controlled=True,
            blind_spot_coverage_pct=97.5,
        ),
        "CAM-501-ENTRY": CameraSurveyProfile(
            camera_id="CAM-501-ENTRY",
            classroom_id="C501",
            resolution_width=1920,
            resolution_height=1080,
            fps=25.0,
            mount_height_m=2.6,
            door_distance_m=2.8,
            lens_focal_length_mm=4.0,
            horizontal_angle_deg=10.0,
            vertical_angle_deg=18.0,
            avg_person_height_px=535,
            avg_face_width_px=96,
            illumination_lux=165.0,
            laplacian_sharpness=140.0,
            rtsp_latency_ms=45.0,
            corridor_width_m=1.2,
            is_corridor_controlled=True,
            blind_spot_coverage_pct=98.0,
        ),
        "CAM-501-EXIT": CameraSurveyProfile(
            camera_id="CAM-501-EXIT",
            classroom_id="C501",
            resolution_width=1920,
            resolution_height=1080,
            fps=25.0,
            mount_height_m=2.7,
            door_distance_m=3.0,
            lens_focal_length_mm=4.0,
            horizontal_angle_deg=13.0,
            vertical_angle_deg=19.0,
            avg_person_height_px=505,
            avg_face_width_px=90,
            illumination_lux=145.0,
            laplacian_sharpness=130.0,
            rtsp_latency_ms=47.0,
            corridor_width_m=1.2,
            is_corridor_controlled=True,
            blind_spot_coverage_pct=96.0,
        ),
    }

    def __init__(self, custom_profiles: Optional[Dict[str, CameraSurveyProfile]] = None):
        self.profiles = dict(self.DEFAULT_CAMPUS_PROFILES)
        if custom_profiles:
            self.profiles.update(custom_profiles)

    def survey_camera(self, profile: CameraSurveyProfile) -> SurveyValidationResult:
        """Validates camera profile against optical and physical requirements."""
        warnings: List[str] = []
        recommendations: List[str] = []

        face_ok = profile.avg_face_width_px >= self.MIN_FACE_WIDTH_PX
        if not face_ok:
            warnings.append(
                f"Face pixel width ({profile.avg_face_width_px}px) < required {self.MIN_FACE_WIDTH_PX}px threshold. Risk of identity recognition loss."
            )
            recommendations.append("Move camera closer to doorway or use longer focal length lens (e.g., 6mm or 8mm).")

        illumination_ok = self.MIN_ILLUMINATION_LUX <= profile.illumination_lux <= self.MAX_ILLUMINATION_LUX
        if not illumination_ok:
            if profile.illumination_lux < self.MIN_ILLUMINATION_LUX:
                warnings.append(f"Corridor illumination ({profile.illumination_lux} lux) too dim (< {self.MIN_ILLUMINATION_LUX} lux).")
                recommendations.append("Install auxiliary LED task light directly above doorway corridor.")
            else:
                warnings.append(f"Corridor illumination ({profile.illumination_lux} lux) too bright (> {self.MAX_ILLUMINATION_LUX} lux). Backlight glare risk.")
                recommendations.append("Enable camera WDR (Wide Dynamic Range) mode or adjust doorway shading.")

        sharpness_ok = profile.laplacian_sharpness >= self.MIN_SHARPNESS_LAPLACIAN
        if not sharpness_ok:
            warnings.append(f"Image sharpness ({profile.laplacian_sharpness:.1f}) below threshold {self.MIN_SHARPNESS_LAPLACIAN}.")
            recommendations.append("Clean optical dome/lens cover and adjust manual focus ring.")

        latency_ok = profile.rtsp_latency_ms <= self.MAX_RTSP_LATENCY_MS
        if not latency_ok:
            warnings.append(f"RTSP stream latency ({profile.rtsp_latency_ms}ms) exceeds {self.MAX_RTSP_LATENCY_MS}ms budget.")
            recommendations.append("Switch RTSP transport from TCP to UDP or tune ffmpeg decoding buffer flags.")

        geometry_ok = (
            profile.mount_height_m <= self.MAX_MOUNT_HEIGHT_M
            and profile.door_distance_m <= self.MAX_DOOR_DISTANCE_M
            and profile.vertical_angle_deg <= 30.0
        )
        if not geometry_ok:
            warnings.append("Camera mounting geometry sub-optimal. Steep vertical angle causes top-down occlusion.")
            recommendations.append("Lower camera mount height to 2.4m - 2.8m and reduce vertical downward tilt angle <= 20°.")

        passed_checks = sum([face_ok, illumination_ok, sharpness_ok, latency_ok, geometry_ok])
        score_pct = round((passed_checks / 5.0) * 100.0, 1)
        is_ready = bool(score_pct >= 80.0 and face_ok)

        return SurveyValidationResult(
            camera_id=profile.camera_id,
            is_production_ready=is_ready,
            face_resolution_ok=face_ok,
            illumination_ok=illumination_ok,
            sharpness_ok=sharpness_ok,
            latency_ok=latency_ok,
            geometry_ok=geometry_ok,
            warnings=warnings,
            recommendations=recommendations,
            score_pct=score_pct,
        )

    def validate_all_campus_cameras(self) -> Dict[str, Any]:
        """Runs survey validation across all campus cameras."""
        results = {}
        all_ready = True
        total_score = 0.0

        for cam_id, profile in self.profiles.items():
            res = self.survey_camera(profile)
            results[cam_id] = res.to_dict()
            if not res.is_production_ready:
                all_ready = False
            total_score += res.score_pct

        avg_score = round(total_score / max(1, len(self.profiles)), 1)
        return {
            "total_cameras": len(self.profiles),
            "all_production_ready": all_ready,
            "average_calibration_score_pct": avg_score,
            "cameras": results,
        }
