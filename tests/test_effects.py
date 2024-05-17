import unittest

from effects import effects

class TestEffects(unittest.TestCase):
    def test_SingleColor(self):
        print("Testing SingleColor()")
        result = effects.SingleColor(1, 0xffffff)
        self.assertEqual(result, [0xffffff])



    def test_Gradient(self):
        print("Testing Gradient()")
        # test valid scenarios
        result = effects.Gradient(1)
        self.assertEqual(result, [0x000000])

        result = effects.Gradient(1, 0xffffff)
        self.assertEqual(result, [0xffffff])

        # test input edge cases
        result  = effects.Gradient(1, 0x000000, 0xffffff)
        self.assertEqual(result, [0x7f7f7f])

        result  = effects.Gradient(0, 0x000000, 0xffffff)
        self.assertEqual(result, [])

        result  = effects.Gradient(3, 0x000000, 0xffffff)
        self.assertEqual(result, [0x000000, 0x7f7f7f, 0xffffff])
        result  = effects.Gradient(3, 0xff0000, 0x0000ff)
        self.assertEqual(result, [0xff0000, 0x7f007f, 0x0000ff])
        


    def test_InterpolateColors(self):
        print("Testing _InterpolateColors()")
        result = effects._InterpolateColors_(0, 0x000000, 0xffffff)
        self.assertEqual(result, 0x000000)
        result = effects._InterpolateColors_(1, 0x000000, 0xffffff)
        self.assertEqual(result, 0xffffff)
        result = effects._InterpolateColors_(0.5, 0x000000, 0xffffff)
        self.assertEqual(result, 0x7f7f7f)


    def test_Rainbow(self):
        result = effects.Rainbow(0)
        self.assertEqual(result, [])

        result = effects.Rainbow(1)
        self.assertEqual(result, [0xff0000])
        result = effects.Rainbow(1)
        self.assertEqual(result, [0xff0000])
        result = effects.Rainbow(3)
        self.assertEqual(result, [0xff0000,0x00ff00, 0x0000ff])

        result = effects.Rainbow(3, offset = 1)
        self.assertEqual(result, [0x0000ff, 0xff0000, 0x00ff00])

        result = effects.Rainbow(3, scale = 3)
        self.assertEqual(result, [0xff0000, 0xff0000, 0xff0000])

        #result = effects.Rainbow(3, scale = 2)
        #self.assertEqual(result, [0xff0000, 0x00ff00, 0x00ff00]) # todo: fix


    def test_RGBToHex(self):
        self.assertEqual(effects.RGBToHex(255,255,255), 0xffffff)
        self.assertEqual(effects.RGBToHex(0,0,0), 0x000000)
        self.assertEqual(effects.RGBToHex(118,74,190), 0x764ABE)

    def test_HexToRGB(self):
        self.assertEqual(effects.HexToRGB(0xffffff), (255,255,255))
        self.assertEqual(effects.HexToRGB(0x000000), (0,0,0))
        self.assertEqual(effects.HexToRGB(0x764ABE), (118,74,190))


    def test_Average(self):
        self.assertEqual(effects._Average([0x000000, 0xffffff]), 0x7f7f7f)

if __name__ == '__main__':
    unittest.main()