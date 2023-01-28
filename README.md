# freecad-parametric-fea

 A flexible parametric FEA library based on FreeCAD

## v0.1
Simple n-parameter FEA with minimal output control 

### TODO
- error handling in model and output dataframe
- add support for multiple parameters
- move away from two plots in one
- better define plot when >3 parameters
- make the outputs scriptable / selectable
- describe how to run the example; better README

### DONE
- :white_check_mark: move FREECADPATH into init.py & autodiscover 
- :white_check_mark: document classes etc
- :white_check_mark: add "dry run" option when model is checked for parameter changes but no FEA is run

## v0.2
A more professional feel; better support for output control

- add logging
- add screenshots / renderings for each datapoint
- allow selecting node sets for outputs
- add optional parameters for plots
