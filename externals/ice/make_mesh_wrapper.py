# WRAPPER 

import sys
import subprocess
import make_mesh 

n_avg = 5
n_avg_max = 200
while True: 
    
    # args = ["python3","make_mesh_inner.py",sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],str(n_avg)]
    # output=subprocess.run(args,stdout=subprocess.PIPE)
    # stdout_str=output.stdout.decode("utf-8")

    hopr_path   = sys.argv[1]
    # reference mode: save reference coordinates and build unstructured mesh 
    # normal mode: bend to ref coords and execute hopr with reference unstructured mesh
    reference_mode = (hopr_path == "NONE")
    hoprbasefile = sys.argv[2]
    name_str    = sys.argv[3]
    random_vars = sys.argv[4].split("_") # random distribution; normal(0.,1.,1) is correct, others improve stability

    stdout_str = make_mesh.make_mesh(hopr_path,reference_mode,hoprbasefile,name_str,random_vars,n_avg)

    all_ok_str = """   <  0.0  <  0.1  <  0.2  <  0.3  <  0.4  <  0.5  <  0.6  <  0.7  <  0.8  <  0.9  <  1.0 
     0 |     0 |"""
    if stdout_str.find(all_ok_str)> -1 and stdout_str.find("HOPR successfully finished") > -1 : 
        print("All ok. Finish up")
        if n_avg > 5: 
            print("NAvg final: " + str(n_avg))
        break 
    else: 
        n_avg *=2
        if n_avg > n_avg_max: 
            print("ERROR - n_avg_max exceeded!")
            print("HOPR STDOUT:")
            print()
            print(stdout_str) 
            sys.exit()
        print("HOPR Crashed or negative or very small Jacobians found. Repeat with increased smoothing: NAvg = " + str(n_avg)) 

