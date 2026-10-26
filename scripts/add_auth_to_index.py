from pathlib import Path
p = Path("static/index.html")
c = p.read_text(encoding="utf-8")
if "auth.css" not in c:
    c = c.replace("</head>", "    <link rel=\"stylesheet\" href=\"auth.css\">\n</head>")
if "auth.js" not in c:
    c = c.replace("</body>", "    <script src=\"auth.js\"></script>\n</body>")
p.write_text(c, encoding="utf-8")
print("done")
