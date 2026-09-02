"""
机场数据解析器

解析AD_HP.csv（机场直升机场）数据
"""

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
import logging

from .base_parser import Arinc424Parser, ParseResult

logger = logging.getLogger(__name__)


@dataclass
class Airport:
    """机场数据模型"""
    id: str  # AD_HP_ID
    code: str  # CODE_ID (ICAO代码)
    name: str  # TXT_NAME
    iata_code: Optional[str]  # CODE_IATA
    fir_code: Optional[str]  # CODE_FIR
    elevation: Optional[float]  # VAL_ELEV
    elevation_unit: Optional[str]  # UOM_DIST_VER
    mag_var: Optional[float]  # VAL_MAG_VAR
    transition_alt: Optional[int]  # VAL_TRANSITION_ALT
    transition_level: Optional[int]  # VAL_TRANSITION_LEVEL
    is_international: bool  # IS_INTERNATIONAL
    is_military: bool  # CODE_TYPE_MIL_OPS
    remarks: Optional[str]  # TXT_RMK

    # 原始数据（用于调试）
    raw_data: dict


class AirportParser(Arinc424Parser):
    """机场数据解析器"""

    FILENAME = "AD_HP.csv"

    REQUIRED_FIELDS = [
        "AD_HP_ID",
        "CODE_ID",
        "TXT_NAME"
    ]

    def parse(self) -> tuple[List[Airport], ParseResult]:
        """
        解析机场数据

        Returns:
            (机场列表, 解析结果)
        """
        result = self.read_csv(self.FILENAME)

        if not result.success:
            logger.error(f"读取机场数据失败: {result.errors}")
            return [], result

        airports = []
        errors = []

        for row_num, row in enumerate(result.data, start=2):
            # 验证必填字段
            validation_errors = self.validate_required_fields(row, self.REQUIRED_FIELDS)
            if validation_errors:
                errors.extend([f"第{row_num}行: {e}" for e in validation_errors])
                continue

            try:
                airport = self._parse_airport(row)
                airports.append(airport)
            except Exception as e:
                errors.append(f"第{row_num}行解析失败: {str(e)}")
                logger.warning(f"解析机场数据失败，行号 {row_num}: {e}")

        logger.info(f"成功解析 {len(airports)} 个机场")

        result.errors.extend(errors)
        result.success = len(airports) > 0

        return airports, result

    def _parse_airport(self, row: dict) -> Airport:
        """解析单个机场记录"""

        # 解析海拔高度
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

        # 解析过渡高度
        transition_alt = None
        if row.get("VAL_TRANSITION_ALT"):
            try:
                transition_alt = int(float(row["VAL_TRANSITION_ALT"]))
            except ValueError:
                pass

        # 解析过渡高度层
        transition_level = None
        if row.get("VAL_TRANSITION_LEVEL"):
            try:
                transition_level = int(float(row["VAL_TRANSITION_LEVEL"]))
            except ValueError:
                pass

        # 判断是否国际机场
        is_international = row.get("IS_INTERNATIONAL", "N").upper() == "Y"

        # 判断是否军用机场
        is_military = row.get("CODE_TYPE_MIL_OPS", "").upper() == "MA"

        return Airport(
            id=row["AD_HP_ID"],
            code=row.get("CODE_ID", ""),
            name=row.get("TXT_NAME", ""),
            iata_code=row.get("CODE_IATA") or None,
            fir_code=row.get("CODE_FIR") or None,
            elevation=elevation,
            elevation_unit=row.get("UOM_DIST_VER") or None,
            mag_var=mag_var,
            transition_alt=transition_alt,
            transition_level=transition_level,
            is_international=is_international,
            is_military=is_military,
            remarks=row.get("TXT_RMK") or None,
            raw_data=row
        )

    def get_airport_by_code(self, airports: List[Airport], code: str) -> Optional[Airport]:
        """
        根据ICAO代码查找机场

        Args:
            airports: 机场列表
            code: ICAO代码

        Returns:
            机场对象或None
        """
        for airport in airports:
            if airport.code == code:
                return airport
        return None
