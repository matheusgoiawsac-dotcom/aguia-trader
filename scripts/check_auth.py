from pathlib import Path
p = Path("static/script.js")
c = p.read_text(encoding="utf-8")
print("has toggleMenu:", "toggleMenu" in c)
print("has openMenu:", "openMenu" in c)
print("has closeMenu:", "closeMenu" in c)
print("has aguiaAuthSuccess:", "aguiaAuthSuccess" in c)
print("has openAuthModal ref:", "openAuthModal" in c)
