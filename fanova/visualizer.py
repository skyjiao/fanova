from ConfigSpace.hyperparameters import CategoricalHyperparameter
import os
import numpy as np
import warnings
import pickle
import re

import matplotlib.pyplot as plt
import itertools as it
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D

class Visualizer(object):

    def __init__(self, fanova, cs, directory):
        """        
        Parameters
        ------------
        fanova: fANOVA object
        
        cs : ConfigSpace instantiation
        
        directory: str
            Path to the directory in which all plots will be stored
        """
        self.fanova = fanova
        self.cs = cs
        self.cs_params = cs.get_hyperparameters()
        assert os.path.exists(directory), "directory %s doesn't exist" % directory
        self.directory = directory

    def create_all_plots(self, **kwargs):
        """
        Creates plots for all main effects and stores them into a directory
        
        """

        for i in range(len(self.cs_params)):
            param = i
            param_name = self.cs_params[param].name
            plt.close()
            outfile_name = os.path.join(self.directory, param_name.replace(os.sep, "_") + ".png")
            print("creating %s" % outfile_name)
            
            self.plot_marginal(param, show=False, **kwargs)
            plt.savefig(outfile_name)
        # additional pairwise plots:
        dimensions = []
        for i in range(len(self.cs_params)):
                dimensions.append(i)
        combis = list(it.combinations(dimensions,2))
        for combi in combis:
            param_names = []
            for p in combi:
                param_names.append(self.cs_params[p].name)
            plt.close()
            param_names = str(param_names)
            param_names = re.sub('[!,@#\'\n$\[\]]', '', param_names)
            outfile_name = os.path.join(self.directory, str(param_names).replace(" ","_") + ".png")
            print("creating %s" % outfile_name)
            self.plot_pairwise_marginal(combi, **kwargs)
            plt.savefig(outfile_name)

    def generate_pairwise_marginal(self, param_indices, resolution=20):
        """
        Creates a plot of pairwise marginal of a selected parameters
        
        Parameters
        ------------
        param_list: list of ints or strings
            Contains the selected parameters  
        
        resolution: int
            Number of samples to generate from the parameter range as
            values to predict

        """
        assert len(param_indices) == 2, "You have to specify 2 (different) parameters"
        grid_list = []
        param_names = []
        if isinstance(self.cs_params[param_indices[0]], (CategoricalHyperparameter)) or isinstance(self.cs_params[param_indices[1]], (CategoricalHyperparameter)):
            choice_arr = []
            param_names = []
            choice_vals = []
            for p in param_indices:
                if isinstance(self.cs_params[p], (CategoricalHyperparameter)):
                    choice_arr.append(self.cs_params[p].choices)
                    choice_vals.append(np.arange(len(self.cs_params[p].choices)))
                else:
                    lower_bound = self.cs_params[p].lower
                    upper_bound = self.cs_params[p].upper
                    grid = np.linspace(lower_bound, upper_bound, resolution)
                    if self.fanova.config_on_hypercube:
                        grid = self.cs_params[p]._transform(grid)
                    choice_arr.append(grid)
                    choice_vals.append(grid)
                    
                param_names.append(self.cs_params[p].name)
                
            choice_arr = [[choice_arr[1], choice_arr[0]] if len(choice_arr[1]) > len(choice_arr[0]) else [choice_arr[0], choice_arr[1]]]
            choice_vals = [[choice_vals[1], choice_vals[0]] if len(choice_vals[1]) < len(choice_vals[0]) else [choice_vals[0],choice_vals[1]]]
            choice_arr = np.asarray(choice_arr).squeeze()
            choice_vals = np.asarray(choice_vals).squeeze()
            param_indices = [[param_indices[1], param_indices[0]] if len(choice_vals[1]) < len(choice_vals[0]) else [param_indices[0], param_indices[1]]]
            choice_arr = np.asarray(choice_arr).squeeze()
            choice_vals = np.asarray(choice_vals).squeeze()
            param_indices = np.asarray(param_indices).squeeze()
            zz = np.zeros((len(choice_vals[0]), len(choice_vals[1])))
            
            for i, x_value in enumerate(choice_vals[0]):
                for j, y_value in enumerate(choice_vals[1]):
                    zz[i][j] = self.fanova.marginal_mean_variance_for_values(param_indices, [x_value, y_value])[0]
            
            return choice_arr, zz
            
        else:
                
            for p in param_indices:
                lower_bound = self.cs_params[p].lower
                upper_bound = self.cs_params[p].upper
                param_names.append(self.cs_params[p].name)
                grid = np.linspace(lower_bound, upper_bound, resolution)
                if self.fanova.config_on_hypercube:
                    grid = self.cs_params[p]._transform(grid)
                grid_list.append(grid)
    
            zz = np.zeros([resolution * resolution])
            for i, y_value in enumerate(grid_list[1]):
                for j, x_value in enumerate(grid_list[0]):
                    zz[i * resolution + j] = self.fanova.marginal_mean_variance_for_values(param_indices, [x_value, y_value])[0]
    
            zz = np.reshape(zz, [resolution, resolution])
    
            return grid_list, zz

    def plot_pairwise_marginal(self, param_list, resolution=20, show=False):
        """
        Creates a plot of pairwise marginal of a selected parameters
        
        Parameters
        ------------
        param_list: list of ints or strings
            Contains the selected parameters
        
        resolution: int
            Number of samples to generate from the parameter range as
            values to predict

        """
        assert len(param_list) == 2, "You have to specify 2 (different) parameters"
        param_names = []
        param_indices= []
        
        for p in param_list:
            if type(p) == str:
                p = self.cs.get_idx_by_hyperparameter_name(p)
            param_names.append(self.cs_params[p].name)
            param_indices.append(p)

        if isinstance(self.cs_params[param_indices[0]], (CategoricalHyperparameter)) or isinstance(self.cs_params[param_indices[1]], (CategoricalHyperparameter)):
            choices, zz = self.generate_pairwise_marginal(param_indices, resolution)
            if isinstance(self.cs_params[param_indices[0]], (CategoricalHyperparameter)) and isinstance(self.cs_params[param_indices[1]], (CategoricalHyperparameter)):
                fig = plt.figure()
                plt.imshow(zz, cmap='hot', interpolation='nearest')
                plt.xticks(np.arange(0,len(choices[0])), choices[0], fontsize=8)
                plt.yticks(np.arange(0,len(choices[1])), choices[1], fontsize=8)
                plt.xlabel(param_names[0])
                plt.ylabel(param_names[1])
                plt.colorbar().set_label("Performance")
                if show:
                    plt.show()
            else:
                cats =  choices[0] if isinstance(choices[0], str) else choices[1]
                x_label = param_names[0] if isinstance(self.cs_params[param_list[1]],(CategoricalHyperparameter)) else param_names[1]

                fig = plt.figure()
                for i, cat in enumerate(cats):
                    plt.plot(zz[i], label='%s' %cat)
                plt.ylabel('Performance')
                plt.xlabel(x_label)
                plt.legend()
                plt.tight_layout()
                    
        else:
            grid_list, zz = self.generate_pairwise_marginal(param_indices, resolution)
    
            display_xx, display_yy = np.meshgrid(grid_list[0], grid_list[1])
    
            fig = plt.figure()
            ax = Axes3D(fig)
    
            surface = ax.plot_surface(display_xx, display_yy, zz, rstride=1, cstride=1, cmap=cm.jet, linewidth=0, antialiased=False)
            ax.set_xlabel(param_names[0])
            ax.set_ylabel(param_names[1])
            ax.set_zlabel("Performance")
            fig.colorbar(surface, shrink=0.5, aspect=5)
            if show:
                plt.show()
            else:
                interact_dir = self.directory + '/interactive_plots'
                print('creating %s/interactive_plots' %self.directory)
                if not os.path.exists(interact_dir):
                    os.makedirs(interact_dir)
                pickle.dump(fig, open(interact_dir + '/%s_%s.fig.pickle' %(param_names[0],param_names[1]), 'wb'))
            return plt

    def generate_marginal(self, param, resolution=100):
        """
        Creates marginals of a selected parameter for own plots
        
        Parameters
        ------------
        param: int or str
            Index of chosen parameter in the ConfigSpace (starts with 0)
        
        resolution: int
            Number of samples to generate from the parameter range as
            values to predict
        
        """
        if type(param) == str:
            param = self.cs.get_idx_by_hyperparameter_name(param)
        
        if isinstance(self.cs_params[param], (CategoricalHyperparameter)):
            param_name = self.cs_params[param].name
            labels= self.cs_params[param].choices
            categorical_size  = len(self.cs_params[param].choices)
            marginals = [self.fanova.marginal_mean_variance_for_values([param], [i]) for i in range(categorical_size)]
            mean, v = list(zip(*marginals))
            std = np.sqrt(v)
            return mean, std
            
        else:        
            lower_bound = self.cs_params[param].lower
            upper_bound = self.cs_params[param].upper
            log = self.cs_params[param].log
            if log:
                # JvR: my conjecture is that ConfigSpace uses the natural logarithm
                base = np.e
                log_lower = np.log(lower_bound) / np.log(base)
                log_upper = np.log(upper_bound) / np.log(base)
                grid = np.logspace(log_lower, log_upper, resolution, endpoint=True, base=base)
                '''
                if abs(grid[0] - lower_bound) > 0.00001:
                    raise ValueError()
                if abs(grid[-1] - upper_bound) > 0.00001:
                    raise ValueError()
                '''
            else:
                grid = np.linspace(lower_bound, upper_bound, resolution)
            mean = np.zeros(resolution)
            std = np.zeros(resolution)
    
            dim = [param]
            for i in range(0, resolution):
                (m, v) = self.fanova.marginal_mean_variance_for_values(dim, [grid[i]])
                mean[i] = m
                std[i] = np.sqrt(v)
            if self.fanova.config_on_hypercube:
                grid = self.cs_params[param]._transform(grid)
            return mean, std, grid

    def plot_marginal(self, param, resolution=100, log_scale=None, show=True):
        """
        Creates a plot of marginal of a selected parameter
        
        Parameters
        ------------
        param: int or str
            Index of chosen parameter in the ConfigSpace (starts with 0)
        
        resolution: int
            Number of samples to generate from the parameter range as
            values to predict
        
        log_scale: boolean
            If log scale is required or not. If no value is given, it is
            deduced from the ConfigSpace provided
        """
        if type(param) == str:
            param = self.cs.get_idx_by_hyperparameter_name(param)
        param_name = self.cs_params[param].name
        
        # check if categorical
        if isinstance(self.cs_params[param], (CategoricalHyperparameter)):
            labels= self.cs_params[param].choices
            categorical_size  = len(self.cs_params[param].choices)
            mean, std = self.generate_marginal(param)
            indices = np.arange(1,categorical_size+1, 1)
            b = plt.boxplot([[x] for x in mean])
            plt.xticks(indices, labels)
            min_y = mean[0]
            max_y = mean[0]
            # blow up boxes 
            for box, std_ in zip(b["boxes"], std):
                y = box.get_ydata()
                y[2:4] = y[2:4] + std_
                y[0:2] = y[0:2] - std_
                y[4] = y[4] - std_
                box.set_ydata(y)
                min_y = min(min_y, y[0] - std_)
                max_y = max(max_y, y[2] + std_)
            
            plt.ylim([min_y, max_y])
            
            plt.ylabel("Performance")
            plt.xlabel(param_name)
            plt.tight_layout()
            
        else:

            if log_scale is None:
                log_scale = self.cs_params[param].log
    
            mean, std, grid = self.generate_marginal(param, resolution)
            mean = np.asarray(mean)
            std = np.asarray(std)
            
            lower_curve = mean - std
            upper_curve = mean + std
    
            if log_scale or (np.diff(grid).std() > 0.000001):
                plt.semilogx(grid, mean, 'b')
            else:
                plt.plot(grid, mean, 'b')
            plt.fill_between(grid, upper_curve, lower_curve, facecolor='red', alpha=0.6)
            plt.xlabel(param_name)
            
            plt.ylabel("Performance")
            plt.tight_layout()
            
        if show:
            plt.show()
        else:
            return plt
        
            
        
    def create_most_important_pairwise_marginal_plots(self, params=None, n=20):
        """
        Creates plots of the n most important pairwise marginals of the whole ConfigSpace
        
        Parameters
        ------------
        params = list
             Contains the selected parameters for pairwise evaluation
        n: int
             The number of most relevant pairwise marginals that will be returned
            
        """
        if self.fanova._dict:
            most_important_pairwise_marginals = self.fanova.tot_imp_dict
        else:
            if params:
                most_important_pairwise_marginals = self.fanova.get_most_important_pairwise_marginals(params=params)
            else:    
                most_important_pairwise_marginals = self.fanova.get_most_important_pairwise_marginals(n=n)

        for param1, param2 in most_important_pairwise_marginals:
            param1, param2 = self.cs.get_idx_by_hyperparameter_name(param1), self.cs.get_idx_by_hyperparameter_name(param2)
            param_names = [self.cs_params[param1].name, self.cs_params[param2].name]
            param_names = str(param_names)
            param_names = re.sub('[!,@#\'\n$\[\]]', '', param_names)
            outfile_name = os.path.join(self.directory, str(param_names).replace(" ","_") + ".png")
            print("creating %s" % outfile_name)
            self.plot_pairwise_marginal((param1, param2), show=False)
            plt.savefig(outfile_name)

