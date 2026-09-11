import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


# // config

JUDGE_MODEL = "deepseek/deepseek-chat" # merges the worker answers into one

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


# defining the judge

def final_answer(user_prompt, results):
    """Merge the agent answers into one reply. One agent = no judge call needed."""

    good = [r for r in results if r["answer"] and not r["error"]]

    if not good:
        errors = "; ".join(f"{r['agent']}: {r['error']}" for r in results)
        return {"answer": "every agent failed: " + errors, "by": None}

    # nothing to merge : do not waste a call
    if len(good) == 1:
        return {"answer": good[0]["answer"], "by": good[0]["agent"]}

    # tell the judge who dropped out, so it can say so instead of hiding it
    skipped = [r["agent"] for r in results if not (r["answer"] and not r["error"])]

    note = ""
    if skipped:
        note = "Note: these agents failed or returned nothing: " + ", ".join(skipped) + ".\n\n"

    # hand the answers to the judge with the agent names attached
    blocks = []
    for r in good:
        blocks.append("--- " + r["agent"] + " agent ---\n" + r["answer"])

    ask = """You are the judge.

Several agents answered the same task. Merge their answers into ONE final answer.

Rules:
- Keep any concrete facts (log lines, commands, numbers) exactly as given
- If agents disagree, say so, and say which one is right and why
- Do not pad : if one agent already answered well, keep it short
- Never invent anything no agent said

The user task was:
""" + note + user_prompt + "\n\n" + "\n\n".join(blocks)

    try:
        response = client.chat.completions.create(
            model=JUDGE_MODEL,
            messages=[{"role": "user", "content": ask}],
        )
        answer = response.choices[0].message.content

    except Exception as e:
        # the judge died : still give the user the raw answers
        answer = "judge failed (" + str(e) + "). Raw agent answers:\n\n" + "\n\n".join(blocks)

    return {"answer": answer, "by": "judge"}
