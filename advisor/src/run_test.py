import numpy as np

size_of_arrays = 3
fn = '../csv_advisor_reports/Picsar_PIC_example.csv'
ai_ref_values = [0.3307, 0.155, 0.0405]
gflops_ref_values = [ 5.04195 ,  2.2794  ,  0.538505]
times_ref_values = [ 0.3624,  0.1479,  0.016 ]


# 1. Test that the module file is found

print("Testing module file")

try:
    import advisor
except ImportError:
    print("Could not load module file advisor.py. Aborting.")
    exit

print("Passed")
    
# 2. Test reading data

print("Testing input reading")
# Read the file
try:
    adv = advisor.advisor_results(fn)
except IOError:
    print("Could not read the input file at "+fn+". Aborting.")
    exit

print("Passed")

print("Testing output")

def op1(val_from_loop,val_filter):
	return ((val_from_loop) == val_filter)

def op2(val_from_loop,val_filter):
	return (int(val_from_loop) in val_filter) 

# 2) Get arrays of arithmetic intensity, flops and time from the file current_deposition.F90
ai = adv.get_array('ai',include_children=True,filterVal=['current_deposition.F90',[2681,2730,9552]],filterKey=['file','line'],filterOp=[op1,op2])
gflops = adv.get_array('gflops',include_children=True,filterVal=['current_deposition.F90',[2681,2730,9552]],filterKey=['file','line'],filterOp=[op1,op2])
times = adv.get_array('selftime',include_children=True,filterVal=['current_deposition.F90',[2681,2730,9552]],filterKey=['file','line'],filterOp=[op1,op2])

if ( all(ai == ai_ref_values) and
     all(gflops == gflops_ref_values) and
     all(times == times_ref_values) ):
    print("Passed")
else:
    print("Tests failed")
    if(not all(ai == ai_ref_values)):
        print("AI values do not match with reference values")
    if(not all(gflops == gflops_ref_values)):
        print("GFLOPS values do not match with reference values")
    if(not all(times == times_ref_values)):
        print("time values do not match with reference values")
