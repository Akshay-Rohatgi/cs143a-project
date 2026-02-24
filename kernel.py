### Fill in the following information before submitting
# Group id: 17
# Members: Akshay Rohatgi, Caitlyn Oda, Candice Lu

from collections import deque
import heapq

PID = int

# This class represents the PCB of processes.
# It is only here for your convinience and can be modified however you see fit.
class PCB:
    pid: PID
    priority: int
    process_level: str

    def __init__(self, pid: PID, priority=0, process_level=""):
        self.pid = pid
        self.priority = priority
        self.process_level = process_level
        self.saved_ticks = 0

# This class represents the Kernel of the simulation.
# The simulator will create an instance of this object and use it to respond to syscalls and interrupts.
# DO NOT modify the name of this class or remove it.
class Kernel:
    scheduling_algorithm: str
    ready_queue: deque[PCB]
    waiting_queue: deque[PCB]
    foreground_queue: deque[PCB]
    background_queue: deque[PCB]

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
        self.time_quantum = 40
        self.level_switch = 200
        self.foreground_queue = deque()
        self.background_queue = deque()
        self.ticks = 0
        self.level_committed_ticks = 0  
        self.current_level = "Foreground"

    # This method is triggered every time a new process has arrived.
    # new_process is this process's PID.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def new_process_arrived(self, new_process: PID, priority: int, process_type: str) -> PID:
        new_pcb = PCB(new_process, priority)
        if self.scheduling_algorithm == "Priority":
            print("Priority in new process: ",priority)
            # if cpu idle, just add to queue and switch to new process
            if self.running == self.idle_pcb:
                heapq.heappush(self.priority_queue, (priority, new_process, new_pcb))
                self.choose_next_process()
            # if new process has higher priority (lower number), preempt current process
            elif priority < self.running.priority:
                heapq.heappush(self.priority_queue, (self.running.priority, self.running.pid, self.running))
                heapq.heappush(self.priority_queue, (priority, new_process, new_pcb))
                self.choose_next_process()
            else:
                heapq.heappush(self.priority_queue, (priority, new_process, new_pcb))
        
        elif self.scheduling_algorithm == "FCFS":
            # add new process to the ready to process queue
            self.ready_queue.append(new_pcb)
            # if cpu idle, switch to new process
            if self.running == self.idle_pcb:
                self.choose_next_process()

        elif self.scheduling_algorithm == "RR":
            # add new process to the ready to process queue
            self.ready_queue.append(new_pcb)
            # if cpu idle, switch to new process
            if self.running == self.idle_pcb:
                self.choose_next_process()
        
        elif self.scheduling_algorithm == "Multilevel":
            new_pcb.process_level = process_type
            if process_type == "Foreground":
                self.foreground_queue.append(new_pcb)
            elif process_type == "Background":
                self.background_queue.append(new_pcb)
            # if cpu idle, switch to new process
            if self.running == self.idle_pcb:
                self.level_committed_ticks = 0  
                self.choose_next_process()
        
        return self.running.pid

    # This method is triggered every time the current process performs an exit syscall.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_exit(self) -> PID:
        self.running = self.idle_pcb
        if self.scheduling_algorithm == "Multilevel" or self.scheduling_algorithm == "RR":
            self.ticks = 0
        self.choose_next_process()
        return self.running.pid
    

    # This is where you can select the next process to run.
    # This method is not directly called by the simulator and is purely for your convinience.
    # Feel free to modify this method as you see fit.
    # It is not required to actually use this method but it is recommended.
    def choose_next_process(self, level_switch=False):
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
        elif self.scheduling_algorithm == "Priority":
            if(len(self.priority_queue) == 0):
                self.running = self.idle_pcb
                return
            priority, process_id, next_pcb = heapq.heappop(self.priority_queue)
            self.running = next_pcb

            return
        elif self.scheduling_algorithm == "RR":
            if self.running != self.idle_pcb:
                # add the currently running process back to the ready queue
                self.ready_queue.append(self.running)

            if(len(self.ready_queue) == 0):
                self.running = self.idle_pcb
                return
            
            # schedule the next process in the ready queue
            next_pcb = self.ready_queue.popleft()
            self.running = next_pcb
            self.ticks = 0

            return
        elif self.scheduling_algorithm == "Multilevel":
            if self.running != self.idle_pcb:
                if self.running.process_level == "Foreground":
                    if level_switch:
                        effective_ticks = self.ticks + 1
                        if effective_ticks >= self.time_quantum / 10:
                            self.running.saved_ticks = 0
                            self.foreground_queue.append(self.running)
                        else:
                            self.running.saved_ticks = effective_ticks
                            self.foreground_queue.appendleft(self.running)
                    else:
                        self.running.saved_ticks = 0
                        self.foreground_queue.append(self.running)
                else:
                    self.background_queue.appendleft(self.running)
            
            while True:
                if self.current_level == "Foreground":
                    if len(self.foreground_queue) == 0:
                        if len(self.background_queue) > 0:
                            self.current_level = "Background"
                            self.level_committed_ticks = 0
                            continue 
                        else:
                            self.running = self.idle_pcb
                            return
                    
                    next_pcb = self.foreground_queue.popleft()
                    self.running = next_pcb
                    self.ticks = next_pcb.saved_ticks  
                    next_pcb.saved_ticks = 0
                    return
                
                elif self.current_level == "Background":
                    if len(self.background_queue) == 0:
                        if len(self.foreground_queue) > 0:
                            self.current_level = "Foreground"
                            self.level_committed_ticks = 0
                            continue  
                        else:
                            self.running = self.idle_pcb
                            return
                    
                    next_pcb = self.background_queue.popleft()
                    self.running = next_pcb
                    self.ticks = 0 
                    return

        else:
            print("Unknown scheduling algorithm")

    def timer_interrupt(self) -> PID:
        if self.scheduling_algorithm == "RR":
            self.ticks += 1
            if self.ticks >= self.time_quantum / 10:
                self.ticks = 0
                self.choose_next_process()
        
        elif self.scheduling_algorithm == "Multilevel":
            self.level_committed_ticks += 1
            
            if self.level_committed_ticks >= self.level_switch / 10:
                if self.current_level == "Foreground":
                    if len(self.background_queue) > 0:
                        self.current_level = "Background"
                        self.level_committed_ticks = 0
                        self.choose_next_process(level_switch=True)
                        return self.running.pid
                    else:
                        self.level_committed_ticks = 0
                else:  
                    if len(self.foreground_queue) > 0:
                        self.current_level = "Foreground"
                        self.level_committed_ticks = 0
                        self.choose_next_process(level_switch=True)
                        return self.running.pid
                    else:
                        self.level_committed_ticks = 0
            
            if self.current_level == "Foreground":
                self.ticks += 1
                if self.ticks >= self.time_quantum / 10:
                    self.ticks = 0
                    self.choose_next_process()
        
        return self.running.pid

    def syscall_set_priority(self, new_priority: int) -> PID:
        old_priority = self.running.priority
        self.running.priority = new_priority
        
        heapq.heappush(self.priority_queue, (new_priority, self.running.pid, self.running))
        
        self.choose_next_process()
        
        return self.running.pid