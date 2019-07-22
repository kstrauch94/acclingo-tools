import argparse

class Configuration:

    def __init__(self, config_str):
        self.name, self.config = config_str.split(";")

        # value of the --configuration option
        self.config_param = ""

        self.parse_config()

    def parse_config(self):

        self.params = {}

        for param in self.config.split():
            if "--stats" in param or "--quiet=2" in param:
                continue

            if "=" in param:
                split = param.split("=")
                name, val = split[0], "=".join(split[1:])
                self.params[name] = val

                if "--configuration" in name:
                    self.config_param = val

    @property
    def param_names(self):
        return set(self.params.keys())

    def get_val(self, param_name):
        if param_name in self.params:
            return self.params[param_name]
        else:
            return ""

    def compare_param(self, param, val):

        if param == "--configuration":
            return "same"

        if param in self.params:
            if val != self.params[param]:
                return "replace"
        
        return "same"

def compare_configs(base_config, other_config, params=None):
    # compare other config to base config using params
    # returns a list with the value of the parameter + the result of comparison

    if params is None:
        params = set()
        params.update(base_config[-1].param_names)
        params.update(other_config[-1].param_names)
        params = sorted(list(params))

    line_base = [base_config.name]
    line_other = [other_config.name]
    for param in params:
        val_base = base_config.get_val(param)
        val_other = other_config.get_val(param)

        line_base.append(val_base)

        overwrite = base_config.compare_param(param, val)
        line_other.append(val_other+"|"+overwrite)

    return line_base, line_other, params

def compare_configs_strings(base_config_str, other_config_str, params=None):

    return compare_configs(Configuration(base_config_str),
                            Configuration(other_config_str), 
                            params)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("-f", "--file", help="File with configurations to compare")
    parser.add_argument("-o", "--out", help="Output file name")

    args = parser.parse_args()


    default_configs = {}
    default_configs["tweety"] = Configuration("tweety;--eq=3 --trans-ext=dynamic --heuristic=Vsids,92 --restarts=L,60 --deletion=basic,50 --del-max=2000000 --del-estimate=1 --del-cfl=+,2000,100,20 --del-grow=0 --del-glue=2,0 --strengthen=recursive,all --otfs=2 --init-moms --score-other=all --update-lbd=less --save-progress=160 --init-watches=least --local-restarts --loops=shared")
    default_configs["trendy"] = Configuration("trendy;--sat-prepro=2,20,25,240 --trans-ext=dynamic --heuristic=Vsids --restarts=D,100,0.7 --deletion=basic,50 --del-init=3.0,500,19500 --del-grow=1.1,20.0,x,100,1.5 --del-cfl=+,10000,2000 --del-glue=2 --strengthen=recursive --update-lbd=less --otfs=2 --save-progress=75 --counter-restarts=3,1023 --reverse-arcs=2 --contraction=250 --loops=common")
    default_configs["frumpy"] = Configuration("frumpy;--eq=5 --heuristic=Berkmin --restarts=x,100,1.5 --deletion=basic,75 --del-init=3.0,200,40000 --del-max=400000 --contraction=250 --loops=common --save-progress=180 --del-grow=1.1 --strengthen=local --sign-def-disj=pos")
    default_configs["crafty"] = Configuration("crafty;--sat-prepro=2,10,25,240 --trans-ext=dynamic --backprop --heuristic=Vsids --save-progress=180 --restarts=x,128,1.5 --deletion=basic,75 --del-init=10.0,1000,9000 --del-grow=1.1,20.0 --del-cfl=+,10000,1000 --del-glue=2 --otfs=2 --reverse-arcs=1 --counter-restarts=3,9973 --contraction=250")
    default_configs["jumpy"]  = Configuration("jumpy;--sat-prepro=2,20,25,240 --trans-ext=dynamic --heuristic=Vsids --restarts=L,100 --deletion=basic,75,mixed --del-init=3.0,1000,20000 --del-grow=1.1,25,x,100,1.5 --del-cfl=x,10000,1.1 --del-glue=2 --update-lbd=glucose --strengthen=recursive --otfs=2 --save-progress=70")
    default_configs["handy"]  = Configuration("handy;--sat-prepro=2,10,25,240 --trans-ext=dynamic --backprop --heuristic=Vsids --restarts=D,100,0.7 --deletion=sort,50,mixed --del-max=200000 --del-init=20.0,1000,14000 --del-cfl=+,4000,600 --del-glue=2 --update-lbd=less --strengthen=recursive --otfs=2 --save-progress=20 --contraction=600 --loops=distinct --counter-restarts=7,1023 --reverse-arcs=2")
    default_configs["auto"]  = Configuration("auto; ")

    # make it a set to have unique values
    all_params = set()

    with open(args.file, "r") as f:
        configs = []
        for c in f.readlines():
            configs.append(Configuration(c))

            all_params.update(configs[-1].param_names)

    #conver to list so it is ordered
    all_params = sorted(list(all_params))

    with open(args.out, "w") as f:
        f.write("name;" + ";".join(all_params) + "\n")

        for c in configs:
            line, _ = compare_configs(default_configs[c.config_param], c)
            f.write("{};".format(c.name) + ";".join(line) + "\n")



