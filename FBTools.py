import requests
from bs4 import BeautifulSoup

class Start:
    def __init__(self, cookie):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://m.facebook.com/",
            "Origin": "https://m.facebook.com"
        })
        self.set_cookies(cookie)

    def set_cookies(self, cookie_string):
        for part in cookie_string.strip().split(';'):
            if '=' in part:
                key, value = part.strip().split('=', 1)
                self.session.cookies.set(key.strip(), value.strip())

    def CommentToPost(self, post, text):
        try:
            post_url = f"https://m.facebook.com/{post}"
            res = self.session.get(post_url)
            if res.status_code != 200:
                return {"status": "fail", "error": "Failed to load post"}

            soup = BeautifulSoup(res.text, "html.parser")
            form = soup.find("form", action=lambda x: x and "/a/comment" in x)
            if not form:
                return {"status": "fail", "error": "Comment form not found"}

            action_url = "https://m.facebook.com" + form.get("action")

            fb_dtsg = form.find("input", {"name": "fb_dtsg"})["value"]
            jazoest = form.find("input", {"name": "jazoest"})["value"]

            payload = {
                "fb_dtsg": fb_dtsg,
                "jazoest": jazoest,
                "comment_text": text,
            }

            post_response = self.session.post(action_url, data=payload)
            if "Your comment has been added" in post_response.text or post_response.status_code == 200:
                return {"status": "success"}
            else:
                return {"status": "fail", "error": "Unknown error while commenting"}
        except Exception as e:
            return {"status": "fail", "error": str(e)}
