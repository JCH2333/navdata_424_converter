"""
NavModel序列化器

支持JSON格式的序列化和反序列化
"""

import json
import gzip
from pathlib import Path
from typing import Union
from datetime import datetime
import logging

from .navmodel import (
    NavModel, NavModelAirport, NavModelRunway, NavModelNavaid,
    NavModelWaypoint, NavModelAirway, Coordinate, SourceInfo,
    CoordinateFormat, NavaidType, WaypointType
)

logger = logging.getLogger(__name__)


class NavModelSerializer:
    """NavModel序列化器"""

    @staticmethod
    def to_dict(navmodel: NavModel) -> dict:
        """
        将NavModel转换为字典

        Args:
            navmodel: NavModel实例

        Returns:
            字典表示
        """
        return {
            'airac_cycle': navmodel.airac_cycle,
            'effective_date': navmodel.effective_date.isoformat() if navmodel.effective_date else None,
            'statistics': navmodel.statistics,
            'airports': [NavModelSerializer._airport_to_dict(a) for a in navmodel.airports],
            'runways': [NavModelSerializer._runway_to_dict(r) for r in navmodel.runways],
            'navaids': [NavModelSerializer._navaid_to_dict(n) for n in navmodel.navaids],
            'waypoints': [NavModelSerializer._waypoint_to_dict(w) for w in navmodel.waypoints],
            'airways': [NavModelSerializer._airway_to_dict(a) for a in navmodel.airways],
        }

    @staticmethod
    def _coordinate_to_dict(coord: Coordinate) -> dict:
        """坐标转字典"""
        return {
            'latitude': coord.latitude,
            'longitude': coord.longitude,
            'format': coord.format.value,
            'raw_latitude': coord.raw_latitude,
            'raw_longitude': coord.raw_longitude,
        }

    @staticmethod
    def _source_to_dict(source: SourceInfo) -> dict:
        """来源信息转字典"""
        return {
            'file_name': source.file_name,
            'line_number': source.line_number,
            'record_id': source.record_id,
            'airac_cycle': source.airac_cycle,
            # raw_data 不序列化（太大）
        }

    @staticmethod
    def _airport_to_dict(airport: NavModelAirport) -> dict:
        """机场转字典"""
        return {
            'icao_code': airport.icao_code,
            'name': airport.name,
            'iata_code': airport.iata_code,
            'coordinate': NavModelSerializer._coordinate_to_dict(airport.coordinate) if airport.coordinate else None,
            'elevation': airport.elevation,
            'magnetic_variation': airport.magnetic_variation,
            'transition_altitude': airport.transition_altitude,
            'transition_level': airport.transition_level,
            'is_international': airport.is_international,
            'is_military': airport.is_military,
            'fir_code': airport.fir_code,
            'remarks': airport.remarks,
            'source': NavModelSerializer._source_to_dict(airport.source) if airport.source else None,
            'runway_count': len(airport.runways),
        }

    @staticmethod
    def _runway_to_dict(runway: NavModelRunway) -> dict:
        """跑道转字典"""
        return {
            'designation': runway.designation,
            'airport_icao': runway.airport_icao,
            'length': runway.length,
            'width': runway.width,
            'surface_type': runway.surface_type,
            'strength_code': runway.strength_code,
            'remarks': runway.remarks,
            'source': NavModelSerializer._source_to_dict(runway.source) if runway.source else None,
        }

    @staticmethod
    def _navaid_to_dict(navaid: NavModelNavaid) -> dict:
        """导航台转字典"""
        return {
            'code': navaid.code,
            'name': navaid.name,
            'navaid_type': navaid.navaid_type.value,
            'coordinate': NavModelSerializer._coordinate_to_dict(navaid.coordinate) if navaid.coordinate else None,
            'elevation': navaid.elevation,
            'frequency': navaid.frequency,
            'frequency_unit': navaid.frequency_unit,
            'magnetic_variation': navaid.magnetic_variation,
            'fir_code': navaid.fir_code,
            'remarks': navaid.remarks,
            'source': NavModelSerializer._source_to_dict(navaid.source) if navaid.source else None,
        }

    @staticmethod
    def _waypoint_to_dict(waypoint: NavModelWaypoint) -> dict:
        """航路点转字典"""
        return {
            'code': waypoint.code,
            'name': waypoint.name,
            'waypoint_type': waypoint.waypoint_type.value,
            'coordinate': NavModelSerializer._coordinate_to_dict(waypoint.coordinate) if waypoint.coordinate else None,
            'fir_code': waypoint.fir_code,
            'region_code': waypoint.region_code,
            'is_terminal': waypoint.is_terminal,
            'is_enroute': waypoint.is_enroute,
            'is_border': waypoint.is_border,
            'remarks': waypoint.remarks,
            'source': NavModelSerializer._source_to_dict(waypoint.source) if waypoint.source else None,
        }

    @staticmethod
    def _airway_to_dict(airway: NavModelAirway) -> dict:
        """航路转字典"""
        return {
            'name': airway.name,
            'airway_type': airway.airway_type,
            'from_waypoint': airway.from_waypoint,
            'to_waypoint': airway.to_waypoint,
            'minimum_altitude': airway.minimum_altitude,
            'maximum_altitude': airway.maximum_altitude,
            'direction': airway.direction,
            'distance': airway.distance,
            'remarks': airway.remarks,
            'source': NavModelSerializer._source_to_dict(airway.source) if airway.source else None,
        }

    @staticmethod
    def save_json(navmodel: NavModel, filepath: Union[str, Path], compress: bool = False):
        """
        保存为JSON文件

        Args:
            navmodel: NavModel实例
            filepath: 文件路径
            compress: 是否使用gzip压缩
        """
        filepath = Path(filepath)
        data = NavModelSerializer.to_dict(navmodel)

        if compress:
            # 保存为.json.gz
            if not str(filepath).endswith('.gz'):
                filepath = Path(str(filepath) + '.gz')

            with gzip.open(filepath, 'wt', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"NavModel已保存到压缩文件: {filepath}")
        else:
            # 保存为.json
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"NavModel已保存到文件: {filepath}")

    @staticmethod
    def save_summary(navmodel: NavModel, filepath: Union[str, Path]):
        """
        保存摘要信息（不包含详细数据）

        Args:
            navmodel: NavModel实例
            filepath: 文件路径
        """
        filepath = Path(filepath)

        summary = {
            'airac_cycle': navmodel.airac_cycle,
            'generated_at': datetime.now().isoformat(),
            'statistics': navmodel.statistics,
            'airports': {
                'total': len(navmodel.airports),
                'international': sum(1 for a in navmodel.airports if a.is_international),
                'military': sum(1 for a in navmodel.airports if a.is_military),
                'with_runways': sum(1 for a in navmodel.airports if len(a.runways) > 0),
            },
            'runways': {
                'total': len(navmodel.runways),
                'avg_length': sum(r.length for r in navmodel.runways if r.length) / len([r for r in navmodel.runways if r.length]) if navmodel.runways else 0,
            },
            'navaids': {
                'total': len(navmodel.navaids),
                'by_type': {},
            },
        }

        # 统计导航台类型
        for navaid in navmodel.navaids:
            navaid_type = navaid.navaid_type.value
            summary['navaids']['by_type'][navaid_type] = summary['navaids']['by_type'].get(navaid_type, 0) + 1

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        logger.info(f"NavModel摘要已保存到: {filepath}")
