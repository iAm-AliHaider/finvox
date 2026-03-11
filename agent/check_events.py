import re, inspect
from livekit.agents.voice.agent_session import AgentSession
src = inspect.getsource(AgentSession)
events = re.findall(r'self\.emit\("(\w+)"', src)
print("Events:", sorted(set(events)))
