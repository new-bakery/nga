from enum import Enum
import base64
import numpy as np
from datasketch import MinHash
import Levenshtein as lev
import rapidfuzz.fuzz as fuzz

class DetectApproach(Enum):
    NAME_BASED = "name_based"
    SIGNATURE_BASED = "signature_based"
    NAME_AND_SIGNATURE_BASED = "name_and_signature_based"


def minhash_signature(values, num_perm=128):
    m = MinHash(num_perm=num_perm)
    for value in set(values):
        m.update(str(value).encode('utf8'))
    return m


def encode_minhash(obj):
    """
    json.dumps(schema, indent=indent, default=encode_minhash)
    """
    if isinstance(obj, MinHash):
        hashvalues_bytes = obj.hashvalues.tobytes()  
        base64_str = base64.b64encode(hashvalues_bytes).decode('utf-8')  
        return {
            "_type": "MinHash",
            "num_perm": obj.num_perm,
            "hashvalues": base64_str
        }
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def decode_minhash(obj):
    """
    json.loads(schema_json, object_hook=decode_minhash)
    """
    if "_type" in obj and obj["_type"] == "MinHash":
        hashvalues_bytes = base64.b64decode(obj["hashvalues"]) 
        minhash = MinHash(num_perm=obj["num_perm"])
        minhash.hashvalues = np.frombuffer(hashvalues_bytes, dtype=np.uint64) 
        return minhash
    return obj  


def compare_column_name_type(table1_schema: dict, column1_schema:dict, table2_schema: dict, column2_schema:dict, threshold=0.6):
    column1_full_name = f"{table1_schema["table_name"]}.{column1_schema["column_name"]}"
    column2_full_name = f"{table2_schema["table_name"]}.{column2_schema["column_name"]}"

    column1_type = column1_schema["type"]
    column2_type = column2_schema["type"]

    ratio = lev.ratio # This is from 0 - 1
    # ratio = lambda x, y: fuzz.ratio(x, y) / 100.0  #  # fuzz.ratio is from 0 - 100, if you want to change, uncomment this line

    name_similarity = ratio(column1_full_name, column2_full_name)
    type_match = 1.0 if column1_type == column2_type else 0.0

    # If the type does not match, it means it is not a match
    return type_match * name_similarity >= threshold  



def calculate_relationships(table_schemas, approach: DetectApproach, signature_threshold = 0.8, name_type_threshold = 0.6):

    if approach in [DetectApproach.SIGNATURE_BASED, DetectApproach.NAME_AND_SIGNATURE_BASED]:
        # try to cache the signature so that we can speed up
        _signature_cache = {}
        def _decode_signature(table_name: str, column_name: str, signature : dict):
            if (table_name, column_name) in _signature_cache:
                return _signature_cache[(table_name, column_name)]
            else:
                _signature_cache[(table_name, column_name)] = decode_minhash(signature)
                return _signature_cache[(table_name, column_name)]

    # These are existing relationships
    existing = {}
    for table in table_schemas:
        if "foreign_keys" in table:
            for foreign_key in table["foreign_keys"]:
                primary_table = foreign_key["primary_table"]
                foreign_table = foreign_key["foreign_table"]
                existing[primary_table] = foreign_table
                existing[foreign_table] = primary_table

    relationships = []

    # if we have shape, we can sort the tables, no shape, treat as 0,0
    table_schemas.sort(key=lambda x: x["shape"] if "shape" in x else [0, 0], reverse=True) # more data (shape), usually primary table
    
    for i, table1_schema in enumerate(table_schemas):
        columns1 = table1_schema["columns"]
        table1_name = table1_schema["table_name"]
        for column1_schema in columns1:
            column1_name = column1_schema["column_name"]
            for j, table2_schema in enumerate(table_schemas):
                if j <= i: # skip the same table or previous tables
                    continue
                columns2 = table2_schema["columns"]
                table2_name = table2_schema["table_name"]
                # relationship already existed, skip
                if table1_name in existing and existing[table1_name] == table2_name:
                    continue
                for column2_schema in columns2:
                    column2_name = column2_schema["column_name"]
                    s1 = False
                    s2 = False
                    if approach in [DetectApproach.NAME_BASED, DetectApproach.NAME_AND_SIGNATURE_BASED]:
                        s1 = compare_column_name_type(table1_schema, column1_schema, table2_schema, column2_schema, name_type_threshold)
                    if approach in [DetectApproach.SIGNATURE_BASED, DetectApproach.NAME_AND_SIGNATURE_BASED]:
                        if "_signature" in column1_schema and "_signature" in column2_schema:
                            sig1 = _decode_signature(table1_name, column1_name, column1_schema["_signature"])
                            sig2 = _decode_signature(table2_name, column2_name, column2_schema["_signature"])
                            s2 = sig1.jaccard(sig2) >= signature_threshold
                        else:
                            s2 = False # No way to get the signature for the combination
                    if (approach == DetectApproach.NAME_BASED and s1) or \
                        (approach == DetectApproach.SIGNATURE_BASED and s2) or \
                        (approach == DetectApproach.NAME_AND_SIGNATURE_BASED and s1 and s2):
                            relationships.append({
                                "foreign_key_name": f'{table1_name}.{column1_name} <-> {table2_name}.{column2_name}',
                                "primary_table": table1_name,
                                "primary_column": column1_name,
                                "foreign_table": table2_name,
                                "foreign_column": column2_name,
                                "by": approach.value,
                            })
    return relationships

