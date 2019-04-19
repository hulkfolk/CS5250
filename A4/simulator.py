'''
CS5250 Assignment 4, Scheduling policies simulator
Sample skeleton program
Input file:
    input.txt
Output files:
    FCFS.txt
    RR.txt
    SRTF.txt
    SJF.txt
'''
import copy
import sys
from collections import deque

input_file = 'input.txt'


class Process:
    last_scheduled_time = 0

    def __init__(self, id, arrive_time, burst_time, priority=10000):
        self.id = id
        self.arrive_time = arrive_time
        self.burst_time = burst_time
        self.priority = priority  # enrich Process class to keep track of priority

    # for printing purpose
    def __repr__(self):
        return ('[id %d : arrival_time %d,  burst_time %d]'%(self.id, self.arrive_time, self.burst_time))


def FCFS_scheduling(process_list):
    # store the (switching time, proccess_id) pair
    schedule = []
    current_time = 0
    waiting_time = 0
    for process in process_list:
        if(current_time < process.arrive_time):
            current_time = process.arrive_time
        schedule.append((current_time,process.id))
        waiting_time = waiting_time + (current_time - process.arrive_time)
        current_time = current_time + process.burst_time
    average_waiting_time = waiting_time/float(len(process_list))
    return schedule, average_waiting_time


# Input: process_list, time_quantum (Positive Integer)
# Output_1 : Schedule list contains pairs of (time_stamp, proccess_id) indicating the time switching to that proccess_id
# Output_2 : Average Waiting Time
def RR_scheduling(process_list, time_quantum ):
    schedule = []
    num_of_process = len(process_list)
    processes = copy.deepcopy(process_list)
    ready_queue = deque()  # using double ended queue to simulate ready queue under RR scheduling algo
    process_expired_quantum = None  # add process expired its quantum to the very end even to break the tie
    current_time = 0
    waiting_time = 0
    while(1):
        completed = True

        tmp = []
        for process in processes:
            # check arrival time of process, append to ready_queue if it's less than current time
            if process.arrive_time <= current_time:
                ready_queue.append(process)
                tmp.append(process)
        if process_expired_quantum:
            ready_queue.append(process_expired_quantum)

        # remove arrived process from process list, prevent from re-adding
        for arrived_process in tmp:
            processes.remove(arrived_process)

        # there are processes to be execute but yet arrived
        if processes and not ready_queue:
            completed = False
            current_time += 1

        # waiting for process to arrive or complete executing all processes
        running_process = ready_queue.popleft() if ready_queue else None
        if running_process and running_process.burst_time > 0:
            schedule.append((current_time, running_process.id))
            completed = False
            if running_process.burst_time > time_quantum:
                current_time += time_quantum
                running_process.burst_time -= time_quantum
                process_expired_quantum = running_process  # append non-completed process at the end of the queue
            else:
                current_time += running_process.burst_time
                process_expired_quantum = None  # remove completed process from ready queue
                # use original process burst time which is not modified to calculate waiting time
                original_process = next(iter([process for process in process_list if process.id == running_process.id and process.arrive_time == running_process.arrive_time]))
                waiting_time += (current_time - running_process.arrive_time - original_process.burst_time)

        if completed:
            break
    return (schedule, waiting_time/float(num_of_process))


def SRTF_scheduling(process_list):
    ready_queue = deque()
    processes = copy.deepcopy(process_list)
    running_process = None
    schedule = []
    num_of_process = len(process_list)
    current_time = 0
    waiting_time = 0
    while(1):
        # in this task we don't need to handle processes arrive at the same time
        process = [process for process in processes if process.arrive_time == current_time]
        process = next(iter(process)) if process else None

        # waiting for new process to arrive
        if not process and not running_process:
            current_time += 1
        else:
            # initialize the running process as the 1st arrived process
            if not running_process:
                running_process = process
                # used  as flag to write to output file
                # write to output iff a new process start running, either newly arrived or shorter remaining time
                change_of_running_process = True

            # assumption:
            # current running process has the shortest burst time
            # preempt current running process only if the arrived process has smaller burst time than the remaining time of current process
            # if there is no new process comes in, complete current process in the ready queue
            if process and running_process.burst_time <= process.burst_time:
                if running_process.id != process.id:  # special handling for the first process
                    ready_queue.append(process)
                    change_of_running_process = False
            if process and running_process.burst_time > process.burst_time:
                preempted_process = running_process  # preempt running process, append to the end of the queue
                ready_queue.append(preempted_process)
                running_process = process
                change_of_running_process = True

            # write to output only if running process changed to another process
            if change_of_running_process:
                schedule.append((current_time, running_process.id))
            current_time += 1
            running_process.burst_time -= 1

        if running_process and running_process.burst_time == 0:
            # use original process burst time which is not modified to calculate waiting time
            original_process = next(iter([process for process in process_list if process.id == running_process.id and process.arrive_time == running_process.arrive_time]))
            waiting_time += (current_time - running_process.arrive_time - original_process.burst_time)
            processes.remove(running_process)  # remove process from list once completed
            # select the process with the shortest burst time to run
            if not ready_queue:
                running_process = None
            else:
                # sort in ascending burst time
                ready_queue = deque(sorted(ready_queue, key=lambda p: p.burst_time, reverse=False))
                running_process = ready_queue.popleft()
                change_of_running_process = True
        else:
            change_of_running_process = False

        completed = True if not running_process and not processes else False
        if completed:
            break

    return (schedule, waiting_time/float(num_of_process))


def SJF_scheduling(process_list, alpha):
    processes = copy.deepcopy(process_list)
    num_of_processes = len(processes)
    ready_queue = deque()
    schedule = []
    current_time = 0
    waiting_time = 0
    future_predict = {}
    while(1):
        tmp = []
        for process in processes:
            # add process with calculated priority to ready queue if arrived
            if process.arrive_time <= current_time:
                if process.id not in future_predict:
                    process.priority = 5  # use initial guess for new process
                    future_predict[process.id] = {"last_prediction": 5}
                else:
                    priority = alpha * future_predict[process.id]["last_actual_burst"] + (1 - alpha) * future_predict[process.id]["last_prediction"]
                    process.priority = priority
                    future_predict[process.id]["last_prediction"] = priority
                tmp.append(process)
                # append new process to ready queue and sort
                # ensure the left most process in the queue has the highest priority
                ready_queue.append(process)
                ready_queue = deque(sorted(ready_queue, key=lambda x: x.priority))

        for process in tmp:
            processes.remove(process)

        running_process = ready_queue.popleft() if ready_queue else None
        if running_process:
            # current running process has the shortest burst time based on prediction
            # other processes have to wait until it's completed
            # behave like FCFS here
            schedule.append((current_time, running_process.id))
            current_time += running_process.burst_time
            waiting_time += (current_time - running_process.arrive_time - running_process.burst_time)
            future_predict[running_process.id]["last_actual_burst"] = running_process.burst_time  # update param for next prediciton

        # waiting for new process to arrive
        if processes and not running_process:
            current_time += 1

        completed = True if not processes and not ready_queue else False
        if completed:
            break

    return (schedule, waiting_time/float(num_of_processes))


def read_input():
    result = []
    with open(input_file) as f:
        for line in f:
            array = line.split()
            if (len(array)!= 3):
                print ("wrong input format")
                exit()
            result.append(Process(int(array[0]),int(array[1]),int(array[2])))
    return result


def write_output(file_name, schedule, avg_waiting_time):
    with open(file_name,'w') as f:
        for item in schedule:
            f.write(str(item) + '\n')
        f.write('average waiting time %.2f \n'%(avg_waiting_time))


def main(argv):
    process_list = read_input()
    print ("printing input ----")
    for process in process_list:
        print (process)

    print ("simulating FCFS ----")
    FCFS_schedule, FCFS_avg_waiting_time =  FCFS_scheduling(process_list)
    write_output('FCFS.txt', FCFS_schedule, FCFS_avg_waiting_time )

    print ("simulating RR ----")
    RR_schedule, RR_avg_waiting_time =  RR_scheduling(process_list,time_quantum = 2)
    write_output('RR.txt', RR_schedule, RR_avg_waiting_time )

    print ("simulating SRTF ----")
    SRTF_schedule, SRTF_avg_waiting_time =  SRTF_scheduling(process_list)
    write_output('SRTF.txt', SRTF_schedule, SRTF_avg_waiting_time )

    print ("simulating SJF ----")
    SJF_schedule, SJF_avg_waiting_time =  SJF_scheduling(process_list, alpha = 0.2)
    write_output('SJF.txt', SJF_schedule, SJF_avg_waiting_time )


if __name__ == '__main__':
    main(sys.argv[1:])

