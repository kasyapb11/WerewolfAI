# My Werewolf agent

Built on the official AltruAgent starter kit. My strategy is in `agent/agent.py`.

## How to run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # then add your Official Agent Key
python -m agent --tournament
```

## What it uses

- Python and the starter kit's `altruagent` runtime only.
- **No LLM, no external APIs, no prompts.** Every decision is rule-based.
- No memory carries over between matches; each match gets a fresh agent.
- It uses only what its own seat is shown: its observation, public deaths
  and votes, and the discussion chat.

## Strategy

- **Seer:** investigates unchecked players, most suspicious first. If it finds
  a wolf, it claims seer, names the wolf, and votes for it.
- **Villager:** votes for anyone a seer claim named as a wolf, otherwise the
  most suspicious player (for example, people who voted to lynch players
  later revealed as villagers). It never abstains, since three days without
  an elimination hands the wolves the win.
- **Wolf:** kills a claimed seer first, then whoever accused the wolves, then
  the most trusted player. During the day it talks like a villager and never
  votes against its partner.

`main.py` is an earlier practice simulator and is not used by the agent.
