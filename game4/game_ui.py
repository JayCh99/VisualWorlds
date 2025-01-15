import tkinter as tk
from PIL import Image, ImageTk
from typing import Dict, Tuple
from .models import Direction, Event
from .game_world import GameWorld


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
            
            actions = self.game_world.get_actions()
            print("actions", actions)
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