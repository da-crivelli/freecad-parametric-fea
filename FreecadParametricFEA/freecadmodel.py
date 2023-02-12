"""FreecadModel object and helpers"""
import sys
import os


def _register_freecad(freecad_path: str) -> None:
    """registers the freecad path and femtools in os.PATH

    Args:
        freecad_path (str): path to the local FreeCAD installation

    Raises:
        ImportError: if the specified folder does not contain the FreeCAD Python libraries
    """
    if freecad_path is not None and freecad_path not in sys.path:
        sys.path.append(os.path.normpath(freecad_path))
    # TODO: should automagically try to find freecad in the usual suspect folders;
    # it should also automatically add /bin if the user didn't specify it
    try:
        global FreeCAD, femtools, vtkResults
        FreeCAD = __import__("FreeCAD", globals(), locals())
        femtools = __import__("femtools.ccxtools", globals(), locals())
        vtkResults = __import__("feminout.importVTKResults", globals(), locals())

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

        self.solver_name = ""
        self.fea_results_name = ""
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

        target_object = self.model.getObjectsByLabel(object_name)
        if not target_object:
            raise KeyError(f"Unable to find object {object_name} in the model")

        # FIXME: this should really be done via type checking
        try:
            is_sketch = str(target_object[0]) == "<Sketcher::SketchObject>"
            if is_sketch:
                target_object[0].getDatum(constraint_name)
            else:
                getattr(target_object[0], constraint_name)
            # TODO: if setting a Feature.param, needs to be addressed directly
            # as getattr(target_object[0], constraint_name).

        except NameError as exc:
            raise NameError(
                f"Invalid constraint name {constraint_name} in object {object_name}"
            ) from exc

        # set the datum to the desired value.
        # TODO: needs to be done via setattr() if setting a feature.param
        if is_sketch:
            target_object[0].setDatum(constraint_name, target_value)
        else:
            setattr(target_object[0], constraint_name, target_value)

        # apply changes and recompute
        self.model.recompute()

        # TODO: check for model errors here

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
        self.solver_name = solver_name
        self.fea_results_name = fea_results_name

        fea = femtools.ccxtools.FemToolsCcx(solver=solver_object)
        fea.purge_results()
        fea.reset_all()
        fea.update_objects()

        # there should be some error handling here
        fea.check_prerequisites()
        fea.run()
        if fea.results_present:
            return self.model.getObject(fea_results_name)
        else:
            raise RuntimeError("FEA results are not present")

    def export_fea_results(self, filename: str, export_format: str = "vtk"):
        """exports the results of a analysis to various mesh formats

        Args:
            filename (str): path to the output file
            export_format (str, optional): output format. Defaults to "vtk".

        Raises:
            NotImplementedError: if the output format specified is not available
        """

        if export_format == "vtk":
            objects = []
            objects.append(self.model.getObject(self.fea_results_name))
            vtkResults.importVTKResults.export(objects, filename)
            del objects
        else:
            raise NotImplementedError(f"Export method {export_format} not available")
