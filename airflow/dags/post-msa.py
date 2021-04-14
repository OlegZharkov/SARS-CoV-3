import yaml
import datetime
from datetime import timedelta

# The DAG object; we'll need this to instantiate a DAG
from airflow import DAG

# Operators; we need this to operate!
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator, ShortCircuitOperator
from airflow.utils.dates import days_ago
from airflow.models import Variable

# These args will get passed on to each operator
# You can override them on a per-task basis during operator initialization

from libs.callbacks import task_fail_slack_alert, task_success_slack_alert

import os
import sys
import pathlib
from pathlib import Path

p = os.path.abspath(str(pathlib.Path(__file__).parent.absolute()) + '/../../python/')
if p not in sys.path:
    sys.path.append(p)

from export_sequences_without_premsa import export_sequences, export_sequences_without_reference
from export_sequences import export_postmsa_sequences
from store_premsa import store_premsa_file
from premsa_log_parse import mark_troubled
from mark_premsa_dupes import mark_premsa_dupes
from get_raw_duplicates import write_raw_duplicates
from mark_duplicates import mark_duplicates
from remove_seq import remove_reference_seq, reserve_only_original_input

WORKING_DIR = Variable.get("WORKING_DIR")
DATE_STRING = datetime.date.today().strftime('%Y-%m-%d')

default_args = {
    'owner': 'sweaver',
    'depends_on_past': False,
    'email': ['sweaver@temple.edu'],
    'email_on_failure': False,
    'email_on_retry': False,
    'params' : {
        'working_dir' : WORKING_DIR,
        'num_procs': 16,
        'python': "/data/shares/veg/SARS-CoV-2/SARS-CoV-2-devel/env/bin/python3",
        'hyphy': "/data/shares/veg/SARS-CoV-2/hyphy/hyphy",
        'hyphy_mpi': "/data/shares/veg/SARS-CoV-2/hyphy/HYPHYMPI",
        'hyphy_lib_path': "/data/shares/veg/SARS-CoV-2/hyphy/res",
        'mafft': "/usr/local/bin/mafft",
        'post_msa' : "/data/shares/veg/SARS-CoV-2/hyphy-analyses-devel/codon-msa/post-msa.bf",
        'compressor' : "/data/shares/veg/SARS-CoV-2/SARS-CoV-2-devel/scripts/compressor.bf",
        'compressor2' : "/data/shares/veg/SARS-CoV-2/SARS-CoV-2-devel/scripts/compressor-2.bf",
        'region_cfg' : "/data/shares/veg/SARS-CoV-2/SARS-CoV-2-devel/airflow/libs/regions.yaml",
        'zero_length_flags' : '--kill-zero-lengths Constrain ENV="_DO_TREE_REBALANCE_=1"',
        'date_string': DATE_STRING
    },
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    #'on_failure_callback': task_fail_slack_alert,
    'concurrency': 20,
    'dag_concurrency' : 20,
	'max_active_runs': 1,
    # 'execution_timeout': timedelta(minutes=30),
    # 'queue': 'bash_queue',
    # 'pool': 'backfill',
    # 'priority_weight': 10,
    # 'end_date': datetime(2016, 1, 1),
    # 'wait_for_downstream': False,
    # 'dag': dag,
    # 'sla': timedelta(hours=2),
    # 'on_retry_callback': another_function,
    # 'sla_miss_callback': yet_another_function,
    # 'trigger_rule': 'all_success'
}

dag = DAG(
    'populate_post_msa',
    default_args=default_args,
    description='performs selection analysis',
    schedule_interval='0 8 * * *',
    start_date=days_ago(2),
    tags=['selection'],
)

with open(dag.params["region_cfg"], 'r') as stream:
    regions = yaml.safe_load(stream)

MAFFT = """
{{ params.mafft }} --auto --thread -1 --mapout --addfragments $INPUT_FN $REFERENCE_FILEPATH >| $TMP_OUTPUT_FN
"""

POSTMSA = """
{{ params.hyphy }} LIBPATH={{params.hyphy_lib_path}} {{ params.post_msa }} --protein-msa $INPUT_FN --nucleotide-sequences $NUC_INPUT_FN --output $COMPRESSED_OUTPUT_FN --duplicates $DUPLICATE_OUTPUT_FN
"""

def is_export_populated(filepath):
	return Path(filepath).stat().st_size > 0

post_msa_tasks = []
i = 0

for gene in regions.keys():

    # Reference directory
    reference_filepath = WORKING_DIR + 'reference_genes/reference.' + gene + '_protein.fas'
    filepath_prefix = WORKING_DIR + 'data/postmsa-processor/' + gene + '/sequences.{{ ds }}'
    prealigned_filepath = WORKING_DIR + 'reference_genes/prealigned/sequences.' + gene + '.500.msa'

    filepath = filepath_prefix + '.fasta'
    nuc_filepath = filepath_prefix + '.nuc.fasta'
    stdout = filepath_prefix  + '.stdout.log'
    tmp_output_fn = filepath_prefix + '.tmp.msa'
    output_fn = filepath_prefix + '.msa'
    reference_output_filepath  = filepath_prefix + '.references.fasta'
    compressed_output_filepath =  filepath_prefix + '.compressed.fas'
    duplicate_output_filepath =  filepath_prefix + '.duplicates.json'

    export_missing_task = PythonOperator(
        task_id=f'export_missing_aligned_{gene}',
        python_callable=export_sequences_without_reference,
        op_kwargs={ "gene" : gene, "output_fn" : filepath, "nuc_output_fn" : nuc_filepath },
        dag=dag,
    )

    populated_check_task = ShortCircuitOperator(
        task_id=f'check_if_populated_{gene}',
        python_callable=is_export_populated,
        op_kwargs={ 'filepath': filepath },
        dag=dag
    )

    # References need to be written out in order to mark duplicates. Then
    # duplicates between mark_premsa dupes and raw dupes need to be merged
    # Write references
    write_references_task = PythonOperator(
        task_id=f'write_references_{gene}',
        python_callable=export_postmsa_sequences,
        op_kwargs={ "config" : default_args['params'], "output_fn" : reference_output_filepath, "gene": gene },
        dag=dag,
    )

    mafft_task = BashOperator(
        task_id=f'mafft_{gene}',
        bash_command=MAFFT,
        params={'mafft': default_args['params']['mafft']},
        env={'INPUT_FN': filepath, 'TMP_OUTPUT_FN': tmp_output_fn, 'REFERENCE_FILEPATH': prealigned_filepath},
        dag=dag
    )

    # input_fn, reference_fn, output_fn
    remove_ref_task = PythonOperator(
        task_id=f'remove_ref_{gene}',
        python_callable=reserve_only_original_input,
        op_kwargs={ "input_fn" : tmp_output_fn, "original_fn" : prot_filepath, "output_fn": output_fn },
        dag=dag,
    )

    # Run POST-MSA on cancatenated dataset to translate back to nucleotides
    post_msa_task = BashOperator(
        task_id=f'post_msa_{gene}',
        bash_command=POSTMSA,
        env={'INPUT_FN': output_fn, 'NUC_INPUT_FN': nuc_filepath, 'COMPRESSED_OUTPUT_FN': compressed_output_filepath, 'DUPLICATE_OUTPUT_FN': duplicate_output_filepath, **os.environ},
        dag=dag
    )


    # # Collate and merge references *AFTER* alignment step
    # collate_references_task  = BashOperator(
	#     task_id=f'collate_references_{gene}',
    #     bash_command=COLLATE_REFERENCES,
    #     params={'regions': regions, 'filepath': filepath, 'gene': gene, 'node' : i % 8, 'stdout' : stdout },
    #     dag=dag,
    # )

    # Compute duplicates by checking duplicate output, and comparing against existing references
    # compute_duplicates_task = PythonOperator(
	#     task_id=f'write_raw_duplicates_{gene}',
	#     python_callable=write_raw_duplicates,
	#     op_kwargs={ "input" : prot_input_filepath, "nuc_input" : nuc_input_filepath, "duplicates" : protein_dupe_output_filepath, "nucleotide_duplicates" : nuc_dupe_output_filepath },
	#     dag=dag,
	# )

    # Import novel sequences
    # import_postmsa_seqs_task = PythonOperator(
    #     task_id=f'store_postmsa_{gene}',
    #     python_callable=store_postmsa_file,
    #     op_kwargs={ "reference_sequence" : nuc_input_filepath, "gene": gene },
    #     dag=dag,
    # )

    # Import new duplicate information
    # mark_raw_dupes_task = PythonOperator(
    #     task_id=f'mark_duplicates_{gene}',
    #     python_callable=mark_duplicates,
    #     op_kwargs={ "dupe_input" : nuc_dupe_output_filepath, "gene": gene },
    #     dag=dag,
    # )

    i += 1
    # post_msa_tasks.append([export_missing, write_references_task] >> populated_check_task >> pre_msa >> [import_premsa_seqs, mark_troubled_task, compute_raw_duplicates_task] >> mark_premsa_dupes_task >> mark_raw_dupes_task)
    post_msa_tasks.append([ export_missing_task, write_references_task ] >> populated_check_task >> mafft_task >> remove_ref_task >> post_msa_task)

dag.doc_md = __doc__
post_msa_tasks
