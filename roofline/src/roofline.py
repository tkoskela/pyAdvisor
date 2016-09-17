import pdb
import matplotlib
import matplotlib.pylab as pl
import matplotlib.pyplot as plt
import numpy as np
import matplotlib

class roofline_results():
    def __init__(self,time,sdefn='sde.out',vtfn='vtune.out',machine='cori',ncore=32,nsocket=2):
        '''This class represents the data produced by D. Doerfler's scripts for measuring
        Arithmetic intensity. Can be used to produce roofline model plots.

        Instructions:
        - Pipe the output from Doug's scripts parse_sde.bash and parse_vtune.bash into ascii files 
          (default file names are sde.out and vtune.out)
        - Start an interactive python session with the command 'ipython' (you probably aready did this)
        - import roofline (this module)
        - rf = roofline_results(time = <runtime_of_your_kernel>, sdefn='sde.out',vtfn='vtune.out') 
          [time argument must be given, filenames can be omitted if default values are used]
        - rf.plot()
        '''

        self.dataset = list()
        if type(time) == list:
            time_list = time
        else:
            time_list = [time]
        if type(sdefn) == list:
            sdefn_list = sdefn
        else:
            sdefn_list = [sdefn]
        if type(vtfn) == list:
            vtfn_list = vtfn
        else:
            vtfn_list = [vtfn]
        if type(ncore) == list:
            ncore_list = ncore
        else:
            ncore_list = [ncore]
        if type(nsocket) == list:
            nsocket_list = nsocket
        else:
            nsocket_list = [nsocket]
            
        for i in np.arange(len(sdefn_list)):
            self.dataset.append(roofline_dataset(sde_diag(sdefn_list[i]),vtune_diag(vtfn_list[i]),time_list[i]))
        
        if machine == 'cori':
            self.peak_Gflops = 36.8 * ncore
            #Cori memory bandwidth reference
            #http://ark.intel.com/products/81060/Intel-Xeon-Processor-E5-2698-v3-40M-Cache-2_30-GHz
            self.peak_bwdth = 68.0 * nsocket
        elif machine == 'edison': 
            self.peak_Gflops = 19.2 * ncore
            #Edison memory bandwith reference
            #https://software.intel.com/en-us/forums/software-tuning-performance-optimization-platform-monitoring/topic/515830     
            self.peak_bwdth = 25.6 * nsocket
        elif machine == 'carl/mcdram':
            self.peak_Gflops = 2252.0 / 64 * ncore
            self.peak_bwdth  = 460.0 * nsocket
        elif machine == 'carl/ddr':
            self.peak_Gflops = 2252.0 / 64 * ncore
            self.peak_bwdth  = 90.0 * nsocket
        else:
            self.peak_Gflops = 0.0
            self.peak_bwdth = 0.0
            
    def plot(self,fignum=1,labels='',fn='none', fontsize=22, markersize=20,
             newfig=True, marker= 'o'):

        #matplotlib.rcParams['backend'] = "Qt4Agg"
        
        num = 200
        
        plt.rcParams.update({'font.size': fontsize})
        
        fig = plt.figure(fignum)

        if newfig:
            fig.clf()
        
        ax = fig.gca()

        #pdb.set_trace()

        num_plots = len(self.dataset)

        #colormap = plt.cm.gist_ncar
        #ax.set_color_cycle([colormap(i) for i in np.linspace(0, 0.9, num_plots)])

        color=iter(plt.cm.rainbow(np.linspace(0,1,num_plots)))
        
        x = np.logspace(-1,1.5,num=num,base=10)

        if newfig:
            
            y = np.minimum(np.ones(num) * self.peak_Gflops / 8, x * self.peak_bwdth)
            l1 = ax.loglog(x,y,basex=10,basey=10,c = 'k',ls = ':' ,lw=2,label='roofline')
            
            y = np.minimum(np.ones(num) * self.peak_Gflops / 4, x * self.peak_bwdth)
            l2 = ax.loglog(x,y,basex=10,basey=10,c = 'k',ls = '-.' ,lw=2,label='roofline (FMA)')
        
            y = np.minimum(np.ones(num) * self.peak_Gflops / 2, x * self.peak_bwdth)
            l3 = ax.loglog(x,y,basex=10,basey=10,c = 'k',ls = '--' ,lw=2,label='roofline (Vect)')
            
            y = np.minimum(np.ones(num) * self.peak_Gflops, x * self.peak_bwdth)
            l4 = ax.loglog(x,y,basex=10,basey=10,c = 'k',ls = '-' ,lw=2,label='roofline (Vect + FMA)')

        for i,d in enumerate(self.dataset):
            c=next(color)
            if not labels == '':
                p1 = ax.plot(d.ai_dram, d.sde.Gflops / d.time, marker, ms=markersize, label=labels[i], c=c)
                #pdb.set_trace()
                #p2 = ax.plot(d.ai_l1,   d.sde.Gflops / d.time, 's', ms=markersize, label=labels[i])
            else:
                p1 = ax.plot(d.ai_dram, d.sde.Gflops / d.time, marker, ms=markersize, c=c)
                #p2 = ax.plot(d.ai_l1,   d.sde.Gflops / d.time, 's', ms=markersize)
        
        ax.set_xlabel('Arithmetic Intensity')
        ax.set_ylabel('Gflops/s')
        ax.axis('tight')
        ax.grid(True)
                
        if labels != '':
            plt.legend(loc=2)

        if fn != 'none':
            plt.savefig(fn)

        plt.draw()
        plt.show(block = False)
        
        plt.savefig('foo.png')
            
        return ax

class roofline_dataset():
    def __init__(self,sde,vtune,time):
        self.sde = sde
        self.vtune = vtune
        self.time = time

        self.ai_dram = self.sde.Gflops / self.vtune.Gbytes       
        self.ai_l1 = self.sde.Gflops / self.sde.Gbytes

        
class sde_diag():
    def __init__(self,fn):
        fid = open(fn)
        self.lines = fid.readlines()
        for l in self.lines:
            if l.find('Total FLOPs') > 0:
                self.Gflops = int(l.split(sep='=')[1]) * 1e-9
            if l.find('Total Bytes read') > 0:
                self.Gbytes = int(l.split(sep='=')[1]) * 1e-9

            if l.find('fp_double_1') > 0:
                self.Gflops_double_1 = int(l.split(sep='=')[1]) * 1e-9
            if l.find('fp_double_2') > 0:
                self.Gflops_double_2 = int(l.split(sep='=')[1]) * 1e-9
            if l.find('fp_double_4') > 0:
                self.Gflops_double_4 = int(l.split(sep='=')[1]) * 1e-9
            if l.find('fp_double_8') > 0:
                self.Gflops_double_8 = int(l.split(sep='=')[1]) * 1e-9

            if l.find('fp_single_1') > 0:
                self.Gflops_single_1 = int(l.split(sep='=')[1]) * 1e-9
            if l.find('fp_single_2') > 0:
                self.Gflops_single_2 = int(l.split(sep='=')[1]) * 1e-9
            if l.find('fp_single_4') > 0:
                self.Gflops_single_4 = int(l.split(sep='=')[1]) * 1e-9
            if l.find('fp_single_8') > 0:
                self.Gflops_single_8 = int(l.split(sep='=')[1]) * 1e-9
        return

class vtune_diag():
    def __init__(self,fn):
        fid = open(fn)
        self.lines = fid.readlines()
        for l in self.lines:
            if l.find('Total Bytes') > 0:
                self.Gbytes = int(l.split(sep='=')[1]) * 1e-9
        return
