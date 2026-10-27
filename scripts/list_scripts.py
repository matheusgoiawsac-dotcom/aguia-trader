from pathlib import Path
import re
p = Path("static/index.html")
c = p.read_text(encoding="utf-8")
for m in re.finditer(r'<script[^>]+src="([^"]+)"', c):
    print(m.group(1))
