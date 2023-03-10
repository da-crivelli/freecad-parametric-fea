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
from FreecadParametricFEA import parametric
import numpy as np

# initialise a parametric FEA object
fea = parametric()

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
### Different names for CCX solver and CCX results
Renaming the CCX solver and results won't affect the solution, but if you're having trouble running the analysis you can set them yourself just before `run_parametric()`:

```python
# in case you need to explicitly set the CalculiX results object and the solver name
fea.setup_fea(fea_results_name="CCX_Results", solver_name="SolverCcxTools")
```

### Exporting data

You can export individual ParaView files using:

```python
results = fea.run_parametric(export_results=True, output_folder="path/to/my/results")
```


Or just save the results dataframe in a .csv, json or serialised pickle object:

```python
fea.save_fea_results("results.csv")
fea.save_fea_results("results.json", mode="json")
fea.save_fea_results("results.pickle", mode="pickle")
```

... or even take a look at the parameters matrix before running any analysis:

```python
results = fea.run_parametric(dry_run=True)
```

### Custom FreeCAD path
If you have multiple installations of FreeCAD or are using a system other than Windows (as of version <=0.3) you have to specify the path to FreeCAD manually in the call to `parametric`:

```python
# you can manually specify the path to FreeCAD on your system:
FREECAD_PATH = "C:/Program Files/FreeCAD 0.20/bin"
fea = parametric(freecad_path=FREECAD_PATH)
```
# Limitations and caveats

As of 0.3:
 * this has been tested on FreeCAD 0.20, on Windows only, but you can try other platforms
 * only Netgen meshes are supported
 * Only static FEM analysis has been tested

# Contributing
I have created this for hobby and personal use, as I was interested in learning more about FreeCAD and writing Python modules. There are a lot of things that I would like to fix, if you want to get involved have a look at the [open issues](https://github.com/da-crivelli/freecad-parametric-fea/issues/) and send me a message if you have any questions.


