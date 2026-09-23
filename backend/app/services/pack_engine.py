"""Route-order bag packing with weight + volume caps; reject when exceed.

品类互斥：印刷品（printed）与液体（liquid）不得同袋，即使双约束仍有余量
也要新开袋；普通（normal）可与任一方同袋。互斥的处理动作是新开袋，不产生
拒收。单站超重量/体积仍直接拒收，原因区分超重与超体积。
"""

from __future__ import annotations

from dataclasses import dataclass, field

CATEGORY_NORMAL = "normal"
CATEGORY_PRINTED = "printed"
CATEGORY_LIQUID = "liquid"
CATEGORIES = (CATEGORY_NORMAL, CATEGORY_PRINTED, CATEGORY_LIQUID)
CATEGORY_LABELS = {
    CATEGORY_NORMAL: "普通",
    CATEGORY_PRINTED: "印刷",
    CATEGORY_LIQUID: "液体",
}

# 互斥品类对：同袋中不得同时出现。仅此一对（印刷-液体），不做泛化。
_INCOMPATIBLE_PAIRS = (frozenset({CATEGORY_PRINTED, CATEGORY_LIQUID}),)


@dataclass(frozen=True)
class StopItem:
    stop_id: int
    seq: int
    weight_kg: float
    volume_l: float
    label: str = ""
    category: str = CATEGORY_NORMAL


@dataclass
class Bag:
    bag_index: int
    items: list[StopItem] = field(default_factory=list)
    weight_kg: float = 0.0
    volume_l: float = 0.0
    categories: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class PackResult:
    bags: list[Bag]
    rejects: list[tuple[StopItem, str]]


def category_compatible(bag: Bag, category: str) -> bool:
    """普通可与任意品类同袋；印刷与液体互斥，不得进入已装对立品类的袋。"""
    if category == CATEGORY_NORMAL:
        return True
    return all(
        frozenset({category, existing}) not in _INCOMPATIBLE_PAIRS
        for existing in bag.categories
    )


def can_fit(bag: Bag, item: StopItem, max_weight: float, max_volume: float) -> bool:
    return (
        bag.weight_kg + item.weight_kg <= max_weight + 1e-9
        and bag.volume_l + item.volume_l <= max_volume + 1e-9
    )


def pack_route(
    stops: list[StopItem],
    max_weight: float,
    max_volume: float,
) -> PackResult:
    ordered = sorted(stops, key=lambda s: s.seq)
    bags: list[Bag] = []
    rejects: list[tuple[StopItem, str]] = []
    current: Bag | None = None

    for item in ordered:
        # 单站超约束：直接拒收，原因如实区分超重/超体积，不进任何袋。
        if item.weight_kg > max_weight or item.volume_l > max_volume:
            reason = []
            if item.weight_kg > max_weight:
                reason.append(f"超重 {item.weight_kg}>{max_weight}")
            if item.volume_l > max_volume:
                reason.append(f"超体积 {item.volume_l}>{max_volume}")
            rejects.append((item, "；".join(reason)))
            continue

        # 双约束放不下，或品类互斥（印刷 vs 液体）——即使仍有余量也新开袋。
        if (
            current is None
            or not can_fit(current, item, max_weight, max_volume)
            or not category_compatible(current, item.category)
        ):
            current = Bag(bag_index=len(bags) + 1)
            bags.append(current)

        current.items.append(item)
        current.weight_kg += item.weight_kg
        current.volume_l += item.volume_l
        current.categories.add(item.category)

    return PackResult(bags=bags, rejects=rejects)
