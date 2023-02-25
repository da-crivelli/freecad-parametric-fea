# freecadparametricfea

 A flexible parametric FEA library based on [FreeCAD](https://www.freecadweb.org/), currently supporting FreeCAD 0.20 on Windows.
 
 If you have 20 minutes I recommend the video tutorial on the [@engineeringmaths Youtube channel](https://www.youtube.com/watch?v=cwtgB4KpdJo).

> **Warning:**
> this project is very early release, and should not be used for any serious structural analysis. It is aimed at hobbyists and makers

## Quickest start
Create a Python 3.8 virtual environment:

`pipenv --python 3.8`

Install the latest version from pypi:

`pipenv install freecadparametricfea`

then run any of the examples inside [the examples folder](examples/)

## Quick start

Create a FreeCAD part and assign names to the constraints that you want to change. You need to set up a FEA analysis as well, I have tested this using CalculiX and Netgen.

Then in a script, or on the command line, run:

```python
from FreecadParametricFEA import parametric as pfea
import numpy as np
# you need to manually specify the path to FreeCAD on your system, for now:
FREECAD_PATH = "C:/Program Files/FreeCAD 0.20/bin"

# initialise a parametric FEA object
fea = pfea(freecad_path=FREECAD_PATH)

# load the FreeCAD model
fea.set_model("your-part-here.fcstd")

# list the parameters to sweep:
fea.set_variables(
    [
        {
            "object_name": "CutsSketch", # the object where to find the constraint
            "constraint_name": "NotchDistance", # the constraint name that you assigned 
            "constraint_values": np.linspace(10, 30, 5), # the values you want to check
        },
        {
            "object_name": "CutsSketch",
            "constraint_name": "NotchDiam",
            "constraint_values": np.linspace(5, 9, 5),
        },
    ]
)

# setup the FEA analysis - we need to know the CalculiX results object and the solver name
fea.setup_fea(fea_results_name="CCX_Results", solver_name="SolverCcxTools")

# run and save the results (will return a Pandas DataFrame)
results = fea.run_parametric()

# plot the results
fea.plot_fea_results()
```

## Feeling fancy

### Custom outputs
The default is to export the max Von Mises stress and max displacement values. You can also specify your own values and data reduction function like this:

```python
fea.set_outputs([
        {
            "output_var": "vonMises",
            "reduction_fun": np.median,
        },
        {
            "output_var": "vonMises",
            "reduction_fun": lambda v: np.percentile(v, 95),
            "column_label": "95th percentile"
        }
    ])
```

### Changing materials
You can specify any material that you can find in the FreeCAD FEA material selection dropdown; just refer to it by its name:

```python
fea.set_outputs([
    {
        "object_name": "MaterialSolid",  # the object where to find the constraint
        "constraint_name": "Material",  # the constraint name that you assigned
        "constraint_values": ["Aluminium-Generic", "Steel-Generic"],
    },
])
```


### Exporting data

You can export individual ParaView files using:

```python
results = fea.run_parametric(export_results=True, output_folder="path/to/my/results")
```


Or just save the results dataframe in a .csv:

```python
fea.save_fea_results("results.csv")
```

... or even take a look at the parameters matrix before running any analysis:

```python
results = fea.run_parametric(dry_run=True)
```

# Limitations and caveats

As of 0.1.2:
 * only netgen meshes are supported

# Contributing
I have created this for hobby and personal use, as I was interested in learning more about FreeCAD and writing Python modules. There are a lot of things that I would like to fix, if you want to get involved have a look at the [open issues](https://github.com/da-crivelli/freecad-parametric-fea/issues/) and send me a message if you have any questions.


