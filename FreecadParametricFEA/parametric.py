"""Provides a FreecadParametricFEA class to handle higher level parametric FEA functions, 
    such as handling parameters and displaying results.   
"""
import time
import warnings
from typing import Union
from os import path
import pandas as pd
import numpy as np


import plotly.express as px

from .freecadmodel import FreecadModel


class parametric:
    """FreeCAD Parametric FEA object"""

    def __init__(self, freecad_path: str) -> None:
        """Initialises a FreecadParametricFEA object

        Args:
            freecad_path (str): path to the local FreeCAD installation.

        """
        self.freecad_document = None
        self.variables = []
        self.outputs = []
        self.fea_results_name = ""
        self.solver_name = ""

        self.freecad_path = freecad_path

        self.results_dataframe = pd.DataFrame()

    def set_model(self, freecad_document: Union[str, FreecadModel]):
        """opens the freecad document and loads it

        Args:
            freecad_document (str or FreecadModel): path to the
                FreeCAD document, or a FreecadModel object
        """
        if isinstance(freecad_document, str):
            self.freecad_document = FreecadModel(
                document_path=freecad_document, freecad_path=self.freecad_path
            )
        elif isinstance(freecad_document, FreecadModel):
            self.freecad_document = freecad_document

    def set_variables(self, variables: list):
        """Sets the variables to run the batch analysis over.

        Args:
            variables (list of dict): a list of dictionaries. The dictionaries
                must contain:
                "object_name" (str): the object where the constraint is in,
                "constraint_name" (str): the name of the constraint to modify
                "constraint_values" (list of values): the values that the variable can assume
        """
        self.variables = variables

    def set_outputs(self, outputs: list):
        """Sets the variables to return as an output.

        Args:
            variables (list of dict): a list of dictionaries. The dictionaries
            must contain:
                "output_var" (str): the output variable (must be available in
                    the freecad fea results object),
                "reduction_fun" (function handle): a handle to the data
                    reduction function (e.g. np.max)
        """
        Warning("set_outputs() is not functioning yet - requested outputs ignored")
        default_outputs = [
            {
                "output_var": "vonMises",
                "reduction_fun": np.max,
            },
            {
                "output_var": "DisplacementLengths",
                "reduction_fun": np.max,
            },
        ]
        self.outputs = default_outputs

    def setup_fea(self, fea_results_name: str, solver_name: str):
        """sets up the FEA analysis object

        Args:
            fea_results_name (str): name of the results object in the document
                e.g. CCX_Results
            solver_name (str): name of the solver object in the document
                e.g. SolverCcxTools
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

    def run_parametric(
        self, dry_run: bool = False, export_results: bool = False
    ) -> pd.DataFrame:
        """runs the parametric sweep and returns the results

        Args:
            ?dry_run (bool): Doesn't run the FEA, but checks for model issues.
                Defaults to False
            ?export_results (bool): export results in .vtk format for each analysis
                Defaults to False

        Returns:
            pd.DataFrame: Pandas dataframe containing the results
        """
        # TODO: this should let the user choose the type of run
        # e.g. "all" (full sampling), and other useful stuff like latin
        # hypercube sampling, random sampling, adaptive sampling...

        # change the target parameter in the CAD model.
        # as it stands it won't really support two parameters...
        # what if
        #  - create a dataframe with the parameters first
        #  - ran a single loop of all analyses over the dataframe
        #  - updated the dataframe?

        self.results_dataframe = self.populate_test_dataframe(
            self.variables, self.outputs
        )

        # iterate over all test cases
        for test_case_idx, test_case_data in self.results_dataframe.iterrows():
            # change each parameter to the value specified in the pd column:
            for parameter in self.variables:
                df_heading = self.param_to_df_heading(parameter)

                self.freecad_document.change_parameter(
                    object_name=parameter["object_name"],
                    constraint_name=parameter["constraint_name"],
                    target_value=test_case_data[df_heading],
                )

            # run (& time) the FEA
            if not dry_run:
                start_time = time.process_time()

                try:
                    fea_results_obj = self.freecad_document.run_fea(
                        solver_name=self.solver_name,
                        fea_results_name=self.fea_results_name,
                    )

                    fea_runtime = time.process_time() - start_time

                    if self.outputs == []:
                        self.set_outputs(outputs=[])
                    for output in self.outputs:
                        pass

                    # adding results to a Pandas dataframe
                    self.results_dataframe.loc[test_case_idx, "vonMises"] = max(
                        fea_results_obj.vonMises
                    )

                    self.results_dataframe.loc[
                        test_case_idx, "DisplacementLengths"
                    ] = max(fea_results_obj.DisplacementLengths)

                    self.results_dataframe.loc[
                        test_case_idx, "FEA_runtime"
                    ] = fea_runtime

                    # export if requested
                    # TODO: infer the number of digits from the size of the dataframe? somehow
                    # TODO: try and join the VTK files together as frames
                    if export_results:
                        (folder, filename) = path.split(self.freecad_document.filename)
                        (fn, _) = path.splitext(filename)
                        self.freecad_document.export_fea_results(
                            filename=path.join(
                                folder, f"FEA_{fn}_{test_case_idx:03}.vtu"
                            ),
                            export_format="vtk",
                        )

                except RuntimeError as e:
                    self.results_dataframe.loc[test_case_idx, "Msg"] = str(e)

        return self.results_dataframe

    def populate_test_dataframe(self, variables, outputs) -> pd.DataFrame:
        """Populates FreecadParametricFEA.results_dataframe with the
        test matrix to be run by the FEA batch. Uses self.variables
        and self.results.

        Args:
            variables (list): variables as defined in set_variables()

        Returns:
            pd.DataFrame: dataframe with test conditions and empty
                results columns
            param_headings: headings in the dataframe related to the variables
            output_headings: headings in the dataframe related to the output
        """
        param_vals = []
        param_headings = []
        output_headings = []

        for parameter in variables:
            param_vals.append(parameter["constraint_values"])
            param_headings.append(self.param_to_df_heading(parameter))

        # TODO: use real outputs later
        output_headings = ["vonMises", "DisplacementLengths"]
        warnings.warn(
            "set_outputs() is not functioning yet - requested outputs ignored"
        )

        # Build list of n-param values
        grid = np.meshgrid(*param_vals)
        grid_list = list(x.ravel() for x in grid)
        param_values_ndim = np.column_stack(grid_list)

        empty_results = np.empty((len(grid_list[0]), len(output_headings) + 1))
        param_values_all = np.column_stack((param_values_ndim, empty_results))

        df = pd.DataFrame(
            data=param_values_all,
            columns=[*param_headings, *output_headings, "FEA_runtime"],
        )
        df["Msg"] = ""
        return df

    def plot_fea_results(self):
        """Plots the FEM analysis results using Plotly"""

        for output in self.outputs:
            if (len(self.variables)) == 1:
                fig = px.line(
                    self.results_dataframe,
                    x=self.param_to_df_heading(self.variables[0]),
                    y=output["output_var"],
                )
            elif (len(self.variables)) == 2:
                fig = px.line(
                    self.results_dataframe,
                    x=self.param_to_df_heading(self.variables[0]),
                    y=output["output_var"],
                    color=self.param_to_df_heading(self.variables[1]),
                )
            else:
                raise NotImplementedError(
                    "Plotting more than 2 variables not supported yet"
                )

            # Set x-axis title
            # TODO: find these from the objects or pass as parameters
            constraint_name = "CHANGE_ME"
            constraint_units = "CHANGE_ME"
            # these will definitely need to change
            # fig.update_xaxes(
            #     title_text=f"{constraint_name} ({constraint_units})"
            # )

            # # Set y-axes titles
            # fig.update_yaxes(
            #     title_text="Max. Von Mises (MPa)", secondary_y=False
            # )
            # fig.update_yaxes(
            #     title_text="Max. displacement (mm)", secondary_y=True
            # )

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

    def param_to_df_heading(self, parameter) -> str:
        return parameter["object_name"] + "." + parameter["constraint_name"]
