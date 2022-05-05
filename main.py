import os, pycdlib, json
from colorama import Fore, Back, Style
"""
Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
Back: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
Style: DIM, NORMAL, BRIGHT, RESET_ALL
"""
from pycdlib import pycdlibexception
from tqdm import tqdm
from math import ceil
from glob import iglob
from os.path import join, basename, splitext, exists, getsize
from wim import WIM

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

    for idx in tqdm(idx_range, f'{Fore.YELLOW}Collecting WIM info{Style.RESET_ALL}', leave=False, colour='blue', dynamic_ncols=True):
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

    for k, v in cfg['sort_criteria'].items():
        if len(v):
            packed_return.append(cfg['sort_criteria'][k].index(eval('x.' + k)))
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


if __name__ == '__main__':

    '''
    Load settings file
    '''
    with open('settings.json') as f:
        cfg = json.load(f)
    if cfg['version'] != 1.0:
        raise NotImplementedError('Unknown version number.')
    
    '''
    Extract install.wim file from iso
    '''
    if cfg['extract_iso']:
        iso = pycdlib.PyCdlib()
        iso_paths = list(iglob(join(cfg['src_dir'], '**/*.iso'), recursive=True))
        if not len(iso_paths):
            print(f'{Fore.RED}Not found ISO files in {cfg["src_dir"]}{Style.RESET_ALL}')
        else:
            for iso_path in tqdm(iso_paths, desc=f'{Fore.YELLOW}Extract {cfg["target_wim"]} file from iso{Style.RESET_ALL}', leave=True, colour='green', dynamic_ncols=True):
                tqdm.write(f'{iso_path}...')
                try:
                    iso.open(iso_path)
                    for dirname, dirlist, filelist in iso.walk(udf_path='/'):
                        for filepath in filelist:
                            if filepath == cfg['target_wim']:
                                os.makedirs(cfg['dst_dir'], exist_ok=True)
                                iso.get_file_from_iso(udf_path='/'.join([dirname, filepath]), local_path=join(cfg['dst_dir'], splitext(basename(iso_path))[0] + splitext(cfg['target_wim'])[1]))
                    iso.close()
                except pycdlibexception.PyCdlibException as e:
                    tqdm.write(f'{Fore.RED}{str(e)}: {iso_path}{Style.RESET_ALL}')

    '''
    Export wim-files to single wim file.
    '''
    wim_paths = list(iglob(join(cfg['dst_dir'], '*' + splitext(cfg['target_wim'])[1])))
    if not len(wim_paths):
        print(f'{Fore.RED}Not found WIM files in {cfg["dst_dir"]}{Style.RESET_ALL}')
    else:
        wim_indexes = []
        for wim_path in tqdm(wim_paths, f'{Fore.YELLOW}Opening WIM file{Style.RESET_ALL}', dynamic_ncols=True, colour='green'):
            wim_indexes += get_wiminfo(wim_path)
        try:
            wim_indexes = sorted(wim_indexes, key=sort_wim)
        except Exception as e:
            tqdm.write(f'{Fore.RED}{str(e)}{Style.RESET_ALL}')
            os.system('pause')
            exit(0)

        print(f'Presorted WIM index sorted by {Fore.YELLOW}sort_criteria{Style.RESET_ALL} is as follows.')
        for idx, wim in enumerate(wim_indexes):
            print(f'{Fore.CYAN if idx % 2 else Fore.GREEN}{Back.BLACK if idx % 2 else Back.BLACK}[{idx+1}]\t{wim}{Style.RESET_ALL}')
        if cfg['enable_pause']: os.system('pause')

        # Remove old WIM
        if cfg['purge_old_wim'] and exists(cfg['dst_wim_path']):
            print(f'{Fore.YELLOW}Remove old wim: {Fore.RED}{cfg["dst_wim_path"]}{Style.RESET_ALL}')
            os.remove(cfg['dst_wim_path'])
        
        # Export using DISM
        for wim in tqdm(wim_indexes, desc=f'{Fore.YELLOW}Exporting WIM{Style.RESET_ALL}', leave=True, colour='green', dynamic_ncols=True):
            tqdm.write(f'\n{wim}\n')
            export(wim.Details_for_image, cfg['dst_wim_path'], range(int(wim.Index), int(wim.Index)+1), check_integrity=False)
        
        # Split WIM to SWM using DISM
        if cfg['split_wim']:
            print(f'{Fore.YELLOW}Split WIM to SWM{Style.RESET_ALL}')
            print(f'Convert {Fore.GREEN}{cfg["dst_wim_path"]}{Fore.WHITE}:{Fore.YELLOW}{getsize(cfg["dst_wim_path"])/1024**3:.02f}GB{Fore.WHITE} to {Style.RESET_ALL}', end='')
            
            wim_size = getsize(cfg['dst_wim_path'])
            for i in range(1, ceil(wim_size/1024**2 / cfg['split_size'])+1):
                wim_print_str = f'Convert {cfg["dst_wim_path"]}:{getsize(cfg["dst_wim_path"])/1024**3:.02f}GB to '
                if i != 1:
                    print(' '*(int(len(wim_print_str))), end='')
                if wim_size/1024**2 >= (cfg['split_size']*i):
                    remain_size = cfg['split_size']
                else:
                    remain_size = int((wim_size/1024**2) % cfg['split_size'])
                print(f'{Fore.CYAN}{splitext(cfg["dst_swm_path"])[0]}{str(i) if i != 1 else ""}{splitext(cfg["dst_swm_path"])[1]}{Fore.WHITE}:{Fore.YELLOW}{remain_size}MB{Style.RESET_ALL}{" (Approx.)" if i == ceil(wim_size/1024**2 / cfg["split_size"]) else ""}')
            if cfg['enable_pause']: os.system('pause')
            if wim_size/1024**2 <= cfg['split_size']:
                print(f'{Fore.RED}`split_size` must be larger than WIM filesize.{Style.RESET_ALL}')
            else:
                wim2swm(cfg['dst_wim_path'], cfg['dst_swm_path'], cfg['split_size'], check_integrity=False)

        print('Converting is finished.')
    os.system('pause')