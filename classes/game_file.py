from classes.game import Game, getWosSubfolder, filepath_regex
from classes.game_release import GameRelease
import requests
import os
import zipfile
import hashlib
from settings import *
import re

TOSEC_REGEX = re.compile('[\(\[](.*?)[\)\]]|\.zip|'+'|'.join(['\.'+x for x in GAME_EXTENSIONS]))

def putPrefixToEnd(game_name):
    for prefix in GAME_PREFIXES:
        if game_name.startswith(prefix + ' '):
            game_name = ' '.join(game_name.split(' ')[1:]) + ', ' + prefix
            return game_name
    return game_name

class GameFile(object):

    game = None
    release = None
    release_seq = 0
    wos_name = ''
    wos_zipped_name = ''
    tosec_path = ''
    machine_type = '48K'
    language = ''
    part = 0
    side = 0
    mod_flags = ''
    # zipped = False
    format = ''
    size = 0
    size_zipped = 0
    md5 = ''
    md5_zipped = ''
    crc32 = ''
    sha1 = ''
    wos_path = ''
    src=''
    dest=''
    alt_dest=''

    def __init__(self, path='', size=0, game=None, release=None):
        if not path:
            return
        filename = os.path.basename(path)
        # if filename.endswith('.zip'):
        #     filename = filename[:-4]
        self.path = path
        self.setSize(size)
        self.format = self.getFormat(path)
        self.game = game
        self.release = release
        self.setMachineType(filename)
        if game:
            if filename.endswith('.zip'):
                self.wos_zipped_name = filename
                self.wos_path = path
            else:
                self.wos_name = filename
        else:
            self.getGameFromFileName()
        if type(size)==str:
            size = int(size.replace(',',''))

    def __repr__(self):
        return '<GameFile: '+self.path+' md5:'+self.md5+'>'

    def __eq__(self, other):
        if self.wos_path and \
            self.wos_path == other.wos_path and \
            self.size == other.size and \
            self.format == other.format:
            return True
        if self.md5 and self.md5==other.md5:
            return True
        return False

    def countAlternateDumpsIn(self, collection=[]):
        count = 0
        for other_file in collection:
            # if self.game.wos_id and \
            #     self.game.wos_id!=other_file.game.wos_id:
            #     continue
            # elif self.getGameName()!=other_file.getGameName():
            #     continue
            if self.dest:
                if self.dest == other_file.dest:
                    count += 1
                continue
            elif not self.game and \
                self.getGameName()==other_file.getGameName():
                print(self.getGameName(),'==',other_file.getGameName())
                print(self, other_file)
                count += 1
            elif self.game.wos_id==other_file.game.wos_id and \
                self.getYear()==other_file.getYear() and \
                self.getPublisher()==other_file.getPublisher() and \
                self.getReleaseSeq() == other_file.getReleaseSeq() and \
                self.machine_type == other_file.machine_type and \
                self.side == other_file.side and \
                self.part == other_file.part and \
                self.language == other_file.language and \
                self.mod_flags == other_file.mod_flags:
                count += 1
        return count

    def addAlternateModFlag(self, copies_count):
        if not copies_count:
            return
        dest = os.path.splitext(self.dest)
        if copies_count == 1:
            alt_mod_flag = '[a]'
        else:
            alt_mod_flag = '[a' + str(copies_count) + ']'
        self.alt_dest = dest[0]+alt_mod_flag+dest[1]

    def isAlternate(self):
        if self.alt_dest:
            return True
        else:
            return False

    def getDestination(self):
        return self.alt_dest if self.alt_dest else self.dest

    def copy(self):
        new = GameFile(self.path, self.size, self.game)
        return new

    def getFileName(self):
        return self.tosec_path if self.tosec_path else os.path.basename(self.path)

    def getGameFromFileName(self):
        filename = os.path.basename(self.path).replace('(demo)', '')
        matches = re.findall(TOSEC_REGEX, filename)
        game_name = re.sub(TOSEC_REGEX, '', filename).strip()
        if not self.game:
            self.game = Game(game_name)
        else:
            self.game.name = game_name
        if len(matches)==0:
            return
        self.game.setYear(matches[0])
        if len(matches)==1:
            return
        self.game.setPublisher(matches[1])
        for each in matches[2:]:
            if len(each)==2 and each.isalpha():
                self.setLanguage(each)
            elif 'Side' in each:
                self.setSide(each)
            elif 'Part' in each or 'Disk' in each:
                self.setPart(each)
            elif each and each[0].lower() in ['m', 'h', 'c', 'f']:
                self.mod_flags += '[%s]' % each

    def setMachineType(self, filename):
        if not filename:
            return
        if '128' in filename and '48' in filename:
            self.machine_type = '48/128K'
        elif '128' in filename:
            self.machine_type = '128K'
        elif '48' in filename:
            self.machine_type = '48K'
        elif '16' in filename:
            self.machine_type = '16K'

    def getMachineType(self):
        if self.machine_type:
            return self.machine_type
        else:
            return self.game.machine_type

    def setLanguage(self, language):
        self.language = language.lower()

    def setPart(self, part):
        part = part.split(' ')
        for i, word in enumerate(part):
            if (word in ['Part', 'Disk']) and \
                len(part)>i and \
                part[i+1][0].isdigit():
                self.part = int(part[i+1][0])


    def getLanguage(self):
        if self.language:
            return self.language
        elif self.release:
            return self.release.getLanguage()
        else:
            return self.game.getLanguage()

    def getFullTOSECName(self, zipped=False):
        if self.tosec_path:
            return self.tosec_path
        basename = self.getGameName()
        params = []
        params.append('('+self.getYear()+')')
        params.append('('+self.getPublisher()+')')
        if self.language:
            params.append('('+self.language+')')
        if self.side:
            params.append('(Side '+self.getSide()+')')
        elif self.part:
            params.append('(Part '+str(self.part)+' of '+str(self.game.parts)+')')
        if self.machine_type and self.machine_type!='48K':
            params.append('[%s]' % self.machine_type)
        if self.mod_flags:
            params.append(self.mod_flags)
        # if self.tosec_info:
        #     params.append(self.tosec_info)
        ext = 'zip' if zipped else self.format
        tosec_name = basename+' '+''.join(params)+'.'+ext
        tosec_name = filepath_regex.sub('', tosec_name.replace('/', '-').replace(':', ' -')).strip()
        return tosec_name

    def setSide(self, side):
        if 'Side A' in side or 'Side 1' in side:
            self.side = SIDE_A
        elif 'Side B' in side or 'Side 2' in side:
            self.side = SIDE_B

    def getSide(self):
        if self.side == SIDE_A:
            return 'A'
        elif self.side == SIDE_B:
            return 'B'

    def setSize(self, size=0, zipped=False):
        if type(size)==str:
            size = int(size.replace(',',''))
        if zipped:
            self.size_zipped = size
        else:
            self.size = size

    def getSize(self):
        return '{:,}'.format(self.size)

    def getFormat(self, path):
        filename = os.path.basename(path)
        format = filename.replace('.zip','').split('.')[-1].lower()
        if format in GAME_EXTENSIONS:
            return format
        else:
            format = os.path.split(os.path.dirname(path))[-1].replace('[', '').replace(']', '').lower()
            if format in GAME_EXTENSIONS:
                return format

    def getMD5(self, zipped=False):
        if zipped and self.md5_zipped:
            return self.md5_zipped
        elif not zipped and self.md5:
            return self.md5
        local_path = self.getLocalPath(zipped=zipped)
        if os.path.exists(local_path):
            file_handle = self.getFileHandle(local_path, zipped=zipped)
            if not file_handle:
                print(self, 'has no valid file handle!')
                return ''
            md5 = hashlib.md5(file_handle).hexdigest()
            if zipped:
                self.md5_zipped = md5
            else:
                self.md5 = md5
            return md5

    def getCRC32(self):
        return self.crc32

    def getSHA1(self):
        if self.sha1:
            return self.sha1
        local_path = self.getLocalPath()
        if os.path.exists(local_path):
            file_handle = self.getFileHandle(local_path)
            if not file_handle:
                print(self, 'has no valid file handle!')
                return ''
            self.sha1 = hashlib.sha1(file_handle).hexdigest()
            return self.sha1

    def getFileHandle(self, local_path, zipped=False):
        if local_path.endswith('.zip') and not zipped:
            with zipfile.ZipFile(local_path, 'r') as zf:
                for zfname in zf.namelist():
                    zfname_ext = zfname.split('.')[-1].lower()
                    if zfname_ext != self.format and zfname_ext in GAME_EXTENSIONS:
                        if self.format:
                            print('FORMAT MISMATCH:', self, zfname)
                        self.format = zfname_ext
                    if zfname_ext == self.format:
                        if not self.size:
                            self.setSize(zf.getinfo(zfname).file_size)
                        if not self.crc32:
                            self.crc32 = hex(zf.getinfo(zfname).CRC)[2:]
                        return zf.read(zfname)
        else:
            return open(local_path, 'rb').read()

    def getOutputPathFormatKwargs(self):
        game_name = self.getGameName()
        return {
            'Genre':self.game.getGenre(),
            'Year':self.getYear(),
            'Letter':getWosSubfolder(game_name),
            'MachineType':self.getMachineType(),
            'Publisher':self.getPublisher(),
            'NumberOfPlayers':str(self.game.number_of_players)+'P',
            'GameName':self.release.aliases[0] if self.release else self.game.name,
            'Language':self.getLanguage()
        }

    def getGameName(self):
        game_name = self.release.aliases[0] if self.release else self.game.name
        game_name = putPrefixToEnd(game_name)
        return game_name

    def getYear(self):
        if self.release:
            return self.release.getYear()
        else:
            return self.game.getYear()

    def getPublisher(self):
        if self.release:
            return self.release.getPublisher()
        else:
            return self.game.getPublisher()

    def getReleaseSeq(self):
        return self.release.release_seq if self.release else 0

    def getSortIndex(self, preferred_formats_list=GAME_EXTENSIONS):
        try:
            return preferred_formats_list.index(self.format)
        except IndexError:
            return 99

    def getWosPath(self, wos_mirror_root = WOS_SITE_ROOT):
        return wos_mirror_root+self.path
        # return self.wos_path
        # wos_folder = WOS_TRDOS_GAME_FILES_DIRECTORY if self.format=='trd' \
        #     else WOS_GAME_FILES_DIRECTORY
        # return '/'.join((wos_mirror_root,
        #                  wos_folder,
        #         getWosSubfolder(self.wos_name),
        #         self.wos_name+'.zip'))
        # subfolder = getWosSubfolder(self.wos_name[0])
        # wos_path = os.path.join(WOS_GAME_FILES_DIRECTORY, subfolder, self.wos_name+'.zip')
        # return wos_path

    def getLocalPath(self, zipped=False):
        if self.wos_path:
            local_path = self.getWosPath(LOCAL_FTP_ROOT)
            if os.path.exists(local_path):
                return local_path
        return self.path
        # if zipped and self.wos_zipped_name:
        #     subfolder = getWosSubfolder(self.wos_zipped_name)
        #     local_path = os.path.join(LOCAL_GAME_FILES_DIRECTORY, subfolder, self.wos_zipped_name)
        #     return local_path
        # elif not zipped and self.wos_name:
        #     subfolder = getWosSubfolder(self.wos_name)
        #     local_path = os.path.join(LOCAL_GAME_FILES_DIRECTORY, subfolder, self.wos_name)
        #     return local_path
        # else:
        #     return self.path

    def getLocalFile(self):
        return open(self.getLocalPath())

    # def getRemoteFile(self):
    #     wos_path = self.getWosPath()
    #     return wos_path

    # def unzip(self):
    #     try:
    #         zf = self.getLocalFile()
    #     except FileNotFoundError:
    #         zf = self.getRemoteFile()

    def savePokesLocally(self):
        path = self.getLocalPath()
