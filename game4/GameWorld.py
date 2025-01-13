
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
