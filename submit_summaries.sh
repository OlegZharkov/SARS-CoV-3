#!/bin/bash
#fdate=$(date +"%Y-%m-%d")
fdate=$1

FQUEUE='batch'
QUEUE='batch'
OUTPUT_DIR=`pwd`/logs/$fdate/
mkdir $OUTPUT_DIR

# Gene
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $FQUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate S 64" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate M 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate N 64" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate E 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate ORF3a 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate ORF6 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate ORF7a 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate ORF7b 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate ORF8 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh 
#qsub -l nodes=2:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate ORF1a 128" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
#qsub -l nodes=2:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate ORF1b 128" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh

# Products
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate leader 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate nsp2 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $FQUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate nsp3 64" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate nsp4 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate 3C 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate nsp6 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate nsp7 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate nsp8 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate nsp9 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate nsp10 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate RdRp 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate helicase 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate exonuclease 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate endornase 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate methyltransferase 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh
qsub -l nodes=1:ppn=1 -d `pwd` -o $OUTPUT_DIR -e $OUTPUT_DIR -q $QUEUE -F "/data/shares/veg/SARS-CoV-2/SARS-CoV-2/data/fasta/$fdate ORF10 32" /data/shares/veg/SARS-CoV-2/SARS-CoV-2/scripts/generate_summaries.sh

