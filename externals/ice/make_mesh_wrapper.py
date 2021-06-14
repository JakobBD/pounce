# WRAPPER 

import sys
import subprocess

n_avg = 5
n_avg_max = 200
while True: 
    args = ["python3","make_mesh.py",sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],str(n_avg)]
    output=subprocess.run(args,stdout=subprocess.PIPE)
    stdout_str=output.stdout.decode("utf-8")
    all_ok_str = """   <  0.0  <  0.1  <  0.2  <  0.3  <  0.4  <  0.5  <  0.6  <  0.7  <  0.8  <  0.9  <  1.0 
     0 |     0 |"""
    i_found = stdout_str.find(all_ok_str)
    if i_found > -1: 
        print("All ok. Finish up")
        if n_avg > 5: 
            print("NAvg final: " + str(n_avg))
        break 
    else: 
        n_avg *=2
        if n_avg > n_avg_max: 
            print("ERROR - n_avg_max exceeded!")
            sys.exit()
        print("Negative or very small Jacobians found. Repeat with increased smoothing: NAvg = " + str(n_avg)) 

