from parseOptions import parse_options
import os
import subprocess
import argparse


FIND = ["find", "folder_placeholder", "-name", "traj_aclib2.json"]

HEADER = """<runscript output="asprin-opt">

	<machine name="zuse" cpu="24x8xE5520@2.27GHz" memory="24GB"/>
	
	<config name="pbs-generic" template="templates/seq-generic2.sh"/>
  
	<system name="asprin" version="1" measures="clingo" config="pbs-generic">
"""

SYSTEM_END = "</system>"

FOOT = """
</runscript>
"""

SETTING = """
        <setting name="{name}" cmdline="'--stats --quiet=2 {options}'" pbstemplate="templates/single.pbs" tag="{tag}" />
"""

BENCHMARK = """
    <benchmark name="{name}">
	    {folders}
    </benchmark>
"""
FOLDER = """<folder path="{path}"></folder>"""

PROJECT = """
	<project name="{name}" job="pbs-single">
		<runtag machine="zuse" benchmark="{benchmark}" tag="{tag}"/>
	</project>
"""

JOB ="""
 	<pbsjob name="pbs-single" timeout="{timeout}" runs="1" script_mode="timeout" walltime="{walltime}" cpt="8" partition="long"/>
"""
class Experiment():
    
    def __init__(self, folder, program=None, exps=3, sets=3):
        
        # tag is also the name
        # the -3 from the split is to include the Experiments folder + type(all, single, multiple)
        # + domain(all, bio-expansion, ...)
        namesplit = folder.split("/")[-4:]
        folderpath = "/".join(namesplit)
        self.name = "---".join(namesplit)
        self.program = program

        self.experiments = {}

        for s in range(1, sets + 1):
            self.experiments[s] = {}
            self.experiments[s]["name"] = "{}_set_{}".format(self.name, s)
            fpath = folderpath +  os.sep + "set_" + str(s)
            self.experiments[s]["options"] = self.get_options(fpath)
        
            folders = [FOLDER.format(path=os.path.abspath(fpath + os.sep + "train")),
                   FOLDER.format(path=os.path.abspath(fpath + os.sep + "test" )) ]
            self.experiments[s]["folders"] = folders
   

    def get_options(self, folder_path):
        
        new_find = list(FIND)
        new_find[1] = folder_path
        
        output = subprocess.check_output(new_find).strip()

        
        if output == b"":
            print(output)
            print(new_find)
            print(folder_path)
            return ""

        with open(output, "r") as f:
            for line in f:
                pass
        
        options = parse_options(line)
        
        if self.program is not None:
            self.test_options(options, program)

        return options

    def test_options(self, options, program):

        #print(options)
        #TODO: dont harcode asprin as the program to use! make it a variable
        try:
            output = subprocess.check_output("echo a.  | {} {}".format(options, program), shell=True)
        except subprocess.CalledProcessError as e:
            output=e.output

        if b"\nSATISFIABLE" not in output and b"MODEL FOUND" not in output:
            raise ValueError("Option: {} \n DOES NOT WORK\noutput: {}".format(options, output))

        return 1 # all good :)

    def get_settings(self, with_base=True):
        settings = []

        for set_num, s in self.experiments.items():
            settings.append(SETTING.format(name=s["name"], options=s["options"], tag=s["name"]))
        
            if with_base:
                settings.append(SETTING.format(name="base-" + s["name"], options="", tag=s["name"]))

        return settings

    def get_benchmark(self):
        
        benchmarks = []
        for exp_num, exp in self.experiments.items():
            benchmarks.append(BENCHMARK.format(name=exp["name"], folders="\n\t\t".join(exp["folders"])))

        return benchmarks

    def get_project(self):
        projects = []
        for exp_num, exp in self.experiments.items():  
            projects.append(PROJECT.format(name=exp["name"], benchmark=exp["name"], tag=exp["name"]))
        
        return projects

def all_dirs_with_subdirs(path, subdirs):
    # make sure no relative paths are returned, can be omitted
    #path = os.path.abspath(path)

    result = []
    for root, dirs, files in os.walk(path):
        if all(subdir in dirs for subdir in subdirs):
                result.append(root)
    return result


def create_xml_bench():
    settings = []
    benchmarks = []
    projects = []

    for directory in all_dirs_with_subdirs(".", ["experiment-1"]):
        exp = Experiment(directory)
        settings.append("\n".join(exp.get_settings()))

        benchmarks.append("\n".join(exp.get_benchmark()))

        projects.append("\n".join(exp.get_project()))
    

    with open("asprin_bench_51.xml", "w") as f:
        f.write(HEADER)
        
        f.writelines(settings)
        f.write(SYSTEM_END)

        f.writelines(benchmarks)
        
        f.writelines(projects)

        f.write(JOB)

        f.write(FOOT)

def create_xml_bench_all(folder, xml_name, program, timeout, walltime):
    settings = []
    benchmarks = []
    projects = []

    for directory in all_dirs_with_subdirs(folder, ["set_1"]):
        print(directory)
        exp = Experiment(directory)
        settings.append("\n".join(exp.get_settings(with_base=False)))
    
    print("Amount of settings: ", len(settings))

    with open(xml_name, "w") as f:
        f.write(HEADER)
    
        f.write(SETTING.format(name="Base", options="", tag="base"))       
        f.write(SETTING.format(name="Heuristic-Domain", options="--heuristic=Domain --dom-mod=neg,show", tag="base-heuristic")) 
        f.write(SETTING.format(name="frumpy", options="--configuration=frumpy", tag="frumpy"))
        f.write(SETTING.format(name="jumpy", options="--configuration=jumpy", tag="jumpy"))
        f.write(SETTING.format(name="tweety", options="--configuration=tweety", tag="tweety"))
        f.write(SETTING.format(name="handy", options="--configuration=handy", tag="handy")) 
        f.write(SETTING.format(name="crafty", options="--configuration=crafty", tag="crafty")) 
        f.write(SETTING.format(name="trendy", options="--configuration=trendy", tag="trendy")) 

        f.writelines(settings)
        f.write(SYSTEM_END)

        f.write(BENCHMARK.format(name="ALL", folders=FOLDER.format(path=os.path.abspath("asprin_benchmarks"))))
        
        f.write(PROJECT.format(name="ALL", benchmark="ALL", tag="*all*"))

        f.write(JOB.format(walltime=walltime, timeout=timeout))

        f.write(FOOT)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-f", "--folder", help="path to folder created by folder_bench_gen.py", default=None)
    parser.add_argument("-x", "--xml", help="Name of the resulting xml file", default=None)
    parser.add_argument("-p", "--program", help="Program with which the parsed configs will be tested", default=None)
    parser.add_argument("--walltime", help="Walltime for the benchmark. Input format: HH:MM:SS", default="48:00:00")
    parser.add_argument("--timeout", help="Timeout for each instance in seconds", type=int, default=300)

    args = parser.parse_args()

    create_xml_bench_all(args.folder, args.xml, args.program, args.timeout, args.walltime)


        

    

