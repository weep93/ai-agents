import os

from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

from openai import OpenAI

load_dotenv()


# // config

WORKER_MODEL = "openrouter/free" # defining the AI model

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


# defining the agents

AGENTS = {
    "general": """
You are the general agent.

Answer the users question to the best of your ability.
Focus on general reasoning and accuracy.
Do not make things up if you are unsure.
""",

    "coding": """
You are the coding agent.

Focus on programming, debugging, APIs, software,
and technical implementation.

Look for bugs and explain how to fix them.
""",

    "security": """
You are the security agent.

Focus on cybersecurity, networking, Linux,
Windows, infrastructure, authentication,
and security.

Be technically accurate and point out
security risks when relevant.
"""
}


# defining the worker structure

def run_agent(name, system_prompt, user_prompt):
    try:
        response = client.chat.completions.create(
            model=WORKER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        return {
            "agent": name,
            "answer": response.choices[0].message.content,
            "error": None
        }

    except Exception as e:
        return {
            "agent": name,
            "answer": None,
            "error": str(e)
        }


# running the agents

def run_agents(user_prompt):
    results = []

    with ThreadPoolExecutor(max_workers=3) as executor:

        futures = [
            executor.submit(
                run_agent,
                name,
                system_prompt,
                user_prompt,
            )
            for name, system_prompt in AGENTS.items()
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

    results = run_agents(user_input)

    for result in results:

        print(f"\n==== {result['agent'].upper()} ====")

        if result["error"]:
            print("[ERROR]", result["error"])

        else:
            print(result["answer"])

        print()


if __name__ == "__main__":
    main()
