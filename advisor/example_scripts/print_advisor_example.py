#
# In this example, we simply show how to read a csv advisor file report
# and how to print the loop properties in your terminal
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

# 2) Show all the results
# Uncomment to see the result
# adv1.print()

# 3) Show only the results with data and also shows the children
adv1.print(include_children=True,has_data=True)

#### Examples with filters #############################################

# 4) Only show loops from the file current_deposition.F90

def op1(val_from_loop,val_filter):
	return ((val_from_loop) == val_filter)

adv1.print(include_children=True,has_data=True,filterVal=['current_deposition.F90'],filterKey=['file'],filterOp=[op1])

# 5) Only show the corresponding the loops at the corresponding lines [2681,2730,9552] and in current_deposition.F90
                      
def op2(val_from_loop,val_filter):
	return (int(val_from_loop) in val_filter)   

adv1.print(include_children=True,has_data=True,filterVal=['current_deposition.F90',[2681,2730,9552]],filterKey=['file','line'],filterOp=[op1,op2])

# Filters can be added like this indefinitely, it's cool isn't it !?     
