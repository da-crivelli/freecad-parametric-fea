# freecad-parametric-fea

 A flexible parametric FEA library based on FreeCAD

## v0.1
Simple n-parameter FEA with minimal output control 

### TODO
- make the outputs scriptable / selectable
- describe how to run the example; better README
- try and suppress the ccx output
- make package installable via pypi

### DONE
- :white_check_mark: error handling in model and output dataframe
- :white_check_mark: move FREECADPATH into init.py & autodiscover 
- :white_check_mark: document classes etc
- :white_check_mark: add "dry run" option when model is checked for parameter changes but no FEA is run
- :white_check_mark: add support for multiple parameters
- :white_check_mark: fix parameter scoping (feature.parameter or absolute search)
- :white_check_mark: move away from two plots in one

## v0.2
A more professional feel; better support for output control

- add logging
- add option to save the results in the active document
- better define plot when >3 parameters
- add screenshots / renderings for each datapoint
- allow selecting node sets for outputs
- add optional parameters for plots
- option to print a scene highlighting the parameters that are being changed
