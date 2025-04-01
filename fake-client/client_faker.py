class FakerClient:
    def __init__(self):
        self.connection = False

    def create_connection(self):
        self.connection = True

    def stop_connection(self):
        self.connection = False

    def delete_task(self): ...
