import os
import tempfile
import zipfile
import logging
import importlib
import importlib.util
import inspect

from typing import Dict, Any, List
from types import ModuleType

NAME = "name"
ANNOTATION = "annotation"
KIND = "kind"


class ModuleRegistry:
    def __init__(self):
        self._modules = {}

    def register(self, name, module):
        self._modules[name] = module
        return module

    def get(self, name):
        return self._modules.get(name, None)
    
    def __getitem__(self, name):
        return self._modules[name]

    def __contains__(self, name):
        return name in self._modules

    def keys(self):
        return self._modules.keys()

    def values(self):
        return self._modules.values()

    def items(self):
        return self._modules.items()
    

class ModuleContext:

    def __init__(self, name : str, registry : ModuleRegistry , logger : logging.Logger):
        self._name = name
        self._data = {}
        self._registry = registry
        self._logger = logger

    def get_registry(self) -> ModuleRegistry:
        return self._registry

    def get_logger(self) -> logging.Logger:
        return self._logger
    
    def set_logger(self, logger: logging.Logger):
        self._logger = logger

    def __getattr__(self, item):
        if item in ['debug', 'info', 'warning', 'error', 'critical']:
            return getattr(self._logger, item)
        if item  == 'registry':
            return getattr(self, '_registry')
        if item == 'logger':
            return getattr(self, '_logger')
        if item == 'data':
            return getattr(self, '_data')
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")
    

_on_init_signature = [
    {
        NAME  : None,
        ANNOTATION : [ModuleContext],
        KIND : inspect._ParameterKind.POSITIONAL_OR_KEYWORD,
    },
    {
        NAME  : None,
        ANNOTATION : None,
        KIND :  inspect._ParameterKind.VAR_KEYWORD,
    },
]

_register_signature = [
    {
        NAME  : None,
        ANNOTATION : [ModuleContext],
        KIND : inspect._ParameterKind.POSITIONAL_OR_KEYWORD,
    },
    {
        NAME : None,
        ANNOTATION : [str, Any],
        KIND : inspect._ParameterKind.POSITIONAL_OR_KEYWORD,
    },
    {
        NAME : None,
        ANNOTATION : [ModuleType, Any],
        KIND : inspect._ParameterKind.POSITIONAL_OR_KEYWORD,
    },
    {
        NAME  : None,
        ANNOTATION : None,
        KIND :  inspect._ParameterKind.VAR_KEYWORD,
    },
]


def _check_signature(func : callable, rules : list[dict], check : callable = None) -> bool:
    def __check_rule(value : Any, rule : Any):
        if rule:
            if isinstance(rule, list):
                return value in rule
            return value == rule
        return True
    if not check:
        check = __check_rule
    check_points = [NAME, ANNOTATION, KIND]
    sig = inspect.signature(func)
    parameters = sig.parameters
    if len(parameters) != len(rules):
        return False
    data = []
    for name, parameter in parameters.items():
        data.append(
            {
                NAME: name,
                ANNOTATION : Any if parameter.annotation == inspect._empty else parameter.annotation,
                KIND : parameter.kind
            }
        )
    check_list = zip(data, rules)
    for check_item in check_list:
        for check_point in check_points:
            if not check(check_item[0][check_point], check_item[1][check_point]):
                return False
    return True


def _register_module(context: ModuleContext, package_name : str, name : str, module_path : str, register : callable, logger : logging.Logger, require_init_file : bool =True, **kwargs) -> bool :
    module_name = f'{package_name}.{name}'
    init_file = os.path.join(module_path, '__init__.py')
    module_file = os.path.join(module_path, f'{name}.py') if not require_init_file else init_file
    if require_init_file and not os.path.isfile(init_file):
        return False
    if os.path.isfile(module_file):
        logger.info(f"try registering module \"{name}\"")
        spec = importlib.util.spec_from_file_location(module_name, module_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, 'on_init'):
            init_func = getattr(module, 'on_init')
            if _check_signature(init_func, _on_init_signature):
                init_func(context, **kwargs)
        try:
            if _check_signature(register, _register_signature):
                if register(context, name, module, **kwargs):
                    context.get_registry().register(name, module)
                    return True
                else:
                    return False
            else:
                return False
        except Exception as ex:
            logger.error(str(ex))
            return False
    else:
        return False


def _extract_and_register(context: ModuleContext, zip_path : str, package_name : str, register : callable, logger : logging.Logger, **kwargs):
    with tempfile.TemporaryDirectory() as temp_dir:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            extracted_dir = os.path.join(temp_dir, os.path.splitext(os.path.basename(zip_path))[0])
            if not os.path.exists(extracted_dir): # Sometimes, the zip file do not contains a sub folder
                extracted_dir = temp_dir
            module_name = os.path.splitext(os.path.basename(zip_path))[0]
            if not _register_module(context, package_name, module_name, extracted_dir, register, logger, True, **kwargs):
                logger.warning(f"Failed to register module \"{module_name}\" at {extracted_dir}")



def discover_modules(context: ModuleContext, modules_folder_name : str, package_name : str, register : callable, logger : logging.Logger = None, **kwargs) :
    
    assert modules_folder_name and str.strip(modules_folder_name) != '', 'module_folder_name should be valid and not empty'
    assert package_name and str.strip(package_name) != '' , "package_name should be valid and not empty"
    assert register and callable(register), 'register function should be valid and callable'

    logger = logger or logging.getLogger(__name__)
    modules_path = os.path.join(os.path.dirname(__file__), modules_folder_name)
    logger.info(f"discovering modules from \"{modules_path}\"")
    if os.path.exists(modules_path):
        for dir_name in os.listdir(modules_path):
            if dir_name.startswith('_'):
                # ignore some folders or files (e.g. __init__.py, __pycache__)
                continue
            module_path = os.path.join(modules_path, dir_name)
            if os.path.isdir(module_path):
                # if its a subfolder, it should be a module with __init__.py
                # we will import the module and register the module
                if not _register_module(context, package_name, dir_name, module_path, register, logger, True, **kwargs):
                    logger.warning(f"Failed to register module \"{dir_name}\" at \"{module_path}\"")
            elif dir_name.endswith('.zip'):
                # if its a zip file, we will extract it to a temporary directory
                # and then import the module and register the module
                _extract_and_register(context, module_path, package_name, register, logger, **kwargs)
            elif dir_name.endswith('.py'):
                # if its a python file, we will import the module and register the connector
                module_name = os.path.splitext(dir_name)[0]
                if not _register_module(context, package_name, module_name, modules_path, register, logger, False, **kwargs):
                    logger.warning(f"Failed to register module \"{module_name}\" at \"{modules_path}\" ")
                
