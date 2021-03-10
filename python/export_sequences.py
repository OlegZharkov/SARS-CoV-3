# -*- coding: utf-8 -*-

import csv
import json
import sys
import argparse
import itertools
import shutil
import copy
import os
import multiprocessing
import unicodedata
from multiprocessing import Pool
from datetime import date, timedelta
from operator import itemgetter
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

import pymongo
from pymongo import MongoClient

def sequence_name(record):
    #hCoV-19/England/20102000906/2020
    def value_or_null (v):
        if v is not None:
            if(isinstance(v, date)):
                return v.strftime('%Y-%m-%d')
            else:
                return v.split (" ")[0]
        return "null"
    def location (v):
        for k in ['state','country','subregion']:
            if v['location'][k]:
                return v['location'][k].replace (' ', '_')

    if('originalCollected' in record.keys()):
        fields = [record['id'], location(record), value_or_null(record['originalCollected']), value_or_null(record['technology'])]
    else:
        fields = [record['id'], location(record), value_or_null(record['collected']), value_or_null(record['technology'])]

    return unicodedata.normalize('NFKD', "/".join (fields))

def export_sequences(config):

    db = MongoClient(host='192.168.0.4')

    acceptable = ['collected', 'originalCollected', 'host', 'id', 'location', 'name', 'technology', 'type', 'nextstrainClade', 'pangolinLineage', 'gisaidClade', 'seq']
    HOST= "Human"
    MINLENGTH=28000

    mongo_query = { "host" : HOST,  "length": {"$gt": MINLENGTH }, "seq": {"$exists":True} }

    output_fn = config["sequence-output"]

    if("clade-type" in config.keys()):
        clade_type = config["clade-type"]
    else:
        clade_type = "pangolinLineage"

    if("clades" in config.keys()):
        # db.inventory.find ( { quantity: { $in: [20, 50] } } )
        mongo_query[clade_type] = { "$in": config["clades"] }
    elif("ignore-clades" in config.keys()):
        mongo_query[clade_type] = { "$nin": config["ignore-clades"] }

    # Query for human host and sequence length greater than 28000, and sequence populated

    # LIMIT=100000
    # LIMIT=10
    records = list(db.gisaid.records.find(mongo_query))
    seq_records = [SeqRecord(Seq(rec["seq"]),id=sequence_name(rec),name='',description='') for rec in records]

    # Write to fasta
    with open(output_fn, 'w', encoding='utf-8') as output_fh:
        SeqIO.write(seq_records, output_fh, "fasta")

def export_premsa_sequences(config, nuc_output_fn, prot_output_fn, gene):
    '''
    config
    nuc_output_fn -- nucleotide output filename
    protein_output_fn -- protein output filename
    gene -- 'region of SARS-CoV-2
    '''

    db = MongoClient(host='192.168.0.4')

    acceptable = ['collected', 'originalCollected', 'host', 'id', 'location', 'name', 'technology', 'type', 'nextstrainClade', 'pangolinLineage', 'gisaidClade']
    HOST= "Human"
    MINLENGTH=28000
    key_to_export = ''

    # Get QC key
    validation_key = 'qc.' + gene + '.passed'
    not_duplicate_key = 'qc.' + gene + '.duplicate_of'
    not_duplicate_val = {"$exists":False}

    second_duplicate_key = 'duplicate_of_by_gene.' + gene
    second_duplicate_val = [{second_duplicate_key:{"$exists":False}},{second_duplicate_key:'reference'}]

    nuc_key_to_export = gene + '_premsa_nuc_seq'
    prot_key_to_export = gene + '_premsa_protein_seq'

    acceptable.extend([nuc_key_to_export, prot_key_to_export])
    mongo_query = { "host" : HOST,  validation_key: True, not_duplicate_key : not_duplicate_val, "$or": second_duplicate_val}

    if("clade-type" in config.keys()):
        clade_type = config["clade-type"]
    else:
        clade_type = "pangolinLineage"

    if("clades" in config.keys()):
        # db.inventory.find ( { quantity: { $in: [20, 50] } } )
        mongo_query[clade_type] = { "$in": config["clades"] }
    elif("ignore-clades" in config.keys()):
        mongo_query[clade_type] = { "$nin": config["ignore-clades"] }

    # Query for human host and sequence length greater than 28000, and sequence populated

    # LIMIT=100000
    # LIMIT=10
    records = list(db.gisaid.records.find(mongo_query))

    # Filter sequences down to those that have been processed
    recs_with_nucs = filter(lambda x: nuc_key_to_export in x.keys(), records)
    nuc_seq_records = [ SeqRecord(Seq(rec[nuc_key_to_export]),id=sequence_name(rec),name='',description='') for rec in recs_with_nucs ]

    recs_with_prot = filter(lambda x: prot_key_to_export in x.keys(), records)
    prot_seq_records = [SeqRecord(Seq(rec[prot_key_to_export]),id=sequence_name(rec),name='',description='') for rec in recs_with_prot]

    # Write to fasta
    with open(nuc_output_fn, 'w', encoding='utf-8') as nuc_output_fh:
        SeqIO.write(nuc_seq_records, nuc_output_fh, "fasta")

    # Write to fasta
    with open(prot_output_fn, 'w', encoding='utf-8') as nuc_output_fh:
        SeqIO.write(prot_seq_records, nuc_output_fh, "fasta")

def export_postmsa_sequences(config, output_fn, gene):
    '''
    config
    output_fn = output filename
    gene -- 'region of SARS-CoV-2
    '''

    db = MongoClient(host='192.168.0.4')

    acceptable = ['collected', 'originalCollected', 'host', 'id', 'location', 'name', 'technology', 'type', 'nextstrainClade', 'pangolinLineage', 'gisaidClade']
    HOST= "Human"
    MINLENGTH=28000
    key_to_export = ''

    duplicate_key = 'duplicate_of_by_gene.' + gene
    duplicate_val = [ {duplicate_key:{"$exists":False}}, {duplicate_key:'reference'} ]

    key_to_export = ".".join(["reference_alignment", gene])

    acceptable.extend([key_to_export])
    mongo_query = { "host" : HOST,  key_to_export : {"$exists": True }, "$or": duplicate_val}

    if("clade-type" in config.keys()):
        clade_type = config["clade-type"]
    else:
        clade_type = "pangolinLineage"

    if("clades" in config.keys()):
        mongo_query[clade_type] = { "$in": config["clades"] }
    elif("ignore-clades" in config.keys()):
        mongo_query[clade_type] = { "$nin": config["ignore-clades"] }

    # Query for human host and sequence length greater than 28000, and sequence populated
    records = list(db.gisaid.records.find(mongo_query))

    # Filter sequences down to those that have been processed
    seq_records = [SeqRecord(Seq(rec["reference_alignment"][gene]),id=sequence_name(rec),name='',description='') for rec in records]

    # Write to fasta
    with open(output_fn, 'w', encoding='utf-8') as output_fh:
        SeqIO.write(seq_records, output_fh, "fasta")


if __name__ == "__main__":

    # arguments = argparse.ArgumentParser(description='Report which dates have full report')
    # arguments.add_argument('-o', '--output',   help = 'fasta output', type = str)
    # args = arguments.parse_args()
    # config = {"sequence-output" : args.output }
    # config["clades"] = ["B.1.351", "P.1"]
    # config["ignore-clades"] = ["B.1.351", "P.1", "B.1.1.7"]
    # config["clade-type"] = "pangolinLineage"
    # export_sequences(config)

    config = {}
    #export_premsa_sequences(config, 'nuc.fas', 'prot.fas', '3C')
    export_postmsa_sequences(config, 'aligned.fas', '3C')


