"""Tests for Demo Mode Scenarios (V1.2 Plan Section 12)."""
import pytest
from fastapi.testclient import TestClient
from app.backend.api import app
from app.orchestration.demo_scenario_runner import DemoScenarioEngine

client = TestClient(app)


def test_list_demo_scenarios():
    res = client.get("/api/demo/scenarios")
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) == 7
    ids = [s["id"] for s in scenarios]
    assert "normal_entry" in ids
    assert "face_occlusion" in ids
    assert "low_lighting" in ids
    assert "unknown_visitor" in ids
    assert "two_people_crossing" in ids
    assert "camera_failure" in ids
    assert "occupancy_mismatch" in ids


@pytest.mark.parametrize("scenario_id", [
    "normal_entry",
    "face_occlusion",
    "low_lighting",
    "unknown_visitor",
    "two_people_crossing",
    "camera_failure",
    "occupancy_mismatch"
])
def test_execute_demo_scenarios(scenario_id):
    res = client.post(f"/api/demo/scenario/{scenario_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["scenario_id"] == scenario_id
    assert len(data["steps"]) == 5
    assert data["final_state"] in ("SUCCESS", "HANDLED_EXCEPTION", "ALARM_TRIGGERED")
    assert len(data["summary"]) > 0


def test_invalid_scenario_id():
    res = client.post("/api/demo/scenario/invalid_nonexistent")
    assert res.status_code == 400
