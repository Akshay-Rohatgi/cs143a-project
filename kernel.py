### Fill in the following information before submitting
# Group id: 
# Members: 



from collections import deque
from dataclasses import dataclass

# PID is just an integer, but it is used to make it clear when a integer is expected to be a valid PID.
PID = int

BACKGROUND: str = "Background"
FOREGROUND: str = "Foreground"

# This class represents the PCB of processes.
# It is only here for your convinience and can be modified however you see fit.
class PCB:
    pid: PID
    priority: int
    num_quantum_ticks: int
    process_type: str

    def __init__(self, pid: PID, priority: int, process_type: str):
        self.pid = pid
        self.priority = priority
        self.num_quantum_ticks = 0
        self.process_type = process_type

    def __str__(self):
        return f"({self.pid}, {self.priority})"
    
    def __repr__(self):
        return f"({self.pid}, {self.priority})"
    
class Semaphore:
    value: int
    blocked_list: list[PCB]
    
    def __init__(self, value: int):
        self.value = value
        self.blocked_list = list()
    
class Mutex:
    locked: bool
    owner: None
    blocked_list: list[PCB]
    
    def __init__(self):
        self.locked = False
        self.owner = None
        self.blocked_list = list()

RR_QUANTUM_TICKS: int = 4
ACTIVE_QUEUE_NUM_TICKS: int = 20

MULTILEVEL: str = "Multilevel"
RR: str = "RR"
FCFS: str = "FCFS"
PRIORITY: str = "Priority"

# This class represents the Kernel of the simulation.
# The simulator will create an instance of this object and use it to respond to syscalls and interrupts.
# DO NOT modify the name of this class or remove it.
class Kernel:
    scheduling_algorithm: str
    ready_queue: deque[PCB]
    waiting_queue: deque[PCB]
    running: PCB
    idle_pcb: PCB
    fcfs_ready_queue: deque[PCB]
    rr_ready_queue: deque[PCB]
    active_queue: str
    active_queue_num_ticks: int
    semaphores: {}
    mutexes: {}

    # Called before the simulation begins.
    # Use this method to initilize any variables you need throughout the simulation.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def __init__(self, scheduling_algorithm: str, logger):
        self.scheduling_algorithm = scheduling_algorithm
        self.ready_queue = deque()
        self.waiting_queue = deque()
        self.idle_pcb = PCB(0, 0, "Foreground")
        self.running = self.idle_pcb
        self.logger = logger
        self.fcfs_ready_queue = deque()
        self.rr_ready_queue = deque()
        self.active_queue = FOREGROUND
        self.active_queue_num_ticks = 0
        self.semaphores = {}
        self.mutexes = {}

    # This method is triggered every time a new process has arrived.
    # new_process is this process's PID.
    # priority is the priority of new_process.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def new_process_arrived(self, new_process: PID, priority: int, process_type: str) -> PID:
        self.ready_queue.append(PCB(new_process, priority, process_type))
        if self.scheduling_algorithm == MULTILEVEL and self.running is self.idle_pcb:
            self.active_queue_num_ticks = 0
        self.choose_next_process()
        return self.running.pid  

    # This method is triggered every time the current process performs an exit syscall.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_exit(self) -> PID:
        self.running = self.idle_pcb
        self.choose_next_process()
        return self.running.pid
    
    # This method is triggered when the currently running process requests to change its priority.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_set_priority(self, new_priority: int) -> PID:
        self.running.priority = new_priority
        self.choose_next_process()
        return self.running.pid


    # This is where you can select the next process to run.
    # This method is not directly called by the simulator and is purely for your convinience.
    # It is not required to actually use this method but it is recommended.
    def choose_next_process(self):
        if self.scheduling_algorithm == FCFS:
            self.fcfs_chose_next_process(self.ready_queue)
        elif self.scheduling_algorithm == PRIORITY:
            if len(self.ready_queue) == 0:
                return
            
            if self.running is not self.idle_pcb:
                self.ready_queue.append(self.running)

            next_process = pop_min_priority(self.ready_queue)
            self.running = next_process
        elif self.scheduling_algorithm == RR:
            self.rr_chose_next_process(self.ready_queue)
        elif self.scheduling_algorithm == MULTILEVEL:
            # Move everything in standard ready queue to proper queues
            while len(self.ready_queue) > 0:
                pcb = self.ready_queue.popleft()
                if pcb.process_type == FOREGROUND:
                    self.rr_ready_queue.append(pcb)
                elif pcb.process_type == BACKGROUND:
                    self.fcfs_ready_queue.append(pcb)
                else:
                    print("Unknown process type")
            
            if self.active_queue == FOREGROUND:
                # RR queue
                self.rr_chose_next_process(self.rr_ready_queue)
            elif self.active_queue == BACKGROUND:
                # FCFS queue
                self.fcfs_chose_next_process(self.fcfs_ready_queue)
            if self.running is self.idle_pcb:
                self.switch_active_queue()
                if self.active_queue == FOREGROUND:
                    # RR queue
                    self.rr_chose_next_process(self.rr_ready_queue)
                elif self.active_queue == BACKGROUND:
                    # FCFS queue
                    self.fcfs_chose_next_process(self.fcfs_ready_queue)
        else:
            print("Unknown scheduling algorithm")

    def rr_chose_next_process(self, queue: deque[PCB]):
        if self.running is self.idle_pcb:
            if len(queue) == 0:
                return
        
            self.running = queue.popleft()
        elif exceeded_quantum(self.running):
            queue.append(self.running)
            self.running = queue.popleft()

    def fcfs_chose_next_process(self, queue: deque[PCB]):
        if len(queue) == 0:
            return
        
        if self.running is self.idle_pcb:
            self.running = queue.popleft()

    def switch_active_queue(self):
        self.active_queue_num_ticks = 0
        if self.active_queue == FOREGROUND:
            if len(self.fcfs_ready_queue) == 0:
                return
            if self.running is not self.idle_pcb:
                if exceeded_quantum(self.running):
                    self.rr_ready_queue.append(self.running)
                    self.running = self.idle_pcb
                else:
                    self.rr_ready_queue.appendleft(self.running)
                    self.running = self.idle_pcb
            self.active_queue = BACKGROUND
        elif self.active_queue == BACKGROUND:
            if len(self.rr_ready_queue) == 0:
                return
            if self.running is not self.idle_pcb:
                self.fcfs_ready_queue.appendleft(self.running)
                self.running = self.idle_pcb
            self.active_queue = FOREGROUND
        else:
            print("Unknown active queue")

    # This method represents the hardware timer intterupt.
    # It is triggered every 10 microseconds and is the only way a kernel can track passing time.
    # Do not use real time to track how much time has passed as time is simulated.
    def timer_interrupt(self) -> PID:
        self.running.num_quantum_ticks += 1
        self.active_queue_num_ticks += 1
        if self.scheduling_algorithm == RR:
            self.choose_next_process()
        elif self.scheduling_algorithm == MULTILEVEL:
            if self.active_queue_num_ticks >= ACTIVE_QUEUE_NUM_TICKS:
                self.switch_active_queue()
            self.choose_next_process()
        return self.running.pid 
    
    # This method is triggered when the currently running process requests to initialize a new semaphore.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_init_semaphore(self, semaphore_id: int, initial_value: int):
        self.semaphores[semaphore_id] = Semaphore(initial_value)
        return
    
    # This method is triggered when the currently running process calls p() on an existing semaphore.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_semaphore_p(self, semaphore_id: int) -> PID:
        semaphore = self.semaphores[semaphore_id]
        semaphore.value -= 1
        if semaphore.value < 0:
            self.running.num_quantum_ticks = 0
            semaphore.blocked_list.append(self.running)
            self.running = self.idle_pcb
            self.choose_next_process()
        return self.running.pid

    # This method is triggered when the currently running process calls v() on an existing semaphore.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_semaphore_v(self, semaphore_id: int) -> PID:
        semaphore = self.semaphores[semaphore_id]
        semaphore.value += 1
        if semaphore.value <= 0:
            if self.scheduling_algorithm == FCFS:
                next_process = pop_min_pid(semaphore.blocked_list)
                self.ready_queue.append(next_process)
            elif self.scheduling_algorithm == RR:
                next_process = pop_min_pid(semaphore.blocked_list)
                self.ready_queue.append(next_process)
                self.choose_next_process() # context switch
            elif self.scheduling_algorithm == PRIORITY:
                next_process = pop_min_priority(semaphore.blocked_list)
                self.ready_queue.append(next_process)
                self.choose_next_process() # context switch
        return self.running.pid 

    # This method is triggered when the currently running process requests to initialize a new mutex.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_init_mutex(self, mutex_id: int):
        self.mutexes[mutex_id] = Mutex()
        return

    # This method is triggered when the currently running process calls lock() on an existing mutex.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_mutex_lock(self, mutex_id: int) -> PID:
        mutex = self.mutexes[mutex_id]
        if mutex.locked == False:
            mutex.locked = True
            mutex.owner = self.running
        else:
            mutex.blocked_list.append(self.running)
            self.running = self.idle_pcb
            self.choose_next_process()
        return self.running.pid 

    # This method is triggered when the currently running process calls unlock() on an existing mutex.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_mutex_unlock(self, mutex_id: int) -> PID:
        mutex = self.mutexes[mutex_id]
        if len(mutex.blocked_list) > 0:
            if self.scheduling_algorithm == RR:
                return
            elif self.scheduling_algorithm == PRIORITY:
                return
        return self.running.pid 


def exceeded_quantum(pcb: PCB) -> bool:
    if pcb.num_quantum_ticks >= RR_QUANTUM_TICKS:
        pcb.num_quantum_ticks = 0
        return True
    else :
        return False
    
def pop_min_priority(pcbs: list[PCB]) -> PCB:
    min_index = 0
    for i in range(1, len(pcbs)):
        process = pcbs[i]
        if process.priority < pcbs[min_index].priority:
            min_index = i
        elif process.priority == pcbs[min_index].priority and process.pid < pcbs[min_index].pid:
            min_index = i
    popped = pcbs[min_index]
    del pcbs[min_index]
    return popped

def pop_min_pid(pcbs: list[PCB]):
    lowest_pid_i = 0
    for i in range(1, len(pcbs)):
        if pcbs[i].pid < pcbs[lowest_pid_i].pid:
            lowest_pid_i = i
    popped = pcbs[lowest_pid_i]
    del pcbs[lowest_pid_i]
    return popped