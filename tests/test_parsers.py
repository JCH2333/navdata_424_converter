"""
测试424解析器模块
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest import AirportParser, RunwayParser, NDBParser


def test_airport_parser():
    """测试机场解析器"""
    data_dir = Path(r"F:\我的世界动画\AI项目\导航数据\424源数据\2608\2608")

    if not data_dir.exists():
        print(f"[SKIP] 数据目录不存在: {data_dir}")
        return

    parser = AirportParser(data_dir)
    airports, result = parser.parse()

    assert result.success, f"解析失败: {result.errors}"
    assert len(airports) > 0, "没有解析到机场数据"

    print(f"[PASS] 机场解析器测试通过")
    print(f"  - 解析了 {len(airports)} 个机场")
    print(f"  - 总记录数: {result.record_count}")

    # 显示前3个机场
    for i, airport in enumerate(airports[:3]):
        print(f"  - 机场 {i+1}: {airport.code} - {airport.name} (海拔: {airport.elevation}{airport.elevation_unit})")

    # 测试查找功能
    zbaa = parser.get_airport_by_code(airports, "ZBAA")
    if zbaa:
        print(f"  - 查找ZBAA: {zbaa.name}")


def test_runway_parser():
    """测试跑道解析器"""
    data_dir = Path(r"F:\我的世界动画\AI项目\导航数据\424源数据\2608\2608")

    if not data_dir.exists():
        print(f"[SKIP] 数据目录不存在: {data_dir}")
        return

    parser = RunwayParser(data_dir)
    runways, result = parser.parse()

    assert result.success, f"解析失败: {result.errors}"
    assert len(runways) > 0, "没有解析到跑道数据"

    print(f"[PASS] 跑道解析器测试通过")
    print(f"  - 解析了 {len(runways)} 条跑道")
    print(f"  - 总记录数: {result.record_count}")

    # 显示前3条跑道
    for i, runway in enumerate(runways[:3]):
        print(f"  - 跑道 {i+1}: {runway.airport_code} {runway.designation} ({runway.length}x{runway.width}{runway.dimension_unit})")

    # 测试跑道端解析
    end1, end2 = parser.parse_runway_ends("01L/19R")
    assert end1 == "01L" and end2 == "19R", "跑道端解析失败"
    print(f"  - 跑道端解析: 01L/19R -> {end1}, {end2}")


def test_ndb_parser():
    """测试NDB解析器"""
    data_dir = Path(r"F:\我的世界动画\AI项目\导航数据\424源数据\2608\2608")

    if not data_dir.exists():
        print(f"[SKIP] 数据目录不存在: {data_dir}")
        return

    parser = NDBParser(data_dir)
    navaids, result = parser.parse()

    assert result.success, f"解析失败: {result.errors}"
    assert len(navaids) > 0, "没有解析到NDB数据"

    print(f"[PASS] NDB解析器测试通过")
    print(f"  - 解析了 {len(navaids)} 个NDB导航台")
    print(f"  - 总记录数: {result.record_count}")

    # 显示前3个NDB
    for i, navaid in enumerate(navaids[:3]):
        print(f"  - NDB {i+1}: {navaid.code} - {navaid.name} (频率: {navaid.frequency} kHz)")


def test_integration():
    """测试集成功能：查找机场及其跑道"""
    data_dir = Path(r"F:\我的世界动画\AI项目\导航数据\424源数据\2608\2608")

    if not data_dir.exists():
        print(f"[SKIP] 数据目录不存在: {data_dir}")
        return

    # 解析机场和跑道
    airport_parser = AirportParser(data_dir)
    airports, _ = airport_parser.parse()

    runway_parser = RunwayParser(data_dir)
    runways, _ = runway_parser.parse()

    # 查找ZBAA及其跑道
    zbaa = airport_parser.get_airport_by_code(airports, "ZBAA")
    if zbaa:
        zbaa_runways = runway_parser.get_runways_by_airport(runways, "ZBAA")
        print(f"[PASS] 集成测试通过")
        print(f"  - 机场: {zbaa.code} - {zbaa.name}")
        print(f"  - 跑道数: {len(zbaa_runways)}")
        for runway in zbaa_runways:
            print(f"    - {runway.designation}")


if __name__ == "__main__":
    print("=" * 60)
    print("424解析器模块测试")
    print("=" * 60)

    try:
        test_airport_parser()
        print()
        test_runway_parser()
        print()
        test_ndb_parser()
        print()
        test_integration()
        print()
        print("=" * 60)
        print("[SUCCESS] 所有测试通过！")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n[FAIL] 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
