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

class roofs():

    def __init__(self,fn,single=False):

        #Read in Roofs    
        fh=open('roofs.dat')
        lines = fh.readlines()
        for line in lines:
            bw = None
            if(single):
                if 'single-threaded' in line and (('compute' in line) or ('memory' in line)):
                    bw = int(line.split()[-2])
                    i = max(line.find('Peak'),line.find('idth')) + 4
            else:
                if not 'single-threaded' in line and (('compute' in line) or ('memory' in line)):
                    bw = int(line.split()[-2])

            if not bw is None:
                i = max(line.find('Peak'),line.find('idth')) + 4
                key = line[:i]
                formatted_key = ''.join(key.split()).lower()
                setattr(self,formatted_key,bw * 1e-9)
        fh.close()

    def plot(self,ax=None):

        if ax is None:
            ax = pl.gca()
        
        xlim = np.array(ax.get_xlim())
        ylim = np.array(ax.get_ylim())

        x = np.logspace(np.log10(xlim[0]),np.log10(xlim[1]),1000)
        
        for bw in [self.drambandwidth,self.l2bandwidth,self.l1bandwidth]:
            for flops in [self.scalaraddpeak, self.dpvectoraddpeak,self.dpvectorfmapeak]:
                y = np.minimum(np.ones(len(x)) * flops , x * bw)
                ax.plot(x,y,color='k',ls='-',lw='2')


class loop():
    """
    This is a class for storing Advisor Data that is calculated per loop. Each loop has a list of
    children that can contain more loop objects. The calling program has to take care of populating
    the children list.
    """

    def __init__(self,line,keys):

        bad_chars = ['%',',','/','(',')','[',']']
        
        self.children = list()

        # Creation of the attributes from line and keys
        for key,val in zip(keys,line):
            formatted_key = ''.join(key.split()).lower()
            for char in bad_chars:
                formatted_key = formatted_key.replace(char,'')
            setattr(self,formatted_key,val)

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

        Input:
        -------------
        fn: advisor report file to be read
        -------------
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

    def get_keys(self):
        """
        This method returns the list of keys
        """
        return self.keys

    def print_keys(self):
        """
        This method prints the available keys (properties of the loops)
        """
        print()
        print(' {} keys available per loop:'.format(len(self.keys)))
        for k,key in enumerate(self.keys):
            print(' {0:2} - {1}'.format(k,key))

    def plot(self,fignum=1,markersize=20,mrk='o',newfig=True,label=None,tooltips=True,
             filterVal=None,filterKey=None,filterOp=None,sizeKey=None,colorKey=None,
             vmin=None,vmax=None,gflopScaling=1.0):
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
                           filterVal=filterVal,filterKey=filterKey,filterOp=filterOp) * gflopScaling
        if type(sizeKey) is str:
            s = self.get_array(key=sizeKey,
                               filterVal=filterVal,filterKey=filterKey,filterOp=filterOp)
            #convert empty cells to 0's and then convert the array dtype to float
            if s.dtype.type is np.str_:
                s[s==''] = 0
                s = np.array([float(foo) for foo in s])
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
                c = np.array([float(foo) for foo in c])
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
        ax.set_xlim(1.0e-2,1.0e1)
        ax.set_ylim(1.0e-1,1.0e3)
        
        ax.set_xlabel('AI')
        ax.set_ylabel('GFLOP/S')
        
        ax.grid(True,which='both')
        
        #plt.hlines(y=5.4235e1,xmin=0,xmax=1)
        
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

    def loop_filter(self,loop,filterVal=None,filterKey=None,filterOp=None):
        """
        This function returns if the loop passes or not the filter

        Input:
        --------
        loop: loop object
        filterVal: list of values for the filter
        filterKey: list of keys for the loops to consider for the filtering process
        filterOp: filter operation defined as a function comparing attributes from filterKey with values in filterVal
        --------

        """

        if filterOp == None: return [True]

        if not type(filterVal) is list:
            filterVal = [filterVal]
        if not type(filterKey) is list:
            filterKey = [filterKey]
        if not type(filterOp) is list:
            filterOp  = [filterOp ]

        filter_pass = [False for i in range(np.size(filterOp))]

        # Go through all the filters
        for i,op in enumerate(filterOp):
            try:
                filter_pass[i] = op(getattr(loop,filterKey[i]),filterVal[i])
            except TypeError:
                filter_pass[i] = False

        return filter_pass


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

    def print_loop_properties(self,include_children=True,has_data=True,filterVal=None,filterKey=None,filterOp=None):
        """
        Print all the loops/functions and their properties in the terminal.

        For filter examples, see print_advisor_example.py

        Input:
        ---------
        include_children: if True, includes the children loops
        has_data: if True, only includes
        filterVal: list of values for the filter
        filterKey: list of keys for the loops to consider for the filtering process
        filterOp: filter operation defined as a function comparing attributes from filterKey with values in filterVal
        ---------
        """

        # Count loops
        nloops = 0
        nloops_with_filters = 0

        # Go through all the loops
        for loop in self.loops:
            
            # Look at loops that have data first
            if(has_data and loop.has_data() or not has_data or (include_children and loop.child_has_data())):
                
                nloops += 1
                filter_pass = self.loop_filter(loop,filterVal=filterVal,filterKey=filterKey,filterOp=filterOp)
                if ((has_data)and(all(filter_pass))): nloops_with_filters += 1

            # If loop didn't have data, go through its children (that have data)
            if(include_children):
                if loop.child_has_data() or not has_data:

                    for child in loop.children:
                        nloops += 1
                        if (has_data):
                            filter_pass = self.loop_filter(loop,filterVal=filterVal,filterKey=filterKey,filterOp=filterOp)
                            if (child.has_data()and(all(filter_pass))): nloops_with_filters += 1
                        else:
                            nloops_with_filters += 1

        # Print information
        print(' ')
        print(' Total number of loops: {0}'.format(nloops))
        print(' Total number of loops with filters: {0}'.format(nloops_with_filters))

        print(' ')
        print(' Filters:')
        if (include_children):
            print(' - children are included')
        else:
            print(' - children not included')
        if (has_data):
            print(' - loops with data')
        else:
            print(' - All loops')

        print(' ')
        print(' List of objects:')
        print('')
        print(' {0:3.3} type      {1:^30.30} {2:^30.30} {3:^10.10} {4:^10.10} {5:^10.10} {6:^10.10}'.format('id','subroutine','file','line','AI','gflops','time'))
        print(' ------------------------------------------------------------------------------------------------------------------')

        default = -999
        
        # Go through all the loops
        for loop in self.loops:

            if 'Function' in loop.type:
                formatstr_parent = '     Function: {0:67.30} {3:>10.10} {4:>10.10} {5:>10.10}'
                loopName = loop.functioncallsitesandloops
            else:
                formatstr_parent = ' {6:3.3} Loop:     {0:30.30} {1:>30.30} {2:>10} {3:>10.10} {4:>10.10} {5:>10.10}'
                loopName = loop.subroutine
                
            formatstr_child  = ' {6:3.3}  | Child: {0:30.30} {1:>30.30} {2:>10} {3:>10.10} {4:>10.10} {5:>10.10}'
            
            # Look at loops that have data first
            if((has_data)and(loop.has_data()) or not has_data or (include_children and loop.child_has_data())):

                filter_pass = self.loop_filter(loop,filterVal=filterVal,filterKey=filterKey,filterOp=filterOp)

                # Check if all filters pass
                if all(filter_pass):
                    if (getattr(loop,'selftimes',default) == default):
                        print(formatstr_parent.format(loopName,loop.file,loop.line,loop.ai,loop.gflops,loop.selftime,loop.id))
                    else:
                        print(formatstr_parent.format(loopName,loop.file,loop.line,loop.ai,loop.gflops,loop.selftimes,loop.id))

                if ((include_children)and(loop.has_children)):

                    # Go through all the children
                    for child in loop.children:

                        if(((has_data)and(child.has_data())) or not(has_data)):

                            filter_pass = self.loop_filter(child,filterVal=filterVal,filterKey=filterKey,filterOp=filterOp)
                            if all(filter_pass):
                                print(formatstr_child.format(child.subroutine,child.file,child.line,child.ai,child.gflops,child.selftime,child.id))                                    


            # If loop didn't have data, go through its children (that have data)
            if(include_children):
                if loop.child_has_data() or not has_data:

                    # Go through all the children
                    for child in loop.children:
                        if (((has_data)and(child.has_data())) or not(has_data)):

                            filter_pass = self.loop_filter(child,filterVal=filterVal,filterKey=filterKey,filterOp=filterOp)
                            if all(filter_pass):
                                print(formatstr_child.format(child.subroutine,child.file,child.line,child.ai,child.gflops,child.selftime,child.id))                       


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
        vals.append(convert_to_int(line))

        return vals,keys

    def sort(self,attr='file'):
        """
        Sort the list of loops according to the specified attribute.

        Inputs:
        -------
        attr : string - attribute to be used for sorting

        """
        self.loops= sorted(self.loops, key=lambda loop: getattr(loop,attr))

# ___________________________________________________________________
#
# Roofline
# ___________________________________________________________________

    def roofline(self,fig,ax,x,roofs=None,dram_bandwidth=None,mcdram_bandwidth=None,scalar_gflops=None,dp_vect_gflops=None):
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

        if not roofs is None:
            for bw in [roofs['DRAM Bandwidth'],roofs['L2 Bandwidth'],roofs['L1 Bandwidth']]:
                for flops in [roofs['Scalar Add Peak'], roofs['DP Vector Add Peak'], roofs['DP Vector FMA Peak']]:
                    y = np.minimum(np.ones(len(x)) * flops , x * bw)
                    ax.plot(x,y,color='k',ls='-',lw='2')
        else:        
            for bw in [dram_bandwidth,mcdram_bandwidth]:
                if bw != None:
                    if scalar_gflops != None:
                        y = np.minimum(np.ones(len(x)) * scalar_gflops , x * bw)
                        ax.plot(x,y,color='k',ls='-',lw='2')
                    if dp_vect_gflops != None:
                        y = np.minimum(np.ones(len(x)) * dp_vect_gflops , x * bw)
                        ax.plot(x,y,color='k',ls='-',lw='2')


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

def convert_to_int(elem):
    """
    Try to convert an element in int, if elem='', then return 0
    """
    felem = None
    try:
        felem = int(elem)
    except ValueError:
        if (elem==''): felem = 0
        pass
    return felem      

def string_contains(s1,s2):

    return s2 in s1



