"""Module for fetching and returning Pokémon information using the PokeAPI."""
from typing import Dict, Any, List, Tuple, Optional
from mcp.server.fastmcp import FastMCP
import httpx
import random

POKEAPI_BASE_URL = "https://pokeapi.co/api/v2"

mcp = FastMCP("poke-mcp")

# Type effectiveness chart (simplified for main types)
TYPE_EFFECTIVENESS = {
    "normal": {"rock": 0.5, "ghost": 0.0, "steel": 0.5},
    "fire": {
        "fire": 0.5,
        "water": 0.5,
        "grass": 2.0,
        "ice": 2.0,
        "bug": 2.0,
        "rock": 0.5,
        "dragon": 0.5,
        "steel": 2.0,
    },
    "water": {
        "fire": 2.0,
        "water": 0.5,
        "grass": 0.5,
        "ground": 2.0,
        "rock": 2.0,
        "dragon": 0.5,
    },
    "electric": {
        "water": 2.0,
        "electric": 0.5,
        "grass": 0.5,
        "ground": 0.0,
        "flying": 2.0,
        "dragon": 0.5,
    },
    "grass": {
        "fire": 0.5,
        "water": 2.0,
        "grass": 0.5,
        "poison": 0.5,
        "ground": 2.0,
        "flying": 0.5,
        "bug": 0.5,
        "rock": 2.0,
        "dragon": 0.5,
        "steel": 0.5,
    },
    "ice": {
        "fire": 0.5,
        "water": 0.5,
        "grass": 2.0,
        "ice": 0.5,
        "ground": 2.0,
        "flying": 2.0,
        "dragon": 2.0,
        "steel": 0.5,
    },
    "fighting": {
        "normal": 2.0,
        "ice": 2.0,
        "rock": 2.0,
        "dark": 2.0,
        "steel": 2.0,
        "poison": 0.5,
        "flying": 0.5,
        "psychic": 0.5,
        "bug": 0.5,
        "ghost": 0.0,
        "fairy": 0.5,
    },
    "poison": {
        "grass": 2.0,
        "poison": 0.5,
        "ground": 0.5,
        "rock": 0.5,
        "ghost": 0.5,
        "steel": 0.0,
        "fairy": 2.0,
    },
    "ground": {
        "fire": 2.0,
        "electric": 2.0,
        "grass": 0.5,
        "poison": 2.0,
        "flying": 0.0,
        "bug": 0.5,
        "rock": 2.0,
        "steel": 2.0,
    },
    "flying": {
        "electric": 0.5,
        "grass": 2.0,
        "fighting": 2.0,
        "bug": 2.0,
        "rock": 0.5,
        "steel": 0.5,
    },
    "psychic": {
        "fighting": 2.0,
        "poison": 2.0,
        "psychic": 0.5,
        "dark": 0.0,
        "steel": 0.5,
    },
    "bug": {
        "fire": 0.5,
        "grass": 2.0,
        "fighting": 0.5,
        "poison": 0.5,
        "flying": 0.5,
        "psychic": 2.0,
        "ghost": 0.5,
        "dark": 2.0,
        "steel": 0.5,
        "fairy": 0.5,
    },
    "rock": {
        "fire": 2.0,
        "ice": 2.0,
        "fighting": 0.5,
        "ground": 0.5,
        "flying": 2.0,
        "bug": 2.0,
        "steel": 0.5,
    },
    "ghost": {"normal": 0.0, "psychic": 2.0, "ghost": 2.0, "dark": 0.5},
    "dragon": {"dragon": 2.0, "steel": 0.5, "fairy": 0.0},
    "dark": {"fighting": 0.5, "psychic": 2.0, "ghost": 2.0, "dark": 0.5, "fairy": 0.5},
    "steel": {
        "fire": 0.5,
        "water": 0.5,
        "electric": 0.5,
        "ice": 2.0,
        "rock": 2.0,
        "fairy": 2.0,
        "steel": 0.5,
    },
    "fairy": {
        "fire": 0.5,
        "fighting": 2.0,
        "poison": 0.5,
        "dragon": 2.0,
        "dark": 2.0,
        "steel": 0.5,
    },
}

STATUS_PARALYSIS = "paralysis"
STATUS_BURN = "burn"
STATUS_POISON = "poison"

STATUS_EFFECTS = [STATUS_PARALYSIS, STATUS_BURN, STATUS_POISON]


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


async def fetch_pokemon_full_data(
    client, pokemon_name: str
) -> Optional[Dict[str, Any]]:
    """Fetch Pokémon data including stats, types, and first move (with power/type)."""
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


def get_type_multiplier(attack_type: str, defender_types: List[str]) -> float:
    multiplier = 1.0
    for d_type in defender_types:
        multiplier *= TYPE_EFFECTIVENESS.get(attack_type, {}).get(d_type, 1.0)
    return multiplier


def calculate_damage(
    attacker: Dict[str, Any], defender: Dict[str, Any], status: Optional[str]
) -> int:
    move = attacker["move"]
    attack_stat = attacker["base_stats"].get("attack", 50)
    defense_stat = defender["base_stats"].get("defense", 50)
    power = move["power"] or 50
    # Burn halves attack
    if status == STATUS_BURN:
        attack_stat = int(attack_stat / 2)
    type_multiplier = get_type_multiplier(move["type"], defender["types"])
    # Simple Pokémon damage formula
    damage = int(
        (((2 * 50 / 5 + 2) * power * attack_stat / defense_stat) / 50 + 2)
        * type_multiplier
    )
    return max(1, damage)


def apply_status_effects(status: Optional[str], hp: int) -> Tuple[int, str]:
    log = ""
    if status == STATUS_BURN:
        burn_damage = max(1, hp // 16)
        hp -= burn_damage
        log = f"Burn deals {burn_damage} damage. "
    elif status == STATUS_POISON:
        poison_damage = max(1, hp // 8)
        hp -= poison_damage
        log = f"Poison deals {poison_damage} damage. "
    return hp, log


def try_inflict_status(move: Dict[str, Any]) -> Optional[str]:
    effect = (move.get("effect") or "").lower()
    if "paralyze" in effect:
        return STATUS_PARALYSIS if random.random() < 0.2 else None
    if "burn" in effect:
        return STATUS_BURN if random.random() < 0.2 else None
    if "poison" in effect:
        return STATUS_POISON if random.random() < 0.2 else None
    return None


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
        poke2 = await fetch_pokemon_full_data(client, pokemon2)
        if not poke1 or not poke2:
            return {"error": "Could not fetch data for one or both Pokémon."}
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
                    f"{first_name} uses {first['move']['name']} and deals {damage} damage!"
                )
                # Try to inflict status
                new_status = try_inflict_status(first["move"])
                if not second_status and new_status:
                    second_status = new_status
                    log.append(f"{second_name} is now {new_status}!")
            # Apply status effects to second
            second_hp, status_log = apply_status_effects(second_status, second_hp)
            if status_log:
                log.append(f"{second_name}: {status_log}")
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
                    f"{second_name} uses {second['move']['name']} and deals {damage} damage!"
                )
                new_status = try_inflict_status(second["move"])
                if not first_status and new_status:
                    first_status = new_status
                    log.append(f"{first_name} is now {new_status}!")
            # Apply status effects to first
            first_hp, status_log = apply_status_effects(first_status, first_hp)
            if status_log:
                log.append(f"{first_name}: {status_log}")
            if first_hp <= 0:
                log.append(f"{first_name} fainted!")
                break
            turn += 1
        winner = first_name if first_hp > 0 else second_name
        log.append(f"Winner: {winner}!")
        return {
            "pokemon1": poke1["name"],
            "pokemon2": poke2["name"],
            "battle_log": log,
            "winner": winner,
        }
