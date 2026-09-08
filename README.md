# ai-agents

```text
┌─────────────────────────────────────────┐
│              AI AGENTS                  │
│                                         │
│  What is this?                          │
│  Why did you build it?                  │
│  How does it work?                      │
│  How do I run it?                       │
│  What did you discover?                 │
│                                         │
│  Architecture diagram                   │
│  Screenshots / demo                     │
│  Results                                │
│  Future work                            │
└─────────────────────────────────────────┘
```

This is a project I made to manage my home lab.

I built it because I regularly use different AI agents for different things, and I needed continuity as well as security across all my systems.




[9/3/26] 
- Added the very very base function to make the ai out put what i ask it
- Configured API keys in .env 

\(^o^)/ chat gpt crashed and gemeni is awful 


# Overall Structure

                       ┌── DeepSeek ─────── General
                       │
User → Task Router ────┼── Qwen3-Coder ──── Coding
                       │
                       └── Qwen3/DeepSeek ─ Security
                                │
                                ▼
                     Hermes DeepSeek Judge
                                │
                                ▼
                         Final Response


for this im using Qwen3/deepseek 

* Each agent is designed to not know about each other, to get the most unbiases normal anwser 



[UPDATES]
- rewrote old `main.py` it now uses openrouter for all 3 agents with different instructions 
- updated `.env` with OPENROUTER keys

[UP NEXT]
- move personalities/instructions to /dev eventually 