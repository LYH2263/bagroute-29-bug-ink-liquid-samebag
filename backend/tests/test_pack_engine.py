from app.services.pack_engine import (
    CATEGORY_LIQUID,
    CATEGORY_NORMAL,
    CATEGORY_PRINTED,
    StopItem,
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
