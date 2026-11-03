from dataclasses import dataclass
from typing import Any

SLEEP_CHANCE = 0.25
VAMPIRE_MAX_HP_DRAIN = 1


@dataclass(frozen=True)
class SpecialRule:
    skip_first_hit: bool = False
    max_hp_drain: int = 0
    sleep_chance: float = 0.0
    rest_and_counter: bool = False


SPECIAL_RULES: dict[str, SpecialRule] = {
    "vampire": SpecialRule(skip_first_hit=True, max_hp_drain=VAMPIRE_MAX_HP_DRAIN),
    "ogre": SpecialRule(rest_and_counter=True),
    "snake_mage": SpecialRule(sleep_chance=SLEEP_CHANCE),
}


def special_rule_for(enemy_type: Any) -> SpecialRule | None:
    name = getattr(enemy_type, "value", enemy_type)
    if name is None:
        return None
    return SPECIAL_RULES.get(str(name).lower())
