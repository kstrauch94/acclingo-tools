import os
import random
import stat
import argparse
import sys

FILE_PATH = os.path.dirname(os.path.abspath(__file__))

PBS_NAME = "acc.pbs"

ACC_TEMPLATE = os.path.join(FILE_PATH, "templates/acclingo_job.sh")

# if the name of the file with the instances changes at some point make sure to change it here and in the populate dir function
RUN_TEMPLATE = os.path.join(FILE_PATH, "templates/run_job.sh")

RUN_ACC_NAME = "run_acc.pbs"

def make_dir(path):
	if not os.path.exists(path):
		try:
			os.makedirs(path)
		except OSError as exc: # Guard against race condition
			if exc.errno != errno.EEXIST:
				raise
	
def write_bash_scripts(folder, instance_file, seed=123):
		
	with open(folder + os.sep + PBS_NAME, "w") as b:
		b.write(ACC_TEXT)

	with open(folder + os.sep + RUN_ACC_NAME, "w") as b:
		b.write(RUN_TEXT.format(instance_file=instance_file, seed=seed))

	make_executable(folder + os.sep + PBS_NAME)

	make_executable(folder + os.sep + "run_acc.pbs")

def make_executable(f):

	st = os.stat(f)
	os.chmod(f, st.st_mode | stat.S_IEXEC)

def prepare_experiments(files, sets_per_sample=3, folder_prefix="experiments"):

		
		run_acc_lines = []

		for _file in files:
			file_name = os.path.basename(_file)
			folder = folder_prefix + os.sep + file_name
			for s in range(1, sets_per_sample+1):
				sample_folder = folder + os.sep + f"sample-{s}"
				make_dir(sample_folder)
				write_bash_scripts(sample_folder, os.path.abspath(_file))
			
				run_acc_lines.append(os.path.abspath(sample_folder + os.sep + RUN_ACC_NAME + "\n"))

		# f_name is the name of the bash script to execute all acc of that type
		f_name = os.path.join(folder_prefix, "run_all.pbs")
		with open(f_name, "w") as b:
			b.write("#!/bin/bash\n\n")
			b.writelines(run_acc_lines)

		make_executable(f_name)


if __name__ == "__main__":
	#	  -: For now the names of the instances have to be UNIQUE! If not then
	#		 there will be conflics when creating the test and train folders.
	#	  -: rework the thing so it takes list of files instead of folders.
	#		 - we can still handle folders by reading the instances in them and create a file path file

	parser = argparse.ArgumentParser()

	parser.add_argument("-p", "--path-to-acc", help="path to the acclingo folder", default=None)

	parser.add_argument("--sets-per-sample", help="Amount of sets to create per sample(amount of configurations to learn from each sample)",
						type=int, default=3)

	parser.add_argument("--folder", help="Name of the folder where the experiments will be created",
						default="Experiments")

	parser.add_argument("--acc-template", help="Path to the acclingo job file template.",
						default=ACC_TEMPLATE)

	parser.add_argument("--run-template", help="Path to the run job file template.",
						default=RUN_TEMPLATE)

	parser.add_argument("--instance-files", help="Path to files constaining a list of instances with total paths! On each file, an instances uses 1 line.", 
						nargs="+", default=None)

	args = parser.parse_args()

	if args.path_to_acc is None:
		print("Please provide the path to the acclingo folder using the option -p or --path-to-acc")
		sys.exit(-1)

	with open(args.acc_template, "r") as f:
		ACC_TEXT = f.read()

	ACC_TEXT = ACC_TEXT.format(ptoa=os.path.abspath(args.path_to_acc))

	with open(args.run_template, "r") as f:
		RUN_TEXT = f.read()

	if args.instance_files is None or args.instance_files == []:
		print("Please provide at least one instance file.")
		sys.exit(-1)

	prepare_experiments(args.instance_files, args.sets_per_sample, folder_prefix=args.folder)




