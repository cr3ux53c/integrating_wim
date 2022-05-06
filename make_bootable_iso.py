import json, os, pycdlib
from pycdlib import pycdlibexception
from colorama import Fore, Back, Style
from os.path import join, exists, dirname

def prepare_iso(architecture, dst_dir, copy_pe=False):
    os.makedirs(join(dst_dir, 'sources'), exist_ok=True)

    winpe_path = f'"%PROGRAMFILES(x86)%\\Windows Kits\\10\\Assessment and Deployment Kit\\Windows Preinstallation Environment\\{architecture}\\en-us\\winpe.wim"'
    bios_boot_path = f'"%PROGRAMFILES(x86)%\\Windows Kits\\10\\Assessment and Deployment Kit\\Deployment Tools\\{architecture}\\Oscdimg\\etfsboot.com"'
    efi_boot_path = f'"%PROGRAMFILES(x86)%\\Windows Kits\\10\\Assessment and Deployment Kit\\Deployment Tools\\{architecture}\\Oscdimg\\efisys.bin"'

    if copy_pe:
        os.system(f'copy {winpe_path} {join(dst_dir, "sources", "boot.wim")}')
    os.system(f'copy {bios_boot_path} {join(dst_dir, "etfsboot.com")}')
    os.system(f'copy {efi_boot_path} {join(dst_dir, "efisys.bin")}')

def make_iso(oscdimg_path, iso_dir, dst_iso_path, volume_label=None, boot_platform: list=['bios', 'efi'], bios_boot_path='boot\\etfsboot.com', efi_boot_path='efi\\microsoft\\boot\\efisys.bin', ign_max_lmt=True, optm_duplicate=True, filesystem='UDF1.02', preview_scan=False, timestamp=None, include_hidden=False):
    """
    `oscdimg -m -o -u2 -udfver102 -bootdata:2#p0,e,bc:\winpe_x64\etfsboot.com#pEF,e,bc:\winpe_x64\efisys.bin c:\winpe_x64\ISO c:\winpe_x64\winpeuefi.iso`

    `m`: Ignores the maximum size limit of the image.
    `o`: Optimizes storage by encoding duplicate files only one time.
    `u2`: Produces an ISO image that has only the Universal Disk Format (UDF) file system on it.
    `udfver102`: Specifies the UDF version 1.02 format.
    `bootdata`: Specifies a multiboot image. This image uses an x86-based boot sector as the default image. This sector starts the Etfsboot.com boot code. A secondary EFI boot image starts an EFI boot application.
        `2`: Specifies the number of boot catalog entries.
        `#`: Functions as the separator between root entries to be put into the boot catalog.
        `p0`: Sets the platform ID to 0 for the first, default boot entry for the BIOS.
        `,`: Each option for a boot entry must be delimited by using a comma (,).
        `e`: Specifies the floppy disk emulation in the El Torito catalog.
        `bc:\winpe_x64 \etfsboot.com`: Puts the specified file (Etfsboot.com) in the boot sectors of the disk.
        `#`: Functions as the separator between the first and second boot entries.
        `pEF`: Sets the platform ID to "EF," as defined by the UEFI specification.
        `bc:\winpe_x64\efisys.bin`: Puts the specified file (Efisys.bin) in the boot sector of the disk. Efisys.bin is the binary floppy disk layout of the EFI boot code. This disk image contains the files that are used to start from the EFI firmware in the Efi\boot\x64boot.efi folder.
    `c:\winpe_x64\ISO`: Represents the path of the files for the image.
    `c:\winpe_x64\winpeuefi.iso`: Represents the output image file.
    `q`: Scans the source files only. This option does not create an image.
    `t mm/dd/yyyy,hh:mm:ss`: Specifies the timestamp for all files and directories. Do not use spaces. You can use any delimiter between the items. For example: -t12/31/2000,15:01:00
    `l`: Specifies the volume label. Do not use spaces. For example: -l<volumeLabel>
    `h`: Includes hidden files and directories in the source path of the image.

    https://docs.microsoft.com/en-us/troubleshoot/windows-server/deployment/create-iso-image-for-uefi-platforms
    https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/oscdimg-command-line-options?view=windows-11#use-multi-boot-entries-to-create-a-bootable-image
    """

    bootdata = f'{len(boot_platform)}'
    for i in range(len(boot_platform)):
        bootdata += f'#{"p"+str(i) if boot_platform[i] == "bios" else "pEF"},e,bc:{join(iso_dir, bios_boot_path) if boot_platform[i] == "bios" else join(iso_dir, efi_boot_path)}'
    
    if 'UDF' in filesystem:
        if filesystem == 'UDF1.02':
            fs = '-u2 -udfver102'
        else:
            fs = '-u2'
    else:
        fs = '-u1'

    cmdline = f'{oscdimg_path}{" -m" if ign_max_lmt else ""}{" -o" if optm_duplicate else ""}{" -h" if include_hidden else ""} {fs} -bootdata:{bootdata} {iso_dir} {dst_iso_path}{" -l"+volume_label if volume_label else ""}'
    
    cmd_output = os.popen(cmdline).readlines()
    
    for line in cmd_output:
        print(line)

if __name__ == '__main__':
    '''
    Load settings file
    '''
    try:
        with open('settings.json') as f:
            cfg = json.load(f)
    except Exception as e:
        print(f'{Fore.RED}Failed to access `settings.json` file.{Style.RESET_ALL}')
        os.system('pause')
        exit(1)
    if cfg['version'] != 1.0:
        raise NotImplementedError('Unknown version number.')
    
    '''
    Extract boot files from ISO.
    '''
    if not exists(cfg['src_iso_path']):
        print(f'{Fore.RED}Not found {cfg["src_iso_path"]} file.{Style.RESET_ALL}')
        os.system('pause')
        exit(1)
    iso = pycdlib.PyCdlib()
    iso.open(cfg['src_iso_path'])

    boot_dir = ['bios' if 'bios' in cfg['boot_platform'] else '']
    for dir, dirlist, filelist in iso.walk(udf_path='/'):
        if dir != '/' and ('bios' in cfg['boot_platform'] and '/boot' in dir) or ('efi' in cfg['boot_platform'] and '/efi' in dir):
            for filepath in filelist:
                os.makedirs(join(cfg["iso_dir"], dir[1:]), exist_ok=True)
                iso.get_file_from_iso(udf_path='/'.join([dir, filepath]), local_path=join(cfg["iso_dir"], dir[1:], filepath))
    iso.close()
    
    if not exists(cfg['oscdimg_path']):
        print(f'{Fore.RED}Not found oscdimg file.{Style.RESET_ALL}')
        os.system('pause')
        exit(1)
    os.makedirs(dirname('./' if dirname(cfg['dst_iso_path']) == '' else cfg['dst_iso_path']), exist_ok=True)
    make_iso(cfg['oscdimg_path'], iso_dir=cfg['iso_dir'], dst_iso_path=cfg['dst_iso_path'], volume_label=cfg['volume_label'], boot_platform=cfg['boot_platform'], include_hidden=cfg['include_hidden_files'])
    
    print('Making ISO is finished.')
    os.system('pause')
