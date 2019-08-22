import os
import random
import stat
import argparse
import sys

#FOLDERS = ["~/TT-opt/acclingo/testinstances/"]
FOLDERS = ["/home/klaus/Desktop/Work/TT-opt/acclingo/testinstances/"]

FILE_PATH = os.path.dirname(os.path.abspath(__file__))

PBS_NAME = "acc.pbs"
ACC_TEMPLATE = os.path.join(FILE_PATH, "templates/acclingo_job.sh")

# if the name of the file with the instances changes at some point make sure to change it here and in the populate dir function
RUN_TEMPLATE = os.path.join(FILE_PATH, "templates/run_job.sh")

EXPERIMENTS = {"all": [], "single": [], "multiple": []}

def make_dir(path):
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

# path   : string to relative or absolute path to be queried
# subdirs: tuple or list containing all names of subfolders that need to be
#          present in the directory
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
    
    #for f in filenames:
    #    fname = get_base_name(f)
    #    with open(folder + os.sep + fname, "w") as out:
    #        out.write(INCLUDE.format(path=f))
     
    with open(folder + os.sep + "instances.txt", "w") as f:
        f.write("\n".join(filenames))
   
def create_sample(exp_type, sample, sets_per_sample, folder, foldername, test, train):
    for s in range(sets_per_sample):
        set_folder = folder + "set_{}".format(s+1) + os.sep

        populate_dir(test, set_folder + "test")
        populate_dir(train, set_folder + "train")

        # has to be done after populating so dir exists
        write_bash_scripts(set_folder, seed=s+1)

        EXPERIMENTS[exp_type].append(set_folder)

    

def write_bash_scripts(folder, seed=123):
        
    with open(folder + os.sep + PBS_NAME, "w") as b:
        b.write(ACC_TEXT)

    with open(folder + os.sep + "run_acc.pbs", "w") as b:
        b.write(RUN_TEXT.format(seed=seed))

    make_executable(folder + os.sep + PBS_NAME)

    make_executable(folder + os.sep + "run_acc.pbs")

def make_executable(f):

    st = os.stat(f)
    os.chmod(f, st.st_mode | stat.S_IEXEC)


def choose_single(f, samples=3, sets_per_sample=3, max_instances=19, folder_prefix="Experiments"):

    files = all_files_in_folder(f)

    foldername = get_base_name(f)

    for sample in range(samples):
        train, test = choose(files, max_instances)

        folder = folder_prefix + os.sep +  "singles" + os.sep + foldername + os.sep + "sample_" + str(sample+1) + os.sep

        create_sample("single", sample, sets_per_sample, folder, foldername, train, test) #sample_obj
            

def choose_multiple(multiples, missing, samples=3, sets_per_sample=3, max_instances=19, folder_prefix="Experiments"):
    
    files = []
    
    for f in multiples:
        files += all_files_in_folder(f)

    foldername =  "missing_"+ get_base_name(missing)

    for sample in range(samples):
        # here choose returns test which is not what we want as testing
        # so we get the test files from the folder not in multiples
        train, test = choose(files, max_instances)
        test = all_files_in_folder(missing)

        folder = folder_prefix + os.sep + "multiple" + os.sep + foldername + os.sep + "sample_" + str(sample+1) + os.sep

        create_sample("multiple", sample, sets_per_sample, folder, foldername, train, test)


def choose_all(classes_folders, samples=3, sets_per_sample=3, max_instances=19, inclusive_train=0, folder_prefix="Experiments"):
    # inclusive_train means that the train set has at least N instances for each class
    # classes are based on the folders given by classes_folders


    files = []
    
    for f in classes_folders:
        files += all_files_in_folder(f)

    classes = len(classes_folders)

    # we have all/all folder because of the PATHTOACC var in ACC is 3 folders up, so we need to be 2 folders deep here
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
        
        folder = folder_prefix + os.sep + "all" + os.sep + foldername + os.sep + "sample_" + str(sample+1) + os.sep
        create_sample("all", sample, sets_per_sample, folder, foldername, train, test)


def prepare_experiments(folders, do_single=False, do_multiple=False, do_all=False, 
                        do_all_inclusive=0, samples=3, sets_per_sample=3,
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
                              sets_per_sample=sets_per_sample, 
                              max_instances=max_instances)

            if do_multiple:
                # with multiple it will choose 19 instances randomly and create training set
                # test set is single folder
                multiple = [fdr for fdr in folders if fdr != f]
                choose_multiple(multiple, missing=single, folder_prefix=folder_prefix,
                                samples=samples, sets_per_sample=sets_per_sample, 
                                max_instances=max_instances)

    if do_all:
        choose_all(folders, inclusive_train=0, folder_prefix=folder_prefix, 
                   samples=samples, sets_per_sample=sets_per_sample,
                   max_instances=max_instances)

    if do_all_inclusive:
        choose_all(folders, inclusive_train=do_all_inclusive, folder_prefix=folder_prefix, 
                   samples=samples, sets_per_sample=sets_per_sample, 
                   max_instances=max_instances)

    for exp_type, exp_folders in EXPERIMENTS.items():
        if exp_folders == []:
            continue

        run_acc_lines = [f + "run_acc.pbs\n" for f in exp_folders]

        # f_name is the name of the bash script to execute all acc of that type
        f_name = "run_{}.pbs".format(exp_type)
        with open(f_name, "w") as b:
            b.write("#!/bin/bash\n\n")
            b.writelines(run_acc_lines)

        make_executable(f_name)


if __name__ == "__main__":
    # TODO -: implement a way to pass the folders. Right now they are a list in python.
    #      -: For now the names of the instances have to be UNIQUE! If not then
    #         there will be conflics when creating the test and train folders.

    parser = argparse.ArgumentParser()

    parser.add_argument("-p", "--path-to-acc", help="path to the acclingo folder", default=None)

    parser.add_argument("-s", "--single", help="For each domain(folder), create a set of samples",
                    action="store_true")

    parser.add_argument("-m", "--multiple", help="For each domain(folder), create a set of samples using all other domains as training set and using the missing domain and test set",
                    action="store_true")

    parser.add_argument("-a", "--all", help="Aggregate all domains and create samples",
                    action="store_true")

    parser.add_argument("-i", "--all-inclusive", help="Aggregate all domains and create samples while guaranteeing that each sample has at least N instance from each domain",
                        type=int, default=0)

    parser.add_argument("--sets-per-sample", help="Amount of sets to create per sample(amount of configurations to learn from each sample)",
                        type=int, default=3)

    parser.add_argument("--max-instances", help="Maximum amount of instances a sample can have. If this number is higher than the amount of instances available then the training set is n-1 instances and the testing set is the reamining instance",
                        type=int, default=19)

    parser.add_argument("--folder", help="Name of the folder where the experiments will be created",
                        default="Experiments")

    parser.add_argument("--samples", help="Aggregate all domains and create samples",
                        type=int, default=3)

    parser.add_argument("--acc-template", help="Path to the acclingo job file template.",
                        default=ACC_TEMPLATE)

    parser.add_argument("--run-template", help="Path to the run job file template.",
                        default=RUN_TEMPLATE)

    parser.add_argument("--instance-folders", help="Path to the instance folders. Each fodler is separated by a space. Each folder will be treated as a domain", 
                        nargs="+", default=[])
    args = parser.parse_args()

    if args.path_to_acc is None:
        print("Please provide the path to the acclingo folder using the option -p or --path-to-acc")
        sys.exit(-1)

    with open(args.acc_template, "r") as f:
        ACC_TEXT = f.read()

    ACC_TEXT = ACC_TEXT.format(ptoa=os.path.abspath(args.path_to_acc))

    with open(args.run_template, "r") as f:
        RUN_TEXT = f.read()

    if args.instance_folders == []:
        print("Please provide at least one instance folder.")
        sys.exit(-1)


    prepare_experiments(args.instance_folders, do_single=args.single, do_multiple=args.multiple, do_all=args.all, do_all_inclusive=args.all_inclusive,
                            samples=args.samples, sets_per_sample=args.sets_per_sample,
                            max_instances=args.max_instances, folder_prefix=args.folder)
