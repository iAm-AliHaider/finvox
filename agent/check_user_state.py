import re, inspect
from livekit.agents.voice.agent_session import AgentSession
src = inspect.getsource(AgentSession)
# Find user_state_changed emissions
matches = re.findall(r'_update_user_state.*?emit.*?user_state.*?\n.*?\n', src, re.DOTALL)
for m in matches:
    print(m[:200])
print("---")
# Find UserState enum
matches2 = re.findall(r'class UserState.*?(?=\nclass )', src, re.DOTALL)
for m in matches2:
    print(m[:300])
# Also check for string literals near user_state
matches3 = re.findall(r'"user_state_changed".*?\n', src)
for m in matches3:
    print(m)
