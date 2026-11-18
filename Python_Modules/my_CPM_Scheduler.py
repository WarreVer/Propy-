"""
    Module Name: my_CPM_Scheduler
    
    THIS MODULE CONTAINS ALL PROCEDURES FOR A NETWORK ANALYSIS AND THE CRITICAL PATH METHOD

    This python file contains the following procedures:
    
    A. Network analysis:

        - transform_predecessor_to_successor_list(dependencies)
        - transform_successor_to_predecessor_list(dependencies)
        - create_activity_network_dependencies(predecessors_list,successors_list,activity_names):
            Note: The project data input must have either a "predecessors_list" or "successor_list"
                  and the create_activity_network_dependencies creates the missing list and the activity_dependencies 
                  (only "activity_dependencies" will be used in the Jupyter notebook)
                  (Info: The patterson files only have successor_list but the hard coded data only has predecessors_list)
      
        - construct_activity_network(activities, activity_dependencies, activity_names,
                               debugInfo=False, visualize=False, includeDummy=False
                - When this procedure is called by the user (in the Experiments), set includeDummy = True
                - Called by other procedures:
                    - includeDummy = True: Called by the procedure "calculate_critical_path" 
                            = dummies necessary to schedule projects
                    - includeDummy = False: Called by "calculate_network_topology_indicators"
                            = dummies forbidden to calculate network indicators (cf. my_Indicator_Calculator.py)
                            
        - visualize_network(G, activity_names, showEdgeLabels=False, showCP=True,
                              xtick_size=None, ytick_size=None, title_size=None, node_size=None,
                              showDummy=True, ProgLevelHierarchy = True)
                Note: You can visualize the network after running "construct_activity_network" or "calculate_critical_path"
                      since both procedures construct a network

        - show_design_structure_matrix(activity_dependencies,
                                 xlabel_size=None, ylabel_size=None,
                                 xtick_size=None,
                                 title_size=None,
                                 showDummy=False):
    B. CPM Scheduling:

        - calculate_critical_path(activities, activity_dependencies, activity_names, buffer = 0, debugInfo = False)
                - Constructs an earliest start schedule with activity start times and slack calculations
                - Optional parameter buffer (default 0, only increase when necessary (e.g. in "resource_scheduler_optimizer"))
                - Calls "construct_activity_network" with includeDummy=True
            
        - def show_gantt_chart(schedule, showCP=True, showDummy=False, showCost=False, showName=True,
                                    xlabel_size=None, ylabel_size=None, xtick_size=None, ytick_size=None, title_size=None):    
                - No "activity_names" necessary since they are in the schedule
                - Optional layout parameters: showCP=True, showDummy=False, showCost=True,
                                              xlabel_size=None, ylabel_size=None,
                                              xtick_size=None, ytick_size=None,
                                              title_size=None
    C. Layout
        - To control the layout for displaying dummy start and end nodes, use "showDummy = True or False"
        - Other optional layout parameters are available: 
            xlabel_size=None, ylabel_size=None,
            xtick_size=None, ytick_size=None, 
            title_size=None

        Reference: Find a general introduction to activity network analysis and the critical path method in:
            Vanhoucke, M., 2013, 
            "Project management with dynamic scheduling: Baseline scheduling, risk analysis and project control"
            Springer: 318 pages (2nd edition)
"""    

from Python_Modules.my_General_Functions import * #nameDummyStart and nameDummyEnd

import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

def transform_predecessor_to_successor_list(dependencies):
    # Initialize an empty dictionary for successors
    successor_dependency_list = {activity: [] for activity in dependencies.keys()}

    # Add entries for all the dependencies (this ensures that activities without predecessors are included)
    for activity in dependencies:
        for predecessor in dependencies[activity]:
            if predecessor not in successor_dependency_list:
                successor_dependency_list[predecessor] = []  # Initialize if predecessor not in the list
            successor_dependency_list[predecessor].append(activity)

    # Display the successor dependency list
    return successor_dependency_list

def transform_successor_to_predecessor_list(dependencies):
    ##### UNDER CONSTRUCTION: TO CHECK
    # Initialize an empty dictionary for successors
    predecessor_dependency_list = {}

    # Transform successors to predecessors
    for activity, successors in dependencies.items():
        for suc in successors:
            if suc not in predecessor_dependency_list:
                predecessor_dependency_list[suc] = []
            predecessor_dependency_list[suc].append(activity)

    # Display the successors matrix
    return predecessor_dependency_list   
    

def create_activity_network_dependencies(predecessors_list, successors_list, activity_names, debugInfo = False):

    # Assuming that at least a predecessors_list or a successors_list (or both) are defined

    if not predecessors_list and not successors_list:
        print("Error: Both predecessors_list and successors_list are missing or empty.")
        return None  
    if not predecessors_list: 
        predecessors_list = transform_successor_to_predecessor_list(successors_list)
    if not successors_list: 
        successors_list = transform_predecessor_to_successor_list(predecessors_list)
    

    # Create a set of all activities from both predecessors and successors lists
    all_activities = set(predecessors_list.keys()) | set(successors_list.keys())

    # Initialize the activity_dependencies dictionary
    activity_dependencies = {}

    # Merge predecessors and successors into a dictionary (using tuples of lists)
    for activity in all_activities:
        activity_dependencies[activity] = (
            predecessors_list.get(activity, []),  # List of predecessors
            successors_list.get(activity, [])     # List of successors
        )

    # Sort the activities by their order in `activity_names`
    sorted_activities = sorted(activity_dependencies.keys(), key=lambda x: list(activity_names.keys()).index(x))

    # Print the sorted result
    if debugInfo == True: 
        for activity in sorted_activities:
            predecessors, successors = activity_dependencies[activity]
            print(f"{activity}: Predecessors: {predecessors}, Successors: {successors}")

    # Print the activity_dependencies in sorted order
    sorted_activity_dependencies = {activity: activity_dependencies[activity] for activity in sorted_activities}
    if debugInfo == True: 
        print("Sorted activity_dependencies = ", sorted_activity_dependencies)
    return sorted_activity_dependencies


def construct_activity_network(activities, activity_dependencies, activity_names,
                               debugInfo=False, visualize=False, includeDummy=False):
    """
    Construct a directed graph (activity network) based on activities and their dependencies.

    Parameters
    ----------
    activities : dict
        Mapping of activity IDs to tuples of (duration, cost)
    activity_dependencies : dict
        Mapping of activity IDs to (predecessors, successors)
    activity_names : dict
        Mapping of activity IDs to readable activity names
    debugInfo : bool, optional
        If True, prints debugging information
    visualize : bool, optional
        If True, draws the network using a hierarchical layout
    includeDummy : bool, optional (default False)
        If False, nodes whose key are equal to keyDummyStart or keyDummyEnd 
        are excluded from the graph (and all their edges are removed).

    Returns
    -------
    G : networkx.DiGraph
        Directed activity network graph
    """

    # Create a directed graph
    G = nx.DiGraph()

    # Add activities as nodes (filtering dummies if needed)
#    for activity, (duration, cost) in activities.items():
#        act_name = activity_names.get(activity, "")
#        if not includeDummy and act_name in (nameDummyStart, nameDummyEnd):
#            continue
#        G.add_node(activity, duration=duration, cost=cost)
    for activity, (duration, cost) in activities.items():
        if not includeDummy and activity in (keyDummyStart, keyDummyEnd):
            continue
#        act_name = activity_names.get(activity, "")
        G.add_node(activity, duration=duration, cost=cost)
    
    # Add dependencies (edges) — skip if either node not included
    for activity, (predecessors, _) in activity_dependencies.items():
        if activity not in G.nodes:
            continue
        for predecessor in predecessors:
            if predecessor in G.nodes:
                G.add_edge(predecessor, activity)
                if debugInfo:
                    print(f"Added edge from {predecessor} to {activity}")

    # Debug information
    if debugInfo:
        print("\nNodes in the graph:")
        print(G.nodes(data=True))
        print("Edges in the graph:")
        print(G.edges())

    # Visualization (hierarchical layout)
    if visualize:
        plt.figure(figsize=(12, 8))
        
        # Identify start nodes (no predecessors)
        start_nodes = {n for n in G.nodes if G.in_degree(n) == 0}
        for node in G.nodes:
            try:
                shortest_paths = [
                    nx.shortest_path_length(G, source=s, target=node)
                    for s in start_nodes if nx.has_path(G, s, node)
                ]
                G.nodes[node]['subset'] = min(shortest_paths) if shortest_paths else float('inf')
            except nx.NetworkXNoPath:
                G.nodes[node]['subset'] = float('inf')

        pos = nx.multipartite_layout(G, subset_key='subset')

        # Draw nodes and edges
        nx.draw(
            G, pos, with_labels=True, node_size=2000, node_color='lightblue',
            edgecolors='black', arrows=True, connectionstyle="arc3,rad=0.05"
        )

        # Node labels
        node_labels = {
            node: f"{activity_names.get(node, node)}\nDur: {G.nodes[node]['duration']:.1f}\nCost: {G.nodes[node]['cost']}"
            for node in G.nodes()
        }
        nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=9)

        title = "Activity Network" + (" (with Dummies)" if includeDummy else " (without Dummies)")
        plt.title(title)
        plt.tight_layout()
        plt.show()

    return G


def calculate_critical_path(activities, activity_dependencies, activity_names, buffer = 0, debugInfo=False):
    """
    Calculate the Critical Path for a given project network.

    Parameters:
    -----------
    activities : dict
        Dictionary where each key is an activity ID, and each value is a tuple (duration, cost)
    activity_dependencies : dict
        Dictionary where each key is an activity ID, and each value is a tuple (predecessors, successors)
    activity_names : dict
        Mapping of activity IDs to readable names
    buffer (optional parameter)
        buffer should be zero in normal circumstances, but sometimes it can be set to a bigger value 
        (e.g. when optimizing resources in "resource_scheduler_optimizer") to calculate the slack with
        a backward step starting from a project duration > the critical path length
    debugInfo : bool, optional
        If True, prints detailed activity table and critical path

    Returns:
    --------
    This procedure constructs a project network graph G with dummies included by calling "construct_activity_network"
    G : networkx.DiGraph
        The resulting project network with all CPM attributes
    max_ef : float
        Project makespan (total duration)
    total_cost : float
        Total cost of all included activities
    activity_schedule : dict
        Dictionary with schedule details for each activity
    """

    # Create a directed graph (where dummies are included)
    G = construct_activity_network(activities, activity_dependencies, activity_names, includeDummy=True)
    
    # Forward pass: Calculate ES and EF
    for node in nx.topological_sort(G):
        predecessors = list(G.predecessors(node))
        if predecessors:
            G.nodes[node]['ES'] = max(G.nodes[p]['EF'] for p in predecessors)
        else:
            G.nodes[node]['ES'] = 0
        G.nodes[node]['EF'] = G.nodes[node]['ES'] + G.nodes[node]['duration']

    # Project duration
    max_ef = max(G.nodes[node]['EF'] for node in G.nodes)
    
    max_ef = max_ef + buffer

    # Total cost
    total_cost = sum(G.nodes[node]['cost'] for node in G.nodes)

    # Backward pass: Calculate LS and LF
    for node in reversed(list(nx.topological_sort(G))):
        successors = list(G.successors(node))
        if successors:
            G.nodes[node]['LF'] = min(G.nodes[s]['LS'] for s in successors)
        else:
            G.nodes[node]['LF'] = max_ef
        G.nodes[node]['LS'] = G.nodes[node]['LF'] - G.nodes[node]['duration']

    # Identify critical path
    epsilon = 1e-5
    critical_path = [
        node for node in G.nodes
        if abs(G.nodes[node]['ES'] - G.nodes[node]['LS']) < epsilon
    ]

    # Debug info
    if debugInfo:
        print("Activity | Duration | ES | EF | LS | LF | Float")
        for node in G.nodes:
            duration = G.nodes[node]['duration']
            es, ef, ls, lf = G.nodes[node]['ES'], G.nodes[node]['EF'], G.nodes[node]['LS'], G.nodes[node]['LF']
            total_float = ls - es
            print(f"   {node}    |    {duration:.2f}    | {es:.2f} | {ef:.2f} | {ls:.2f} | {lf:.2f} |  {total_float:.2f}")
        print("Critical Path:", ' -> '.join(critical_path))
        print(f"Project Duration: {max_ef:.2f}")

    # Build schedule dictionary
    activity_schedule = {}
    for node in G.nodes:
        duration = G.nodes[node]['duration']
        cost = G.nodes[node]['cost']
        start = G.nodes[node]['ES']
        end = start + duration
        slack = G.nodes[node]['LS'] - G.nodes[node]['ES']
        activity_schedule[node] = [(activity_names[node], duration, cost, start, end, slack)]

    return G, max_ef, total_cost, activity_schedule

def visualize_network(G, activity_names, 
                      showEdgeLabels=False,
                      showCP=True,
                      xtick_size=None, ytick_size=None,
                      title_size=None,
                      node_size=None,
                      showDummy=True,
                      ProgLevelHierarchy = True,
                      curvedEdges = False):
    """
    Visualize an activity network using a hierarchical (Multipartite) layout
    with full control over font sizes, node size, optional edge labels,
    and the ability to hide/show dummy start/end nodes.
    
    Parameters
    ----------
    G : nx.DiGraph
        The activity network graph
    activity_names : dict
        Mapping of node IDs to activity names
    showEdgeLabels : bool
        Whether to display edge labels
    xtick_size, ytick_size, title_size, node_size : int, optional
        Font sizes and node size for visualization. If None, uses global defaults.
    showDummy : bool
        If False, dummy start/end nodes and their edges are hidden.
    ProgLevelHierarchy : bool
        = Defines the horizontal depth of an activity in the network (based on precedence hierarchy).
        True: Progressive (precedence-based) level (recommended)
            An activity is placed at a level strictly greater than that of all its predecessors
            (i → j implies level(j) > level(i)).
        False: Shortest-path level
            An activity is placed according to the minimum number of arcs on any path from a start node to that activity.
    curvedEdges : bool
        True: The edges that span multiple levels are drawn curved to avoid overlapping other edges.
        False: All edges are drawn straight, regardless of length or potential overlap.
    """

    global Value_xtick_size, Value_ytick_size, Value_title_size, Value_node_size

    # Use provided parameters or fallback to global defaults
    xtick_size = xtick_size if xtick_size is not None else Value_xtick_size
    ytick_size = ytick_size if ytick_size is not None else Value_ytick_size
    title_size = title_size if title_size is not None else Value_title_size
    node_size = node_size if node_size is not None else Value_node_size

    infinity = 999999
    title = "Project Network with Critical Path" if showCP else "Project Network"

    # Filter nodes and edges if dummy nodes should be hidden
    if not showDummy:
        nodes_to_plot = [n for n in G.nodes() if n not in (keyDummyStart, keyDummyEnd)]
        G_plot = G.subgraph(nodes_to_plot).copy()
    else:
        nodes_to_plot = list(G.nodes())
        G_plot = G.copy()

    # Ensure ES, EF, LS exist
    for node in nodes_to_plot:
        if any(attr not in G_plot.nodes[node] for attr in ['ES', 'EF', 'LS']):
            G_plot.nodes[node].setdefault('ES', 0)
            G_plot.nodes[node].setdefault(
                'EF',
                G_plot.nodes[node].get('ES', 0) + G_plot.nodes[node].get('duration', 0)
            )
            G_plot.nodes[node].setdefault('LS', infinity)
            title = "Project Network"

    # Determine node colors
    node_colors = [
        'grey' if activity_names[node] in (nameDummyStart, nameDummyEnd)
        else (
            'red' if showCP and (G_plot.nodes[node]['LS'] - G_plot.nodes[node]['ES'] < 1e-5)
            else 'lightblue'
        )
        for node in nodes_to_plot
    ]

    # Layout: Compute hierarchical levels 
    if ProgLevelHierarchy:
        # Progressive (precedence-based) levels: i → j  ⇒  level(j) > level(i)
        levels = {}

        for node in nx.topological_sort(G_plot):
            preds = list(G_plot.predecessors(node))
            if not preds:
                levels[node] = 0
            else:
                levels[node] = max(levels[p] for p in preds) + 1

        nx.set_node_attributes(G_plot, levels, 'subset')

    else:
        # Shortest-path levels: minimum distance from any start node (in number of arcs)
        start_nodes = {n for n in G_plot.nodes() if G_plot.in_degree(n) == 0}

        for node in G_plot.nodes():
            try:
                shortest_paths = [
                    nx.shortest_path_length(G_plot, source=s, target=node)
                    for s in start_nodes if nx.has_path(G_plot, s, node)
                ]
                G_plot.nodes[node]['subset'] = (
                    min(shortest_paths) if shortest_paths else float('inf')
                )
            except nx.NetworkXNoPath:
                G_plot.nodes[node]['subset'] = float('inf')

    # Layout using the computed levels
    plt.figure(figsize=(12, 8))
    pos = nx.multipartite_layout(G_plot, subset_key='subset')
    
    # Draw nodes (straigth edges, default)
    if not curvedEdges:
        nx.draw(G_plot, pos, with_labels=False, node_size=node_size, node_color=node_colors, edgecolors='black')
 
    # Draw nodes (curved edges: to avoid overlaps)
    # = draws a clean, hierarchical project network showing activity dependencies with directed arcs. 
    #   - straight arrows indicate immediate precedence, 
    #   - curved arrows highlight edges that span multiple levels to avoid overlap. 
    #   Note: arrowheads are sized and positioned to touch node boundaries, ensuring clarity.
    else:
        nx.draw_networkx_nodes(G_plot, pos, node_size=node_size, node_color=node_colors, edgecolors='black')

        import math

        # Compute margins based on node size
        node_radius = math.sqrt(node_size) / 2
        target_margin = node_radius       # arrow tip touches node boundary
        source_margin = node_radius * 0.2 # small gap at source

        ax = plt.gca()  # current axis

        # Separate edges into straight (short) and curved (long)
        levels = nx.get_node_attributes(G_plot, 'subset')
        straight_edges = []
        curved_edges = []

        for u, v in G_plot.edges():
            if levels[v] - levels[u] > 1:
                curved_edges.append((u, v))
            else:
                straight_edges.append((u, v))

        # Draw straight edges
        nx.draw_networkx_edges(G_plot, pos, edgelist=straight_edges, arrows=True, arrowstyle='->', 
                               arrowsize=16, min_source_margin=source_margin, min_target_margin=target_margin, ax=ax)

        # Draw curved edges
        nx.draw_networkx_edges(G_plot, pos, edgelist=curved_edges, arrows=True, arrowstyle='->', arrowsize=16, 
                               connectionstyle='arc3,rad=0.2', min_source_margin=source_margin, 
                               min_target_margin=target_margin, ax=ax)

    # Node labels
    node_labels = {node: f"{node}" for node in G_plot.nodes()}
    nx.draw_networkx_labels(G_plot, pos, labels=node_labels, font_size=ytick_size)

    # Edge labels (optional)
    if showEdgeLabels:
        edge_labels = {(u, v): f"{u}->{v}" for u, v in G_plot.edges()}
        nx.draw_networkx_edge_labels(G_plot, pos, edge_labels=edge_labels, font_size=ytick_size)

    # Title and axis
    if title_size:
        plt.title(title, fontsize=title_size)

    plt.xticks(fontsize=xtick_size)
    plt.yticks(fontsize=ytick_size)
    plt.tight_layout()
    plt.show()


def show_gantt_chart(schedule, showCP=True, showDummy=False, showCost=False, showName=True,
                                    xlabel_size=None, ylabel_size=None,
                                    xtick_size=None, ytick_size=None,
                                    title_size=None):
    """
    Displays a Gantt chart from a schedule dictionary with optional font-size and bar-height control.

    Parameters
    ----------
    schedule : dict
        Dictionary with key: (activity name, duration, cost, start, end, slack)
    showCP : bool, optional
        Whether to highlight activities on the critical path (zero slack) in red. Default is True.
    showDummy : bool, optional
        Whether to include dummy start/end activities in the chart. Default is False.
    showCost : bool, optional
        Whether to display cost annotations inside bars. Default is False.
    xlabel_size, ylabel_size, xtick_size, ytick_size, title_size : float, optional
        Font sizes for X-axis label, Y-axis label, X-axis ticks, Y-axis ticks, and title.
        Defaults are taken from global variables if not provided.
    """

    # Use global variables if function parameters are None
    global Value_xlabel_size, Value_ylabel_size, Value_xtick_size, Value_ytick_size, Value_title_size

    xlabel_size = xlabel_size if xlabel_size is not None else Value_xlabel_size
    ylabel_size = ylabel_size if ylabel_size is not None else Value_ylabel_size
    xtick_size = xtick_size if xtick_size is not None else Value_xtick_size
    ytick_size = ytick_size if ytick_size is not None else Value_ytick_size
    title_size = title_size if title_size is not None else Value_title_size

    # Filter out dummy activities if requested      
    if not showDummy:
        filtered_schedule = {
            k: v for k, v in schedule.items()
            if k not in (keyDummyStart, keyDummyEnd)
        }
    else:
        filtered_schedule = schedule        

    # Assign a unique index to each activity
    activity_list = list(filtered_schedule.keys())
    activity_indices = {name: i for i, name in enumerate(activity_list)}

    # Adjust figure height dynamically
#    fig_height = max(5, min(0.5 * len(activity_list), 12))
#    fig, ax = plt.subplots(figsize=(15, fig_height))
    
    # TEST
    num_activities = len(activity_list)
    max_label_length = max(len(str(filtered_schedule[name][0][0])) for name in activity_list)
    # Dynamic figure height (same logic as before)
    fig_height = max(5, min(0.5 * num_activities, 12))  # 0.5 inch per activity, capped 5-12
    # Dynamic figure width (based on max label length)
    fig_width = max(10, min(0.5 * max_label_length, 20))  # 0.5 inch per character, capped 10-20
    # Create figure with dynamic size
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    epsilon = 1e-5

    # Create a bar for each activity
    for name, details in filtered_schedule.items():
        activity_name, duration, cost, start, finish, slack = details[0]
        y_pos = activity_indices[name]

        # Color based on critical path or slack
        if showCP:
            color = 'red' if slack < epsilon else 'skyblue'
        else:
            color = 'skyblue'

        ax.barh(y_pos, duration, left=start, color=color, edgecolor='black')

        # Annotate cost
        if showCost:
#            ax.text(start + duration / 2, y_pos, f'Cost: {cost:,}', ha='center', va='center', fontsize=ytick_size)
            ax.text(start + duration / 2, y_pos, f'Cost: {cost:}', ha='center', va='center', fontsize=ytick_size)

    # Set Y-axis labels (activity names)
#    ax.set_yticks(range(len(activity_list)))
#    ax.set_yticklabels(
#        [filtered_schedule[name][0][0] for name in activity_list],
#        fontsize=ytick_size
#    )
    
    ax.set_yticks(range(len(activity_list)))

    if showName:
        # Show activity names (from filtered_schedule)
        y_labels = [filtered_schedule[name][0][0] for name in activity_list]
    else:
        # Show activity keys (like 'A', 'B', 'C', etc.)
        y_labels = activity_list

    ax.set_yticklabels(y_labels, fontsize=ytick_size)

    

    # Labels, title, and X-axis tick labels
    ax.set_xlabel('Time', fontsize=xlabel_size)
    ax.set_ylabel('Activities', fontsize=ylabel_size)
    ax.set_xticklabels(ax.get_xticks(), fontsize=xtick_size)
    ax.set_title('Gantt Chart of Activities', fontsize=title_size)

    # Grid and layout
    ax.grid(axis='x')
    plt.tight_layout()
    plt.show()  
    
def show_design_structure_matrix(activity_dependencies,
                                 xlabel_size=None, ylabel_size=None,
                                 xtick_size=None,
                                 title_size=None,
                                 showDummy=False):
    
    xlabel_size = xlabel_size if xlabel_size is not None else Value_xlabel_size
    ylabel_size = ylabel_size if ylabel_size is not None else Value_ylabel_size
    xtick_size = xtick_size if xtick_size is not None else Value_xtick_size
    title_size = title_size if title_size is not None else Value_title_size

    # Sort activities by key but add dummy start at the beginning and dummy end at the end
#    activities = sorted(
#        activity_dependencies.keys(),
#        key=lambda x: (
#            0 if x == nameDummyStart else
#            2 if x == nameDummyEnd else
#            1,  # all other activities get middle priority
#            int(x) if x.isdigit() else x  # sort numerically if key is a number (also works alphabetically)
#            x   # then sort alphabetically by key
#        )
#    )
    
    activities = sorted(
        activity_dependencies.keys(),
        key=lambda x: (
            0 if x == keyDummyStart else
            2 if x == keyDummyEnd else
            1,  # middle priority for regular activities
            (0, x) if x.isalpha() else (1, int(x)) if x.isdigit() else (2, x)
        )
    )
    # Filter out dummy nodes if showDummy is False
    if not showDummy:
        activities = [a for a in activities if a not in (keyDummyStart, keyDummyEnd)]

    n = len(activities)

    # Adjust figure size dynamically
    fig_width = max(6, min(n * 0.5, 15))
    fig_height = max(6, min(n * 0.5, 15))

    # Create an empty NxN matrix
    dsm_matrix = np.zeros((n, n), dtype=str)

    # Mapping activity names to matrix indices
    activity_index = {activity: i for i, activity in enumerate(activities)}

    # Fill the matrix based on dependencies
    for activity, (_, successors) in activity_dependencies.items():
        if activity not in activity_index:
            continue  # Skip dummy nodes if filtered out
        for successor in successors:
            if successor not in activity_index:
                continue  # Skip dummy nodes if filtered out
            dsm_matrix[activity_index[activity], activity_index[successor]] = "x"

    # Plot DSM
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(activities, fontsize=xlabel_size)
    ax.set_yticklabels(activities, fontsize=ylabel_size)

    # Move x-axis labels to the top
    ax.xaxis.set_label_position('top')
    ax.xaxis.tick_top()
    
    # Create the DSM table
    for i in range(n):
        for j in range(n):
            text = dsm_matrix[i, j] if dsm_matrix[i, j] else ""
            ax.text(j, i, text, ha="center", va="center", fontsize=xtick_size)

    # Grid and aesthetics
    ax.set_xticks(np.arange(n + 1) - 0.5, minor=True)
    ax.set_yticks(np.arange(n + 1) - 0.5, minor=True)
    ax.grid(which="minor", color="black", linestyle='-', linewidth=0.5)
    ax.tick_params(which="minor", size=0)

    # Invert y-axis to match DSM convention
    ax.invert_yaxis()

    # Title
    plt.title("Design Structure Matrix (using x for succeeding activities)", fontsize=title_size)
    plt.show()

    