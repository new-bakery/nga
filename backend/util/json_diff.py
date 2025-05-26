import logging
import jsondiff
from jsondiff import symbols

def _apply_diff(diffs, target, parent_key=None, logger=None, **kwargs):
    allowed_update_keys = kwargs.get("allowed_update_keys", [])
    allowed_delete_keys = kwargs.get("allowed_delete_keys", [])
    
    if not allowed_update_keys or len(allowed_update_keys) == 0:
        raise ValueError("allowed_update_keys must be a non-empty list")
    if not allowed_delete_keys or len(allowed_delete_keys) == 0:
        raise ValueError("allowed_delete_keys must be a non-empty list")
    
    logger = logger or logging.getLogger(__name__)
    for key, value in diffs.items():
        if key == symbols.insert:
            if isinstance(target, list): # INSERT IS ALL ALLOWED
                for index, element in value: # value is a list of tuple (index, value)
                    logger.info(f'insert {element} at index {index}')
                    target.insert(index, element)
            elif isinstance(target, dict):
                for field, field_value in value.items():
                    logger.info(f'insert(set) {field} to {field_value}')
                    target[field] = field_value
        elif key == symbols.delete: # ONLY ALLOW DELETE ON TABLES AND COLUMNS
            if isinstance(target, list):
                for index in sorted(value, reverse=True):
                    if parent_key and parent_key in allowed_delete_keys: 
                        logger.info(f'delete {index} from {parent_key}')
                        target.pop(index)
            elif isinstance(target, dict):
                for field in value:
                    if field in target:
                        # del target[field]
                        pass # NOT ALLOWED
        elif key == symbols.update: # IF NOT UPDATING DESCRIPTION, LANG, TEXT, DOMAINS, TAGS, ITS OK
            if isinstance(target, list):
                for index, element_diff in value.items():
                    if isinstance(element_diff, dict):
                        _apply_diff(element_diff, target[index], index, logger, **kwargs)
                    else:
                        # target[index] = element_diff
                        pass # NOT ALLOWED
            elif isinstance(target, dict):
                for field, field_diff in value.items():
                    if isinstance(field_diff, dict):
                        if field not in target:
                            target[field] = {}
                        _apply_diff(field_diff, target[field], field, logger, **kwargs)
                    else:
                        if field not in allowed_update_keys: # ONLY THESE ARE NOT ALLOWED
                            logger.info(f'set {field} to {field_diff}')
                            target[field] = field_diff
        else:
            if isinstance(value, dict):
                if isinstance(target, dict) and key not in target:
                    target[key] = {}
                if isinstance(target,dict):
                    _apply_diff(value, target[key], key, logger, **kwargs)
                elif isinstance(target, list):
                    _apply_diff(value, target[int(key)], key, logger, **kwargs)
            else:
                if isinstance(target, dict):
                    if key not in allowed_update_keys: # IF NOT UPDATING DESCRIPTION, LANG, TEXT, DOMAINS, TAGS, ITS OK
                        logger.info(f'set {key} to {value}')
                        target[key] = value
                elif isinstance(target, list):
                    # target[int(key)] = value
                    pass # NOT ALLOWED



# Before do jsondiff, we need convert list items to dict. Otherwise, sometimes the sort of the list will be different and cause trouble.
def convert_list_to_dict(data: dict, pkeys: list[str]):
    if not pkeys or len(pkeys) == 0:
        raise ValueError("pkeys cannot be empty")
    for key in data:
        if isinstance(data[key], list):
            for pkey in pkeys:
                if all([isinstance(item, dict) and (pkey in item.keys()) for item in data[key]]):
                    data[key] = {item[pkey]: item for item in data[key]}
                    for item in data[key].values():
                        convert_list_to_dict(item, pkeys)
                    break
                

# After the process (merge), I need to convert the dict back to list. 
def convert_dict_to_list(data: dict, pkeys: list[str]):
    if not pkeys or len(pkeys) == 0:
        raise ValueError("pkeys cannot be empty")
    for key in data:
        if isinstance(data[key], dict):
            for pkey in pkeys:
                if all([isinstance(item, dict) and (pkey in item.keys()) for item in data[key].values()]):
                    data[key] = list(data[key].values())
                    for item in data[key]:
                        convert_dict_to_list(item, pkeys)
                    break
                

def apply_changes(existing, modified, options: dict, logger: logging.Logger):
    """
    {
        "primary_keys" : ["table_name", "column_name", "foreign_key_name", "lang"],
        "allowed_update_keys" : ["description", "lang", ""text", "domains", "tags" ],
        "allowed_delete_keys" : ["tables", "columns"],
    }
    """
    def _get_required_option(key):
        if key in options.keys():
            return options[key]
        else:
            raise Exception(f"Missing required option \"{key}\"")
    
    primary_keys = _get_required_option('primary_keys')
    allowed_update_keys = _get_required_option('allowed_update_keys')
    allowed_delete_keys = _get_required_option('allowed_delete_keys')
    
    convert_list_to_dict(existing, pkeys=primary_keys)
    convert_list_to_dict(modified, pkeys=primary_keys)
    diffs = jsondiff.diff(existing, modified, syntax='explicit')
    _apply_diff(diffs, existing, logger=logger, allowed_update_keys = allowed_update_keys, allowed_delete_keys = allowed_delete_keys)
    convert_dict_to_list(existing, pkeys=primary_keys)
    convert_dict_to_list(modified, pkeys=primary_keys)
    
    