from parseOptions import parse_options
import os
import subprocess
import argparse


FIND = ["find", "folder_placeholder", "-name", "traj_aclib2.json"]

DEFAULT_CONFIGS = {}
DEFAULT_CONFIGS["tweety"] = "tweety ; --eq=3 --trans-ext=dynamic --heuristic=Vsids,92 --restarts=L,60 --deletion=basic,50 --del-max=2000000 --del-estimate=1 --del-cfl=+,2000,100,20 --del-grow=0 --del-glue=2,0 --strengthen=recursive,all --otfs=2 --init-moms --score-other=all --update-lbd=less --save-progress=160 --init-watches=least --local-restarts --loops=shared"
DEFAULT_CONFIGS["trendy"] = "trendy ; --sat-prepro=2,20,25,240 --trans-ext=dynamic --heuristic=Vsids --restarts=D,100,0.7 --deletion=basic,50 --del-init=3.0,500,19500 --del-grow=1.1,20.0,x,100,1.5 --del-cfl=+,10000,2000 --del-glue=2 --strengthen=recursive --update-lbd=less --otfs=2 --save-progress=75 --counter-restarts=3,1023 --reverse-arcs=2 --contraction=250 --loops=common"
DEFAULT_CONFIGS["frumpy"] = "frumpy ; --eq=5 --heuristic=Berkmin --restarts=x,100,1.5 --deletion=basic,75 --del-init=3.0,200,40000 --del-max=400000 --contraction=250 --loops=common --save-progress=180 --del-grow=1.1 --strengthen=local --sign-def-disj=pos"
DEFAULT_CONFIGS["crafty"] = "crafty ; --sat-prepro=2,10,25,240 --trans-ext=dynamic --backprop --heuristic=Vsids --save-progress=180 --restarts=x,128,1.5 --deletion=basic,75 --del-init=10.0,1000,9000 --del-grow=1.1,20.0 --del-cfl=+,10000,1000 --del-glue=2 --otfs=2 --reverse-arcs=1 --counter-restarts=3,9973 --contraction=250"
DEFAULT_CONFIGS["jumpy"]  = "jumpy ; --sat-prepro=2,20,25,240 --trans-ext=dynamic --heuristic=Vsids --restarts=L,100 --deletion=basic,75,mixed --del-init=3.0,1000,20000 --del-grow=1.1,25,x,100,1.5 --del-cfl=x,10000,1.1 --del-glue=2 --update-lbd=glucose --strengthen=recursive --otfs=2 --save-progress=70"
DEFAULT_CONFIGS["handy"]  = "handy ; --sat-prepro=2,10,25,240 --trans-ext=dynamic --backprop --heuristic=Vsids --restarts=D,100,0.7 --deletion=sort,50,mixed --del-max=200000 --del-init=20.0,1000,14000 --del-cfl=+,4000,600 --del-glue=2 --update-lbd=less --strengthen=recursive --otfs=2 --save-progress=20 --contraction=600 --loops=distinct --counter-restarts=7,1023 --reverse-arcs=2"
DEFAULT_CONFIGS["base"] = "Base ;  "
DEFAULT_CONFIGS["heuristic-domain"] = "Heuristic-Domain ; --heuristic=Domain --dom-mod=neg,show"


def get_file_paths(folder):
    new_find = list(FIND)
    new_find[1] = folder
    
    paths = subprocess.check_output(new_find).decode("utf-8").split()

    return paths

def get_options(file_path, program=None):
    
    with open(file_path, "r") as f:
        for line in f:
            pass
    
    options = parse_options(line)
    
    if program is not None:
        test_options(options, program)

    return options

def test_options(options, program):

    #print(options)
    #TODO: dont harcode asprin as the program to use! make it a variable
    try:
        output = subprocess.check_output("echo a.  | {} {}".format(options, program), shell=True)
    except subprocess.CalledProcessError as e:
        output=e.output

    if b"\nSATISFIABLE" not in output and b"MODEL FOUND" not in output:
        raise ValueError("Option: {} \n DOES NOT WORK\noutput: {}".format(options, output))

    return 1 # all good :)

def write_options_file(folder, add_defaults=False, outname="options.txt"):

    if outname is None:
        outname = "options.txt"

    with open(outname, "w") as f:
        for path in get_file_paths(folder):
            options = get_options(path)
            path_split = path.split("/")
            name = "---".join(path_split[-6:-3])+"_"+path_split[-3]

            f.write("{} ; {}\n".format(name, options))

        if add_defaults:
            for config, config_str in DEFAULT_CONFIGS.items():
                f.write("{}\n".format(config_str))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-f", "--folder", help="Folder where the acclingo results are located")
    parser.add_argument("-o", "--out", help="Output file name")
    parser.add_argument("-d", "--add-defaults", action="store_true", help="Add the default options(jumpy, trendy, etc.) to the file.")

    args = parser.parse_args()

    write_options_file(args.folder, add_defaults=args.add_defaults, outname=args.out)