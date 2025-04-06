from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Literal
import httpx
from pydantic import BaseModel
from typing import List, Optional, Dict, Union

app = FastAPI(title="WoW Mythic+ Character Lookup")

# Set up templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Raider.IO API base URL
RAIDER_IO_API_URL = "https://raider.io/api/v1"

# Models for API responses
class Affix(BaseModel):
    id: int
    name: str
    description: str
    icon: str
    icon_url: str
    wowhead_url: str

class MythicPlusRun(BaseModel):
    dungeon: str
    short_name: str
    mythic_level: int
    completed_at: str
    clear_time_ms: int
    par_time_ms: int
    num_keystone_upgrades: int
    score: float
    url: str
    affixes: List[Affix]


class RunDetailPlayer(BaseModel):
    character_name: str
    character_class: str
    character_role: Literal["tank", "dps", "healer" ]
    profile_url: str
    item_level: Optional[float] = None

class RunDetail(BaseModel):
    run_id: int
    keystone_run_id: int
    players: List[RunDetailPlayer]
    average_item_level: Optional[float] = None

class CharacterMythicPlusData(BaseModel):
    mythic_plus_recent_runs: Optional[List[MythicPlusRun]] = None
    mythic_plus_best_runs: Optional[List[MythicPlusRun]] = None
    name: str
    race: str
    class_name: str
    active_spec_name: str
    profile_url: str
    thumbnail_url: str
    run_details: Optional[Dict[int, RunDetail]] = None

async def fetch_run_details(run_id: int, season: str = "season-tww-2"):
    """Fetch detailed information about a specific Mythic+ run."""
    url = f"{RAIDER_IO_API_URL}/mythic-plus/run-details"
    params = {
        "season": season,
        "id": run_id
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            
            if response.status_code != 200:
                print(f"API error for run {run_id}: Status {response.status_code}")
                print(f"Response: {response.text}")
                return None
            
            data = response.json()
            
            players = []
            item_levels = []
            
            # Extract players info and item levels
            for roster_slot in data.get("roster", []):
                player = roster_slot.get("character", {})
                
                try:
                    # Debug logging

                    player_name = player.get('name')
                    player_class = (player.get('class').get('slug'))
                    player_role = (player.get('spec').get('role'))
                    item_level = round(roster_slot.get("items", {}).get("item_level_equipped"), 1)

                    print(f"Player name: {player_name}")
                    print(f"Class: {player_class}")
                    print(f"Item level: {item_level}")
                    
                    player_data = RunDetailPlayer(
                        character_name=player_name,
                        character_class=player_class,
                        character_role=player_role,
                        profile_url=player.get("profile_url", ""),
                        item_level=item_level
                    )
                    players.append(player_data)
                    
                    # Add item level to the list if available
                    if player_data.item_level is not None:
                        item_levels.append(player_data.item_level)
                except Exception as e:
                    print(f"Error parsing player data: {str(e)}")
            
            # Calculate average item level if we have data
            average_item_level = None
            print(f"Item levels:{item_levels}")
            if item_levels:
                average_item_level = sum(item_levels) / len(item_levels)
            print(f"Average item levels:{average_item_level}")
            run_detail = RunDetail(
                run_id=run_id,
                keystone_run_id=data.get("keystone_run_id", 0),
                players=players,
                average_item_level=average_item_level
            )
            print(run_detail)
            
            return run_detail
    except Exception as e:
        print(f"Exception fetching run {run_id} with season {season}: {str(e)}")
        return None

async def fetch_character_data(region: str, realm: str, character_name: str):
    """Fetch character Mythic+ data from Raider.IO API."""
    url = f"{RAIDER_IO_API_URL}/characters/profile"
    params = {
        "region": region,
        "realm": realm,
        "name": character_name,
        "fields": "mythic_plus_recent_runs,mythic_plus_best_runs"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, 
                               detail=f"Error fetching data from Raider.IO: {response.text}")
        
        data = response.json()
        
        # Transform the data to match our model
        character_data = {
            "name": data.get("name", ""),
            "race": data.get("race", ""),
            "class_name": data.get("class", ""),
            "active_spec_name": data.get("active_spec_name", ""),
            "profile_url": data.get("profile_url", ""),
            "thumbnail_url": data.get("thumbnail_url", ""),
            "mythic_plus_recent_runs": data.get("mythic_plus_recent_runs", []),
            "mythic_plus_best_runs": data.get("mythic_plus_best_runs", []),
            "run_details": {}
        }
        
        # Fetch detailed information for each best run
        if character_data["mythic_plus_best_runs"]:
            run_details = {}
            for run in character_data["mythic_plus_best_runs"]:
                try:
                    run_id = run.get("keystone_run_id")
                    if run_id:
                        # Use the current TWW season
                        season = "season-tww-2"
                        
                        # Try to extract season from URL, but default to season-tww-2 if not found
                        url_parts = run.get("url", "").split("/")
                        if len(url_parts) > 3 and url_parts[3].startswith("season-"):
                            extracted_season = url_parts[3]
                            print(f"Found season in URL: {extracted_season}")
                            # Only use extracted season if it looks valid
                            if extracted_season.startswith("season-"):
                                season = extracted_season
                        
                        print(f"Fetching details for run {run_id} using season: {season}")
                        run_detail = await fetch_run_details(run_id, season)
                        if run_detail:
                            run_details[run_id] = run_detail
                except Exception as e:
                    # Log the error but continue with other runs
                    print(f"Error processing run {run_id}: {str(e)}")
                    print(f"Season used: {season}")
            
            character_data["run_details"] = run_details
        
        return character_data

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/character-lookup")
async def character_lookup(request: Request, region: str, realm: str, character: str):
    """Handle form submission and redirect to character page."""
    # Clean up the inputs
    clean_realm = realm.strip().lower().replace(" ", "-")
    clean_character = character.strip()
    
    # Redirect to the character page
    return RedirectResponse(url=f"/character/{region}/{clean_realm}/{clean_character}")

@app.get("/api/character/{region}/{realm}/{name}")
async def get_character(region: str, realm: str, name: str):
    """API endpoint to fetch character Mythic+ data."""
    try:
        character_data = await fetch_character_data(region, realm, name)
        return character_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/character/{region}/{realm}/{name}", response_class=HTMLResponse)
async def character_page(request: Request, region: str, realm: str, name: str):
    """Render the character details page."""
    try:
        character_data = await fetch_character_data(region, realm, name)
        return templates.TemplateResponse(
            "character.html", 
            {"request": request, "character": character_data}
        )
    except HTTPException as e:
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "status_code": e.status_code, "detail": e.detail}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "error.html", 
            {"request": request, "status_code": 500, "detail": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)