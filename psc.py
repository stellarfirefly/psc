import random
import datetime
import multiprocessing
import time
import ctypes

free_cores = 2      # number of cores to not use
max_value = 2**63 - 1
report_block = 2_000_000

def make_grid():
    grid = [[0] * 3 for _ in range(3)]
    for x in range(3):
        for y in range(3):
            grid[x][y] = random.randint(0, max_value)
    return grid

def check_grid(grid):
    row1sum = grid[0][0]**2 + grid[0][1]**2 + grid[0][2]**2
    row2sum = grid[1][0]**2 + grid[1][1]**2 + grid[1][2]**2
    row3sum = grid[2][0]**2 + grid[2][1]**2 + grid[2][2]**2

    if row1sum != row2sum or row1sum != row3sum:
        return False

    col1sum = grid[0][0]**2 + grid[1][0]**2 + grid[2][0]**2
    col2sum = grid[0][1]**2 + grid[1][1]**2 + grid[2][1]**2
    col3sum = grid[0][2]**2 + grid[1][2]**2 + grid[2][2]**2

    if row1sum != col1sum or row1sum != col2sum or row1sum != col3sum:
        return False

    diag1sum = grid[0][0]**2 + grid[1][1]**2 + grid[2][2]**2
    diag2sum = grid[0][2]**2 + grid[1][1]**2 + grid[2][0]**2

    if row1sum != diag1sum or row1sum != diag2sum:
        return False

    return True

def process_grids(global_grids_checked, global_mss_found, process_num):
    grids_checked = 0
    mss_found = 0
    while True:
        grid = make_grid()
        is_mss = check_grid(grid)
        grids_checked += 1
        if is_mss:
            mss_found += 1
            print("MSS found!")
            for row in grid:
                print(row)
        if grids_checked % report_block == 0:
            now = datetime.datetime.now()
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S") + "." + f"{now.microsecond // 1000:03d}"
            
            # Update global counters using shared memory
            with global_grids_checked.get_lock():
                global_grids_checked.value += grids_checked
                total_checked = global_grids_checked.value  # Get the current total
            with global_mss_found.get_lock():
                global_mss_found.value += mss_found
                total_found = global_mss_found.value

            # Display total grids checked in millions
            total_checked_millions = total_checked / 1_000_000
            print(f"[{timestamp}] Process {process_num}: Checked {grids_checked} grids, found {mss_found} total.  GLOBAL: Checked {total_checked_millions:.1f}M, found {total_found}")
            
            grids_checked = 0  # Reset local counter
            mss_found = 0      # Reset local counter

def main(max_cores):
    # Create shared memory variables for global counts
    global_grids_checked = multiprocessing.Value('Q', 0)
    global_mss_found = multiprocessing.Value('Q', 0)

    processes = []
    for i in range(max_cores):
        p = multiprocessing.Process(target=process_grids, args=(global_grids_checked, global_mss_found, i))
        processes.append(p)
        p.start()

    # Keep the main process alive to keep the others running
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Terminating processes...")
        for p in processes:
            p.terminate()
            p.join()
        print("All processes terminated.")
        
        # Display final total grids checked before we terminate
        total_checked_millions = global_grids_checked.value / 1_000_000
        print(f"GLOBAL FINAL: Checked {total_checked_millions:.1f}M, found {global_mss_found.value} total.")

if __name__ == "__main__":
    max_cores = multiprocessing.cpu_count() - free_cores
    if max_cores > 0:
        print(f"Using {max_cores} cores.")
        main(max_cores)
    else:
        print("Cannot find multiple CPU cores.")
