"""Provides a FreecadParametricFEA class to handle higher level parametric FEA functions,
such as handling parameters and displaying results.
"""
import time
from typing import Union
import pandas as pd


import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .freecadmodel import FreecadModel


class FreecadParametricFEA:
    """FreeCAD Parametric FEA object"""

    def __init__(self, freecad_path: str) -> None:
        """Initialises a FreecadParametricFEA object

        Args:
            freecad_path (str): path to the local FreeCAD installation.
        """
        self.freecad_document = None
        self.variables = None
        self.fea_results_name = None
        self.solver_name = None

        self.freecad_path = freecad_path

        self.results_dataframe = pd.DataFrame()

    def set_model(self, freecad_document: Union[str, FreecadModel]):
        """opens the freecad document and loads it

        Args:
            freecad_document (str or FreecadModel): path to the FreeCAD document, or a
                FreecadModel object
        """
        if isinstance(freecad_document, str):
            self.freecad_document = FreecadModel(
                document_path=freecad_document, freecad_path=self.freecad_path
            )
        elif isinstance(freecad_document, FreecadModel):
            self.freecad_document = freecad_document

    def set_variables(self, variables: list):
        """Sets the variables to optimise over.

        Args:
            variables (list of dict): a list of dictionaries. The dictionaries must contain:
                "object_name" (str): the object where the constraint is contained,
                "constraint_name" (str): the name of the constraint to modify,
                "constraint_values" (list of values): the values that the variable can assume
        """
        self.variables = variables

    def setup_fea(self, fea_results_name: str, solver_name: str):
        """sets up the FEA analysis object

        Args:
            fea_results_name (str): name of the results object in the document, e.g. CCX_Results
            solver_name (str): name of the solver object in the document, e.g. SolverCcxTools
        """
        self.fea_results_name = fea_results_name
        self.solver_name = solver_name

    def run_fea(self):
        """Runs the FEM analysis

        Returns:
           fea object: a FreeCAD object containing the FEA results
        """
        return self.freecad_document.run_fea(
            solver_name=self.solver_name,
            fea_results_name=self.fea_results_name,
        )

    def run_parametric(self) -> pd.DataFrame:
        """runs the parametric sweep and returns the results

        Returns:
            pd.DataFrame: Pandas dataframe containing the results
        """
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
        """Plots the FEM analysis results using Plotly"""
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
            title_text=f"FreeCAD optimisation on {self.freecad_document.filename}"
        )

        # Set x-axis title
        # TODO: find these from the objects or pass as parameters
        constraint_name = "CHANGE_ME"
        constraint_units = "CHANGE_ME"
        # these will definitely need to change
        fig.update_xaxes(title_text=f"{constraint_name} ({constraint_units})")

        # Set y-axes titles
        fig.update_yaxes(title_text="Max. Von Mises (MPa)", secondary_y=False)
        fig.update_yaxes(title_text="Max. displacement (mm)", secondary_y=True)

        fig.show()

    def save_fea_results(self, results_filename: str, mode: str = "csv") -> None:
        """Saves the results of the analysis to a file.

        Args:
            results_filename (str): destination file
            mode (str, optional): saving mode. Can be one of:
                "csv" (default): comma separated values, as exported by Pandas

        Raises:
            NotImplementedError: if an export mode is not implemented.
        """
        if mode == "csv":
            self.results_dataframe.to_csv(results_filename)
        else:
            raise NotImplementedError(f"Export mode {mode} not yet implemented")
