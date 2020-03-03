import pandas as pd
import numpy as np
from collections import defaultdict
import os
import sys
import argparse

"""
Use output of uniq_annot.py and files with r2 coefficients generated by plink
(e.g. chr{i}.height.2m.r2.ld.gz i=1..22) to construct ld-informed annotations.
"""
chr_r2_file_dir = "/home/weiqiuc/workspace2/testrun2/1000G/dataprocess/schork/"
chr_r2_prefix = "chr"
chr_r2_suffix = ".schork.r2.ld.gz"
nonoverlapping_annot_file = "/home/weiqiuc/workspace2/testrun2/1000G/dataprocess/knownGene_ucsc_hg19.annomat.uniq.txt.gz"
out_f_name = "/home/weiqiuc/workspace2/testrun2/1000G/dataprocess/schork/ /home/weiqiuc/workspace2/testrun2/1000G/dataprocess/knownGene_ucsc_hg19.annot.ld_informed_test.txt.gz"
annot2use = ["5UTR", "3UTR", "Exon", "Intron", "1kUp", "1kDown", "10kUp", "10kDown"]
auxiliary_annot = ["NoncodingTranscript", "100kUp", "100kDown", "mirna", "tfbs"]

dfa = pd.read_table(nonoverlapping_annot_file)
df_annot2use = dfa[annot2use] #SNP*annot2use: 8452253*8
ld_annot_data = df_annot2use.values.copy().astype(float) #<class 'numpy.ndarray'> same info with df_annot2use,diff format

snp_annot = dict(zip(*np.where(ld_annot_data))) #dict: snp_i=>annot_i; N=3391701
snp_ind = dict(zip(dfa.SNP, dfa.index)) #dict: snp_id=>snp_i; N=8452254
    #     snp_i - index of snp in dfa["SNP"]
    #     annot_i - index of annotation category in annot2use

#define dict for ld info 
snp_in_ld_id = defaultdict(list) # snp_i : [snp_i_1, snp_i_2, ...] - ids of snps in LD with the key snp
snp_in_ld_r2 = defaultdict(list) #snp_i : [snp_r2_1, snp_r2_2, ...] - r2 of snps in LD with the key snp

#testrun, only for chr22; for all chr using for i in range(1,23):
i=21
f_name = os.path.join(chr_r2_file_dir, f"{chr_r2_prefix}{i}{chr_r2_suffix}") # "/home/weiqiuc/workspace2/testrun2/1000G/dataprocess/schork/chr21.schork.r2.ld.gz"
#print("Reading %s" % f_name)
df = pd.read_table(f_name, usecols=["SNP_A", "SNP_B", "R2"],delim_whitespace=True)
#   >>> df[1:3]
#           SNP_A       SNP_B        R2
#   1  rs71220884  rs71205710  0.568647
#   2  rs71220884  rs68192677  0.597525
for row in df.itertuples():
    i1 = snp_ind[row.SNP_A]
    i2 = snp_ind[row.SNP_B]
    snp_in_ld_id[i1].append(i2)
    snp_in_ld_id[i2].append(i1)
    snp_in_ld_r2[i1].append(row.R2)
    snp_in_ld_r2[i2].append(row.R2)

for snp_i, snp_in_ld_ii in snp_in_ld_id.items():
    if snp_i%100000 == 0: print("%d snp processed" % snp_i)
    snp_i_r2 = snp_in_ld_r2[snp_i]
    annot_ii = [snp_annot[i] for i in snp_in_ld_ii if i in snp_annot]
    annot_r2 = [r2 for i,r2 in zip(snp_in_ld_ii, snp_i_r2) if i in snp_annot]
    annot_ld = np.bincount(annot_ii, annot_r2, len(annot2use))
    ld_annot_data[snp_i] += annot_ld

i = ld_annot_data<1
ld_annot_data[i] = 0
ld_annot_data[~i] = 1

out_df = pd.DataFrame(index=dfa.SNP, columns=annot2use, data=ld_annot_data)
# add intergenic column properly based on auxiliary annotation columns from dfa
intergenic = np.zeros(len(out_df))
i = (out_df.sum(1).values + dfa[auxiliary_annot].sum(1).values) == 0 # out_df.sum(1).values & dfa[auxiliary_annot].sum(1).values: located in functional categories
intergenic[i] = 1 # define the mutation is intergenic if this mutation doesn't locate at any of the functional categories. 
out_df["Intergenic"] = intergenic 

out_df = out_df.astype(int)
print(out_df.sum())

print("Saving result to %s" % out_f_name)
out_df.to_csv(out_f_name, sep='\t', compression='gzip')


if __name__ == "__main__":
    print("Start")
    main()
    print("Done")