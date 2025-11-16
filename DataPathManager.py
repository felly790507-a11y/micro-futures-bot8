import os

class DataPathManager:
    def __init__(self, external_root="F:/期貨/data", internal_root=None):
        if internal_root is None:
            internal_root = os.path.join(os.path.dirname(__file__), "data")
        self.external_root = external_root
        self.internal_root = internal_root

    def get_path(self, filename, prefer_external=False):
        if prefer_external:
            return os.path.join(self.external_root, filename)
        else:
            return os.path.join(self.internal_root, filename)

    def ensure_dirs(self):
        os.makedirs(self.internal_root, exist_ok=True)
        os.makedirs(self.external_root, exist_ok=True)
