"""
统一NavModel中间数据模型

跨AIRAC、跨格式的标准化数据结构
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class CoordinateFormat(Enum):
    """坐标格式"""
    DMS = "degrees_minutes_seconds"  # 度分秒 (N39°30'00")
    PACKED = "packed"  # 紧凑格式 (N394530)
    DECIMAL = "decimal"  # 十进制度数 (39.75)


class NavaidType(Enum):
    """导航台类型"""
    NDB = "NDB"
    VOR = "VOR"
    DME = "DME"
    VORDME = "VOR-DME"
    TACAN = "TACAN"
    VORTAC = "VORTAC"


class WaypointType(Enum):
    """航路点类型"""
    NAMED = "NAMED"  # 命名航路点
    UNNAMED = "UNNAMED"  # 无名航路点
    TERMINAL = "TERMINAL"  # 终端点
    RUNWAY = "RUNWAY"  # 跑道点


class ProcedureType(Enum):
    """程序类型"""
    SID = "SID"  # 标准离场程序
    STAR = "STAR"  # 标准进场程序
    APPROACH = "APPROACH"  # 进近程序
    MISSED = "MISSED"  # 复飞程序


@dataclass
class SourceInfo:
    """数据来源信息"""
    file_name: str  # CSV文件名
    line_number: int  # 行号
    record_id: str  # 记录ID
    airac_cycle: str = "2608"  # AIRAC周期
    raw_data: Dict[str, Any] = field(default_factory=dict)  # 原始424数据


@dataclass
class Coordinate:
    """坐标"""
    latitude: float  # 十进制度数（北纬为正）
    longitude: float  # 十进制度数（东经为正）
    format: CoordinateFormat = CoordinateFormat.DECIMAL  # 坐标格式
    raw_latitude: Optional[str] = None  # 原始纬度字符串
    raw_longitude: Optional[str] = None  # 原始经度字符串

    @staticmethod
    def from_packed(lat_str: str, lon_str: str) -> 'Coordinate':
        """
        从紧凑格式解析坐标

        格式示例:
        - N291522 = 北纬29度15分22秒
        - E0914551 = 东经91度45分51秒
        """
        def parse_packed(s: str) -> float:
            # 去除方向字母
            direction = s[0]
            coords = s[1:]

            # 根据长度判断格式
            if len(coords) == 6:  # DDMMSS
                degrees = int(coords[0:2])
                minutes = int(coords[2:4])
                seconds = int(coords[4:6])
            elif len(coords) == 7:  # DDDMMSS (经度)
                degrees = int(coords[0:3])
                minutes = int(coords[3:5])
                seconds = int(coords[5:7])
            else:
                raise ValueError(f"无法解析坐标格式: {s}")

            # 转换为十进制度数
            decimal = degrees + minutes / 60.0 + seconds / 3600.0

            # 应用方向
            if direction in ['S', 'W']:
                decimal = -decimal

            return decimal

        lat = parse_packed(lat_str)
        lon = parse_packed(lon_str)

        return Coordinate(
            latitude=lat,
            longitude=lon,
            format=CoordinateFormat.PACKED,
            raw_latitude=lat_str,
            raw_longitude=lon_str
        )

    def to_dms(self) -> tuple[str, str]:
        """转换为度分秒格式"""
        def to_dms_str(decimal: float, is_latitude: bool) -> str:
            is_positive = decimal >= 0
            decimal = abs(decimal)

            degrees = int(decimal)
            minutes_decimal = (decimal - degrees) * 60
            minutes = int(minutes_decimal)
            seconds = (minutes_decimal - minutes) * 60

            if is_latitude:
                direction = 'N' if is_positive else 'S'
            else:
                direction = 'E' if is_positive else 'W'

            return f"{direction}{degrees:02d}°{minutes:02d}'{seconds:05.2f}\""

        lat_dms = to_dms_str(self.latitude, True)
        lon_dms = to_dms_str(self.longitude, False)

        return lat_dms, lon_dms


@dataclass
class NavModelAirport:
    """机场模型"""
    # 基本标识
    icao_code: str  # ICAO代码 (如ZBAA)
    name: str  # 机场名称
    iata_code: Optional[str] = None  # IATA代码

    # 地理位置
    coordinate: Optional[Coordinate] = None  # 坐标
    elevation: Optional[float] = None  # 海拔高度（米）
    magnetic_variation: Optional[float] = None  # 磁差（度）

    # 过渡高度
    transition_altitude: Optional[int] = None  # 过渡高度（英尺）
    transition_level: Optional[int] = None  # 过渡高度层

    # 分类
    is_international: bool = False  # 是否国际机场
    is_military: bool = False  # 是否军用机场

    # FIR信息
    fir_code: Optional[str] = None  # 飞行情报区代码

    # 备注
    remarks: Optional[str] = None

    # 来源信息
    source: Optional[SourceInfo] = None

    # 关联数据
    runways: List['NavModelRunway'] = field(default_factory=list)  # 跑道列表


@dataclass
class NavModelRunway:
    """跑道模型"""
    # 基本信息
    designation: str  # 跑道标识 (如"01L/19R")
    airport_icao: str  # 所属机场ICAO代码

    # 尺寸
    length: Optional[float] = None  # 长度（米）
    width: Optional[float] = None  # 宽度（米）

    # 道面信息
    surface_type: Optional[str] = None  # 道面类型
    strength_code: Optional[str] = None  # 强度代码 (PCR/PCN)

    # 备注
    remarks: Optional[str] = None

    # 来源信息
    source: Optional[SourceInfo] = None

    def get_runway_ends(self) -> tuple[str, str]:
        """获取跑道两端标识"""
        if '/' in self.designation:
            parts = self.designation.split('/')
            return parts[0].strip(), parts[1].strip()
        return self.designation.strip(), ""


@dataclass
class NavModelNavaid:
    """导航台模型"""
    # 基本标识
    code: str  # 导航台标识符
    name: Optional[str] = None  # 名称
    navaid_type: NavaidType = NavaidType.NDB  # 导航台类型

    # 地理位置
    coordinate: Optional[Coordinate] = None  # 坐标
    elevation: Optional[float] = None  # 海拔高度（米）

    # 频率
    frequency: Optional[float] = None  # 频率
    frequency_unit: Optional[str] = None  # 频率单位 (kHz/MHz)

    # 磁差
    magnetic_variation: Optional[float] = None  # 磁差（度）

    # FIR信息
    fir_code: Optional[str] = None  # 飞行情报区代码

    # 备注
    remarks: Optional[str] = None

    # 来源信息
    source: Optional[SourceInfo] = None


@dataclass
class NavModelWaypoint:
    """航路点模型"""
    # 基本标识
    code: str  # 航路点标识符
    name: Optional[str] = None  # 名称
    waypoint_type: WaypointType = WaypointType.NAMED  # 航路点类型

    # 地理位置
    coordinate: Optional[Coordinate] = None  # 坐标

    # 区域信息
    fir_code: Optional[str] = None  # 飞行情报区代码
    region_code: Optional[str] = None  # 区域代码

    # 用途
    is_terminal: bool = False  # 是否终端点
    is_enroute: bool = False  # 是否航路点
    is_border: bool = False  # 是否边界点

    # 备注
    remarks: Optional[str] = None

    # 来源信息
    source: Optional[SourceInfo] = None


@dataclass
class NavModelAirway:
    """航路模型"""
    # 基本标识
    name: str  # 航路名称 (如"H14")

    # 航路段
    from_waypoint: str  # 起点航路点
    to_waypoint: str  # 终点航路点

    # 类型
    airway_type: Optional[str] = None  # 航路类型 (J/V/B等)

    # 限制
    minimum_altitude: Optional[int] = None  # 最低高度（英尺）
    maximum_altitude: Optional[int] = None  # 最高高度（英尺）

    # 方向限制
    direction: Optional[str] = None  # 方向 (F=前向, B=后向)

    # 距离
    distance: Optional[float] = None  # 距离（海里）

    # 备注
    remarks: Optional[str] = None

    # 来源信息
    source: Optional[SourceInfo] = None


@dataclass
class NavModel:
    """统一导航数据模型"""
    # AIRAC信息
    airac_cycle: str = "2608"
    effective_date: Optional[datetime] = None

    # 核心数据
    airports: List[NavModelAirport] = field(default_factory=list)
    runways: List[NavModelRunway] = field(default_factory=list)
    navaids: List[NavModelNavaid] = field(default_factory=list)
    waypoints: List[NavModelWaypoint] = field(default_factory=list)
    airways: List[NavModelAirway] = field(default_factory=list)

    # 统计信息
    @property
    def statistics(self) -> Dict[str, int]:
        """获取统计信息"""
        return {
            'airports': len(self.airports),
            'runways': len(self.runways),
            'navaids': len(self.navaids),
            'waypoints': len(self.waypoints),
            'airways': len(self.airways),
        }

    def get_airport_by_icao(self, icao: str) -> Optional[NavModelAirport]:
        """根据ICAO代码查找机场"""
        for airport in self.airports:
            if airport.icao_code == icao:
                return airport
        return None

    def get_runways_by_airport(self, icao: str) -> List[NavModelRunway]:
        """获取指定机场的所有跑道"""
        return [r for r in self.runways if r.airport_icao == icao]
