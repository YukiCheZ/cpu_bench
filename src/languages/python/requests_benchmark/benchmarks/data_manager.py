import json
from pathlib import Path

class DataManager:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def generate_nested_data(self, size, file_path):
        """Generate nested JSON dataset and save to file."""
        data = {
            "size": size,
            "data": [
                {
                    "value": i,
                    "meta": {
                        "even": (i % 2 == 0),
                        "square": i * i
                    }
                }
                for i in range(size)
            ]
        }
        with open(file_path, "w") as f:
            json.dump(data, f)
        return data

    def generate_dataset(self, size):
        """
        Always generate dataset regardless of existing file.
        Returns dataset as a Python dict.
        """
        filename = self.data_dir / f"data_{size}.json"
        return self.generate_nested_data(size, filename)

    def load_dataset(self, size):
        """Load dataset from file and return as a Python dict."""
        filename = self.data_dir / f"data_{size}.json"
        if not filename.exists():
            raise FileNotFoundError(f"Dataset not found: {filename}")
        with open(filename, "r") as f:
            return json.load(f)
