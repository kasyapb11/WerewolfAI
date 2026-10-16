import random

# ============================================
# WEREWOLF AI ARENA - VERSION 4
# Night attacks, discussion, voting history,
# and suspicion scores
# ============================================

# Create seven players
players = [
    "Alice",
    "Bob",
    "Charlie",
    "Diana",
    "Eve",
    "Frank",
    "Grace"
]

# Assign two Werewolves and five Villagers
roles = [
    "Werewolf",
    "Werewolf",
    "Villager",
    "Villager",
    "Villager",
    "Villager",
    "Villager"
]

# Shuffle roles randomly
random.shuffle(roles)

# Store each player's secret role and status
game = {}

for player, role in zip(players, roles):
    game[player] = {
        "role": role,
        "alive": True
    }

# Remember votes throughout the game
voting_history = []

# Track suspicion for each player
suspicion = {}

for player in players:
    suspicion[player] = 0


# ============================================
# GAME HELPER FUNCTIONS
# ============================================

def living_players():
    """Return all players who are still alive."""
    return [
        player for player in players
        if game[player]["alive"]
    ]


def check_winner():
    """Check whether either team has won."""
    alive = living_players()

    werewolves = [
        player for player in alive
        if game[player]["role"] == "Werewolf"
    ]

    villagers = [
        player for player in alive
        if game[player]["role"] == "Villager"
    ]

    if len(werewolves) == 0:
        print("\nTHE VILLAGERS WIN!")
        return True

    if len(werewolves) >= len(villagers):
        print("\nTHE WEREWOLVES WIN!")
        return True

    return False


def discussion_phase(alive_players):
    """Print a random discussion statement for each player."""
    print("\nThe villagers begin discussing...")

    statements = [
        "I think we should examine the voting patterns.",
        "Someone here is hiding something.",
        "We need to be careful before accusing anyone.",
        "I suspect someone is trying to manipulate us.",
        "Let's hear everyone's reasoning before we vote."
    ]

    for player in alive_players:
        message = random.choice(statements)
        print(f"\n{player}: {message}")


# ============================================
# START THE GAME
# ============================================

print("=" * 40)
print("       WEREWOLF AI ARENA")
print("=" * 40)
print(f"{len(players)} players enter the village.")
print("Two are secretly Werewolves!")
print("")

round_number = 1

while True:

    # ========================================
    # NIGHT PHASE
    # ========================================

    print(f"\n{'=' * 12} NIGHT {round_number} {'=' * 12}")

    alive = living_players()

    werewolves = [
        player for player in alive
        if game[player]["role"] == "Werewolf"
    ]

    victims = [
        player for player in alive
        if game[player]["role"] == "Villager"
    ]

    # Werewolves secretly attack a Villager
    if werewolves and victims:
        victim = random.choice(victims)
        game[victim]["alive"] = False

        print("The village sleeps...")
        print("A Werewolf attack occurs!")
        print(f"{victim} was eliminated during the night.")

    # Check for a winner after the night attack
    if check_winner():
        break

    # ========================================
    # DAY PHASE
    # ========================================

    print(f"\n{'=' * 12} DAY {round_number} {'=' * 12}")

    alive = living_players()

    print("Living players:", ", ".join(alive))

    # Players discuss their suspicions
    discussion_phase(alive)

    # Everyone votes
    print("\nEveryone votes to eliminate a suspect.")

    votes = {}

    for player in alive:

        # Players cannot vote for themselves
        targets = [
            other for other in alive
            if other != player
        ]

        target = random.choice(targets)

        votes[target] = votes.get(target, 0) + 1

        # Record this vote
        voting_history.append({
            "round": round_number,
            "voter": player,
            "target": target
        })

        print(f"{player} votes for {target}")

    # Find the player with the most votes
    highest_votes = max(votes.values())

    candidates = [
        player for player, count in votes.items()
        if count == highest_votes
    ]

    # Randomly resolve a tie
    eliminated = random.choice(candidates)

    game[eliminated]["alive"] = False

    print(f"\n{eliminated} was voted out!")
    print(f"Revealed role: {game[eliminated]['role']}")

    # ========================================
    # UPDATE SUSPICION SCORES
    # ========================================

    # Players who voted for an eliminated Villager
    # receive one suspicion point.
    if game[eliminated]["role"] == "Villager":

        for vote in voting_history:
            if (
                vote["round"] == round_number
                and vote["target"] == eliminated
            ):
                suspicion[vote["voter"]] += 1

    # Check for a winner after the vote
    if check_winner():
        break

    round_number += 1


# ============================================
# GAME OVER: REVEAL ALL ROLES
# ============================================

print("\n" + "=" * 40)
print("             GAME OVER")
print("=" * 40)

print("\nFinal roles:")

for player in players:
    status = (
        "Alive"
        if game[player]["alive"]
        else "Eliminated"
    )

    print(f"{player}: {game[player]['role']} ({status})")


# ============================================
# DISPLAY VOTING HISTORY
# ============================================

print("\n" + "=" * 40)
print("           VOTING HISTORY")
print("=" * 40)

if not voting_history:
    print("No votes were cast.")
else:
    for vote in voting_history:
        print(
            f"Round {vote['round']}: "
            f"{vote['voter']} voted for "
            f"{vote['target']}"
        )


# ============================================
# DISPLAY SUSPICION SCORES
# ============================================

print("\n" + "=" * 40)
print("          SUSPICION SCORES")
print("=" * 40)

for player in players:
    print(f"{player}: {suspicion[player]}")


print("\nThanks for playing Werewolf AI Arena!")
