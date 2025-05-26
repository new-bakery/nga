from bson import ObjectId
import copy
import json
import re



def doc_encoder(value):
    if isinstance(value, dict):
        # 如果字典中有 _id 并且 _id 是 ObjectId 类型，转换为字符串
        if "_id" in value and isinstance(value["_id"], ObjectId):
            value["_id"] = str(value["_id"])
        # # 递归处理字典内部的 _id
        # for key, val in value.items():
        #     if isinstance(val, dict):
        #         value[key] = doc_dict_encoder(val)  # 递归调用
    return value


def copy_without_control_keys(json_data, is_control_key=lambda key: key.startswith('_')):
    def _remove_control_keys(data):
        if isinstance(data, dict):
            keys_to_remove = [key for key in data if is_control_key(key)]
            for key in keys_to_remove:
                del data[key]
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    _remove_control_keys(value)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    _remove_control_keys(item)
        return data

    json_data_copy = copy.deepcopy(json_data)
    return _remove_control_keys(json_data_copy)


# This is used for extracting JSON data from the LLM output
def get_json(text):
    match = re.search(r'```json(.*?)```', text, re.DOTALL)
    if match:
        json_data = match.group(1).strip()
        try:
            data = eval(json_data)
            return data
        except json.JSONDecodeError:
            raise
        except NameError:
            json_data = json_data.replace("null", '"null"')
            return eval(json_data)
    else:
        try:
            data = eval(text)
            return data
        except:
            raise