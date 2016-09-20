import csv
import numpy as np
import pylab as pl
import matplotlib.pyplot as plt

class loop():
    """
    This is a class for storing Advisor Data that is calculated per loop. Each loop has a list of
    children that can contain more loop objects. The calling program has to take care of populating
    the children list.
    """

    def __init__(self,line,keys):

        self.children = list()

        for i,key in enumerate(keys):
            formatted_key = ''.join(key.split()).lower()
            setattr(self,formatted_key,line[i])

    def has_data(self):
        """
        Returns True if both AI and GFLOPS strings have length greater than 0
        """
        if len(self.ai) > 0 and (self.ai[0:1] != '<') and len(self.gflops) > 0:
            return True
        else:
            return False

    def child_has_data(self):
        """
        Returns True if both AI and GFLOPS strings of any of the children have length greater than 0
        """

        for child in self.children:
            if len(child.ai) > 0 and len(child.gflops) > 0:
                return True
                
        return False
        
class advisor_results():
    """
    This class parses the data from a csv output file from Intel Advisor and stores it in a python
    object. The raw data is stored in dictionary format in the data - field with keys in the keys - field.
    The data is also kept in loop-objects that keep track of the parent-child relationships of loops, these
    are stored in the loops - field. There are methods to plot the data and to calculate sums.
    """

    def __init__(self,fn):
        """
        This constructor reads the csv data file and creates the dictionary and loop objects.
        """


        lines = list()

        self.filename = fn
        
        with open(fn,mode='r') as infile:
            reader = csv.reader(infile)
            for row in reader:
                if(len(row) > 0):
                    lines.append(row)

        self.lines = lines
        for i,l in enumerate(lines):
            if l[0].find('ID') >= 0:
                keyLineId = i
                break
        self.keys = lines[keyLineId]
        self.data = dict()

        self.loops = list()
        
        for key in self.keys:
            self.data[key] = list()

        for i,l in enumerate(lines[keyLineId+1:]):

            if not l[1].find('child') > 0:
                self.loops.append(loop(l,self.keys))
            else:
                self.loops[-1].children.append(loop(l,self.keys))
            
            for j,val in enumerate(l):
                self.data[self.keys[j]].append(val)
                
        self.labels = self.data['Function Call Sites and Loops']

    def parse_functioncallsitesandloops(self,loop_with_data):
        """
        This method parses the child property, the subroutine, the file and the line number 
        for each loop with data from the functioncallsitesandloops parameter.

        Inputs:
        -------
        loop_with_data: list - list of loops with data, loops are dictionnaries
        -------        
        """

        # functioncallsitesandloops
        fcsal = loop_with_data['fcsal']
        child = False
        subroutine = ''
        file = ''
        line = 0

        # Get the child property
        if fcsal[1:6] == 'child':
            child = True
            fcsal = fcsal[16:-1]
        else:
            fcsal = fcsal[8:-1]

        # Get the subroutine that contains the loop
        fcsal = fcsal.split(' at ')
        subroutine = fcsal[0]

        # Get the file
        fcsal = fcsal[1].split(':')
        file = fcsal[0]

        # get the line number
        line = int(fcsal[1])

        loop_with_data['child'] = child
        loop_with_data['subroutine'] = subroutine
        loop_with_data['file'] = file
        loop_with_data['line'] = line

    def compute_loops_with_data(self):
        """
        This method computes the list of loops with data. Each loop is represented by a dictionnary.
        """

        # Creation of the list of loop with data
        self.loops_with_data = []
        k = 0
        for loop in self.loops:
            if loop.has_data():
                temp = {}
                temp['id'] = k
                temp['ai'] = float(loop.ai)
                temp['gflops']=(float(loop.gflops))
                temp['time']=(float(loop.selftime[:-1]))
                if 'Vectorized' in loop.type:
                    temp['gain'] = float(loop.gainestimate[:-1])
                    temp['type'] = 'Vectorized'
                else:
                    temp['gain'] = 0.
                    temp['type'] = 'Scalar'
                temp['fcsal'] = loop.functioncallsitesandloops
                self.parse_functioncallsitesandloops(temp)
                self.loops_with_data.append(temp)
                k += 1

            elif loop.child_has_data():
                for child in loop.children:
                    if child.has_data():
                        temp = {}
                        temp['id'] = k
                        temp['ai'] = float(child.ai)
                        temp['gflops']=(float(child.gflops))
                        temp['time']=(float(child.selftime[:-1]))
                        if 'Vectorized' in child.type:
                            temp['gain'] = float(loop.gainestimate[:-1])
                            temp['type'] = 'Vectorized'
                        else:
                            temp['gain'] = 0.
                            temp['type'] = 'Scalar'
                        temp['fcsal'] = child.functioncallsitesandloops
                        self.parse_functioncallsitesandloops(temp)
                        self.loops_with_data.append(temp)
                        k += 1

    def remove_in_loops_with_data(self,file=None):
        """
        Remove loops from the list of loops with data according to the provided filter arguments.

        Inputs:
        -------
        file : string - fine name

        """
        n = 0
        for i,loop in enumerate(self.loops_with_data):
            if loop['file'] in file:
                self.loops_with_data.pop(i)   
                n+=1
        print(' In remove_in_loops_with_data: {0} loops have been deleted'.format(n)) 

    def sort_loops_with_data(self,key='file'):
        """
        Sort the list of loops according to the specified key.

        Inputs:
        -------
        key : string - key ot be used for sorting

        """
        self.loops_with_data = sorted(self.loops_with_data, key=lambda k: k[key])

    def get_properties_from_loops_with_data(self,file=None,line=None):
        """
        Convert the list of loops into several lists for each property (in a sens, go from AoS to SoA).
        Filter options can be specified in input.

        Inputs:
        -------
        file : string - file name filter
        line : integer - line number filter

        Output:
        -------
        ai         : list - list of arithmetic intensities
        gflops     : list - list of gflops
        subroutine : list - list of subroutines
        """

        # Creation of the lists
        lid = list()
        ai = list()
        gflops = list()
        subroutines = list()
        times = list()

        # Fill the lists
        for loop in self.loops_with_data:
            if ((file == None)or(loop['file'] in file)):
                if ((line == None)or(loop['line']in line)):
                    lid.append(loop['id'])
                    ai.append(loop['ai'])
                    gflops.append(loop['gflops'])
                    times.append(loop['time'])
                    subroutines.append(loop['subroutine'])
        return lid,ai,gflops,times,subroutines

    def print(self):
        """
        This method prints in the terminal the properties of the loops with data.
        """
        # Number of loops with data
        nloops = len(self.loops_with_data)

        print(' \n')
        print(' List of loops with data:')
        print(' Number of loops: {0:2} \n'.format(nloops))
        print(' {0:2}: {1:20} {2:45} {3:5} {4:10} {5:10} {6:10} {7:10} {8:10}'.format('id','file','subroutine','line','Flop/byte','Gflop/s','Time (s)','gain','type'))
        print(' -------------------------------------------------------------------------------------------------------------------------')

        for i in range(nloops):
            loop = self.loops_with_data[i]
            print(' {0:2d}: {1:20} {2:45} {3:5} {4:10} {5:10} {6:10} {7:10} {8:10}'.format(loop['id'],loop['file'][0:20],loop['subroutine'][0:45],loop['line'],loop['ai'],loop['gflops'],loop['time'],loop['gain'],loop['type']))


    def roofline(self,fig,ax,x,dram_bandwidth=None,mcdram_bandwidth=None,scalar_gflops=None,dp_vect_gflops=None):
        """
        Plot the rooflines according to the given numbers

        Input
        ------
        fig              : figure object
        ax               : figure axis
        x                : array of floats - array of abscissa (arithmetic intensities in flops/byte)
        dram_bandwidth   : float - dram bandwidth in gbytes/s
        mcdram_bandwidth : float - mcdram bandwidth in gbytes/s
        ------
        """
        # Dram roofline
        xlim = np.array(ax.get_xlim())
        ylim = np.array(ax.get_ylim())

        if dram_bandwidth != None:
            if scalar_gflops != None:
                y = np.minimum(np.ones(len(x)) * scalar_gflops , x * dram_bandwidth)
                ax.plot(x,y,color='k',ls='-',lw='2')
            if dp_vect_gflops != None:
                y = np.minimum(np.ones(len(x)) * dp_vect_gflops , x * dram_bandwidth)
                ax.plot(x,y,color='k',ls='-',lw='2')

    def plot(self,fignum=1,markersize=200,mrk='o',newfig=True,label=None,tooltips=True):
        """
        This method plots all the loops in the object in a scatter plot on log-log scale.
        Marker size represents the self time of the loop (in seconds) and marker color represents
        the estimated vectorization gain.

        Inputs:
        -------
        fignum     : integer - figure number (default 1)
        markersize : integer - scaling factor for marker size (default 200)
        mrk        : string  - marker style (default 'o')
        newfig     : boolean - clear previous plots in figure (default True)
        label      : string  - label for legend if plotting multiple data sets (default None)
        tooltips   : boolean - show loop name on the plot by clicking on a data point (default True)
        -------
        """
        # Tooltip code adapted from http://matplotlib.sourceforge.net/examples/event_handling/pick_event_demo.html
        
        fig = plt.figure(fignum)
        if newfig:
            plt.clf()
        ax = plt.gca()

        # x-values of the plot (Arithmetic Intensity)
        x = list()
        # y-values of the plot (GFLOP/sec)
        y = list()
        # size of the markers (self time)
        s = list()
        # color of the markers (vectorization gain estimate)
        c = list()        
        labels = list()

        # Dummy value for vectorization gain of scalar loops that gets inserted into the list for plotting purposes
        scalarValue = -10.0
        
        for loop in self.loops:
            if loop.has_data():
                x.append(float(loop.ai))
                y.append(float(loop.gflops))
                s.append(float(loop.selftime[:-1]))
                if 'Vectorized' in loop.type:
                    c.append(float(loop.gainestimate[:-1]))
                else:
                    c.append(scalarValue)
                labels.append(loop.functioncallsitesandloops)
            elif loop.child_has_data():
                for child in loop.children:
                    if child.has_data():
                        
                        x.append(float(child.ai))
                        y.append(float(child.gflops))
                        s.append(float(child.selftime[:-1]))
                        if 'Vectorized' in loop.type:
                            c.append(float(loop.gainestimate[:-1]))
                        else:
                            c.append(scalarValue)
                        labels.append(loop.functioncallsitesandloops)

        if tooltips:
            h = list()
            def onpick3(event):
                for handle in h:
                    handle.remove()
                h.clear()
                for ind in event.ind:
                    h.append(ax.text(x[ind],y[ind],labels[ind]))
                    plt.draw()
                    plt.show(block=False)
                    
            scatter = ax.scatter(np.array(x),
                                 np.array(y),
                                 np.array(s)*markersize,
                                 np.array(c),
                                 marker=mrk,
                                 label=label,
                                 cmap=plt.cm.jet,
                                 picker=True)
            
            fig.canvas.mpl_connect('pick_event', onpick3)
        else:
            scatter = ax.scatter(np.array(x),
                                 np.array(y),
                                 np.array(s)*markersize,
                                 np.array(c),
                                 marker=mrk,
                                 label=label,
                                 cmap=plt.cm.jet)
            
        ax.set_yscale('log')
        ax.set_xscale('log')
        ax.set_xlim(1.0e-2,1.0e0)
        ax.set_ylim(1.0e-1,1.0e2)
        
        ax.set_xlabel('AI')
        ax.set_ylabel('GFLOP/S')
        
        ax.grid(True,which='both')
        
        plt.hlines(y=5.4235e1,xmin=0,xmax=1)
        
        plt.show(block=False)

        return scatter

    def get_sum(self,key):
        """
        Calculate the sum of any field over all the loops. NOTE: there may be loops in the list
        that are not actually executed by the program and therefore the result may be an overestimation.
        For example, for FLOPS a better number is given in the Advisor GUI summary page.
        """

        tot = 0
        for elem in self.data[key]:
            try:
                felem = float(elem)
            except ValueError:
                felem = 0
                if not len(elem) == 0 and elem[-1] is 's':
                    try:
                        felem = float(elem[:-1])
                    except ValueError:
                        pass
            tot = tot + felem
        return tot
