import os
import logging
import asyncio
from types import FunctionType, CoroutineType

from models.user import User
from util.module_discover import discover_modules, ModuleRegistry, ModuleContext
from source_types._relationships import DetectApproach
from schemas.source import *

def _register_source_type(context: ModuleContext, name, module, **kwargs):
    required_methods = [
                        'display_info',
                        'connection_info',
                        'test_connectivity',
                        'list_entities',
                        'create_source',
                        'update_source',
                        'detect_relationships',
                        # 'embedding',
                        'statistics',
                        'preview_data',
                    ]

    if not all(hasattr(module, method) for method in required_methods):
        context.info(f"Ignore : Source Type {name} does not have required methods ")
        return False
    
    return True


def discover_source_types(context : ModuleContext):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    discover_modules(context, os.path.join(current_dir, 'source_types'), 'source_types', _register_source_type, context.get_logger())


global_source_type_context = None

def setup_source_types():
    global _global_source_type_context
    context = ModuleContext(__name__, ModuleRegistry() , logging.getLogger())
    discover_source_types(context)
    _global_source_type_context = context
    return context

# Depends
def get_source_type_context():
    global _global_source_type_context
    if _global_source_type_context is None:
        setup_source_types()
    return _global_source_type_context


async def get_supported_source_types(context : ModuleContext):
    source_types = []
    for k, v in context.get_registry().items():
        source_types.append(await get_source_type(context, k))
    return source_types

async def get_source_type(context : ModuleContext, source_type : str):
    if source_type not in context.get_registry():
        raise Exception(f"Source type {source_type} not found")
    module = context.get_registry()[source_type]
    return {
        "name": source_type,
        "display_info": await module.display_info(),
        "connection_info": await module.connection_info(),
    }


async def test_connectivity(context: ModuleContext, source_type: str, connection_info: dict) -> dict:
    if source_type not in context.get_registry():
        raise Exception(f"Source type {source_type} not found")
    module = context.get_registry()[source_type]
    func = getattr(module, "test_connectivity", None)
    if not func:
        raise Exception(f"Source type {source_type} does not have required function : test_connectivity")
    if asyncio.iscoroutinefunction(func):
        result = await func(connection_info)
    else:
        result = func(connection_info)
    return result
        


async def list_entities(context: ModuleContext, source_type: str, connection_info: dict):
    if source_type not in context.get_registry():
        raise Exception(f"Source type {source_type} not found")
    module = context.get_registry()[source_type]
    func = getattr(module, "list_entities", None)
    if not func:
        raise Exception(f"Source type {source_type} does not have required function : list_entities")
    if asyncio.iscoroutinefunction(func):
        result = await func(connection_info)
    else:
        result = func(connection_info)
    return result


async def create_source(context: ModuleContext, source_type: str, current_user: User, name: str, is_private : bool, description: list[LangDescriptionModel], connection_info: dict, additional_details: str, entities: list[EntitySchemaModel]):
    if source_type not in context.get_registry():
        raise Exception(f"Source type {source_type} not found")
    module = context.get_registry()[source_type]
    func = getattr(module, "create_source", None)
    if not func:
        raise Exception(f"Source type {source_type} does not have required function : create_source")
    if asyncio.iscoroutinefunction(func):
        result = await func(current_user, name, is_private, description, connection_info, additional_details, entities)
    else:
        result = func(current_user, name, is_private, description, connection_info, additional_details, entities)
    return result


async def update_source(context: ModuleContext, source_type: str, current_user: User, source_id: int,  name: str, is_private : bool, description: list[LangDescriptionModel], connection_info: dict, additional_details: str, entities: list[EntitySchemaModel]):
    if source_type not in context.get_registry():
        raise Exception(f"Source type {source_type} not found")
    module = context.get_registry()[source_type]
    func = getattr(module, "update_source", None)
    if not func:
        raise Exception(f"Source type {source_type} does not have required function : update_source")
    if asyncio.iscoroutinefunction(func):
        result = await func(current_user, source_id, name, is_private, description, connection_info, additional_details, entities)
    else:
        result = func(current_user, source_id, name, is_private, description, connection_info, additional_details, entities)
    return result


async def detect_relationships(context: ModuleContext, source_type: str, source_id : int, approach: DetectApproach = DetectApproach.NAME_BASED):
    if source_type not in context.get_registry():
        raise Exception(f"Source type {source_type} not found")
    module = context.get_registry()[source_type]
    func = getattr(module, "detect_relationships", None)
    if not func:
        raise Exception(f"Source type {source_type} does not have required function : detect_relationships")
    if asyncio.iscoroutinefunction(func):
        result = await func(source_id, approach)
    else:
        result = func(source_id, approach)
    return result


async def embedding(context: ModuleContext, source_type: str, source_id: int):
    if source_type not in context.get_registry():
        raise Exception(f"Source type {source_type} not found")
    module = context.get_registry()[source_type]
    func = getattr(module, "embedding", None)
    if not func:
        raise Exception(f"Source type {source_type} does not have required function : embedding")
    if asyncio.iscoroutinefunction(func):
        result = await func(source_id)
    else:
        result = func(source_id)
    return result


async def preview_data(context: ModuleContext, source_type: str, source_id: int, entity_name: dict, limit: int = 50):
    if source_type not in context.get_registry():
        raise Exception(f"Source type {source_type} not found")
    module = context.get_registry()[source_type]
    func = getattr(module, "preview_data", None)
    if not func:
        raise Exception(f"Source type {source_type} does not have required function : preview_data")
    if asyncio.iscoroutinefunction(func):
        result = await func(source_id, entity_name, limit)
    else:
        result = func(source_id, entity_name, limit)
    return result
