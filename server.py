"""Module for fetching and returning Pokémon information using the PokeAPI."""
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
import httpx

POKEAPI_BASE_URL = "https://pokeapi.co/api/v2"

mcp = FastMCP("poke-mcp")


@mcp.tool()
async def get_pokemon_info(pokemon_name: str) -> Dict[str, Any]:
    """
    Get comprehensive information about a Pokémon, including base stats, types, abilities, moves (with effects), and evolution information.

    Args:
        pokemon_name: The name of the Pokémon to get information about

    Returns:
        A dictionary containing the Pokémon's information
    """
    try:
        async with httpx.AsyncClient() as client:
            # Fetch main Pokémon data
            pokemon_url = f"{POKEAPI_BASE_URL}/pokemon/{pokemon_name.lower()}"
            pokemon_response = await client.get(pokemon_url)
            pokemon_response.raise_for_status()
            pokemon_data = pokemon_response.json()

            # Base stats
            base_stats = {
                stat["stat"]["name"]: stat["base_stat"]
                for stat in pokemon_data["stats"]
            }

            # Types
            types = [t["type"]["name"] for t in pokemon_data["types"]]

            # Abilities (with effect text)
            abilities = []
            for ability_entry in pokemon_data["abilities"]:
                ability_name = ability_entry["ability"]["name"]
                ability_url = ability_entry["ability"]["url"]
                ability_resp = await client.get(ability_url)
                ability_resp.raise_for_status()
                ability_data = ability_resp.json()
                effect_entries = ability_data.get("effect_entries", [])
                effect = next(
                    (
                        e["effect"]
                        for e in effect_entries
                        if e["language"]["name"] == "en"
                    ),
                    None,
                )
                abilities.append({"name": ability_name, "effect": effect})

            # Moves (with effect text, only first 10 for brevity)
            moves = []
            for move_entry in pokemon_data["moves"][:10]:
                move_name = move_entry["move"]["name"]
                move_url = move_entry["move"]["url"]
                move_resp = await client.get(move_url)
                move_resp.raise_for_status()
                move_data = move_resp.json()
                effect_entries = move_data.get("effect_entries", [])
                effect = next(
                    (
                        e["effect"]
                        for e in effect_entries
                        if e["language"]["name"] == "en"
                    ),
                    None,
                )
                moves.append({"name": move_name, "effect": effect})

            # Evolution information
            species_url = pokemon_data["species"]["url"]
            species_resp = await client.get(species_url)
            species_resp.raise_for_status()
            species_data = species_resp.json()
            evolution_chain_url = species_data["evolution_chain"]["url"]
            evolution_resp = await client.get(evolution_chain_url)
            evolution_resp.raise_for_status()
            evolution_data = evolution_resp.json()

            def parse_evolution_chain(chain):
                evo_chain = []
                current = chain
                while current:
                    evo_chain.append(current["species"]["name"])
                    if current["evolves_to"]:
                        current = current["evolves_to"][0]
                    else:
                        current = None
                return evo_chain

            evolution_chain = parse_evolution_chain(evolution_data["chain"])

            return {
                "name": pokemon_data["name"],
                "id": pokemon_data["id"],
                "base_stats": base_stats,
                "types": types,
                "abilities": abilities,
                "moves": moves,
                "evolution_chain": evolution_chain,
            }
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP error: {e}"}
    except httpx.RequestError as e:
        return {"error": f"Request error: {e}"}
