import pandas as pd
from pandas import DataFrame
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import norm

def get_stats_from_file(filename):
    # read data from given file
    df = pd.read_table(filename, delimiter='|', skiprows = { 1 })
    # pre-process the status
    df["Status"].replace(to_replace="Yes", value=1, inplace=True)
    df["Status"].fillna(value=0, inplace=True)

    # return the dataframe
    return df[["Rating","Status"]]

def plot_distribution(data, filename, title):
    # set the plot style
    sns.set(font_scale=0.8, style="darkgrid")

    # initialize the figure
    f, ax = plt.subplots(figsize=(6, 10))

    # plot the total number of problems
    sns.set_color_codes("pastel")
    sns.barplot(x="total", y="rating", data=data, label="Total", color="b", orient="h")

    # plot the solved problems
    sns.set_color_codes("muted")
    sns.barplot(x="solved", y="rating", data=data, label="Solved", color="b", orient="h")

    # annotate the plots
    fontsize = 8
    for p in ax.patches:
        count = int(p.get_width())
        x = p.get_x() + p.get_width() + 1
        y = p.get_y() + p.get_height()/2 + 1.5*fontsize/100
        ax.annotate(count,xy=(x,y), fontsize=fontsize)

    # add a legend and axis label
    ax.legend(ncol=2, loc="lower right", frameon=True)
    ax.set(xticklabels=[], xlim=(0,180), ylabel="",
        xlabel="", title=title)
    sns.despine(left=True, bottom=True)
    plt.savefig(filename)

def process_stats(data):
    # group by rating and aggregate the status column
    df = data.groupby("Rating").agg({ "Status": [ "count", "sum" ] })

    # reset the index
    df.reset_index(inplace=True)

    # set the right column names
    df.columns = [ "rating", "total", "solved" ]
    return df

# initialize the division numbers and problem types
divisions = [ "1", "2", "3" ]
problem_types = [ "a", "b", "c", "d", "e", "f", "g", "h" ]

for div in divisions:
    print("Division " + div)
    print("Reading data from files...")

    div_stats = pd.DataFrame()

    for ptype in problem_types:
        filename = "div" + div + "/" + ptype + ".md"

        try:
            stats_from_file = get_stats_from_file(filename)
            div_stats = div_stats.append(stats_from_file)
        except:
            print("{}: File not found... Skipping...".format(filename))

    print("OK")
    print("Pre-processing data...")

    # pre-process data before plotting
    div_stats = process_stats(div_stats)

    print("OK")
    print("Plotting data...")

    # plot and save the plots
    plot_name = "stats-div{}.png".format(div)
    plot_title = "Division {}: Solved Problems by Rating".format(div)

    plot_distribution(div_stats, plot_name, plot_title)

    print("OK")
