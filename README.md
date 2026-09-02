# 424导航数据统一转换工具

## 简介

本工具从ARINC 424原始数据出发，转换到各种飞行模拟器导航数据格式的统一转换平台。

## 支持的目标格式

- **Default Navdata** - MSFS 2024通用导航数据格式
- **PMDG** - PMDG 737/777系列
- **FSLabs** - FSLabs A320系列
- **TFDI** - TFDI MD-11等
- **iFly** - iFly 737等
- **Fenix** - Fenix A320

## 系统要求

- Python 3.8+
- Windows 10/11（用于MSFS 2024部署）
- MSFS 2024 SDK（用于Default格式BGL编译）

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本使用

```bash
# 查看帮助
python main.py --help

# 转换为Default格式
python main.py convert --format default --input "F:\我的世界动画\AI项目\导航数据\424源数据\2608\2608"

# 转换为PMDG格式
python main.py convert --format pmdg --input "F:\我的世界动画\AI项目\导航数据\424源数据\2608\2608"

# 启动GUI界面
python gui.py
```

## 项目结构

```
navdata_424_converter/
├── CLAUDE.md              # 开发计划和规则
├── README.md              # 本文件
├── requirements.txt       # Python依赖
├── .gitignore            # Git忽略规则
├── main.py               # CLI入口
├── gui.py                # GUI入口（计划中）
├── src/                  # 源代码
│   ├── ingest/          # 424解析器
│   ├── model/           # 统一NavModel
│   ├── adapters/        # 格式适配器
│   ├── validators/      # 验证器
│   ├── deployers/       # 部署管理器
│   └── utils/           # 工具函数
├── tests/               # 单元测试
├── docs/                # 文档
└── config/              # 配置文件

```

## 开发状态

当前版本：**R001 - 项目初始化阶段**

详细开发计划请查看 [CLAUDE.md](CLAUDE.md)

## 数据来源

- 原始数据：`F:\我的世界动画\AI项目\导航数据\424源数据\2608\2608`
- 参考成品：`F:\我的世界动画\AI项目\导航数据\424源数据\2608\`

## 相关项目

- [fenix_to_default_navdata](../fenix_to_default_navdata) - Fenix到Default格式转换
- [fenix_to_pmdg](../fenix_to_pmdg) - Fenix到PMDG格式转换
- [fenix_to_fslabs](../fenix_to_fslabs) - Fenix到FSLabs格式转换
- [fenix_to_tfdi](../fenix_to_tfdi) - Fenix到TFDI格式转换

## 许可证

本项目仅供个人学习和研究使用。

## 贡献指南

1. 遵循CLAUDE.md中的开发规则
2. 每次改动后运行测试
3. 提交前确保代码通过lint检查
4. 编写清晰的commit message（中文）

## 联系方式

GitHub: https://github.com/JCH2333/navdata_424_converter

---

最后更新：2026-09-02
