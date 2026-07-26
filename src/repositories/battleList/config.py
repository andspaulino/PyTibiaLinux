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
creaturesNamesImagesHashes = {}

def get_monster_image_path(folder: pathlib.Path, name: str) -> pathlib.Path | None:
    exact = folder / f'{name}.png'
    if exact.exists():
        return exact
    name_lower = f'{name}.png'.lower()
    for item in folder.iterdir():
        if item.name.lower() == name_lower:
            return item
    return None

monsters_folder = pathlib.Path(monstersPath)
for creatureName in creatures:
    img_path = get_monster_image_path(monsters_folder, creatureName)
    if img_path is not None:
        creatureNameImage = loadFromRGBToGray(str(img_path))
        creatureNameImage = np.ravel(creatureNameImage[8:9, 0:115])
        creatureNameImageHash = hashit(creatureNameImage)
        creaturesNamesImagesHashes[creatureNameImageHash] = creatureName
