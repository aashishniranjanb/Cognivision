import axios from "axios";

export const SPRING_BASE = "http://localhost:8080/api";
export const AI_BASE = "http://localhost:8000/api";
export const AI_WS_URL = "ws://localhost:8000/ws/dashboard";

const springApi = axios.create({
    baseURL: SPRING_BASE,
    timeout: 3000,
    headers: { "Content-Type": "application/json" }
});

const aiApi = axios.create({
    baseURL: AI_BASE,
    timeout: 3000,
    headers: { "Content-Type": "application/json" }
});

// --- Four Truths & AI Service APIs ---
export const getFourTruths = (classroomId) =>
    aiApi.get("/campus/four_truths", { params: classroomId ? { classroom_id: classroomId } : {} });

export const getStudentEvidence = (studentId) =>
    aiApi.get(`/evidence/${studentId}`);

export const getCameraHealth = () =>
    aiApi.get("/camera/health");

export const getCampusSummary = async () => {
    try {
        const res = await aiApi.get("/campus/summary");
        return res;
    } catch {
        return springApi.get("/dashboard/summary");
    }
};

export const getEvents = async () => {
    try {
        const res = await aiApi.get("/events/recent?limit=50");
        return res;
    } catch {
        return springApi.get("/events");
    }
};

export const getClassrooms = async () => {
    try {
        const res = await aiApi.get("/classrooms");
        return res;
    } catch {
        return springApi.get("/classrooms");
    }
};

export const getStudents = () =>
    springApi.get("/students");

export const getCameras = async () => {
    try {
        const res = await aiApi.get("/camera/health");
        return res;
    } catch {
        return springApi.get("/cameras");
    }
};

export const getTodayAttendance = () =>
    springApi.get("/attendance/today");

export const simulateEvent = (data) =>
    aiApi.post("/events/simulate", data);

export default aiApi;