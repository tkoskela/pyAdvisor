import pylab as pl
import advisor

fn1 = '../examples/advisor.csv'
fn2 = '../examples/advisor2.csv'

adv1 = advisor.advisor_results(fn1)
adv2 = advisor.advisor_results(fn2)

fig = pl.figure(1)

sc1 = adv1.plot(fignum = 1,sizeKey='selftime',colorKey='gainestimate',mrk='s',markersize=200)
sc2 = adv2.plot(fignum = 1,sizeKey='selftime',colorKey='gainestimate',mrk='o',newfig=False,tooltips=False,markersize=200)

pl.plot(0,0,'bs',ms = 10,label='Code 1')
pl.plot(0,0,'bo',ms = 10,label='Code 2')

pl.legend(loc=2)

fig.colorbar(sc1)

for loop in adv1.loops:
    if loop.has_data():
        for loop2 in adv2.loops:
            if loop.functioncallsitesandloops in loop2.functioncallsitesandloops and loop2.has_data():
                # print(loop.functioncallsitesandloops+' ' +  loop.gflops)
                # print(loop2.functioncallsitesandloops+' ' +  loop2.gflops)

                x = [float(loop.ai),    float(loop2.ai)]
                y = [float(loop.gflops),float(loop2.gflops)]
                pl.plot(x,y,'k--')
    # Check if the loop has a child with data
    elif loop.child_has_data():
        # Loop through loops in 2nd set and look for matching label
        for loop2 in adv2.loops:
            if loop.functioncallsitesandloops in loop2.functioncallsitesandloops:
                # Look for the child with the data in the 1st set
                for i,child in enumerate(loop.children):
                    if len(loop2.children) > i and child.has_data() and loop2.children[i].has_data():
                        # Assume that the children have the same order in the 2nd set
                        #print('child '+str(i)+ ' of '+loop.functioncallsitesandloops+
                        #      ' ' +  child.gflops + ' ' + loop2.children[i].gflops)
                        x = [float(child.ai),    float(loop2.children[i].ai)]
                        y = [float(child.gflops),float(loop2.children[i].gflops)]
                        pl.plot(x,y,'k--')

pl.show()                        
                
