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

# Show the results
adv1.print(include_children=True,has_data=True)
                      
                
