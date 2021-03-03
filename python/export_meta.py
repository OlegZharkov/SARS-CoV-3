import csv
import json
import sys
import argparse
import itertools
import shutil
import copy
import os
import multiprocessing
from multiprocessing import Pool
from datetime import date, timedelta
from operator import itemgetter
from Bio import SeqIO

import pymongo
from pymongo import MongoClient

def export_meta(config):

    db = MongoClient(host='192.168.0.4')
    acceptable = ['address', 'genbank_accession', 'age', 'assembly', 'authors', 'originalCollected', 'coverage', 'length', 'gender', 'sex', 'host', 'id', 'lab', 'originating_lab', 'location', 'name', 'passage', 'seqLength', 'originalSubmitted', 'submitter', 'submitting_lab', 'technology', 'type', 'nextstrainClade', 'pangolinLineage', 'gisaidClade']

    # transform acceptable into mongo query
    acceptable_dict = { k: 1 for k in acceptable}

    output_fn = config["meta-output"]
    mongo_query = {}

    if("clade-type" in config.keys()):
        clade_type = config["clade-type"]
    else:
        clade_type = "pangolinLineage"

    if("clades" in config.keys()):
        # db.inventory.find ( { quantity: { $in: [20, 50] } } )
        mongo_query[clade_type] = { "$in": config["clades"] }
    elif("ignore-clades" in config.keys()):
        mongo_query[clade_type] = { "$nin": config["ignore-clades"] }

    records = list(db.gisaid.records.find(mongo_query, acceptable_dict))

    records = [{k: v for k, v in rec.items() if k in acceptable} for rec in records]
    output_json = { row["id"] : row for row in records }

    # Write attributes.csv file and MASTER-NO-JSON file
    with open(output_fn, 'w') as output_fh:
        json.dump(output_json, output_fh, indent=4, sort_keys=True)

if __name__ == "__main__":
    arguments = argparse.ArgumentParser(description='Report which dates have full report')
    arguments.add_argument('-o', '--output', help = 'json output', type = str)
    args = arguments.parse_args()
    config = {"meta-output" : args.output }
    # config["clades"] = ["B.1.351", "P.1"]
    # config["ignore-clades"] = ["B.1.351", "P.1", "B.1.1.7"]
    # config["clade-type"] = "pangolinLineage"
    export_meta(config)
