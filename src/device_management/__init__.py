import os
import glob
import importlib

# Get the current package name dynamically
package_name = __name__

# Get all Python files in the directory (excluding __init__.py)
modules = glob.glob(os.path.join(os.path.dirname(__file__), "*.py"))
module_names = [
    os.path.basename(f)[:-3] for f in modules if f.endswith(".py") and not f.endswith("__init__.py")
]

# Import all modules dynamically
for module in module_names:
    importlib.import_module(f".{module}", package_name)

# Clean up namespace
del os, glob, importlib, modules, module_names, package_name
