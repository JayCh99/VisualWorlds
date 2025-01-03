import os
import shutil
import json
import hashlib

def check_room_images():
    # Load room data
    with open('game_data.json', 'r') as f:
        data = json.load(f)
        world_data = json.loads(data['world'])
        rooms = world_data['rooms']

    # Calculate hashes for current rooms
    valid_hashes = set()
    for room in rooms:
        room_hash = hashlib.sha256(
            f"{room['name']}{room['description']}{room['image_prompt']}".encode()
        ).hexdigest()
        valid_hashes.add(room_hash)

    # Create old directory if it doesn't exist
    os.makedirs("room_images/old", exist_ok=True)

    # Check all files in room_images
    for filename in os.listdir("room_images"):
        if filename.endswith(".png"):
            file_hash = filename.replace(".png", "")
            if file_hash not in valid_hashes:
                # Move file to old directory
                old_path = os.path.join("room_images", filename)
                new_path = os.path.join("room_images", "old", filename)
                shutil.move(old_path, new_path)
                print(f"Moved {filename} to room_images/old/")

check_room_images()