import json, subprocess, os
result = subprocess.run(['curl.exe', '-s', 'http://localhost:8000/api/anomalies/moche/recent'], capture_output=True, text=True)
d = json.loads(result.stdout)
print(f'Total anomalies: {d["total"]}')
for a in d['anomalies'][:3]:
    an = a['anomaly']
    print(f'  ID: {an["id"]} Sev: {an["severity"]} Score: {an["anomaly_score"]:.2f} PressVar: {an["pressure_variation"]} FlowVar: {an["flow_variation"]} Loss: {an["estimated_loss_volume"]} Desc: {an["description"][:50] if an["description"] else "None"}...')