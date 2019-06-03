#
# Class responsible for injecting settings into configuration files
#
# Author: Jakub Wlodek
#

import os
import DataModel.install_config as IC

class ConfigInjector:
    """
    Class that is responsible for injecting configuration information and replaces macros.

    Attributes
    ----------
    injector_file_links : Dict of str to str
        locations of target files for specific injections
    path_to_configure : str
        path to installSynApps configuration directory
    install_config : InstallConfiguration
        the currently loaded install configuration

    Methods
    -------
    get_injector_files()
        gets list of current injector files in configuration directory
    get_macro_replace_files()
        gets list of files with lists of macro replacements
    get_injector_file_link(injector_file_path : str)
        gets the target file path for a given injector file
    inject_into_file(injector_file_path : str)
        injects a given injector file into its target
    get_macro_replace_from_file(macro_list : List, macro_file_path : str)
        appends list of macro-value pairs to main list from file
    update_macros(macro_val_list : List, target : str)
        updates the macros in a target directory files given a list of macro-value pairs
    """

    def __init__(self, path_to_configure, install_config):
        """Constructor for ConfigInjector"""

        self.injector_file_links = {
            "AD_RELEASE_CONFIG"     : "$(AREA_DETECTOR)/configure/RELEASE_PRODS.local",
            "AUTOSAVE_CONFIG"       : "$(AREA_DETECTOR)/ADCore/iocBoot/commonPlugin_settings.req",
            "MAKEFILE_CONFIG"       : "$(AREA_DETECTOR)/ADCore/ADApp/commonDriverMakefile",
            "PLUGIN_CONFIG"         : "$(AREA_DETECTOR)/ADCore/iocBoot/commonPlugins.cmd",
        }
        self.path_to_configure = path_to_configure
        self.install_config = install_config


    def get_injector_files(self):
        """
        Function that gets list of injector files by searching configure/injectionFiles

        Returns
        -------
        injector_files : List
            List of injector file paths
        """

        injector_files = []
        if os.path.exists(self.path_to_configure) and os.path.isdir(self.path_to_configure):
            for file in os.listdir(self.path_to_configure + "/injectionFiles"):
                if os.path.isfile(self.path_to_configure + "/injectionFiles/" + file):
                    if self.injector_file_links[file] != None:
                        injector_files.append(self.path_to_configure + "/injectionFiles/" + file)
        
        return injector_files


    def get_macro_replace_files(self):
        """
        Function that retrieves the list of macro replace files from configure/macroFiles

        Returns
        -------
        macro_replace_files : List
            List of macro file paths
        """

        macro_replace_files = []
        if os.path.exists(self.path_to_configure) and os.path.isdir(self.path_to_configure):
            for file in os.listdir(self.path_to_configure + "/macroFiles"):
                if os.path.isfile(self.path_to_configure + "/macroFiles/" + file):
                    macro_replace_files.append(self.path_to_configure + "/" + file)

        return macro_replace_files


    def get_injector_file_link(self, injector_file_path):
        """
        Function that given an injector file path returns a target file

        Parameters
        ----------
        injector_file_path : str
            path to a given injector file
        
        Returns
        -------
        self.injector_file_links[filename] : str
            the relative path to the target file as stored in the class's dictionary
        """

        filename = injector_file_path.split('/')[-1]
        return self.injector_file_links[filename]


    def inject_to_file(self, injector_file_path):
        """
        Function that injects contents of specified file into target

        First, convert to absolute path given the install config. Then open it in append mode, then
        write all uncommented lines in the injector file into the target, and then close both

        Parameters
        ----------
        injector_file_path : str
            path to a given injector file
        """

        target_path = self.get_injector_file_link(injector_file_path)
        target_path = self.install_config.convert_path_abs(target_path)
        target_fp = open(target_path, "a")
        target_fp.write("# ------------The following was auto-generated by installSynApps-------\n")
        injector_fp = open(injector_file_path, "r")

        line = injector_fp.readline()
        while line:
            if not line.startswith('#') and len(line) > 1:
                target_fp.write(line)
            line = injector_fp.readline()
        target_fp.write("# --------------------------Auto-generated end----------------------\n")
        target_fp.close()
        injector_fp.close()


    def get_macro_replace_from_file(self, macro_list, macro_file_path):
        """
        Function that adds to a list of macro-value pairs as read from a configurtion file

        Parameters
        ----------
        macro_list : List
            list containting macro-value pairs to append
        macro_file_path : str
            path to config file with new macro settings
        """

        if os.path.exists(macro_file_path) and os.path.isfile(macro_file_path):
            macro_fp = open(macro_file_path, "r")
            line = macro_fp.readline()
            while line:
                if not line.startswith('#') and '=' in line:
                    macro_list.append(line.strip().split('='))

                line = macro_fp.readline()
            macro_fp.close()


    def update_macros(self, macro_replace_list, target_dir):
        """
        Function that updates the macros for all files in a target location, given a list of macro-value pairs

        Parameters
        ----------
        macro_replace_list : List
            list containting macro-value pairs
        target_dir : str
            path of target dir for which all macros will be edited.
        """

        if os.path.exists(target_dir) and os.path.isdir(target_dir):
            if not os.path.exists(target_dir + "/OLD_FILES"):
                os.mkdir(target_dir + "/OLD_FILES")
            for file in os.listdir(target_dir):
                if os.path.isfile(target_dir + "/" + file):
                    os.rename(target_dir + "/" + file, target_dir + "/OLD_FILES/" + file)
                    old_fp = open(target_dir + "/OLD_FILES/" + file, "r")

                    if file.endswith(self.install_config.epics_arch) or file.endswith(".local") or "." not in file:
                        if file.startswith("EXAMPLE_"):
                            new_fp = open(target_dir + "/" + file[8:], "w")
                        else:
                            new_fp = open(target_dir + "/" + file, "w")

                        line = old_fp.readline()
                        while line:
                            line = line.strip()
                            wrote_line = False
                            for macro in macro_replace_list:
                                if (macro[0] + "=") in line and len(macro) < 3:
                                    new_fp.write("{}={}\n".format(macro[0], macro[1]))
                                    macro.append("DONE")
                                    wrote_line = True
                            
                            if not wrote_line and not line.startswith('#'):
                                new_fp.write("#" + line + "\n")
                            elif not wrote_line:
                                new_fp.write(line + "\n")

                            line = old_fp.readline()

                        for macro in macro_replace_list:
                            if len(macro) < 3:
                                new_fp.write("{}={}\n".format(macro[0], macro[1]))

                        new_fp.close()

                    old_fp.close()


