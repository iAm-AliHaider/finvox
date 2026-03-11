"""Remove first Agent/AgentSession creation, keep the second one that has OTP context."""
import pathlib

p = pathlib.Path(__file__).parent.parent / "agent.py"
lines = p.read_text(encoding="utf-8").split("\n")

# Find and remove lines 304-320 (first agent + session block)
# Find "    agent = Agent(" at line ~304
start = None
end = None
for i, line in enumerate(lines):
    if line.strip() == "agent = Agent(" and start is None:
        start = i
    if start and line.strip() == ")" and i > start + 10:
        end = i + 1
        break

if start and end:
    # Remove from start to end (includes Agent + AgentSession)
    print(f"Removing lines {start+1} to {end} (first Agent+Session block)")
    del lines[start:end]
    # Add a comment placeholder
    lines.insert(start, "    # Agent and session created below after OTP pre-generation")

p.write_text("\n".join(lines), encoding="utf-8")
print("Done")
