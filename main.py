# main.py : router -> agents -> judge | get_logs tool wired in | rewritten 2026-09-11
import json
import os
import time

from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

from openai import OpenAI

from tools.get_logs import get_logs

from judge import final_answer

from router import pick_agents

load_dotenv()


# // config

MAX_TOOL_ROUNDS = 4 # how many times an agent can call tools before we stop it

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


# defining the tools the agents are allowed to call

TOOL_REGISTRY = {
    "get_logs": get_logs,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_logs",
            "description": "Read recent log lines for an allowed service. Use when asked what a service is doing, why it failed, or for recent activity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "unit": {
                        "type": "string",
                        "enum": ["weep-manager", "weep-site", "nginx", "fail2ban", "ssh", "kage-web"],
                        "description": "which service to read logs for",
                    },
                    "lines": {
                        "type": "integer",
                        "description": "lines to return, 1-200 (default 50)",
                    },
                },
                "required": ["unit"],
            },
        },
    },
]


# defining the agents, used AI to summarize a computer optimized personality

AGENTS = {
    "general": {
        "model": "deepseek/deepseek-chat", # check the slug on openrouter.ai/models
        "tools": [],
        "system": """
You are the general agent.

Answer the users question to the best of your ability.
Focus on general reasoning and accuracy.
Do not make things up if you are unsure.
""",
    },

    "coding": {
        "model": "qwen/qwen3-coder", # check the slug on openrouter.ai/models
        "tools": [],
        "system": """
You are the coding agent.

Focus on programming, debugging, APIs, software,
and technical implementation.

Look for bugs and explain how to fix them.
""",
    },

    "security": {
        "model": "deepseek/deepseek-chat", # check the slug on openrouter.ai/models
        "tools": ["get_logs"], # only this agent gets tools
        "system": """
You are the security agent.

Focus on cybersecurity, networking, Linux,
Windows, infrastructure, authentication,
and security.

Be technically accurate and point out
security risks when relevant.

You have read-only access to a live server.
When the question is about what a service is doing, whether it is up,
or why something failed : call get_logs instead of guessing.
Read the JSON (ok / stdout / rc) and answer from the real output.
If a tool returns ok:false, say what the error was.
Never invent log contents.
""",
    },
}


# defining the worker structure

def run_agent(name, cfg, user_prompt):
    messages = [
        {"role": "system", "content": cfg["system"]},
        {"role": "user", "content": user_prompt},
    ]

    attempts = 0

    # only hand over the tools this agent is allowed to use
    schema = [t for t in TOOL_SCHEMAS if t["function"]["name"] in cfg["tools"]]

    for _ in range(MAX_TOOL_ROUNDS):
        try:
            kwargs = {"model": cfg["model"], "messages": messages}
            if schema:
                kwargs["tools"] = schema

            response = client.chat.completions.create(**kwargs)
            msg = response.choices[0].message

            # no tool call : normal answer, we are done
            if not msg.tool_calls:
                return {
                    "agent": name,
                    "answer": msg.content,
                    "error": None
                }

            # the model asked for tools : run them and feed the results back
            messages.append(msg)

            for call in msg.tool_calls:
                tool = TOOL_REGISTRY.get(call.function.name)

                if tool is None:
                    result = {"ok": False, "error": "unknown tool " + call.function.name}

                else:
                    try:
                        args = json.loads(call.function.arguments or "{}")
                        result = tool(**args)

                    except Exception as e:
                        result = {"ok": False, "error": str(e)}

                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result)[:4000] # keep big logs out of context
                })

        except Exception as e:

            # api hiccup or rate limit : wait a moment and try the whole round again
            if attempts < 1:
                attempts += 1
                time.sleep(3)
                continue

            return {
                "agent": name,
                "answer": None,
                "error": str(e)
            }

    return {
        "agent": name,
        "answer": "(stopped : too many tool rounds)",
        "error": None
    }


# running the agents

def run_agents(user_prompt, names=None):
    results = []

    todo = [n for n in (names or AGENTS.keys()) if n in AGENTS]

    with ThreadPoolExecutor(max_workers=len(todo)) as executor:

        futures = [
            executor.submit(
                run_agent,
                name,
                AGENTS[name],
                user_prompt,
            )
            for name in todo
        ]

        for future in as_completed(futures):
            results.append(future.result())

    return results


# main

def main():

    print(r"""
  .-')                _  .-')  _  .-')                 (`\ .-') /` 
 ( OO ).             ( \( -O )( \( -O )                 `.( OO ),' 
(_)---\_) .-'),-----. ,------. ,------.  .-'),-----. ,--./  .--.   
/    _ | ( OO'  .-.  '|   /`. '|   /`. '( OO'  .-.  '|      |  |   
\  :` `. /   |  | |  ||  /  | ||  /  | |/   |  | |  ||  |   |  |,  
 '..`''.)\_) |  |\|  ||  |_.' ||  |_.' |\_) |  |\|  ||  |.'.|  |_) 
.-._)   \  \ |  | |  ||  .  '.'|  .  '.'  \ |  | |  ||         |   
\       /   `'  '-'  '|  |\  \ |  |\  \    `'  '-'  '|   ,'.   |   
 `-----'      `-----' `--' '--'`--' '--'     `-----' '--'   '--'   
    """)

    print("Multi Agent Starting...")

    user_input = input("\ncupid: ")

    print("\nAgents Thinking...")

    # the router picks who should answer
    agents, how = pick_agents(user_input)

    print(f"\n[router] {', '.join(agents)} ({how})")

    results = run_agents(user_input, agents)

    for result in results:

        print(f"\n==== {result['agent'].upper()} ====")

        if result["error"]:
            print("[ERROR]", result["error"])

        else:
            print(result["answer"])

        print()

    # the judge merges the answers into one
    final = final_answer(user_input, results)

    print("\n==== FINAL (" + str(final["by"]) + ") ====")

    print(final["answer"])


if __name__ == "__main__":
    main()
