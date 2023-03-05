import pytest
from FreecadParametricFEA import parametric
import pandas as pd
import numpy as np

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
def test_create_freecad_object(initialise_freecad_object):
    # initialise a parametric FEA object
    fea_obj = initialise_freecad_object
    assert type(fea_obj) is parametric


def test_single_parametric(initialise_freecad_object):
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


# TODO:
# - add parameters correctly
# - add non-existent parameters
# - add parameters that break the model, e.g. set something to 0
# - test dry run is full of zeros
# - test custom outputs
# - test function outputs
# -
# - test benchmark problem run against exact values
# - test benchmark problem with errors -- check dataframe
