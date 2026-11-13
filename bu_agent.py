import os, sys, time, asyncio, inspect
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent / ".env"

def read_env_file():
    if not ENV_PATH.exists():
        return {}
    raw = ENV_PATH.read_bytes()
    text = raw.decode("utf-16") if raw.startswith((b"\xff\xfe", b"\xfe\xff")) \
        else raw.decode("utf-8-sig", errors="replace")
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out

env = read_env_file()
key = env.get("GOOGLE_API_KEY") or env.get("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not key:
    sys.exit("No API key found in .env (expected GOOGLE_API_KEY=...)")
os.environ["GOOGLE_API_KEY"] = key
print(f"Key loaded ({len(key)} characters)")

# ---- Test several models; keep the ones that work, fastest first ----
from google import genai
from google.genai import types

CANDIDATES = [
    "gemini-3.1-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3-flash-preview",
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
]
try:
    client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=20000))
except Exception:
    client = genai.Client(api_key=key)

working = []
for m in CANDIDATES:
    t = time.time()
    try:
        client.models.generate_content(model=m, contents="Reply with the word OK")
        secs = time.time() - t
        working.append((secs, m))
        print(f"  OK   {m}  ({secs:.1f}s)")
    except Exception as e:
        print(f"  FAIL {m}: {str(e)[:110]}")

if not working:
    sys.exit("No Gemini model worked. Read the FAIL lines above, then check aistudio.google.com.")

working.sort()                                  # fastest first
primary, backup = working[0][1], (working[1][1] if len(working) > 1 else None)
print("Using:", primary, "| backup:", backup)

# ---- Browser agent ----
from browser_use import Agent, Browser, ChatGoogle

llm = ChatGoogle(model=primary, api_key=key)
fallback = ChatGoogle(model=backup, api_key=key) if backup else None
browser = Browser(headless=False)

TASK = """
Find a laptop matching these specs on an Indian e-commerce website.

TARGET SPECS:
- Brand/model: HP 255 G8 Notebook PC (preferred)
- Processor: AMD Ryzen 5 5500U
- RAM: 8 GB
- Storage: 512 GB SSD

STEPS:
1. The browser is already open. First go to https://www.bing.com
2. Search Bing for "Flipkart" and open the official Flipkart website from the
   results (www.flipkart.com). Ignore sponsored ads.
   If Flipkart does not open, search Bing for "Amazon India" and open www.amazon.in.
3. On the shopping site, use its own search box to search for
   "HP 255 G8 Ryzen 5 5500U 8GB 512GB".
   If a login popup appears, close it. Do not log in.
   If the search box cannot be used, open the site's search URL directly.
4. Open at most 4 promising product pages and read their specifications.
5. Prefer an exact HP 255 G8 match. Otherwise pick HP laptops with
   Ryzen 5 5500U, 8 GB RAM and 512 GB SSD, or the closest alternatives.
6. Do not add anything to the cart and do not buy anything.

FINAL ANSWER: up to 3 best matches, each with name, price, processor, RAM,
storage, link, and which specs match or do not match.
Only report details you actually saw. If something is not shown, write "not shown".
Then finish.
"""

wanted = dict(
    task=TASK, llm=llm, browser=browser,
    fallback_llm=fallback,
    use_vision=False,
    max_failures=5,
    llm_timeout=180,
    step_timeout=240,
)
allowed = set(inspect.signature(Agent.__init__).parameters)
kwargs = {k: v for k, v in wanted.items() if k in allowed and v is not None}

async def main():
    # Open the browser first so you can see it before the agent starts
    try:
        await browser.start()
        print("Browser opened. Starting the agent in 3 seconds...")
        await asyncio.sleep(3)
    except Exception as e:
        print("Could not pre-start the browser (the agent will start it):", str(e)[:150])

    agent = Agent(**kwargs)
    result = await agent.run(max_steps=30)

    final = result.final_result() or "No result."
    print("\n===== FINAL RESULT =====")
    print(final)

    out = Path(__file__).resolve().parent / "laptop_result.md"
    out.write_text(final, encoding="utf-8")
    print("\nSaved to", out)

asyncio.run(main())