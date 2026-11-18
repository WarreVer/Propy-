#############################################################################
### Example experiment 10: Time forecasting accuracy study with Earned Value Management (EVM) 
### = The project network structure has a major impact on the accuracy of EVM predictions
###
###   The experiment replicates the simulations of the following book:
###      - Title: Measuring Time: Improving Project Performance Using Earned Value Management
###      - Author: Mario Vanhoucke
###      - Year: 2010
###      - Publisher: Springer
###      - Source: https://doi.org/10.1007/978-1-4419-1014-1
###
###   Alert: This experiment may take some time!
###      - When using multiple Monte Carlo runs, avoid setting the number too high
###      - Processing simulated data, including EVM predictions and accuracy calculations, can be time-consuming
###      - Keep an eye on the progress bar—and be patient! 
###
###   Note: 
###      - The experiment makes use of the so-called MT dataset (MT is used to refer to the book title "Measuring Time")
###      - The MT project files follow the Patterson format (but ignore the resources)
###      - The MT dataset can be downloaded from www.projectmanagement.ugent.be/research/data
###
###    Summary details:
###      - Time forecasting (3 x 3 = 9 methods):
###        * The forecasting methods EAC(t) come from three classes:
###            ° Planned Value Method (PVM)
###            ° Earned Duration Method (EDM)
###            ° Earned Schedule Method (ESM)
###        * Each of these methods can be used under three Performance Factor (PF) settings:
###            ° Version 1: PF = 1: Future performance is expected to follow the baseline schedule
###            ° Version 2: PF = SPI or SPI(t): Future performance is expected to follow the current time performance
###            ° Version 3: PF = SCI or SCI(t): Future performance is expected to follow the current time and cost performance (with SCI = Schedule Cost Index (SCI = SPI * CPI and SCI(t) = SPI(t) * CPI))
###      - Cost forecasting (8 methods):
###            ° PF = 1: Future performance is expected to follow the baseline schedule (version 1)
###            ° PF = SPI or SPI(t): Future performance is expected to follow the current time performance (versions 2 and 3)
###            ° PF = CPI: Future performance is expected to follow the current cost performance (version 4)
###            ° PF = SCI or SCI(t): Future performance is expected to follow the current time and cost performance (versions 5 to 8)
###              (This method can be used under four versions, i.e. PF is equal to the current SCI performance (version 5 and 6) 
###               or to a weighted time and cost performance (versions 7 and 8))
###
###    Other interesting reference for the SP indicator:
###      - Vanhoucke, M., Coelho, J., Debels, D., Maenhout, B. and Tavares, L.V.
###        "An evaluation of the adequacy of project network generators with systematically sampled networks"
###        European Journal of Operational Research, 187(2), 511–524, 2018 (doi:10.1016/j.ejor.2007.03.032).
###
###    Download the summary file "Summary_Experiment_10.pdf" or print on screen
###
#############################################################################

# Choose the project (from 1 to 900) and print the summary file of the experiment
projectID = 401
print_summary_file(Infofolder, 10)
#filename = Filefolder + "MT/ev810.rcp"
#filename = Filefolder + "MT/ev401.rcp"
filename = f"{Filefolder}MT/ev{projectID}.rcp"

#############################################################################
### Step 1. Construct a CPM schedule (earliest start schedule)            ###
#############################################################################

(_, activity_set, successors_list, activity_names, 
        _, _, activity_risk_classes) = read_patterson_file(filename)
add_dummy_nodes_to_project_data(activity_set,activity_names,sul=successors_list,arc=activity_risk_classes)
activity_dependencies = create_activity_network_dependencies({},successors_list,activity_names, debugInfo = False)

# Construct the CPM schedule
graph, PD, BAC, planned_schedule = calculate_critical_path(activity_set, activity_dependencies, activity_names, False)
print('Planned duration (PD) = ', PD)
print('Budget at completion (BAC) = ', BAC)

# Visualize the network graph (created in the "calculate_critical_path" function)
visualize_network(graph, activity_names, title_size=0)

# Visualize the schedule using a Gantt chart
#show_gantt_chart(planned_schedule)

##############################################################################
### Step 2. Simulate multiple real-life execution to imitate project progress
### 
###         = the real activity durations differ from the planned durations
###         = the cost is linearly related to the real duration 
##############################################################################

print("activity_risk_classes = ", activity_risk_classes)

nrRuns = 1000 
list_simulated_schedules_df = perform_monte_carlo_simulation(
    nrRuns, activity_names, activity_dependencies, planned_schedule,  
    "LOW", "CLASS", "CPM", 
    activity_risk_classes, resource_requirements=None, resource_availability=None, 
    debugInfo=True)

##############################################################################
### Step 3. Forecast duration/cost for each simulated schedule
###      3.1 Calculate at each integer time interval, the EAC(€) and EAC(t)
###      3.2 Calculate the MAPE and MPE for each simulated schedule
###      3.3 Calculate the average MAPE and MPE values
##############################################################################

time_method_names = ["EACtPV1", "EACtPV2", "EACtPV3", "EACtED1", "EACtED2", "EACtED3", "EACtES1", "EACtES2", "EACtES3"]
cost_method_names = ["EAC1", "EAC2", "EAC3", "EAC4", "EAC5", "EAC6", "EAC7", "EAC8"]
    
# Initialize dictionaries to store MAPE and MPE values
forecast_accuracy = {
    "time": {"MAPE": [], "MPE": [], "methods": time_method_names},
    "cost": {"MAPE": [], "MPE": [], "methods": cost_method_names}
}

# Store predictions for analysis
all_time_predictions = {"EACtPV1": [], "EACtPV2": [], "EACtPV3": [], "EACtED1": [], "EACtED2": [], "EACtED3": [], "EACtES1": [], "EACtES2": [], "EACtES3": []}
all_cost_predictions = {"EAC1": [], "EAC2": [], "EAC3": [], "EAC4": [], "EAC5": [], "EAC6": [], "EAC7": [], "EAC8": []}

total_rows = len(list_simulated_schedules_df)
for count, row in enumerate(list_simulated_schedules_df.itertuples(index=False), start=0):
    total_duration = row[0]
    total_cost = row[1]
    simulated_schedule = row[2]
    
    print_progress_bar("Generating EVM data (including predictions and accuracy metrics): ", count, total_rows, steps = 1, bar_length = 40)
    
    # Calculate EVM metrics
    PV, AC, EV, ES, AT, SV, SVt, CV, SPI, SPIt, CPI = calculate_evm_key_metrics(planned_schedule, simulated_schedule)

    # Calculate predictions
    (EACtPV1, EACtPV2, EACtPV3, EACtED1, EACtED2, EACtED3, EACtES1, EACtES2, EACtES3, 
     EAC1, EAC2, EAC3, EAC4, EAC5, EAC6, EAC7, EAC8) = calculate_evm_predictions(
        planned_schedule, PV, AC, EV, ES, AT, SV, SVt, CV, SPI, SPIt, CPI)

    predictions = {
        "time": [EACtPV1, EACtPV2, EACtPV3, EACtED1, EACtED2, EACtED3, EACtES1, EACtES2, EACtES3],
        "cost": [EAC1, EAC2, EAC3, EAC4, EAC5, EAC6, EAC7, EAC8]
    }
    
    actual_values = {"time": total_duration, "cost": total_cost}
    
    # Compute and store MAPE/MPE for both time and cost
    for key in ["time", "cost"]:
        MAPE, MPE = get_all_forecasting_accuracy(actual_values[key], predictions[key], forecast_accuracy[key]["methods"])
        forecast_accuracy[key]["MAPE"].append(MAPE)
        forecast_accuracy[key]["MPE"].append(MPE)
        
        
# Compute the averages
for key in ["time", "cost"]:
    forecast_accuracy[key]["avg_MAPE"] = np.mean(forecast_accuracy[key]["MAPE"], axis=0)
    forecast_accuracy[key]["avg_MPE"] = np.mean(forecast_accuracy[key]["MPE"], axis=0)

# Print results
for key in ["time", "cost"]:
    print(f"\nFinal Average {key.capitalize()} Accuracy Values:")
    for method, avg_mape, avg_mpe in zip(forecast_accuracy[key]["methods"], forecast_accuracy[key]["avg_MAPE"], forecast_accuracy[key]["avg_MPE"]):
        print(f"{method}: Avg MAPE = {avg_mape:.2f}%, Avg MPE = {avg_mpe:.2f}%")

        
####### Create some boxplots
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

def prepare_forecast_df(forecast_accuracy, key, metric_label):
    """
    Transpose the forecast_accuracy[key][metric_label] from [runs][methods]
    to [methods][runs] and prepare a long-format DataFrame.
    """
    methods = forecast_accuracy[key]["methods"]
    metric_data = forecast_accuracy[key][metric_label]  # List of lists

    # Transpose: from shape [runs][methods] to [methods][runs]
    transposed = list(zip(*metric_data))  # Each tuple = one method's values across all runs

    # Build DataFrame for seaborn
    long_data = []
    for method, values in zip(methods, transposed):
        for v in values:
            long_data.append({"Method": method, metric_label: v})

    return pd.DataFrame(long_data)

def plot_forecast_boxplot(df, metric_label, title,
                                xlabel_size=None, ylabel_size=None,
                                xtick_size=None, ytick_size=None,
                                title_size=None):

    xlabel_size = xlabel_size if xlabel_size is not None else Value_xlabel_size
    ylabel_size = ylabel_size if ylabel_size is not None else Value_ylabel_size
    xtick_size = xtick_size if xtick_size is not None else Value_xtick_size
    ytick_size = ytick_size if ytick_size is not None else Value_ytick_size
    title_size = title_size if title_size is not None else Value_title_size
    
    plt.figure(figsize=(12, 6))
    sns.boxplot(x="Method", y=metric_label, data=df)
    # Axis labels
    plt.xlabel("Method", fontsize=xlabel_size)
    if ylabel_size:
        plt.ylabel(metric_label, fontsize=ylabel_size)
    # Tick sizes
    plt.xticks(rotation=45, fontsize=xtick_size)
    plt.yticks(fontsize=ytick_size)
    # Title
    plt.title(title, fontsize=title_size)
    plt.grid(True)
    plt.tight_layout()
    plt.show()
    
    
    

# TIME — MAPE
df_time_mape = prepare_forecast_df(forecast_accuracy, key="time", metric_label="MAPE")
plot_forecast_boxplot(df_time_mape, metric_label="MAPE", title="MAPE for Time Forecasting Methods", ylabel_size=0)

# COST — MAPE
df_cost_mape = prepare_forecast_df(forecast_accuracy, key="cost", metric_label="MAPE")
plot_forecast_boxplot(df_cost_mape, metric_label="MAPE", title="MAPE for Cost Forecasting Methods", ylabel_size=0)

# TIME — MPE
df_time_mpe = prepare_forecast_df(forecast_accuracy, key="time", metric_label="MPE")
plot_forecast_boxplot(df_time_mpe, metric_label="MPE", title="MPE for Time Forecasting Methods", ylabel_size=0)

# COST — MPE
df_cost_mpe = prepare_forecast_df(forecast_accuracy, key="cost", metric_label="MPE")
plot_forecast_boxplot(df_cost_mpe, metric_label="MPE", title="MPE for Cost Forecasting Methods", ylabel_size=0)



