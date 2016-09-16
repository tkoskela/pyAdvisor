import csv
import numpy as np
import pylab as pl
import matplotlib.pyplot as plt

# import mpld3

class loop():

    def __init__(self,line,keys):

        self.children = list()

        for i,key in enumerate(keys):
            formatted_key = ''.join(key.split()).lower()
            setattr(self,formatted_key,line[i])

    def has_data(self):

        if len(self.ai) > 0 and len(self.gflops) > 0:
            return True
        else:
            return False

    def child_has_data(self):

        for child in self.children:
            if len(child.ai) > 0 and len(child.gflops) > 0:
                return True
                
        return False
        
class advisor_results():

    def __init__(self,fn):

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

    def plot(self,fignum=1,markersize=200,mrk='o',newfig=True,label=None,tooltips=True):

        # Tooltip code adapted from http://matplotlib.sourceforge.net/examples/event_handling/pick_event_demo.html
        
        fig = plt.figure(fignum)
        if newfig:
            plt.clf()
        ax = plt.gca()
        
        x = list()
        y = list()
        s = list()
        c = list()
        labels = list()

        # ai = list()
        # gflops = list()
        # time = list()
        # gain = list()

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
                        # ai.append(float(child.ai))
                        # gflops.append(float(child.gflops))
                        # time.append(float(child.selftime[:-1]))
                        # if len(loop.gainestimate) > 0:
                        #     gain.append(float(loop.gainestimate[:-1]))
                        
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

        # tooltip = mpld3.plugins.PointLabelTooltip(scatter, labels=self.labels)
        # mpld3.plugins.connect(fig, tooltip)
        
        # mpld3.display()
        
        plt.show(block=False)

        return scatter

    def get_sum(self,key):

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
