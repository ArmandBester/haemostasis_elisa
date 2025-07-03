import streamlit as st
from pathlib import Path
import zipfile
import pandas as pd
import numpy as np
import random, string
import os
import subprocess
from glob import glob
import plotly.express as px
import plotly.io as pio
pio.templates[pio.templates.default].layout.colorway = px.colors.qualitative.Dark24

# Set up session state, initialize empty session states

for key in ['session', 'save_folder', 'min_len', 'max_len', 'blast_outFmt']:
    st.session_state[key] = ''

## Set up functions

def create_session():
    '''
    Generate a random alpha numeric string 
    as random_session
    Create a directory structure with this
    Return the session string    
    '''
    random_session = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
    os.mkdir(f"work_dir/{random_session}")
    for directory in ['1_fasta_len_filt', '2_cdhit', '3_blast', '4_mapping', '5_depth', "6_cons"]:
        os.mkdir(f"work_dir/{random_session}/{directory}")
    return random_session


def preprocess_fastq_for_cdhit(fastq_path, min_len, max_len):
    cmd = f"zcat {fastq_path}fastq_pass/{bc}/*.fastq.gz | seqkit fq2fa | seqkit seq -g --min-len {min_len} --max-len {max_len} > {fastq_path}1_fasta_len_filt/{bc}.fasta"
    subprocess.call(cmd, shell=True)
    return cmd

def cdhitest(path):
    cmd = f"cd-hit-est -i {path}1_fasta_len_filt/{bc}.fasta -c 0.95 -n 10 -o {path}2_cdhit/{bc} -d 0"
    subprocess.call(cmd, shell=True)
    return cmd

def blast(path):
    outFmt = "'6 qaccver saccver pident length mismatch gapopen qstart qend sstart send evalue bitscore staxid stitle'"
    st.session_state['blast_outFmt'] = outFmt.replace("'", "")
    cmd = f"blastn -query {path}2_cdhit/{bc} -db  refs/16S_ribosomal_RNA -outfmt {outFmt} -num_threads 8 -max_target_seqs 50 -out {path}3_blast/{bc}.blst"
    subprocess.call(cmd, shell=True)
    return(cmd, outFmt)

def parse_chdit_blast(path, outFmt):
    blastDf = pd.DataFrame()
    names = outFmt
    blstFiles = glob(f"{path}3_blast/*.blst")
    for s in blstFiles:
        tmp = pd.read_csv(s, sep="\t", names=names)
        tmp['sample'] = s.split("/")[3].replace(".blst", "")
        blastDf = pd.concat([blastDf, tmp])
    
    blastDf = (blastDf
               .sort_values(['sample','qaccver' ,'bitscore'], ascending=[True, True, False])
               .drop_duplicates(subset=['sample', 'qaccver'], keep='first')               
               )
    return blastDf


def get_refs_from_blastdb(path):
    cmd = f"blastdbcmd -db refs/16S_ribosomal_RNA -entry_batch {path}4_mapping/{bc}_acc.txt > {path}/4_mapping/{bc}_hits.fasta"
    subprocess.call(cmd, shell=True)
    return cmd

def mapping_to_refs(path):
    cmd_map = f"zcat {path}/fastq_pass/{bc}/*.fastq.gz | minimap2 {path}4_mapping/{bc}_hits.fasta - -ax map-ont | samtools sort -o {path}4_mapping/{bc}.bam"
    cmd_index = f"samtools index {path}4_mapping/{bc}.bam"
    subprocess.call(cmd_map, shell=True)
    subprocess.call(cmd_index, shell=True)
    return [cmd_map, cmd_index]
    
def get_depth(path):
    cmd = f"samtools depth -a {path}4_mapping/{bc}.bam > {path}5_depth/{bc}.depth"
    subprocess.call(cmd, shell=True)
    return cmd    



        
# App

## Sidebar 
st.sidebar.title("PoepSnuifer")

with st.sidebar.expander("Info on fastq_pass folder"):
    st.markdown('''Remember your zipped fastq_pass folder must 
                        have a `samplesheet.csv` file in the top directory, ie
                        alongside your barcode folders.'''
                        )

with st.sidebar.form(key="Form :", clear_on_submit = True, ):
    File = st.file_uploader(label = "Upload file zipped fastq_pass folder", type=["zip"])
    min_len = st.slider(min_value=100, max_value=10000, value=1000, label='Min length')
    max_len = st.slider(min_value=100, max_value=10000, value=3000, label='Max length')
    Submit = st.form_submit_button(label='Submit')



if Submit:
    # Call teh create session function and create the session 
    session = create_session()

    # Save uploaded file
    save_folder = f'work_dir/{session}/'
    save_path = Path(save_folder, File.name)
    with open(save_path, mode='wb') as w:
        w.write(File.getvalue())
    if save_path.exists():
        st.sidebar.success(f'File {File.name} was successfully saved!')
    
    # unzip the file
    with zipfile.ZipFile(save_path, 'r') as zip_ref:
        zip_ref.extractall(save_folder)

    # parse the samplesheet file for the analysis name    
    with open(f'{save_folder}/fastq_pass/samplesheet.csv', 'r') as samplesheet:
        analysis_name = samplesheet.readlines()[0].replace(",", "").strip()
        st.header(f'Analysis: {analysis_name}')

    st.session_state['session'] = session
    st.session_state['save_folder'] = save_folder


# get some session states which was generated in the fastq upload section  
save_folder = st.session_state['save_folder']
session = st.session_state['session']


# parse the samplesheet file for barcode names
sampleDict = {}
if session != '':
    with open(f'{save_folder}/fastq_pass/samplesheet.csv', 'r') as samplesheet:
        for line in samplesheet.readlines()[1:]:
            barcode = line.split(",")[0]
            sampleName = line.split(",")[1]
            sampleDict[barcode] = sampleName
    
    sampleDf = pd.DataFrame.from_dict(sampleDict, orient='index').reset_index()
    sampleDf.columns = ['barcode', "sample_name"]    
    st.table(sampleDf)

# convert to fasta and filter based on length
if session != '':
    for bc in sampleDict.keys():
        #st.write(bc)
        preprocessReturns = preprocess_fastq_for_cdhit(fastq_path=save_folder, min_len=min_len, max_len=max_len)
        cdhitReturns = cdhitest(path=save_folder)
        blastReturns = blast(path=save_folder)
    
    outFmt = st.session_state['blast_outFmt'].split(" ")[1:]
    blastDf = parse_chdit_blast(path=save_folder, outFmt=outFmt)

    # write cd-hit-est prelim blast results
    with st.expander("Preliminary blast results from ch-hit-clusters"):
        st.dataframe(
            blastDf.groupby("sample")['stitle'].value_counts()
            )
        st.dataframe(
            blastDf.groupby(["sample", 'stitle'])['pident'].describe()[['count', 'min', 'mean', 'max']]
            )
    
    # write out the accession numbers
    for bc in blastDf['sample'].unique():
        blastDf.query("sample == @bc")['saccver'].unique().tofile(f"{save_folder}4_mapping/{bc}_acc.txt", sep='\n', format='%s')

    # get the ref sequences from the blast databases
    for bc in blastDf['sample'].unique():
        get_refs_from_blastdb(save_folder)

    # mapping
    for bc in sampleDict.keys():
        mapping_to_refs(save_folder)

    # depth
    for bc in sampleDict.keys():
        get_depth(save_folder)

    # mapping and depth results
    depthDf = pd.DataFrame()
    depth_data = glob(f"{save_folder}5_depth/*.depth")
    
    for i in depth_data:
        tmpDf = pd.read_csv(i, sep="\t", names=['saccver', 'pos', 'depth'])
        tmpDf['sample'] = i.split("/")[3].replace(".depth", "")
        depthDf = pd.concat([depthDf, tmpDf], axis=0)
    
    
    depthDf['barcode'] = depthDf['sample']
    depthDf['sample'] = depthDf['sample'].replace(sampleDict, regex=False)
    depthDf = depthDf.merge(
        blastDf[['saccver', 'stitle']].drop_duplicates(), 
        on='saccver', how='left')
    
    # Main results
    st.markdown("---")
    st.markdown("## Main results")
    st.markdown("**This is the main results after mapping the original fastq reads to the references found by blast**")

    summaryDf = pd.DataFrame(depthDf.groupby(['sample', 'barcode', 'saccver', 'stitle'])[['depth']].mean()).reset_index()
    summaryDf["relative_abundance"] = summaryDf.groupby(['barcode'])['depth'].transform(lambda z: z / z.sum() * 100)
    summaryDf = summaryDf[['sample', 'barcode', 'relative_abundance', 'depth', 'stitle', 'saccver']]
    summaryDf.set_index('sample', inplace=True)
    summaryDf.sort_values(by=['barcode', 'relative_abundance'], inplace=True)
    st.dataframe(summaryDf)
    

    ##
    plotting_depthDf = depthDf
    plotting_depthDf['Organism'] = plotting_depthDf['stitle'].apply(
        lambda s: " ".join(
            s.split(" ")[0:2]
            )
        )
    
    st.markdown("Depth and coverage:")
    with st.expander("Expand"):
        for sample in plotting_depthDf['sample'].unique():
            st.markdown(f"Read depth for {sample}")
            depth_fig = px.scatter(data_frame=plotting_depthDf.query("sample == @sample"), 
                                x="pos", y='depth', 
                                color='Organism', height=400, width=600,
                                hover_data=['pos', 'depth', 'stitle', 'Organism'])
            depth_fig = depth_fig.update_yaxes(matches=None)
            st.plotly_chart(depth_fig)

    # Plot relative abundance
    plotting_rel_abDf = summaryDf
    plotting_rel_abDf['Organism'] = plotting_rel_abDf['stitle'].apply(
        lambda s: " ".join(
            s.split(" ")[0:2]
            )
    )

    st.markdown("---")
    st.markdown("Relative abundance:")
    plotting_rel_abDf['Sample_name'] = plotting_rel_abDf.index
    with st.expander("Expand"):
        for sample in plotting_rel_abDf['Sample_name'].unique():
            st.markdown(f"Relative abundance for {sample}")
            rel_ab_fig=px.pie(data_frame=plotting_rel_abDf.query('Sample_name == @sample'), 
                            names="Organism", 
                            #facet_row=summaryDf['Sample_name'], facet_row_spacing=0.3,
                            height=300, width=600,
                            values="relative_abundance", hole=0.8, labels={'Organism'})
            rel_ab_fig.update_traces(textposition='outside', textinfo='percent+label')
            st.plotly_chart(rel_ab_fig)
        