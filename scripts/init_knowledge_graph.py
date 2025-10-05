"""
知识图谱数据导入脚本

从 data/knowledge/ 目录导入知识点和关系数据到数据库。
支持增量导入、数据验证和重复检测。

使用方法:
    uv run python scripts/init_knowledge_graph.py --subject math --grade 7
    uv run python scripts/init_knowledge_graph.py --all
    uv run python scripts/init_knowledge_graph.py --validate-only
"""

import argparse
import asyncio
import json
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set
from uuid import UUID

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal, Base, engine
from src.models.knowledge import (
    KnowledgeNode,
    KnowledgeRelation,
    NodeType,
    RelationType,
)


class KnowledgeGraphImporter:
    """知识图谱数据导入器"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.code_to_id_map: Dict[str, UUID] = {}  # 编码到ID的映射
        self.stats = {
            "nodes_created": 0,
            "nodes_updated": 0,
            "nodes_skipped": 0,
            "relations_created": 0,
            "relations_updated": 0,
            "relations_skipped": 0,
            "errors": [],
        }

    async def load_existing_nodes(self) -> None:
        """加载已存在的节点编码映射"""
        result = await self.session.execute(
            select(KnowledgeNode.code, KnowledgeNode.id)
        )
        rows = result.all()
        # 确保 ID 是 UUID 类型
        self.code_to_id_map = {
            str(row[0]): uuid.UUID(str(row[1])) if isinstance(row[1], str) else row[1]
            for row in rows
        }
        print(f"✓ 已加载 {len(self.code_to_id_map)} 个现有节点")

    async def import_nodes(self, nodes_data: List[Dict]) -> None:
        """
        导入知识节点

        Args:
            nodes_data: 节点数据列表
        """
        print(f"\n开始导入 {len(nodes_data)} 个知识节点...")

        for node_data in nodes_data:
            try:
                code = node_data["code"]

                # 检查节点是否已存在
                if code in self.code_to_id_map:
                    # 更新现有节点
                    node_id = self.code_to_id_map[code]
                    # 确保 node_id 是 UUID 对象
                    if isinstance(node_id, str):
                        node_id = uuid.UUID(node_id)

                    result = await self.session.execute(
                        select(KnowledgeNode).where(KnowledgeNode.id == str(node_id))
                    )
                    node = result.scalar_one()

                    # 更新字段
                    node.name = node_data["name"]
                    node.node_type = node_data["node_type"]
                    node.subject = node_data["subject"]
                    node.level = node_data["level"]
                    node.description = node_data.get("description")  # type: ignore
                    node.keywords = node_data.get("keywords")  # type: ignore
                    node.examples = node_data.get("examples")  # type: ignore
                    node.difficulty = node_data.get("difficulty", 3)
                    node.importance = node_data.get("importance", 3)
                    node.tags = node_data.get("tags")  # type: ignore
                    node.external_links = node_data.get("external_links")  # type: ignore

                    self.stats["nodes_updated"] += 1
                    print(f"  ↻ 更新节点: {code} - {node_data['name']}")
                else:
                    # 创建新节点 (暂时不设置 parent_id)
                    node = KnowledgeNode(
                        code=code,
                        name=node_data["name"],
                        node_type=node_data["node_type"],
                        subject=node_data["subject"],
                        level=node_data["level"],
                        description=node_data.get("description"),
                        keywords=node_data.get("keywords"),
                        examples=node_data.get("examples"),
                        difficulty=node_data.get("difficulty", 3),
                        importance=node_data.get("importance", 3),
                        tags=node_data.get("tags"),
                        external_links=node_data.get("external_links"),
                    )

                    self.session.add(node)
                    await self.session.flush()  # 获取生成的ID

                    # 更新映射
                    self.code_to_id_map[code] = node.id  # type: ignore

                    self.stats["nodes_created"] += 1
                    print(f"  + 创建节点: {code} - {node_data['name']}")

            except Exception as e:
                error_msg = f"导入节点失败 {node_data.get('code', 'unknown')}: {str(e)}"
                self.stats["errors"].append(error_msg)
                print(f"  ✗ {error_msg}")

        # 提交第一批节点
        await self.session.commit()

        # 第二次遍历：设置 parent_id
        print(f"\n设置父子关系...")
        for node_data in nodes_data:
            parent_code = node_data.get("parent_code")
            if parent_code:
                try:
                    code = node_data["code"]
                    node_id = self.code_to_id_map[code]
                    parent_id = self.code_to_id_map.get(parent_code)

                    if not parent_id:
                        raise ValueError(f"父节点 {parent_code} 不存在")

                    # 确保查询 ID 是字符串格式
                    node_id_str = (
                        str(node_id) if isinstance(node_id, uuid.UUID) else node_id
                    )

                    result = await self.session.execute(
                        select(KnowledgeNode).where(KnowledgeNode.id == node_id_str)
                    )
                    node = result.scalar_one()

                    # parent_id 需要是 UUID 对象（SQLAlchemy 会自动转换为字符串存储）
                    if isinstance(parent_id, str):
                        node.parent_id = uuid.UUID(parent_id)  # type: ignore
                    else:
                        node.parent_id = parent_id  # type: ignore

                    print(f"  → {code} 的父节点设为 {parent_code}")

                except Exception as e:
                    error_msg = f"设置父节点失败 {code}: {str(e)}"
                    self.stats["errors"].append(error_msg)
                    print(f"  ✗ {error_msg}")

        # 提交父子关系
        await self.session.commit()

    async def import_relations(self, relations_data: List[Dict]) -> None:
        """
        导入知识点关系

        Args:
            relations_data: 关系数据列表
        """
        print(f"\n开始导入 {len(relations_data)} 个知识关系...")

        for rel_data in relations_data:
            try:
                from_code = rel_data["from_code"]
                to_code = rel_data["to_code"]

                # 获取节点ID
                from_node_id = self.code_to_id_map.get(from_code)
                to_node_id = self.code_to_id_map.get(to_code)

                if not from_node_id:
                    raise ValueError(f"源节点 {from_code} 不存在")
                if not to_node_id:
                    raise ValueError(f"目标节点 {to_code} 不存在")

                # 转换为 UUID 对象（用于查询和赋值）
                from_node_id_uuid = (
                    from_node_id
                    if isinstance(from_node_id, uuid.UUID)
                    else uuid.UUID(from_node_id)
                )
                to_node_id_uuid = (
                    to_node_id
                    if isinstance(to_node_id, uuid.UUID)
                    else uuid.UUID(to_node_id)
                )

                # 检查关系是否已存在（查询和赋值都使用 UUID 对象）
                result = await self.session.execute(
                    select(KnowledgeRelation).where(
                        KnowledgeRelation.from_node_id == from_node_id_uuid,
                        KnowledgeRelation.to_node_id == to_node_id_uuid,
                        KnowledgeRelation.relation_type == rel_data["relation_type"],
                    )
                )
                existing_rel = result.scalar_one_or_none()

                if existing_rel:
                    # 更新现有关系
                    existing_rel.weight = rel_data.get("weight", 1.0)
                    existing_rel.is_bidirectional = rel_data.get(
                        "is_bidirectional", False
                    )
                    existing_rel.description = rel_data.get("description")  # type: ignore
                    existing_rel.confidence = rel_data.get("confidence", 0.8)

                    self.stats["relations_updated"] += 1
                    print(
                        f"  ↻ 更新关系: {from_code} → {to_code} ({rel_data['relation_type']})"
                    )
                else:
                    # 创建新关系（使用 UUID 对象）
                    relation = KnowledgeRelation(
                        from_node_id=from_node_id_uuid,
                        to_node_id=to_node_id_uuid,
                        relation_type=rel_data["relation_type"],
                        weight=rel_data.get("weight", 1.0),
                        is_bidirectional=rel_data.get("is_bidirectional", False),
                        description=rel_data.get("description"),
                        confidence=rel_data.get("confidence", 0.8),
                    )

                    self.session.add(relation)

                    self.stats["relations_created"] += 1
                    print(
                        f"  + 创建关系: {from_code} → {to_code} ({rel_data['relation_type']})"
                    )

            except Exception as e:
                error_msg = f"导入关系失败 {from_code} → {to_code}: {str(e)}"
                self.stats["errors"].append(error_msg)
                print(f"  ✗ {error_msg}")

        # 提交关系
        await self.session.commit()

    async def import_from_file(self, file_path: Path) -> None:
        """
        从JSON文件导入数据

        Args:
            file_path: JSON文件路径
        """
        print(f"\n{'=' * 60}")
        print(f"导入文件: {file_path}")
        print(f"{'=' * 60}")

        # 读取JSON文件
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        metadata = data.get("metadata", {})
        print(f"\n元数据:")
        print(f"  学科: {metadata.get('subject', 'unknown')}")
        print(f"  年级: {metadata.get('grade', 'unknown')}")
        print(f"  版本: {metadata.get('version', 'unknown')}")
        print(f"  描述: {metadata.get('description', '')}")

        # 导入节点
        nodes_data = data.get("nodes", [])
        if nodes_data:
            await self.import_nodes(nodes_data)

        # 导入关系
        relations_data = data.get("relations", [])
        if relations_data:
            await self.import_relations(relations_data)

    def print_stats(self) -> None:
        """打印统计信息"""
        print(f"\n{'=' * 60}")
        print("导入统计:")
        print(f"{'=' * 60}")
        print(f"知识节点:")
        print(f"  + 新建: {self.stats['nodes_created']}")
        print(f"  ↻ 更新: {self.stats['nodes_updated']}")
        print(f"  - 跳过: {self.stats['nodes_skipped']}")
        print(f"\n知识关系:")
        print(f"  + 新建: {self.stats['relations_created']}")
        print(f"  ↻ 更新: {self.stats['relations_updated']}")
        print(f"  - 跳过: {self.stats['relations_skipped']}")

        if self.stats["errors"]:
            print(f"\n✗ 错误 ({len(self.stats['errors'])}):")
            for error in self.stats["errors"][:10]:  # 只显示前10个
                print(f"  - {error}")
            if len(self.stats["errors"]) > 10:
                print(f"  ... 还有 {len(self.stats['errors']) - 10} 个错误")
        else:
            print(f"\n✓ 导入成功，无错误")


async def validate_data_file(file_path: Path) -> bool:
    """
    验证数据文件格式

    Args:
        file_path: JSON文件路径

    Returns:
        验证是否通过
    """
    print(f"\n验证文件: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  ✗ JSON格式错误: {e}")
        return False
    except Exception as e:
        print(f"  ✗ 读取文件失败: {e}")
        return False

    errors = []

    # 验证元数据
    metadata = data.get("metadata", {})
    if not metadata:
        errors.append("缺少 metadata 字段")
    else:
        required_meta_fields = ["subject", "grade", "version"]
        for field in required_meta_fields:
            if field not in metadata:
                errors.append(f"metadata 缺少字段: {field}")

    # 验证节点
    nodes = data.get("nodes", [])
    if not nodes:
        errors.append("没有节点数据")
    else:
        node_codes = set()
        required_node_fields = ["code", "name", "node_type", "subject", "level"]

        for i, node in enumerate(nodes):
            # 检查必填字段
            for field in required_node_fields:
                if field not in node:
                    errors.append(f"节点 {i} 缺少字段: {field}")

            # 检查编码唯一性
            code = node.get("code")
            if code:
                if code in node_codes:
                    errors.append(f"节点编码重复: {code}")
                node_codes.add(code)

            # 检查节点类型
            node_type = node.get("node_type")
            if node_type and node_type not in [
                "subject",
                "chapter",
                "section",
                "concept",
                "skill",
                "problem_type",
            ]:
                errors.append(f"节点 {code} 的 node_type 无效: {node_type}")

            # 检查难度和重要性范围
            difficulty = node.get("difficulty")
            if difficulty is not None and not (1 <= difficulty <= 5):
                errors.append(f"节点 {code} 的 difficulty 应在 1-5 之间: {difficulty}")

            importance = node.get("importance")
            if importance is not None and not (1 <= importance <= 5):
                errors.append(f"节点 {code} 的 importance 应在 1-5 之间: {importance}")

        # 验证关系
        relations = data.get("relations", [])
        if relations:
            required_rel_fields = ["from_code", "to_code", "relation_type"]

            for i, rel in enumerate(relations):
                # 检查必填字段
                for field in required_rel_fields:
                    if field not in rel:
                        errors.append(f"关系 {i} 缺少字段: {field}")

                # 检查节点存在性
                from_code = rel.get("from_code")
                to_code = rel.get("to_code")

                if from_code and from_code not in node_codes:
                    errors.append(f"关系引用了不存在的源节点: {from_code}")
                if to_code and to_code not in node_codes:
                    errors.append(f"关系引用了不存在的目标节点: {to_code}")

                # 检查关系类型
                rel_type = rel.get("relation_type")
                if rel_type and rel_type not in [
                    "prerequisite",
                    "contains",
                    "similar",
                    "applies_to",
                    "derives_from",
                ]:
                    errors.append(f"关系类型无效: {rel_type}")

                # 检查权重和置信度范围
                weight = rel.get("weight")
                if weight is not None and not (0.0 <= weight <= 1.0):
                    errors.append(f"关系权重应在 0.0-1.0 之间: {weight}")

                confidence = rel.get("confidence")
                if confidence is not None and not (0.0 <= confidence <= 1.0):
                    errors.append(f"关系置信度应在 0.0-1.0 之间: {confidence}")

    # 打印结果
    if errors:
        print(f"  ✗ 发现 {len(errors)} 个错误:")
        for error in errors[:20]:  # 只显示前20个
            print(f"    - {error}")
        if len(errors) > 20:
            print(f"    ... 还有 {len(errors) - 20} 个错误")
        return False
    else:
        print(f"  ✓ 验证通过 ({len(nodes)} 个节点, {len(relations)} 个关系)")
        return True


async def create_tables_if_not_exist():
    """创建数据库表（如果不存在）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ 数据库表已准备就绪")


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="知识图谱数据导入工具")
    parser.add_argument("--subject", type=str, help="学科 (math/chinese/english)")
    parser.add_argument("--grade", type=int, help="年级 (7/8/9)")
    parser.add_argument("--all", action="store_true", help="导入所有数据")
    parser.add_argument(
        "--validate-only", action="store_true", help="仅验证数据，不导入"
    )
    parser.add_argument("--create-tables", action="store_true", help="创建数据库表")

    args = parser.parse_args()

    # 确定要处理的文件
    data_dir = Path(__file__).parent.parent / "data" / "knowledge"
    files_to_process: List[Path] = []

    if args.all:
        # 导入所有数据
        for subject_dir in data_dir.iterdir():
            if subject_dir.is_dir():
                for grade_file in subject_dir.glob("grade_*.json"):
                    files_to_process.append(grade_file)
    elif args.subject and args.grade:
        # 导入指定学科和年级
        file_path = data_dir / args.subject / f"grade_{args.grade}.json"
        if file_path.exists():
            files_to_process.append(file_path)
        else:
            print(f"✗ 文件不存在: {file_path}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

    if not files_to_process:
        print("✗ 没有找到要处理的文件")
        sys.exit(1)

    # 验证模式
    if args.validate_only:
        print("\n" + "=" * 60)
        print("数据验证模式")
        print("=" * 60)

        all_valid = True
        for file_path in files_to_process:
            if not await validate_data_file(file_path):
                all_valid = False

        if all_valid:
            print("\n✓ 所有文件验证通过")
            sys.exit(0)
        else:
            print("\n✗ 部分文件验证失败")
            sys.exit(1)

    # 创建表（如果需要）
    if args.create_tables:
        await create_tables_if_not_exist()

    # 导入模式
    async with AsyncSessionLocal() as session:
        importer = KnowledgeGraphImporter(session)

        # 加载现有节点
        await importer.load_existing_nodes()

        # 导入所有文件
        for file_path in files_to_process:
            # 先验证
            if not await validate_data_file(file_path):
                print(f"✗ 跳过文件: {file_path}")
                continue

            # 导入
            await importer.import_from_file(file_path)

        # 打印统计
        importer.print_stats()


if __name__ == "__main__":
    asyncio.run(main())
