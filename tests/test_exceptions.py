import pytest
from FreecadParametricFEA import parametric
import numpy as np

FREECAD_PATH = "C:/Program Files/FreeCAD 0.20/bin"
FREECAD_INCORRECT_PATH = "C:/Program Files/Solidworks/bin"

TEST_MODEL = "./examples/hole/shell_test.FCStd"


# TODO: this fixture should be shared
@pytest.fixture(scope="module")
def initialise_freecad_object():
    fea = parametric(freecad_path=FREECAD_PATH)

    # load the FreeCAD model
    fea.set_model(TEST_MODEL)
    return fea


def test_missing_object(initialise_freecad_object: parametric):
    fea_obj = initialise_freecad_object

    with pytest.raises(KeyError):
        fea_obj.set_variables(
            [
                {
                    "object_name": "nonexisting_object",
                    "constraint_name": "HoleDiam",
                    "constraint_values": (1, 2),
                },
            ]
        )
        fea_obj.run_parametric(dry_run=True)


def test_missing_constraint(initialise_freecad_object: parametric):  #
    fea_obj = initialise_freecad_object

    with pytest.raises((NameError, IndexError)):
        fea_obj.set_variables(
            [
                {
                    "object_name": "Sketch",
                    "constraint_name": "nonexisting_constraint",
                    "constraint_values": (1, 2),
                },
            ]
        )
        fea_obj.run_parametric(dry_run=True)


def test_breaking_model(initialise_freecad_object: parametric):
    fea_obj = initialise_freecad_object

    fea_obj.set_variables(
        [
            {
                "object_name": "Sketch",
                "constraint_name": "HoleDiam",
                "constraint_values": np.linspace(0, 1, 2),
            },
        ]
    )

    results = fea_obj.run_parametric()

    assert len(results) == 2
    assert results.loc[0, "Msg"] != ""
    assert results.loc[1, "Msg"] == ""
