"""Download Korean web fonts (Black Han Sans, Jua) locally for offline frame rendering."""
import os, re, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 Chrome/120 Safari/537.36"
URL = "https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Jua&display=block"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
os.makedirs(OUT, exist_ok=True)

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA})).read()

css = get(URL).decode()
def repl(m):
    url = m.group(1)
    name = re.sub(r"[^A-Za-z0-9._-]", "_", url.split("/s/")[1])
    path = os.path.join(OUT, name)
    if not os.path.exists(path):
        with open(path, "wb") as f:
            f.write(get(url))
    return f"url(fonts/{name})"
css = re.sub(r"url\((https://[^)]+)\)", repl, css)
with open(os.path.join(os.path.dirname(OUT), "fonts.css"), "w") as f:
    f.write(css)
print("fonts:", len(os.listdir(OUT)))
