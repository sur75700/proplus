from fastapi import FastAPI
import requests

app = FastAPI()

PROXIES = {
    "http":  "socks5h://127.0.0.1:9050",
    "https": "socks5h://127.0.0.1:9050",
}

@app.get("/tor-ip")
def tor_ip():
    r = requests.get("https://api.ipify.org", proxies=PROXIES, timeout=20)
    return {"tor_exit_ip": r.text}

@app.get("/tor-get")
def tor_get(url: str):
    # Օգտագործիր միայն օրինական և անվտանգ նշված URL-ներով
    r = requests.get(url, proxies=PROXIES, timeout=20)
    return {
        "url": url,
        "status_code": r.status_code,
        "content_snippet": r.text[:400],
    }
