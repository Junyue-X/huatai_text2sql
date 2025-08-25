# T-Metrics SQL Generator / T-Metrics SQL 生成器

### Overview
A specialized SQL generation agent that converts natural language queries into Timeplus SQL queries for the `t_metrics` table. The agent uses CSV knowledge base lookup and enforces single-table constraints for metrics analysis.

### Features
- **Natural Language to SQL**: Convert questions about metrics data into valid Timeplus SQL queries
- **CSV Knowledge Integration**: Automatically searches metric dictionary for accurate metric names and tags
- **Single Table Constraint**: Ensures queries only target the `t_metrics` table (no JOINs allowed)
- **Bilingual Support**: Handles queries in both English and Chinese

### File Structure
```
t_metric2sql/
├── t_metrics_agent_v2.py      # 主要代理实现 (ReAct + 验证)
├── t_metrics_agent.py         # 简化版代理实现
├── analyzer.py                # SQL验证客户端
├── timeplus_schema_reader.py  # 动态Schema读取模块
├── metric.csv                 # 指标字典数据
├── prompt.txt                 # SQL生成提示模板
├── agent_config.json          # 代理配置文件
├── agent_config_example.json  # 配置文件示例
├── requirements.txt           # 依赖包列表
└── README.md                  # 说明文档
```

### Quick Start
1. Install dependencies:
   ```bash
   pip install agno
   ```

2. Run the agent:
   ```python
   # 推荐使用V2版本（带验证功能）
   python t_metrics_agent_v2.py
   
   # 或者使用简化版本
   python t_metrics_agent.py
   ```

### Usage Example
```python
# V2版本（推荐）
from t_metrics_agent_v2 import generate_sql_v2

query = "Show tick market data latency for Shenzhen"
sql = generate_sql_v2(query)
print(sql)

# 简化版本
from t_metrics_agent import generate_sql
sql = generate_sql(query)
print(sql)
```

### Sample Queries
- "查询深圳的tick行情延时" (Query tick market latency for Shenzhen)
- "显示所有交易中心的策略成交额" (Show strategy trading volume for all centers)
- "统计高频Alpha团队的CPU使用情况" (Statistics of CPU usage for HF Alpha team)

---

### 项目概述
专门用于将自然语言查询转换为 Timeplus SQL 查询的智能代理，专注于 `t_metrics` 表的指标分析。代理使用 CSV 知识库查找并强制执行单表约束。

### 主要功能
- **自然语言转 SQL**: 将关于指标数据的问题转换为有效的 Timeplus SQL 查询
- **CSV 知识库集成**: 自动搜索指标字典以获取准确的指标名称和标签
- **单表约束**: 确保查询只针对 `t_metrics` 表（不允许 JOIN 操作）
- **双语支持**: 支持中英文查询

### 文件结构
```
t_metric2sql/
├── t_metrics_agent_v2.py      # 主要代理实现 (ReAct + 验证)
├── t_metrics_agent.py         # 简化版代理实现
├── analyzer.py                # SQL验证客户端
├── timeplus_schema_reader.py  # 动态Schema读取模块
├── metric.csv                 # 指标字典数据
├── prompt.txt                 # SQL生成提示模板
├── agent_config.json          # 代理配置文件
├── agent_config_example.json  # 配置文件示例
├── requirements.txt           # 依赖包列表
└── README.md                  # 说明文档
```

### 快速开始
1. 安装依赖：
   ```bash
   pip install agno
   ```

2. 运行代理：
   ```python
   # 推荐使用V2版本（带验证功能）
   python t_metrics_agent_v2.py
   
   # 或者使用简化版本
   python t_metrics_agent.py
   ```

### 使用示例
```python
# V2版本（推荐）
from t_metrics_agent_v2 import generate_sql_v2

query = "查询深圳的tick行情延时"
sql = generate_sql_v2(query)
print(sql)

# 简化版本
from t_metrics_agent import generate_sql
sql = generate_sql(query)
print(sql)
```

### 示例查询
- "查询深圳的tick行情延时"
- "显示所有交易中心的策略成交额" 
- "统计高频Alpha团队的CPU使用情况"
- "近一小时的订单废单数量"

### 工作流程
1. **搜索指标字典**: 在 CSV 知识库中搜索相关指标
2. **获取表结构**: 确认 t_metrics 表结构和约束
3. **生成 SQL**: 使用精确的指标名称和标签生成符合 Timeplus 语法的 SQL