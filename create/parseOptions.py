from argparse import ArgumentParser 
import json

INCUMBENT = "incumbent"

NAME = "name"
FLAG = "F"
SKIP = "S"
SPECIAL = -1



def parse_options(options, thread_separator=" "):
    arguments = {}
    options = json.loads(options)[INCUMBENT]
    options = [opt.replace("\'", "") for opt in options]
    
    for opt in options:
        options, val = opt.split("=")
     
        # take first argument out(useless), store name and then take name out
        thread = options.split(":")[0].replace("@","")
        options = options.split(":")[1:]
        name = options[-1]
        options = options[:-1]

        if thread not in arguments:
            arguments[thread] = {}
        
        if len(options) > 0 and options[0] == SKIP:
            continue

        if name not in arguments[thread]:
            arguments[thread][name] = {}

        if len(options) > 0:
            # first argument is either a flag a skip a number or a "No"
            if options[0] == FLAG:
                # flags with value no will be skipped, yes leads to no arguments
                if val == "no":
                    arguments[thread][name][SPECIAL] = SKIP

            elif options[0].lower() == u"no":
                arguments[thread][name][1] = val
                arguments[thread][name][SPECIAL] = "no"
            else:
                # assign the value to the position given by the option
                arguments[thread][name][int(options[0])] = val            

        else:
            # if there are no options
            arguments[thread][name][1] = val
    
    arg_str = ""
    
    for thread in arguments.keys():
        thread_args = arguments[thread]
        for name, args in thread_args.items():
            pre_arg_str=argstostring(name, args)
            #deal with special cases
            if "no-vsids-progress" in pre_arg_str:
                pre_arg_str = pre_arg_str.replace("--no-vsids-progress", "--vsids-progress=no")
            if "dom-heur" in pre_arg_str:
                pre_arg_str = pre_arg_str.replace(",", " ")

            arg_str += pre_arg_str + " "

        # add separator between thread arguments    
        arg_str += thread_separator

    return arg_str


def parse_options_thread(options):
    arguments = {}
    options = json.loads(options)[INCUMBENT]
    options = [opt.replace("\'", "") for opt in options]
    
    for opt in options:
        options, val = opt.split("=")
     
        # store first argument(thread) and then take it out, store name and then take name out
        thread = options.split(":")[0].replace("@","")
        options = options.split(":")[1:]
        name = options[-1]
        options = options[:-1]

        if thread not in arguments:
            arguments[thread] = {}
        
        if len(options) > 0 and options[0] == SKIP:
            continue

        if name not in arguments[thread]:
            arguments[thread][name] = {}

        if len(options) > 0:
            # first argument is either a flag a skip a number or a "No"
            if options[0] == FLAG:
                # flags with value no will be skipped, yes leads to no arguments
                if val == "no":
                    arguments[thread][name][SPECIAL] = SKIP

            elif options[0].lower() == u"no":
                arguments[thread][name][1] = val
                arguments[thread][name][SPECIAL] = "no"
            else:
                # assign the value to the position given by the option
                arguments[thread][name][int(options[0])] = val            

        else:
            # if there are no options
            arguments[thread][name][1] = val
    
    arg_str = ""
    
    for thread in arguments.keys():
        thread_args = arguments[thread]
        for name, args in thread_args.items():
            pre_arg_str=argstostring(name, args)
            #deal with special cases
            if "no-vsids-progress" in pre_arg_str:
                pre_arg_str = pre_arg_str.replace("--no-vsids-progress", "--vsids-progress=no")
            if "dom-heur" in pre_arg_str:
                pre_arg_str = pre_arg_str.replace(",", " ")

            arg_str += pre_arg_str + " "

        # add separator between thread arguments    
        arg_str += " // "

    return arg_str


def argstostring(name, args):

    # deal with special solver argument
    if name == "solver":
        return ""
    
    # dealing with special options in the options
    if SPECIAL in args:
        if args[SPECIAL] == SKIP:
            return ""
        if args[SPECIAL] == "no":
            if args[1] == u"no":
                return "--no-" + name
            else:
                return "--" + name + "=" + ",".join([args[pos] for pos in sorted(args) if pos > 0])

    elif len(args) > 0:
        return "--" + name + "=" + ",".join([args[pos] for pos in sorted(args) if pos != SPECIAL])
    
    else:
        return "--" + name


            
if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("file", help="Path to file created by acclingo")

    args = parser.parse_args()
    
    with open(args.file, "r") as f:
        for line in f:
            pass
    #line is now the last learned (best one)
    print(parse_options(line))
