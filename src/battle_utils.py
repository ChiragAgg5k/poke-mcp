"""Module for battle utilities."""
from typing import Any, Dict, List, Optional, Tuple
import random
from src.constants import (
    TYPE_EFFECTIVENESS,
    STATUS_PARALYSIS,
    STATUS_BURN,
    STATUS_POISON,
)


def parse_evolution_chain(chain):
    """Parse the evolution chain of a Pokémon.

    Args:
        chain (any): The evolution chain to parse.

    Returns:
        A list of Pokémon names in the evolution chain.
    """
    evo_chain = []
    current = chain
    while current:
        evo_chain.append(current["species"]["name"])
        if current["evolves_to"]:
            current = current["evolves_to"][0]
        else:
            current = None
    return evo_chain


def get_type_multiplier(attack_type: str, defender_types: List[str]) -> float:
    """Get the type multiplier for an attack.

    Args:
        attack_type (str): The type of the attack.
        defender_types (List[str]): The types of the defender.

    Returns:
        float: The type multiplier.
    """
    multiplier = 1.0
    for d_type in defender_types:
        multiplier *= TYPE_EFFECTIVENESS.get(attack_type, {}).get(d_type, 1.0)
    return multiplier


def calculate_damage(
    attacker: Dict[str, Any], defender: Dict[str, Any], status: Optional[str]
) -> int:
    """Calculate the damage dealt by an attack.

    Args:
        attacker (Dict[str, Any]): The attacker.
        defender (Dict[str, Any]): The defender.
        status (Optional[str]): The status of the attacker.

    Returns:
        int: The damage dealt.
    """
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
    """Apply status effects to a Pokémon.

    Args:
        status (Optional[str]): The status to apply.
        hp (int): The HP of the Pokémon.

    Returns:
        Tuple[int, str]: The new HP and the log of the status effects.
    """
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
    """Try to inflict a status effect on a Pokémon.

    Args:
        move (Dict[str, Any]): The move to try to inflict a status effect on.

    Returns:
        Optional[str]: The status effect inflicted, or None if no status effect was inflicted.
    """
    effect = (move.get("effect") or "").lower()
    if "paralyze" in effect:
        return STATUS_PARALYSIS if random.random() < 0.2 else None
    if "burn" in effect:
        return STATUS_BURN if random.random() < 0.2 else None
    if "poison" in effect:
        return STATUS_POISON if random.random() < 0.2 else None
    return None
