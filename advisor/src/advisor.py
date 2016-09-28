""" 
 ___________________________________________________________________

 ADVISOR.PY

 Version ?
 
 Author:
 Tuomas Koskela (tkoskela@lbl.gov)

 Developers:
 Tuomas Koskela (tkoskela@lbl.gov)
 Mathieu Lobet (mlobet@lbl.gov)
 ___________________________________________________________________
"""

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

        # Creation of the attributes from line and keys
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

    def has_children(self):
        """
        Return True if the loop has at least one child
        """
        if (len(self.children)>0):
            return True
        else:
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
        
        # Open the file and store the lines
        with open(fn,mode='r') as infile:
            reader = csv.reader(infile)
            for row in reader:
                if(len(row) > 0):
                    lines.append(row)
        self.lines = lines

        # Search keys
        for i,l in enumerate(lines):
            if l[0].find('ID') >= 0:
                keyLineId = i
                break
        self.keys = [x.lower() for x in lines[keyLineId]]

        # Bonus keys
        self.keys.append('child')        
        self.keys.append('subroutine')
        self.keys.append('file')
        self.keys.append('line')

        # Loop information is also stored in a dictionnary
        self.data = dict()

        # List of loops
        self.loops = list()
        
        # data[key] is a list 
        for key in self.keys:
            self.data[key] = list()

        for i,l in enumerate(lines[keyLineId+1:]):

            # Add loop to the list of loops
            if not l[1].find('child') > 0:

                # Some treatments to get new attributes
                self.parse_functioncallsitesandloops(l[1],l,self.keys)
                # add loop
                self.loops.append(loop(l,self.keys))

            else:
                # Some treatments
                self.parse_functioncallsitesandloops(l[1],l,self.keys)
                # add loop
                self.loops[-1].children.append(loop(l,self.keys))
            
            # Add value to each key of the loop of the data dictionnary
            for j,val in enumerate(l):
                self.data[self.keys[j]].append(val)
                
        self.labels = self.data['function call sites and loops']


    def plot(self,fignum=1,markersize=20,mrk='o',newfig=True,label=None,tooltips=True,
             filterVal=None,filterKey=None,filterOp=None,sizeKey=None,colorKey=None,
             vmin=None,vmax=None):
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

        filterVal  : any - threshold value to filter plotted loops (default None)
        filterKey  : any - attribute name for comparison to threshold in filter (default None)
        filterOp   : function - function to use for filtering. Must take in two arguments and return True/False (default None)
        sizeKey    : string/int/float - key to retrieve marker sizes or fixed marker size understood by scatter
        colorKey   : string/int/float - key to retrieve marker colors or fixed marker color understood by scatter
        vmin       : float - minimum of the color scale
        vmax       : float - maximum of the color scale
        -------
        """
        
        # Tooltip code adapted from http://matplotlib.sourceforge.net/examples/event_handling/pick_event_demo.html
        
        fig = plt.figure(fignum)
        if newfig:
            plt.clf()
        ax = plt.gca()
        
        x = self.get_array(key='ai',
                           filterVal=filterVal,filterKey=filterKey,filterOp=filterOp)
        y = self.get_array(key='gflops',
                           filterVal=filterVal,filterKey=filterKey,filterOp=filterOp)
        if type(sizeKey) is str:
            s = self.get_array(key=sizeKey,
                               filterVal=filterVal,filterKey=filterKey,filterOp=filterOp)
            #convert empty cells to 0's and then convert the array dtype to float
            if s.dtype.type is np.str_:
                s[s==''] = 0
                s = np.array([float(x) for x in s])
        elif sizeKey is None:
            s = markersize
        else:
            s = sizeKey            
            
        if type(colorKey) is str and len(colorKey) > 1:
            c = self.get_array(key=colorKey,
                               filterVal=filterVal,filterKey=filterKey,filterOp=filterOp)
            #convert empty cells to 0's and then convert the array dtype to float
            if c.dtype.type is np.str_:
                c[c==''] = 0
                c = np.array([float(x) for x in c])
        elif colorKey is None:
            c = 'b'
        else:
            c = colorKey
            
        labels = self.get_array(key='functioncallsitesandloops',
                                filterVal=filterVal,filterKey=filterKey,filterOp=filterOp)
        
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
                    
        #scatter = ax.scatter(x,y,s*markersize,c,marker=mrk,vmin=1,vmax=8,
        #                     label=label,cmap=plt.cm.jet,picker=tooltips)            
        scatter = ax.scatter(x,y,s*markersize,c,marker=mrk,vmin=vmin,vmax=vmax,
                             label=label,cmap=plt.cm.jet,picker=tooltips)            

        if tooltips:
            fig.canvas.mpl_connect('pick_event', onpick3)
            
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
            felem = convert_to_float(elem)
            if not felem is None:
                tot = tot + felem
        return tot

    def get_array(self,key,include_children=True,filterVal=None,filterKey=None,filterOp=None):
        """
        Return an array collected from all the loops of a single value specified by key.
        Filter results by passing filterVal, filterKey and filterOp to compare the value
        in loop.filterKey to filterVal using operator filterOp. Use import operator to
        pass operators.
        """
        
        l = list()

        if not type(filterVal) is list:
            filterVal = [filterVal]
        if not type(filterKey) is list:
            filterKey = [filterKey]
        if not type(filterOp) is list:
            filterOp  = [filterOp ]

        filter_pass = [False for i in range(np.size(filterOp))]

        # Go through all the loops
        for loop in self.loops:
            # Look at loops that have data first
            if(loop.has_data()):

                # Go through all the filters
                for i,op in enumerate(filterOp):
                    try:
                        filter_pass[i] = op(getattr(loop,filterKey[i]),filterVal[i])
                    except TypeError:
                        filter_pass[i] = False

                # Check if all filters pass
                if filterOp[0] is None or all(filter_pass):
        
                    elem = getattr(loop,key)
                    felem = convert_to_float(elem)
                    if not felem is None:
                        l.append(felem)
                    else:
                        l.append(elem)

            # If loop didn't have data, go through its children (that have data)
            elif(include_children and loop.child_has_data()):
                for child in loop.children:
                    if child.has_data():

                        # Go through all the filters for the child
                        for i,op in enumerate(filterOp):
                            try:
                                filter_pass[i] = op(getattr(child,filterKey[i]),filterVal[i])
                            except TypeError:
                                filter_pass[i] = False

                        # Check if all filters pass for the child
                        if filterOp[0] is None or all(filter_pass):
                            if key is 'gainestimate':
                                elem = getattr(loop,key)
                            else:
                                elem = getattr(child,key)
                            felem = convert_to_float(elem)
                            if not felem is None:
                                l.append(felem)
                            else:
                                l.append(elem)
  
        arr = np.array(l)

        return arr

    def print(self,include_children=True,has_data=True):
        """
        Print all the loops and their properties in the terminal

        Input:
        ---------
        include_children: if True, includes the children loops
        has_data: if True, only includes 
        ---------
        """

        print(' ')
        print(' Total number of loops:')
        print(' Total number of loops with children:')

        print(' ')
        print(' Filters:')
        if (include_children): print(' - children are included')

        print(' ')
        print(' List of loops:')
        print(' {0:3.3} type      {1:^30.30} {2:^25.25} {3:^10.10} {4:^10.10} {5:^10.10}'.format('id','subroutine','file','line','AI','gflops','time'))
        print(' -----------------------------------------------------------------------------------------------------------')

        # Go through all the loops
        for loop in self.loops:

            # Look at loops that have data first
            if((has_data)and(loop.has_data())):

                print(' {6:3.3} Loop:     {0:30.30} {1:>25.25} {2:>10} {3:>10.10} {4:>10.10}'.format(loop.subroutine,
                    loop.file,loop.line,loop.ai,loop.gflops,loop.selftime,loop.id))

                if ((loop.has_children)and(include_children)):

                    # Go through all the children
                    for child in loop.children:

                        if((has_data)and(child.has_data())):

                            print(' {6:3.3}  | Child: {0:30.30} {1:>25.25} {2:>10} {3:>10.10} {4:>10:10}'.format(child.subroutine,
                                child.file,child.line,child.ai,child.gflops,child.selftime,child.id))

            # If loop didn't have data, go through its children (that have data)
            elif(include_children and loop.child_has_data()):

                for child in loop.children:
                    if (has_data)and(child.has_data()):

                            print(' {6:3.3}  | Child: {0:30.30} {1:>25.25} {2:>10} {3:>10.10} {4:>10.10}'.format(child.subroutine,
                                child.file,child.line,child.ai,child.gflops,child.selftime,child.id))                       


    def parse_functioncallsitesandloops(self,fcsal,vals,keys):
        """
        This method parses the child property, the subroutine, the file and the line number 
        from the functioncallsitesandloops parameter and add these properties as attributes to loop.
        Values and keys are added to existing list vals and keys given in arguments.

        Inputs:
        -------
        fcsal: string to be parsed
        vals: values
        keys: keys
        -------        
        """

        # functioncallsitesandloops
        child = False
        subroutine = 'None'
        file = 'None'
        line = ''

        # Get the child property
        if fcsal[1:6] == 'child':
            child = True
            fcsal = fcsal[17:-1]
        else:
            fcsal = fcsal[9:-1]

        # Get the subroutine that contains the loop
        if (' at ' in fcsal):
            fcsal = fcsal.split(' at ')
            subroutine = fcsal[0]

            # Get the file
            try:
                fcsal = fcsal[1].split(':')
            except :
                print(' Problem with loop format')
                print(fcsal,'\n')

            file = fcsal[0]

            # get the line number
            line = int(fcsal[1])

        vals.append(child)

        vals.append(subroutine)

        vals.append(file)

        vals.append(line)


        return vals,keys

# ___________________________________________________________________
#
# Roofline
# ___________________________________________________________________

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


# ___________________________________________________________________
#
# Loops_with_data
# ___________________________________________________________________

# This section concerns a subset of the loops called loops_with_data

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
        lines = list()
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
                    lines.append(loop['line'])
        return lid,ai,gflops,times,subroutines,lines

    def print_loops_with_data(self):
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

    def parse_functioncallsitesandloops_for_loops_with_data(self,loop_with_data):
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
        try:
            fcsal = fcsal[1].split(':')
        except :
            print(' Problem with loop format')
            print(loop_with_data['fcsal'],'\n')

        file = fcsal[0]

        # get the line number
        line = int(fcsal[1])

        loop_with_data['child'] = child
        loop_with_data['subroutine'] = subroutine
        loop_with_data['file'] = file
        loop_with_data['line'] = line

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

# ___________________________________________________________________
#
# Internal functions
# ___________________________________________________________________

def convert_to_float(elem):
    """
    Try to convert an element in string elem to a floating point. Check for some special cases like
    time values ending in 's'. On failure return None.
    """
    felem = None
    try:
        felem = float(elem)
    except ValueError:
        #felem = 0
        if len(elem) > 0 and elem[-1] in 'sx':
            try:                
                felem = float(elem[:-1])
            except ValueError:
                pass
    return felem
        
def string_contains(s1,s2):

    return s1 in s2 or s2 in s1


