"""
导航台数据解析器

解析NDB.csv（NDB无线电导航台）数据
"""

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
import logging

from .base_parser import Arinc424Parser, ParseResult

logger = logging.getLogger(__name__)


@dataclass
class Navaid:
    """导航台数据模型（NDB）"""
    id: str  # SIGNIFICANT_POINT_ID
    code: str  # CODE_ID (导航台标识符)
    name: Optional[str]  # TXT_NAME
    navaid_type: Optional[str]  # CODE_TYPE (NDB/VOR/DME等)
    frequency: Optional[float]  # VAL_FREQ
    frequency_unit: Optional[str]  # UOM_FREQ
    latitude: Optional[str]  # GEO_LAT_ACCURACY (格式: N291522)
    longitude: Optional[str]  # GEO_LONG_ACCURACY (格式: E0914551)
    elevation: Optional[float]  # VAL_ELEV
    mag_var: Optional[float]  # VAL_MAG_VAR
    fir_code: Optional[str]  # CODE_FIR
    remarks: Optional[str]  # TXT_RMK

    # 原始数据
    raw_data: dict


class NDBParser(Arinc424Parser):
    """NDB导航台解析器"""

    FILENAME = "NDB.csv"

    REQUIRED_FIELDS = [
        "SIGNIFICANT_POINT_ID",
        "CODE_ID"
    ]

    def parse(self) -> tuple[List[Navaid], ParseResult]:
        """
        解析NDB数据

        Returns:
            (导航台列表, 解析结果)
        """
        result = self.read_csv(self.FILENAME)

        if not result.success:
            logger.error(f"读取NDB数据失败: {result.errors}")
            return [], result

        navaids = []
        errors = []

        for row_num, row in enumerate(result.data, start=2):
            # 验证必填字段
            validation_errors = self.validate_required_fields(row, self.REQUIRED_FIELDS)
            if validation_errors:
                errors.extend([f"第{row_num}行: {e}" for e in validation_errors])
                continue

            try:
                navaid = self._parse_navaid(row)
                navaids.append(navaid)
            except Exception as e:
                errors.append(f"第{row_num}行解析失败: {str(e)}")
                logger.warning(f"解析NDB数据失败，行号 {row_num}: {e}")

        logger.info(f"成功解析 {len(navaids)} 个NDB导航台")

        result.errors.extend(errors)
        result.success = len(navaids) > 0

        return navaids, result

    def _parse_navaid(self, row: dict) -> Navaid:
        """解析单个NDB记录"""

        # 解析频率
        frequency = None
        if row.get("VAL_FREQ"):
            try:
                frequency = float(row["VAL_FREQ"])
            except ValueError:
                pass

        # 解析海拔
        elevation = None
        if row.get("VAL_ELEV"):
            try:
                elevation = float(row["VAL_ELEV"])
            except ValueError:
                pass

        # 解析磁差
        mag_var = None
        if row.get("VAL_MAG_VAR"):
            try:
                mag_var = float(row["VAL_MAG_VAR"])
            except ValueError:
                pass

        return Navaid(
            id=row["SIGNIFICANT_POINT_ID"],
            code=row["CODE_ID"],
            name=row.get("TXT_NAME") or None,
            navaid_type=row.get("CODE_TYPE") or None,
            frequency=frequency,
            frequency_unit=row.get("UOM_FREQ") or None,
            latitude=row.get("GEO_LAT_ACCURACY") or None,
            longitude=row.get("GEO_LONG_ACCURACY") or None,
            elevation=elevation,
            mag_var=mag_var,
            fir_code=row.get("CODE_FIR") or None,
            remarks=row.get("TXT_RMK") or None,
            raw_data=row
        )

    def _parse_coordinate(self, coord_str: str) -> float:
        """
        解析坐标字符串

        支持多种格式：
        - 十进制度数：39.5
        - 度分秒：N39°30'00"

        Args:
            coord_str: 坐标字符串

        Returns:
            十进制度数
        """
        coord_str = coord_str.strip()

        # 尝试直接转换为浮点数
        try:
            return float(coord_str)
        except ValueError:
            pass

        # TODO: 实现度分秒格式解析
        # 如果需要支持其他格式，在这里添加解析逻辑

        raise ValueError(f"无法解析坐标: {coord_str}")

    def get_navaid_by_code(self, navaids: List[Navaid], code: str) -> Optional[Navaid]:
        """
        根据代码查找导航台

        Args:
            navaids: 导航台列表
            code: 导航台代码

        Returns:
            导航台对象或None
        """
        for navaid in navaids:
            if navaid.code == code:
                return navaid
        return None
