# acclingo-tools
Tools that simplify the use of Acclingo.

#Requirements
This tool requires acclingo and python 3.
To see how to install acclingo go to: 
https://github.com/potassco/acclingo

The evaluation part requires Pandas and Numpy.
# Usage

## Creating acclingo jobs
To create acclingo jobs you have to use the script create/create_jobs.py

The script has an assortment of options that indicate how the training sets are created. Sample amount, set of configurations to learn per sample and maximum amount of instances per sample can be provided aswell.

 Templates are used to create the acclingo job and run scripts. Default templates can be found in the create/templates folder. Of course, you can create your own templates and pass them to the script. The only requirement is that the acclingo template has a "{ptoa}" somewhere in the text. "{ptoa}" is where the path to the acclingo folder will be written to.

After the jobs are created use the executables created to run the acclingo job scripts. There is a different executable for each job "type". For example, if you used the "-s" option, there will be a "run_single.pbs" executable.

Example command:

```
python create/create_jobs.py -p /path/to/my_acclingo/acclingo/ -s --samples 4 --sets-per-sample 3 --max-instance 10 --folder output-folder-name 
```

## Retrieve the learned configurations

Once you the acclingo jobs have finished learning a configuration you can extract those configurations by using either the create/get_configs.py or the create/extract_configs.py script.

get_configs.py retrieves the configurations and writes an XML file that is compatible with the python based benchmarking tool found here: https://github.com/potassco/benchmark-tool
The XML file only has some default values and should be looked at before using it.

extract_configs.py writes a file with all configurations learned and their "names" in the following format:
config_name ; configuration
This file is used later in the evaluation

# Evaluation of results

The evaluation tool works for __OPTIMIZATION__ problems. 

Once you have run some benchmarks with the learned configurations two csv files are needed to make use of the evaluation scripts provided here. One containing the optimization values found and one file that says if the configuration proved optimality for each instance.

To evaluate the results use the script eval/parse_results.py

The script requires both csv files described above aswell as the "best bound" file. The main result of the evaluation is a "virtual best" that comprises of the best N configuration where "best" is defined in different terms:

Score :: Best N configurations based on score*

Unique :: Best N configurations based on score* where each configuration has at least one unique best result

Meank rank :: Best N configurations based on the mean rank of the configurations.

Optimal count :: Best N configurations based on the amount of optimal values found.

For each virtual best there is also a file that contains the configurations belonging to each k-way configuration.

*score: score is calculated by adding the amount of optimal values found that are BETTER than the ones in the best bound file and the values that are EQUAL to the values found in the best bound file.
in short: score = better + same