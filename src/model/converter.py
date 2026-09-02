"""
424解析器到NavModel的转换器

将解析器的数据模型转换为统一的NavModel
"""

from typing import List
import logging

from ..ingest import Airport, Runway, Navaid
from .navmodel import (
    NavModel, NavModelAirport, NavModelRunway, NavModelNavaid,
    SourceInfo, Coordinate, NavaidType, CoordinateFormat
)

logger = logging.getLogger(__name__)


class NavModelConverter:
    """NavModel转换器"""

    def __init__(self, airac_cycle: str = "2608"):
        """
        初始化转换器

        Args:
            airac_cycle: AIRAC周期
        """
        self.airac_cycle = airac_cycle

    def convert_airports(self, airports: List[Airport]) -> List[NavModelAirport]:
        """
        转换机场列表

        Args:
            airports: 解析器机场列表

        Returns:
            NavModel机场列表
        """
        result = []
        for airport in airports:
            try:
                nav_airport = self._convert_airport(airport)
                result.append(nav_airport)
            except Exception as e:
                logger.warning(f"转换机场失败 {airport.code}: {e}")

        logger.info(f"成功转换 {len(result)}/{len(airports)} 个机场")
        return result

    def _convert_airport(self, airport: Airport) -> NavModelAirport:
        """转换单个机场"""
        # 创建来源信息
        source = SourceInfo(
            file_name="AD_HP.csv",
            line_number=0,  # TODO: 从raw_data获取
            record_id=airport.id,
            airac_cycle=self.airac_cycle,
            raw_data=airport.raw_data
        )

        return NavModelAirport(
            icao_code=airport.code,
            name=airport.name,
            iata_code=airport.iata_code,
            coordinate=None,  # TODO: 解析坐标
            elevation=airport.elevation,
            magnetic_variation=airport.mag_var,
            transition_altitude=airport.transition_alt,
            transition_level=airport.transition_level,
            is_international=airport.is_international,
            is_military=airport.is_military,
            fir_code=airport.fir_code,
            remarks=airport.remarks,
            source=source,
            runways=[]
        )

    def convert_runways(self, runways: List[Runway]) -> List[NavModelRunway]:
        """
        转换跑道列表

        Args:
            runways: 解析器跑道列表

        Returns:
            NavModel跑道列表
        """
        result = []
        for runway in runways:
            try:
                nav_runway = self._convert_runway(runway)
                result.append(nav_runway)
            except Exception as e:
                logger.warning(f"转换跑道失败 {runway.airport_code} {runway.designation}: {e}")

        logger.info(f"成功转换 {len(result)}/{len(runways)} 条跑道")
        return result

    def _convert_runway(self, runway: Runway) -> NavModelRunway:
        """转换单个跑道"""
        # 创建来源信息
        source = SourceInfo(
            file_name="RWY.csv",
            line_number=0,
            record_id=runway.id,
            airac_cycle=self.airac_cycle,
            raw_data=runway.raw_data
        )

        return NavModelRunway(
            designation=runway.designation,
            airport_icao=runway.airport_code,
            length=runway.length,
            width=runway.width,
            surface_type=runway.surface_composition,
            strength_code=runway.strength_code,
            remarks=runway.remarks,
            source=source
        )

    def convert_navaids(self, navaids: List[Navaid]) -> List[NavModelNavaid]:
        """
        转换导航台列表

        Args:
            navaids: 解析器导航台列表

        Returns:
            NavModel导航台列表
        """
        result = []
        for navaid in navaids:
            try:
                nav_navaid = self._convert_navaid(navaid)
                result.append(nav_navaid)
            except Exception as e:
                logger.warning(f"转换导航台失败 {navaid.code}: {e}")

        logger.info(f"成功转换 {len(result)}/{len(navaids)} 个导航台")
        return result

    def _convert_navaid(self, navaid: Navaid) -> NavModelNavaid:
        """转换单个导航台"""
        # 创建来源信息
        source = SourceInfo(
            file_name="NDB.csv",
            line_number=0,
            record_id=navaid.id,
            airac_cycle=self.airac_cycle,
            raw_data=navaid.raw_data
        )

        # 解析坐标
        coordinate = None
        if navaid.latitude and navaid.longitude:
            try:
                coordinate = Coordinate.from_packed(navaid.latitude, navaid.longitude)
            except Exception as e:
                logger.warning(f"解析导航台坐标失败 {navaid.code}: {e}")

        # 确定导航台类型
        navaid_type = NavaidType.NDB  # 默认NDB
        if navaid.navaid_type:
            navaid_type_str = navaid.navaid_type.upper()
            if navaid_type_str in NavaidType.__members__:
                navaid_type = NavaidType[navaid_type_str]

        return NavModelNavaid(
            code=navaid.code,
            name=navaid.name,
            navaid_type=navaid_type,
            coordinate=coordinate,
            elevation=navaid.elevation,
            frequency=navaid.frequency,
            frequency_unit=navaid.frequency_unit,
            magnetic_variation=navaid.mag_var,
            fir_code=navaid.fir_code,
            remarks=navaid.remarks,
            source=source
        )

    def build_navmodel(
        self,
        airports: List[Airport],
        runways: List[Runway],
        navaids: List[Navaid]
    ) -> NavModel:
        """
        构建完整的NavModel

        Args:
            airports: 机场列表
            runways: 跑道列表
            navaids: 导航台列表

        Returns:
            NavModel实例
        """
        logger.info("开始构建NavModel...")

        # 转换数据
        nav_airports = self.convert_airports(airports)
        nav_runways = self.convert_runways(runways)
        nav_navaids = self.convert_navaids(navaids)

        # 关联跑道到机场
        airport_dict = {a.icao_code: a for a in nav_airports}
        for runway in nav_runways:
            if runway.airport_icao in airport_dict:
                airport_dict[runway.airport_icao].runways.append(runway)

        # 创建NavModel
        navmodel = NavModel(
            airac_cycle=self.airac_cycle,
            airports=nav_airports,
            runways=nav_runways,
            navaids=nav_navaids
        )

        logger.info(f"NavModel构建完成: {navmodel.statistics}")

        return navmodel
