import numpy as np
import pathlib
from src.utils.core import hashit
from src.utils.image import loadFromRGBToGray
from src.wiki.creatures import creatures


parentPath = pathlib.Path(__file__).parent.resolve()
imagesPath = f'{parentPath}/images'
containersPath = f'{imagesPath}/containers'
iconsPath = f'{imagesPath}/icons'
monstersPath = f'{imagesPath}/monsters'
skullsPath = f'{imagesPath}/skulls'
images = {
    'containers': {
        'bottomBar': loadFromRGBToGray(f'{containersPath}/bottomBar.png'),
    },
    'icons': {
        'battleList': loadFromRGBToGray(f'{iconsPath}/battleList.png'),
    },
    'skulls': {
        'black': loadFromRGBToGray(f'{skullsPath}/black.png'),
        'green': loadFromRGBToGray(f'{skullsPath}/green.png'),
        'orange': loadFromRGBToGray(f'{skullsPath}/orange.png'),
        'red': loadFromRGBToGray(f'{skullsPath}/red.png'),
        'white': loadFromRGBToGray(f'{skullsPath}/white.png'),
        'yellow': loadFromRGBToGray(f'{skullsPath}/yellow.png'),
    }
}

# Index monster image files on disk by lowercased filename to overcome Linux ext4 case-sensitivity
monsterFilesOnDisk = {
    f.name.lower(): f
    for f in pathlib.Path(monstersPath).iterdir()
    if f.is_file()
}

creaturesNamesImagesHashes = {}

for creatureName in creatures:
    fileName = f"{creatureName}.png"
    targetPath = monsterFilesOnDisk.get(fileName.lower())
    if targetPath is None:
        continue
    creatureNameImage = loadFromRGBToGray(str(targetPath))
    creatureNameImage = np.ravel(creatureNameImage[8:9, 0:115])
    creatureNameImageHash = hashit(creatureNameImage)
    creaturesNamesImagesHashes[creatureNameImageHash] = creatureName
