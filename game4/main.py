import os
import json
import hashlib
from openai import OpenAI
import google.generativeai as genai
from typing import Dict, List, Optional, Tuple
import tkinter as tk
from PIL import Image, ImageTk
import requests
from io import BytesIO
from enum import Enum
import typing_extensions as typing
import tkinter.ttk as ttk
import openai
from pypdf import PdfReader


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
    original_room_visit_order: List[str]

Event = typing.NamedTuple('Event', [('event', str), ('is_canon', bool)])


class Room:
    def __init__(self, name: str, description: str, image_prompt: str, canon_event: str):
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

        self.canon_event = canon_event

class GameWorld:
    def __init__(self, original_room_visit_order: List[str] = None):
        self.rooms: Dict[str, Room] = {}
        self.current_room: Optional[Room] = None
        self.original_room_visit_order = original_room_visit_order or []
        os.environ["OPENAI_API_KEY"] = "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"
        self.openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        
        self.current_event: Optional[Event] = None
        self.visited_rooms = []
        self.seen_events = []
    
    def is_canon_route(self) -> bool:
        # return True
        return self.visited_rooms == self.original_room_visit_order[:min(len(self.original_room_visit_order), len(self.visited_rooms))]

    def add_room(self, room: Room):
        self.rooms[room.name] = room
        if not self.current_room:
            self.visited_rooms.append(room.name)
            self.current_room = room
            self.current_event = Event(event=room.canon_event, is_canon=True)

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
    
    def get_event(self, room: Room) -> Tuple[str, bool]:
        if self.is_canon_route():
            return room.canon_event, True
        else:
            return generate_non_canon_event(room, self.seen_events), False

class GameUI:
    def __init__(self, game_world: GameWorld):
        self.game_world = game_world
        self.root = tk.Tk()
        self.root.title("Text Adventure")
        
        # Create main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Create map frame
        self.map_frame = tk.Frame(self.root)
        self.map_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Create canvas for map with larger initial size
        self.map_canvas = tk.Canvas(self.map_frame, width=500, height=500, bg='white')
        self.map_canvas.pack(padx=20, pady=20)  # Add padding around canvas
        
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
        
        # Store room positions for map
        self.room_positions: Dict[str, Tuple[int, int]] = {}
        self.calculate_room_positions()
        
        self.update_display()

    def calculate_room_positions(self):
        # Start with the first room at the center
        visited = set()
        queue = []
        
        # Track grid positions
        self.grid_positions = {}  # Store grid coordinates
        self.min_x = self.min_y = float('inf')
        self.max_x = self.max_y = float('-inf')
        
        # Start with current room at (0,0)
        start_room = self.game_world.current_room
        if not start_room:
            return
            
        # Start at grid center (0,0)
        self.grid_positions[start_room.name] = (0, 0)
        queue.append((start_room, 0, 0))
        visited.add(start_room.name)
        
        # Update min/max for first room
        self.min_x = min(self.min_x, 0)
        
        self.max_x = max(self.max_x, 0)
        self.min_y = min(self.min_y, 0)
        self.max_y = max(self.max_y, 0)
        
        # Direction offsets in grid coordinates
        offsets = {
            Direction.NORTH: (0, -1),
            Direction.SOUTH: (0, 1),
            Direction.EAST: (1, 0),
            Direction.WEST: (-1, 0)
        }
        
        # BFS to assign grid positions
        while queue:
            current_room, grid_x, grid_y = queue.pop(0)
            
            for direction, next_room in current_room.connections.items():
                if next_room and next_room.name not in visited:
                    dx, dy = offsets[direction]
                    new_grid_x, new_grid_y = grid_x + dx, grid_y + dy
                    self.grid_positions[next_room.name] = (new_grid_x, new_grid_y)
                    queue.append((next_room, new_grid_x, new_grid_y))
                    visited.add(next_room.name)
                    
                    # Update min/max coordinates
                    self.min_x = min(self.min_x, new_grid_x)
                    self.max_x = max(self.max_x, new_grid_x)
                    self.min_y = min(self.min_y, new_grid_y)
                    self.max_y = max(self.max_y, new_grid_y)

    def draw_map(self):
        self.map_canvas.delete("all")
        
        # Grid settings
        cell_size = 100
        margin = 20
        border_width = 2  # Account for border width
        
        # Calculate grid dimensions
        grid_cols = self.max_x - self.min_x + 1
        grid_rows = self.max_y - self.min_y + 1
        
        # Calculate exact canvas size needed, accounting for borders
        canvas_width = (grid_cols * cell_size) + (2 * margin) + border_width
        canvas_height = (grid_rows * cell_size) + (2 * margin) + border_width
        
        # Update canvas size to exactly fit the grid
        self.map_canvas.config(width=canvas_width, height=canvas_height)
        
        # Draw connections as doors between rooms
        for room_name, (grid_x, grid_y) in self.grid_positions.items():
            room = self.game_world.rooms[room_name]
            cell_x = (grid_x - self.min_x) * cell_size + margin
            cell_y = (grid_y - self.min_y) * cell_size + margin
            
            # Draw doors for each connection
            for direction, connected_room in room.connections.items():
                if connected_room and connected_room.name in self.grid_positions:
                    door_length = 20  # Length of the door line
                    
                    if direction == Direction.NORTH:
                        self.map_canvas.create_line(
                            cell_x + cell_size/2 - door_length/2, cell_y,
                            cell_x + cell_size/2 + door_length/2, cell_y,
                            fill='black', width=3
                        )
                    elif direction == Direction.SOUTH:
                        self.map_canvas.create_line(
                            cell_x + cell_size/2 - door_length/2, cell_y + cell_size,
                            cell_x + cell_size/2 + door_length/2, cell_y + cell_size,
                            fill='black', width=3
                        )
                    elif direction == Direction.EAST:
                        self.map_canvas.create_line(
                            cell_x + cell_size, cell_y + cell_size/2 - door_length/2,
                            cell_x + cell_size, cell_y + cell_size/2 + door_length/2,
                            fill='black', width=3
                        )
                    elif direction == Direction.WEST:
                        self.map_canvas.create_line(
                            cell_x, cell_y + cell_size/2 - door_length/2,
                            cell_x, cell_y + cell_size/2 + door_length/2,
                            fill='black', width=3
                        )
        
        # Draw only rooms that exist
        for room_name, (grid_x, grid_y) in self.grid_positions.items():
            # Calculate cell position
            cell_x = (grid_x - self.min_x) * cell_size + margin
            cell_y = (grid_y - self.min_y) * cell_size + margin
            
            # Draw room cell with different color if it's current room
            fill_color = 'lightblue' if room_name == self.game_world.current_room.name else 'white'
            
            # Draw the room rectangle
            self.map_canvas.create_rectangle(
                cell_x, cell_y, cell_x + cell_size, cell_y + cell_size,
                fill=fill_color, outline='black', width=border_width
            )
            
            # Create white background for text to ensure visibility
            center_x = cell_x + cell_size/2
            center_y = cell_y + cell_size/2
            
            # Add room name with background
            text_bg = self.map_canvas.create_rectangle(
                center_x - 45, center_y - 10,
                center_x + 45, center_y + 10,
                fill=fill_color, outline=fill_color
            )
            
            text = self.map_canvas.create_text(
                center_x, center_y,
                text=room_name,
                font=('Arial', 10, 'bold'),
                width=80,
                justify='center'
            )

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
            self.game_world.visited_rooms.append(self.game_world.current_room.name)
            # Generate and save new canon event for the room we just moved to
            event, is_canon = self.game_world.get_event(self.game_world.current_room)
            self.game_world.current_event = Event(event=event, is_canon=is_canon)
            self.game_world.seen_events.append(Event)
            
            
            self.update_display()
            

    def update_display(self):
        if not self.game_world.current_room:
            return
            
        # Update description text size based on whether there's an image
        if self.game_world.current_room.image_path:
            self.description_text.config(height=10, width=50)  # Original size
        else:
            self.description_text.config(height=20, width=80)  # Bigger when no image
        
        # Update description
        self.description_text.delete(1.0, tk.END)
        self.description_text.insert(tk.END, f"Current Room: {self.game_world.current_room.name}\n\n")
        self.description_text.insert(tk.END, f"{self.game_world.current_room.description}\n\n")
        print(self.game_world.current_event.is_canon)
        event_type = "Non-Canon" if not self.game_world.current_event.is_canon else "Canon"
        self.description_text.insert(tk.END, f"{event_type} Event: {self.game_world.current_event.event}\n")
        
        # Update image if it exists
        if self.game_world.current_room.image_path:
            image = Image.open(self.game_world.current_room.image_path)
            image = image.resize((512, 512))  # Resize for display
            photo = ImageTk.PhotoImage(image)
            self.image_label.configure(image=photo)
            self.image_label.image = photo
        else:
            self.image_label.configure(image='')
            self.image_label.image = None

        # Update button states
        self.north_button.config(state=tk.NORMAL if self.game_world.current_room.connections[Direction.NORTH] else tk.DISABLED)
        self.south_button.config(state=tk.NORMAL if self.game_world.current_room.connections[Direction.SOUTH] else tk.DISABLED)
        self.east_button.config(state=tk.NORMAL if self.game_world.current_room.connections[Direction.EAST] else tk.DISABLED)
        self.west_button.config(state=tk.NORMAL if self.game_world.current_room.connections[Direction.WEST] else tk.DISABLED)
        
        # Update map
        self.draw_map()

    def run(self):
        self.root.mainloop()


def process_book_with_openai(story: str) -> str:
    client = openai.OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )

    response = client.beta.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "system", 
            "content": f"""
            I'm creating a playable version of the story attached. Create a list of rooms and the connections between them.

            For each room include:
            - A name for the spaceship location (STRICTLY 100 characters max)
            - A description referencing details from the book and describing the spaceship setting (STRICTLY 50 words max) 
            - An image prompt for DALL-E to generate an illustration of the spaceship interior (STRICTLY 100 words max)
            
            For connections, specify:
            - Which two spaceship rooms are connected
            - The direction (north, south, east, or west) through the ship's corridors

            ##### STORY #####
            {story}
            """
        }],
        response_format={"type": "world_output"},
    )

    return response.choices[0].message.content

def process_book_with_gemini(story: str) -> str:
    os.environ["GOOGLE_API_KEY"] = "AIzaSyDD9YRzLbPU1o-XehqkvvQD9PLG0rokBws"
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    
    model = genai.GenerativeModel("gemini-1.5-flash") 

    prompt = f"""
    I'm creating a playable version of the story attached. Create a list of rooms and the connections between them.

    Create a world with rooms representing different areas of the spaceship. Provide:
    1. A list of rooms with descriptions and image prompts that reference the book and spaceship setting
    2. A list of connections between the rooms detailed above, specifying which rooms connect and in what direction. Make sure all rooms are reachable from every other room through some path and only use rooms that are in the list above.
    3. A list of room names in the order they were visited in the book.
    
    For each room include:
    - A name for the spaceship location (STRICTLY 100 characters max)
    - A description referencing details from the book and describing the spaceship setting (STRICTLY 50 words max) 
    - An image prompt for DALL-E to generate an illustration of the spaceship interior (STRICTLY 100 words max)
    
    For connections, specify:
    - Which two spaceship rooms are connected
    - The direction (north, south, east, or west) through the ship's corridors


    ##### STORY #####
    {story}
    """
    
    response = model.generate_content(
        [prompt], 
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json", 
            response_schema=WorldSetup
        )
    )
    return response.text


def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    story = ""
    for page in reader.pages:
        story += page.extract_text()
    return story


def process_book(pdf_path: str, use_gemini: bool = True) -> str:
    # Extract text content from PDF
    story = extract_text_from_pdf(pdf_path)

    # Process with selected AI model
    if use_gemini:
        return process_book_with_gemini(story)
    else:
        return process_book_with_openai(story)
    
def generate_game_data():
    # world_setup = process_book("Dark_Age_Red_Rising_Saga_5_-_Pierce_Brown-481-502.pdf", use_gemini=True)

    # with open('game_data.json', 'w') as f:
    #     json.dump({'world': world_setup}, f)
    
    # Load and print
    with open('game_data.json', 'r') as f:
        data = json.load(f)
        if isinstance(data['world'], str):
            world_data = json.loads(data['world'])
        else:
            world_data = data['world'] 
        print(world_data)
    
    # Generate canon events for each room
    for room in world_data['rooms']:
        # if True:
        if 'canon_event' not in room:
            print(f"Generating canon event for {room['name']}")
            room['canon_event'] = generate_canon_event(room)
    
    for room in world_data['rooms']:
        print(f"Room: {room['name']}")
        print(f"Canon Event: {room['canon_event']}")

    # Save updated data back to file
    with open('game_data.json', 'w') as f:
        json.dump({'world': world_data}, f, indent=4)


def generate_canon_event(room: dict) -> str:
    text = extract_text_from_pdf("Dark_Age_Red_Rising_Saga_5_-_Pierce_Brown-481-502.pdf")
    
    os.environ["GOOGLE_API_KEY"] = "AIzaSyDD9YRzLbPU1o-XehqkvvQD9PLG0rokBws"
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash") 

    prompt = f"""
    What event in the story occurs in this room? Keep the description to 100 words max.

    ##### STORY #####
    {text}
    
    ##### ROOM DESCRIPTION #####
    Room: {room['name']}
    Description: {room['description']}
    """
    
    response = model.generate_content(
        [prompt], 
        # generation_config=genai.GenerationConfig(
        #     response_mime_type="application/json", 

        # )
    )
    return response.text


def generate_non_canon_event(room: Room, seen_events: List[str]) -> str:
    text = extract_text_from_pdf("Dark_Age_Red_Rising_Saga_5_-_Pierce_Brown-481-502.pdf")

    os.environ["GOOGLE_API_KEY"] = "AIzaSyDD9YRzLbPU1o-XehqkvvQD9PLG0rokBws"
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel("gemini-1.5-flash") 

    prompt = f"""
    Using the attached story, provided room description with its original canon event, and a list of canon events seen so far, create a desscription of a plausible non-canon event that occurs in the story in the room.
    Keep the description to 100 words max.

    ##### STORY #####
    {text}
    
    ##### ROOM DESCRIPTION #####
    Room: {room.name}
    Description: {room.description}
    Canon Event: {room.canon_event}

    ##### EVENTS SEEN SO FAR #####
    {seen_events}
    """

    response = model.generate_content(
        [prompt], 
    )
    return response.text

def run_game():
    with open('game_data.json', 'r') as f:
        data = json.load(f)
        if isinstance(data['world'], str):
            world_data = json.loads(data['world'])  # Parse if it's a string
        else:
            world_data = data['world']  # Use as-is if it's already a dict
        # world_data = json.loads(data['world'])  # Parse the string into JSON
        rooms = world_data['rooms']
        connections = world_data['connections']
        original_room_visit_order = world_data.get('original_room_visit_order', [])  # Get visit order
    
    # Initialize game world with visit order
    game_world = GameWorld(original_room_visit_order=original_room_visit_order)
    
    # Create rooms first
    for room_data in rooms:
        room = Room(room_data["name"], room_data["description"], room_data["image_prompt"], room_data["canon_event"])
        game_world.add_room(room)
        # game_world.generate_room_image(room)
    
    # Then set up connections
    for conn in connections:
        game_world.connect_rooms(conn["room1"], conn["room2"], Direction(conn["direction"]))
    
    # Start the game UI
    game_ui = GameUI(game_world)
    game_ui.run()


if __name__ == "__main__":
    # generate_game_data()
    run_game()


