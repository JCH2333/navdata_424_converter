"""基础测试 - 验证项目结构"""

import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_imports():
    """测试所有模块可以正常导入"""
    import src
    from src import ingest, model, adapters, validators, deployers, utils

    assert src.__version__ == "0.1.0-R001"
    assert src.__airac__ == "2608"


def test_project_structure():
    """测试项目目录结构完整性"""
    project_root = Path(__file__).parent.parent

    assert (project_root / "CLAUDE.md").exists()
    assert (project_root / "README.md").exists()
    assert (project_root / ".gitignore").exists()
    assert (project_root / "requirements.txt").exists()
    assert (project_root / "main.py").exists()

    assert (project_root / "src").is_dir()
    assert (project_root / "tests").is_dir()
    assert (project_root / "docs").is_dir()
    assert (project_root / "config").is_dir()

    assert (project_root / "src" / "ingest").is_dir()
    assert (project_root / "src" / "model").is_dir()
    assert (project_root / "src" / "adapters").is_dir()
    assert (project_root / "src" / "validators").is_dir()
    assert (project_root / "src" / "deployers").is_dir()
    assert (project_root / "src" / "utils").is_dir()


if __name__ == "__main__":
    test_imports()
    test_project_structure()
    print("[PASS] 所有测试通过")
