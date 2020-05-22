import parseOptions
import os
import subprocess
import argparse



HEADER = """<runscript output="output-folder">

	<machine name="zuse" cpu="24x8xE5520@2.27GHz" memory="24GB"/>
	
	<config name="pbs-generic" template="templates/seq-generic.sh"/>
  
	<system name="clingo" version="1" measures="clingo" config="pbs-generic">
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
	    <folder path="{path}"></folder>
    </benchmark>
"""

PROJECT = """
	<project name="{name}" job="pbs-single">
		<runtag machine="zuse" benchmark="{benchmark}" tag="{tag}"/>
	</project>
"""

JOB ="""
 	<pbsjob name="pbs-single" timeout="{timeout}" runs="1" script_mode="timeout" walltime="{walltime}" cpt="8" partition="long"/>
"""
    

def craft_xml(xml_name, walltime, timeout, settings):

    with open(xml_name, "w") as f:
        f.write(HEADER)
    
        f.writelines(settings)
    
        f.write(SYSTEM_END)

        f.write(BENCHMARK.format(name="ALL", folders=benchmarks_folder))
        
        f.write(PROJECT.format(name="ALL", benchmark="ALL", tag="*all*"))

        f.write(JOB.format(walltime=walltime, timeout=timeout))

        f.write(FOOT)


def read_config_file(file_path):

	settings = []
	with open(file_path, "r") as f:
		for line in f.readlines():
			name, options = line.split(";")

			settings.append(SETTING.format(name=name, options=options, tag=name))

	return settings


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--config-file", help="path to folder created by extract_configs.py", default=None)
    parser.add_argument("-x", "--xml", help="Name of the resulting xml file", default=None)
    parser.add_argument("--walltime", help="Walltime for the benchmark. Input format: HH:MM:SS", default="48:00:00")
    parser.add_argument("--timeout", help="Timeout for each instance in seconds", type=int, default=300)

    args = parser.parse_args()

    craft_xml(args.xml, args.walltime, args.timeout, read_config_file(args.config_file))