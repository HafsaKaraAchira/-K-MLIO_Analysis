
import os
import time
import math

from pyJoules.device.rapl_device import RaplCoreDomain , RaplDramDomain
from pyJoules.handler.csv_handler import CSVHandler
from pyJoules.energy_meter import EnergyContext

csv_handler = CSVHandler('./logs/log_energy.csv')

file = "generator/CM13,4M_2400MO_SEP0,2/points.csv"
N = 13421800
k = 10
dim = 10

#@measure_energy(handler=csv_handler, domains=[RaplCoreDomain(0),RaplDramDomain(0)])
def program_call(M):
    os.system("./prog_energy_buf "+file+" "+str(k)+" "+str(N)+" "+str(int(N/M))+" "+str(dim))

def prog_memory_est(N,dim,k,MC) :
    double_size = 8
    int_size = 4
    M = int(N/MC)
    chunk_size = M * dim * double_size
    dist_mat_size = M * k * double_size
    kmeans_assign_size = 2 * M *int_size
    chunk_assign_size = M * int_size
    # dataset_assign_size = N * int_size
    
    size = chunk_size+dist_mat_size+kmeans_assign_size+chunk_assign_size
    size = math.ceil(( (size) / (1024**2)) + 1.5 ) +1
    
    return size


affinity_mask = {1}
pid = 0
os.sched_setaffinity(0, affinity_mask)

governor = "userspace"
memory_constraint = [4] #[1,2,4,5,8,10]
unit = 100000



os.system("echo "+governor+" | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor")
        
for MC in reversed(memory_constraint) :
    # $1 is the governor name
    S=prog_memory_est(N,dim,k,MC)
    os.system("echo $(( "+str(int(S))+" * 1024 * 1024)) > /sys/fs/cgroup/memory/kmeans/memory.limit_in_bytes")
    print(str(MC)+"  "+str(int(1024/MC))+"    "+str(S))
    for freq in [13* unit] : #range(28 * unit, 7 * unit, -unit) :
        os.system("./scripts/prog_script_cache")
        os.system("cpupower -c all frequency-set -f "+str(freq))
        os.system("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_setspeed")
        time.sleep(5)
        with EnergyContext(handler=csv_handler, domains=[RaplCoreDomain(0),RaplDramDomain(0)], start_tag=str(N)+","+str(int(N/MC))+","+str(MC)+","+str(freq)) as ctx:
            # call the target program
            program_call(MC)
            
    csv_handler.save_data()



#################################################################