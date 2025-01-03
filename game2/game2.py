import json

# Classes for the game
class Room:
    def __init__(self, name, description, items, connections):
        self.name = name
        self.description = description
        self.items = items
        self.connections = connections

class Item:
    def __init__(self, name, description, use):
        self.name = name
        self.description = description
        self.use = use

class Game:
    def __init__(self):
        self.rooms = {}
        self.items = {}
        self.actions = {}
        self.current_room = None
        self.inventory = []

    def load_data(self):
        with open('rooms.json') as f:
            rooms_data = json.load(f)
        with open('items.json') as f:
            items_data = json.load(f)
        with open('actions.json') as f:
            actions_data = json.load(f)

        for room_name, room_info in rooms_data.items():
            self.rooms[room_name] = Room(
                name=room_name,
                description=room_info["description"],
                items=room_info["items"],
                connections=room_info["connections"]
            )

        for item_name, item_info in items_data.items():
            self.items[item_name] = Item(
                name=item_name,
                description=item_info["description"],
                use=item_info["use"]
            )

        self.actions = actions_data
        self.current_room = self.rooms["Grand Atrium"]

    def describe_room(self):
        room = self.current_room
        print(f"\n{room.name}")
        print(room.description)
        if room.items:
            print("Items in the room:")
            for item in room.items:
                print(f" - {item}")

    def move(self, direction):
        if direction in self.current_room.connections:
            self.current_room = self.rooms[self.current_room.connections[direction]]
            self.describe_room()
        else:
            print("You can't go that way.")

    def take_item(self, item_name):
        if item_name in self.current_room.items:
            self.inventory.append(item_name)
            self.current_room.items.remove(item_name)
            print(f"You have taken the {item_name}.")
        else:
            print(f"There is no {item_name} here.")

    def use_item(self, item_name):
        if item_name in self.inventory:
            action = self.actions.get(item_name)
            if action and self.current_room.name in action:
                result = action[self.current_room.name]
                print(result["success"])
                if "effect" in result:
                    for effect in result["effect"]:
                        self.rooms[effect["room"]].items.append(effect["item"])
            else:
                print(f"The {item_name} can't be used here.")
        else:
            print(f"You don't have the {item_name}.")

    def show_inventory(self):
        if self.inventory:
            print("You are carrying:")
            for item in self.inventory:
                print(f" - {item}")
        else:
            print("Your inventory is empty.")

    def show_map(self):
        room = self.current_room
        print(f"\nYou are in the {room.name}")
        if room.connections:
            print("You can go:")
            for direction, destination in room.connections.items():
                print(f" - {direction} to {destination}")
        else:
            print("There are no obvious exits.")

    def play(self):
        self.describe_room()
        while True:
            command = input("\nEnter a command: ").strip().lower()
            if command in ["quit", "exit"]:
                print("Thanks for playing!")
                break
            elif command == "help":
                print("\nAvailable commands:")
                print(" - go [direction]: Move in a direction (north, south, east, west)")
                print(" - take [item]: Pick up an item from the room")
                print(" - use [item]: Use an item from your inventory")
                print(" - inventory: Show your current inventory")
                print(" - map: Show your current location and possible exits")
                print(" - help: Show this help message")
                print(" - quit/exit: End the game")
            elif command == "map":
                self.show_map()
            elif command.startswith("go "):
                direction = command.split(" ")[1]
                self.move(direction)
            elif command.startswith("take "):
                item_name = command.split(" ", 1)[1]
                self.take_item(item_name)
            elif command.startswith("use "):
                item_name = command.split(" ", 1)[1]
                self.use_item(item_name)
            elif command == "inventory":
                self.show_inventory()
            else:
                print("Unknown command.")

# Main game execution
if __name__ == "__main__":
    game = Game()
    game.load_data()
    game.play()
