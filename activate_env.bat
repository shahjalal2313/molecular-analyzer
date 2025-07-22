@echo off
echo Activating Molecular Analyzer Environment...
call molecular-analyzer-env\Scripts\activate.bat
echo Environment activated! You can now use:
echo   - python (with all dependencies)
echo   - jupyter notebook
echo   - streamlit run app/streamlit_app.py
echo.
cmd /k