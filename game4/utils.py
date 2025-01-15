import os
import json
import openai
import google.generativeai as genai
from pypdf import PdfReader
from typing import Dict, List
import game4.models as models

# Constants
BOOK_PATH = os.path.join(os.path.dirname(__file__), "Dark_Age_Red_Rising_Saga_5_-_Pierce_Brown-481-502.pdf")
os.environ["GOOGLE_API_KEY"] = "AIzaSyDD9YRzLbPU1o-XehqkvvQD9PLG0rokBws"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

model = genai.GenerativeModel("gemini-1.5-flash") 

def process_book_with_gemini(story: str) -> str:
    os.environ["GOOGLE_API_KEY"] = "AIzaSyDD9YRzLbPU1o-XehqkvvQD9PLG0rokBws"
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    
    model = genai.GenerativeModel("gemini-1.5-flash") 

    prompt = f"""
    I'm creating a playable version of the story attached. Create a list of rooms and the connections between them.

    Create a world with rooms representing different areas of the spaceship. Provide:
    1. A list of rooms with descriptions and image prompts that reference the book and spaceship setting
    2. A list of connections between the rooms detailed above, specifying which rooms connect and in what direction.
    3. A list of room names in the order they were visited in the book.
    
    For each room include:
    - A name for the spaceship location (STRICTLY 100 characters max)
    - A description referencing details from the book and describing the spaceship setting (STRICTLY 50 words max) 
    - An image prompt for DALL-E to generate an illustration of the spaceship interior (STRICTLY 100 words max)
    
    For connections, specify:
    - Which two spaceship rooms are connected
    - The direction (north, south, east, or west) through the ship's corridors
    - Make sure all rooms are reachable from every other room through some path and only use rooms that are in the list above.


    ##### STORY #####
    {story}
    """
    
    response = model.generate_content(
        [prompt], 
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json", 
            response_schema=models.WorldSetup
        )
    )
    return response.text


def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    story = ""
    for page in reader.pages:
        story += page.extract_text()
    return story


def process_book(pdf_path: str = BOOK_PATH, use_gemini: bool = True) -> str:
    story = extract_text_from_pdf(pdf_path)

    # Process with selected AI model
    if use_gemini:
        return process_book_with_gemini(story)
    # else:
    #     return process_book_with_openai(story)
    
def generate_game_data():
    # world_setup = process_book(BOOK_PATH, use_gemini=True)

    # with open('game_data.json', 'w') as f:
    #     json.dump({'world': world_setup}, f)
    
    # Load and print
    with open('game_data.json', 'r') as f:
        data = json.load(f)
        if isinstance(data['world'], str):
            world_data = json.loads(data['world'])
        else:
            world_data = data['world'] 
        # print(world_data)
    

    variables = generate_variables(world_data)
    print("variables:", variables)
    models.Variables.model_validate(json.loads(variables))
    world_data['variables'] = json.loads(variables)['variables']

    # Generate canon events for each room
    for room in world_data['rooms']:
        # if True:
        if 'canon_event' not in room:
            # print(f"Generating canon event for {room['name']}")
            room['canon_event'] = generate_canon_event(room)
    
    # for room in world_data['rooms']:
        # print(f"Room: {room['name']}")
        # print(f"Canon Event: {room['canon_event']}")

    # Save updated data back to file
    with open('game_data.json', 'w') as f:
        json.dump({'world': world_data}, f, indent=4)


def generate_canon_event(room: dict) -> str:
    text = extract_text_from_pdf(BOOK_PATH)
    
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


def generate_non_canon_event(room: models.Room, seen_events: List[str]) -> str:
    text = extract_text_from_pdf(BOOK_PATH)

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

def generate_variables(world_data: dict) -> str:
    text = extract_text_from_pdf(BOOK_PATH)
    os.environ["GOOGLE_API_KEY"] = "AIzaSyDD9YRzLbPU1o-XehqkvvQD9PLG0rokBws"
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    
    model = genai.GenerativeModel("gemini-1.5-flash") 

    prompt = f"""
    What factors influence the story? Create a few variables tracking important story values. Do not track the current location or locations visited.

    For each variable, follow the format variable_name: initial value
    ##### STORY #####
    {text}
    """
    
    response = model.generate_content(
        [prompt], 
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json", 
            response_schema=models.Variables
        )
    )
    return response.text

def generate_actions(room: models.Room, current_event: str, variables: str) -> str:
    text = extract_text_from_pdf(BOOK_PATH)
    prompt = f"""
    What actions can the player take in this room based on the story, current event, and the variables?

    Provide a list of 3 actions in the format:
    Action 1: changed variables
    Action 2: changed variables
    Action 3: changed variables

    ##### STORY #####
    {text}
    
    ##### ROOM DESCRIPTION #####
    Room: {room.name}
    Description: {room.description}
    Current Event: {current_event}

    ##### VARIABLES #####
    {variables}
    """

    response = model.generate_content(
        [prompt], 
    )
    return response.text
    
# def generate_non_canon_event(room: Room, seen_events: List[str]) -> str:
#     text = extract_text_from_pdf(BOOK_PATH)

#     os.environ["GOOGLE_API_KEY"] = "AIzaSyDD9YRzLbPU1o-XehqkvvQD9PLG0rokBws"
#     genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
#     model = genai.GenerativeModel("gemini-1.5-flash") 

#     prompt = f"""







