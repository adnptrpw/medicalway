import time

from google.cloud import storage

from bsbi import BSBIIndex
from compression import VBEPostings

storage_client = storage.Client()
bucket = storage_client.bucket("medicalway-be")


def search(request):
    query = request.args.get("query")
    if query is None:
        return "You need to enter a search query to proceed.", 400

    BSBI = BSBIIndex(output_dir='index', postings_encoding=VBEPostings)

    start_time = time.time()
    rank = BSBI.retrieve_bm25(query, k=100, k1=2.75, b=0.75)
    end_time = time.time()

    serp = {}
    serp_length = 0

    for (_, doc) in rank:
        serp_length += 1
        with bucket.blob(doc.replace("\\", "/")).open("r") as file:
            serp[doc.replace("\\", "/")] = file.read()

    return {"duration": end_time - start_time, "serp length": serp_length, "serp": serp}, 200
