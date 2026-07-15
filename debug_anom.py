import json, subprocess, sys
result = subprocess.run(['curl.exe', '-s', 'http://localhost:8000/api/anomalies/moche/analyze'], capture_output=True, text=True)
d = json.loads(result.stdout)
p = [x['value'] for x in d.get('pressure', [])]
f = [x['value'] for x in d.get('flow', [])]
print(f'Pressure range: {min(p):.1f}-{max(p):.1f} MCA')
print(f'Flow range: {min(f):.1f}-{max(f):.1f} LPS')
anom_flow = sum(1 for x in f if x > 35)
anom_press = sum(1 for x in p if x < 40)
print(f'Flow > 35: {anom_flow}')
print(f'Pressure < 40: {anom_press}')