# app.py
#
# This script creates a simple Flask web server to provide a web API
# for the Rubik's Cube solver.

from flask import Flask, request, jsonify
from flask_cors import CORS
from solver import solve as solve_cube # Renamed import to avoid conflict with function name

# Initialize the Flask application
app = Flask(__name__)

# Enable Cross-Origin Resource Sharing (CORS) for all routes
# This is not strictly necessary now that Flask serves the frontend,
# but it's kept here for flexibility during development.
CORS(app)

@app.route('/solve', methods=['GET'])
def solve_endpoint():
    """
    API endpoint to solve a Rubik's Cube scramble.
    Accepts a 'scramble' query parameter.
    e.g., http://127.0.0.1:5002/solve?scramble=R U F'
    """
    # Get the scramble string from the URL query parameters
    scramble_str = request.args.get('scramble')

    # Check if the scramble parameter was provided
    if not scramble_str:
        return jsonify({"error": "A 'scramble' query parameter is required."}), 400

    # Call the solver function from our solver script
    # Note: The solver function prints its own progress, which will appear in the console
    print(f"Received API request for scramble: {scramble_str}")
    solution_str = solve_cube(scramble_str) # Call the imported solver function

    # If the solver returns an explicit error string, return 400
    if isinstance(solution_str, str) and solution_str.startswith("ERROR:"):
        return jsonify({
            "error": solution_str,
            "scramble": scramble_str
        }), 400

    # CORRECTED LOGIC: Check if a valid solution (including empty string) was found.
    # An empty string means the cube is already solved relative to the goal.
    if solution_str is not None: # This is the key change!
        # Return the scramble and its solution in a JSON response
        return jsonify({
            "scramble": scramble_str,
            "solution": solution_str
        })
    else:
        # This 'else' block now only catches cases where solve_cube explicitly returns None
        # for a complete failure, which is how we designed it to behave for "too deep" limits.
        return jsonify({
            "error": "Solver could not find a solution within the search limits, or an unexpected error occurred.",
            "scramble": scramble_str
        }), 500

if __name__ == "__main__":
    """
    Main execution block to run the Flask application.
    The server will be accessible on http://127.0.0.1:5000
    """
    # Setting debug=True enables auto-reloading when the code changes
    app.run(debug=True, port=5002)