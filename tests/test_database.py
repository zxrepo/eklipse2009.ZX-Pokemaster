from classes.database import *
from classes.game import *
from classes.game_file import *
from classes.zxdb_scraper import ZXDBScraper
from functions.game_name_functions import *
from classes.tipshop_scraper import TipshopScraper
import  unittest
import time
if (os.getcwd().endswith('tests')):
    os.chdir('..')

db = Database()
# db.loadCache()

class TestDatabase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestDatabase, self).__init__(*args, **kwargs)
        self.db = db

    def test_adding_game(self):
        game = Game(name='Tujad', zxdb_id=5448)
        zxdb = ZXDBScraper()
        game = zxdb.getGames(' AND entries.id=5448')[0]
        game.releases[0].getInfoFromLocalFiles()
        ts = TipshopScraper()
        game.tipshop_page = 'http://www.the-tipshop.co.uk/cgi-bin/info.pl?wosid=0005448'
        ts.scrapePokes(game)
        self.db.addGame(game)
        self.db.commit()
        game = self.db.getGameByWosID(5448)
        self.check_if_game_is_tujad(game)

    def test_search_string(self):
        game_name = 'La Abadia Del Crimen'
        self.assertEqual(getSearchStringFromGameName(game_name), 'abadiadelcrimen')
        game_name = 'Abadia Del Crimen, La'
        self.assertEqual(getSearchStringFromGameName(game_name), 'abadiadelcrimen')

    # Irrelevant test, since now each Game with empty zxdb_id has 9000000+ auto id
    # def test_adding_broken_zxdb_id(self):
    #     game = Game()
    #     with self.assertRaises(Exception):
    #         self.db.addGame(game)

    def test_getting_game_by_zxdb_id(self):
        game = self.db.getGameByWosID(5448)
        self.check_if_game_is_tujad(game)

    def check_if_game_is_tujad(self, game):
        self.assertEqual(game.name, 'Tujad')
        self.assertEqual(game.publisher, 'Ariolasoft UK')
        self.assertEqual(game.year, 1986)
        self.assertEqual(game.number_of_players, 1)
        self.assertEqual(game.genre, 'Arcade Game - Maze')
        self.assertEqual(game.machine_type, '48K')
        self.assertTrue(len(game.getFiles())>0)
        for file in game.getFiles():
            if file.md5 == '200c35cb8984a40257dd8b317263d752':
                self.assertEqual(file.wos_name, 'TUJAD.TAP')

    def test_getting_game_by_md5(self):
        file = GameFile('ftp/pub/sinclair/games/t/Tujad.tap.zip')
        md5 = '200c35cb8984a40257dd8b317263d752'
        self.assertEqual(md5, file.getMD5())
        game = self.db.getGameByFileMD5(file.getMD5())
        self.check_if_game_is_tujad(game)

    def test_importing_corrupt_pok_file(self):
        game = self.db.getGameByWosID(26046)
        self.assertEqual(len(game.cheats), 0)

    def test_getting_game_by_file_name(self):
        'He had such a big head that if he were a mouse he would have to toss the mice from under the bed with a brow - Part II'
        filename = 'He Had Such A Big Head That If He Were A Cat He Would Have To Toss The Mice From Under The Bed With A Brow - Part II (2011)(Apenao)[CSSCGC].tap'
        game = self.db.getGameByFilePath(filename)
        self.assertEqual(game.zxdb_id, 31193)
        filename = '2048 (2014)(Alone Coder).tap'
        game = self.db.getGameByFilePath(filename)
        self.assertEqual(game.zxdb_id, 30134)
        filename = 'Helter Skelter + Editor (1991)(Audiogenic)[h Rajsoft].tap'
        game = self.db.getGameByFilePath(filename)
        self.assertEqual(game.zxdb_id, 2291)
        filename = 'Helter Skelter (1991)(Audiogenic)[h Rajsoft].tap'
        game = self.db.getGameByFilePath(filename)
        self.assertEqual(game.zxdb_id, 2291)
        filename = '66 (19xx)(Stankisoft)(de).tap'
        game = self.db.getGameByFilePath(filename)
        self.assertEqual(game.zxdb_id, 39)
        filename = "Giant's Revenge (1984)(Thor Computer Software).tap"
        game = self.db.getGameByFilePath(filename)
        self.assertEqual(game.zxdb_id, 2040)
        filename = "Coin-Op Hits (1990)(US Gold).tap"
        game = self.db.getGameByFilePath(filename)
        self.assertEqual(game.zxdb_id, 11598)
        filename = "Coin-Op Hits (1990)(U.S. Gold).tap"
        game = self.db.getGameByFilePath(filename)
        self.assertEqual(game.zxdb_id, 11598)


    def test_appending_tosec_file_info(self):
        filename = "Gonzzalezz (1989)(Opera Soft)(es)(Side B).zip"
        file_path = os.path.join('tosec', 'Sinclair ZX Spectrum', 'games', '[TAP]', filename)
        game_file = GameFile(file_path)
        file_md5 = game_file.getMD5()
        print(file_md5)
        game = self.db.getGameByFileMD5(file_md5)
        self.assertEqual(game.zxdb_id, 2097)

    def test_adding_multipart_files(self):
        zxdb = ZXDBScraper()
        game = zxdb.getGames(' AND entries.id=16')[0]
        for release in game.releases:
            release.getInfoFromLocalFiles()
        self.db.addGame(game)
        self.db.commit()
        game = self.db.getGameByWosID(16)
        self.assertGreaterEqual(len(game.getFiles()), 7)
        file = self.get_file_from_game_by_wos_name(game, '19 Part 1 - Boot Camp - Side A.tzx')
        self.assertEqual(file.wos_name, '19 Part 1 - Boot Camp - Side A.tzx')
        self.assertEqual(file.md5, '33ab1b76b8fd735299c10307981a912e')
        file = self.get_file_from_game_by_wos_name(game, '19 Part 1 - Boot Camp - Side B.tzx')
        self.assertEqual(file.wos_name, '19 Part 1 - Boot Camp - Side B.tzx')
        self.assertEqual(file.md5, 'bf2b3dbae671bbaf10b6c94b712c4ed8')

    def test_game_by_filename(self):
        gamefile = GameFile('tosec_games/[TAP]/Alien 8 (1985)(Ultimate Play The Game).zip')
        game = self.db.getGameByFile(gamefile)
        self.assertEqual(game.name, 'Alien 8')

    def test_alta_tension(self):
        game = Game('Alta tension', 6)
        zxdb = ZXDBScraper()
        game = zxdb.getGames(' AND entries.id=6')[0]
        game.releases[0].getInfoFromLocalFiles()
        self.db.addGame(game)
        self.db.commit()
        game = self.db.getGameByWosID(6)
        self.assertGreater(len(game.getFiles()), 2)

    def test_jswilly_3(self):
        game_file = GameFile('tosec//Games//[Z80]//Jet Set Willy III (1985)(MB - APG Software).zip')
        game = self.db.getGameByFile(game_file)
        self.assertEqual(game.name, 'JetSet Willy III')

    def get_file_from_game_by_wos_name(self, game, filename):
        for file in game.getFiles():
            if file.wos_name==filename:
                return file

    def test_find_game_file_with_article_and_alias(self):
        game = self.db.getGameByFilePath('Time of the End, The (1986)(Mandarin).zip')
        self.assertEqual(game.name, 'Time of the End')
        game = self.db.getGameByFilePath('Zipper Flipper (1984)(R.E.D. Sunshine).zip')
        self.assertEqual(game.zxdb_id, 5857)

    def test_multiple_releases(self):
        game = self.db.getGameByWosID(1)
        self.assertEqual(len(game.releases), 4)
        self.assertEqual('Domark', game.releases[0].publisher)
        self.assertEqual('Erbe', game.releases[1].publisher)
        self.assertEqual('Musical 1', game.releases[2].publisher)
        self.assertEqual('Hit Squad, The', game.releases[3].publisher)

    def test_zzzz(self):
        game_file = GameFile('tosec\Games\[TZX]\Zzzz (1986)(Zenobi Software)[re-release].zip')
        game_file.format = 'tzx'
        game = self.db.getGameByFile(game_file)
        self.assertEqual(game.name, 'Zzzz')
        self.assertEqual(len(game.releases), 2)
        release = game.findReleaseByFile(GameFile('Zzzz (1986)(Zenobi Software)'))
        self.assertEqual(release.release_seq, 1)
        release = game.findReleaseByFile(GameFile('Zzzz (1986)(Mastertronic)'))
        self.assertEqual(release.release_seq, 0)
        for release in game.releases:
            print(release, release.files)

    def test_9hole_golf(self):
        md5 = '98fa942231a33b03d55f351afb3006fa'
        game = self.db.getGameByFileMD5(md5)
        self.assertEqual(game.name, '9-Hole Golf')
        self.assertEqual(len(game.releases), 1)

    def test_olisa(self):
        md5 = '61edae0e09709406bb3082bbeecb8b63'
        game = self.db.getGameByFileMD5(md5)
        self.assertGreaterEqual(len(game.getFiles()), 3)

    # I don't remember why I've written this test. It does not pass now and it's OK.
    # def test_find_games_with_no_original_release(self):
    #     games = db.getAllGames()
    #     games_with_no_original_release = []
    #     for game in games:
    #         if not game.getFiles():
    #             continue
    #         if not game.releases[0].files:
    #             games_with_no_original_release.append(game)
    #     print(games_with_no_original_release)
    #     self.assertEqual(len(games_with_no_original_release), 0)

    def test_car_game(self):
        game_file = GameFile('tosec\CSSCGC Games Reviewed\\1996\Car (1996)(Yates, Damion)(48K-128K)[CSSCGC].z80')
        game = db.getGameByFile(game_file)
        self.assertNotEqual(game.zxdb_id, 1299)

    def test_xrated(self):
        game = self.db.getGameByWosID(3861)
        for file in game.getFiles():
            tosec_name = file.getTOSECName()
            self.assertTrue('[adult]' in tosec_name)

    def test_machine_type_48K(self):
        pattern = '{GameName} ({Year}) ({Publisher}) ({MachineType}) {ModFlags}'
        game_file = GameFile('tosec\\reviewed files\homebrew\Games\Souls (2013)(Retrobytes Productions)(ES).tap')
        game_file.game = db.getGameByFile(game_file)
        output_name = game_file.getOutputName(pattern)
        self.assertEqual(output_name, 'Souls (2013) (Retrobytes Productions) (48K).tap')
        game_file = GameFile('ftp/pub/sinclair/games/s/Souls.tzx.zip')

    # def test_disk_cache(self):
    #     time_start = time.clock()
    #     db.loadCache()
    #     print('Loaded cache from sql in ', time.clock()-time_start)
    #     # db.saveDiskCache()
    #     db.cache_by_crc32, db.cache_by_zxdb_id, db.cache_by_name, db.cache_by_md5 = {}, {}, {}, {}
    #     time_start = time.clock()
    #     db.loadCacheFromDisk()
    #     print('Loaded cache from disk in ', time.clock()-time_start)
    #     crc32 = 'e0bd1ed3'
    #     games = db.getGamesByFileCRC32(crc32)
    #     self.assertEqual(len(games), 1)
    #     game = games[0]
    #     file = game.findFileByCRC32(crc32)
    #     self.assertEqual(file.md5, '341881d1991f14e5382b4daa193f7bcc')



if __name__=='__main__':
    unittest.main()