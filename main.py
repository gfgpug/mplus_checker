from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import httpx
import os
from pydantic import BaseModel
from typing import List, Optional

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

class CharacterMythicPlusData(BaseModel):
    mythic_plus_recent_runs: Optional[List[MythicPlusRun]] = None
    mythic_plus_best_runs: Optional[List[MythicPlusRun]] = None
    name: str
    race: str
    class_name: str
    active_spec_name: str
    profile_url: str
    thumbnail_url: str

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
            "mythic_plus_best_runs": data.get("mythic_plus_best_runs", [])
        }
        
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