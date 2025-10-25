rd /s /q  dist
rd /s /q  build
rd /s /q  hyload.egg-info

python -m build --wheel && twine upload dist/*.whl

pause