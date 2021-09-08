import os
import random
import stat
import argparse
import sys

FILE_PATH = os.path.dirname(os.path.abspath(__file__))

EXPERIMENTS = []

def make_dir(path):
	if not os.path.exists(path):
		try:
			os.makedirs(path)
		except OSError as exc: # Guard against race condition
			if exc.errno != errno.EEXIST:
				raise

# path   : string to relative or absolute path to be queried
# subdirs: tuple or list containing all names of subfolders that need to be
#		present in the directory
def all_dirs_with_subdirs(path, subdirs):
	# make sure no relative paths are returned, can be omitted
	#path = os.path.abspath(path)

	result = []
	for root, dirs, files in os.walk(path):
		if all(subdir in dirs for subdir in subdirs):
			result.append(root)
	return result


def all_files_in_folder(folder):
	all_files = []
	for path, subdirs, files in os.walk(folder):
		if "encodings" in path: #ignore file containing encoding
			continue
		for name in files:
			all_files.append(os.path.abspath(os.path.join(path, name)))

	return all_files

def get_base_name(path):
	# this gets the name of the parent folder

	# if there is a trailing backslash then delete it
	if path.endswith("/"):
		path = path[:-1]

	return os.path.basename(path)


def choose(instances, max_instances):
	# Training set is either all instances but 1 if the amount of instances
	# is lower than max_instances.
	# Else, a set of instances with length "max_instances.
	# Test set is the remainder of the instances

	if len(instances) <= max_instances:
		test = [random.choice(instances)]
		train = [f for f in instances if f not in test]
	
	else:
		train = random.sample(instances, max_instances)
		test = [f for f in instances if f not in train]

	return train, test
	 
# if the name of the file with the instances changes at some point make sure to change it here and in the RUN_ACC variable
def populate_dir(filenames, folder):
	make_dir(folder)
	
	with open(folder + os.sep + "instances.txt", "w") as f:
		f.write("\n".join(filenames))
	 
def create_sample(folder, train, test):

	populate_dir(test, folder + "test")
	populate_dir(train, folder + "train")

	EXPERIMENTS.append(folder + "train")

def choose_single(f, samples=3, max_instances=19, folder_prefix="Experiments"):

	files = all_files_in_folder(f)

	foldername = get_base_name(f)

	for sample in range(samples):
		train, test = choose(files, max_instances)

		folder = folder_prefix + os.sep +	"singles" + os.sep + foldername + os.sep + "sample_" + str(sample+1) + os.sep

		create_sample(folder, train, test)
		

def choose_multiple(multiples, missing, samples=3, max_instances=19, folder_prefix="Experiments"):
	
	files = []
	
	for f in multiples:
		files += all_files_in_folder(f)

	foldername = "missing_"+ get_base_name(missing)

	for sample in range(samples):
		# here choose returns test which is not what we want as testing
		# so we get the test files from the folder not in multiples
		train, test = choose(files, max_instances)
		test = all_files_in_folder(missing)

		folder = folder_prefix + os.sep + "multiple" + os.sep + foldername + os.sep + "sample_" + str(sample+1) + os.sep

		create_sample(folder, train, test)


def choose_all(classes_folders, samples=3, max_instances=19, inclusive_train=0, folder_prefix="Experiments"):
	# inclusive_train means that the train set has at least N instances for each class
	# classes are based on the folders given by classes_folders


	files = []
	
	for f in classes_folders:
		files += all_files_in_folder(f)

	classes = len(classes_folders)

	if inclusive_train:
		foldername="all_inclusive"
	else:
		foldername="all"

	for sample in range(samples):
		if inclusive_train > 0:
			# should test to see if taking n instance from each class is less than max instances
			train = []
			# get N instances from each class and add it to the training set
			for f in classes_folders:
				t, test = choose(all_files_in_folder(f), inclusive_train)
				train += t

			# take already chosen instances from available instances to chose from
			all_files_no_chosen = [f for f in files if f not in train]

			#chose remaining files form new all files no chosen variable
			t, test = choose(all_files_no_chosen, max_instances-len(train))
			train += t

			# get files not in training set into a test set
			test = [f for f in files if f not in train]

		else:
			train, test = choose(files, max_instances)
		
		folder = folder_prefix + os.sep + foldername + os.sep + "sample_" + str(sample+1) + os.sep
		create_sample(folder, train, test)

def choose_all_instances(classes_folders, sets_per_sample=3, folder_prefix="instance-files"):

	files = []

	for f in classes_folders:
		files += all_files_in_folder(f)

	folder = folder_prefix + os.sep + "all-files" + os.sep + "sample_1" + os.sep
	create_sample(folder, files, [])

def prepare_experiments(folders, do_single=False, do_multiple=False, do_all=False, use_all_instances=False, 
				do_all_inclusive=0, samples=3,
				max_instances=19, 
				folder_prefix="experiments"):

	
	if do_single or do_multiple:
		for f in folders:
			# this is the current folder
			# useful to know which folder to pass to choose_single
			# and which folder is missing when using choose_multiple
			single = f

			if do_single:
				# with single I will create the training using all but one(or a maximum amt)
				# and use the rest as testing
				choose_single(f, folder_prefix=folder_prefix, samples=samples,
						max_instances=max_instances)

			if do_multiple:
				# with multiple it will choose 19 instances randomly and create training set
				# test set is single folder
				multiple = [fdr for fdr in folders if fdr != f]
				choose_multiple(multiple, missing=single, folder_prefix=folder_prefix,
						        samples=samples, max_instances=max_instances)

	if do_all:
		choose_all(folders, inclusive_train=0, folder_prefix=folder_prefix, 
			 samples=samples, max_instances=max_instances)

	if do_all_inclusive:
		choose_all(folders, inclusive_train=do_all_inclusive, folder_prefix=folder_prefix, 
			 samples=samples, max_instances=max_instances)

	if use_all_instances:
		choose_all_instances(folders, sets_per_sample, folder_prefix=folder_prefix)


if __name__ == "__main__":
	# TODO -: implement a way to pass the folders. Right now they are a list in python.
	#	-: For now the names of the instances have to be UNIQUE! If not then
	#	   there will be conflics when creating the test and train folders.
	#	-: rework the thing so it takes list of files instead of folders.
	#	   - we can still handle folders by reading the instances in them and create a file path file
	#	-: add more documentation to the functions

	parser = argparse.ArgumentParser()

	parser.add_argument("-s", "--single", help="For each domain(folder), create a set of samples",
			  action="store_true")

	parser.add_argument("-m", "--multiple", help="For each domain(folder), create a set of samples using all other domains as training set and using the missing domain and test set",
			  action="store_true")

	parser.add_argument("-a", "--all", help="Aggregate all domains and create samples",
			  action="store_true")

	parser.add_argument("-i", "--all-inclusive", help="Aggregate all domains and create samples while guaranteeing that each sample has at least N instance from each domain",
				type=int, default=0)

	parser.add_argument("--use-all-instances", help="Aggregate all domains and use all instances in the training while having none in the testing set. The --samples option is ignored.", action="store_true")


	parser.add_argument("--max-instances", help="Maximum amount of instances a sample can have. If this number is higher than the amount of instances available then the training set is n-1 instances and the testing set is the reamining instance",
				type=int, default=19)

	parser.add_argument("--folder", help="Name of the folder where the files will be stored",
				default="Experiments")

	parser.add_argument("--samples", help="amount of samples to create",
				type=int, default=3)

	parser.add_argument("--instance-folders", help="Path to the instance folders. Each folder is separated by a space. Each folder will be treated as a domain", 
				nargs="+", default=[])

	args = parser.parse_args()

	if args.instance_folders == []:
		print("Please provide at least one instance folder.")
		sys.exit(-1)

	prepare_experiments(args.instance_folders, do_single=args.single, do_multiple=args.multiple, do_all=args.all, do_all_inclusive=args.all_inclusive, use_all_instances=args.use_all_instances,
					samples=args.samples, max_instances=args.max_instances, folder_prefix=args.folder)


