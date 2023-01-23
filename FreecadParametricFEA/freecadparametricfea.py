import sys
import time
import pandas as pd


import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _register_freecad(freecad_path: str) -> None:
    if freecad_path is not None and freecad_path not in sys.path:
        sys.path.append(freecad_path)

    try:
        global FreeCAD, femtools
        FreeCAD = __import__("FreeCAD", globals(), locals())
        femtools = __import__("femtools.ccxtools", globals(), locals())
    except ImportError as err:
        raise ImportError(
            f"{freecad_path} does not contain the FreeCAD Python libraries"
        ) from err


class FreecadParametricFEA:
    def __init__(self, freecad_path: str) -> None:
        # try and find the FreeCAD path
        _register_freecad(freecad_path=freecad_path)

        self.results_dataframe = pd.DataFrame()
        pass

    def set_model(self, freecad_document):
        if isinstance(freecad_document, str):
            self.freecad_document = FreecadModel(freecad_document)
        elif isinstance(freecad_document, FreecadModel):
            self.freecad_document = freecad_document

        pass

    def set_variables(self, variables: list):
        self.variables = variables

    def setup_fea(self, fea_results_name: str, solver_name: str):
        self.fea_results_name = fea_results_name
        self.solver_name = solver_name

    def run_fea(self):
        return self.freecad_document.run_fea(
            solver_name=self.solver_name,
            fea_results_name=self.fea_results_name,
        )

    def run_parametric(self):
        # TODO: this should let the user choose the type of run
        # e.g. "all" (full sampling), and other useful stuff like latin
        # hypercube sampling, random sampling, adaptive sampling...

        # change the target parameter in the CAD model
        for parameter in self.variables:
            for target_value in parameter["constraint_values"]:
                self.freecad_document.change_parameter(
                    object_name=parameter["object_name"],
                    constraint_name=parameter["constraint_name"],
                    target_value=target_value,
                )

                # run (& time) the FEA
                start_time = time.process_time()
                fea_results_obj = self.freecad_document.run_fea(
                    solver_name=self.solver_name,
                    fea_results_name=self.fea_results_name,
                )
                fea_runtime = time.process_time() - start_time

                # adding results to a Pandas dataframe
                self.results_dataframe = pd.concat(
                    [
                        self.results_dataframe,
                        pd.DataFrame(
                            {
                                "Target_Value": [target_value],
                                "vonMises_Max": [max(fea_results_obj.vonMises)],
                                "displacement_Max": [
                                    max(fea_results_obj.DisplacementLengths)
                                ],
                                "FEA_runtime": [fea_runtime],
                            },
                        ),
                    ],
                    ignore_index=True,
                )
        return self.results_dataframe

    def plot_fea_results(self):
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=self.results_dataframe["Target_Value"],
                y=self.results_dataframe["vonMises_Max"],
                name="Max. Von Mises (MPa)",
            ),
            secondary_y=False,
        )

        fig.add_trace(
            go.Scatter(
                x=self.results_dataframe["Target_Value"],
                y=self.results_dataframe["displacement_Max"],
                name="Max. displacement (mm)",
            ),
            secondary_y=True,
        )

        # Add figure title
        fig.update_layout(
            title_text="FreeCAD optimisation on {}".format(
                self.freecad_document.filename
            )
        )

        # Set x-axis title
        # TODO: find these from the objects or pass as parameters
        constraint_name = "CHANGE_ME"
        constraint_units = "CHANGE_ME"
        fig.update_xaxes(
            title_text="{} ({})".format(
                constraint_name, constraint_units
            )  # these will definitely need to change
        )

        # Set y-axes titles
        fig.update_yaxes(title_text="Max. Von Mises (MPa)", secondary_y=False)
        fig.update_yaxes(title_text="Max. displacement (mm)", secondary_y=True)

        fig.show()


class FreecadModel:
    def __init__(self, document_path: str) -> None:
        self.filename = document_path
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
