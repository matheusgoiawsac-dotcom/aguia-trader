with open("static/style.css", encoding="utf-8") as f:
    for i,l in enumerate(f,1):
        if "#f0" in l or "#e8" in l or "#d3" in l or "#1a2e" in l:
            print(i,l.rstrip())
