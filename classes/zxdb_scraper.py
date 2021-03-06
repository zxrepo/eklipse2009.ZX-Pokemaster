from classes.database import *
from classes.game import Game
from classes.game_release import GameRelease
from classes.game_file import GameFile, ROUND_BRACKETS_REGEX
from classes.game_alias import GameAlias
from classes.scraper import *
from functions.game_name_functions import *
from mysql import connector
import time

def get_win_friendly_alias(alias):
    alias = ' '.join([x for x in alias.replace(':', ' : ').split(' ') if x])
    win_friendly_alias = filepath_regex.sub('-', alias)
    return win_friendly_alias

IDIOM_IDS_TO_TOSEC_LANGS = {
    '?0':'en-hr',
    '?1':'cz-en',
    '?2':'en-nl',
    '?3':'de-en',
    '?4':'en-pl',
    '?5':'en-pt',
    '?6':'en-ru',
    '?7':'en-sk',
    '?8':'en-es',
    '?9':'ca-es',
    '?a':'M3',
    '?b':'M3',
    '?c':'M5',
    '?d':'M5',
    '?e':'M3',
    '?f':'M4',
    '?g':'M3',
    '?h':'M4',
    '?i':'M4',
    '?j':'es-la',
    '?k':'en-fr',
    '?l':'M4',
    '?m':'M4',
    '?n':'M6',
    '?o':'M3',
    '?p':'M5',
    '?q':'M6',
    '?r':'M3',
    '?s':'M8',
    '?t':'en-it'
}

class RowConverter(connector.conversion.MySQLConverter):

    def row_to_python(self, row, fields):
        row = super(RowConverter, self).row_to_python(row, fields)
        def to_unicode(col):
            if type(col) == bytearray:
                return col.decode('utf-8')
            return col
        return[to_unicode(col) for col in row]

class ZXDBScraper():

    def __init__(self):
        self.conn = connector.connect(
                                user='root',
                                password='',
                                host='localhost',
                                database='zxdb',
                                charset='utf8',
                                converter_class=RowConverter
                                )
        self.cur = self.conn.cursor(dictionary=True, buffered=True)
        self.loadLookupTables()

    def loadLookupTables(self):
        self.file_exclusion_list = []
        with open('same_md5.csv', 'r', encoding='utf-8') as f:
            for line in f.readlines():
                line = line.split(';')
                decision = line[7]
                if not decision.startswith('KEEP'):
                    self.file_exclusion_list.append(line[9]+'|'+line[10])
        self.manually_corrected_content_descriptions = {}
        with open('content_desc_aliases.csv', 'r', encoding='latin-1') as f:
            for line in f.readlines():
                line = line.strip().split(';')
                if len(line)<5 or not line[4]:
                    continue
                key = line[5]+'|'+line[4]
                if line[2].startswith('NONE'):
                    self.manually_corrected_content_descriptions[key] = 'NONE'
                elif line[2].startswith('ALT'):
                    self.manually_corrected_content_descriptions[key] = line[2]
        self.pok_file_paths = {}
        with open('AllTipshopPokes\\zxdb_update.csv', 'r', encoding='utf-8') as f:
            for line in f.readlines():
                line = line.strip().split(';')
                if len(line)==2:
                    self.pok_file_paths[int(line[0])] = line[1].replace('/zxdb/sinclair/pokes', 'AllTipshopPokes')

    def update(self, script_path):
        self.cur.execute('SET FOREIGN_KEY_CHECKS = 0')
        requests = self.cur.execute(
            "SELECT concat('DROP TABLE IF EXISTS ', table_name, ';' "
            "FROM information_schema.tables WHERE table_schema = 'zxdb'")
        for request in requests:
            print(request)
            self.cur.execute(request)
        self.cur.execute('COMMIT')
        self.cur.execute('SET FOREIGN_KEY_CHECKS = 1')
        with open(script_path, 'r', encoding='utf-8') as f:
            sql = f.read().split(';\n')
            for query in sql:
                if not query or 'COMMIT' in query:
                    continue
                self.cur.execute(query)
            self.cur.execute('COMMIT')
        print('DB updated')

    def getAllGames(self):
        return self.getGames()

    def getGames(self, sql_where='', sql_limit=9999999):
        sql = 'SELECT entries.id AS zxdb_id, ' \
              'releases.release_seq AS release_seq, ' \
              'entries.title AS name, ' \
              'entries.library_title AS tosec_compliant_name, ' \
              'entries.is_xrated AS x_rated, ' \
              'webrefs.link AS tipshop_page, ' \
              'genretypes.text AS genre, ' \
              'entries.max_players AS number_of_players, ' \
              'entries.idiom_id AS language, ' \
              'entries.availabletype_id AS availability, ' \
              'downloads.file_link AS file_link, ' \
              'downloads.file_size AS file_size, ' \
              'downloads.filetype_id AS file_type_id, ' \
              'downloads.idiom_id AS file_language, ' \
              'downloads.comments AS file_version, ' \
              'filetypes.text AS file_type, ' \
              'entry_machinetype.text AS machine_type, ' \
              'download_machinetype.text AS file_machine_type, ' \
              'schemetypes.text AS protection_scheme, ' \
              'releases.release_seq AS release_id, ' \
              'aliases.library_title AS alt_name, ' \
              'aliases.idiom_id AS alt_language, ' \
              'publisher_labels.name AS publisher, ' \
              'publisher_labels.labeltype_id AS publisher_type, ' \
              'author_labels.name AS author, ' \
              'author_labels.labeltype_id AS author_type, ' \
              'author_teams_labels.name AS author_team, ' \
              'author_teams_labels.labeltype_id AS author_team_type, ' \
              'releases.release_year AS year,' \
              'publisher_labels.country_id AS country ' \
              'FROM entries ' \
              'LEFT JOIN webrefs ON entries.id=webrefs.entry_id AND webrefs.website_id=9 ' \
              'LEFT JOIN releases ON entries.id=releases.entry_id ' \
              'LEFT JOIN downloads ON downloads.entry_id=entries.id AND downloads.release_seq=releases.release_seq ' \
              'LEFT JOIN publishers ON publishers.entry_id=entries.id AND publishers.release_seq=releases.release_seq  ' \
              'LEFT JOIN labels AS publisher_labels ON publisher_labels.id=publishers.label_id ' \
              'LEFT JOIN authors ON authors.entry_id=entries.id  ' \
              'LEFT JOIN labels AS author_labels ON author_labels.id=authors.label_id  ' \
              'LEFT JOIN labels AS author_teams_labels ON author_teams_labels.id=authors.team_id  ' \
              'LEFT JOIN aliases ON aliases.entry_id=entries.id AND aliases.release_seq=releases.release_seq ' \
              'LEFT JOIN filetypes ON downloads.filetype_id=filetypes.id ' \
              'LEFT JOIN genretypes ON genretypes.id=entries.genretype_id ' \
              'LEFT JOIN machinetypes download_machinetype ON download_machinetype.id=downloads.machinetype_id ' \
              'LEFT JOIN machinetypes entry_machinetype ON entry_machinetype.id=entries.machinetype_id ' \
              'LEFT JOIN schemetypes ON schemetypes.id=downloads.schemetype_id   ' \
              'WHERE (entries.id>4000000 OR entries.id<2000000) AND ' \
              '(downloads.filetype_id IS NULL OR downloads.filetype_id!=-1) and '\
              '(authors.author_seq<=3 OR authors.author_seq IS NULL) '
        if sql_where:
            sql += sql_where+' '
        sql +='ORDER BY zxdb_id, release_seq, entries.title IS NOT NULL ' \
              'LIMIT '+str(sql_limit)
        self.cur.execute(sql)
        game = Game()
        release = GameRelease()
        games = []
        for row in self.cur:
            #Skipping ZX80/ZX81 files
            # print(row)
            if row['machine_type'] and row['machine_type'].startswith('ZX8'):
                continue
            if row['genre']=='Box Set':
                if row['zxdb_id'] in [8030]:
                    row['genre'] = 'Compilation - Applications'
                elif row['zxdb_id'] in [11472]:
                    row['genre'] = 'Compilation - Educational'
                else:
                    row['genre'] = 'Compilation - Games'
            if row['publisher'] == 'Creative.Radical.Alternative.Production Games':
                row['publisher'] = 'Creative Radical Alternative Production Games'
            if row['author_team']:
                row['author'] = row['author_team']
                row['author_type'] = row['author_team_type']
            if row['zxdb_id'] and row['name'] and row['zxdb_id']!=game.zxdb_id:
                game = self.gameFromRow(row)
                release = self.releaseFromRow(row, game)
                game.addRelease(release)
                games.append(game)
            if row['release_seq'] and row['release_seq']!=release.release_seq:
                release = self.releaseFromRow(row, game)
                game.addRelease(release)
            if release.release_seq==0 and game.publisher and row['publisher'] and game.raw_publisher and row['publisher'] not in game.raw_publisher:
                game.raw_publisher.append(row['publisher'])
                publisher = self.publisherNameFromRow(row)
                publishers = game.publisher.split(' - ')
                publishers.append(publisher)
                game.publisher = ' - '.join(sorted(publishers, key=str.lower))
            if release.publisher and row['publisher'] and row['publisher'] not in release.raw_publisher:
                release.raw_publisher.append(row['publisher'])
                publisher = self.publisherNameFromRow(row)
                release_publishers = release.publisher.split(' - ')
                release_publishers.append(publisher)
                release.publisher = ' - '.join(sorted(release_publishers, key=str.lower))
            if game.author and row['author'] and game.raw_author and row['author'] not in game.raw_author:
                game.raw_author.append(row['author'])
                author = self.authorNameFromRow(row)
                authors = game.author.split(' - ')
                authors.append(author)
                game.author = ' - '.join(sorted(authors, key = str.lower))
            if row['file_link'] and not (row['file_link'].endswith('.mlt')) and \
                    not  row['file_link'].endswith('pdf') and not row['file_link'].endswith('.jpg'):
                if row['file_type']=='Loading screen':
                    if row['file_link'].endswith('.gif'):
                        if release.loading_screen_gif_filepath and \
                                        release.loading_screen_gif_filepath!=row['file_link']:
                            pass
                        else:
                            release.loading_screen_gif_filepath = row['file_link']
                            release.loading_screen_gif_filesize = row['file_size']
                    elif row['file_link'].endswith('scr'):
                        if release.loading_screen_scr_filepath and \
                                        release.loading_screen_scr_filepath!=row['file_link']:
                            pass
                        else:
                            release.loading_screen_scr_filepath = row['file_link']
                            release.loading_screen_scr_filesize = row['file_size']
                elif row['file_type']=='In-game screen':
                    if row['file_link'].endswith('gif'):
                        if release.ingame_screen_gif_filepath and \
                                        release.ingame_screen_gif_filepath!=row['file_link']:
                            pass
                        else:
                            release.ingame_screen_gif_filepath = row['file_link']
                            release.ingame_screen_gif_filesize = row['file_size']
                    elif row['file_link'].endswith('scr'):
                        if release.ingame_screen_scr_filepath and \
                                        release.ingame_screen_scr_filepath != row['file_link']:
                            pass
                        else:
                            release.ingame_screen_scr_filepath = row['file_link']
                            release.ingame_screen_scr_filesize = row['file_size']
                elif row['file_type']=='Instructions' and row['file_link'].endswith('.txt'):
                    if release.manual_filepath and \
                                    release.manual_filepath!=row['file_link']:
                        pass
                    else:
                        release.manual_filepath = row['file_link']
                        release.manual_filesize = row['file_size']
                else:
                    if row['publisher'] and \
                            ('Nyitrai' in row['publisher'] or 'Jatekgyaros' in row['publisher']) and \
                            row['genre'] and row['genre'] == 'Compilation':
                        pass
                    else:
                        file_type = row['file_type'].lower()
                        if 'snapshot' in file_type or \
                             'disk' in file_type or \
                             'tape' in file_type or \
                             'rom' in file_type or \
                             'covertape' in file_type or \
                             'tr-dos' in file_type or \
                             'electronic magazine' in file_type or \
                             'cartridge' in file_type:
                            game_file = self.gameFileFromRow(row, game)
                            release.addFile(game_file)
                if row['alt_name'] and row['alt_language'] in (None, 'en'):
                    alias = self.sanitizeAlias(row['alt_name'])
                    release.addAlias(alias)
        games.append(game)
        return games

    def gameFromRow(self, row):
        # print(row['name'])
        # print('game_name=', row.get('tosec_compliant_name', row['name']))
        game_name = row.get('tosec_compliant_name', '').strip()
        if not game_name:
            game_name = row['name']
        game_name = self.sanitizeAlias(game_name)
        game = Game(game_name, int(row['zxdb_id']))
        publisher = self.publisherNameFromRow(row)
        game.setPublisher(publisher)
        author = self.authorNameFromRow(row)
        game.setAuthor(author)
        game.setYear(row['year'])
        pok_file_path = self.pok_file_paths.get(game.zxdb_id)
        if pok_file_path:
            game.importPokFile(file_path=pok_file_path)
        #TEMPORARY
        if not row['genre']:
            if game.zxdb_id in [
                            32168, 32169, 32170, 32171,
                            32172, 32173, 32174, 32180,
                            30349, 32176, 32201, 32175,
                            34322
                            ]:
                game.setGenre('Various Games')
            elif game.zxdb_id in [32176]:
                game.setGenre('Utilities - Screen')
            elif game.zxdb_id in [32257, 32258, 32259]:
                game.setGenre('Utilities')
            elif game.zxdb_id in [27590, 1000246]:
                game.setGenre('Firmware')
        elif game.zxdb_id in [8100]:
            game.setGenre('Compilation - Educational')
        else:
            game.setGenre(row['genre'])
        game.x_rated = row['x_rated']
        game.setNumberOfPlayers(row['number_of_players'])
        game.setMachineType(row['machine_type'])
        if row['language']:
            if row['language'] in IDIOM_IDS_TO_TOSEC_LANGS:
                game.setLanguage(IDIOM_IDS_TO_TOSEC_LANGS[row['language']])
            else:
                game.setLanguage(row['language'])
        game.setAvailability(row['availability'])
        game.tipshop_page = row['tipshop_page']
        game.raw_publisher, game.raw_author = [row['publisher']], [row['author']]
        return game

    def releaseFromRow(self, row, game):
        release_name = row['alt_name'] if row['alt_name'] else game.name
        release_name = self.sanitizeAlias(release_name)
        publisher = self.publisherNameFromRow(row)
        release = GameRelease(row['release_seq'],
                              row['year'],
                              publisher,
                              row['country'],
                              game,
                              [release_name])
        release.raw_publisher = [row['publisher']]
        if release.release_seq>0:
            release.addAlias(game.name)
        return release

    def publisherNameFromRow(self, row):
        if row['publisher_type']=='+': #person
            return putInitialsToEnd(row['publisher']).strip()
        elif row['publisher_type']=='-': #nickname
            return row['publisher'].strip()
        else: #company
            publisher = putPrefixToEnd(row['publisher'])
            publisher = publisher_regex.sub('', publisher)
            return publisher.strip()
        # if row['publisher_is_company'] in (None, 1):
        #     return putPrefixToEnd(row['publisher'])
        # elif row['publisher_is_company'] == 0:
        #     return putInitialsToEnd(row['publisher'])

    def authorNameFromRow(self, row):
        if row['author_type']=='+': #person
            author = remove_brackets_regex.sub('', row['author'])
            return putInitialsToEnd(author).strip()
        elif row['author_type']=='-': #nickname
            return row['author'].strip()
        else: #company
            author = putPrefixToEnd(row['author'])
            author  = publisher_regex.sub('', author)
            return putPrefixToEnd(author).strip()
        # if row['author_is_company'] in (None, 1):
        #     author = putPrefixToEnd(row['author'])
        #     if row['author_is_company']:
        #         author = publisher_regex.sub('', author)
        #     return author.strip()
        # elif row['author_is_company'] == 0:
        #     return putInitialsToEnd(row['author'])

    def sanitizeAlias(self, alias):
        round_brackets_contents = re.findall(ROUND_BRACKETS_REGEX, alias)
        alias = remove_brackets_regex.sub('', alias).strip()
        alias = alias.replace('Lerm ', '').replace('LERM ', '')
        alias = alias.replace(' ,', ',')
        alias = alias.replace('AlchNews', 'Alchemist News')
        alias = alias.replace('Zx Spectrum +', 'ZX Spectrum+')
        if alias == 'Pozycje Milosne':
            alias = '22 Pozycje milosne'
        elif alias == 'Treasure Island Dizzy':
            alias = 'Dizzy 2 - '+alias
        elif alias == 'Fantasy World Dizzy':
            alias = 'Dizzy 3 - ' + alias
        elif alias == 'Magicland Dizzy':
            alias = 'Dizzy 4 - '+alias
        elif alias == 'Spellbound Dizzy':
            alias = 'Dizzy 5 - '+alias
        elif alias == 'Dizzy, Prince of the YolkFolk':
            alias = 'Dizzy 6 - '+alias
        elif alias == 'Crystal Kingdom Dizzy':
            alias = 'Dizzy 7 - '+alias
        alias = alias.replace('BubbleLand', 'Bubble Land')
        alias = alias.replace('F-14 Afterburner', 'Afterburner')
        alias = alias.replace('Santa Clause', 'Santa Claus')
        alias = alias.replace('Trooper -Point', 'Trooper Point')
        if 'Dalek Attack' in alias or 'the Daleks' in alias:
            alias = 'Dalek Attack'
        alias = ' - '.join([alias]+round_brackets_contents)
        if alias.endswith(', 3D'):
            alias = '3D ' + alias[:-4]
        if alias.endswith(' +'):
            alias = alias.replace(' +', '+')
        if alias.startswith('The '):
            alias = alias [4:] + ', The'
        return alias

    def gameFileFromRow(self, row, game):
        game_file = GameFile(row['file_link'], game=game, source='wos')
        game_file.size_zipped = row['file_size']
        game_file.setMachineType(row['machine_type'])
        game_file.setProtectionScheme(row['protection_scheme'])
        if row['file_language']:
            if row['file_language'] in IDIOM_IDS_TO_TOSEC_LANGS:
                game_file.setLanguage(IDIOM_IDS_TO_TOSEC_LANGS[row['file_language']])
            else:
                game_file.setLanguage(row['file_language'])
        if row['file_version'] and row['file_version'].lower().startswith('v') \
                and row['file_version'][1].isdigit():
            game_file.content_desc = ' '+remove_brackets_regex.sub('', row['file_version']).strip()

        return game_file

    def downloadMissingFilesForGames(self, games):
        print("Downloading missing files...")
        s = Scraper()
        for game in games:
            for file in game.getFiles():
                local_path = file.getLocalPath()
                if os.path.exists(local_path) and \
                        (os.path.getsize(local_path) == file.size_zipped or \
                        not file.size_zipped):
                    continue
                local_size = os.path.getsize(local_path) if os.path.exists(local_path) else 0
                if local_size and local_size != file.size_zipped:
                    print('wrong file size:', local_path)
                    continue
                if 'pub\sinclair' in local_path:
                    local_path = local_path.replace('/pub/sinclair', '/sinclair')
                    mirror = WOS_MIRRORS[0] #archive.org
                else:
                    mirror = WOS_MIRRORS[1] #spectrumcomputing.co.uk
                try:
                    file_url = file.getWosPath(wos_mirror_root=mirror).replace('pub/sinclair', 'sinclair')
                    status = s.downloadFile(file_url, local_path)
                    if os.path.exists(local_path) and \
                            os.path.getsize(local_path) != file.size_zipped:
                        print('wrong file size after download:', local_path)
                    time.sleep(.5)
                except:
                    print(traceback.format_exc())

    def getInfoFromLocalFiles(self, games):
        for game in games:
            game.setCountryFromFiles()
            for release in game.releases:
                release.getInfoFromLocalFiles()
                for game_file in release.files:
                    file_exclusion_key = game_file.wos_name + '|' + game_file.wos_path
                    if file_exclusion_key in self.file_exclusion_list:
                        release.removeFile(file_exclusion_key)
            game.setContentDescForZXDBFiles(self.manually_corrected_content_descriptions)
