import os, pycdlib, ast
from pycdlib import pycdlibexception
import configparser
from tqdm import tqdm
from glob import iglob
from os.path import join, basename, splitext, exists

CFG_PATH = './wim_exporter.cfg'

def get_max_idx(src):
    cmd_find_max_idx = 'dism /get-wiminfo /wimfile:{} /english'.format(src)
    lines = os.popen(cmd_find_max_idx).readlines()
    for idx in range(len(lines)-1, 0, -1):
        if 'Index' in lines[idx]:
            return int(lines[idx].split(':')[1])

def desc(src, idx=None, category: list=None):
    cmd = 'dism /get-wiminfo /wimfile:{}{} /english'.format(src, ' /index:{}'.format(idx) if idx is not None else '')
    if category is not None:
        if idx is not None:
            cnsl_redir = os.popen(cmd)
            for li in cnsl_redir.readlines():
                if li.split(':')[0] in ' '.join(category):
                    print(li, end='')
        else:
            for idx in range(1, get_max_idx(src)+1):
                cmd = 'dism /get-wiminfo /wimfile:{} /index:{} /english'.format(src, idx)
                detail = os.popen(cmd).readlines()
                for det_idx in range(len(detail)):
                    cri = detail[det_idx].replace('\n', '').replace('\t', '')
                    if len(cri) > 0 and cri.split(':')[0].replace(' ', '') in ' '.join(category):
                        if cri.split(':')[0].replace(' ', '') == 'Languages':
                            print(cri + ' ' + detail[det_idx+1].replace('\t', ''))
                        else:
                            print(cri)
    else:
        return os.system(cmd)

def export(src, dst, idx=None):
    if idx is not None:
        os.system('dism /export-image /sourceimagefile:{} /sourceindex:{} /destinationimagefile:{} /english'.format(src, idx, dst))
    else:
        for idx in range(1, get_max_idx(src)+1):
            os.system('dism /export-image /sourceimagefile:{} /sourceindex:{} /destinationimagefile:{} /english'.format(src, idx, dst))


# def sort(src, dst, criteria):
#     criteria.reverse()
#     max_idx = get_max_idx(src)
#     init_sorted = [i for i in range(1, max_idx+1)]
    
#     details = []
#     for i in init_sorted:
#         cmd = 'dism /get-wiminfo /wimfile:{} /index:{} /english'.format(src, i)
#         details.append(os.popen(cmd).readlines())
    
#     ret = srt(details, criteria)

# def srt(details, criteria):
#     if len(criteria) > 1:
#         srt(details, criteria[1:])
#     criterion = criteria[0]
    
#     sorted_details = []
#     for detail in details:
#         for det in detail:
#             if criterion == det.split('')[0]:
#                 value = det.split('')[1].replace('\n', '').replace('\t', '')
#                 sorted_details.append(detail)
#                 break
#     return sorted_details

def wim2swm(src, dst, size=4095, chk_integrity=False):
    os.system('dism /split-image /imagefile:{} /swmfile:{} /filesize:{}{}'.format(src, dst, size, ' /checkintegrity' if chk_integrity else ''))

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
    
    target_filename = config['DEFAULT']['target_filename'] + '.' + config['DEFAULT']['target_ext']
    

    '''
    Extract install.wim file from iso
    '''
    if int(config['Features']['extract_wim']):
        iso = pycdlib.PyCdlib()
        iso_paths = list(iglob(join(config['DEFAULT']['src_dir'], '**/*.iso'), recursive=True))

        print('Extract install.wim file from iso...\n' + '='*80 + '\n')
        for iso_path in tqdm(iso_paths, colour='green', desc='Extract install.wim from ISO'):
            try:
                iso.open(iso_path)
                for dirname, dirlist, filelist in iso.walk(udf_path='/'):
                    for filepath in filelist:
                        if filepath == target_filename:
                            os.makedirs(config['DEFAULT']['dest_dir'], exist_ok=True)
                            dst_path = join(config['DEFAULT']['dest_dir'], splitext(basename(iso_path))[0] + '.' + config['DEFAULT']['target_ext'])
                            iso.get_file_from_iso(udf_path='/'.join([dirname, filepath]), local_path=dst_path)
                iso.close()
            except pycdlibexception.PyCdlibException as e:
                tqdm.write(str(e) + f': {iso_path}')

    '''
    Export wim-files to single wim file.
    '''
    if int(config['Features']['export_wim']):
        criteria = ast.literal_eval(config['Export']['export_criteria'])
        pass


    # wim2swm('all.wim', 'install.swm', chk_integrity=True)

    # for i in range(1, 50):
        # desc("allinone.wim", idx=i)
    # desc("allinone.wim", idx=1)
    # desc("allinone.wim", category=['Index', 'Name', 'Description', 'Architecture', 'Languages', 'Installation'])
    # desc("x86.wim", category=['Index', 'Name', 'Description', 'Architecture', 'Languages', 'Installation'])
    # desc("x64.wim", category=['Index', 'Name', 'Description', 'Architecture', 'Languages', 'Installation'])
    # desc("ko.wim", category=['Index', 'Name', 'Description', 'Architecture', 'Languages', 'Installation'])
    
    # for i in [38,44,39,45,40,46,41,47,42,48,43,49,50,51,52,53,54,55,56,57,58]:
        # export('allinone.wim', i, 'ko.wim')
    # for i in range(31, 38):
        # export('allinone.wim', i, 'en.wim')
    
    # export('en.wim', i, 'en.wim')
    # export('ko.wim', i, 'ko.wim')
    # export('en.wim', 'all.wim')
    # export('ko.wim', 'all.wim')

    # desc("all.wim", category=['Index', 'Name', 'Description', 'Architecture', 'Languages', 'Installation'])
    # desc("all.wim", category=['Name'])

    # desc("en.wim", category=['Index', 'Name', 'Architecture'])
    # desc("en.wim", category=[ 'Architecture'])

    # for i in range(1, 59):
    #     if i in [1,2,3,4,5,6,7,8,9,10,11,12,13,27,28,38,39,40,41,42,43,50]:
    #         export('allinone.wim', i, 'x86.wim')
    #     else:
    #         export('allinone.wim', i, 'x64.wim')
    
    # os.system('dism /get-imageinfo /imagefile:allinone.wim')
    # desc("C:\\Users\\Administrator\\Desktop\\install3-ko.wim")
    # for i in range(1, 59):
        # filts = desc("allinone.wim", i, ['Index', 'Name', 'Description', 'Architecture', 'Modified', 'Languages'])
    
    # for idx in range(1, 4):
    #     export("C:\\Users\\Administrator\\Desktop\\home-x86.wim", idx, "C:\\Users\\Administrator\\Desktop\\install.wim")
    # for idx in range(1, 11):
    #     # if idx == 6: continue
    #     export("N:\\sources\\install.wim", idx, "C:\\Users\\Administrator\\Desktop\\install.wim")
    # for idx in range(1, 4):
    #     export("C:\\Users\\Administrator\\Desktop\\home-x64.wim", idx, "C:\\Users\\Administrator\\Desktop\\install.wim")
    # for idx in range(1, 11):
    #     export("O:\\sources\\install.wim", idx, "C:\\Users\\Administrator\\Desktop\\install.wim")
    # for idx in range(1, 12):
    #     export("C:\\Users\\Administrator\\Desktop\\install3.wim", idx, "C:\\Users\\Administrator\\Desktop\\install.wim")
    
    
    # export("P:\\sources\\install.wim", 1, "C:\\Users\\Administrator\\Desktop\\install.wim")
    # for idx in range(1, 7):
    #     export("R:\\sources\\install.wim", idx, "C:\\Users\\Administrator\\Desktop\\install.wim")
    # export("Q:\\sources\\install.wim", 1, "C:\\Users\\Administrator\\Desktop\\install.wim")
    # for idx in range(1, 7):
    #     export("S:\\sources\\install.wim", idx, "C:\\Users\\Administrator\\Desktop\\install.wim")
    
    # for idx in range(1, 10):
    #     export("C:\\Users\\Administrator\\Desktop\\install3-ko.wim", idx, "C:\\Users\\Administrator\\Desktop\\install.wim")
    
    # desc("C:\\Users\\Administrator\\Desktop\\install.wim")
    # desc("E:\os\AllInOne\install.wim")