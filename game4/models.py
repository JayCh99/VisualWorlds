from enum import Enum
import typing_extensions as typing
from typing import List, Dict, Optional
from pydantic import BaseModel

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
    # variables: List[str]

class Variables(BaseModel):
    variables: List[str]

class Actions(BaseModel):
    actions: List[str]

Event = typing.NamedTuple('Event', [('event', str), ('is_canon', bool)])

class Room:
    def __init__(self, name: str, description: str, image_prompt: str, canon_event: str):
        self.name = name
        self.description = description
        self.image_prompt = image_prompt
        self.image_path = None
        self.connections: Dict[Direction, Optional[str]] = {
            Direction.NORTH: None,
            Direction.SOUTH: None,
            Direction.EAST: None,
            Direction.WEST: None
        }
        self.canon_event = canon_event 