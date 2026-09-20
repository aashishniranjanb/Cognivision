"""Selective Inference Scheduler balancing CPU/GPU throughput across multiple concurrent streams."""
class SelectiveInferenceScheduler:
    def __init__(self, full_recognition_interval: int = 4):
        self.interval = full_recognition_interval
        self.frame_counters = {}

    def should_infer_modality(self, camera_id: str, modality: str) -> bool:
        """Determines if a given modality should be evaluated on the current camera frame."""
        if camera_id not in self.frame_counters:
            self.frame_counters[camera_id] = 0

        self.frame_counters[camera_id] += 1
        count = self.frame_counters[camera_id]

        if modality == "detection":
            return True  # Detector and ByteTrack run every frame for tracking stability

        if modality == "face":
            return (count % 2) == 0  # Face checks run every 2nd frame

        if modality == "body":
            return (count % 3) == 0  # Body Re-ID runs every 3rd frame

        return True
