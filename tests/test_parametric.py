import glob
import os
import pytest
from FreecadParametricFEA import parametric
import pandas as pd
import numpy as np
import pickle

FREECAD_PATH = "C:/Program Files/FreeCAD 0.20/bin"
FREECAD_INCORRECT_PATH = "C:/Program Files/Solidworks/bin"

TEST_MODEL = "./examples/hole/shell_test.FCStd"


@pytest.fixture(scope="module")
def initialise_freecad_object():
    fea = parametric(freecad_path=FREECAD_PATH)

    # load the FreeCAD model
    fea.set_model(TEST_MODEL)
    return fea


# test initialisation
def test_create_freecad_object(initialise_freecad_object: parametric):
    # initialise a parametric FEA object
    fea_obj = initialise_freecad_object
    assert type(fea_obj) is parametric


def test_single_parametric(initialise_freecad_object: parametric):
    fea_obj = initialise_freecad_object
    fea_obj.set_variables(
        [
            {
                "object_name": "Sketch",  # the object where to find the constraint
                "constraint_name": "HoleDiam",  # the constraint name that you assigned
                "constraint_values": np.linspace(
                    10, 30, 3
                ),  # the values you want to check
            },
        ]
    )

    empty_df = fea_obj.run_parametric(dry_run=True)
    assert type(empty_df) is pd.DataFrame
    assert len(empty_df) == 3

    results = fea_obj.run_parametric()
    assert len(results) == 3
    assert results["amax(vonMises)"].max() > 1.9
    assert results["amax(vonMises)"].max() < 2.1


def test_parametric_material(initialise_freecad_object: parametric):
    fea_obj = initialise_freecad_object

    fea_obj.set_variables(
        [
            {
                "object_name": "Sketch",  # the object where to find the constraint
                "constraint_name": "HoleDiam",  # the constraint name that you assigned
                "constraint_values": np.linspace(
                    10, 30, 2
                ),  # the values you want to check
            },
            {
                "object_name": "MaterialSolid",  # the object where to find the constraint
                "constraint_name": "Material",  # the constraint name that you assigned
                "constraint_values": ["Aluminium-Generic", "Steel-Generic"],
            },
        ]
    )
    results = fea_obj.run_parametric()
    assert len(results) == 4
    assert results["amax(vonMises)"].max() > 1.9
    assert results["amax(vonMises)"].max() < 2.1
    assert results["amax(DisplacementLengths)"].max() < 0.01
    assert results["amax(DisplacementLengths)"].min() > 0.0001


def test_parametric_3params(initialise_freecad_object: parametric):
    fea_obj = initialise_freecad_object

    fea_obj.set_variables(
        [
            {
                "object_name": "Sketch",  # the object where to find the constraint
                "constraint_name": "HoleDiam",  # the constraint name that you assigned
                "constraint_values": np.linspace(
                    10, 30, 2
                ),  # the values you want to check
            },
            {
                "object_name": "MaterialSolid",  # the object where to find the constraint
                "constraint_name": "Material",  # the constraint name that you assigned
                "constraint_values": ["Aluminium-Generic", "Steel-Generic"],
            },
            {
                "object_name": "ShellThickness",
                "constraint_name": "Thickness",
                "constraint_values": np.linspace(10, 20, 3),
            },
        ]
    )

    fea_obj.setup_fea(fea_results_name="CCX_Results", solver_name="SolverCcxTools")

    results = fea_obj.run_parametric(dry_run=True)
    assert len(results) == 12


def test_parametric_generic_obj(initialise_freecad_object: parametric):
    fea_obj = initialise_freecad_object

    fea_obj.set_variables(
        [
            {
                "object_name": "ShellThickness",
                "constraint_name": "Thickness",
                "constraint_values": np.linspace(10, 20, 2),
            },
        ]
    )

    results = fea_obj.run_parametric()
    assert len(results) == 2
    assert results["amax(vonMises)"].min() < 1
    assert results["amax(vonMises)"].min() > 0.9


def test_custom_outputs(initialise_freecad_object: parametric):
    fea_obj = initialise_freecad_object

    fea_obj.set_variables(
        [
            {
                "object_name": "ShellThickness",
                "constraint_name": "Thickness",
                "constraint_values": np.linspace(10, 20, 2),
            },
        ]
    )

    fea_obj.set_outputs(
        [
            {
                "output_var": "vonMises",
                "reduction_fun": np.median,
            },
            {
                "output_var": "vonMises",
                "reduction_fun": lambda v: np.percentile(v, 95),
                "column_label": "95th percentile",
            },
        ]
    )

    results = fea_obj.run_parametric()
    assert len(results) == 2
    assert results["median(vonMises)"].max() < 0.3
    assert results["median(vonMises)"].max() > 0.2
    assert results["95th percentile(vonMises)"].max() < 0.9
    assert results["95th percentile(vonMises)"].max() > 0.7


def test_export_results(initialise_freecad_object: parametric, tmp_path):
    fea_obj = initialise_freecad_object

    fea_obj.set_variables(
        [
            {
                "object_name": "ShellThickness",
                "constraint_name": "Thickness",
                "constraint_values": np.linspace(10, 20, 2),
            },
        ]
    )

    results = fea_obj.run_parametric(export_results=True, output_folder=tmp_path)

    assert len(results) == len(glob.glob(os.path.join(tmp_path, "*.vtu")))

    csv_file = os.path.join(tmp_path, "test.csv")
    fea_obj.save_fea_results(results_filename=csv_file, mode="csv")
    assert len(pd.read_csv(csv_file)) == len(results)

    json_file = os.path.join(tmp_path, "test.json")
    fea_obj.save_fea_results(results_filename=json_file, mode="json")
    assert len(pd.read_json(json_file, lines=True)) == len(results)

    pickle_file = os.path.join(tmp_path, "test.pickle")
    fea_obj.save_fea_results(results_filename=pickle_file, mode="pickle")
    with open(pickle_file, "rb") as pf:
        df = pickle.load(pf)

    assert df.equals(results)

    with pytest.raises(NotImplementedError):
        fea_obj.save_fea_results(results_filename=csv_file, mode="toml")


# TODO:
# - test dry run is full of zeros

# - test benchmark problem run against exact values
# - test benchmark problem with errors -- check dataframe
