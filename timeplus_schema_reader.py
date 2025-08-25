"""
Timeplus/Proton动态Schema读取模块
支持从Timeplus或Proton数据库动态获取t_metrics表结构
"""

from typing import Dict, Any, Optional, List, Tuple
import os
import logging

try:
    from proton_driver import client
    PROTON_AVAILABLE = True
except ImportError:
    PROTON_AVAILABLE = False
    logging.warning("proton-driver不可用，将使用静态schema")

class TimeplusSchemaReader:
    """Timeplus/Proton Schema读取器"""
    
    def __init__(self, 
                 host: str = None,
                 port: int = None,
                 user: str = None,
                 password: str = None,
                 database: str = None):
        """
        初始化Schema读取器
        
        Args:
            host: Timeplus/Proton服务器地址
            port: 端口号
            user: 用户名
            password: 密码  
            database: 数据库名
        """
        self.host = host or os.getenv("TIMEPLUS_HOST", "localhost")
        self.port = port or int(os.getenv("TIMEPLUS_PORT", "8463"))
        self.user = user or os.getenv("TIMEPLUS_USER", "default")
        self.password = password or os.getenv("TIMEPLUS_PASSWORD", "")
        self.database = database or os.getenv("TIMEPLUS_DATABASE", "default")
        self.client = None
        
    def connect(self) -> bool:
        """建立数据库连接"""
        if not PROTON_AVAILABLE:
            return False
            
        try:
            self.client = client.Client(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            # 测试连接
            self.client.execute("SELECT 1")
            return True
        except Exception as e:
            logging.error(f"连接Timeplus失败: {e}")
            return False
    
    def get_table_columns(self, table_name: str) -> List[Tuple[str, str, str]]:
        """
        获取表的列信息
        
        Args:
            table_name: 表名
            
        Returns:
            列信息列表: [(column_name, data_type, comment), ...]
        """
        if not self.client:
            return []
            
        try:
            # 优先使用system.columns查询
            query = f"""
            SELECT name, type, comment
            FROM system.columns 
            WHERE database = '{self.database}' AND table = '{table_name}'
            ORDER BY position
            """
            
            result = self.client.execute(query)
            columns = []
            
            for row in result:
                column_name = row[0] if len(row) > 0 else ""
                column_type = row[1] if len(row) > 1 else ""
                comment = row[2] if len(row) > 2 else ""
                columns.append((column_name, column_type, comment))
            
            if not columns:
                # 回退到DESCRIBE方法
                columns = self._describe_table(table_name)
                
            return columns
            
        except Exception as e:
            logging.error(f"获取表结构失败: {e}")
            return self._describe_table(table_name)
    
    def _describe_table(self, table_name: str) -> List[Tuple[str, str, str]]:
        """使用DESCRIBE命令获取表结构"""
        try:
            query = f"DESCRIBE {self.database}.{table_name}"
            result = self.client.execute(query)
            
            columns = []
            for row in result:
                if len(row) >= 2:
                    column_name = row[0]
                    column_type = row[1]
                    comment = row[2] if len(row) > 2 else ""
                    columns.append((column_name, column_type, comment))
            
            return columns
        except Exception as e:
            logging.error(f"DESCRIBE表失败: {e}")
            return []
    
    def get_schema_dict(self, table_name: str = "t_metrics") -> Dict[str, Any]:
        """
        获取表的完整schema字典
        
        Args:
            table_name: 表名，默认为t_metrics
            
        Returns:
            Schema字典
        """
        if not self.connect():
            return self._get_fallback_schema(table_name)
        
        columns_info = self.get_table_columns(table_name)
        
        if not columns_info:
            return self._get_fallback_schema(table_name)
        
        # 构建columns字典
        columns = {}
        for col_name, col_type, comment in columns_info:
            description = col_type
            if comment:
                description += f" - {comment}"
            elif col_name in self._get_column_descriptions():
                description += f" - {self._get_column_descriptions()[col_name]}"
            columns[col_name] = description
        
        return {
            "table_name": table_name,
            "description": "Time-series metrics data table - ONLY TABLE ALLOWED FOR QUERIES",
            "columns": columns,
            "constraints": [
                "SINGLE TABLE ONLY - No JOINs allowed",
                "No subqueries with other tables", 
                "Must search CSV knowledge base first to find relevant metrics"
            ],
            "source": "timeplus_api",
            "connection_info": {
                "host": self.host,
                "port": self.port,
                "database": self.database
            }
        }
    
    def _get_column_descriptions(self) -> Dict[str, str]:
        """获取列的业务描述"""
        return {
            "event_ts": "Event timestamp",
            "metric": "Metric name identifier",
            "value": "Metric value (use to_float64() for numeric operations)",
            "metric_date": "Date component",
            "metric_time": "Time component",
            "metric_datetime": "Combined datetime",
            "tagK1": "Tag key 1",
            "tagV1": "Tag value 1", 
            "tagK2": "Tag key 2",
            "tagV2": "Tag value 2",
            "tagK3": "Tag key 3",
            "tagV3": "Tag value 3",
            "tagK4": "Tag key 4",
            "tagV4": "Tag value 4",
            "tagK5": "Tag key 5", 
            "tagV5": "Tag value 5",
            "_tp_time": "System timestamp"
        }
    
    def _get_fallback_schema(self, table_name: str) -> Dict[str, Any]:
        """获取回退的静态schema"""
        return {
            "table_name": table_name,
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
            ],
            "source": "fallback"
        }

# 全局Schema读取器实例
_schema_reader = None

def get_schema_reader() -> TimeplusSchemaReader:
    """获取全局Schema读取器实例"""
    global _schema_reader
    if _schema_reader is None:
        _schema_reader = TimeplusSchemaReader()
    return _schema_reader

def get_table_schema(table_name: str = "t_metrics") -> Dict[str, Any]:
    """
    获取表schema的便捷函数
    
    Args:
        table_name: 表名，默认为t_metrics
        
    Returns:
        表的schema字典
    """
    reader = get_schema_reader()
    return reader.get_schema_dict(table_name)

if __name__ == "__main__":
    # 测试Schema读取功能
    print("=== Timeplus Schema Reader 测试 ===")
    
    # 测试静态schema
    reader = TimeplusSchemaReader()
    fallback_schema = reader._get_fallback_schema("t_metrics")
    print(f"静态Schema - 表名: {fallback_schema['table_name']}")
    print(f"静态Schema - 列数: {len(fallback_schema['columns'])}")
    print(f"静态Schema - 来源: {fallback_schema['source']}")
    
    # 测试动态schema获取
    print("\n尝试连接Timeplus获取动态Schema...")
    dynamic_schema = get_table_schema()
    print(f"动态Schema - 表名: {dynamic_schema['table_name']}")
    print(f"动态Schema - 列数: {len(dynamic_schema['columns'])}")
    print(f"动态Schema - 来源: {dynamic_schema['source']}")
    
    if dynamic_schema['source'] == 'timeplus_api':
        print("✓ 成功连接到Timeplus API并获取Schema")
        print("前5个列:")
        for i, (col, desc) in enumerate(list(dynamic_schema['columns'].items())[:5]):
            print(f"  {col}: {desc}")
    else:
        print("⚠ 使用静态Schema (Timeplus API不可用)")
        
    print("\n=== 测试完成 ===")