from os import path
import numpy as np
from FreecadParametricFEA import FreecadParametricFEA as pfea


"""
A single parameter sweep on a simple 3D linkage model.
Runs a static analysis and extracts the max. Von Mises stress 
and max deflection.
"""

# initialise the parametric FEA object
fea = pfea()
# set a path to the FreeCAD model
script_path = path.dirname(path.realpath(__file__))
fea.set_model(path.join(script_path, "linkage-example.fcstd"))
# list the parameters to sweep
fea.set_variables(
    [
        {
            "object_name": "Pocket",
            "constraint_name": "Spacing",
            "constraint_values": np.arange(15, 30, 3),
        },
    ]
)

# setup the FEA
fea.setup_fea(fea_results_name="CCX_Results", solver_name="SolverCcxTools")
results = fea.run_parametric()
fea.plot_fea_results()

print(results)
