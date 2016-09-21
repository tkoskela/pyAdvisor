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
        if len(self.ai) > 0 and len(self.gflops) > 0:
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
        self.keys = [x.lower() for x in lines[keyLineId]]
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
            s[s==''] = 0
            s = np.array([float(x) for x in s])
        elif sizeKey is None:
            s = markersize
        else:
            s = sizeKey
            
        print(type(s))
            
        if type(colorKey) is str and len(colorKey) > 1:
            c = self.get_array(key=colorKey,
                               filterVal=filterVal,filterKey=filterKey,filterOp=filterOp)
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


