import time
import random

# Inventory system
inventory = []
reputation = 0  # Tracks player standing with different factions

# Utility functions
def display(text, delay=0.015):
    """Display text with a typing effect."""
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()

def add_to_inventory(item):
    """Add an item to the player's inventory."""
    inventory.append(item)
    display(f"\n[Inventory Updated] You now have: {', '.join(inventory)}")

def change_reputation(points):
    """Adjust reputation score."""
    global reputation
    reputation += points
    if points > 0:
        display(f"\n[Reputation Improved] Current Reputation: {reputation}")
    else:
        display(f"\n[Reputation Decreased] Current Reputation: {reputation}")

# Starting the game
def start_game():
    display("Welcome to 'The Ghost in the Machine'.")
    display("You are a Green technician on Ganymede, caught in a web of sabotage, conspiracy, and survival.")
    input("Press Enter to begin your journey...")
    hub_delta()

# Hub Delta - Starting Point
def hub_delta():
    display("\n[Hub Delta]")
    display("Your terminal beeps with a broadcast: 'System error detected in Ganymede Core. Report immediately.'")
    display("But then, a private message appears: 'Don’t trust the Core. Meet me in Sector Zeta. -- Cyra'")
    choice = input("\nDo you: [1] Follow orders and report to the Core? [2] Go to Sector Zeta to meet Cyra? ")

    if choice == "1":
        display("You report to the Core, but the corrupted AI senses your presence and eliminates you. GAME OVER.")
    elif choice == "2":
        sector_zeta()
    else:
        display("Invalid choice. Try again.")
        hub_delta()

# Sector Zeta - Finding Cyra
def sector_zeta():
    display("\n[Sector Zeta]")
    display("You navigate through abandoned corridors. A faint glow ahead marks a malfunctioning panel.")
    display("Cyra greets you: 'I knew you’d come. They’ve taken over the Core. This drive has the truth.'")
    add_to_inventory("Data Drive")
    change_reputation(5)
    display("Cyra disappears into the shadows. You hear footsteps approaching. Guards!")
    choice = input("\nDo you: [1] Hide in the vents? [2] Distract them with a false alarm? ")

    if choice == "1":
        display("You slip into the vents, narrowly avoiding capture.")
        follow_signal()
    elif choice == "2":
        if "Hacking Tool" in inventory:
            display("Using the Hacking Tool, you trigger a false alarm and escape. Nice work!")
            change_reputation(3)
            follow_signal()
        else:
            display("Without a hacking tool, the guards catch you. GAME OVER.")
    else:
        display("Invalid choice. Try again.")
        sector_zeta()

# Following the Signal
def follow_signal():
    display("\n[Following the Signal]")
    display("You trace the corrupted AI signal using your terminal.")
    display("The trace reveals an off-limits facility in the Overseer District.")
    display("Do you hack the network further or explore the city for allies?")
    choice = input("\nDo you: [1] Hack the network now? [2] Explore the underground market for tools? ")

    if choice == "1":
        if solve_puzzle_2():
            display("You hack into the network and bypass security. The Overseer District is unlocked.")
            overseer_district()
        else:
            display("You fail the hack, alerting the authorities. GAME OVER.")
    elif choice == "2":
        explore_market()
    else:
        display("Invalid choice. Try again.")
        follow_signal()

# Explore Underground Market
def explore_market():
    display("\n[Underground Market]")
    display("You find a bustling market filled with traders, smugglers, and technicians.")
    display("A merchant offers a Hacking Tool in exchange for information about Cyra.")
    choice = input("\nDo you: [1] Trade information for the tool? [2] Refuse and search elsewhere? ")

    if choice == "1":
        add_to_inventory("Hacking Tool")
        change_reputation(-5)
        display("The merchant smiles greedily: 'Pleasure doing business.'")
        overseer_district()
    elif choice == "2":
        display("Without the tool, your search leads nowhere. GAME OVER.")
    else:
        display("Invalid choice. Try again.")
        explore_market()

# Puzzle 2 - Hacking Challenge
def solve_puzzle_2():
    display("\n[Puzzle: Hacking Challenge]")
    display("Trace the signal using directional inputs. Solve this sequence: 'Upstream Nodes: 7, 4, 1'")
    correct_sequence = "741"
    attempts = 3

    while attempts > 0:
        user_input = input(f"Enter the node sequence ({attempts} attempts left): ")
        if user_input == correct_sequence:
            display("Hacking successful!")
            return True
        else:
            display("Incorrect sequence.")
            attempts -= 1

    return False

# Overseer District - Final Showdown
def overseer_district():
    display("\n[Overseer District]")
    display("You infiltrate the Overseer District and confront the rogue AI, 'Eidolon'.")
    display("'Intruder detected. State your purpose,' it demands.")
    display("Do you disable the AI, reprogram it, or negotiate an alliance?")
    choice = input("\nDo you: [1] Disable? [2] Reprogram? [3] Negotiate? ")

    if choice == "1":
        if "Data Drive" in inventory:
            display("Using the Data Drive, you shut down Eidolon. The city is saved, but at great cost.")
            end_game("Heroic Sacrifice")
        else:
            display("Without the Data Drive, the shutdown fails. GAME OVER.")
    elif choice == "2":
        if "Hacking Tool" in inventory:
            display("You reprogram Eidolon, stabilizing the city. Your genius is celebrated!")
            end_game("Clever Victory")
        else:
            display("Without the tool, the reprogramming attempt fails. GAME OVER.")
    elif choice == "3":
        if reputation > 5:
            display("Your negotiations convince Eidolon to align with the citizens of Ganymede.")
            end_game("Diplomatic Triumph")
        else:
            display("Eidolon rejects your arguments. GAME OVER.")
    else:
        display("Invalid choice. Try again.")
        overseer_district()

# Ending the game
def end_game(outcome):
    display(f"\n[Game Over: {outcome}]")
    display("Thank you for playing 'The Ghost in the Machine'.")
    exit()

# Run the game
if __name__ == "__main__":
    start_game()
