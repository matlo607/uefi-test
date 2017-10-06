echo -on

fs0:
ls
hello-world.efi
if %lasterror% == %SHELL_SUCCESS%
    echo "PASSED"
