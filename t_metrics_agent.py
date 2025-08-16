from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.knowledge.csv import CSVKnowledgeBase
from typing import Dict, Any

def get_table_schema() -> Dict[str, Any]:
    """Return t_metrics table schema with single table constraint"""
    return {
        "table_name": "t_metrics",
        "description": "Time-series metrics data table - ONLY TABLE ALLOWED FOR QUERIES",
        "columns": {
            "event_ts": "uint64 - Event timestamp",
            "metric": "string - Metric name identifier", 
            "value": "string - Metric value (use to_float64() for numeric operations)",
            "metric_date": "int64 - Date component",
            "metric_time": "int64 - Time component", 
            "metric_datetime": "int64 - Combined datetime",
            "tagK1": "low_cardinality(string) - Tag key 1",
            "tagV1": "string - Tag value 1",
            "tagK2": "low_cardinality(string) - Tag key 2",
            "tagV2": "string - Tag value 2", 
            "tagK3": "low_cardinality(string) - Tag key 3",
            "tagV3": "string - Tag value 3",
            "tagK4": "low_cardinality(string) - Tag key 4", 
            "tagV4": "string - Tag value 4",
            "tagK5": "low_cardinality(string) - Tag key 5",
            "tagV5": "string - Tag value 5",
            "_tp_time": "datetime64(3, 'UTC') - System timestamp"
        },
        "constraints": [
            "SINGLE TABLE ONLY - No JOINs allowed",
            "No subqueries with other tables",
            "Must search CSV knowledge base first to find relevant metrics"
        ]
    }

# Load t_metrics SQL prompt
with open('promptnew.txt', 'r', encoding='utf-8') as f:
    T_METRICS_PROMPT = f.read()

# Enhanced prompt with CSV search workflow
ENHANCED_PROMPT = f"""
{T_METRICS_PROMPT}

## MANDATORY WORKFLOW (必须遵循的工作流程)

### Step 1: Search Metric Dictionary
- **必须先搜索 CSV 知识库** 根据用户问题搜索相关指标
- 从 metric.csv 获取精确的 metric 名称和标签信息
- 识别可用的 tagK/tagV 组合

### Step 2: Get Table Schema  
- **调用 get_table_schema()** 确认表结构和约束
- 验证只查询 t_metrics 单表

### Step 3: Generate SQL
- 使用搜索到的精确 metric 名称
- 应用相关的标签过滤条件
- 生成符合 Timeplus 语法的 SQL

### CRITICAL CONSTRAINTS
- **单表约束**: 只允许查询 t_metrics 表
- **禁止 JOIN**: 不允许与任何其他表连接  
- **强制工具调用**: 必须先搜索CSV获取指标信息再生成 SQL
"""

# Create CSV Knowledge Base
metric_knowledge = CSVKnowledgeBase(
    path="metric.csv",
    formats=["txt", "csv", "json"]
)

# T-Metrics SQL Agent with CSV Knowledge and Table Schema
t_metrics_sql_agent = Agent(
    model=Claude(id="claude-sonnet-4-20250514"),
    tools=[get_table_schema],
    knowledge=[metric_knowledge], 
    instructions=ENHANCED_PROMPT,
    markdown=True,
    name="T-Metrics SQL Generator",
    description="Specialized agent for converting natural language to Timeplus SQL queries for t_metrics table"
)

def generate_sql(query: str) -> str:
    """
    Generate SQL for t_metrics table from natural language query
    
    Args:
        query: Natural language question about metrics data
        
    Returns:
        Generated SQL query string
    """
    response = t_metrics_sql_agent.run(query)
    return response.content

if __name__ == "__main__":
    # Example usage
    test_queries = [
        "查询深圳的tick行情延时",
        "显示所有交易中心的策略成交额",
        "统计高频Alpha团队的CPU使用情况",
        "近一小时的订单废单数量"
    ]
    
    print("=== T-Metrics SQL Generator 测试 ===\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"测试 {i}: {query}")
        try:
            sql = generate_sql(query)
            print(f"生成SQL:\n{sql}\n")
        except Exception as e:
            print(f"错误: {e}\n")
        print("-" * 50)