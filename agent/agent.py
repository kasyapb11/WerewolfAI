"""Rule-based Werewolf agent for the AltruAgent tournament.

No LLM and no outside services: every decision comes from the rules below,
using only what this seat is shown (its observation, public deaths/votes,
and the discussion chat). A fresh agent is created for each match, so no
memory carries over between games.

Game: 7 players = 2 wolves, 1 seer, 4 villagers. Actions are seat numbers;
"7" means abstain (day vote only).

Strategy summary
- Seer: investigates players it hasn't checked yet (most suspicious first).
  If it finds a wolf, it claims seer in the discussion, names the wolf, and
  votes for it.
- Villager: votes for whoever a seer claim accused; otherwise for the most
  suspicious player. Never abstains, because 3 days with no elimination
  hands the wolves the win.
- Wolf: kills a claimed seer first, then whoever accused the wolves, then
  the most trusted villager. During the day it acts like a villager, never
  votes for its partner, and pushes votes onto the loudest accuser.
"""

from __future__ import annotations

import random
import re

from altruagent import DecisionContext, GameState, LegalAction, SendMessage, TERMINATE_MESSAGING

ABSTAIN = "7"
SEAT_RE = re.compile(r"player\s*(\d+)", re.IGNORECASE)


def _seats_in(text: str) -> list[int]:
    return [int(n) for n in SEAT_RE.findall(text or "")]


class WerewolfAgent:
    def __init__(self) -> None:
        self.me: int | None = None
        self.role: str | None = None          # "wolf", "seer" or "villager"
        self.partner: int | None = None       # the other wolf, if I am a wolf
        self.checked: dict[int, str] = {}     # seer results: seat -> "wolf"/"villager"
        self.cleared: set[int] = set()        # seats publicly revealed as non-wolves
        self.revealed_wolves: set[int] = set()
        self.suspicion: dict[int, float] = {}
        self.seer_claims: dict[int, dict] = {}  # claimer seat -> {"wolves": set, "clear": set}
        self.accused_me: set[int] = set()
        self.seen_messages: set[tuple] = set()
        self.spoke_on_day: int | None = None
        self.messages_today = 0
        self.rng = random.Random()

    # ------------------------------------------------------------ helpers
    def _game_state(self, state: GameState) -> dict:
        return (state.raw.get("game_state") or {}) if isinstance(state.raw, dict) else {}

    def _name_to_seat(self, state: GameState) -> dict[str, int]:
        mapping = {}
        for p in state.raw.get("players") or []:
            try:
                mapping[str(p.get("name"))] = int(p.get("position"))
            except (TypeError, ValueError, AttributeError):
                continue
        return mapping

    def _to_seat(self, value, names: dict[str, int]) -> int | None:
        if isinstance(value, int):
            return value
        if isinstance(value, dict):
            for key in ("position", "seat", "player"):
                if isinstance(value.get(key), int):
                    return value[key]
            value = value.get("name") or value.get("player") or ""
        value = str(value)
        if value in names:
            return names[value]
        seats = _seats_in(value)
        return seats[0] if seats else None

    def _alive(self, state: GameState) -> set[int]:
        names = self._name_to_seat(state)
        alive = set()
        for entry in self._game_state(state).get("alive") or []:
            seat = self._to_seat(entry, names)
            if seat is not None:
                alive.add(seat)
        return alive

    def _update(self, state: GameState, context: DecisionContext) -> None:
        """Refresh what we know from this seat's observation and public info."""
        if self.me is None:
            self.me = context.seat_position
            if self.me is None:
                pos = state.raw.get("your_position")
                self.me = pos if isinstance(pos, int) else None

        obs = state.observation or ""
        low = obs.lower()
        if self.role is None:
            m = re.search(r"role\s*[:=]?\s*(werewolf|wolf|seer|villager)", low)
            if m:
                self.role = "wolf" if "wolf" in m.group(1) else m.group(1)

        # Seer results: any line that names a player and says wolf/villager.
        if self.role == "seer":
            for line in re.split(r"[\n;.]", obs):
                seats = [s for s in _seats_in(line) if s != self.me]
                if len(seats) != 1:
                    continue
                l = line.lower()
                if "wolf" in l and "not" not in l:
                    self.checked[seats[0]] = "wolf"
                elif "villager" in l or "not a wolf" in l or "innocent" in l:
                    self.checked[seats[0]] = "villager"

        # Wolves: the partner is usually named in the observation.
        if self.role == "wolf" and self.partner is None:
            for line in re.split(r"[\n;.]", obs):
                l = line.lower()
                if "wolf" in l or "partner" in l or "ally" in l or "teammate" in l:
                    others = [s for s in _seats_in(line) if s != self.me]
                    if len(others) == 1:
                        self.partner = others[0]
                        break

        # Public deaths reveal true roles.
        names = self._name_to_seat(state)
        for entry in self._game_state(state).get("dead") or []:
            seat = self._to_seat(entry, names)
            if seat is None:
                continue
            text = str(entry).lower()
            if "wolf" in text:
                self.revealed_wolves.add(seat)
            else:
                self.cleared.add(seat)

        self._score_votes(state, names)

    def _score_votes(self, state: GameState, names: dict[str, int]) -> None:
        """Players who voted to lynch a revealed non-wolf look suspicious;
        players who voted for a revealed wolf look trustworthy."""
        history = self._game_state(state).get("vote_history") or []
        score: dict[int, float] = {}
        for day in history if isinstance(history, list) else []:
            votes = day.get("votes") if isinstance(day, dict) else None
            if votes is None and isinstance(day, dict):
                votes = day
            items = votes.items() if isinstance(votes, dict) else []
            for voter, target in items:
                v = self._to_seat(voter, names)
                t = self._to_seat(target, names)
                if v is None or t is None:
                    continue
                if t in self.cleared:
                    score[v] = score.get(v, 0) + 1.0
                if t in self.revealed_wolves:
                    score[v] = score.get(v, 0) - 1.5
        self._vote_score = score

    def _sus(self, seat: int) -> float:
        s = self.suspicion.get(seat, 0.0) + getattr(self, "_vote_score", {}).get(seat, 0.0)
        if seat in self.revealed_wolves:
            s += 100
        if seat in self.cleared:
            s -= 100
        if self.checked.get(seat) == "wolf":
            s += 100
        if self.checked.get(seat) == "villager":
            s -= 100
        # A seer claim from someone we haven't caught lying carries weight.
        for claimer, claim in self.seer_claims.items():
            if claimer == seat:
                continue
            if seat in claim["wolves"]:
                s += 6
            if seat in claim["clear"]:
                s -= 3
        return s

    def _read_chat(self, state: GameState) -> None:
        for msg in state.new_messages or []:
            key = (msg.index, msg.sender, msg.content)
            if key in self.seen_messages or msg.sender == self.me:
                continue
            self.seen_messages.add(key)
            text = (msg.content or "").lower()
            named = [s for s in _seats_in(msg.content) if s != msg.sender]
            if "seer" in text and ("i am" in text or "i'm" in text or "im the" in text):
                claim = self.seer_claims.setdefault(msg.sender, {"wolves": set(), "clear": set()})
                says_wolf = "wolf" in text and "not a wolf" not in text and "not wolf" not in text
                for s in named:
                    (claim["wolves"] if says_wolf else claim["clear"]).add(s)
            elif "wolf" in text or "suspicious" in text or "vote" in text:
                for s in named:
                    self.suspicion[s] = self.suspicion.get(s, 0) + 0.5
                    if s == self.me:
                        self.accused_me.add(msg.sender)
                    if self.role == "wolf" and s == self.partner:
                        self.accused_me.add(msg.sender)

    def _seat_actions(self, state: GameState) -> dict[int, LegalAction]:
        out = {}
        for a in state.legal_actions:
            try:
                out[int(a.action_id)] = a
            except ValueError:
                continue
        return out

    def _pick_max(self, seats, key) -> int:
        seats = list(seats)
        self.rng.shuffle(seats)  # random tie-break
        return max(seats, key=key)

    # ------------------------------------------------------------ actions
    def choose_action(self, state: GameState, context: DecisionContext):
        try:
            return self._choose(state, context)
        except Exception:
            # Never crash a match: fall back to any non-abstain legal move.
            options = [a for a in state.legal_actions if a.action_id != ABSTAIN] or state.legal_actions
            return self.rng.choice(options)

    def _choose(self, state: GameState, context: DecisionContext):
        self._update(state, context)
        self._read_chat(state)
        sub = self._game_state(state).get("phase")
        actions = self._seat_actions(state)
        targets = {s: a for s, a in actions.items() if str(s) != ABSTAIN and s != self.me}

        if sub == "night_wolf" or (self.role == "wolf" and "kill" in str(state.legal_actions[0].label).lower()):
            self.role = "wolf"
            # Anyone alive who is not a legal kill target (and not me) is my partner.
            alive = self._alive(state)
            if self.partner is None and alive:
                others = alive - set(targets) - {self.me}
                if len(others) == 1:
                    self.partner = others.pop()
            return targets[self._wolf_kill(targets)]

        if sub == "night_seer" or "investigate" in str(state.legal_actions[0].label).lower():
            self.role = "seer"
            unchecked = [s for s in targets if s not in self.checked and s not in self.cleared]
            pool = unchecked or list(targets)
            return targets[self._pick_max(pool, self._sus)]

        # Day vote.
        if not targets:
            return state.legal_actions[0]
        return targets[self._day_vote(targets)]

    def _wolf_kill(self, targets: dict[int, LegalAction]) -> int:
        # 1. A player who claimed seer.  2. Someone who accused us.
        # 3. The most trusted player (lowest suspicion) — a strong villager voice.
        claimers = [s for s in targets if s in self.seer_claims]
        if claimers:
            return self._pick_max(claimers, lambda s: len(self.seer_claims[s]["wolves"]))
        accusers = [s for s in targets if s in self.accused_me]
        if accusers:
            return self.rng.choice(accusers)
        return self._pick_max(targets, lambda s: -self._sus(s))

    def _day_vote(self, targets: dict[int, LegalAction]) -> int:
        if self.role == "seer":
            wolves = [s for s in targets if self.checked.get(s) == "wolf"]
            if wolves:
                return wolves[0]
            pool = [s for s in targets if self.checked.get(s) != "villager"] or list(targets)
            return self._pick_max(pool, self._sus)

        if self.role == "wolf":
            pool = [s for s in targets if s != self.partner] or list(targets)
            # Push votes onto whoever accused us or claimed seer; otherwise
            # pile onto the village's top suspect to blend in.
            danger = [s for s in pool if s in self.accused_me or s in self.seer_claims]
            if danger:
                return self._pick_max(danger, lambda s: (s in self.seer_claims, self._sus(s)))
            return self._pick_max(pool, self._sus)

        # Villager (or unknown role).
        return self._pick_max(targets, self._sus)

    # ------------------------------------------------------------ chat
    def choose_message(self, state: GameState, context: DecisionContext):
        try:
            return self._message(state, context)
        except Exception:
            return TERMINATE_MESSAGING

    def _message(self, state: GameState, context: DecisionContext):
        self._update(state, context)
        self._read_chat(state)
        day = self._game_state(state).get("day")
        if self.spoke_on_day == day:
            return TERMINATE_MESSAGING
        self.spoke_on_day = day

        alive = self._alive(state) - {self.me}
        if self.role == "seer":
            wolves = [s for s in alive if self.checked.get(s) == "wolf"]
            if wolves:
                clears = [s for s in alive if self.checked.get(s) == "villager"]
                text = f"I am the seer. Player{wolves[0]} is a wolf. Vote Player{wolves[0]}."
                if clears:
                    text += " " + ", ".join(f"Player{s}" for s in clears) + " checked clean."
                return SendMessage(text)
            return SendMessage("Watch who votes for players later revealed as villagers. That is our best evidence.")

        candidates = [s for s in alive if s != self.partner] if self.role == "wolf" else list(alive)
        if self.role == "wolf":
            danger = [s for s in candidates if s in self.accused_me or s in self.seer_claims]
            if danger:
                t = danger[0]
                return SendMessage(f"I'm a villager. Player{t}'s accusation feels like a wolf deflecting. I'm voting Player{t}.")
        if candidates:
            top = self._pick_max(candidates, self._sus)
            if self._sus(top) > 0:
                return SendMessage(f"I'm a villager. Player{top} looks most suspicious to me from the votes and chat.")
        return SendMessage("I'm a villager. Let's not abstain: a no-lynch day helps the wolves. Pick a target and commit.")


def create_agent():
    return WerewolfAgent()
