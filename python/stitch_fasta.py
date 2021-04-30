"""
Combine individual alignments into a composite FASTA file

Author:
    Sergei L Kosakovsky Pond (spond@temple.edu)

Version:
    v0.0.1 (2020-05-02)


"""

import argparse
import sys
import json
import re
import datetime
import os
import math, csv
from   os import  path
import operator
import compress_json
import mappy
from progress.bar import Bar

from   Bio import SeqIO


from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

arguments = argparse.ArgumentParser(description='Combine alignments into a single file, adding a reference sequence as well')

arguments.add_argument('-d', '--dir',          help = 'Directory with files',                   required = True, type = str )
arguments.add_argument('-o', '--output',       help = 'Write the file to',                      required = True, type = argparse.FileType('w'))
arguments.add_argument('-x', '--extras',       help = 'Insert additional sequences',            required = False, type = argparse.FileType('r'))
arguments.add_argument('-r', '--reference',    help = 'Reference sequence index',            required = True, type = str)
arguments.add_argument('-c', '--cutoff',       help = 'Only report variants reaching this count (if >= 1 or frequency if in [0-1])', required = False, type = float, default = 5)
arguments.add_argument('-m', '--map',          help = 'EPI ID => UID map',            required = True, type = str)
arguments.add_argument('-D', '--deletions',          help = 'Include deletions',            required = False, action = 'store_true')
arguments.add_argument('--sequence_pattern',          help = 'File name pattern for sequence files',            required = False, type = str, default = ".%s.compressed.fas")
arguments.add_argument('--duplicate_pattern',          help = 'File name pattern for duplicate lists',            required = False, type = str, default = '.%s.duplicates.json.gz')

genes = ['leader','nsp2','nsp3','nsp4','3C','nsp6','nsp7','nsp8','nsp9','nsp10','RdRp','helicase','exonuclease','endornase','methyltransferase','S','ORF3a','E','M','ORF6','ORF7a','ORF8','N','ORF10']
#genes = ['N']

def load_json_or_compressed (file_name):
    if file_name.find (".json") + 5 == len(file_name):
        with open (file_name, "r") as file_object:
            return json.load (file_object)
    else:
        return compress_json.load (file_name)

def pad_sequence (s, insert_gap):
    seq = []
    si = 0
    for k in insert_gap:
        if k:
            seq.append ('-')
        else:
            seq.append (s[si])
            si += 1 
            
    return ''.join (seq)


import_settings = arguments.parse_args()

combined_fasta = {}


'''
#compute alignment consensus
'''

extras = []

if import_settings.extras:
    for seq_record in SeqIO.parse(import_settings.extras, "fasta"):
        extras.append (seq_record)
        
consensus_strikes = []

nucs = set ('ACGT')
        
def consensus_filter (the_items, pos):
    c = sorted (the_items.items(), key=operator.itemgetter(1), reverse = True)
    best = '-'
    for res in c:
        if res[0] in nucs:
            if res[1] * 1000 > len (combined_fasta):
                best = res[0]
                break
    
    if best == '-':
        consensus_strikes.append (pos)
        return ''
    return best

mapper_r = load_json_or_compressed (import_settings.map)
mapper = {}
for i, id in enumerate (mapper_r):
    mapper [id.split ('_')[2]] = i

consensus = []
ci = 0

def extract_id (seq_id):
    parts = seq_id.upper().split ('/')
    parts = parts[0].upper().split ('_')
    if len(parts) == 1:
        return seq_id
    epi = parts.index ('EPI')
    return parts[epi+2]    

for i, gene in enumerate (genes):
    local_set = {}
    

    try:
        dups_file = "".join ([import_settings.dir, import_settings.duplicate_pattern % gene])
        dups_raw = load_json_or_compressed (dups_file)
        dups = {}
        for id, dup_list in dups_raw.items():
            idc = mapper[extract_id(id)]
            dups[idc] = [mapper[extract_id(k)] for ignore,k in dup_list.items()]
            dups[idc].append (idc)
        
    except FileNotFoundError as e:
        print ("Not found %s" % dups_file, file = sys.stderr)
        continue   
        
         
    count = 0
    
    for seq_record in SeqIO.parse(open ("".join ([import_settings.dir, import_settings.sequence_pattern % gene]), "r"), "fasta"):
        seq_id   = seq_record.name
        seq = str (seq_record.seq).upper()
        no_count = mapper[extract_id (seq_id)]
        local_set [no_count] = seq
        _copy_count = len (dups[no_count])
        count += _copy_count
        #print (dups[seq_id], file = sys.stderr)
        for i,dup_id_clean in  enumerate(dups[no_count]):
            #dup_id_clean = mapper[extract_id(dup_id)]
            if dup_id_clean != seq_id:
                local_set [dup_id_clean] = seq       
    
        if ci == len (consensus):
            for l in enumerate (seq):
                consensus.append ({})
            #consensus = [{} for l in enumerate (seq)]
            
        for i,l in enumerate (seq):
            if l not in consensus[ci+i]:
                consensus[ci+i][l] = _copy_count
            else:
                consensus[ci+i][l] += _copy_count
       # break
    #print (local_set)
            
    ci = len (consensus)

    if len (combined_fasta):
        to_delete = set ()
        for i in combined_fasta:
            if i in local_set:
                combined_fasta[i] += local_set[i]
            else:
                to_delete.add (i)
            
        for i in to_delete:
            del combined_fasta[i]
            
    else:
        for i,s in local_set.items():
            combined_fasta[i] = s

    print (gene, len (combined_fasta), count, file = sys.stderr)
 
ref_seq = ''.join ([consensus_filter(d, pos) for pos,d in enumerate(consensus)])

if len (consensus_strikes):

    stencil = []
    with Bar('Striking %d poor quality variants from sequences' % len (consensus_strikes), max=len (combined_fasta)) as bar:
        for k in combined_fasta:
            seq = combined_fasta[k]
            if len (stencil) == 0:
                stencil = [True for k in range(len (seq))]
                for z in consensus_strikes:
                    stencil [z] = False
                
            #print (len (stencil), len (seq))        
            combined_fasta[k] = ''.join([seq[i] for i,c in enumerate(stencil) if c])
            bar.next()

aligner     = mappy.Aligner (import_settings.reference, preset = "asm5")
genome      = aligner.seq (aligner.seq_names[0])
ref_seq_output  = []

ref = 0
qry = 0

summary_json    = {
                        'reference_base' : [],
                        'sequences' : {}
                  }
                  
aligner_segments = sorted (list (aligner.map (ref_seq)), key=lambda x: x.r_st)          
       

for i, segment in enumerate (aligner_segments):
    print (ref, qry, segment.r_st , segment.q_st, segment.r_en, segment.q_en)
    while ref < segment.r_st :
        summary_json['reference_base'].append (genome[ref])
        ref += 1
    while qry < segment.q_st:
        #ref_seq_output.append ([-1,'-'])
        ref_seq_output.append ([-ref-1,'-'])
        qry += 1
    
    if i > 0:
        print (genome[last_endr:segment.r_st])
        print (ref_seq[last_endq:segment.q_st])
        
    last_endq =      segment.q_en   
    last_endr =      segment.r_en   
          
    for op in segment.cigar:
        if op[1] == 0: # matched    
            for i in range (op[0]):
                #print (genome[ref],":",ref_seq[qry])
                ref_seq_output.append ([ref,genome[ref]])
                summary_json['reference_base'].append (genome[ref])
                ref+=1
                qry+=1
        elif op[1] == 1: #insertion
            for i in range (op[0]):
                #print ("-:",ref_seq[qry])
                ref_seq_output.append ([-ref-1,'-'])
                qry+=1
        elif op[1] == 2: #deletion
            for i in range (op[0]):
                #ref_seq_output.append ([ref,genome[ref]])
                summary_json['reference_base'].append (genome[ref])
                #print (genome[ref],":-")
                ref+=1
                

for i in range (qry, len (ref_seq)): #tail end of the consensus did not map to anything
    ref_seq_output.append ([-ref-1,'-'])
    
current_strike = 0

variant_counts  = {}
sequence_count  = 0

with Bar('Calling variants in sequences', max=len (combined_fasta)) as bar:
    for seq_id, seq in combined_fasta.items ():

        seq = seq.upper()
        sequence_count += 1
        if import_settings.deletions:
            summary_json ['sequences'][seq_id] = [(ref_seq_output[k][0],seq[k]) for k in range (len (seq)) if ref_seq_output[k][0]>=0 and ref_seq_output[k][1] != seq[k]]
        else:
            summary_json ['sequences'][seq_id] = [(ref_seq_output[k][0],seq[k]) for k in range (len (seq)) if ref_seq_output[k][0]>=0 and ref_seq_output[k][1] != seq[k] and seq[k] != '-']
    
        for variant in summary_json ['sequences'][seq_id]:
            if not variant in variant_counts:
                variant_counts [variant] = 0
            variant_counts [variant] += 1
    
        bar.next()
        #print (seq_id, summary_json ['sequences'] [seq_id], file = sys.stderr)

if import_settings.cutoff < 1.:
    import_settings.cutoff *= sequence_count
    
accepted_variants = {}
for v,c in variant_counts.items():
    if c >= import_settings.cutoff:
        accepted_variants[v] = c
        

summary_json['variants'] = [[k[0],k[1],c] for k, c in accepted_variants.items()]
        
filtered_variants = {}
for s, variants in summary_json ['sequences'].items():
    filtered_variants[s] = [l for k in variants if k in accepted_variants for l in k]
    
summary_json ['sequences'] = filtered_variants

json.dump (summary_json, import_settings.output, indent = 1)





