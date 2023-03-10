from os import path
import numpy as np
from FreecadParametricFEA import parametric as pfea


"""
A single parameter sweep on a simple 3D linkage model.
Runs a static analysis and extracts the max. Von Mises stress
and max deflection.
"""

FREECAD_PATH = "C:/Program Files/FreeCAD 0.20/bin"

# initialise the parametric FEA object
fea = pfea(freecad_path=FREECAD_PATH)
# set a path to the FreeCAD model
script_path = path.dirname(path.realpath(__file__))
fea.set_model(path.join(script_path, "notch-example.fcstd"))
# list the parameters to sweep
fea.set_variables(
    [
        {
            "object_name": "CutsSketch",
            "constraint_name": "NotchDistance",
            "constraint_values": np.linspace(10, 30, 2),
        },
        {
            "object_name": "CutsSketch",
            "constraint_name": "NotchDiam",
            "constraint_values": np.linspace(5, 9, 2),
        },
    ]
)

fea.set_outputs(
    [
        {
            "output_var": "vonMises",
            "reduction_fun": np.median,
        },
        {
            "output_var": "vonMises",
            "reduction_fun": lambda v: np.percentile(v, 95),
            "column_label": "95th percentile"
        },        
    ]
)

# setup the FEA
fea.setup_fea(fea_results_name="CCX_Results", solver_name="SolverCcxTools")

#results = fea.run_parametric(export_results=True)
results = fea.run_parametric()

fea.plot_fea_results()

fea.save_fea_results(path.join(script_path, "notch-results.csv"))
print(results)
