# mongodb_server.py
from fastmcp import FastMCP
from pymongo import MongoClient
from datetime import datetime
from typing import Optional, List, Dict
import logging
import os

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_db_config():
    """Get database configuration from environment variables."""
    config = {
        "uri": os.getenv("MONGO_URI", "mongodb://localhost:27017"),
        "key": os.getenv("QUERY_KEY"),
        "database": os.getenv("DATABASE_NAME","execMcpSecurity")
    }
    
    if not all([config["uri"], config["key"], config["database"]]):
        logging.error("Missing required database configuration. Please check environment variables:")
        logging.error("MONGO_URI, QUERY_KEY, and DATABASE_NAME are required")
        raise ValueError("Missing required database configuration")
    
    return config

# 创建 MCP Server
mcp = FastMCP("ebpfExecDB")

# 定义查询工具：根据集合名称和时间戳范围查询集合内容
@mcp.tool()
def query_collection(
    collection_name: str, 
    start_time: Optional[str] = None, 
    end_time: Optional[str] = None
) -> List[Dict]:
    """
    根据集合名称和时间戳范围查询集合内容。
    
    :param collection_name: 集合名称
    :param start_time: 开始时间（ISO格式，如2025-01-01T00:00:00）
    :param end_time: 结束时间（ISO格式，如2025-01-02T23:59:59）
    """
    config = get_db_config()
    if config['key'] != 'admin888':
        return

    # 初始化 MongoDB 客户端
    client = MongoClient(config['uri'])
    db = client[config['database']]

    collection = db[collection_name]  # 动态选择集合
    query = {}
    
    if start_time:
        query["timestamp"] = {"$gte": datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S").timestamp()}
    if end_time:
        if "timestamp" not in query:
            query["timestamp"] = {}
        query["timestamp"]["$lte"] = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S").timestamp()
    
    logging.info(f"Querying collection '{collection}' with query: {query}")
    result = list(collection.find(query))
    return result