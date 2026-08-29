# 数据资源说明

本目录存放「重型机械装配车间螺栓拧紧质量智能检测与工艺追溯系统」的全部数据资源，覆盖原始数据、预处理后特征数据集、业务基础数据三类，完整落地工业大数据预处理与特征工程技术。

## 一、数据来源

### 1.1 自建模拟数据集（本项目核心训练数据）

本项目针对 5 类拧紧质量状态（合格、欠拧、过拧、滑牙、虚拧）构建检测模型。由于公开领域**不存在同时标注这 5 类质量状态的单一数据集**，核心训练数据采用**自建模拟数据**：基于螺栓拧紧「力矩-转角」力学模型（空行程 → 贴合 → 弹性上升 → 保持/跌落 四阶段），结合重型机械装配工艺规范，通过 Python 脚本生成。

数据规模共 **3000 条**完整拧紧周期，采样频率 100 Hz：

| 子集 | 样本数 | 说明 |
|------|--------|------|
| `raw/benchmark/` | 1200 | 标准工况基准集（合格 700 + 缺陷 500） |
| `raw/extended/`  | 1800 | 扩展工况集（不同螺栓等级/工具磨损/环境温度，扩充稀有缺陷样本） |

质量标签编码：`0=合格 1=欠拧 2=过拧 3=滑牙 4=虚拧`。数据为小型数据集（约 5 MB），直接提交至本仓库 `/data` 目录。

### 1.2 公开数据集参考来源（有效链接）

以下公开数据集与本项目场景相关，作为方法论与数据组织参考，不直接作为本项目 5 类检测的训练数据：

- **pyscrew Screw Driving Dataset**（公开，含扭矩/角度/时间/类别通道及 OK/NOK 标签）：https://github.com/nikolaiwest/pyscrew
- **AURSAD**（Universal Robot Screwdriving Anomaly Detection Dataset，拧紧过程异常检测公开数据）：见 ScienceDirect 论文 [ML-Pipeline for the Quality Assessment of Screwdriving Processes](https://www.sciencedirect.com/science/article/pii/S221282712400934X)
- **国家基础学科公共科学数据中心——螺栓紧固实验测试数据**（力矩-转角关系模型）：https://nbsdc.cn/general/dataDetail?id=6988b31b195d2616afb01c17&type=1
- **M2/M3 螺钉力矩-角度曲线数据集**（关注滑牙/螺纹失效）：DOI: [10.3390/data9100115](https://doi.org/10.3390/data9100115)

## 二、目录结构

```
data/
├── generate_data.py          # 数据生成脚本（生成原始时序数据）
├── preprocess.py             # 预处理 + 特征工程 + 数据集划分脚本
├── raw/                      # 原始数据集
│   ├── benchmark/            # 标准工况基准集
│   │   ├── records.jsonl     #   时序数据（JSONL，每条一行）
│   │   └── metadata.csv      #   记录元数据与标签
│   └── extended/             # 扩展工况集
│       ├── records.jsonl
│       └── metadata.csv
├── processed/                # 预处理后的特征数据集
│   ├── train.csv             # 训练集（70%，标准化）
│   ├── val.csv               # 验证集（20%，标准化）
│   ├── test.csv              # 测试集（10%，标准化）
│   └── feature_metadata.json # 特征元信息（选择结果、标准化参数）
├── business/                 # 基础业务数据
│   └── init.sql              # MySQL 建库建表与基础数据导入脚本
└── README.md                 # 本文档
```

## 三、原始数据格式

`records.jsonl` 每行一条 JSON 记录，字段如下：

```json
{
  "id": "B0001",            // 记录ID（B=基准集，E=扩展集）
  "spec": "M12",            // 螺栓规格 M12/M16/M20/M24
  "grade": "8.8",           // 性能等级
  "wear": 0,                // 工具磨损 0新/1中度/2重度
  "temp": 20.0,             // 环境温度 ℃
  "target_torque": 80.0,    // 目标扭矩 N·m
  "speed": 181.51,          // 拧紧转速 deg/s
  "label": 0,               // 质量标签
  "label_name": "合格",
  "angle": [0.0, 1.8, ...], // 转角序列 deg
  "torque": [-0.6, 1.3, ...] // 力矩序列 N·m
}
```

`metadata.csv` 为上述元数据（不含时序数组）的汇总，便于快速检索与统计。

## 四、预处理与特征工程流程

对应课程「工业大数据预处理与特征工程」，由 `preprocess.py` 自动化执行：

1. **数据清洗**：去除拧紧过程前后的空行程段；基于一阶差分采用 3σ 准则识别并剔除跳变点，线性插值补全；连续缺失超过 5% 的序列弃用。
2. **特征提取**：从力矩-转角时序提取 12 维时域特征（力矩最大值/平均值/标准差、力矩峰值出现角度、贴合点扭矩、拧紧总转角、平均速率、上升斜率、力矩波动率、转角偏差量、最终扭矩、保持段波动率）。
3. **特征选择**：计算各特征与质量标签的 Pearson 相关系数，剔除相关系数低于 0.1 的弱相关特征；对相关系数高于 0.97 的共线性特征对进行合并（连通分量聚类，每组保留与标签相关性最强代表），最终保留 **8 维核心特征**。
4. **特征标准化**：对特征向量做 Z-score 标准化，标准化参数**仅基于训练集**统计量计算，验证集/测试集复用，避免数据泄露。
5. **数据集划分**：按 7:2:1 比例分层随机抽样（按质量标签分层），保证各类别占比均衡。

最终保留的 8 维特征：`torque_mean`、`torque_peak_angle`、`total_angle`、`avg_rate`、`rising_slope`、`angle_deviation`、`final_torque`、`hold_fluctuation`。完整相关系数与选择依据见 `processed/feature_metadata.json`。

## 五、数据复现与使用

```bash
# 1. 生成原始数据
python data/generate_data.py

# 2. 预处理 + 特征工程 + 划分
python data/preprocess.py

# 3. 初始化业务数据库（MySQL）
mysql -u root -p < data/business/init.sql
```

加载数据示例：

```python
import json, pandas as pd

# 原始时序数据
with open("data/raw/benchmark/records.jsonl", encoding="utf-8") as f:
    records = [json.loads(line) for line in f]

# 特征数据集
train = pd.read_csv("data/processed/train.csv")
```
