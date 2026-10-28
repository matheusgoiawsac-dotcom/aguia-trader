import subprocess
r=subprocess.run(['git','diff'],cwd='.',stdout=subprocess.PIPE)
print(len(r.stdout))
