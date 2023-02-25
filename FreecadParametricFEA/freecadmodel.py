"""FreecadModel object and helpers"""
import sys
import os
import contextlib
from .loghandler import logger

from typing import Tuple


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
    except (ImportError, ModuleNotFoundError):
        logger.exception(f'"{freecad_path}" does not contain FreeCAD Python libraries')
        raise
    logger.debug(f"FreeCAD path added to sys.path: {freecad_path}")


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
        logger.debug(f"Opened FreeCAD model {document_path}")

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
            try:
                raise KeyError(f"Unable to find object {object_name} in the model")
            except KeyError as e:
                logger.exception(str(e))
                raise

        # supported specific object types:
        # <Sketcher::SketchObject>
        # <App::MaterialObjectPython object>

        # FIXME: this should really be done via type checking

        try:
            target_str = str(target_object[0])

            # sketcher objects need obj.getDatum / obj.setDatum
            if target_str == "<Sketcher::SketchObject>":
                target_object[0].getDatum(constraint_name)
                logger.debug(
                    f"Object {object_name} is a sketch, found {constraint_name}"
                )

                target_object[0].setDatum(constraint_name, target_value)

            # materials need some special treatment via material cards
            elif target_str == "<App::MaterialObjectPython object>":
                from materialtools.cardutils import import_materials as getmats  # type: ignore

                materials, _, _ = getmats(target_object[0].Category)

                for (_, m) in materials.items():
                    if m["CardName"] == target_value:
                        target_object[0].Material = m
                        return

                logger.debug(
                    f"Object {object_name} is a material, "
                    "setting material {constraint_name}"
                )

            # generic objects need setattr(obj, attr, value)
            else:
                getattr(target_object[0], constraint_name)
                logger.debug(
                    f"Object {object_name} is an object, found {constraint_name}"
                )

                setattr(target_object[0], constraint_name, target_value)

        except (NameError, IndexError):
            logger.exception(
                f"Invalid constraint name {constraint_name} in object {object_name}"
            )
            raise

        logger.debug(f"Set {object_name}.{constraint_name} to {target_value}")
        # apply changes and recompute
        self.model.recompute()
        logger.debug("Model recomputed")
        # TODO: check for model errors here

    def run_fea(self):
        """runs a FEA analysis in the specified freecad document

        Args:
            solver_name (str): name of the solver (e.g. SolverCcxTools)
            fea_results_name (str): name of the FEA results container (e.g.
                CCX_Results)

        Returns:
            fea object: a FreeCAD object containing the FEA results
        """

        if self.solver_name == "":
            self._find_solver_result_names()

        solver_object = self.model.getObject(self.solver_name)

        fea = femtools.ccxtools.FemToolsCcx(solver=solver_object)
        fea.purge_results()
        fea.reset_all()
        fea.update_objects()
        logger.debug(f"Prepared solver {solver_object.Name}")

        # there should be some error handling here
        fea.check_prerequisites()
        logger.debug("Checked FEA prerequisites")
        # patching this because Calculix prints some useless info in
        # Freecad 0.20 for solid models only... see bug #3
        with open(os.devnull, "w", encoding="utf8") as devnull:
            with contextlib.redirect_stdout(devnull):
                fea.run()

        if fea.results_present:
            logger.debug("FEA results generated")
            return self.model.getObject(self.fea_results_name)
        else:
            try:
                raise RuntimeError("FEA results are not present")
            except RuntimeError as e:
                logger.exception(str(e))
                raise

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
            logger.info(f"Exporting VTK file {filename}")
            del objects
        else:
            try:
                raise NotImplementedError(
                    f"Export method {export_format} not available"
                )
            except NotImplementedError as e:
                logger.exception(str(e))
                raise

    def _find_solver_result_names(self) -> Tuple[str, str]:
        # do stuff...
        solver_name = ""
        fea_results_name = ""

        for el in self.model.Objects:
            if str(el) == "<Fem::FemSolverObjectPython object>":
                solver_name = el.Name
            if str(el) == "<Fem::FemResultObjectPython object>":
                fea_results_name = el.Name

        if "" in (solver_name, fea_results_name):
            try:
                raise NameError(
                    "FEA solver or results not found, consider "
                    "specifying manually using parametric.setup_fea()"
                )
            except NameError as e:
                logger.exception(str(e))
                raise

        logger.debug(f"Found solver name: {solver_name}")
        logger.debug(f"Found FEA results name: {fea_results_name}")

        self.solver_name = solver_name
        self.fea_results_name = fea_results_name
        return (self.solver_name, self.fea_results_name)
