import os
import time
from collections import deque
from cube_model import Cube, nCr

# Constants
N_CO_STATES = 2187  # 3^7
N_EO_STATES = 2048  # 2^11
N_UDS_STATES = 495 # C(12,4)
N_MOVES = 18
CO_PRUNE_FILE = "co_prune.dat"
EO_PRUNE_FILE = "eo_prune.dat"
UDS_PRUNE_FILE = "uds_prune.dat"

# The 18 standard moves
MOVES = [
    "U", "U2", "U'", "D", "D2", "D'",
    "L", "L2", "L'", "R", "R2", "R'",
    "F", "F2", "F'", "B", "B2", "B'"
]

def build_co_move_table():
    """
    Builds a table that maps (corner_orientation_coord, move) -> new_corner_orientation_coord.
    """
    print("Building corner orientation move table...")
    start_time = time.time()
    
    move_table = [[-1] * N_MOVES for _ in range(N_CO_STATES)]
    temp_cube = Cube()

    for coord in range(N_CO_STATES):
        temp_coord = coord
        orientation_sum = 0
        for i in range(6, -1, -1):
            orientation = temp_coord % 3
            temp_cube.co[i] = orientation
            orientation_sum += orientation
            temp_coord //= 3
        
        temp_cube.co[7] = (3 - (orientation_sum % 3)) % 3
        
        for move_idx, move_str in enumerate(MOVES):
            move_cube = Cube()
            move_cube.co = list(temp_cube.co)
            move_cube.apply_move(move_str)
            new_coord = move_cube.corner_orientation_coord()
            move_table[coord][move_idx] = new_coord
            
    end_time = time.time()
    print(f"CO Move table built in {end_time - start_time:.2f} seconds.")
    return move_table

def generate_co_prune_table():
    """
    Generates the pruning table for corner orientations using BFS.
    """
    move_table = build_co_move_table()
    
    print("\nGenerating corner orientation pruning table with BFS...")
    start_time = time.time()
    
    pruning_table = [255] * N_CO_STATES
    queue = deque([0])
    pruning_table[0] = 0
    visited_count = 1
    
    while queue:
        current_coord = queue.popleft()
        current_depth = pruning_table[current_coord]
        
        for move_idx in range(N_MOVES):
            new_coord = move_table[current_coord][move_idx]
            if pruning_table[new_coord] == 255:
                pruning_table[new_coord] = current_depth + 1
                queue.append(new_coord)
                visited_count += 1

    end_time = time.time()
    print(f"CO Pruning table generated in {end_time - start_time:.2f} seconds.")
    print(f"Total states visited: {visited_count}/{N_CO_STATES}")
    
    return pruning_table

def build_eo_move_table():
    """
    Builds a table that maps (edge_orientation_coord, move) -> new_edge_orientation_coord.
    """
    print("\nBuilding edge orientation move table...")
    start_time = time.time()
    
    move_table = [[-1] * N_MOVES for _ in range(N_EO_STATES)]
    temp_cube = Cube()

    for coord in range(N_EO_STATES):
        temp_coord = coord
        orientation_sum = 0
        for i in range(10, -1, -1):
            orientation = temp_coord % 2
            temp_cube.eo[i] = orientation
            orientation_sum += orientation
            temp_coord //= 2
        
        temp_cube.eo[11] = (2 - (orientation_sum % 2)) % 2
        
        for move_idx, move_str in enumerate(MOVES):
            move_cube = Cube()
            move_cube.eo = list(temp_cube.eo)
            move_cube.apply_move(move_str)
            new_coord = move_cube.edge_orientation_coord()
            move_table[coord][move_idx] = new_coord
            
    end_time = time.time()
    print(f"EO Move table built in {end_time - start_time:.2f} seconds.")
    return move_table

def generate_eo_prune_table():
    """
    Generates the pruning table for edge orientations using BFS.
    """
    move_table = build_eo_move_table()
    
    print("\nGenerating edge orientation pruning table with BFS...")
    start_time = time.time()
    
    pruning_table = [255] * N_EO_STATES
    queue = deque([0])
    pruning_table[0] = 0
    visited_count = 1
    
    while queue:
        current_coord = queue.popleft()
        current_depth = pruning_table[current_coord]
        
        for move_idx in range(N_MOVES):
            new_coord = move_table[current_coord][move_idx]
            if pruning_table[new_coord] == 255:
                pruning_table[new_coord] = current_depth + 1
                queue.append(new_coord)
                visited_count += 1

    end_time = time.time()
    print(f"EO Pruning table generated in {end_time - start_time:.2f} seconds.")
    print(f"Total states visited: {visited_count}/{N_EO_STATES}")
    
    return pruning_table

def build_uds_move_table():
    """
    Builds a table that maps (ud_slice_coord, move) -> new_ud_slice_coord.
    """
    print("\nBuilding UD slice move table...")
    start_time = time.time()
    
    move_table = [[-1] * N_MOVES for _ in range(N_UDS_STATES)]
    temp_cube = Cube()

    for coord in range(N_UDS_STATES):
        # Decode the coordinate to set the edge permutation
        temp_coord = coord
        k = 4
        slice_edges_placed = 0
        other_edges_placed = 0
        
        # Reset edge permutation
        temp_cube.ep = [-1] * 12
        
        for n in range(11, -1, -1):
            comb = nCr(n, k)
            if temp_coord >= comb:
                temp_cube.ep[n] = 8 + slice_edges_placed # Place a slice edge
                slice_edges_placed += 1
                temp_coord -= comb
                k -= 1
            else:
                temp_cube.ep[n] = other_edges_placed # Place a non-slice edge
                other_edges_placed += 1

        for move_idx, move_str in enumerate(MOVES):
            move_cube = Cube()
            move_cube.ep = list(temp_cube.ep)
            move_cube.apply_move(move_str)
            new_coord = move_cube.ud_slice_coord()
            move_table[coord][move_idx] = new_coord
            
    end_time = time.time()
    print(f"UDS Move table built in {end_time - start_time:.2f} seconds.")
    return move_table

def generate_uds_prune_table():
    """
    Generates the pruning table for UD slice edges using BFS.
    """
    move_table = build_uds_move_table()
    
    print("\nGenerating UD slice pruning table with BFS...")
    start_time = time.time()
    
    pruning_table = [255] * N_UDS_STATES
    # The solved state for UD slice is C(11,4)+C(10,3)+C(9,2)+C(8,1) = 330+120+36+8 = 494
    solved_coord = nCr(11, 4) + nCr(10, 3) + nCr(9, 2) + nCr(8, 1)
    queue = deque([solved_coord])
    pruning_table[solved_coord] = 0
    visited_count = 1
    
    while queue:
        current_coord = queue.popleft()
        current_depth = pruning_table[current_coord]
        
        for move_idx in range(N_MOVES):
            new_coord = move_table[current_coord][move_idx]
            if pruning_table[new_coord] == 255:
                pruning_table[new_coord] = current_depth + 1
                queue.append(new_coord)
                visited_count += 1

    end_time = time.time()
    print(f"UDS Pruning table generated in {end_time - start_time:.2f} seconds.")
    print(f"Total states visited: {visited_count}/{N_UDS_STATES}")
    
    return pruning_table

if __name__ == "__main__":
    print("--- Starting Corner Orientation Table Generation ---")
    co_pruning_table = generate_co_prune_table()
    print(f"\nSaving table to {CO_PRUNE_FILE}...")
    try:
        with open(CO_PRUNE_FILE, "wb") as f:
            f.write(bytearray(co_pruning_table))
        print("Successfully saved CO pruning table.")
    except IOError as e:
        print(f"Error saving file: {e}")

    print("\n--- Starting Edge Orientation Table Generation ---")
    eo_pruning_table = generate_eo_prune_table()
    print(f"\nSaving table to {EO_PRUNE_FILE}...")
    try:
        with open(EO_PRUNE_FILE, "wb") as f:
            f.write(bytearray(eo_pruning_table))
        print("Successfully saved EO pruning table.")
    except IOError as e:
        print(f"Error saving file: {e}")

    print("\n--- Starting UD Slice Table Generation ---")
    uds_pruning_table = generate_uds_prune_table()
    print(f"\nSaving table to {UDS_PRUNE_FILE}...")
    try:
        with open(UDS_PRUNE_FILE, "wb") as f:
            f.write(bytearray(uds_pruning_table))
        print("Successfully saved UDS pruning table.")
    except IOError as e:
        print(f"Error saving file: {e}")

    print("\nProcess complete.")
