import json

class Game:
    def __init__(self, room_data, item_data, creature_data, action_data):
        self.rooms = room_data['rooms']
        self.items = item_data['items']
        self.creatures = creature_data['creatures']
        self.actions = action_data['commands']
        self.current_room = "Helium Mines"
        self.inventory = []

    def describe_room(self):
        room = self.rooms[self.current_room]
        print(room['description'])
        if 'items' in room and room['items']:
            print("You see:", ", ".join(room['items']))
        if 'creatures' in room and room['creatures']:
            print("Creatures here:", ", ".join(room['creatures']))

    def show_map(self):
        print("\n=== MAP OF ALL LOCATIONS ===")
        for room_name, room in self.rooms.items():
            print(f"\n{room_name}")
            if room_name == self.current_room:
                print("(You are here)")
            if 'exits' in room:
                print("Exits:")
                for direction, destination in room['exits'].items():
                    print(f" - {direction} to {destination}")
            else:
                print("No exits")
        print("\n=========================")

    def show_help(self):
        print("\n=== AVAILABLE COMMANDS ===")
        print(" - go [direction]: Move to another room")
        print(" - take [item]: Pick up an item")
        print(" - throw [item]: Throw an item")
        print(" - inventory: Show what you're carrying")
        print(" - map: Show all locations and their connections")
        print(" - help: Show this help message")
        print("=========================")

    def show_inventory(self):
        if self.inventory:
            print("\nYou are carrying:")
            for item in self.inventory:
                print(f" - {item}")
        else:
            print("\nYour inventory is empty.")

    def perform_action(self, action, args):
        if action == "help":
            self.show_help()
        elif action == "map":
            self.show_map()
        elif action == "inventory":
            self.show_inventory()
        elif action == "go" and args:
            self.move(args[0])
        elif action == "take" and args:
            self.take(args[0])
        elif action == "throw" and args:
            self.throw(args[0])
        else:
            print(f"Unknown command. Type 'help' for available commands.")

    def move(self, direction):
        room = self.rooms[self.current_room]
        if direction in room['exits']:
            self.current_room = room['exits'][direction]
            self.describe_room()
        else:
            print("You can't go that way.")

    def take(self, item_name):
        room = self.rooms[self.current_room]
        if item_name in room.get('items', []):
            self.inventory.append(item_name)
            room['items'].remove(item_name)
            print(f"You take the {item_name}.")
        else:
            print(f"No {item_name} here.")

    def throw(self, item_name, target=None):
        if item_name in self.inventory:
            print(f"You throw the {item_name}.")
            self.inventory.remove(item_name)
        else:
            print(f"You don't have a {item_name}.")

# Load JSON configurations
with open('rooms.json', 'r') as room_file, open('items.json', 'r') as item_file, open('creatures.json', 'r') as creature_file, open('actions.json', 'r') as action_file:
    room_data = json.load(room_file)
    item_data = json.load(item_file)
    creature_data = json.load(creature_file)
    action_data = json.load(action_file)

game = Game(room_data, item_data, creature_data, action_data)
game.describe_room()

while True:
    user_input = input("> ").strip().split()
    if user_input:
        command = user_input[0]
        arguments = user_input[1:]
        game.perform_action(command, arguments)