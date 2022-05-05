import os, pycdlib, configparser
from colorama import Fore, Style
"""
Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
Style: DIM, NORMAL, BRIGHT, RESET_ALL
"""
from pycdlib import pycdlibexception
from tqdm import tqdm
from glob import iglob
from os.path import join, basename, splitext, exists
from wim import WIM

CFG_PATH = './wim_exporter.cfg'

def print_wiminfo(wim_path, idx_range: range=None, category: list=None):
    if idx_range is None:
        idx_range = range(1, get_max_idx(wim_path)+1, 1)
    
    for idx in idx_range:
        cmdline = f'dism /get-wiminfo /wimfile:{wim_path} /index:{idx} /english'
        cmd_output = os.popen(cmdline).readlines()
        for line in cmd_output:
            line = line.strip()
            if category is not None:
                if line.split(':')[0].strip() in category:
                    print(line)
            else:
                print(line)

def get_wiminfo(wim_path, idx_range: range=None):
    wim_indexes = []

    if idx_range is None:
        idx_range = range(1, get_max_idx(wim_path)+1, 1)

    for idx in tqdm(idx_range, 'Collecting WIM info', dynamic_ncols=True, colour='green', leave=False):
        cmdline = f'dism /get-wiminfo /wimfile:{wim_path} /index:{idx} /english'
        cmd_output = os.popen(cmdline).readlines()

        output_dict = {}
        fallback = []
        for line in cmd_output:
            
            # Fallback for multiline list
            if len(line.split(':', 1)) >= 2 and line.split(':', 1)[1] == '\n':
                fallback = line
                continue
            if fallback:
                if line == '\n': # End of list
                    line = fallback[:-1]
                    fallback = []
                else:
                    fallback += line + ','
                    continue
                
            # Print splited strings
            splited = [li.strip() for li in line.split(':', 1)]
            if len(splited) > 1:
                output_dict[splited[0]] = splited[1]
        wim_indexes.append(WIM(output_dict))
    return wim_indexes

def get_max_idx(wim_path):
    cmd_find_max_idx = 'dism /get-wiminfo /wimfile:{} /english'.format(wim_path)
    lines = os.popen(cmd_find_max_idx).readlines()
    for idx in range(len(lines)-1, 0, -1):
        if 'Index' in lines[idx]:
            return int(lines[idx].split(':')[1])

def sort_wim(x):
    from packaging.version import parse
    packed_return = []

    for k, v in sort_criteria.items():
        if len(v):
            packed_return.append(sort_criteria[k].index(eval('x.' + k)))
        else:
            packed_return.append((parse(eval('x.' + k))))

    return packed_return[0] if len(packed_return) == 1 else packed_return[0], *packed_return[1:]

def export(src_path, dst_path, idx_range: range=None, compress: str=None, check_integrity=False):
    if idx_range is None: 
        idx_range = range(1, get_max_idx(src_path)+1)

    for idx in idx_range:
        """
        /Export-Image Usage

        Dism /Export-Image /SourceImageFile:<path_to_image_file> {/SourceIndex:<image_index> | /SourceName:<image_name>} /DestinationImageFile:<path_to_image_file> [/DestinationName:<Name>] [/Compress:{fast|max|none|recovery}] [/Bootable] [/WIMBoot] [/CheckIntegrity]
        """
        os.system(f'dism /export-image /sourceimagefile:{src_path} /sourceindex:{idx} /destinationimagefile:{dst_path}{" /compress:" + compress if compress else ""}{" /checkintegrity" if check_integrity else ""} /english')

def wim2swm(src_path, dst_path, size=4095, check_integrity=False):
    os.system(f'dism /split-image /imagefile:{src_path} /swmfile:{dst_path} /filesize:{size}{" /checkintegrity" if check_integrity else ""}')

def create_cfg(config):
    config['DEFAULT'] = {
        'cfg_version': '1.0',
        'src_dir': 'iso',
        'dest_dir': 'wim',
        'target_filename': 'install',
        'target_ext': 'wim',
    }

    config['Features'] = {
        'extract_wim': '1',
        'export_wim': '1',
    }

    config['Export'] = {
        'export_criteria': '[]',
    }

    with open(CFG_PATH, 'w') as configfile:
        config.write(configfile)
    
    return config


if __name__ == '__main__':

    '''
    Check configuration file
    '''
    config = configparser.ConfigParser()
    if exists(CFG_PATH):
        config.read(CFG_PATH)
    else:
        config = create_cfg(config)
    
    if not config['DEFAULT']['cfg_version'] == '1.0':
        raise NotImplementedError('Unknown version number.')
    
    target_ext = config['DEFAULT']['target_ext']
    target_filename = config['DEFAULT']['target_filename'] + '.' + target_ext
    src_dir = config['DEFAULT']['src_dir']
    dst_dir = config['DEFAULT']['dest_dir']
    sort_criteria = eval(config['Export']['sort_criteria'])
    enable_pause = int(config['DEFAULT']['enable_pause'])
    split_wim = int(config['Features']['split_wim'])
    purge_old_wim = int(config['Export']['purge_old_wim'])
    dest_wim_fname = config['Export']['dest_wim_fname']
    dest_swm_fname = config['Export']['dest_swm_fname']
    split_size = int(config['Export']['split_size'])
    sort_count = -1

    '''
    Uncompress install.wim file from iso
    '''
    if int(config['Features']['uncompress_wim']):
        iso = pycdlib.PyCdlib()
        iso_paths = list(iglob(join(src_dir, '**/*.iso'), recursive=True))

        print('\n\nUncompress install.wim file from iso...')
        for iso_path in tqdm(iso_paths, colour='green', desc='Uncompress install.wim from ISO'):
            tqdm.write(iso_path + '...')
            try:
                iso.open(iso_path)
                for dirname, dirlist, filelist in iso.walk(udf_path='/'):
                    for filepath in filelist:
                        if filepath == target_filename:
                            os.makedirs(dst_dir, exist_ok=True)
                            dst_path = join(dst_dir, splitext(basename(iso_path))[0] + '.' + target_ext)
                            iso.get_file_from_iso(udf_path='/'.join([dirname, filepath]), local_path=dst_path)
                iso.close()
            except pycdlibexception.PyCdlibException as e:
                tqdm.write(f'{Fore.RED}{str(e)}: {iso_path}{Style.RESET_ALL}')

    '''
    Export wim-files to single wim file.
    '''

    if int(config['Features']['export_wim']):
        wim_paths = list(iglob(join(dst_dir, '*.' + target_ext)))
        wim_indexes = []
        for wim_path in tqdm(wim_paths, 'Opening WIM file', dynamic_ncols=True, colour='blue'):
            wim_indexes += get_wiminfo(wim_path)
        try:
            wim_indexes = sorted(wim_indexes, key=sort_wim)
        except Exception as e:
            tqdm.write(f'{Fore.RED}{str(e)}{Style.RESET_ALL}')
            os.system('pause')
            exit(0)

        # Summary sorted list
        print('='*80)
        for idx, wim in enumerate(wim_indexes):
            print(f'{Fore.CYAN if idx % 2 else Fore.GREEN}[{idx+1}]\t{wim}{Style.RESET_ALL}')
        print('='*80, '\nThe sorted results are as above.')
        if enable_pause: os.system('pause')

        # Export using DISM
        for wim in tqdm(wim_indexes, desc='Exporting WIM', colour='green', leave=False, dynamic_ncols=True):
            tqdm.write(f'{Fore.YELLOW}{wim}{Fore.WHITE} from {Fore.CYAN}{wim.Details_for_image}{Fore.WHITE}:{Fore.GREEN}{wim.Index}{Style.RESET_ALL}')
            if purge_old_wim and exists(dest_wim_fname):
                print(f'{Fore.YELLOW}Remove old wim: {Fore.RED}{dest_wim_fname}{Style.RESET_ALL}')
                os.remove(dest_wim_fname)
            export(wim.Details_for_image, dest_wim_fname, range(1, 2), check_integrity=False)
        
        # Split WIM to SWM using DISM
        if split_wim:
            wim2swm(dest_wim_fname, dest_swm_fname, split_size, check_integrity=False)
