from app.services.pack_engine import (
    CATEGORY_LIQUID,
    CATEGORY_NORMAL,
    CATEGORY_PRINTED,
    Bag,
    StopItem,
    category_compatible,
    pack_route,
)


def test_packs_in_route_order_splitting_bags():
    stops = [
        StopItem(1, 1, 2.0, 3.0),
        StopItem(2, 2, 2.5, 3.0),
        StopItem(3, 3, 1.0, 1.0),
    ]
    result = pack_route(stops, max_weight=4.0, max_volume=10.0)
    assert len(result.bags) == 2
    assert [i.stop_id for i in result.bags[0].items] == [1]
    assert [i.stop_id for i in result.bags[1].items] == [2, 3]
    assert not result.rejects


def test_reject_oversized_stop():
    stops = [StopItem(1, 1, 9.0, 1.0, "大件"), StopItem(2, 2, 1.0, 1.0)]
    result = pack_route(stops, max_weight=5.0, max_volume=5.0)
    assert len(result.rejects) == 1
    assert result.rejects[0][0].stop_id == 1
    assert len(result.bags) == 1
    assert result.bags[0].items[0].stop_id == 2


def test_volume_cap_triggers_new_bag():
    stops = [StopItem(1, 1, 1.0, 4.0), StopItem(2, 2, 1.0, 4.0)]
    result = pack_route(stops, max_weight=10.0, max_volume=5.0)
    assert len(result.bags) == 2


def test_printed_and_liquid_never_share_bag_even_when_capacity_allows():
    # 印刷与液体顺序相邻，合计 5.3kg/8.5L，双约束（8kg/18L）本可同袋，
    # 仅因品类互斥必须新开袋。
    stops = [
        StopItem(1, 1, 3.5, 5.5, "印刷站", CATEGORY_PRINTED),
        StopItem(2, 2, 1.8, 3.0, "液体站", CATEGORY_LIQUID),
    ]
    result = pack_route(stops, max_weight=8.0, max_volume=18.0)
    assert not result.rejects
    assert len(result.bags) == 2
    assert [i.stop_id for i in result.bags[0].items] == [1]
    assert [i.stop_id for i in result.bags[1].items] == [2]
    assert result.bags[0].categories == {CATEGORY_PRINTED}
    assert result.bags[1].categories == {CATEGORY_LIQUID}


def test_adjacent_normal_can_share_bag_with_printed():
    # 相邻的普通订户可与印刷品同袋；后续液体即便容量仍够也不得并入。
    stops = [
        StopItem(1, 1, 2.0, 3.0, "印刷站", CATEGORY_PRINTED),
        StopItem(2, 2, 1.0, 1.0, "普通站", CATEGORY_NORMAL),
        StopItem(3, 3, 1.0, 1.0, "液体站", CATEGORY_LIQUID),
    ]
    result = pack_route(stops, max_weight=10.0, max_volume=20.0)
    assert not result.rejects
    assert len(result.bags) == 2
    assert [i.stop_id for i in result.bags[0].items] == [1, 2]
    assert [i.stop_id for i in result.bags[1].items] == [3]


def test_normal_can_share_bag_with_liquid_then_printed_split():
    stops = [
        StopItem(1, 1, 1.0, 1.0, "液体站", CATEGORY_LIQUID),
        StopItem(2, 2, 1.0, 1.0, "普通站", CATEGORY_NORMAL),
        StopItem(3, 3, 1.0, 1.0, "印刷站", CATEGORY_PRINTED),
    ]
    result = pack_route(stops, max_weight=10.0, max_volume=20.0)
    assert not result.rejects
    assert len(result.bags) == 2
    assert [i.stop_id for i in result.bags[0].items] == [1, 2]
    assert [i.stop_id for i in result.bags[1].items] == [3]


def test_oversized_stop_still_rejected_with_category():
    # 双约束单站超限仍按现网拒收，且拒收不影响后续站点装袋。
    stops = [
        StopItem(1, 1, 1.0, 1.0, "印刷站", CATEGORY_PRINTED),
        StopItem(2, 2, 9.5, 6.0, "超大件", CATEGORY_NORMAL),
        StopItem(3, 3, 2.0, 4.5, "咖啡店", CATEGORY_NORMAL),
    ]
    result = pack_route(stops, max_weight=8.0, max_volume=18.0)
    assert len(result.rejects) == 1
    rejected, reason = result.rejects[0]
    assert rejected.stop_id == 2
    assert "超重" in reason
    assert [i.stop_id for i in result.bags[0].items] == [1, 3]


def _assert_no_ink_liquid_mix(result):
    for bag in result.bags:
        cats = {i.category for i in bag.items}
        assert CATEGORY_PRINTED not in cats or CATEGORY_LIQUID not in cats, (
            f"袋 {bag.bag_index} 印刷与液体同袋: {[i.stop_id for i in bag.items]}"
        )
        # 袋标记必须与袋内实际物品一致（不得丢弃印刷/液体标记）
        assert bag.categories == cats


def test_interleaved_ink_liquid_normal_never_mix_and_marks_match():
    # 大量交错序列：印刷/液体反复交替，普通穿插；容量始终充裕。
    seq = [
        CATEGORY_PRINTED, CATEGORY_NORMAL, CATEGORY_LIQUID, CATEGORY_LIQUID,
        CATEGORY_NORMAL, CATEGORY_PRINTED, CATEGORY_PRINTED, CATEGORY_LIQUID,
        CATEGORY_NORMAL, CATEGORY_LIQUID, CATEGORY_PRINTED, CATEGORY_NORMAL,
    ]
    stops = [
        StopItem(i + 1, i + 1, 0.5, 0.5, f"站{i + 1}", cat)
        for i, cat in enumerate(seq)
    ]
    result = pack_route(stops, max_weight=100.0, max_volume=100.0)
    assert not result.rejects
    _assert_no_ink_liquid_mix(result)
    # 同品类相邻（含普通）应同袋：袋数严格小于站点数
    assert len(result.bags) < len(stops)
    # 互斥切换点必须新开袋：同袋内相邻物品不得是印刷/液体对
    for b in result.bags:
        for i1, i2 in zip(b.items, b.items[1:]):
            assert {i1.category, i2.category} != {CATEGORY_PRINTED, CATEGORY_LIQUID}, (
                f"袋 {b.bag_index} 内相邻印刷/液体同袋"
            )


def test_bag_categories_always_reflect_items_for_seed_layout():
    # 对齐种子数据：印刷站 -> 液体站相邻，即使双约束有余量也必须分开，
    # 且两侧袋标记分别为印刷、液体，不被掏空成空集合。
    stops = [
        StopItem(1, 1, 2.2, 4.0, "普通站", CATEGORY_NORMAL),
        StopItem(2, 2, 3.5, 5.5, "印刷站", CATEGORY_PRINTED),
        StopItem(3, 3, 1.8, 3.0, "液体站", CATEGORY_LIQUID),
        StopItem(4, 4, 2.0, 4.5, "咖啡店", CATEGORY_NORMAL),
    ]
    result = pack_route(stops, max_weight=8.0, max_volume=18.0)
    _assert_no_ink_liquid_mix(result)
    assert result.bags[0].categories == {CATEGORY_NORMAL, CATEGORY_PRINTED}
    assert result.bags[1].categories == {CATEGORY_LIQUID, CATEGORY_NORMAL}


def test_over_volume_only_reason_is_not_fake_overweight():
    # 仅超体积（重量合规）时，拒收原因必须写超体积，不得伪装成超重。
    stops = [StopItem(1, 1, 1.0, 99.0, "超体积件", CATEGORY_NORMAL)]
    result = pack_route(stops, max_weight=8.0, max_volume=18.0)
    assert len(result.rejects) == 1
    _, reason = result.rejects[0]
    assert "超体积" in reason
    assert "超重" not in reason


def test_overweight_and_overvolume_reason_lists_both():
    stops = [StopItem(1, 1, 99.0, 99.0, "双超限件", CATEGORY_PRINTED)]
    result = pack_route(stops, max_weight=8.0, max_volume=18.0)
    assert len(result.rejects) == 1
    rejected, reason = result.rejects[0]
    assert rejected.category == CATEGORY_PRINTED
    assert "超重" in reason and "超体积" in reason


def test_mutex_split_never_rejects_when_capacity_holds():
    # 互斥的处理动作是新开袋而非拒收：再多次交替也不产生拒收。
    stops = [
        StopItem(i + 1, i + 1, 0.3, 0.3, "站",
                 CATEGORY_PRINTED if i % 2 == 0 else CATEGORY_LIQUID)
        for i in range(10)
    ]
    result = pack_route(stops, max_weight=8.0, max_volume=18.0)
    assert not result.rejects
    assert len(result.bags) == 10
    _assert_no_ink_liquid_mix(result)


def test_repack_same_route_is_deterministic():
    stops = [
        StopItem(1, 1, 3.5, 5.5, "印刷站", CATEGORY_PRINTED),
        StopItem(2, 2, 1.8, 3.0, "液体站", CATEGORY_LIQUID),
        StopItem(3, 3, 1.0, 1.0, "普通站", CATEGORY_NORMAL),
    ]
    first = pack_route(list(stops), 8.0, 18.0)
    second = pack_route(list(stops), 8.0, 18.0)
    layout1 = [[(i.stop_id, i.category) for i in b.items] for b in first.bags]
    layout2 = [[(i.stop_id, i.category) for i in b.items] for b in second.bags]
    assert layout1 == layout2


def test_category_compatible_unit():
    base = Bag(bag_index=1)
    assert category_compatible(base, CATEGORY_PRINTED)
    assert category_compatible(base, CATEGORY_LIQUID)
    base.categories.add(CATEGORY_PRINTED)
    assert category_compatible(base, CATEGORY_NORMAL)
    assert category_compatible(base, CATEGORY_PRINTED)
    assert not category_compatible(base, CATEGORY_LIQUID)
    base.categories = {CATEGORY_LIQUID}
    assert not category_compatible(base, CATEGORY_PRINTED)
