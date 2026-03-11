import re, inspect
from livekit.agents.voice.agent_session import AgentSession
src = inspect.getsource(AgentSession)
matches = re.findall(r'_update_user_state\(.*?"(\w+)"', src)
print("User states:", sorted(set(matches)))
matches2 = re.findall(r'_update_agent_state\(.*?"(\w+)"', src)
print("Agent states:", sorted(set(matches2)))
