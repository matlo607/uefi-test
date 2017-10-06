#include <efi.h>
#include <efilib.h>

/* Application entrypoint must be set to 'efi_main'
 * for gnu-efi crt0 compatibility.
 */
EFI_STATUS
    EFIAPI
efi_main(EFI_HANDLE ImageHandle, EFI_SYSTEM_TABLE *SystemTable)
{
#if defined(_GNU_EFI)
    InitializeLib(ImageHandle, SystemTable);
#endif

    /*
     * In addition to the standard %-based flags, Print() supports the following:
     *   %N       Set output attribute to normal
     *   %H       Set output attribute to highlight
     *   %E       Set output attribute to error
     *   %r       Human readable version of a status code
     */
    Print(L"\n%H*** UEFI:Test ***%N\n\n");
    Print(L"Hello world !\n\n");
    Print(L"test status: %H<OK>%N\n\n");

    //Print(L"%EPress any key to exit.%N\n");
    //SystemTable->ConIn->Reset(SystemTable->ConIn, FALSE);
    //UINTN Event;
    //SystemTable->BootServices->WaitForEvent(1, &SystemTable->ConIn->WaitForKey, &Event);

#if defined(_DEBUG)
    // If running in debug mode, use the EFI shut down call to close QEMU
    SystemTable->RuntimeServices->ResetSystem(EfiResetShutdown, EFI_SUCCESS, 0, NULL);
#endif

    return EFI_SUCCESS;
}
