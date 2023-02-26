import os
import sys
import glob

from .loghandler import logger


def register_freecad(freecad_path: str = ""):
    """registers the freecad path and femtools in os.PATH

    Args:
        freecad_path (str): path to the local FreeCAD installation. If empty, will
            attempt to automagically find it

    Raises:
        ImportError: if the specified folder does not contain the FreeCAD Python libraries
    """
    supported_platforms = {
        "win32": [
            "C:/Program Files/FreeCAD *",
            os.path.expandvars("%LOCALAPPDATA%/Programs/FreeCAD *"),
        ],
        # "darwin": [] # macOS
        # "linux": [] # linux
    }
    if freecad_path is None or freecad_path == "":
        this_platform = sys.platform
        if this_platform not in supported_platforms.keys():
            try:
                raise ValueError(
                    f"Your platform ({this_platform}) is not yet explicitly supported. "
                    "You can still specify the path to FreeCAD manually using "
                    'parametric(freecad_path="path/to/freecad")'
                )
            except ValueError as e:
                logger.exception(str(e))
                raise
        for possible_path in supported_platforms[this_platform]:
            d = glob.glob(os.path.normpath(possible_path))
            if (len(d)) > 1:
                try:
                    raise ValueError(
                        "You seem to have multiple FreeCAD installations in your system. "
                        "You must specify the path to FreeCAD manually using "
                        'parametric(freecad_path="path/to/freecad")'
                    )
                except ValueError as e:
                    logger.exception(str(e))
                    raise

            if (len(d)) == 0:
                logger.debug(f"FreeCAD not found in {possible_path}")

            if (len(d)) == 1:
                freecad_path = d[0]
                logger.debug(f"Found FreeCAD at {freecad_path}")
                break

    if not freecad_path.endswith("bin"):
        freecad_path = os.path.join(freecad_path, "bin")

    if freecad_path not in sys.path:
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

    return (FreeCAD, femtools, vtkResults)
