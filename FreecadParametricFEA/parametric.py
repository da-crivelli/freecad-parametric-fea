"""Provides a FreecadParametricFEA class to handle higher level parametric FEA functions,
    such as handling parameters and displaying results.
"""
import time
from typing import Union
from os import path
import pandas as pd
import numpy as np

import pickle

from tqdm import tqdm

import plotly.express as px

from .freecadmodel import FreecadModel
from .loghandler import logger


class parametric:
    """FreeCAD Parametric FEA object"""

    def __init__(self, freecad_path: str = "") -> None:
        """Initialises a FreecadParametricFEA object

        Args:
            freecad_path (str): (optional) path to the local FreeCAD installation.
                If not set, freecadmodel will make a few attempts at finding it in common
                locations

        """
        self.variables = []
        self.outputs = []
        self.fea_results_name = ""
        self.solver_name = ""

        self.freecad_path = freecad_path

        self.results_dataframe = pd.DataFrame()

        # initialise output headings to defaults
        self.set_outputs()

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

        logger.info(f"FreeCAD document {freecad_document} loaded successfully")

    def set_variables(self, variables: list):
        """Sets the variables to run the batch analysis over.

        Args:
            variables (list of dict): a list of dictionaries. The dictionaries
                must contain:
                "object_name" (str): the object where the constraint is in,
                "constraint_name" (str): the name of the constraint to modify
                "constraint_values" (list of values):  values that the variable can assume
        """
        self.variables = variables

    def set_outputs(self, outputs: list = []):
        """Sets the variables to return as an output.

        Args:
            variables (list of dict): a list of dictionaries. The dictionaries
            must contain:
                "output_var" (str): the output variable (must be available in
                    the freecad fea results object),
                "reduction_fun" (function handle): a handle to the data
                    reduction function (e.g. np.max)
                ?"column_label" (str): (optional) label for the column.
                    Defaults to the function's __qualname__
        """
        if outputs == []:
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
        else:
            self.outputs = outputs

        logger.debug(f"Analysis outputs set to {self.outputs}")

    def setup_fea(self, fea_results_name: str, solver_name: str):
        """sets up the FEA analysis object

        Args:
            fea_results_name (str): name of the results object in the document
                e.g. CCX_Results
            solver_name (str): name of the solver object in the document
                e.g. SolverCcxTools
        """
        self.freecad_document.fea_results_name = fea_results_name
        self.freecad_document.solver_name = solver_name

    def run_parametric(
        self,
        dry_run: bool = False,
        export_results: bool = False,
        output_folder: str = "",
        quiet_mode: bool = False,
    ) -> pd.DataFrame:
        """runs the parametric sweep and returns the results

        Args:
            ?dry_run (bool): Doesn't run the FEA, but checks for model issues.
                Defaults to False
            ?export_results (bool): export results in .vtk format for each analysis
                Defaults to False
            ?output_folder (str): folder for results output
            ?quiet_mode (bool): suppresses all output.
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
        logger.debug("Results dataframe initialised")

        # iterate over all test cases

        if not quiet_mode:
            pbar = tqdm(total=len(self.results_dataframe), desc="Running test cases")

        for (test_case_idx, test_case_data) in self.results_dataframe.iterrows():
            # change each parameter to the value specified in the pd column:
            for parameter in self.variables:
                df_heading = self._param_to_df_heading(parameter)

                try:
                    self.freecad_document.change_parameter(
                        object_name=parameter["object_name"],
                        constraint_name=parameter["constraint_name"],
                        target_value=test_case_data[df_heading],
                    )
                except ValueError as e:
                    self.results_dataframe.loc[  # type: ignore (Pylance's fault)
                        test_case_idx, "Msg"
                    ] = str(e)

            # run (& time) the FEA
            if not dry_run:
                start_time = time.process_time()

                try:
                    fea_results_obj = self.freecad_document.run_fea()
                    fea_runtime = time.process_time() - start_time
                    logger.info(f"FEA test case {test_case_idx} ran in {fea_runtime}s")

                    if self.outputs == []:
                        self.set_outputs()
                    for output in self.outputs:
                        self.results_dataframe.loc[
                            test_case_idx, self._output_to_df_heading(output)
                        ] = output[  # type: ignore (looks like Pylance's fault)
                            "reduction_fun"
                        ](
                            fea_results_obj.getPropertyByName(output["output_var"])
                        )

                    self.results_dataframe.loc[
                        test_case_idx, "FEA_Runtime"
                    ] = fea_runtime  # type: ignore (looks like Pylance's fault)

                    # export if requested
                    # TODO: try and join the VTK files together as frames
                    if export_results:

                        (folder, filename) = path.split(self.freecad_document.filename)
                        (fn, _) = path.splitext(filename)

                        if output_folder != "":
                            folder = output_folder

                        n = int(
                            np.ceil(np.log10(len(self.results_dataframe) + 1))
                        )  # number of digits for vtk file

                        self.freecad_document.export_fea_results(
                            filename=path.join(
                                folder, f"FEA_{fn}_{test_case_idx:0{n}}.vtu"
                            ),
                            export_format="vtk",
                        )

                # TODO: may want to add runtime errors to the dataframe also
                # when in dry run
                except RuntimeError as e:
                    self.results_dataframe.loc[
                        test_case_idx, "Msg"
                    ] = str(  # type:ignore (looks like Pylance's fault)
                        e
                    )
                    logger.warning(f"Test case {test_case_idx} exited with error {e}")

            if not quiet_mode:
                pbar.update(1)  # type: ignore (only exists if quiet_mode is false)

        if not quiet_mode:
            pbar.close()  # type: ignore (only exists if quiet_mode is false)

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
            param_headings.append(self._param_to_df_heading(parameter))

        for output in outputs:
            output_headings.append(self._output_to_df_heading(output))

        # Build list of n-param values
        grid = np.meshgrid(*param_vals)
        grid_list = list(x.ravel() for x in grid)

        df = pd.DataFrame()

        for (count, column) in enumerate(param_headings):
            df[column] = grid_list[count]

        for column in output_headings:
            df[column] = 0

        # generic empty data
        df["Msg"] = ""
        df["FEA_Runtime"] = 0
        logger.debug("Empty dataframe created")
        return df

    def plot_fea_results(self):
        """Plots the FEM analysis results using Plotly"""

        logger.debug("Preparing to plot FEA results")
        for output in self.outputs:
            if (len(self.variables)) == 1:
                fig = px.line(
                    self.results_dataframe,
                    x=self._param_to_df_heading(self.variables[0]),
                    y=self._output_to_df_heading(output),
                )
            elif (len(self.variables)) == 2:
                fig = px.line(
                    self.results_dataframe,
                    x=self._param_to_df_heading(self.variables[0]),
                    y=self._output_to_df_heading(output),
                    color=self._param_to_df_heading(self.variables[1]),
                )
            else:
                raise NotImplementedError(
                    "Plotting more than 2 variables not supported yet"
                )

            fig.show()

    def save_fea_results(self, results_filename: str, mode: str = "csv") -> None:
        """Saves the results of the analysis to a file.

        Args:
            results_filename (str): destination file
            mode (str, optional): saving mode. Can be one of:
                "csv" (default): comma separated values, as exported by Pandas
                "json": json file as exported by Pandas
                "pickle": .pickle file containing the Pandas dataframe

        Raises:
            NotImplementedError: if an export mode is not implemented.
        """
        if mode == "csv":
            self.results_dataframe.to_csv(results_filename)
        elif mode == "json":
            self.results_dataframe.to_json(
                results_filename, lines=True, orient="records"
            )
        elif mode == "pickle":
            with open(results_filename, "wb") as f:
                pickle.dump(self.results_dataframe, f)
        else:
            raise NotImplementedError(f"Export mode {mode} not yet implemented")

    def _param_to_df_heading(self, parameter) -> str:
        return f"{parameter['object_name']}.{parameter['constraint_name']}"

    def _output_to_df_heading(self, output) -> str:
        if "column_label" in output.keys():
            col_name = output["column_label"]
        else:
            col_name = output["reduction_fun"].__qualname__

        return f"{col_name}({output['output_var']})"
