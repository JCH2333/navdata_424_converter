"""
NavModel验证器

验证NavModel的数据完整性和一致性
"""

from typing import List, Dict, Set
from dataclasses import dataclass
import logging

from .navmodel import NavModel, NavModelAirport, NavModelRunway

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """验证问题"""
    severity: str  # ERROR/WARNING/INFO
    category: str  # 问题类别
    message: str  # 问题描述
    entity_type: str  # 实体类型
    entity_id: str  # 实体标识


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool  # 是否通过验证
    issues: List[ValidationIssue]  # 问题列表

    @property
    def error_count(self) -> int:
        """错误数量"""
        return len([i for i in self.issues if i.severity == 'ERROR'])

    @property
    def warning_count(self) -> int:
        """警告数量"""
        return len([i for i in self.issues if i.severity == 'WARNING'])

    def print_summary(self):
        """打印验证摘要"""
        print(f"\n{'='*60}")
        print(f"NavModel验证结果")
        print(f"{'='*60}")
        print(f"状态: {'[PASS]' if self.is_valid else '[FAIL]'}")
        print(f"错误: {self.error_count}")
        print(f"警告: {self.warning_count}")
        print(f"总问题数: {len(self.issues)}")

        if self.issues:
            print(f"\n问题详情:")
            for i, issue in enumerate(self.issues[:10], 1):  # 只显示前10个
                print(f"  {i}. [{issue.severity}] {issue.category}: {issue.message}")

            if len(self.issues) > 10:
                print(f"  ... 还有 {len(self.issues) - 10} 个问题")

        print(f"{'='*60}\n")


class NavModelValidator:
    """NavModel验证器"""

    def __init__(self):
        self.issues: List[ValidationIssue] = []

    def validate(self, navmodel: NavModel) -> ValidationResult:
        """
        验证NavModel

        Args:
            navmodel: NavModel实例

        Returns:
            ValidationResult
        """
        self.issues = []

        logger.info("开始验证NavModel...")

        # 基本统计验证
        self._validate_statistics(navmodel)

        # 机场验证
        self._validate_airports(navmodel)

        # 跑道验证
        self._validate_runways(navmodel)

        # 导航台验证
        self._validate_navaids(navmodel)

        # 关联验证
        self._validate_associations(navmodel)

        # 判断是否通过（没有ERROR级别的问题）
        is_valid = self.error_count == 0

        result = ValidationResult(is_valid=is_valid, issues=self.issues)

        logger.info(f"验证完成: {'通过' if is_valid else '失败'}, "
                   f"错误={result.error_count}, 警告={result.warning_count}")

        return result

    @property
    def error_count(self) -> int:
        """错误数量"""
        return len([i for i in self.issues if i.severity == 'ERROR'])

    def _add_issue(self, severity: str, category: str, message: str,
                   entity_type: str = '', entity_id: str = ''):
        """添加验证问题"""
        issue = ValidationIssue(
            severity=severity,
            category=category,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id
        )
        self.issues.append(issue)

    def _validate_statistics(self, navmodel: NavModel):
        """验证基本统计信息"""
        stats = navmodel.statistics

        if stats['airports'] == 0:
            self._add_issue('ERROR', 'empty_data', '没有机场数据')

        if stats['runways'] == 0:
            self._add_issue('WARNING', 'empty_data', '没有跑道数据')

        if stats['navaids'] == 0:
            self._add_issue('WARNING', 'empty_data', '没有导航台数据')

    def _validate_airports(self, navmodel: NavModel):
        """验证机场数据"""
        icao_codes: Set[str] = set()

        for airport in navmodel.airports:
            # 检查ICAO代码重复
            if airport.icao_code in icao_codes:
                self._add_issue('ERROR', 'duplicate', f'重复的ICAO代码',
                              'airport', airport.icao_code)
            icao_codes.add(airport.icao_code)

            # 检查必填字段
            if not airport.icao_code:
                self._add_issue('ERROR', 'missing_field', 'ICAO代码缺失',
                              'airport', airport.name or '未知')

            if not airport.name:
                self._add_issue('WARNING', 'missing_field', '机场名称缺失',
                              'airport', airport.icao_code)

            # 检查坐标
            if airport.coordinate:
                self._validate_coordinate(airport.coordinate, 'airport', airport.icao_code)

            # 检查海拔
            if airport.elevation is not None and (airport.elevation < -500 or airport.elevation > 6000):
                self._add_issue('WARNING', 'out_of_range',
                              f'海拔值异常: {airport.elevation}m',
                              'airport', airport.icao_code)

    def _validate_runways(self, navmodel: NavModel):
        """验证跑道数据"""
        for runway in navmodel.runways:
            # 检查必填字段
            if not runway.designation:
                self._add_issue('ERROR', 'missing_field', '跑道标识缺失',
                              'runway', runway.airport_icao)

            if not runway.airport_icao:
                self._add_issue('ERROR', 'missing_field', '机场ICAO代码缺失',
                              'runway', runway.designation)

            # 检查尺寸合理性
            if runway.length is not None and (runway.length < 300 or runway.length > 6000):
                self._add_issue('WARNING', 'out_of_range',
                              f'跑道长度异常: {runway.length}m',
                              'runway', f'{runway.airport_icao} {runway.designation}')

            if runway.width is not None and (runway.width < 10 or runway.width > 100):
                self._add_issue('WARNING', 'out_of_range',
                              f'跑道宽度异常: {runway.width}m',
                              'runway', f'{runway.airport_icao} {runway.designation}')

    def _validate_navaids(self, navmodel: NavModel):
        """验证导航台数据"""
        codes: Set[str] = set()

        for navaid in navmodel.navaids:
            # 检查代码重复（同类型）
            key = f"{navaid.navaid_type.value}:{navaid.code}"
            if key in codes:
                self._add_issue('WARNING', 'duplicate',
                              f'重复的导航台代码',
                              'navaid', navaid.code)
            codes.add(key)

            # 检查必填字段
            if not navaid.code:
                self._add_issue('ERROR', 'missing_field', '导航台代码缺失',
                              'navaid', navaid.name or '未知')

            # 检查坐标
            if navaid.coordinate:
                self._validate_coordinate(navaid.coordinate, 'navaid', navaid.code)

            # 检查频率
            if navaid.frequency is not None:
                if navaid.frequency_unit == 'kHz' and (navaid.frequency < 100 or navaid.frequency > 1500):
                    self._add_issue('WARNING', 'out_of_range',
                                  f'NDB频率异常: {navaid.frequency} kHz',
                                  'navaid', navaid.code)
                elif navaid.frequency_unit == 'MHz' and (navaid.frequency < 100 or navaid.frequency > 120):
                    self._add_issue('WARNING', 'out_of_range',
                                  f'VOR频率异常: {navaid.frequency} MHz',
                                  'navaid', navaid.code)

    def _validate_coordinate(self, coordinate, entity_type: str, entity_id: str):
        """验证坐标"""
        # 检查纬度范围
        if coordinate.latitude < -90 or coordinate.latitude > 90:
            self._add_issue('ERROR', 'out_of_range',
                          f'纬度超出范围: {coordinate.latitude}',
                          entity_type, entity_id)

        # 检查经度范围
        if coordinate.longitude < -180 or coordinate.longitude > 180:
            self._add_issue('ERROR', 'out_of_range',
                          f'经度超出范围: {coordinate.longitude}',
                          entity_type, entity_id)

    def _validate_associations(self, navmodel: NavModel):
        """验证关联关系"""
        # 构建机场ICAO索引
        airport_icaos = {a.icao_code for a in navmodel.airports}

        # 检查跑道的机场引用
        for runway in navmodel.runways:
            if runway.airport_icao not in airport_icaos:
                self._add_issue('ERROR', 'broken_reference',
                              f'跑道引用的机场不存在: {runway.airport_icao}',
                              'runway', runway.designation)

        # 检查跑道关联
        for airport in navmodel.airports:
            runway_count = len([r for r in navmodel.runways if r.airport_icao == airport.icao_code])
            if runway_count == 0:
                self._add_issue('INFO', 'missing_association',
                              f'机场没有跑道数据',
                              'airport', airport.icao_code)
            elif runway_count != len(airport.runways):
                self._add_issue('WARNING', 'inconsistent_association',
                              f'机场跑道列表不一致: 预期{runway_count}, 实际{len(airport.runways)}',
                              'airport', airport.icao_code)
