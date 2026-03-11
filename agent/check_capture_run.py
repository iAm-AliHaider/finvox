import inspect
from livekit.agents.voice.agent_session import AgentSession
src = inspect.getsource(AgentSession.start)
# Find capture_run handling
lines = src.split('\n')
for i, line in enumerate(lines):
    if 'capture_run' in line or 'run_result' in line.lower() or 'RunResult' in line or '_run' in line:
        for j in range(max(0,i-1), min(len(lines), i+5)):
            print(f"{j}: {lines[j]}")
        print("---")
