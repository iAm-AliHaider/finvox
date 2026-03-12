import asyncio

async def main():
    message = (
        "*Call Summary - MRNA*\n\n"
        "Hello Ali Haider,\n\n"
        "- Checked loan status for personal loan\n"
        "- Portfolio reviewed, 12% return YTD\n"
        "- Scheduled callback for next week\n\n"
        "For queries, reply to this message or call us.\n"
        "_MRNA Financial Services_"
    )
    proc = await asyncio.create_subprocess_exec(
        r"C:\Users\AI\AppData\Roaming\npm\openclaw.cmd", "message", "send",
        "--target", "+966534006682",
        "--message", message,
        "--channel", "whatsapp",
        "--json",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
    print(f"RC: {proc.returncode}")
    print(f"OUT: {stdout.decode()}")
    print(f"ERR: {stderr.decode()}")

asyncio.run(main())
