#
# In this example, we simply show how to extract arrays 
# from the csv advisor file report using filters and to plot them
#
# ____________________________________________________________________

import pylab as pl
import advisor

# Path to the csv advisor file report
fn1 = '../csv_advisor_reports/Picsar_PIC_example.csv'

# Read the file
adv1 = advisor.advisor_results(fn1)

# 1) Print the list of keys

adv1.print_keys()

# 2) Creation of the filters

def op1(val_from_loop,val_filter):
	return ((val_from_loop) == val_filter)

def op2(val_from_loop,val_filter):
	return (int(val_from_loop) in val_filter) 

# 2) Get arrays of arithmetic intensity, flops and time from the file current_deposition.F90
ai = adv1.get_array('ai',include_children=True,filterVal=['current_deposition.F90',[2681,2730,9552]],filterKey=['file','line'],filterOp=[op1,op2])
gflops = adv1.get_array('gflops',include_children=True,filterVal=['current_deposition.F90',[2681,2730,9552]],filterKey=['file','line'],filterOp=[op1,op2])
times = adv1.get_array('selftime',include_children=True,filterVal=['current_deposition.F90',[2681,2730,9552]],filterKey=['file','line'],filterOp=[op1,op2])

# 3) Plot of the data

fig = pl.figure(1)
ax = pl.subplot()

scatter = ax.scatter(ai,
                     gflops,
                     times*400,
                     marker='o',
                     color='r',
                     alpha=0.5,
                     label='current_deposition.F90')

ax.legend(loc='best')

ax.set_xlabel('Arithmetic intensity (flops/byte)')
ax.set_ylabel('Performance (gflops/s)')

pl.show()
