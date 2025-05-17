"""Module for fetching and returning Pokémon information using the PokeAPI."""
import random
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
import httpx
from src.constants import STATUS_PARALYSIS, POKEAPI_BASE_URL
from src.battle_utils import (
    calculate_damage,
    apply_status_effects,
    try_inflict_status,
    parse_evolution_chain,
)
from src.pokeapi_client import fetch_pokemon_full_data

mcp = FastMCP("poke-mcp")


@mcp.tool()
async def get_pokemon_info(pokemon_name: str) -> Dict[str, Any]:
    """
    Get comprehensive information about a Pokémon.

    Includes base stats, types, abilities, moves (with effects), and evolution information.

    Args:
        pokemon_name: The name of the Pokémon to get information about.

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


@mcp.tool()
async def simulate_battle(pokemon1: str, pokemon2: str) -> Dict[str, Any]:
    """
    Simulate a Pokémon battle between two Pokémon using core mechanics.
    Args:
        pokemon1: Name of the first Pokémon
        pokemon2: Name of the second Pokémon
    Returns:
        Battle log and winner
    """
    async with httpx.AsyncClient() as client:
        poke1 = await fetch_pokemon_full_data(client, pokemon1)

        if not poke1:
            return {"error": f"Could not fetch data for {pokemon1}."}
        poke2 = await fetch_pokemon_full_data(client, pokemon2)
        if not poke2:
            return {"error": f"Could not fetch data for {pokemon2}."}

        hp1 = poke1["base_stats"].get("hp", 100)
        hp2 = poke2["base_stats"].get("hp", 100)
        status1 = None
        status2 = None
        log = []
        turn = 1

        # Determine turn order by speed
        speed1 = poke1["base_stats"].get("speed", 50)
        speed2 = poke2["base_stats"].get("speed", 50)
        first, second = (poke1, poke2) if speed1 >= speed2 else (poke2, poke1)
        first_hp, second_hp = (hp1, hp2) if speed1 >= speed2 else (hp2, hp1)
        first_status, second_status = (
            (status1, status2) if speed1 >= speed2 else (status2, status1)
        )
        first_name, second_name = first["name"], second["name"]
        while first_hp > 0 and second_hp > 0:
            log.append(f"Turn {turn}:")

            # First attacks
            if first_status == STATUS_PARALYSIS and random.random() < 0.25:
                log.append(f"{first_name} is paralyzed and can't move!")
            else:
                damage = calculate_damage(first, second, first_status)
                second_hp -= damage
                log.append(
                    f"{first_name} uses {first['move']['name']} and deals {damage} damage! ({second_name} HP: {max(0, second_hp)})"
                )
                # Try to inflict status
                new_status = try_inflict_status(first["move"])
                if not second_status and new_status:
                    second_status = new_status
                    log.append(f"{second_name} is now {new_status}!")

            # Apply status effects to second
            second_hp, status_log = apply_status_effects(second_status, second_hp)
            if status_log:
                log.append(f"{second_name}: {status_log} (HP: {max(0, second_hp)})")
            if second_hp <= 0:
                log.append(f"{second_name} fainted!")
                break

            # Second attacks
            if second_status == STATUS_PARALYSIS and random.random() < 0.25:
                log.append(f"{second_name} is paralyzed and can't move!")
            else:
                damage = calculate_damage(second, first, second_status)
                first_hp -= damage
                log.append(
                    f"{second_name} uses {second['move']['name']} and deals {damage} damage! ({first_name} HP: {max(0, first_hp)})"
                )
                new_status = try_inflict_status(second["move"])
                if not first_status and new_status:
                    first_status = new_status
                    log.append(f"{first_name} is now {new_status}!")

            # Apply status effects to first
            first_hp, status_log = apply_status_effects(first_status, first_hp)
            if status_log:
                log.append(f"{first_name}: {status_log} (HP: {max(0, first_hp)})")
            if first_hp <= 0:
                log.append(f"{first_name} fainted!")
                break
            turn += 1

        winner = first_name if first_hp > 0 else second_name
        log.append(f"Winner: {winner}!")
        return {
            "pokemon1": poke1["name"],
            "pokemon2": poke2["name"],
            "initial_hp": {poke1["name"]: hp1, poke2["name"]: hp2},
            "battle_log": log,
            "winner": winner,
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")
