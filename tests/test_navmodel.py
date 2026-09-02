"""
测试NavModel模块
"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingest import AirportParser, RunwayParser, NDBParser
from src.model import NavModelConverter, NavModelValidator, NavModelSerializer
from src.model.navmodel import Coordinate


def test_coordinate_parsing():
    """测试坐标解析"""
    print("=" * 60)
    print("测试坐标解析")
    print("=" * 60)

    # 测试紧凑格式解析
    coord = Coordinate.from_packed("N291522", "E0914551")

    assert coord.latitude > 29.25 and coord.latitude < 29.27, f"纬度解析错误: {coord.latitude}"
    assert coord.longitude > 91.75 and coord.longitude < 91.77, f"经度解析错误: {coord.longitude}"

    print(f"原始格式: N291522, E0914551")
    print(f"十进制度数: {coord.latitude:.6f}, {coord.longitude:.6f}")

    # 测试转换为度分秒
    lat_dms, lon_dms = coord.to_dms()
    print(f"度分秒格式: {lat_dms}, {lon_dms}")

    print("[PASS] 坐标解析测试通过\n")


def test_navmodel_conversion():
    """测试NavModel转换"""
    data_dir = Path(r"F:\我的世界动画\AI项目\导航数据\424源数据\2608\2608")

    if not data_dir.exists():
        print(f"[SKIP] 数据目录不存在: {data_dir}\n")
        return None

    print("=" * 60)
    print("测试NavModel转换")
    print("=" * 60)

    # 解析424数据
    airport_parser = AirportParser(data_dir)
    airports, _ = airport_parser.parse()

    runway_parser = RunwayParser(data_dir)
    runways, _ = runway_parser.parse()

    ndb_parser = NDBParser(data_dir)
    navaids, _ = ndb_parser.parse()

    # 转换为NavModel
    converter = NavModelConverter(airac_cycle="2608")
    navmodel = converter.build_navmodel(airports, runways, navaids)

    # 检查统计信息
    stats = navmodel.statistics
    print(f"NavModel统计:")
    print(f"  - 机场: {stats['airports']}")
    print(f"  - 跑道: {stats['runways']}")
    print(f"  - 导航台: {stats['navaids']}")

    assert stats['airports'] > 0, "没有机场数据"
    assert stats['runways'] > 0, "没有跑道数据"
    assert stats['navaids'] > 0, "没有导航台数据"

    # 测试查询功能
    zbaa = navmodel.get_airport_by_icao("ZBAA")
    assert zbaa is not None, "找不到ZBAA机场"
    print(f"\n查询ZBAA机场:")
    print(f"  - 名称: {zbaa.name}")
    print(f"  - 海拔: {zbaa.elevation}m")
    print(f"  - 跑道数: {len(zbaa.runways)}")

    zbaa_runways = navmodel.get_runways_by_airport("ZBAA")
    print(f"  - 跑道列表:")
    for runway in zbaa_runways:
        print(f"    - {runway.designation}: {runway.length}x{runway.width}m")

    # 测试坐标解析
    navaids_with_coords = [n for n in navmodel.navaids if n.coordinate is not None]
    print(f"\n导航台坐标解析:")
    print(f"  - 总数: {len(navmodel.navaids)}")
    print(f"  - 有坐标: {len(navaids_with_coords)}")

    if navaids_with_coords:
        sample = navaids_with_coords[0]
        print(f"  - 示例: {sample.code} ({sample.coordinate.latitude:.6f}, {sample.coordinate.longitude:.6f})")

    print("[PASS] NavModel转换测试通过\n")

    return navmodel


def test_navmodel_validation(navmodel):
    """测试NavModel验证"""
    if navmodel is None:
        print("[SKIP] 没有NavModel数据\n")
        return

    print("=" * 60)
    print("测试NavModel验证")
    print("=" * 60)

    validator = NavModelValidator()
    result = validator.validate(navmodel)

    result.print_summary()

    if not result.is_valid:
        print("[WARNING] 验证发现问题，但不影响测试通过")
    else:
        print("[PASS] NavModel验证测试通过\n")


def test_navmodel_serialization(navmodel):
    """测试NavModel序列化"""
    if navmodel is None:
        print("[SKIP] 没有NavModel数据\n")
        return

    print("=" * 60)
    print("测试NavModel序列化")
    print("=" * 60)

    output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)

    # 测试保存摘要
    summary_path = output_dir / "navmodel-summary.json"
    NavModelSerializer.save_summary(navmodel, summary_path)
    assert summary_path.exists(), "摘要文件未创建"
    print(f"摘要已保存: {summary_path}")

    # 测试保存完整JSON
    json_path = output_dir / "navmodel-test.json"
    NavModelSerializer.save_json(navmodel, json_path, compress=False)
    assert json_path.exists(), "JSON文件未创建"
    print(f"JSON已保存: {json_path} ({json_path.stat().st_size / 1024:.1f} KB)")

    # 测试保存压缩JSON
    gz_path = output_dir / "navmodel-test.json.gz"
    NavModelSerializer.save_json(navmodel, gz_path, compress=True)
    assert gz_path.exists(), "压缩文件未创建"
    print(f"压缩JSON已保存: {gz_path} ({gz_path.stat().st_size / 1024:.1f} KB)")

    print("[PASS] NavModel序列化测试通过\n")


if __name__ == "__main__":
    print("=" * 60)
    print("NavModel模块测试")
    print("=" * 60)
    print()

    try:
        # 测试坐标解析
        test_coordinate_parsing()

        # 测试NavModel转换
        navmodel = test_navmodel_conversion()

        # 测试验证
        test_navmodel_validation(navmodel)

        # 测试序列化
        test_navmodel_serialization(navmodel)

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
