"""Module for fetching Pokémon data from the PokéAPI."""
from typing import Any, Dict, Optional
from src.constants import POKEAPI_BASE_URL


async def fetch_pokemon_full_data(
    client, pokemon_name: str
) -> Optional[Dict[str, Any]]:
    """Fetch Pokémon data including stats, types, and first move (with power/type).

    Args:
        client (httpx.AsyncClient): The client to use to fetch the data.
        pokemon_name (str): The name of the Pokémon to fetch data for.

    Returns:
        Optional[Dict[str, Any]]: The Pokémon data, or None if the Pokémon was not found.
    """
    pokemon_url = f"{POKEAPI_BASE_URL}/pokemon/{pokemon_name.lower()}"
    resp = await client.get(pokemon_url)
    if resp.status_code != 200:
        return None
    data = resp.json()
    base_stats = {stat["stat"]["name"]: stat["base_stat"] for stat in data["stats"]}
    types = [t["type"]["name"] for t in data["types"]]
    moves = data["moves"]
    if not moves:
        return None
    # Use the first move for simplicity
    move_url = moves[0]["move"]["url"]
    move_resp = await client.get(move_url)
    if move_resp.status_code != 200:
        return None
    move_data = move_resp.json()
    move_power = move_data.get("power", 50)  # Default to 50 if missing
    move_type = move_data.get("type", {}).get("name", "normal")
    move_name = move_data.get("name", "tackle")
    move_effect = next(
        (
            e["effect"]
            for e in move_data.get("effect_entries", [])
            if e["language"]["name"] == "en"
        ),
        None,
    )
    return {
        "name": data["name"],
        "base_stats": base_stats,
        "types": types,
        "move": {
            "name": move_name,
            "power": move_power,
            "type": move_type,
            "effect": move_effect,
        },
    }
