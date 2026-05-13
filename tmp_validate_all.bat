@echo off
cd /d C:\work\HermesCOBOL
echo Starting validate_byte_layout.py for all programs > tmp_validate_byte_layout_out.txt
echo =========================================================== >> tmp_validate_byte_layout_out.txt
echo.

for %%f in (data\byte_layouts\*.json) do (
    echo Processing: %%~nf.json
    python scripts\carddemo_imported\validate_byte_layout.py --byte-layout "%%f" --out "tmp_validate_%%~nf.json" >> tmp_validate_byte_layout_out.txt 2>&1
    echo --- >> tmp_validate_byte_layout_out.txt
    echo.
)

echo.
echo =========================================================== >> tmp_validate_byte_layout_out.txt
echo Summary: >> tmp_validate_byte_layout_out.txt
findstr /C:"PASS" /C:"FAIL" tmp_validate_byte_layout_out.txt
echo.
echo Done.