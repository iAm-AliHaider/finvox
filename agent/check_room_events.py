import re, inspect
from livekit import rtc
src = inspect.getsource(rtc.Room)
events = re.findall(r'self\.emit\("(\w+)"', src)
print("Room events:", sorted(set(events)))
