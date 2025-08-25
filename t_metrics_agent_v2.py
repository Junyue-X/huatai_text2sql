"""
T-Metrics SQL Agent V2 - 集成ReAct模式的动态Schema读取
支持从Timeplus API动态获取表结构
"""

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.models.openai import OpenAI
from agno.models.groq import Groq
from agno.knowledge.csv import CSVKnowledgeBase
from typing import Dict, Any, Optional, Union
import os
import json
from dataclasses import dataclass

# 检查Proton驱动可用性
try:
    from proton_driver import client
    PROTON_AVAILABLE = True
except ImportError:
    PROTON_AVAILABLE = False

# 导入SQL分析器
from analyzer import Client as AnalyzerClient

# ============================================================================
# 配置系统
# ============================================================================

@dataclass
class ModelConfig:
    """模型配置类"""
    provider: str  # anthropic, openai, groq
    model_id: str
    api_key: Optional[str] = None
    api_url: Optional[str] = None
    temperature: float = 0.1
    max_tokens: Optional[int] = None

@dataclass
class TimeplusConfig:
    """Timeplus连接配置类"""
    host: str = "localhost"
    port: int = 8463
    user: str = "default"
    password: str = ""
    database: str = "default"
    table: str = "t_metrics"

class AgentConfigManager:
    """Agent配置管理器"""
    
    def __init__(self, config_file: str = "agent_config.json"):
        self.config_file = config_file
        self.model_config = self._load_model_config()
        self.timeplus_config = self._load_timeplus_config()
    
    def _load_model_config(self) -> ModelConfig:
        """加载模型配置"""
        # 优先从文件读取
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    model_data = config_data.get('model', {})
                    return ModelConfig(
                        provider=model_data.get('provider', 'anthropic'),
                        model_id=model_data.get('model_id', 'claude-sonnet-4-20250514'),
                        api_key=model_data.get('api_key'),
                        api_url=model_data.get('api_url'),
                        temperature=model_data.get('temperature', 0.1),
                        max_tokens=model_data.get('max_tokens')
                    )
            except Exception as e:
                print(f"配置文件读取失败: {e}，使用默认配置")
        
        # 从环境变量读取
        return ModelConfig(
            provider=os.getenv("AGENT_MODEL_PROVIDER", "anthropic"),
            model_id=os.getenv("AGENT_MODEL_ID", "claude-sonnet-4-20250514"),
            api_key=os.getenv("AGENT_API_KEY"),
            api_url=os.getenv("AGENT_API_URL"),
            temperature=float(os.getenv("AGENT_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("AGENT_MAX_TOKENS")) if os.getenv("AGENT_MAX_TOKENS") else None
        )
    
    def _load_timeplus_config(self) -> TimeplusConfig:
        """加载Timeplus配置"""
        # 优先从文件读取
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    timeplus_data = config_data.get('timeplus', {})
                    return TimeplusConfig(
                        host=timeplus_data.get('host', 'localhost'),
                        port=timeplus_data.get('port', 8463),
                        user=timeplus_data.get('user', 'default'),
                        password=timeplus_data.get('password', ''),
                        database=timeplus_data.get('database', 'default'),
                        table=timeplus_data.get('table', 't_metrics')
                    )
            except Exception:
                pass
        
        # 从环境变量读取（保持向后兼容）
        return TimeplusConfig(
            host=os.getenv("TIMEPLUS_HOST", "localhost"),
            port=int(os.getenv("TIMEPLUS_PORT", "8463")),
            user=os.getenv("TIMEPLUS_USER", "default"),
            password=os.getenv("TIMEPLUS_PASSWORD", ""),
            database=os.getenv("TIMEPLUS_DATABASE", "default"),
            table=os.getenv("TIMEPLUS_TABLE", "t_metrics")
        )
    
    def create_model(self) -> Union[Claude, OpenAI, Groq]:
        """根据配置创建模型实例"""
        config = self.model_config
        
        if config.provider.lower() == "anthropic":
            kwargs = {"id": config.model_id}
            if config.api_key:
                kwargs["api_key"] = config.api_key
            if config.api_url:
                kwargs["base_url"] = config.api_url
            if config.temperature is not None:
                kwargs["temperature"] = config.temperature
            if config.max_tokens:
                kwargs["max_tokens"] = config.max_tokens
            return Claude(**kwargs)
        
        elif config.provider.lower() == "openai":
            kwargs = {"id": config.model_id}
            if config.api_key:
                kwargs["api_key"] = config.api_key
            if config.api_url:
                kwargs["base_url"] = config.api_url
            if config.temperature is not None:
                kwargs["temperature"] = config.temperature
            if config.max_tokens:
                kwargs["max_tokens"] = config.max_tokens
            return OpenAI(**kwargs)
        
        elif config.provider.lower() == "groq":
            kwargs = {"id": config.model_id}
            if config.api_key:
                kwargs["api_key"] = config.api_key
            if config.temperature is not None:
                kwargs["temperature"] = config.temperature
            if config.max_tokens:
                kwargs["max_tokens"] = config.max_tokens
            return Groq(**kwargs)
        
        else:
            raise ValueError(f"不支持的模型提供商: {config.provider}")
    
    def save_config(self):
        """保存当前配置到文件"""
        config_data = {
            "model": {
                "provider": self.model_config.provider,
                "model_id": self.model_config.model_id,
                "api_key": self.model_config.api_key,
                "api_url": self.model_config.api_url,
                "temperature": self.model_config.temperature,
                "max_tokens": self.model_config.max_tokens
            },
            "timeplus": {
                "host": self.timeplus_config.host,
                "port": self.timeplus_config.port,
                "user": self.timeplus_config.user,
                "password": self.timeplus_config.password,
                "database": self.timeplus_config.database,
                "table": self.timeplus_config.table
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        
        print(f"配置已保存到: {self.config_file}")

# 全局配置管理器实例
config_manager = AgentConfigManager()

# ============================================================================
# ReAct模式的Schema工具函数
# ============================================================================

def get_table_schema_from_api(table_name: str = "t_metrics") -> Dict[str, Any]:
    """
    从Timeplus API动态获取表结构 - ReAct工具函数
    
    Args:
        table_name: 表名，默认t_metrics
        
    Returns:
        表结构信息，Agent可以基于此结果进行推理和决策
    """
    if not PROTON_AVAILABLE:
        return {
            "success": False,
            "source": "driver_unavailable",
            "error": "proton-driver not installed",
            "table_name": table_name,
            "solution": "pip install proton-driver --extra-index-url https://d.timeplus.com/simple/",
            "recommendation": "Use get_static_schema() as fallback"
        }
    
    # 使用配置管理器获取连接配置
    timeplus_config = config_manager.timeplus_config
    host = timeplus_config.host
    port = timeplus_config.port
    database = timeplus_config.database
    
    try:
        # 连接Timeplus/Proton
        c = client.Client(host=host, port=port)
        
        # 查询表结构
        query = f"""
        SELECT name, type, comment
        FROM system.columns 
        WHERE database = '{database}' AND table = '{table_name}'
        ORDER BY position
        """
        
        result = c.execute(query)
        columns = {}
        
        for row in result:
            col_name = row[0] if len(row) > 0 else ""
            col_type = row[1] if len(row) > 1 else ""
            comment = row[2] if len(row) > 2 and row[2] else ""
            
            if col_name:
                description = col_type
                if comment:
                    description += f" - {comment}"
                # 添加业务描述
                if col_name in _get_column_business_descriptions():
                    business_desc = _get_column_business_descriptions()[col_name]
                    if not comment:
                        description += f" - {business_desc}"
                columns[col_name] = description
        
        if columns:
            return {
                "success": True,
                "source": "timeplus_api",
                "table_name": table_name,
                "database": database,
                "connection": f"{host}:{port}",
                "columns": columns,
                "column_count": len(columns),
                "recommendation": "Use this real-time schema for SQL generation"
            }
        else:
            return {
                "success": False,
                "source": "no_data",
                "error": f"No columns found for table {table_name}",
                "table_name": table_name,
                "database": database,
                "recommendation": "Check table name or use get_static_schema()"
            }
            
    except Exception as e:
        return {
            "success": False,
            "source": "connection_error",
            "error": str(e),
            "table_name": table_name,
            "connection_attempted": f"{host}:{port}",
            "recommendation": "Check Timeplus server status or use get_static_schema()"
        }

def get_static_schema(table_name: str = "t_metrics") -> Dict[str, Any]:
    """
    获取静态表结构 - ReAct工具函数备用方案
    
    Args:
        table_name: 表名
        
    Returns:
        静态表结构信息
    """
    if table_name == "t_metrics":
        columns = {
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
        }
        
        return {
            "success": True,
            "source": "static_definition",
            "table_name": table_name,
            "columns": columns,
            "column_count": len(columns),
            "note": "Static schema - may not reflect current database structure",
            "recommendation": "Prefer API schema when available"
        }
    else:
        return {
            "success": False,
            "source": "unsupported_table",
            "error": f"No static schema available for {table_name}",
            "supported_tables": ["t_metrics"],
            "recommendation": "Use get_table_schema_from_api() for other tables"
        }

def build_complete_schema_info(table_name: str = "t_metrics") -> Dict[str, Any]:
    """
    构建完整的表结构信息 - ReAct工具函数
    包含约束、建议等元信息
    
    Args:
        table_name: 表名
        
    Returns:
        完整的表结构元信息
    """
    return {
        "table_name": table_name,
        "description": "Time-series metrics data table - ONLY TABLE ALLOWED FOR QUERIES",
        "constraints": [
            "SINGLE TABLE ONLY - No JOINs allowed",
            "No subqueries with other tables",
            "Must search CSV knowledge base first to find relevant metrics"
        ],
        "query_patterns": [
            "Use to_float64(value) for numeric operations",
            "Use _tp_time for time-based filtering and windows",
            "Filter by metric field for specific metric types",
            "Use tagK/tagV pairs for dimension filtering",
            "Use table(t_metrics) for historical data analysis",
            "Use streaming queries for real-time monitoring"
        ],
        "common_functions": [
            "tumble(t_metrics, _tp_time, interval) - Non-overlapping windows",
            "hop(t_metrics, _tp_time, hop_size, window_size) - Sliding windows",
            "to_float64(value) - Convert string values to numbers",
            "now() - Current timestamp for time filters"
        ]
    }

def validate_sql_query(sql: str, host: str = None, port: int = None, username: str = None, password: str = None) -> Dict[str, Any]:
    """
    使用analyzer.py验证SQL查询 - ReAct工具函数
    
    Args:
        sql: 要验证的SQL查询
        host: 分析器服务器地址，默认使用配置文件中的host
        port: 分析器服务器端口，默认使用3218
        username: 用户名，默认使用配置文件中的user
        password: 密码，默认使用配置文件中的password
        
    Returns:
        验证结果字典，包含成功状态、分析结果等信息
    """
    try:
        # 使用配置管理器获取默认连接参数
        timeplus_config = config_manager.timeplus_config
        
        # 使用提供的参数或配置文件中的默认值
        analyzer_host = host or timeplus_config.host
        analyzer_port = port or 3218  # analyzer默认端口
        analyzer_username = username or timeplus_config.user
        analyzer_password = password or timeplus_config.password
        
        # 创建分析器客户端
        analyzer_client = AnalyzerClient(
            username=analyzer_username,
            password=analyzer_password,
            host=analyzer_host,
            port=analyzer_port
        )
        
        # 执行SQL分析
        analysis_result = analyzer_client.analyze_sql(sql)
        
        return {
            "success": True,
            "sql": sql,
            "analysis": analysis_result,
            "analyzer_host": f"{analyzer_host}:{analyzer_port}",
            "recommendation": "SQL validation completed successfully"
        }
        
    except Exception as e:
        return {
            "success": False,
            "sql": sql,
            "error": str(e),
            "analyzer_host": f"{analyzer_host}:{analyzer_port}" if 'analyzer_host' in locals() else "unknown",
            "recommendation": "Check SQL syntax and analyzer service availability"
        }

def _get_column_business_descriptions() -> Dict[str, str]:
    """内部函数：获取列的业务描述"""
    return {
        "event_ts": "Original event timestamp from source system",
        "metric": "Metric identifier for filtering and grouping",
        "value": "Metric value, stored as string, convert with to_float64() for math",
        "metric_date": "Pre-computed date component for date-based queries",
        "metric_time": "Pre-computed time component for time-based queries", 
        "metric_datetime": "Combined datetime for temporal analysis",
        "tagK1": "First tag key for dimensional analysis",
        "tagV1": "First tag value corresponding to tagK1",
        "tagK2": "Second tag key for additional dimensions",
        "tagV2": "Second tag value corresponding to tagK2",
        "tagK3": "Third tag key for further categorization",
        "tagV3": "Third tag value corresponding to tagK3",
        "tagK4": "Fourth tag key for detailed segmentation",
        "tagV4": "Fourth tag value corresponding to tagK4",
        "tagK5": "Fifth tag key for finest granularity",
        "tagV5": "Fifth tag value corresponding to tagK5",
        "_tp_time": "System ingestion timestamp, use for time windows and filters"
    }

# ============================================================================
# Agent配置和Prompt
# ============================================================================

# 加载原有prompt
try:
    with open('promptnew.txt', 'r', encoding='utf-8') as f:
        T_METRICS_PROMPT = f.read()
except FileNotFoundError:
    with open('prompt.txt', 'r', encoding='utf-8') as f:
        T_METRICS_PROMPT = f.read()

# 增强的ReAct模式Prompt
REACT_ENHANCED_PROMPT = f"""
{T_METRICS_PROMPT}

## REACT WORKFLOW FOR SCHEMA-AWARE SQL GENERATION

You have access to these ReAct tools for dynamic schema management:

1. **get_table_schema_from_api(table_name)** - Get real-time schema from Timeplus API
2. **get_static_schema(table_name)** - Get fallback static schema 
3. **build_complete_schema_info(table_name)** - Get constraints and query patterns
4. **validate_sql_query(sql)** - Validate generated SQL using analyzer service

### MANDATORY ReAct WORKFLOW:

#### Step 1: Search Metric Dictionary
- **MUST search CSV knowledge base** for relevant metrics based on user query
- Get exact metric names and tag information from metric.csv
- Identify available tagK/tagV combinations

#### Step 2: Obtain Table Schema (ReAct Decision Making)
- **FIRST attempt**: Call get_table_schema_from_api("t_metrics") 
- **Analyze result**: Check "success" field and "source" field
- **IF success=True and source="timeplus_api"**: Use this real-time schema
- **IF success=False**: Call get_static_schema("t_metrics") as fallback
- **ALWAYS call**: build_complete_schema_info("t_metrics") for constraints

#### Step 3: Generate Schema-Aware SQL
- Use the obtained column information and data types
- Apply search results from CSV knowledge base
- Follow constraints from complete_schema_info
- Generate Timeplus-compatible SQL

#### Step 4: Validate Generated SQL
- **ALWAYS call**: validate_sql_query(generated_sql) to verify syntax and semantics
- **Analyze validation result**: Check "success" field and "analysis" response
- **IF success=True**: SQL is valid and ready for use
- **IF success=False**: Review error message and regenerate SQL with corrections

#### Step 5: Final Quality Check
- Ensure single-table constraint compliance
- Include appropriate type conversions (to_float64, etc.)
- Add time-based filtering when relevant
- Provide validated SQL with confidence level

### REASONING EXAMPLES:

**Good ReAct Flow:**
1. "I need to search CSV knowledge base for CPU metrics"
2. "Now I'll get real-time schema: get_table_schema_from_api('t_metrics')"  
3. "API returned success=True, using 17 columns from timeplus_api"
4. "Getting constraints: build_complete_schema_info('t_metrics')"
5. "Generating SQL with real column types and search results"
6. "Validating SQL: validate_sql_query(generated_sql)"
7. "Validation success=True, SQL is syntactically correct and ready for use"

**Fallback Flow:**
1. "Searching CSV knowledge base..."
2. "Attempting API schema: get_table_schema_from_api('t_metrics')"
3. "API failed with connection_error, using fallback: get_static_schema('t_metrics')"
4. "Got 17 columns from static_definition source"
5. "Generating SQL with static schema and CSV search results"
6. "Validating SQL: validate_sql_query(generated_sql)"
7. "Validation success=True, SQL is valid despite using static schema"

### CRITICAL REQUIREMENTS:
- **Always use tool functions** - Never assume schema, always call tools
- **Check tool results** - React based on success/failure in tool responses
- **Prefer API schema** - Use real-time when available, fallback when not
- **Validate all SQL** - Always call validate_sql_query() before providing final result
- **Single table only** - Enforce t_metrics table constraint
- **CSV search first** - Must search knowledge base before SQL generation
"""

# ============================================================================
# Agent创建和主要函数
# ============================================================================

# CSV知识库
metric_knowledge = CSVKnowledgeBase(
    path="metric.csv",
    formats=["txt", "csv", "json"]
)

# 使用配置化模型创建Agent
def create_agent(config_manager: AgentConfigManager = None) -> Agent:
    """创建配置化的Agent实例"""
    if config_manager is None:
        config_manager = globals()['config_manager']
    
    model = config_manager.create_model()
    
    return Agent(
        model=model,
        tools=[get_table_schema_from_api, get_static_schema, build_complete_schema_info, validate_sql_query],
        knowledge=[metric_knowledge],
        instructions=REACT_ENHANCED_PROMPT,
        markdown=True,
        name="T-Metrics SQL Agent V2 (ReAct)",
        description=f"智能SQL生成器 ({config_manager.model_config.provider}:{config_manager.model_config.model_id})，使用ReAct模式动态获取表结构和SQL验证"
    )

# 创建默认Agent实例
t_metrics_agent_v2 = create_agent(config_manager)

def generate_sql_v2(query: str) -> str:
    """
    使用ReAct模式生成SQL查询
    
    Args:
        query: 自然语言查询
        
    Returns:
        生成的SQL查询字符串
    """
    response = t_metrics_agent_v2.run(query)
    return response.content

def configure_model(provider: str, model_id: str, api_key: str = None, api_url: str = None, temperature: float = 0.1) -> Agent:
    """
    配置并创建新的Agent实例
    
    Args:
        provider: 模型提供商 (anthropic, openai, groq)
        model_id: 模型ID
        api_key: API密钥
        api_url: API URL
        temperature: 温度参数
        
    Returns:
        配置好的Agent实例
    """
    # 创建新的配置管理器
    temp_config = AgentConfigManager()
    temp_config.model_config.provider = provider
    temp_config.model_config.model_id = model_id
    temp_config.model_config.api_key = api_key
    temp_config.model_config.api_url = api_url
    temp_config.model_config.temperature = temperature
    
    return create_agent(temp_config)

def save_default_config():
    """保存示例配置文件"""
    config_manager.save_config()
    print("示例配置文件已创建。")

def show_current_config():
    """显示当前配置"""
    model_config = config_manager.model_config
    timeplus_config = config_manager.timeplus_config
    
    print("=== 当前配置 ===")
    print(f"模型提供商: {model_config.provider}")
    print(f"模型ID: {model_config.model_id}")
    print(f"API密钥: {'已设置' if model_config.api_key else '未设置'}")
    print(f"API URL: {model_config.api_url or '默认'}")
    print(f"温度: {model_config.temperature}")
    print(f"最大Token: {model_config.max_tokens or '默认'}")
    
    print("\nTimeplus配置:")
    print(f"主机: {timeplus_config.host}:{timeplus_config.port}")
    print(f"数据库: {timeplus_config.database}")
    print(f"表名: {timeplus_config.table}")

def test_schema_tools():
    """测试所有schema工具函数"""
    print("=== Schema Tools 测试 ===")
    
    # 测试API schema获取
    print("\n1. 测试API Schema获取:")
    api_result = get_table_schema_from_api()
    print(f"   成功: {api_result['success']}")
    print(f"   来源: {api_result['source']}")
    if api_result['success']:
        print(f"   列数: {api_result['column_count']}")
        print(f"   连接: {api_result['connection']}")
    else:
        print(f"   错误: {api_result.get('error', 'Unknown')}")
        print(f"   建议: {api_result.get('recommendation', 'None')}")
    
    # 测试静态schema
    print("\n2. 测试静态Schema:")
    static_result = get_static_schema()
    print(f"   成功: {static_result['success']}")
    print(f"   来源: {static_result['source']}")
    print(f"   列数: {static_result['column_count']}")
    
    # 测试完整schema信息
    print("\n3. 测试完整Schema信息:")
    complete_info = build_complete_schema_info()
    print(f"   表名: {complete_info['table_name']}")
    print(f"   约束数: {len(complete_info['constraints'])}")
    print(f"   查询模式数: {len(complete_info['query_patterns'])}")
    
    # 测试SQL验证功能
    print("\n4. 测试SQL验证功能:")
    test_sql = "SELECT metric, to_float64(value) as val FROM t_metrics WHERE metric = 'cpu_usage' LIMIT 10"
    validation_result = validate_sql_query(test_sql)
    print(f"   成功: {validation_result['success']}")
    print(f"   分析器主机: {validation_result['analyzer_host']}")
    if validation_result['success']:
        print(f"   分析结果: {validation_result.get('analysis', {}).keys() if isinstance(validation_result.get('analysis'), dict) else 'Available'}")
    else:
        print(f"   错误: {validation_result.get('error', 'Unknown')}")
        print(f"   建议: {validation_result.get('recommendation', 'None')}")
    
    return {
        "api_schema": api_result,
        "static_schema": static_result, 
        "complete_info": complete_info,
        "validation_test": validation_result
    }

if __name__ == "__main__":
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--config":
        print("=== T-Metrics Agent V2 配置演示 ===\n")
        
        # 显示当前配置
        show_current_config()
        
        # 保存示例配置文件
        print("\n保存配置文件...")
        save_default_config()
        
        # 演示不同模型配置
        print("\n演示不同模型配置:")
        
        # OpenAI 配置示例
        print("\n1. OpenAI GPT-4 配置:")
        try:
            openai_agent = configure_model(
                provider="openai",
                model_id="gpt-4",
                temperature=0.1
            )
            print("   ✓ OpenAI Agent创建成功")
        except Exception as e:
            print(f"   ✗ OpenAI Agent创建失败: {e}")
        
        # Groq 配置示例
        print("\n2. Groq Llama配置:")
        try:
            groq_agent = configure_model(
                provider="groq", 
                model_id="llama-3.1-70b-versatile",
                temperature=0.1
            )
            print("   ✓ Groq Agent创建成功")
        except Exception as e:
            print(f"   ✗ Groq Agent创建失败: {e}")
        
        print(f"\n{'='*60}")
        print("配置演示完成")
        print(f"{'='*60}")
        
    else:
        # 常规测试模式
        test_queries = [
            "查询深圳的tick行情延时",
            "显示所有交易中心的策略成交额",
            "统计高频Alpha团队的CPU使用情况", 
            "近一小时的订单废单数量"
        ]
        
        print("=== T-Metrics SQL Agent V2 (ReAct Mode) 测试 ===\n")
        
        # 显示当前配置
        print("当前Agent配置:")
        show_current_config()
        
        # 首先测试schema工具
        print(f"\n{'='*60}")
        print("测试Schema工具函数...")
        tool_results = test_schema_tools()
        
        # 显示推荐的schema来源
        if tool_results["api_schema"]["success"]:
            print(f"\n✓ 推荐使用: {tool_results['api_schema']['source']} schema")
        else:
            print(f"\n⚠ 将使用: {tool_results['static_schema']['source']} schema")
        
        # 测试SQL生成
        print(f"\n{'='*60}")
        print("开始SQL生成测试 (ReAct模式)...")
        print(f"{'='*60}")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n测试 {i}: {query}")
            print("-" * 40)
            try:
                sql_result = generate_sql_v2(query)
                print("生成结果:")
                print(sql_result)
            except Exception as e:
                print(f"错误: {e}")
            print("-" * 40)
        
        print(f"\n{'='*60}")
        print("测试完成")
        print("运行 'python t_metrics_agent_v2.py --config' 查看配置功能")
        print(f"{'='*60}")