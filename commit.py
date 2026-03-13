import subprocess, os

os.chdir(r'C:\Users\AI\.openclaw\workspace\finvox')

# Write gitignore additions
gi_path = '.gitignore'
with open(gi_path, 'a', encoding='utf-8') as f:
    f.write('\nagent/wa_browser/wa_data/\nagent/logs/\nagent/statements/\nagent/test*.py\nagent/patch_*.py\nagent/*.log\nfrontend/src/app/patch_*.py\npatch_*.py\n')
print("gitignore updated")

# Stage everything except blocked files
def run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"WARN: {r.stderr[:200]}")
    else:
        print(r.stdout.strip()[:200] or 'ok')

run('git rm -r --cached agent/wa_browser/wa_data 2>nul || echo skipped')
run('git add -A -- ":!agent/wa_browser/wa_data" ":!agent/logs" ":!agent/statements"')
run('git commit -m "v4.0 - Universal DB Attacher: attach any client DB, auto-discover schema"')
run('git push origin HEAD:master')
