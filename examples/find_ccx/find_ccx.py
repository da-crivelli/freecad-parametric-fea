from FreecadParametricFEA import parametric as pfea
import numpy as np

# you need to manually specify the path to FreeCAD on your system, for now:
FREECAD_PATH = "C:/Program Files/FreeCAD 0.20/bin"

# initialise a parametric FEA object
fea = pfea(freecad_path=FREECAD_PATH)

# load the FreeCAD model
fea.set_model("./examples/find_ccx/find_ccx.FCStd")

# list the parameters to sweep:
fea.set_variables(
    [
        {
            "object_name": "Sketch",  # the object where to find the constraint
            "constraint_name": "D",  # the constraint name that you assigned
            "constraint_values": np.linspace(
                30, 40, 2
            ),  # the values you want to check
        },
        {
            "object_name": "RenamedMaterialSolid",
            "constraint_name": "Material",  # the constraint name that you assigned
            "constraint_values": ["Aluminium-Generic", "Steel-Generic"],
        },
    ]
)

# setup the FEA analysis - we need to know the CalculiX results object and the solver name
# fea.setup_fea(fea_results_name="CCX_Results", solver_name="SolverCcxTools")

# run and save the results (will return a Pandas DataFrame)
results = fea.run_parametric(export_results=True)

# plot the results
fea.plot_fea_results()

print(results)
