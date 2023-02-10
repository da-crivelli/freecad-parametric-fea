import pytest
from FreecadParametricFEA import parametric as pfea

FREECAD_PATH = "C:/Program Files/FreeCAD 0.20/bin"
FREECAD_INCORRECT_PATH = "C:/Program Files/Solidworks/bin"

TEST_MODEL = "./examples/hole/shell_test.FCStd"

@pytest.fixture(scope="module")
def initialise_freecad_object():
    fea = pfea(freecad_path=FREECAD_PATH)

    # load the FreeCAD model
    fea.set_model(TEST_MODEL)
    return fea

# test initialisation
def test_create_freecad_object(initialise_freecad_object):
    # initialise a parametric FEA object
    fea_obj = initialise_freecad_object
    assert type(fea_obj) is pfea

def test_incorrect_freecad_path():
    with pytest.raises(ModuleNotFoundError):
        pfea(FREECAD_INCORRECT_PATH)

def test_automagic_freecad_path():
    fea = pfea()
    assert type(fea) is pfea

# TODO: 
# - add parameters correctly
# - add non-existent parameters
# - add parameters that break the model, e.g. set something to 0
# 
# - test dry run is full of zeros
# - test benchmark problem run against exact values
# - test benchmark problem with errors -- check dataframe