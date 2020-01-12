# ASUC Elections Tabulator
The Elections Tabulator for ASUC Elections.

## Using the Tabulator
A copy of ElectionsApp.app is included in this repo. Simply download it and double-click to open the program. As a demo, you can load candidates2020Test.txt and 2020ElectionResultsTest.csv.

## Developing
This project currently utilizes PyInstaller to create a simple Mac app/bundle. Simply install PyInstaller by running `pip install pyinstaller` then create the bundle by running `pyinstaller ElectionApp.py --onefile --windowed`. The bundle can be found in the dist/ directory.

PyInstaller will create a file named ElectionApp.spec in addition to the bundle. To create new versions of the bundle based on modifications of ElectionApp.spec, run `pyinstaller ElectionApp.spec`.

### Resolution Fix
One final touch is required to ensure that the Mac app will display properly on the Mac's retina display. In ElectionApp.spec, modify the BUNDLE arguments to add the last argument as below.
```
app = BUNDLE(exe,
                 name='ElectionApp.app',
                 icon='asuc.ico',
                 bundle_identifier=None,
                 info_plist={
                    'NSPrincipalClass': 'NSApplication'
                 }
            )
```
Now run `pyinstaller ElectionApp.spec` to see the change reflected.
