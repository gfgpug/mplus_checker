import asyncio
import os
from typing import Any, Dict, List, Literal, Optional, Tuple

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

app = FastAPI(title="WoW Mythic+ Character Lookup")

# Set up templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")
load_dotenv()

# Raider.IO API base URL
RAIDER_IO_API_URL = "https://raider.io/api/v1"
RIO_API_KEY = os.getenv("RIO_API_KEY")

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
    character_role: Literal["tank", "dps", "healer"]
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

def extract_season_from_url(url: str) -> str:
    """Extract the season identifier from a Raider.IO URL."""
    default_season = "season-tww-2"
    
    url_parts = url.split("/")
    if len(url_parts) > 3 and url_parts[3].startswith("season-"):
        extracted_season = url_parts[3]
        # Only use extracted season if it looks valid
        if extracted_season.startswith("season-"):
            return extracted_season
    
    return default_season

def calculate_run_metrics(run: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate common metrics for a run."""
    time_diff_percent = round(((run["clear_time_ms"] - run["par_time_ms"]) / run["par_time_ms"] * 100), 1)
    clear_time_minutes = round(run["clear_time_ms"] / 1000 / 60, 1)
    par_time_minutes = round(run["par_time_ms"] / 1000 / 60, 1)
    
    return {
        "time_diff_percent": time_diff_percent,
        "clear_time_minutes": clear_time_minutes,
        "par_time_minutes": par_time_minutes
    }

async def fetch_run_details(run_id: int, season: str = "season-tww-2") -> Optional[RunDetail]:
    """Fetch detailed information about a specific Mythic+ run."""
    url = f"{RAIDER_IO_API_URL}/mythic-plus/run-details"
    params = {
        "access_key": RIO_API_KEY,
        "season": season,
        "id": run_id
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            
            if response.status_code != 200:
                print(f"API error for run {run_id}: Status {response.status_code}")
                return None
            
            data = response.json()
            
            players = []
            item_levels = []
            
            # Extract players info and item levels
            for roster_slot in data.get("roster", []):
                player = roster_slot.get("character", {})
                
                try:
                    player_name = player.get('name')
                    player_class = player.get('class', {}).get('slug')
                    player_role = player.get('spec', {}).get('role')
                    item_level = roster_slot.get("items", {}).get("item_level_equipped")
                    
                    # Make sure we have a valid item level (convert to float and round)
                    if item_level is not None:
                        item_level = round(float(item_level), 1)
                    
                    player_data = RunDetailPlayer(
                        character_name=player_name,
                        character_class=player_class,
                        character_role=player_role,
                        profile_url=player.get("profile_url", ""),
                        item_level=item_level
                    )
                    players.append(player_data)
                    
                    # Add item level to the list if available
                    if item_level is not None:
                        item_levels.append(item_level)
                except Exception as e:
                    print(f"Error parsing player data: {str(e)}")
            
            # Calculate average item level if we have data
            average_item_level = round(sum(item_levels) / len(item_levels), 1) if item_levels else None
            
            run_detail = RunDetail(
                run_id=run_id,
                keystone_run_id=data.get("keystone_run_id", 0),
                players=players,
                average_item_level=average_item_level
            )
            
            return run_detail
    except Exception as e:
        print(f"Exception fetching run {run_id} with season {season}: {str(e)}")
        return None

async def fetch_run_details_concurrently(run_ids: List[Tuple[int, str]]) -> Dict[int, RunDetail]:
    """Fetch details for multiple runs concurrently."""
    # Create a mapping of tasks to run IDs
    run_id_to_season = {
        run_id: extract_season_from_url(url) for run_id, url in run_ids
    }
    
    # Create all tasks
    tasks = [fetch_run_details(run_id, season) for run_id, season in run_id_to_season.items()]
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    run_details_dict = {}
    for i, (run_id, _) in enumerate(run_id_to_season.items()):
        result = results[i]
        if isinstance(result, Exception):
            print(f"Error fetching run {run_id}: {str(result)}")
        elif result:
            run_details_dict[run_id] = result
    
    return run_details_dict

def enhance_run(run: Dict[str, Any], run_details_dict: Dict[int, RunDetail], character_name: str) -> Dict[str, Any]:
    """Enhance a run with additional calculated metrics."""
    enhanced_run = run.copy()
    run_id = run.get("keystone_run_id")
    enhanced_run["run_id"] = run_id
    
    # Add time metrics
    metrics = calculate_run_metrics(run)
    enhanced_run.update(metrics)
    
    # Add player item level and group metrics if run details are available
    if run_id in run_details_dict:
        run_detail = run_details_dict[run_id]
        player_ilvl = None
        other_players_ilvls = []
        
        # Collect player's item level and all other valid player item levels
        for player in run_detail.players:
            # Check if the item level is valid (not None, not 0)
            if player.item_level is not None and player.item_level > 0:
                if player.character_name.lower() == character_name.lower():
                    player_ilvl = player.item_level
                else:
                    other_players_ilvls.append(player.item_level)
        
        # Calculate average of other players' item levels
        other_avg_ilvl = None
        if other_players_ilvls:  # Make sure there's at least one valid item level
            other_avg_ilvl = round(sum(other_players_ilvls) / len(other_players_ilvls), 1)
        
        # Calculate delta comparing player to the average of others
        ilvl_delta = None
        if player_ilvl is not None and other_avg_ilvl is not None:
            ilvl_delta = round(player_ilvl - other_avg_ilvl, 1)
        
        enhanced_run["player_ilvl"] = player_ilvl
        enhanced_run["other_avg_ilvl"] = other_avg_ilvl
        enhanced_run["ilvl_delta"] = ilvl_delta
    else:
        # Default values if run details not available
        enhanced_run["player_ilvl"] = None
        enhanced_run["other_avg_ilvl"] = None
        enhanced_run["ilvl_delta"] = None
    
    return enhanced_run

async def fetch_character_data(region: str, realm: str, character_name: str):
    """Fetch character Mythic+ data from Raider.IO API and enrich with additional details."""
    url = f"{RAIDER_IO_API_URL}/characters/profile"
    params = {
        "access_key": RIO_API_KEY,
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
            "mythic_plus_recent_runs": [],
            "mythic_plus_best_runs": [],
            "run_details": {}
        }
        
        # Process runs (both recent and best)
        recent_runs = data.get("mythic_plus_recent_runs", [])
        best_runs = data.get("mythic_plus_best_runs", [])
        
        # Collect run IDs and URLs for all runs
        run_ids = set()
        for run in recent_runs + best_runs:
            run_id = run.get("keystone_run_id")
            if run_id:
                run_ids.add((run_id, run.get("url", "")))
        
        # Fetch details for all unique run IDs concurrently
        run_details_dict = await fetch_run_details_concurrently(list(run_ids))
        
        # Process recent and best runs
        character_data["mythic_plus_recent_runs"] = [
            enhance_run(run, run_details_dict, character_data["name"]) 
            for run in recent_runs
        ]
        
        character_data["mythic_plus_best_runs"] = [
            enhance_run(run, run_details_dict, character_data["name"]) 
            for run in best_runs
        ]
        
        # Store the run details for reference
        character_data["run_details"] = run_details_dict
        
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