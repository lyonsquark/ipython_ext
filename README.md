ipython_ext
===========

My ipython extensions

## ipythonRoot

Supplies two cell magics, `%%rootprint` and `%%rootplot`, for making it easier to use [pyroot](http://root.cern.ch/drupal/content/pyroot) in an ipython notebook. pyroot is the python wrapper around CERN's [ROOT](http://root.cern.ch) data analysis system. 

Many Root functions and commands send their output directly to `stdout`, so such output will not appear in the notebook cell. If you use `%%rootprint` in the cell, then output to `stdout` will be captured and will appear in the cell output.

`%%rootplot` will display a resulting ROOT plot in the cell output.
