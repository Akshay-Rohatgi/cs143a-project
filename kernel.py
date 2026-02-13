### Fill in the following information before submitting
# Group id: 
# Members: 

from collections import deque
import heapq

# PID is just an integer, but it is used to make it clear when a integer is expected to be a valid PID.
PID = int

# This class represents the PCB of processes.
# It is only here for your convinience and can be modified however you see fit.
class PCB:
    pid: PID

    def __init__(self, pid: PID, priority=0):
        self.pid = pid
        self.priority = priority

# This class represents the Kernel of the simulation.
# The simulator will create an instance of this object and use it to respond to syscalls and interrupts.
# DO NOT modify the name of this class or remove it.
class Kernel:
    scheduling_algorithm: str
    ready_queue: deque[PCB]
    waiting_queue: deque[PCB]

    running: PCB
    idle_pcb: PCB

    # Called before the simulation begins.
    # Use this method to initilize any variables you need throughout the simulation.
    # logger is provided which allows you to include your own print statements in the
    #   output logs. These will not impact grading.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def __init__(self, scheduling_algorithm: str, logger):
        self.scheduling_algorithm = scheduling_algorithm
        self.ready_queue = deque()
        self.waiting_queue = deque()
        self.priority_queue = []
        self.idle_pcb = PCB(0)
        self.running = self.idle_pcb

    # This method is triggered every time a new process has arrived.
    # new_process is this process's PID.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def new_process_arrived(self, new_process: PID, priority: int, process_type: str) -> PID:
        new_pcb = PCB(new_process, priority)
        if self.scheduling_algorithm == "Priority":
            print("Priority in new process: ",priority)
            heapq.heappush(self.priority_queue, (priority, new_process, new_pcb))
            # if cpu idle, switch to new process
            if self.running == self.idle_pcb:
                self.choose_next_process()
            
            # smaller priority has arrived so we need to select that one
            if(priority < self.running.priority):
                # don't forget to add the old process back to the heap!
                heapq.heappush(self.priority_queue, (self.running.priority, self.running.pid, self.running))
                self.choose_next_process()
        
        if self.scheduling_algorithm == "FCFS":
            # add new process to the ready to process queue
            self.ready_queue.append(new_pcb)
            # if cpu idle, switch to new process
            if self.running == self.idle_pcb:
                self.choose_next_process()
        
        return self.running.pid

    # This method is triggered every time the current process performs an exit syscall.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_exit(self) -> PID:
        self.running = self.idle_pcb
        self.choose_next_process()
        return self.running.pid
    

    # This is where you can select the next process to run.
    # This method is not directly called by the simulator and is purely for your convinience.
    # Feel free to modify this method as you see fit.
    # It is not required to actually use this method but it is recommended.
    def choose_next_process(self):
        # print("Len ready queue: ", len(self.ready_queue))
        # print("Len heap queue: ", len(self.priority_queue))
    
        if self.scheduling_algorithm == "FCFS":
            if(len(self.ready_queue) == 0):
                self.running = self.idle_pcb
                return
            # schedule the next process in the ready queue
            next_pcb = self.ready_queue.popleft()
            self.running = next_pcb
            return
        if self.scheduling_algorithm == "Priority":
            if(len(self.priority_queue) == 0):
                self.running = self.idle_pcb
                return
            priority, process_id, next_pcb = heapq.heappop(self.priority_queue)
            print("NEXT PCB PID: ", next_pcb.pid, "NEXT PCB PRIORITY: ", next_pcb.priority)
            self.running = next_pcb

            return
        else:
            print("Unknown scheduling algorithm")
        
    def timer_interrupt(self) -> PID:
        return self.running.pid

    def syscall_set_priority(self, new_priority: int) -> PID:
        self.running.priority = new_priority
        self.choose_next_process()
        return self.running.pid
