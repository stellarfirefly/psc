import random
import datetime
import multiprocessing
import math
import time
import argparse

free_cores = 1      # number of cores to keep free, by default
max_value = 2**63 - 1
report_block = 2_000_000

def make_grid():
    grid = [[0] * 3 for _ in range(3)]
    for y in range(3):
        for x in range(3):
            grid[y][x] = random.randint(0, max_value)
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

def isqrt_if_gt0(n):
    return r if (r := math.isqrt(n)) * r == n else 0

def fill_grid(grid):
    row1sum = grid[0][0]**2 + grid[0][1]**2 + grid[0][2]**2
    
    cell5 = row1sum - grid[1][0]**2 - grid[1][1]**2
    if cell5 <= 0 or (sr := isqrt_if_gt0(cell5)) == 0:
        return False
    grid[1][2] = sr

    cell6 = row1sum - grid[0][0]**2 - grid[1][0]**2
    if cell6 <= 0 or (sr := isqrt_if_gt0(cell6)) == 0:
        return False
    grid[2][0] = sr

    cell7 = row1sum - grid[0][1]**2 - grid[1][1]**2
    if cell7 <= 0 or (sr := isqrt_if_gt0(cell7)) == 0:
        return False
    grid[2][1] = sr

    cell8 = row1sum - grid[2][0]**2 - grid[2][1]**2
    if cell8 <= 0 or (sr := isqrt_if_gt0(cell8)) == 0:
        return False
    grid[2][2] = sr
    
    return check_grid(grid)

def format_with_suffix(num):
    """
    Converts a number to a string with an appropriate suffix:
    K (thousand), M (million), G (billion), T (trillion).
    """
    suffixes = ['', 'K', 'M', 'G', 'T']
    i = 0
    while abs(num) >= 1000 and i < len(suffixes) - 1:
        num /= 1000.0
        i += 1
    return f"{num:.1f}{suffixes[i]}"

def process_grids(global_grids_checked, global_mss_found, process_num):
    grids_checked = 0
    mss_found = 0
    
    start = time.perf_counter()

    while True:
        grid = make_grid()
        is_mss = fill_grid(grid)
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

            end = time.perf_counter()
            diff = end - start
            
            # Display total grids checked in millions
            str_checked = format_with_suffix(grids_checked)
            str_total_checked = format_with_suffix(total_checked)
            str_perf = format_with_suffix(grids_checked / diff)
            print(f"[{timestamp}] Process {process_num}: Checked {str_checked} grids, found {mss_found}, {str_perf}/s.  GLOBAL: Checked {str_total_checked}, found {total_found}")
            
            grids_checked = 0  # Reset local counter
            mss_found = 0      # Reset local counter
            start = time.perf_counter()

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
        str_total_checked = format_with_suffix(global_grids_checked.value)
        print(f"GLOBAL FINAL: Checked {str_total_checked}, found {global_mss_found.value} total.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--cores', type=int, default=None, help='Number of CPU cores to use')
    args = parser.parse_args()

    cpu_cores = multiprocessing.cpu_count()
    max_cores = args.cores if args.cores is not None else cpu_cores - free_cores
    if max_cores < 1:
        print("Insufficient CPU cores.")
    elif max_cores > cpu_cores:
        print(f"CPU has only {cpu_cores} (virtual) cores available.")
    else:
        print(f"Using {max_cores} cores.")
        main(max_cores)
