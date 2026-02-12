class HeartbeatService:
    def __init__(self, backend):
        self.backend = backend

    def tick(self):
        self.backend.send_heartbeat()
