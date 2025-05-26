import logging
from bson import ObjectId
from itertools import groupby
import networkx as nx
from networkx.readwrite import json_graph
from celery import Celery, shared_task, current_app
from celery.exceptions import MaxRetriesExceededError
import asyncio

from source_types._relationships import DetectApproach,  calculate_relationships, encode_minhash, minhash_signature
from ._shared import update_source_status
from database import get_pgdb, get_mgdb
from config import config
from celery_app import worker

logger = logging.getLogger()



@shared_task(bind=True)
def task_detect_relationships(self, prev, source_id : int, approach: str):
    loop = asyncio.get_event_loop()
    try:
        return loop.run_until_complete(run_task_detect_relationships(source_id, approach))
    except Exception as ex:
        logger.error(ex)
        raise


async def run_task_detect_relationships(source_id : int, approach: str):
    approach = DetectApproach(approach)
    try:
        db_source = await update_source_status(source_id, {"detect_relationships": {"status": "running"} })
        doc_id = db_source.doc_id
        if not doc_id:
            raise Exception("Failed to fetch source data")
        async for mgdb in get_mgdb():
            schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
            doc = await schema_collection.find_one({"_id": ObjectId(doc_id)})
        if not doc:
            raise Exception("Failed to fetch source doc")
        connection_info = doc.get('connection', {})
        table_schemas = doc.get('tables', [])        
        if approach in [DetectApproach.SIGNATURE_BASED, DetectApproach.NAME_AND_SIGNATURE_BASED]:
            if db_source.status.get("calculate_signatures", "") != "done": # NOTICE, we used status here !
                raise Exception("signatures are not calculated")
        logger.info(f'calculating relationships with by approach {approach.value}')
        relationships = calculate_relationships(table_schemas, approach, config.SIGNATURE_THRESHOLD, config.NAME_TYPE_THRESHOLD)
        relationships.sort(key=lambda x: x["primary_table"])
        # TODO: we need check if the foreign key data are set to primary table ? Or should be foreign table ?
        grouped_relationships = {k: list(v) for k, v in groupby(relationships, key=lambda x: x["primary_table"])}
        for table_schema in table_schemas:
            if "foreign_keys" not in table_schema:
                table_schema["foreign_keys"] = []
            table_schema["foreign_keys"].extend(grouped_relationships.get(table_schema["table_name"], []))
        logger.info('building graph')
        await build_graph(doc)
        async for mgdb in get_mgdb():
            schema_collection = mgdb[config.SCHEMA_COLLECTION_NAME]
            doc = await schema_collection.update_one({"_id": ObjectId(doc_id)}, {'$set': doc})
        await update_source_status(source_id, {"detect_relationships": {"status": "done"} })
    except Exception as ex:
        await update_source_status(source_id,  {"detect_relationships": {"status": "failed", "error": str(ex) } })
        logger.error(ex)
        raise
    
    

async def build_graph(doc):
    G = nx.Graph()
    for table in doc["tables"]:
        G.add_node(table["table_name"])

    for table in doc["tables"]:
        for foreign_key in table["foreign_keys"]:
            primary_table = foreign_key["primary_table"]
            foreign_table = foreign_key["foreign_table"]
            by = foreign_key["by"] if "by" in foreign_key else "design"
            G.add_edge(primary_table, foreign_table, by=by)

    graph_data = json_graph.node_link_data(G, edges="edges")
    # We do NOT care its existed or not, we just update it
    doc["_graph"] = graph_data
