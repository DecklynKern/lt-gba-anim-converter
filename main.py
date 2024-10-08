from parse import *
from spell import *

from PyQt5 import QtGui
import os
import json
import shutil

spellName = input("spell name: ")
animationPath = input("animation path: ")
outputPath = input("output folder (will be created if it doesn't exist): ")

def dumpJSON(name, data):
    with open(os.path.join(outputPath, name + ".json"), "w") as outputFile:
        json.dump(data, outputFile, indent=4)

def main():

    app = QtGui.QGuiApplication([])

    parser = Parser(spellName)
    spell = parser.parse(os.path.join(animationPath, "Spell.txt"))

    spell.calculatePalettes(animationPath)

    if not os.path.exists(outputPath):
        os.mkdir(outputPath)

    dumpJSON(spell.name + "_effect", spell.generateParentEffectJSON())

    dumpJSON(spell.name + "FGHit_effect", spell.generateForegroundOnHitJSON())
    dumpJSON(spell.name + "FGMiss_effect", spell.generateForegroundOnMissJSON())

    dumpJSON(spell.name + "FGHit_Image_palette", spell.generateForegroundOnHitPaletteJSON())
    dumpJSON(spell.name + "FGMiss_Image_palette", spell.generateForegroundOnMissPaletteJSON())

    fgHitPath = os.path.join(outputPath, spell.name + "FGHit.png")
    fgMissPath = os.path.join(outputPath, spellName + "FGMiss.png")

    spell.getForegroundSheet(animationPath).save(fgHitPath)
    shutil.copyfile(fgHitPath, fgMissPath)

    if not spell.skipBackground:

        dumpJSON(spell.name + "BGHit_effect", spell.generateBackgroundOnHitJSON())
        dumpJSON(spell.name + "BGMiss_effect", spell.generateBackgroundOnMissJSON())

        dumpJSON(spell.name + "BGHit_Image_palette", spell.generateBackgroundOnHitPaletteJSON())
        dumpJSON(spell.name + "BGMiss_Image_palette", spell.generateBackgroundOnMissPaletteJSON())

        bgHitPath = os.path.join(outputPath, spell.name + "BGHit.png")
        bgMissPath = os.path.join(outputPath, spellName + "BGMiss.png")

        spell.getBackgroundSheet(animationPath).save(bgHitPath)
        shutil.copyfile(bgHitPath, bgMissPath)

if __name__ == "__main__":
    main()
