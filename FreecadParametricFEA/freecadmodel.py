"""FreecadModel object and helpers"""
import sys


def _register_freecad(freecad_path: str) -> None:
    """registers the freecad path and femtools in os.PATH

    Args:
        freecad_path (str): path to the local FreeCAD installation

    Raises:
        ImportError: if the specified folder does not contain the FreeCAD Python libraries
    """
    if freecad_path is not None and freecad_path not in sys.path:
        sys.path.append(freecad_path)
    # TODO: should automagically try to find freecad in the usual suspect folders;
    # it should also automatically add /bin if the user didn't specify it
    try:
        global FreeCAD, femtools
        FreeCAD = __import__("FreeCAD", globals(), locals())
        femtools = __import__("femtools.ccxtools", globals(), locals())
    except ImportError as err:
        raise ImportError(
            f"{freecad_path} does not contain the FreeCAD Python libraries"
        ) from err


class FreecadModel:
    """FreecadModel class"""

    def __init__(self, document_path: str, freecad_path: str) -> None:
        """initialises a FreecadModel object

        Args:
            document_path (str): path to the FreeCAD file
            freecad_path (str): path to the FreeCAD Python libraries
        """
        self.filename = document_path
        _register_freecad(freecad_path=freecad_path)
        self.model = FreeCAD.open(document_path)
        # TODO: error handling

    def change_parameter(
        self, object_name: str, constraint_name: str, target_value: float
    ):
        """changes a parameter (e.g. a named constraint) inside a freecad
        document. Currently works if the constraint is inside the driving
        sketch of the referenced object (e.g. a pocket)

        Args:
            object_name (str): name of the Freecad object containing the
                sketch containing the constraint
            constraint_name (str): name of the constraint to modify
            target_value (float): target value for the constraint
        """

        target_sketch = self.model.getObject(object_name).Profile[0]

        # loop over constraints to find the target
        edge_idx = None
        for (edge_idx, constraint) in enumerate(target_sketch.Constraints):
            if constraint.Name == constraint_name:
                break

        # set the datum to the desired value
        target_sketch.setDatum(edge_idx, target_value)

        # apply changes and recompute
        self.model.recompute()

    def run_fea(self, solver_name: str, fea_results_name: str):
        """runs a FEA analysis in the specified freecad document

        Args:
            solver_name (str): name of the solver (e.g. SolverCcxTools)
            fea_results_name (str): name of the FEA results container (e.g.
                CCX_Results)

        Returns:
            fea object: a FreeCAD object containing the FEA results
        """
        solver_object = self.model.getObject(solver_name)

        fea = femtools.ccxtools.FemToolsCcx(solver=solver_object)
        fea.purge_results()
        fea.reset_all()
        fea.update_objects()

        # there should be some error handling here
        fea.check_prerequisites()
        fea.run()

        return self.model.getObject(fea_results_name)