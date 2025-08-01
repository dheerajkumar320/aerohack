# solver.py
#
# This script implements the Kociemba's Two-Phase IDA* algorithm
# to solve a Rubik's Cube. It relies on pre-computed pruning tables
# generated by 'generate_tables.py' and the Cube model from 'cube_model.py'.

import os
import time
from cube_model import Cube # Assuming cube_model.py is in the same directory

# --- Constants and Table Loading ---
TABLES_DIR = "solver_tables" # Directory where pruning tables are stored
CO_PRUNE_FILE = os.path.join(TABLES_DIR, "co_prune.dat")
EO_PRUNE_FILE = os.path.join(TABLES_DIR, "eo_prune.dat")
UDS_PRUNE_FILE = os.path.join(TABLES_DIR, "uds_prune.dat")

# Global variables to store pruning tables (loaded once on script start)
co_prune_table = None
eo_prune_table = None
uds_prune_table = None

def load_pruning_tables():
    """Loads the pre-computed pruning tables into global memory."""
    global co_prune_table, eo_prune_table, uds_prune_table
    
    print("Initializing solver: Loading pruning tables...")
    try:
        with open(CO_PRUNE_FILE, "rb") as f:
            co_prune_table = bytearray(f.read())
        with open(EO_PRUNE_FILE, "rb") as f:
            eo_prune_table = bytearray(f.read())
        with open(UDS_PRUNE_FILE, "rb") as f:
            uds_prune_table = bytearray(f.read())
        print("Pruning tables loaded successfully.")
    except FileNotFoundError as e:
        print(f"Error: Pruning table not found at {e.filename}.")
        print("Please ensure 'solver_tables' directory exists and contains the .dat files.")
        print("You likely need to run 'generate_tables.py' first.")
        exit(1) # Exit if tables are not found, as the solver cannot function

# Load tables when the module is imported (e.g., by app.py)
load_pruning_tables()

# Allowed moves for each phase
PHASE1_MOVES = [
    "U", "U2", "U'", "D", "D2", "D'",
    "L", "L2", "L'", "R", "R2", "R'",
    "F", "F2", "F'", "B", "B2", "B'"
]
# Phase 2 only allows quarter turns of U/D faces and half turns of L/R/F/B faces
PHASE2_MOVES = [
    "U", "U2", "U'", "D", "D2", "D'",
    "L2", "R2", "F2", "B2"
]

def heuristic(cube, phase):
    """
    Calculates the heuristic value (h(n)) for the current cube state.
    Uses the pre-loaded pruning tables.
    """
    if phase == 1:
        co_coord = cube.corner_orientation_coord()
        eo_coord = cube.edge_orientation_coord()
        uds_coord = cube.ud_slice_coord()
        
        # h(n) = max(dist_co, dist_eo, dist_uds)
        return max(co_prune_table[co_coord], eo_prune_table[eo_coord], uds_prune_table[uds_coord])
    else: # Phase 2
        # In Phase 2, corner and edge orientations are solved.
        # We primarily use the UD slice coordinate heuristic here.
        # For a full Kociemba, you'd also have permutation tables for corners and edges.
        uds_coord = cube.ud_slice_coord()
        
        # NOTE: A critical assumption here is that uds_prune_table is non-zero
        # for *any* state not fully solved regarding the UD slice. If a simple
        # RUR operation somehow maps to a 0 in your UDS table, it might cause Phase 2
        # to find an empty solution prematurely.
        return uds_prune_table[uds_coord]

# Helper function to get the inverse of a move string
def inverse_move(move_str):
    if len(move_str) == 1: # e.g., "U" -> "U'"
        return move_str + "'"
    elif move_str[1] == "'": # e.g., "U'" -> "U"
        return move_str[0]
    else: # move_str[1] == '2', e.g., "U2" -> "U2" (self-inverse)
        return move_str

def search(cube, depth, bound, path, phase):
    """
    The core recursive search function for IDA* (Iterative Deepening A*).
    Finds a solution path for the current phase within a given depth bound.
    """
    h_val = heuristic(cube, phase)
    f = depth + h_val # f(n) = g(n) + h(n)

    # Debugging print (uncomment if you need verbose output)
    # print(f"  [DEBUG] Phase {phase} - Depth: {depth}, Heuristic: {h_val}, f: {f}, Bound: {bound}")
    # print(f"  [DEBUG] Current path: {path}")
    # if h_val > 0: # Only print cube state if not solved for clarity
    #     print(f"  [DEBUG] Current cube state (for phase {phase}): CO={cube.corner_orientation_coord()}, EO={cube.edge_orientation_coord()}, UDS={cube.ud_slice_coord()}")


    # Pruning step: If f(n) exceeds the current bound, prune this branch.
    if f > bound:
        return None, f # Return None for solution, and the minimum f-value encountered

    # Goal test: If heuristic is 0, the goal state for this phase is reached.
    if h_val == 0:
        return path, 0 # Return the path (solution) and 0 for new_bound (goal reached)

    min_f_found = float('inf') # To track the minimum f-value for the next iteration's bound
    moves = PHASE1_MOVES if phase == 1 else PHASE2_MOVES
    
    for move_str in moves:
        # Optimization: Don't apply moves that directly cancel the previous one
        # or consecutive moves on the same face (e.g., U U instead of U2)
        if path:
            last_move = path[-1]
            
            # Check for direct cancellation (e.g., U followed by U')
            if move_str == inverse_move(last_move):
                continue
            
            # Check for consecutive moves on the same face (e.g., U then U, U2, or U')
            # This avoids redundant search paths if U2 is already preferred.
            if move_str[0] == last_move[0]:
                continue 
            
        # Apply the move to the cube
        cube.apply_move(move_str)
        
        # Recursive call: Explore the next state
        solution, new_f_from_child = search(cube, depth + 1, bound, path + [move_str], phase)
        
        # Backtrack: Undo the move to restore the cube state for the next sibling branch
        cube.apply_move(inverse_move(move_str))
            
        # If a solution was found in the recursive call, propagate it up immediately
        if solution is not None:
            return solution, 0
        
        # Update the minimum f-value found in this iteration (for determining the next bound)
        min_f_found = min(min_f_found, new_f_from_child)

    return None, min_f_found

def solve(scramble_str):
    """
    Main solver function that orchestrates the two-phase IDA* search.
    Takes a scramble string as input and returns the solution as a string.
    Returns an empty string if the cube is already solved, or an "ERROR:" string on failure.
    """
    print(f"Solving scramble: {scramble_str}")
    
    # --- Phase 1: Reduce to G1 Group (orientations solved, UD-slice correct) ---
    phase1_cube = Cube()
    phase1_cube.apply_move(scramble_str)
    
    bound = heuristic(phase1_cube, 1) # Start bound at the initial heuristic value
    phase1_solution = None
    print("--- Starting Phase 1 ---")
    
    # Iterative Deepening loop for Phase 1
    while True:
        # print(f"Searching Phase 1 with bound: {bound}") # Uncomment for verbose debugging
        solution, new_bound = search(phase1_cube, 0, bound, [], 1)
        
        if solution is not None: # Solution found for Phase 1
            phase1_solution = solution
            break
        
        # Handle cases where new_bound is excessively large (no path found)
        if new_bound == float('inf'): 
             print("Phase 1 search exhausted or hit an unreachable state.")
             return "ERROR: Phase 1 search failed (unreachable or infinite bound)."

        bound = new_bound # Increase bound for the next iteration
        # Safety break for Phase 1: typical max depth for 3x3 is around 12-14.
        # If it goes much deeper, something might be wrong or it's genuinely too hard.
        if bound > 14: 
             print(f"Phase 1 search too deep (bound={bound}), aborting.")
             return "ERROR: Phase 1 search exceeded depth limit."

    print(f"Phase 1 solution found: {' '.join(phase1_solution) if phase1_solution else ' (already in G1)'}")

    # --- Phase 2: Solve from G1 to Solved (permutations solved) ---
    phase2_cube = Cube()
    phase2_cube.apply_move(scramble_str) # Apply original scramble
    
    # Apply Phase 1 solution to transition to the G1 group
    # CRITICAL FIX: Only apply if phase1_solution is not empty.
    # If phase1_solution is [], joining it results in "", which apply_move might not handle.
    if phase1_solution:
        phase2_cube.apply_move(' '.join(phase1_solution))
    
    # Initial bound for Phase 2 can also start from its heuristic.
    bound = heuristic(phase2_cube, 2)
    phase2_solution = None
    print("\n--- Starting Phase 2 ---")
    
    # Iterative Deepening loop for Phase 2
    while True:
        # print(f"Searching Phase 2 with bound: {bound}") # Uncomment for verbose debugging
        solution, new_bound = search(phase2_cube, 0, bound, [], 2)
        
        if solution is not None: # Solution found for Phase 2
            phase2_solution = solution
            break
        
        if new_bound == float('inf'):
            print("Phase 2 search exhausted or hit an unreachable state.")
            return "ERROR: Phase 2 search failed (unreachable or infinite bound)."

        bound = new_bound # Increase bound for the next iteration
        # Safety break for Phase 2: typical max depth for full G2 solve is around 18-20.
        if bound > 22: # Increased slightly for robustness in edge cases
            print(f"Phase 2 search too deep (bound={bound}), aborting.")
            return "ERROR: Phase 2 search exceeded depth limit."

    print(f"Phase 2 solution found: {' '.join(phase2_solution) if phase2_solution else ' (already solved)'}")
    
    # Combine solutions. This will be an empty string if both phases return empty lists.
    full_solution_moves = phase1_solution + phase2_solution
    return ' '.join(full_solution_moves)

if __name__ == "__main__":
    # Example usage when running solver.py directly for testing

    print("--- Solver Test Run ---")

    test_scrambles = [
        "R U R' U'", # A common 4-move scramble
        "U U U U U U", # Highly redundant, should simplify to U2
        "R U U U U U U U U R", # Simplifies to R U R
        "R R R R R R", # Simplifies to R2 (This is the problematic one for you)
        "L2 F2 U2 R2 B2 D2 F2 L2 U2 B2 R2 D2", # A deep (20-move) scramble
        "", # Test an already solved cube
        "U", # Simple 1-move scramble
        "F L D B' U' R F'" # Another example
    ]

    for i, scramble_to_test in enumerate(test_scrambles):
        print(f"\n--- Running Test Case {i+1}: '{scramble_to_test}' ---")
        start_time = time.time()
        
        solution_path = solve(scramble_to_test)
        
        end_time = time.time()
        
        if solution_path and not solution_path.startswith("ERROR:"):
            print(f"\nFinal Solution: '{solution_path}'")
            print(f"Total moves: {len(solution_path.split()) if solution_path else 0}")
        else:
            print(f"\nSolver result: {solution_path}")
            
        print(f"Total time: {end_time - start_time:.4f} seconds")