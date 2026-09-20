"""Comprehensive Unit Tests for Spatial Line Crossing, Event Deduplication, and Duration Calculation."""
import time
from app.attendance.zone import VirtualLine, LineCrossingDetector
from app.attendance.duration import DurationEngine
from app.attendance.state import AttendanceStateMachine, AttendanceStatus

def test_line_crossing_in_and_out():
    # Horizontal line at y=100
    line = VirtualLine(pt1=(0, 100), pt2=(200, 100), name="TEST_LINE")
    detector = LineCrossingDetector(line, cooldown_seconds=0.1)

    # Initial position above line (y=80)
    evt = detector.check_crossing(track_id=1, current_centroid=(50, 80))
    assert evt is None

    # Cross below line (y=120) -> Crossing detected
    evt = detector.check_crossing(track_id=1, current_centroid=(50, 120))
    assert evt == "IN"

    # Hovering below line should NOT emit duplicate
    evt_hover = detector.check_crossing(track_id=1, current_centroid=(50, 125))
    assert evt_hover is None

    # Wait out cooldown and cross back up (y=75) -> OUT
    time.sleep(0.15)
    evt_back = detector.check_crossing(track_id=1, current_centroid=(50, 75))
    assert evt_back == "OUT"

def test_duration_engine_entry_and_exit():
    dur_engine = DurationEngine()
    t0 = 1000.0

    # Record entry
    sess = dur_engine.record_entry("STU001", "ROOM_203", timestamp=t0)
    assert sess.status == "INSIDE"
    assert dur_engine.get_session("STU001") is not None

    # Record exit 15 minutes and 10 seconds later
    t1 = t0 + 910.0
    closed_sess = dur_engine.record_exit("STU001", timestamp=t1)
    assert closed_sess is not None
    assert closed_sess.status == "EXITED"
    assert closed_sess.duration_seconds == 910.0
    assert closed_sess.current_duration_formatted == "15m 10s"
    assert dur_engine.get_session("STU001") is None

def test_attendance_state_machine():
    sm = AttendanceStateMachine()
    st = sm.get_or_create("STU001")
    assert st.current_status == AttendanceStatus.UNKNOWN

    st_in = sm.transition_on_event("STU001", "IN", "ROOM_203", timestamp=time.time())
    assert st_in.current_status == AttendanceStatus.INSIDE

    st_out = sm.transition_on_event("STU001", "OUT", "ROOM_203", timestamp=time.time())
    assert st_out.current_status == AttendanceStatus.EXITED
