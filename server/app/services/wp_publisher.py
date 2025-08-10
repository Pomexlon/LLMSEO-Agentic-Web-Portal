import requests
from typing import Dict

class WordPressPublisher:
    def __init__(self, base_url: str, username: str, app_password: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.auth = (username, app_password)

    def create_post(self, title: str, content_html: str, status: str = "draft", categories=None, tags=None) -> Dict:
        data = {"title": title, "content": content_html, "status": status}
        if categories: data["categories"] = categories
        if tags: data["tags"] = tags
        r = self.session.post(f"{self.base_url}/wp-json/wp/v2/posts", json=data, timeout=30)
        r.raise_for_status()
        return r.json()
