import pytest
from FreecadParametricFEA import parametric

FREECAD_PATH = "C:/Program Files/FreeCAD 0.20/bin"
FREECAD_INCORRECT_PATH = "C:/Program Files/Solidworks/bin"

TEST_MODEL = "./examples/hole/shell_test.FCStd"


@pytest.fixture(autouse=True)
def run_before_and_after_tests():
    """Fixture to execute asserts before and after a test is run"""
    # syspathcopy = sys.path

    yield  # this is where the testing happens

    # Teardown : reset sys.path to the original value
    # sys.path = syspathcopy
    # print(sys.path)


def test_incorrect_freecad_path():
    with pytest.raises(ModuleNotFoundError):
        fea = parametric(FREECAD_INCORRECT_PATH)
        fea.set_model(TEST_MODEL)


def test_automagic_freecad_path():
    fea = parametric()
    fea.set_model(TEST_MODEL)
    assert type(fea) is parametric


def test_create_freecad_object():
    # initialise a parametric FEA object
    fea = parametric(freecad_path=FREECAD_PATH)

    # load the FreeCAD model
    fea.set_model(TEST_MODEL)
    assert type(fea) is parametric
