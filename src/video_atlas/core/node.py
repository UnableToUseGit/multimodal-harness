# -*- coding: utf-8 -*-
"""
FSNode - File System Node (READ-ONLY)

Represents a file or directory in the VideoAtlas workspace.
This class is READ-ONLY - all write operations should go through Workspace.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class NodeType(str, Enum):
    """节点类型"""
    FILE = "file"
    DIRECTORY = "directory"


class FSNode(BaseModel):
    """
    文件系统 node - 可以是目录或文件 (READ-ONLY)
    
    注意：这个类只用于内存中的树结构表示，不包含写操作。
    所有文件系统的修改操作应通过 Workspace 执行 Linux 命令来完成。
    
    Attributes:
        name: 节点名称 (文件名或目录名)
        node_type: 节点类型 (file/directory)
        content: 文件内容 (仅文件有效)
        summary: 摘要/README 内容
        children: 子节点列表 (仅目录有效)
        meta: 元信息
        created_at: 创建时间
        updated_at: 更新时间
    """
    name: str = Field(..., description="节点名称")
    node_type: NodeType = Field(default=NodeType.FILE, description="节点类型")
    content: Optional[str] = Field(default=None, description="文件内容")
    summary: Optional[str] = Field(default=None, description="摘要/README")
    children: List[FSNode] = Field(default_factory=list, description="子节点")
    meta: Dict[str, Any] = Field(default_factory=dict, description="元信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    @property
    def is_dir(self) -> bool:
        """是否为目录"""
        return self.node_type == NodeType.DIRECTORY
    
    @property
    def is_file(self) -> bool:
        """是否为文件"""
        return self.node_type == NodeType.FILE
    
    def get_child(self, name: str) -> Optional[FSNode]:
        """获取子节点"""
        if not self.is_dir:
            return None
        for child in self.children:
            if child.name == name:
                return child
        return None
    
    def to_tree_str(self, prefix: str = "", is_last: bool = True, depth: int = -1, current_depth: int = 0) -> str:
        """
        生成树形结构字符串
        
        Args:
            prefix: 前缀字符串
            is_last: 是否为同级最后一个节点
            depth: 最大深度 (-1 表示无限)
            current_depth: 当前深度
        """
        if depth != -1 and current_depth > depth:
            return ""
        
        connector = "└── " if is_last else "├── "
        icon = "📁 " if self.is_dir else "📄 "
        
        # 根节点不需要连接符
        if current_depth == 0:
            result = f"{icon}{self.name}/\n" if self.is_dir else f"{icon}{self.name}\n"
        else:
            result = f"{prefix}{connector}{icon}{self.name}" + ("/" if self.is_dir else "") + "\n"
        
        if self.is_dir and self.children:
            # 计算子节点的前缀
            child_prefix = prefix + ("    " if is_last else "│   ") if current_depth > 0 else ""
            for i, child in enumerate(self.children):
                is_child_last = (i == len(self.children) - 1)
                result += child.to_tree_str(child_prefix, is_child_last, depth, current_depth + 1)
        
        return result
    
    def find_node(self, path_parts: List[str]) -> Optional[FSNode]:
        """
        根据路径部分查找节点
        
        Args:
            path_parts: 路径分段列表，如 ["dir1", "dir2", "file.md"]
        """
        if not path_parts:
            return self
        
        if not self.is_dir:
            return None
        
        first_part = path_parts[0]
        remaining = path_parts[1:]
        
        child = self.get_child(first_part)
        if child is None:
            return None
        
        if not remaining:
            return child
        
        return child.find_node(remaining)
    
    def get_all_files(self) -> List[FSNode]:
        """获取所有文件节点（递归）"""
        files = []
        if self.is_file:
            files.append(self)
        else:
            for child in self.children:
                files.extend(child.get_all_files())
        return files
    
    def get_all_dirs(self) -> List[FSNode]:
        """获取所有目录节点（递归）"""
        dirs = []
        if self.is_dir:
            dirs.append(self)
            for child in self.children:
                dirs.extend(child.get_all_dirs())
        return dirs
    
    @classmethod
    def create_file(cls, name: str, content: str = "", summary: str = "", meta: Dict = None) -> FSNode:
        """创建文件节点（内存中）"""
        return cls(
            name=name,
            node_type=NodeType.FILE,
            content=content,
            summary=summary,
            meta=meta or {}
        )
    
    @classmethod
    def create_dir(cls, name: str, summary: str = "", meta: Dict = None) -> FSNode:
        """创建目录节点（内存中）"""
        return cls(
            name=name,
            node_type=NodeType.DIRECTORY,
            summary=summary,
            meta=meta or {}
        )


# class 
