from urllib.request import Request, urlopen
from urllib.parse import quote, unquote
import re, base64, json

queries = [
    'site:zhihu.com C++ interview shared_ptr zhihu',
    'site:zhihu.com C++ interview virtual function zhihu',
    'site:zhihu.com C++ interview memory model zhihu',
    'site:zhihu.com C++ interview template zhihu',
    'site:zhihu.com C++ interview RAII zhihu',
]

out = {}
for q in queries:
    url = 'https://www.bing.com/search?q=' + quote(q)
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urlopen(req, timeout=20).read().decode('utf-8', 'ignore')
    items = []
    pattern = re.compile(r'<li class="b_algo".*?<h2><a href="(.*?)"[^>]*>(.*?)</a>.*?(?:<div class="b_caption"><p>(.*?)</p>)?', re.S)
    for href, title, snip in pattern.findall(html)[:5]:
        title = re.sub('<.*?>', '', title)
        snip = re.sub('<.*?>', '', (snip or ''))
        real = href
        m = re.search(r'[?&]u=([^&]+)', href)
        if m:
            u = unquote(m.group(1))
            if u.startswith('a1'):
                s = u[2:] + '=' * ((4 - len(u[2:]) % 4) % 4)
                try:
                    real = base64.b64decode(s).decode('utf-8', 'ignore')
                except Exception:
                    pass
        items.append({'title': title, 'url': real, 'snippet': snip})
    out[q] = items
print(json.dumps(out, ensure_ascii=False, indent=2))
