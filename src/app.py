import streamlit as st
import random, string
from pathlib import Path
import os
import json
from openpyxl import workbook, load_workbook
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score
import plotly.express as px
import plotly.graph_objects as go

for key in ['session', 'save_folder']:
    st.session_state[key] = ''


def create_session():
    '''
    Generate a random alpha numeric string 
    as random_session
    Create a directory structure with this
    Return the session string    
    '''
    random_session = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(16))
    os.mkdir(f"work_dir/{random_session}")
    return random_session


## ----------------------------------------------------------------------------------------##
# FUNCTIONS ""
## ----------------------------------------------------------------------------------------##

# Make the percentage dilution ranges
def make_ranges_for_std_curve(n):
    '''
    Takes n as an argument, the number of times 100% is halved.
    Returns a list of percentage ranges for the standard curve.
    The ranges are in the form of a list of percentages, 
    starting from 100% and going down to 0% in steps of 50%.

    Returns: a list of percentages.
    '''
    perc = 100
    vwf_ref_prec = []
    i = n
    while i >= 0 :
        vwf_ref_prec.append(perc)
        perc = perc / 2             # halving the percentage
        i-=1                        # decrementing the counter
        
    vwf_ref_prec.append(0)          # add 0% to the list
    return vwf_ref_prec


# Read the template file
def get_template_from_config():
    with open('config/config.json', 'r') as file:
        config = json.load(file)
    
    return config

# read the data
def read_data_to_dataframe(input_file):
    '''
    Takes the path to an input file
    returns a dataframe
    '''
    data = pd.DataFrame()
    config = get_template_from_config()

    excel_to_csv = pd.read_excel(input_file, header=None)
    
    analysis_name = excel_to_csv.iloc[config['analysis_name_pos']['row']-1, 
                                    config['analysis_name_pos']['col']-1
                                    ]
    serial_name = excel_to_csv.iloc[config['serial_name_pos']['row']-1, 
                                    config['serial_name_pos']['col']-1
                                    ]
    data = pd.DataFrame()

    for plate in config["plates"]:
        row = plate['pos']['row']
        col = plate['pos']['col']
        
        tmpDf = pd.DataFrame(excel_to_csv.iloc[row-1:row+7, col:col+12])
        tmpDf['analysis_name'] = analysis_name
        tmpDf['serial_name'] = serial_name
        
        target_name = excel_to_csv.iloc[
            plate["assay_name_pos"]['row']-1, 
            plate["assay_name_pos"]['col']-1
            ]
        tmpDf['assay'] = target_name

        data = pd.concat([data, tmpDf])
    #data = data.reset_index()
    return data

def logistic_4_param(x, a, b, c, d):
    return d + ( (a - d) / (1 + (x / c)**b) )


def compute_4PL(y, a, b, c, d):
    """
    x = c * ((a - d) / (y - d) - 1) ** (1 / b)
    """
    if y == d:
        raise ValueError("Division by zero: y must not be equal to d.")
    inner = (a - d) / (y - d) - 1
    if inner < 0 and b % 2 == 0:
        raise ValueError("Cannot compute even root of a negative number.")
    x = c * (inner) ** (1 / b)
    return x


## initial values
p0 = [0, 1, 25, 1] # this may need work for the inititial predictions

def compute_4PL_params(p0 = p0):
    unique_assays = data['assay'].unique()

    param_results_dict = {}

    for assay in unique_assays:
        print(assay)
        # create a datafram to make things easier, these value are then passed to a dictionary
        standard_curve_data = data.query("assay == @assay").iloc[:,0:2]
        standard_curve_data['mean'] = standard_curve_data.mean(axis=1)
        standard_curve_data['diffs_of_values'] = abs(standard_curve_data.iloc[:,0] - standard_curve_data.iloc[:,1]) 
        standard_curve_data['perc'] = make_ranges_for_std_curve(6)

        callibrators = standard_curve_data["mean"].values
        perc = standard_curve_data["perc"].values
        diffs_of_values = standard_curve_data['diffs_of_values'].values
        
        popt, pcov = curve_fit(logistic_4_param, perc, callibrators, p0=p0)
        
        # Extract the fitted parameters
        a_fit, b_fit, c_fit, d_fit = popt

        # Generate the fitted curve
        x_fit = np.linspace(min(perc), max(perc)*2, 10000)
        y_fit = logistic_4_param(x_fit, a_fit, b_fit, c_fit, d_fit)

        param_results_dict[assay] = {"params": popt, 
                            "perc": perc, 
                            "callibrators": callibrators,
                            "diffs_of_values": diffs_of_values,
                            "x_fit": x_fit, 
                            "y_fit": y_fit}
        
    return param_results_dict

## A function to create figures
def create_figures(param_results_dict):
    list_of_figures = []
    for key in param_results_dict.keys():
        fig = go.Figure()
        # Add the points for the percentage calibrator and Absorbance
        f = fig.add_trace(
            go.Scatter(
                x=param_results_dict[key]["perc"],
                y=param_results_dict[key]["callibrators"],
                error_y=dict(
                    type='data', 
                    array=param_results_dict[key]["diffs_of_values"],
                    visible=True),
                mode='markers',
                marker=dict(
                    size=10,
                    color='teal',
                    symbol='circle'
                    )
                )
            )
        # Add a line plot for the fitted model
        f = fig.add_trace(
            go.Scatter(
                x=param_results_dict[key]["x_fit"],
                y=param_results_dict[key]["y_fit"],
                mode='lines',
                marker=dict(
                    color='orange'
                    )
            )            
        )
        # Update the figure size, margin and title
        f = fig.update_layout(
            autosize=False,
            width=600,
            height=400,
            margin=dict(
                l=50,
                r=50,
                b=10,
                t=40,
                pad=4
                ),
            title=dict(text=key, font=dict(size=20)),
            xaxis=dict(title=dict(text="Percentage")),
            yaxis=dict(title=dict(text="Absorbance"))
            
            )

        fig_dict = f.to_dict()
        list_of_figures.append(fig_dict)

    return list_of_figures


        
## ----------------------------------------------------------------------------------------##
# APP
## ----------------------------------------------------------------------------------------##
      

## Sidebar 
st.sidebar.title("Haemostasis ELISA calculator")

with st.sidebar.expander("Info"):
    st.markdown('''This is where you upload your 
                template xlsx file 
                with your ELISA results
                '''
                        )

with st.sidebar.form(key="Form :", clear_on_submit = True, ):
    File = st.file_uploader(label = "Upload your xlsx file", type=["xlsx"])
    Submit = st.form_submit_button(label='Submit')



if Submit:
    # Call the create session function and create the session 
    session = create_session()

    # Save uploaded file
    save_folder = f'work_dir/{session}/'
    save_path = Path(save_folder, File.name)
    with open(save_path, mode='wb') as w:
        w.write(File.getvalue())
    if save_path.exists():
        st.sidebar.success(f'File {File.name} was successfully saved!')
    
    st.session_state['session'] = session
    st.session_state['save_folder'] = save_folder


# get some session states which was generated
save_folder = st.session_state['save_folder']
session = st.session_state['session']


if session != '':
    print("OK")
    st.markdown("## Uploaded data")

    data = read_data_to_dataframe(save_path)
    st.dataframe(data)

    unique_assays = data['assay'].unique()

    st.markdown("## Assay names")
    st.write(unique_assays)

    # compute and extract the standard curve data
    param_results_dict = compute_4PL_params()
    figure_dicts = create_figures(param_results_dict)

    st.markdown("## Regression plots")
    for plot in figure_dicts:
        st.plotly_chart(plot)

    



    
