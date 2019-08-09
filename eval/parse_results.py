import sys
import os
import subprocess
import errno
import itertools
import argparse

import pandas as pd
import numpy as np
import json
import time
import comparing_tool



OPT_VAL_PATH = "/home/klaus/Desktop/Work/TT-opt/results-TT/TT-opt-only/TT-opt-only.csv"
OPTIMAL_PATH = "/home/klaus/Desktop/Work/TT-opt/results-TT/TT-test-optimal/TT-test-optimal.csv"

bestbound_path = "/home/klaus/Desktop/Work/TT-opt/bestboundtest.csv"

NAME_PREFIX = "clingo-1/oppt-tae-3sets-10-samples-i-45instances-45min-115runs---"
NAME_PREFIX_2 = "clingo-1/"

NAME_SPLIT = "-||-"

def strip_name(name):
    # strip any folder names
    return name.split("/")[-1]

def create_folder(path):
    """
    from http://stackoverflow.com/posts/5032238/revisions

    :param path: folder to be created
    """
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return itertools.chain.from_iterable(itertools.combinations(s, r) for r in range(1, len(s)+1))

def compare_to_best(best, data):

    df = pd.DataFrame()
    df_percent = pd.DataFrame()

    best_no_zero = best.replace(to_replace=0, value=1, inplace=False)

    for col in data.columns:
        df[col] = (data[col] - best["bounds"]) 

        df_percent[col] = data[col].replace(to_replace=0, value=1, inplace=False) / best_no_zero["bounds"]

    return df, df_percent

def get_best(data_optval, data_optimal, best, folder):

    comp_df, perc_df = compare_to_best(best, data_optval)

    unique_cols, unique_count = unique_vals_in_cols(data_optval)

    mean, geometric_mean = get_mean_and_geometric_mean(perc_df)

    df = pd.DataFrame()

    df["worse"] = (comp_df > 0).apply(np.count_nonzero)
    df["better"] = (comp_df < 0).apply(np.count_nonzero)
    df["same"] = (comp_df == 0).apply(np.count_nonzero)
    df["score"] = df["better"] + df["same"]

    df["optimal_count"] = optimal_count(data_optimal)

    df["unique_count"] = unique_count

    df["perc_mean"] = mean

    df["perc_geometric_mean"] = geometric_mean

    new_folder_name = "comparisons"
    new_folder = os.path.join(folder, new_folder_name)
    create_folder(new_folder)

    to_csv_sorted(df, [["score", "better", "same"], ["same", "better"], ["better", "same"], ["optimal_count", "score"], ["unique_count", "score"], ["perc_mean"], ["perc_geometric_mean"]], new_folder)

    to_csv_normal(comp_df, best, os.path.join(new_folder, "compared-to-best.csv"))
    to_csv_normal(perc_df, best, os.path.join(new_folder, "percent-to-best.csv"), mean=True)

    return comp_df, perc_df, df


def to_csv_sorted(df, columns_to_sort, new_folder):

    for cols in columns_to_sort:
        df.sort_values(cols, ascending=[False]*len(cols)).to_csv(os.path.join(new_folder, "sortby-{}.csv".format(cols[0])))

def get_mean_and_geometric_mean(data):
    ## geomtric mean can be very unrealiable
    # values can multiply to over max int
    # doing a 300th root of a number is not very precide
    # etc.
    # Should try to implemet geometric mean using logs

    mean_vals = data.mean()
    row_count = len(data.index)
    geometric_mean_vals = np.power(data.iloc[:,:row_count].prod(axis=0),1.0/row_count)

    return mean_vals, geometric_mean_vals

def to_csv_normal(data, best, name, mean=False):

    data["bounds"] = best["bounds"]
    # the -1 is because data.columns has bounds as the last
    # here we rearrange them so bounds is first
    columns = ["bounds"] + list(data.columns[:-1])
    data = data[columns].copy()

    if mean:
        mean, geo_mean = get_mean_and_geometric_mean(data)
        data["mean"] = mean
        data["geomtric_mean"] = geo_mean
    
    data.to_csv(name)

def to_csv_index(data, indexes, best, name, mean=False):

    data["bounds"] = best["bounds"]
    columns = ["bounds"] + list(indexes)
    data = data[columns].copy()

    if mean:
        data.loc["mean"] = data.mean()

    data.to_csv(name)

def virtual_best(data, columns):

    # copy orinal dataframe
    df = data.copy()
    combo_rank = {}
    for combo in powerset(columns):
        k = len(combo)
        combo_list = list(combo)
        if k < 2:
            # only get k-way configs for k > 1
            continue
        if k not in combo_rank:
            combo_rank[k] = []

        # add the min of the combo to the df as a new config
        name = NAME_SPLIT.join(combo_list)
        df[name] = data[combo_list].min(axis=1)
        combo_rank[k].append(name)

    #calculate mean_rank for all the configs

    mean_ranks = df.rank(axis=1).mean()

    # go through each list of rank conbos
    # and select the one with the lowest rank
    columns_to_use = []
    best_kway = {}
    for key, config_combos in combo_rank.items():
        best_val = mean_ranks[config_combos].min()
        best_name = mean_ranks[config_combos].idxmin()
        best_kway[key] = {"mean_rank": best_val, "configs": best_name.split(NAME_SPLIT)}

        columns_to_use.append(best_name)

    columns_to_use += list(columns)

    return best_kway, mean_ranks[columns_to_use].sort_values()


def virtual_to_csv(data, cols, name, data_optimal):

    kway_combos, ranks = virtual_best(data, cols)

    optimal_series = optimal_count(data_optimal, ranks.index)

    df = pd.DataFrame()
    df["mean rank"] = ranks
    df["optimal"] = optimal_series

    k_ways = [k for k in ranks.index if NAME_SPLIT in k]
    singles = [k for k in ranks.index if NAME_SPLIT not in k]

    virtual_best_members(k_ways, singles, name+"members")

    virtual_best_list_members(k_ways, name+"member-list")

    df.rename(index=virtual_rename, inplace=True)
    df.to_csv(name)


class Membership:

    def __init__(self, name):
        self.name = name
        self.is_member = []
        self.count = 0

    def add(self, k):
        self.is_member.append(k)

        self.count += 1

    def belongs_to(self, k):
        if k in self.is_member:
            return "X"

        return " "


def virtual_best_members(k_ways, singles, name):

    membership = []

    max_k = len(k_ways)+1

    for single in singles:
        membership.append(Membership(single))
        for kw in sorted(k_ways):
            k = len(kw.split(NAME_SPLIT))
            if single in kw:
                membership[-1].add(k)

    membership.sort(key=lambda x: x.count, reverse=True)

    with open(name.replace(".csv","")+".csv", "w") as f:
        range_str = [str(i) for i in range(2,max_k+1)]

        f.write(",{}\n".format(",".join(range_str)))
        for single in membership:
            line = single.name
            for k in range(2,max_k+1):
                line += "," + single.belongs_to(k)
            f.write(line+"\n")

def virtual_best_list_members(k_ways, name):

    with open(name.replace(".csv","")+".csv", "w") as f:
        for kw in k_ways:
            k = len(kw.split(NAME_SPLIT))
            f.write("{}: {}\n".format(k, "  ".join(kw.split(NAME_SPLIT))))


def optimal_count(data_optimal, columns=None):
    if columns is None:
        columns = list(data_optimal.columns)

    series = pd.Series()

    for col in columns:
        # split columns if necesary
        cols = col.split(NAME_SPLIT)

        series[col] = data_optimal[cols].max(axis=1).sum()

    return series

def virtual_rename(name):
    if NAME_SPLIT in name:
        return "best-{}-way".format(len(name.split(NAME_SPLIT)))
    else:
        return name

def best_n_by_score(cols, df_score, best_n):

    #grab the best n configs by score from the uniques
    # first we grab only the configs we want and the socres of those
    # configs, then we sort
    # finally we grab the first n values of the index list
    cols = df_score.loc[cols,"score"].sort_values(ascending=False).index[:best_n]

    return cols

def unique_vals_in_cols(data):
    # gets all columns with unique values

    # best for every instance
    df = data.subtract(data.min(axis=1), axis="index")

    # get unique configs
    # configs where 0 is present on a particular instance 
    # and no other config has that value
    # eq(0) makes sure that the row has a 0
    # sum(1) makes sure to sum all occurences of the 0
    # eq(1) then makes sure that there is only 1 such ocurrence
    # this gives us for which ROWS(instances) there are unique values
    df = df[df.eq(0).sum(1).eq(1)]
    # at this point, each row in df has exactly 1 value that is 0

    #TODO: Sum number of 0s to count the number of uniques per column
    unique_count = df.eq(0).sum(0).sort_values(ascending=False)

    # (df != 0) builds truth df with nonzero values
    # .all(axis(0)) makes a truth array for every column saying that 
    # ALL values are nonzero
    # then, we save the columns where all values are nonzero(no unique)
    df_all_vall_nonzero = df.loc[:, (df != 0).all(axis=0)]

    # here we get all columns not present in the above df
    # since the above df has columns with no unique values
    # this new set will be all solumns with at least 1 unique value
    nonzero_cols = [col for col in list(df.columns) if col not in list(df_all_vall_nonzero.columns)]
    return nonzero_cols, unique_count

def read_data(data_file, nonval_replacement=None):
    #nonval_replacement has to be a function that takes a row as an argument and returns a value
    if nonval_replacement is None:
        nonval_replacement = lambda row: row.max()

    # load data
    data = pd.read_csv(data_file, header=0, index_col=0)
    data.rename_axis("instances")

    data = data.drop(data.index[[0]])

    data.rename(columns=lambda n: n.replace(NAME_PREFIX, "").replace(NAME_PREFIX_2, ""), inplace=True)
    
    data.rename(index=lambda n: n.split("/")[1].replace(".gz", ""), inplace=True)

    data.drop("ud3_erlangen2013_2")

    for col in data.columns:
        data[col] = data[col].astype(float)

    # replace nan values using the function given in nonval_replacement
    data = data.apply(lambda row: row.fillna(nonval_replacement(row)), axis=1)

    return data

def write_param_files(param_file, configs, output_name):
    # read the file with the config names and its parameters and
    # extract only the configs we want
    # then write to a separate file
    with open(param_file, "r") as f:
        lines = f.readlines()

        with open(output_name, "w") as out:
            for line in lines:
                if any(line.startswith(config) for config in configs):
                    out.write(line)


def do_virtual_best(data, config_names, best_n, data_optimal, VB_name, folder_name):
    create_folder(folder_name)

    t = time.time()
    print("calculating virtual best based on {}".format(VB_name))
    virtual_to_csv(data, config_names, os.path.join(folder_name,"{}-top{}.csv".format(VB_name, best_n)), data_optimal)
    print("time taken: {}".format(time.time() - t))

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--optimal", help="path to the csv optimal file.", default=None)
    parser.add_argument("--optval", help="path to the csv optimum value file", default=None)
    parser.add_argument("--best", help="path to the best bounds file", default=None)
    parser.add_argument("--vb-n", type=int, help="How many configuration to use for the virtual best", default=None)
    parser.add_argument("--options-file", help="Path to the file generated by extract_configs.py")
    args = parser.parse_args()

    data_optval = read_data(args.optval, nonval_replacement=lambda row: 2 * row.max())
    data_optimal = read_data(args.optimal, nonval_replacement=lambda row: 0)

    # load best bound data
    best = pd.read_csv(args.best, header=None, index_col=0)
    best.rename_axis("instances")
    best.columns = ["bounds"]
    best.drop("ud3_erlangen2013_2")

    folder = "test-csv-folder"
    create_folder(folder)

    comp_df, perc_df, data_summary = get_best(data_optval, data_optimal, best, folder)

    # best singular if better than best
    # here we get all configs where at least one instance has a better
    # optimum value than the best bound
    comp_df[comp_df < 0].dropna(how="all").dropna(axis=1, how="all").to_csv(os.path.join(folder,"better_singular.csv"))
    
    unique_cols = data_summary.index[data_summary['unique_count'] != 0].tolist()
    unique_count = data_summary["unique_count"]

    best_n = args.vb_n

    best_n_unique_score = best_n_by_score(unique_cols, data_summary, best_n)
    
    best_n_unique_count = unique_count.index[:best_n]

    best_n_all = best_n_by_score(list(data_optval.columns), data_summary, best_n)

    # top cols by mean_rank
    best_n_mean_rank = data_optval.rank(axis=1).mean().sort_values().index[:best_n]

    # top cols by optimal count
    best_n_optimal_count = data_summary["optimal_count"].sort_values(ascending=False).index[:best_n]


    do_virtual_best(data_optval, best_n_unique_score, best_n, data_optimal,"by-unique-score", os.path.join(folder, "VB-uniques-score"))

    do_virtual_best(data_optval, best_n_unique_count, best_n, data_optimal,"by-unique-count", os.path.join(folder, "VB-uniques-count"))

    do_virtual_best(data_optval, best_n_all, best_n, data_optimal,"by-score", os.path.join(folder, "VB-best-by-scrore"))

    do_virtual_best(data_optval, best_n_mean_rank, best_n, data_optimal,"by-mean-rank", os.path.join(folder, "VB-mean_rank"))

    do_virtual_best(data_optval, best_n_optimal_count, best_n, data_optimal,"by-optimal-count", os.path.join(folder, "VB-optimal-count"))

    parameter_folder = "parameter-files"
    new_folder = os.path.join(folder, parameter_folder)
    create_folder(new_folder)

    # write option files
    write_param_files(args.options_file, best_n_unique_score, os.path.join(new_folder,"unique-score-options.txt"))
    write_param_files(args.options_file, best_n_unique_count, os.path.join(new_folder,"unique-count-options.txt"))
    write_param_files(args.options_file, best_n_all, os.path.join(new_folder,"bestall-options.txt"))
    write_param_files(args.options_file, best_n_mean_rank, os.path.join(new_folder,"mean_rank-options.txt"))
    write_param_files(args.options_file, best_n_optimal_count, os.path.join(new_folder,"optimal_count-options.txt"))


    to_compare = list(zip(range(best_n - 1), range(1, best_n)))
    comparing_tool.compare_configs_by_number(os.path.join(new_folder,"unique-score-options.txt"), to_compare, os.path.join(folder, "VB-uniques-score") + os.sep + "compared_options.csv")
    comparing_tool.compare_configs_by_number(os.path.join(new_folder,"unique-count-options.txt"), to_compare, os.path.join(folder, "VB-uniques-count") + os.sep + "compared_options.csv")
    comparing_tool.compare_configs_by_number(os.path.join(new_folder,"bestall-options.txt"), to_compare, os.path.join(folder, "VB-best-by-scrore") + os.sep + "compared_options.csv")
    comparing_tool.compare_configs_by_number(os.path.join(new_folder,"mean_rank-options.txt"), to_compare, os.path.join(folder, "VB-mean_rank") + os.sep + "compared_options.csv")
    comparing_tool.compare_configs_by_number(os.path.join(new_folder,"optimal_count-options.txt"), to_compare, os.path.join(folder, "VB-optimal-count") + os.sep + "compared_options.csv")