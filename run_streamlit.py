#!/usr/bin/env python3
"""
Run Streamlit in-process after removing problematic PyTorch proxy modules from sys.modules.
This is a pragmatic workaround for the RuntimeError seen when Streamlit's local_sources_watcher
tries to access attributes on torch proxy objects (e.g. when the torch package exposes
custom Python wrappers that raise on attribute access).

Usage:
    python run_streamlit.py

This script attempts to remove 'torch._classes' entries and related attributes from
sys.modules before invoking Streamlit's CLI programmatically.
"""
import sys
import os

# Remove suspect torch proxy modules from sys.modules before Streamlit watches modules
for k in list(sys.modules.keys()):
    if k.startswith('torch._classes') or k == 'torch._classes':
        try:
            del sys.modules[k]
        except Exception:
            pass

# If torch module is loaded, try to remove its _classes attribute if present
try:
    if 'torch' in sys.modules:
        tmod = sys.modules['torch']
        if hasattr(tmod, '_classes'):
            try:
                delattr(tmod, '_classes')
            except Exception:
                pass
except Exception:
    pass

# Launch Streamlit programmatically in the current process so the watcher sees the
# cleaned sys.modules state.
try:
    from streamlit.web import cli as stcli
except Exception:
    # Fall back for older Streamlit packaging
    from streamlit import cli as stcli

# Build argv and call Streamlit's main (default to eval_final.py)
sys.argv = ["streamlit", "run", "eval_final.py"]
# Optionally add extra flags, or pass a filename as the first arg to this script
sys.exit(stcli.main())
