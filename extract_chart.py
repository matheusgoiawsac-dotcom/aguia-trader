import re

# Read the original script.js
with open('static/script.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the chart section boundaries
start = content.find('function renderTradingChartReal')
end = content.find('async function testPythonBackend')

print(f"Start: {start}, End: {end}")
print(f"Chart section length: {end - start}")

# Save the chart section to a file for inspection
with open('chart_section.txt', 'w', encoding='utf-8') as f:
    f.write(content[start:end])

print("Chart section saved to chart_section.txt")