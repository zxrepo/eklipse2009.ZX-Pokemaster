from classes.tipshop_scraper import *
from classes.game import Game
from classes.wos_scraper import *
from classes.database import *
import unittest
import pprint
pp = pprint.PrettyPrinter(indent=2)

class TipshopScraperTests(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TipshopScraperTests, self).__init__(*args, **kwargs)
        self.ts = TipshopScraper()
        self.db = Database()

    def test_simple_pokes_scraping(self):
        game = Game(name='Tujad', zxdb_id=5448)
        self.ts.scrapePokes(game)
        self.assertEqual(len(game.cheats), 2)
        self.assertEqual(game.cheats[0].description, "Infinite lives")
        self.assertEqual(len(game.cheats[0].pokes), 1)
        self.assertEqual(game.cheats[0].pokes[0].value, 58)
        self.assertEqual(game.cheats[1].description, "Infinite energy")
        self.assertEqual(len(game.cheats[1].pokes), 1)
        self.assertEqual(game.cheats[1].pokes[0].address, 31443)

    def test_medium_pokes_scraping(self):
        game = Game(name="Gimme Bright", zxdb_id=25640)
        self.ts.scrapePokes(game)
        pp.pprint(game.cheats)
        self.assertEquals(game.cheats[0].description, "Lives")
        self.assertEquals(game.cheats[1].description, "Time")
        self.assertEquals(game.cheats[2].description, "Lives")
        self.assertEquals(game.cheats[3].description, "Time")

    def test_complex_pokes_scraping(self):
        game = Game(name="Ghost Hunters", zxdb_id=9350)
        self.ts.scrapePokes(game)
        pp.pprint(game.cheats)
        self.assertEquals(game.cheats[2].description, 'You don\'t need blood goblet (Platform "A")')
        self.assertEquals(game.cheats[2].pokes[0].address, 41530)
        self.assertEquals(game.cheats[2].pokes[0].value, 130)

    def test_multipoke_cheats_scraping(self):
        game = Game(name="Apulija-13", zxdb_id=27997)
        self.ts.scrapePokes(game)
        pp.pprint(game.cheats)
        self.assertEquals(len(game.cheats), 7)
        multipoke_cheat = game.cheats[-1]
        self.assertEquals(len(multipoke_cheat.pokes), 9)

    def test_no_pokes_scraping(self):
        game = Game(name='100', zxdb_id=21130)
        self.ts.scrapePokes(game)
        self.assertEquals(len(game.cheats), 0)

    def test_invalid_tag_name(self):
        game = Game(name='Captain Blood', zxdb_id=810)
        self.ts.scrapePokes(game)
        game = Game(zxdb_id=825)
        self.ts.scrapePokes(game)

    def test_short_desc_elimination(self):
        game = Game(name='Zzoom', zxdb_id=5894)
        self.ts.scrapePokes(game)
        pp.pprint(game.cheats)
        self.assertEquals(len(game.cheats), 1)
        self.assertTrue(self.game_has_cheat_named(game, 'infinite lives'))

    def test_non_empty_desc(self):
        game = Game(name='Zybex', zxdb_id=5889)
        self.ts.scrapePokes(game)
        self.assertEquals(game.cheats[0].description, 'Infinite lives')
        self.assertEquals(len(game.cheats[0].pokes), 2)

    def test_multipart_desc(self):
        game = Game(name='Senda Salvaje', zxdb_id=4395)
        self.ts.scrapePokes(game)
        pp.pprint(game.cheats)
        self.assertEquals(len(game.cheats), 5)
        self.assertEquals(game.cheats[0].description, "Infinite lives")

    def test_variable_poke(self):
        game = Game(name="Pinball", zxdb_id=3718)
        self.ts.scrapePokes(game)
        cheat = game.cheats[1]
        pp.pprint(game.cheats)
        self.assertEqual(cheat.description, 'Lives')
        self.assertEqual(len(cheat.pokes), 1)
        self.assertEqual(cheat.pokes[0].address, 28950)
        self.assertEqual(cheat.pokes[0].value, 256)

    def test_jet_set_willy(self):
        game = Game(name="Jet Set WIlly", zxdb_id=2589)
        self.ts.scrapePokes(game)
        game.exportPokFile('test.pok')
        game.importPokFile('test.pok')

    def test_addams_family(self):
        game = Game(name='Addams Family', zxdb_id=82)
        self.ts.scrapePokes(game)
        print(game.cheats)
        self.assertEqual(4, len(game.cheats))


    def test_stonkers(self):
        game = Game(name='Stonkers', zxdb_id=4913)
        self.ts.scrapePokes(game)
        print(game.cheats)
        self.assertEqual(len(game.cheats), 7)

    def test_extraordinarios_casos(self):
        game = Game(zxdb_id=14654)
        self.ts.scrapePokes(game)
        print(game.cheats)
        self.assertEqual(len(game.cheats), 3)

    def test_ms_pacman(self):
        game = Game(zxdb_id=3316)
        self.ts.scrapePokes(game)
        print(game.cheats)
        self.assertEqual(len(game.cheats), 5)

    def test_franknstein(self):
        game = Game(zxdb_id=3316)
        self.ts.scrapePokes(game)
        print(game.cheats)
        self.assertEqual(game.cheats[0].description, 'Infinite lives (One player mode)')
        self.assertTrue(self.game_has_cheat_named(game, 'immunity'))
        self.assertTrue(self.game_has_cheat_named(game, 'silent game'))

    def test_ah_diddum(self):
        #THIS SHOULD BE FIXED MANUALLY
        game = Game(name='Ah diddum', zxdb_id=112, db=self.db)
        self.ts.scrapePokes(game)
        print(game.cheats)
        # self.assertTrue(self.game_has_cheat_named(game, 'kempston'))

    def test_cowboy(self):
        #THIS SHOULD BE FIXED MANUALLY
        game = Game(name='Cowboy', zxdb_id=15419, db=self.db)
        game = self.db.getGameByWosID(game.zxdb_id)
        print(game.cheats)
        self.assertEqual(len(game.cheats), 2)
        self.ts.scrapePokes(game)
        self.assertEqual(len(game.cheats), 3)

    def test_comeme(self):
        game = Game(name='Comeme', zxdb_id=1035)
        self.ts.scrapePokes(game)
        print(game.cheats)
        self.assertEqual(len(game.cheats), 4)

    # THIS SHOULD BE FIXED MANUALLY
    # def test_ghostbusters(self):
    #     game = Game(name='Ghostbusters', zxdb_id=2025, db=self.db)
    #     self.ts.scrapePokes(game)
    #     game.exportPokFile('test.pok')
    #     game.cheats = []
    #     game.importPokFile('test.pok')
    #     pp.pprint(game.cheats)
    #     self.assertFalse(self.game_has_cheat_named(game, 'randomize usr'))

    def game_has_cheat_named(self, game, cheat_description):
        for cheat in game.cheats:
            if cheat_description in cheat.description.lower():
                return True
        return False

    def test_desc_in_brackets_and_broken_brackets(self):
        game = Game('Flynn''s Adventure In Bombland', 26114)
        self.ts.scrapePokes(game)
        self.assertEqual(game.cheats[0].description, 'Infinite lives')
        self.assertEqual(game.cheats[1].description, 'Infinite time')
        #Bug on website: need manual fixing
        self.assertEqual(game.cheats[2].description, '(number of lives')

    def test_desc_in_brackets_and_multiline_cheat(self):
        game = Game('Myth', 3354)
        self.ts.scrapePokes(game)
        self.assertEqual(game.cheats[0].description, 'Credits')
        self.assertEqual(game.cheats[1].description, 'Number of lives')
        self.assertEqual(game.cheats[2].description, 'Level 1')
        self.assertEqual(len(game.cheats), 6)

    def test_multiline_pok(self):
        game = Game(name='Crazy Balloons', zxdb_id=1118)
        self.ts.scrapePokes(game)
        self.assertEqual(len(game.cheats), 4)

if __name__=='__main__':
    unittest.main()