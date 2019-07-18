from parseOptions import parse_options
import os
import subprocess
import argparse


FIND = ["find", "folder_placeholder", "-name", "traj_aclib2.json"]


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

def write_options_file(folder, outname="options.txt"):

    if outname is None:
        outname = "options.txt"

    with open(outname, "w") as f:
        for path in get_file_paths(folder):
            options = get_options(path)
            path_split = path.split("/")
            name = "---".join(path_split[-6:-3])+"_"+path_split[-3]

            f.write("{} ; {}\n".format(name, options))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-f", "--folder", help="Folder where the acclingo results are located")
    parser.add_argument("-o", "--out", help="Output file name")

    args = parser.parse_args()

    write_options_file(args.folder, outname=args.out)