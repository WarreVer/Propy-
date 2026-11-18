from IPython.display import display, HTML, clear_output
import ipywidgets as widgets
import os
import random

# Import the Python Modules (in this order)
from Python_Modules.my_General_Functions import *
from Python_Modules.my_Project_Data import *
from Python_Modules.my_CPM_Scheduler import *
from Python_Modules.my_Indicator_Calculator import *
from Python_Modules.my_RCP_Scheduler import *
from Python_Modules.my_TCT_Optimizer import *
from Python_Modules.my_SRA_Engine import *
from Python_Modules.my_EVM_Analyser import *
Filefolder = "Example_Files/"
Infofolder = "Summary_Files/"

def run_experiments_ui():
    # ----------------------------------------------------
    # Helper to run .py files inside Python_Experiments/
    # ----------------------------------------------------
    def run_script(filename):
        path = os.path.join("Python_Experiments", filename)
        print(f"Running {path}...\n")
        exec(open(path).read(), globals())

    # ----------------------------------------------------
    # Mapping of labels to .py filenames
    # ----------------------------------------------------
    procedure_map = {
        "Experiment 1. Critical Path Method":          lambda: run_script("my_Experiment1_cpm.py"),
        "Experiment 2. Time/Cost Trade-Offs":          lambda: run_script("my_Experiment2_tc.py"),
        "Experiment 3. Resources (heuristic)":         lambda: run_script("my_Experiment3_heuristic.py"),
        "Experiment 4. Resources (optimal)":           lambda: run_script("my_Experiment4_optimal.py"),
        "Experiment 5. Sensitivity Metrics":           lambda: run_script("my_Experiment5_sensitivity.py"),
        "Experiment 6. Schedule Risk Analysis":        lambda: run_script("my_Experiment6_sra.py"),
        "Experiment 7. Sensitivity Metrics (res.)":    lambda: run_script("my_Experiment7_sensitivity_res.py"),
        "Experiment 8. Schedule Risk Analysis (res.)": lambda: run_script("my_Experiment8_sra_res.py"),
        "Experiment 9. Earned Value Management":       lambda: run_script("my_Experiment9_evm.py"),
        "Experiment 10. Project Forecasting":          lambda: run_script("my_Experiment10_forecasting.py"),
    }

    # ----------------------------------------------------
    # Title section
    # ----------------------------------------------------
    title = widgets.HTML(
        value="""
        <div style='text-align:center;'>
            <h2>10 experiments of the book<br> “Data-Driven Project Management with Python”</h2>
            <h4>by Mario Vanhoucke</h4>
            <p>
                You can run the 10 experiments by clicking on the buttons below.<br>
                If you want to change the experiments, edit the code in the "Python_Experiments" folder.<br>
                If you want to change other procedures, edit the code in the "Python_Modules" folder.
            </p>
        </div>
        """
    )

    # ----------------------------------------------------
    # Create buttons
    # ----------------------------------------------------
    buttons = []
    for label, func in procedure_map.items():
        btn = widgets.Button(description=label, layout=widgets.Layout(width='280px'))

        def on_click(b, f=func):
            clear_output(wait=True)
            display(title, grid)
            print(f"Below you see the results for {b.description}\n")
            display(HTML("<hr style='border:1px solid gray;'>"))
            f()  # run the corresponding .py file

        btn.on_click(on_click)
        buttons.append(btn)

    # ----------------------------------------------------
    # 2-column layout
    # ----------------------------------------------------
    col1 = widgets.VBox(buttons[:5])
    col2 = widgets.VBox(buttons[5:])
    global grid  # make grid accessible inside on_click
    grid = widgets.HBox([col1, col2], layout=widgets.Layout(justify_content="center", gap="40px"))

    # ----------------------------------------------------
    # Display UI
    # ----------------------------------------------------
    display(title, grid)
