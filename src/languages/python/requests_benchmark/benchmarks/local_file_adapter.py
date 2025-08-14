import os
import json
import requests
from requests.adapters import BaseAdapter
from requests.models import Response

class LocalFileAdapter(BaseAdapter):
    _cache = {}  # Cache: { "file://path": bytes }

    @classmethod
    def preload_from_data(cls, filepath, data):
        """Preload JSON data directly into memory cache."""
        file_url = f"file://{filepath}"
        cls._cache[file_url] = json.dumps(data).encode("utf-8")

    def send(self, request, stream=False, timeout=None, verify=True, cert=None, proxies=None):
        file_url = request.url
        if file_url not in self._cache:
            # First time: read from disk and cache
            path = file_url[len("file://") :]
            with open(path, "rb") as f:
                self._cache[file_url] = f.read()

        resp = Response()
        resp.status_code = 200
        resp._content = self._cache[file_url]
        resp.url = file_url
        return resp

    def close(self):
        pass
