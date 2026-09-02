"""
ARINC 424数据解析器基类

负责读取和解析424格式的CSV文件
"""

import csv
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    """解析结果"""
    success: bool
    record_count: int
    errors: List[str]
    data: List[Dict[str, Any]]


class Arinc424Parser:
    """ARINC 424解析器基类"""

    def __init__(self, data_dir: Path):
        """
        初始化解析器

        Args:
            data_dir: 424数据目录路径
        """
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            raise FileNotFoundError(f"数据目录不存在: {self.data_dir}")

    def read_csv(self, filename: str, encoding: str = 'utf-8') -> ParseResult:
        """
        读取CSV文件

        Args:
            filename: CSV文件名
            encoding: 文件编码，默认utf-8，如果失败会尝试gbk

        Returns:
            ParseResult: 解析结果
        """
        filepath = self.data_dir / filename

        if not filepath.exists():
            return ParseResult(
                success=False,
                record_count=0,
                errors=[f"文件不存在: {filepath}"],
                data=[]
            )

        errors = []
        data = []

        # 尝试多种编码
        encodings = [encoding, 'utf-8', 'gbk', 'utf-8-sig']

        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc, newline='') as f:
                    reader = csv.DictReader(f)
                    data = []

                    for row_num, row in enumerate(reader, start=2):  # 从第2行开始（第1行是表头）
                        # 清理字段：去除首尾空格和末尾逗号
                        cleaned_row = {}
                        for key, value in row.items():
                            if key:  # 跳过空键
                                clean_key = key.strip()
                                clean_value = value.strip() if value else ''
                                cleaned_row[clean_key] = clean_value

                        data.append(cleaned_row)

                logger.info(f"成功读取 {filename}，使用编码 {enc}，共 {len(data)} 条记录")

                return ParseResult(
                    success=True,
                    record_count=len(data),
                    errors=[],
                    data=data
                )

            except UnicodeDecodeError:
                continue
            except Exception as e:
                errors.append(f"读取文件失败 ({enc}): {str(e)}")

        # 所有编码都失败
        return ParseResult(
            success=False,
            record_count=0,
            errors=errors,
            data=[]
        )

    def validate_required_fields(self, row: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """
        验证必填字段

        Args:
            row: 数据行
            required_fields: 必填字段列表

        Returns:
            错误列表
        """
        errors = []
        for field in required_fields:
            if field not in row or not row[field]:
                errors.append(f"缺少必填字段: {field}")
        return errors
