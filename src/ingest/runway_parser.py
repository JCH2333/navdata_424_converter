"""
跑道数据解析器

解析RWY.csv（跑道）数据
"""

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
import logging

from .base_parser import Arinc424Parser, ParseResult

logger = logging.getLogger(__name__)


@dataclass
class Runway:
    """跑道数据模型"""
    id: str  # RWY_ID
    airport_id: str  # AD_HP_ID (关联机场)
    airport_code: str  # CODE_AIRPORT (ICAO代码)
    designation: str  # TXT_DESIG (跑道号，如"01L/19R")
    length: Optional[float]  # VAL_LEN
    width: Optional[float]  # VAL_WID
    dimension_unit: Optional[str]  # UOM_DIM_RWY
    surface_composition: Optional[str]  # CODE_COMPOSITION
    strength_code: Optional[str]  # CODE_STRENGTH (PCR/PCN)
    strength_description: Optional[str]  # TXT_DESCR_STRENGTH
    remarks: Optional[str]  # TXT_RMK

    # 原始数据
    raw_data: dict


class RunwayParser(Arinc424Parser):
    """跑道数据解析器"""

    FILENAME = "RWY.csv"

    REQUIRED_FIELDS = [
        "RWY_ID",
        "AD_HP_ID",
        "CODE_AIRPORT",
        "TXT_DESIG"
    ]

    def parse(self) -> tuple[List[Runway], ParseResult]:
        """
        解析跑道数据

        Returns:
            (跑道列表, 解析结果)
        """
        result = self.read_csv(self.FILENAME)

        if not result.success:
            logger.error(f"读取跑道数据失败: {result.errors}")
            return [], result

        runways = []
        errors = []

        for row_num, row in enumerate(result.data, start=2):
            # 验证必填字段
            validation_errors = self.validate_required_fields(row, self.REQUIRED_FIELDS)
            if validation_errors:
                errors.extend([f"第{row_num}行: {e}" for e in validation_errors])
                continue

            try:
                runway = self._parse_runway(row)
                runways.append(runway)
            except Exception as e:
                errors.append(f"第{row_num}行解析失败: {str(e)}")
                logger.warning(f"解析跑道数据失败，行号 {row_num}: {e}")

        logger.info(f"成功解析 {len(runways)} 条跑道")

        result.errors.extend(errors)
        result.success = len(runways) > 0

        return runways, result

    def _parse_runway(self, row: dict) -> Runway:
        """解析单个跑道记录"""

        # 解析长度
        length = None
        if row.get("VAL_LEN"):
            try:
                length = float(row["VAL_LEN"])
            except ValueError:
                pass

        # 解析宽度
        width = None
        if row.get("VAL_WID"):
            try:
                width = float(row["VAL_WID"])
            except ValueError:
                pass

        return Runway(
            id=row["RWY_ID"],
            airport_id=row["AD_HP_ID"],
            airport_code=row["CODE_AIRPORT"],
            designation=row["TXT_DESIG"].strip(),
            length=length,
            width=width,
            dimension_unit=row.get("UOM_DIM_RWY") or None,
            surface_composition=row.get("CODE_COMPOSITION") or None,
            strength_code=row.get("CODE_STRENGTH") or None,
            strength_description=row.get("TXT_DESCR_STRENGTH") or None,
            remarks=row.get("TXT_RMK") or None,
            raw_data=row
        )

    def get_runways_by_airport(self, runways: List[Runway], airport_code: str) -> List[Runway]:
        """
        获取指定机场的所有跑道

        Args:
            runways: 跑道列表
            airport_code: 机场ICAO代码

        Returns:
            跑道列表
        """
        return [r for r in runways if r.airport_code == airport_code]

    def parse_runway_ends(self, designation: str) -> tuple[str, str]:
        """
        解析跑道两端标识

        Args:
            designation: 跑道号，如"01L/19R"

        Returns:
            (跑道1, 跑道2) 如("01L", "19R")
        """
        if '/' in designation:
            parts = designation.split('/')
            return parts[0].strip(), parts[1].strip()
        return designation.strip(), ""
