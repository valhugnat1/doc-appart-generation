import time
from datetime import datetime
from collections import defaultdict

class MonitoringService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MonitoringService, cls).__new__(cls)
            cls._instance.start_time = time.time()
            cls._instance.total_requests = 0
            cls._instance.error_count_4xx = 0
            cls._instance.error_count_5xx = 0
            cls._instance.requests_by_endpoint = defaultdict(int)
            cls._instance.response_times = []  # Store last 100 response times
            cls._instance.max_response_times_history = 1000
        return cls._instance

    def log_request(self, endpoint: str, method: str, processing_time: float, status_code: int):
        self.total_requests += 1
        
        # Track by endpoint (method + path)
        key = f"{method} {endpoint}"
        self.requests_by_endpoint[key] += 1

        # Track errors
        if 400 <= status_code < 500:
            self.error_count_4xx += 1
        elif status_code >= 500:
            self.error_count_5xx += 1

        # Track response time
        self.response_times.append(processing_time)
        if len(self.response_times) > self.max_response_times_history:
            self.response_times.pop(0)

    def get_stats(self):
        avg_response_time = 0
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)

        # Calculate uptime
        uptime_seconds = int(time.time() - self.start_time)
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"

        return {
            "uptime": uptime_str,
            "total_requests": self.total_requests,
            "error_rate_4xx": self.error_count_4xx,
            "error_rate_5xx": self.error_count_5xx,
            "avg_response_time_ms": round(avg_response_time * 1000, 2),
            "requests_by_endpoint": dict(self.requests_by_endpoint),
            "start_time_iso": datetime.fromtimestamp(self.start_time).isoformat()
        }

monitoring_service = MonitoringService()
