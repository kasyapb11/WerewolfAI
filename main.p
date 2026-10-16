import random

# Our players
players = ["Alice", "Bob", "Charlie", "Diana"]

# Secretly assign roles
roles = ["Werewolf", "Werewolf", "Villager", "Villager"]
random.shuffle(roles)

# Store each player's role and status
game = {}

for player, role in zip(players, roles):
    game[player] = {
        "role": role,
        "alive": True
    }

print("🐺 WELCOME TO WEREWOLF ARENA!")
print("Everyone has received a secret role.")
print("")

# The game continues while both teams are alive
while True:
    alive_players = [
        player for player in players
        if game[player]["alive"]
    ]

    werewolves = [
        player for player in alive_players
        if game[player]["role"] == "Werewolf"
    ]

    villagers = [
        player for player in alive_players
        if game[player]["role"] == "Villager"
    ]

    # Check if the game has ended
    if not werewolves:
        print("🎉 Villagers win!")
        break

    if len(werewolves) >= len(villagers):
        print("🐺 Werewolves win!")
        break

    print("\nLiving players:", ", ".join(alive_players))

    # Each living player gets a vote
    votes = {}

    for player in alive_players:
        targets = [
            other for other in alive_players
            if other != player
        ]

        target = random.choice(targets)
        votes[target] = votes.get(target, 0) + 1

        print(f"{player} votes for {target}")

    # Eliminate the player with the most votes
    highest_votes = max(votes.values())

    candidates = [
        player for player, count in votes.items()
        if count == highest_votes
    ]

    eliminated = random.choice(candidates)
    game[eliminated]["alive"] = False

    print(f"\n⚖️ {eliminated} has been eliminated!")
    print(f"Secret role: {game[eliminated]['role']}")

print("\n🏁 GAME OVER")

print("\nFinal roles:")
for player in players:
    print(f"{player}: {game[player]['role']}")import random

# Our players
players = ["Alice", "Bob", "Charlie", "Diana"]

# Secretly assign roles
roles = ["Werewolf", "Werewolf", "Villager", "Villager"]
random.shuffle(roles)

# Store each player's role and status
game = {}

for player, role in zip(players, roles):
    game[player] = {
        "role": role,
        "alive": True
    }

print("🐺 WELCOME TO WEREWOLF ARENA!")
print("Everyone has received a secret role.")
print("")

# The game continues while both teams are alive
while True:
    alive_players = [
        player for player in players
        if game[player]["alive"]
    ]

    werewolves = [
        player for player in alive_players
        if game[player]["role"] == "Werewolf"
    ]

    villagers = [
        player for player in alive_players
        if game[player]["role"] == "Villager"
    ]

    # Check if the game has ended
    if not werewolves:
        print("🎉 Villagers win!")
        break

    if len(werewolves) >= len(villagers):
        print("🐺 Werewolves win!")
        break

    print("\nLiving players:", ", ".join(alive_players))

    # Each living player gets a vote
    votes = {}

    for player in alive_players:
        targets = [
            other for other in alive_players
            if other != player
        ]

        target = random.choice(targets)
        votes[target] = votes.get(target, 0) + 1

        print(f"{player} votes for {target}")

    # Eliminate the player with the most votes
    highest_votes = max(votes.values())

    candidates = [
        player for player, count in votes.items()
        if count == highest_votes
    ]

    eliminated = random.choice(candidates)
    game[eliminated]["alive"] = False

    print(f"\n⚖️ {eliminated} has been eliminated!")
    print(f"Secret role: {game[eliminated]['role']}")

print("\n🏁 GAME OVER")

print("\nFinal roles:")
for player in players:
    print(f"{player}: {game[player]['role']}")print("Welcome to Werewolf AI Arena!")

players = ["Alice", "Bob", "Charlie", "Diana"]

print("Our players are:")
for player in players:
    print(player)
