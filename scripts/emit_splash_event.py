from pathlib import Path
p = Path("static/script.js")
c = p.read_text(encoding="utf-8")
if "aguia:splash-done" not in c:
    old = '''    } catch (error) {
        document.documentElement.classList.remove("app-booting");
        console.warn("Falha na coreografia da splash:", error);
    }'''
    new = '''    } catch (error) {
        document.documentElement.classList.remove("app-booting");
        console.warn("Falha na coreografia da splash:", error);
        try { window.dispatchEvent(new CustomEvent('aguia:splash-done')); } catch(e){}
    }
    // Dispatch splash done event after settle
    setTimeout(function(){ try { window.dispatchEvent(new CustomEvent('aguia:splash-done')); } catch(e){} }, 6500);'''
    if old in c:
        c = c.replace(old, new)
    else:
        c += "\nsetTimeout(function(){ try { window.dispatchEvent(new CustomEvent('aguia:splash-done')); } catch(e){} }, 6500);\n"
    p.write_text(c, encoding="utf-8")
    print("done")
else:
    print("exists")
