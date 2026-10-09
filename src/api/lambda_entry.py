"""AWS Lambda entry point: the same FastAPI app, behind API Gateway. Used by template.yaml.

Each Lambda starts with an empty /tmp, so Cedar would know no principals. With
KK_SEED_ON_COLD_START=1 (set in template.yaml for the demo) the cold start loads
the same synthetic sample world as `make seed`.
"""

import os

from mangum import Mangum

from api.app import app, get_store
from ledger.world import load_world, sample_world
from policy import directory

if os.getenv("KK_SEED_ON_COLD_START") == "1":
    store = get_store()
    if not store.list_actors():
        load_world(store, sample_world())
        directory.refresh()

handler = Mangum(app, lifespan="off")
