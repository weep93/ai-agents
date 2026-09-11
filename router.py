import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


# // config

ROUTER_MODEL = "deepseek/deepseek-chat" # cheap + fast : only used when the rules cannot decide

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


# keyword rules : obvious prompts get routed instantly, no API call

RULES = {
    "coding": [
        "code", "bug", "error", "python", "script", "function", "api",
        "debug", "traceback", "install", "git", "regex", "class", "compile",
    ],
    "security": [
        "log", "logs", "server", "service", "systemd", "journalctl", "port",
        "ssh", "firewall", "ufw", "fail2ban", "honeypot", "nginx", "vps",
        "vulnerab", "ban", "exploit", "auth", "leak",
        "bot", "not responding", "offline", "down", "restart", "crash",
    ],
}


# defining the router

def rules_route(prompt):
    low = prompt.lower()

    picked = [
        name
        for name, words in RULES.items()
        if any(word in low for word in words)
    ]

    return picked


def llm_route(prompt):
    """Ask a cheap model to pick the agents. Only for prompts the rules missed."""

    ask = """You are a task router.
Pick which agents should answer the user's task.

Agents:
- general  : everything else, everyday questions, reasoning
- coding   : programming, debugging, APIs, software
- security : servers, logs, networks, authentication, security risks

Answer with JSON only, no text around it:
{"agents": ["general"], "reason": "one short sentence"}
Pick more than one agent only when the task really needs it.

User task: """ + prompt

    response = client.chat.completions.create(
        model=ROUTER_MODEL,
        messages=[{"role": "user", "content": ask}],
    )

    raw = response.choices[0].message.content or ""

    # models love wrapping json in fences : strip them
    raw = raw.strip().replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(raw)
        agents = [a for a in data.get("agents", []) if a in ("general", "coding", "security")]
        if not agents:
            agents = ["general"]
        return agents, data.get("reason", "")

    except Exception:
        return ["general"], "router could not parse its own answer : defaulted to general"


def pick_agents(prompt):
    """Returns (list of agent names, why). Rules first, model only if needed."""

    picked = rules_route(prompt)

    if picked:
        return picked, "rules"

    agents, reason = llm_route(prompt)
    return agents, reason
