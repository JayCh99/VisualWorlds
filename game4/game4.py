import os
import json
import hashlib
from openai import OpenAI
import google.generativeai as genai
from typing import Dict, List, Optional
import tkinter as tk
from PIL import Image, ImageTk
import requests
from io import BytesIO
from enum import Enum
import typing_extensions as typing


class Direction(str, Enum):
    NORTH = "north"
    SOUTH = "south"
    EAST = "east"
    WEST = "west"

class RoomDict(typing.TypedDict):
    name: str
    description: str
    image_prompt: str

class ConnectionDict(typing.TypedDict):
    room1: str
    room2: str
    direction: str

class WorldSetup(typing.TypedDict):
    rooms: List[RoomDict]
    connections: List[ConnectionDict]

class Room:
    def __init__(self, name: str, description: str, image_prompt: str):
        self.name = name
        self.description = description
        self.image_prompt = image_prompt
        self.image_path: Optional[str] = None
        self.connections: Dict[Direction, Optional[str]] = {
            Direction.NORTH: None,
            Direction.SOUTH: None,
            Direction.EAST: None,
            Direction.WEST: None
        }

class GameWorld:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.current_room: Optional[Room] = None
        os.environ["OPENAI_API_KEY"] = "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"
        self.openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    def add_room(self, room: Room):
        self.rooms[room.name] = room
        if not self.current_room:
            self.current_room = room

    def connect_rooms(self, room1_name: str, room2_name: str, direction: Direction):
        if room1_name not in self.rooms or room2_name not in self.rooms:
            return
            
        opposite = {
            Direction.NORTH: Direction.SOUTH,
            Direction.SOUTH: Direction.NORTH,
            Direction.EAST: Direction.WEST,
            Direction.WEST: Direction.EAST
        }
        room1 = self.rooms[room1_name]
        room2 = self.rooms[room2_name]
        room1.connections[direction] = room2
        # room2.connections[opposite[direction]] = room1

    def generate_room_image(self, room: Room):
        try:
            # Create hash from room properties
            room_hash = hashlib.sha256(
                f"{room.name}{room.description}{room.image_prompt}".encode()
            ).hexdigest()
            
            # Check if image already exists
            image_path = f"room_images/{room_hash}.png"
            if os.path.exists(image_path):
                room.image_path = image_path
                return image_path
            
            # Generate new image if it doesn't exist
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=room.image_prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            # Download the image
            image_url = response.data[0].url
            response = requests.get(image_url)
            img_data = BytesIO(response.content)
            
            # Save the image using hash
            os.makedirs("room_images", exist_ok=True)
            with open(image_path, "wb") as f:
                f.write(img_data.getbuffer())
            
            room.image_path = image_path
            return image_path
        except Exception as e:
            print(f"Error generating image for room {room.name}: {e}")
            return None

class GameUI:
    def __init__(self, game_world: GameWorld):
        self.game_world = game_world
        self.root = tk.Tk()
        self.root.title("Text Adventure")
        
        # Create main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(padx=10, pady=10)
        
        # Image display
        self.image_label = tk.Label(self.main_frame)
        self.image_label.pack()
        
        # Room description
        self.description_text = tk.Text(self.main_frame, height=10, width=50)
        self.description_text.pack(pady=10)
        
        # Navigation buttons frame
        self.nav_frame = tk.Frame(self.main_frame)
        self.nav_frame.pack()
        
        # Create navigation buttons
        self.create_navigation_buttons()
        
        # Bind arrow keys
        self.root.bind('<Left>', lambda e: self.move('west'))
        self.root.bind('<Right>', lambda e: self.move('east'))
        self.root.bind('<Up>', lambda e: self.move('north'))
        self.root.bind('<Down>', lambda e: self.move('south'))
        
        self.update_display()

    def create_navigation_buttons(self):
        # North
        self.north_button = tk.Button(self.nav_frame, text="North", command=lambda: self.move('north'))
        self.north_button.grid(row=0, column=1)
        
        # West
        self.west_button = tk.Button(self.nav_frame, text="West", command=lambda: self.move('west'))
        self.west_button.grid(row=1, column=0)
        
        # East
        self.east_button = tk.Button(self.nav_frame, text="East", command=lambda: self.move('east'))
        self.east_button.grid(row=1, column=2)
        
        # South
        self.south_button = tk.Button(self.nav_frame, text="South", command=lambda: self.move('south'))
        self.south_button.grid(row=2, column=1)

    def move(self, direction: str):
        if not self.game_world.current_room:
            return
            
        next_room = self.game_world.current_room.connections[direction]
        if next_room:
            self.game_world.current_room = next_room
            self.update_display()

    def update_display(self):
        if not self.game_world.current_room:
            return
            
        # Update description
        self.description_text.delete(1.0, tk.END)
        self.description_text.insert(tk.END, f"Current Room: {self.game_world.current_room.name}\n\n")
        self.description_text.insert(tk.END, self.game_world.current_room.description)
        
        # Update image
        if self.game_world.current_room.image_path:
            image = Image.open(self.game_world.current_room.image_path)
            image = image.resize((512, 512))  # Resize for display
            photo = ImageTk.PhotoImage(image)
            self.image_label.configure(image=photo)
            self.image_label.image = photo

        # Update button states
        self.north_button.config(state=tk.NORMAL if self.game_world.current_room.connections[Direction.NORTH] else tk.DISABLED)
        self.south_button.config(state=tk.NORMAL if self.game_world.current_room.connections[Direction.SOUTH] else tk.DISABLED)
        self.east_button.config(state=tk.NORMAL if self.game_world.current_room.connections[Direction.EAST] else tk.DISABLED)
        self.west_button.config(state=tk.NORMAL if self.game_world.current_room.connections[Direction.WEST] else tk.DISABLED)

    def run(self):
        self.root.mainloop()


def process_book_with_gemini(pdf_path: str, setting_desc: str, protagonist_desc: str):
    # TODO: Fix
    os.environ["GOOGLE_API_KEY"] = "AIzaSyDD9YRzLbPU1o-XehqkvvQD9PLG0rokBws"
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    
    uploaded_file = genai.upload_file(path=pdf_path, display_name="Red Rising") 
    print(f"Uploaded file '{uploaded_file.display_name}' as: {uploaded_file.uri}")
    model = genai.GenerativeModel("gemini-1.5-flash") 

    # My code
    prompt1 = f"""
    Generate a world setup for a text adventure game based on the attached book.

    Create a world with up to 6 rooms. Provide:
    1. A list of rooms with descriptions and image prompts that reference the book
    2. A list of connections between the rooms detailed above, specifying which rooms connect and in what direction. Make sure all rooms are reachable from every other room through some path and only use rooms that are in the list above.
    
    For each room include:
    - A name (100 characters max, don't include new lines)
    - A description referencing the book (50 words max, don't include new lines)
    - An image prompt for DALL-E to generate an illustration (100 words max, don't include new lines)
    
    For connections, specify:
    - Which two rooms are connected
    - The direction (north, south, east, or west)
    """
    
    summary = model.generate_content(
        [uploaded_file, prompt1], 
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json", 
            response_schema=WorldSetup
        )
    )
    print("Summary:\n", summary.text)
    return summary.text


def run_game():
    # Initialize game world
    game_world = GameWorld()

    with open('game_data.json', 'r') as f:
        data = json.load(f)
        world_data = json.loads(data['world'])  # Parse the string into JSON
        rooms = world_data['rooms']
        connections = world_data['connections']
    
    # Create rooms first
    for room_data in rooms:
        room = Room(room_data["name"], room_data["description"], room_data["image_prompt"])
        game_world.add_room(room)
        game_world.generate_room_image(room)
    
    # Then set up connections
    for conn in connections:
        game_world.connect_rooms(conn["room1"], conn["room2"], Direction(conn["direction"]))
    
    # Start the game UI
    game_ui = GameUI(game_world)
    game_ui.run()


def generate_game_data():
    world_setup = process_book_with_gemini("Golden_Son_Red_Rising_Saga_2_-_Pierce_Brown.pdf", 
                                         "A mysterious Victorian mansion", 
                                         "A curious explorer seeking ancient secrets")

    with open('game_data.json', 'w') as f:
        json.dump({'world': world_setup}, f)
    
    # Load and print
    with open('game_data.json', 'r') as f:
        data = json.load(f)
        world_data = json.loads(data['world'])
        print(world_data)


if __name__ == "__main__":
    # generate_game_data()
    run_game()


